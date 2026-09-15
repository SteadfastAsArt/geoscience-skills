"""Project-owned synthetic MALA bytes; no third-party observations or noise."""
import json
from pathlib import Path
import struct


def generate(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    samples, traces = 64, 9
    # A known impulse at sample 32 and trace-dependent DC/digital amplitude.
    values = [[1000 + 3 * trace + (3000 + 10 * trace if sample == 32 else 0)
               for sample in range(samples)] for trace in range(traces)]
    (directory / 'controlled.rd3').write_bytes(struct.pack('<' + 'h' * (samples * traces),
                                                       *(v for trace in values for v in trace)))
    (directory / 'controlled.rad').write_text(
        'SAMPLES:64\nTIMEWINDOW:157.5\nDISTANCE INTERVAL:0.25\nANTENNA SEPARATION:0\n')
    metadata = {'sample_interval_ns': 2.5, 'time_origin_ns': 0.0,
                'trace_spacing_m': 0.25, 'profile_origin_m': 0.0,
                'horizontal_crs': None, 'vertical_reference': 'Synthetic local zero-offset profile',
                'source_note': 'Project-generated little-endian int16 MALA layout; TIMEWINDOW explicitly denotes last sample time 63*2.5 ns in this controlled fixture. Local trace positions 0:0.25:2 m; not a field survey.'}
    path = directory / 'controlled_sampling.json'
    path.write_text(json.dumps(metadata, indent=2) + '\n')
    return directory / 'controlled.rad', path, values
