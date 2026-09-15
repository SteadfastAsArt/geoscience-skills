"""Actual GemGIS examples and GIS helper against real GeoTIFF/GeoPackage IO."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import gemgis
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from pyproj import Geod, Transformer
from shapely.geometry import LineString, Point

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('gis_prepare', ROOT / 'gemgis/scripts/prepare_gempy_data.py')
HELPER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(HELPER)


def example(path, heading):
    text = (ROOT / path).read_text()
    section = re.search(rf'^## {re.escape(heading)}\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    block = re.search(r'^```python\n(.*?)^```', section[1], re.M | re.S)
    namespace = {}
    exec(compile(block[1], path, 'exec'), namespace)
    return namespace


class GisExamples(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.dem = self.directory / 'dem.tif'
        elevations = np.array([[100, 110, 120], [200, 210, 220], [300, -9999, 320]], dtype='float32')
        with rasterio.open(self.dem, 'w', driver='GTiff', height=3, width=3, count=1,
                           dtype='float32', crs='EPSG:32632', transform=from_origin(500000, 5600030, 10, 10),
                           nodata=-9999) as dem:
            dem.write(elevations, 1)
        self.contacts = gpd.GeoDataFrame({'formation': ['older', 'younger']},
            geometry=[LineString([(500005, 5600025), (500015, 5600025)]),
                      LineString([(500005, 5600015), (500015, 5600015), (500025, 5600015)])],
            crs='EPSG:32632', index=[7, 19])

    def test_markdown_preserves_attributes_when_line_vertex_counts_differ(self):
        function = example('gemgis/SKILL.md', 'Extract contact vertices')['contacts_at_dem']
        with rasterio.open(self.dem) as dem:
            result = function(self.contacts, dem)
        self.assertEqual(result.formation.tolist(), ['older', 'older', 'younger', 'younger', 'younger'])
        np.testing.assert_array_equal(result.Z, [100, 110, 200, 210, 220])
        np.testing.assert_array_equal(result.X, [500005, 500015, 500005, 500015, 500025])

    def test_profile_markdown_uses_real_raster_api_and_chainage(self):
        function = example('gemgis/references/data_extraction.md', 'DEM profile')['sample_profile']
        with rasterio.open(self.dem) as dem:
            distance, z = function(LineString([(500005, 5600025), (500025, 5600025)]), dem, 3)
        np.testing.assert_array_equal(distance, [0, 10, 20])
        np.testing.assert_array_equal(z, [100, 110, 120])

    def test_helper_reprojects_vectors_and_converts_only_declared_vertical_units(self):
        geographic = self.contacts.to_crs('EPSG:4326')
        result = HELPER.extract_interfaces(geographic, self.dem, dem_z_unit='ft')
        np.testing.assert_allclose(result.Z, np.array([100, 110, 200, 210, 220]) * .3048)
        np.testing.assert_allclose(result.X, [500005, 500015, 500005, 500015, 500025], atol=1e-6)
        self.assertEqual(result.formation.tolist(), ['older', 'older', 'younger', 'younger', 'younger'])

    def test_nodata_and_outside_points_fail_without_fabricated_elevations(self):
        for point, message in [(Point(500015, 5600005), 'NoData'), (Point(500035, 5600005), 'outside')]:
            data = gpd.GeoDataFrame({'formation': ['A']}, geometry=[point], crs=self.contacts.crs)
            with self.subTest(point=point), self.assertRaisesRegex(ValueError, message):
                HELPER.extract_interfaces(data, self.dem, dem_z_unit='m')

    def test_orientation_polarity_rhr_and_invalid_dip(self):
        data = gpd.GeoDataFrame({'formation': ['A', 'B'], 'dip': [30, 45], 'strike': [300, 90], 'polarity': [-1, 1]},
            geometry=[Point(500005, 5600025), Point(500015, 5600025)], crs=self.contacts.crs, index=[7, 19])
        with self.assertRaisesRegex(ValueError, 'right-hand-rule'):
            HELPER.extract_orientations(data, self.dem, dem_z_unit='m')
        result = HELPER.extract_orientations(data, self.dem, dem_z_unit='m', strike_convention='rhr', azimuth_reference='dem-grid')
        np.testing.assert_array_equal(result.azimuth, [30, 180])
        np.testing.assert_array_equal(result.polarity, [-1, 1])
        self.assertEqual(result.formation.tolist(), ['A', 'B'])
        data.loc[7, 'dip'] = 120
        with self.assertRaisesRegex(ValueError, 'Dip'):
            HELPER.extract_orientations(data, self.dem, dem_z_unit='m', strike_convention='rhr', azimuth_reference='dem-grid')

    def test_custom_formation_selection_does_not_duplicate_or_restore_old_labels(self):
        contacts = self.contacts.assign(unit=['A', 'B'])
        result = HELPER.extract_interfaces(contacts, self.dem, 'unit', dem_z_unit='m')
        self.assertEqual(result.columns.tolist(), ['X', 'Y', 'Z', 'formation'])
        self.assertEqual(result.formation.tolist(), ['A', 'A', 'B', 'B', 'B'])

    def test_true_north_conversion_matches_projected_geodesic_bearing(self):
        lon, lat, true_azimuth = 12., 50., 40.
        transform = Transformer.from_crs('EPSG:4326', 'EPSG:32632', always_xy=True)
        x, y = transform.transform(lon, lat)
        dem_path = self.directory / 'convergence.tif'
        with rasterio.open(dem_path, 'w', driver='GTiff', height=3, width=3, count=1,
                           dtype='float32', crs='EPSG:32632', transform=from_origin(x - 15, y + 15, 10, 10)) as dem:
            dem.write(np.full((3, 3), 100, dtype='float32'), 1)
        data = gpd.GeoDataFrame({'formation': ['A'], 'dip': [30.], 'azimuth': [true_azimuth]},
                               geometry=[Point(lon, lat)], crs='EPSG:4326')
        result = HELPER.extract_orientations(data, dem_path, dem_z_unit='m', azimuth_reference='true-north')
        lon2, lat2, _ = Geod(ellps='WGS84').fwd(lon, lat, true_azimuth, 1.)
        x2, y2 = transform.transform(lon2, lat2)
        expected = np.degrees(np.arctan2(x2 - x, y2 - y)) % 360
        self.assertAlmostEqual(result.azimuth.iloc[0], expected, places=5)
        self.assertGreater(abs(result.azimuth.iloc[0] - true_azimuth), 2.)
        with self.assertRaisesRegex(ValueError, 'Declare azimuth reference'):
            HELPER.extract_orientations(data, dem_path, dem_z_unit='m')

    def test_nonconformal_projection_rejects_simple_true_north_rotation(self):
        x, y = Transformer.from_crs('EPSG:4326', 'EPSG:3035', always_xy=True).transform(12., 50.)
        path = self.directory / 'equal-area.tif'
        with rasterio.open(path, 'w', driver='GTiff', height=3, width=3, count=1,
                           dtype='float32', crs='EPSG:3035', transform=from_origin(x - 15, y + 15, 10, 10)) as dem:
            dem.write(np.full((3, 3), 100, dtype='float32'), 1)
        data = gpd.GeoDataFrame({'formation': ['A'], 'dip': [30.], 'azimuth': [40.]},
                               geometry=[Point(12., 50.)], crs='EPSG:4326')
        with self.assertRaisesRegex(ValueError, 'locally conformal'):
            HELPER.extract_orientations(data, path, dem_z_unit='m', azimuth_reference='true-north')

    def test_missing_crs_labels_and_invalid_extent_fail(self):
        with self.assertRaisesRegex(ValueError, 'known CRS'):
            HELPER.extract_interfaces(self.contacts.set_crs(None, allow_override=True), self.dem, dem_z_unit='m')
        with self.assertRaisesRegex(ValueError, 'Missing columns'):
            HELPER.extract_interfaces(self.contacts.drop(columns='formation'), self.dem, dem_z_unit='m')
        with self.assertRaisesRegex(ValueError, 'Extent'):
            HELPER.clip_to_extent(self.contacts, [5, 1, 2, 3])

    def test_cli_real_geopackage_csv_readback_and_crs_assertion(self):
        source = self.directory / 'contacts.gpkg'
        self.contacts.to_crs('EPSG:4326').to_file(source, driver='GPKG')
        output = self.directory / 'output'
        command = [sys.executable, str(ROOT / 'gemgis/scripts/prepare_gempy_data.py'), '--contacts', str(source),
                   '--dem', str(self.dem), '--dem-z-unit', 'm', '--vertical-datum', 'synthetic local datum',
                   '--output-dir', str(output)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        table = pd.read_csv(output / 'interfaces.csv')
        np.testing.assert_array_equal(table.Z, [100, 110, 200, 210, 220])
        metadata = json.loads((output / 'spatial_metadata.json').read_text())
        self.assertEqual(metadata['crs'], 'EPSG:32632')
        self.assertEqual(metadata['xyz_units'], 'm')
        result = subprocess.run(command + ['--target-crs', 'EPSG:32633', '--output-dir', str(self.directory / 'wrong-crs')], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('must match DEM CRS', result.stderr)
        before = (output / 'interfaces.csv').read_bytes()
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('already contains', result.stderr)
        self.assertEqual((output / 'interfaces.csv').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
