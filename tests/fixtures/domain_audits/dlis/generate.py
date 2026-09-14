"""Project-owned synthetic RP66 fixture; no third-party measurements.

dliswriter requires unique data keys. Equal-length channel labels are replaced
after serialization to encode two same-named objects with different origins.
String lengths and all numeric payloads remain unchanged. dlisio validates the
result as an ordinary DLIS physical file; no reader is mocked or patched.
"""
from datetime import datetime, timezone
from pathlib import Path
import tempfile

from dliswriter import DLISFile, enums
import numpy as np


def generate(path, depths=None, unit='m', index_type=None):
    depth = np.asarray([1000, 1000.5, 1001.5, 1002] if depths is None else depths, dtype=float)
    if len(depth) != 4:
        raise ValueError('Fixture requires four depth samples')
    file = DLISFile()
    logical = file.add_logical_file()
    logical.add_origin('SYNTHETIC', well_name='Project synthetic audit',
                       creation_time=datetime(2026, 9, 14, tzinfo=timezone.utc))
    d = logical.add_channel('DEPTH', data=depth, units=unit)
    a = logical.add_channel('GAMMA_A', data=np.array([10., -999.25, np.nan, 40.]),
                            units='gAPI', origin_reference=1)
    b = logical.add_channel('GAMMA_B', data=np.array([11., 22., 33., 44.]),
                            units='gAPI', origin_reference=2)
    image = logical.add_channel('IMAGE', data=np.arange(16., dtype=float).reshape(4, 4), units='mV')
    logical.add_frame('MAIN', channels=(d, a, b, image),
                      index_type=index_type or enums.FrameIndexType.BOREHOLE_DEPTH)
    # A second frame and logical file make selection observable.
    d2 = logical.add_channel('DEPTH2', data=depth, units=unit)
    g2 = logical.add_channel('GAMMA2', data=np.array([11., 22., 33., 44.]), units='gAPI')
    logical.add_frame('SECOND', channels=(d2, g2), index_type=enums.FrameIndexType.BOREHOLE_DEPTH)
    file.write(str(path))
    other_file = DLISFile()
    other = other_file.add_logical_file()
    other.add_origin('OTHER', well_name='Separate synthetic logical file',
                     creation_time=datetime(2026, 9, 14, tzinfo=timezone.utc))
    other_d = other.add_channel('DEPTH', data=np.array([20., 21., 22., 23.]), units='ft')
    other_gr = other.add_channel('GR', data=np.array([101., 102., 103., 104.]), units='gAPI')
    other.add_frame('OTHER', channels=(other_d, other_gr), index_type=enums.FrameIndexType.BOREHOLE_DEPTH)
    path = Path(path)
    data = path.read_bytes()
    for label in (b'GAMMA_A', b'GAMMA_B'):
        if data.count(label) < 2:
            raise RuntimeError('Expected channel definition and frame reference')
        data = data.replace(label, b'GAMMA_X')
    # One storage-unit label, followed by two independently encoded logical
    # files. Strip only the second 80-byte RP66 storage-unit label.
    with tempfile.TemporaryDirectory() as directory:
        second = Path(directory) / 'second.dlis'
        other_file.write(str(second))
        second_data = second.read_bytes()
        if data[4:9] != b'V1.00' or second_data[4:9] != b'V1.00':
            raise RuntimeError('Unexpected RP66 storage-unit label')
        data += second_data[80:]
    path.write_bytes(data)
    return path


if __name__ == '__main__':
    generate(Path(__file__).with_name('synthetic.dlis'))
