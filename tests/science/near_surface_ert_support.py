"""Normalize existing licensed field observations; no new or fabricated field data."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from field_case_support import verify_case


GEOMETRY_NOTE = ('Crescentino first station, Zenodo 18183049 v1, CC BY 4.0. '
                 'Instrument nominal local x positions in metres; original surveyed coordinates '
                 'are EPSG:32632 with no supplied elevations. A flat nominal line is an explicit '
                 'diagnostic simplification; no georeferenced zero-elevation surface is invented.')


def prepare_field_inputs(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    fixture, provenance = verify_case('ert_survey')
    original = pd.read_csv(fixture / 'Resistivity_data.csv.gz').iloc[:318].copy()
    if not np.array_equal(original.meas_num, np.arange(1, 319)):
        raise ValueError('Unexpected first-station acquisition ordering')
    columns = {'meas_num': 'measurement_id', 'A': 'a', 'B': 'b', 'M': 'm', 'N': 'n',
               'Rho(Ohm*m)': 'rhoa_ohm_m', 'St.Dev.(%)': 'repeatability_pct',
               'V_MN(mV) ': 'voltage_mV', 'I_AB(mA)': 'current_mA'}
    original.rename(columns=columns).to_csv(directory / 'observations.csv', index=False, float_format='%.17g')
    pd.DataFrame({'electrode_id': np.arange(1, 14),
                  'x_m': provenance['nominal_electrode_x_m']}).to_csv(directory / 'electrodes.csv', index=False)
    (directory / 'source.json').write_text(json.dumps({'source_provenance': provenance,
        'selection': 'First 318 acquisition records; no target-dependent selection',
        'conversion': 'Rename columns only; retain original measurement units and additional columns',
        'geometry_note': GEOMETRY_NOTE}, indent=2) + '\n')
    return directory / 'observations.csv', directory / 'electrodes.csv'
