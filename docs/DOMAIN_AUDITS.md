# Domain API and scientific consistency audits

Checked on 2026-09-14 using isolated CPython 3.11 environments. These tests
execute actual Markdown Python blocks and real library calls, including binary
DLIS, GeoTIFF/GeoPackage, LAS and VTK readback. They are additional domain checks,
separate from portable-skill structure, installer and coding-agent evaluations.
Missing dependencies cause import failures; they do not count as skipped passes.

| Suite | Baseline | Tests | Verified result |
|---|---|---:|---|
| `test_dlis_examples.py` | `requirements-audits.txt` | 9 | RP66 file/frame selection, duplicate object identity, array shape, units, NaN/sentinel semantics, depth order/precision and LAS roundtrip |
| `test_gis_examples.py` | `requirements-audits.txt` | 10 | Vertex attributes, selected formation column, CRS conversion, DEM units/masks, dip/polarity, true/grid north, nonconformal rejection and CSV readback |
| `test_loopstructural_examples.py` | `requirements-audits.txt` | 6 | Constrained FDI/PLI models, world coordinates, asymmetric VTK point ordering, scalar/surface readback and failed exports |
| `test_petropy_examples.py` | `requirements-audits-petropy.txt` | 6 | Configured two-mineral/PVT evaluation, volume conservation, TVD/feet assumptions, missing masks, irregular interval accounting and LAS readback |

The domain audit adds 31 tests. It does not establish universal vendor-file
support, arbitrary geological configurations, all legacy PetroPy functions,
or that any coding agent completed an unsupervised scientific task.

## Reproduce in separate environments

From the repository root, create two new environments. Do not install these
baselines into a user's global environment or merge them with the core/model
baselines. The requirements pin the directly exercised scientific libraries
and compatibility-sensitive packages, not every transitive dependency.

```bash
python3.11 -m venv /tmp/geoscience-audits
/tmp/geoscience-audits/bin/python -m pip install -r tests/science/requirements-audits.txt
MPLBACKEND=Agg MPLCONFIGDIR=/tmp/geoscience-audits/mpl OPENBLAS_NUM_THREADS=1 /tmp/geoscience-audits/bin/python -m unittest discover -s tests/science -p test_dlis_examples.py -v
MPLBACKEND=Agg MPLCONFIGDIR=/tmp/geoscience-audits/mpl OPENBLAS_NUM_THREADS=1 /tmp/geoscience-audits/bin/python -m unittest discover -s tests/science -p test_gis_examples.py -v
MPLBACKEND=Agg MPLCONFIGDIR=/tmp/geoscience-audits/mpl OPENBLAS_NUM_THREADS=1 /tmp/geoscience-audits/bin/python -m unittest discover -s tests/science -p test_loopstructural_examples.py -v

python3.11 -m venv /tmp/geoscience-petropy-audit
/tmp/geoscience-petropy-audit/bin/python -m pip install -r tests/science/requirements-audits-petropy.txt
MPLBACKEND=Agg MPLCONFIGDIR=/tmp/geoscience-petropy-audit/mpl OPENBLAS_NUM_THREADS=1 /tmp/geoscience-petropy-audit/bin/python -m unittest discover -s tests/science -p test_petropy_examples.py -v
```

These are POSIX shell examples. On Windows use the environment's
`Scripts/python.exe` and set the three environment variables with the shell's
native syntax. The executed audit used Linux x86-64; this is not a Windows
scientific-stack validation. Matplotlib configuration is isolated, and VTK
checks require no interactive display.

The first baseline uses dlisio 1.0.4, dliswriter 1.2.0, GemGIS 1.1.9,
GeoPandas 1.1.4, Rasterio 1.4.4, LoopStructural 1.8.0, loop-interpolation 0.0.2,
PyVista 0.49.0 and lasio 0.32. The second uses PetroPy 0.1.6 with **lasio 0.30**:
0.32 removed `add_curve`, while older 0.23/0.29 fail with modern NumPy during
header parsing. `setuptools==80.9.0` preserves the legacy `pkg_resources`
dependency. `cchardet==2.2.0a2` has CPython 3.11 wheels; building the old 2.1.7
release on Python 3.11 failed. An index that omits prereleases cannot reproduce
that baseline; use an index providing the explicitly pinned release.

## Data provenance and independent expectations

The committed [DLIS fixture](../tests/fixtures/domain_audits/dlis/README.md) is
project-generated synthetic data under this repository's MIT license, with a
[checksum and expected decoded contents](../tests/fixtures/domain_audits/dlis/provenance.json).
No external well data is covered by inference from a software license. The
fixture uses actual RP66 records with two logical files and three frames,
including duplicate channel names distinguished by origin and a four-value
array channel. Extra invalid/precision variants are generated temporarily.

GIS tests write small deterministic rasters and vectors to temporary files.
Known cell elevations, vertex labels and projected locations are checked
independently. True-north conversion is compared with a geodesic direction
projected into UTM; a nonconformal equal-area projection is rejected rather
than incorrectly applying a simple rotation. The helper assumes elevations
already share a documented vertical datum; it converts units but does not
transform that datum or infer magnetic declination.

LoopStructural tests use a fully specified plane with nonzero origin and an
asymmetric extent. Expected scalar values and level-set locations are known
analytically, so empty or wrongly ordered grids cannot pass merely because a
VTK file exists. FDI/PLI residual tolerances reflect numerical discretization.
Fault networks, fold frames, interactive rendering, uncertainty ensembles and
arbitrary field constraints are not validated by the planar case.

PetroPy tests generate a known 65% quartz + 15% calcite + 20% water-filled pore
mixture, forward-compute density/neutron/resistivity, then execute the actual
configured fluid and multimineral routines. Recovered fractions, bulk/pore
volume closure and water partitioning have independent physical expectations.
Fluid responses are used in the synthetic forward construction, so the tests
establish consistency, not empirical PVT accuracy on a reservoir. The example
explicitly uses calcite density 2.71 g/cm³ and a vertical-well TVD basis; it is
not a field default. NaNs, the excluded bottom sample, and unknown interval
thickness remain identifiable. Gas, organic-rich/shaly calibrations, custom
permeability, electrofacies and plotting remain separate verification tasks.

## Upstream sources

Sources were checked against the installed versions on 2026-09-14:

- [dlisio DLIS API](https://dlisio.readthedocs.io/en/latest/dlis/api.html) and [dliswriter source](https://github.com/well-id/dliswriter).
- [GemGIS source](https://github.com/cgre-aachen/gemgis), [Rasterio sampling](https://rasterio.readthedocs.io/en/stable/api/rasterio.sample.html), and [PyProj projection factors](https://pyproj4.github.io/pyproj/stable/api/proj.html#pyproj.Proj.get_factors).
- [LoopStructural model implementation](https://github.com/Loop3D/LoopStructural/blob/master/LoopStructural/modelling/core/geological_model.py).
- [PetroPy implementation and parameter definitions](https://github.com/toddheitmann/PetroPy/blob/master/petropy/log.py).
