# Frames, channel identities and array exports

## Unique channel access

`LogicalFile.find` performs regex matching by default; there is no `regex=True`
keyword. `LogicalFile.object` accepts `origin` and `copynr` to resolve a name.
The following function keeps the full fingerprint when returning a result:

```python
from dlisio import dlis

def find_channels(path, pattern='.*GR.*'):
    found = []
    with dlis.load(str(path)) as files:
        for logical in files:
            for channel in logical.find('CHANNEL', pattern):
                found.append((channel.fingerprint, channel.units, channel.dimension))
    return found
```

To request an exact match, use `logical.find('CHANNEL', 'GR', matcher=dlis.exact)`.
If multiple GR channels exist, inspect origin/copy number and choose the object;
do not arbitrarily take the first. In a frame, use
`records[channel.fingerprint]`. Generated dtype names such as `GR.0.1` are
convenient labels, while a fingerprint preserves full object identity.

## Shape and indexing

A channel with dimensions `[3, 2]` has an array shaped `(samples, 3, 2)` in the
structured frame data. Preserve its dimensional interpretation, units and
axis metadata. The first indexed channel is a depth or time coordinate according
to `frame.index_type`; do not infer it from a familiar mnemonic alone.

`frame.curves()` reads all curves efficiently once. `channel.curves()` is useful
for one channel, but repeatedly calling it for all channels duplicates I/O.
The input may contain missing/out-of-order frame numbers; investigate these
rather than replacing the recorded index with `arange`.

## Lossless numeric array sidecar

Continue with the `arrays` dictionary returned by `read_frame` in the entrypoint.
The keys retain channel fingerprints; write the metadata dictionary alongside
this NPZ using JSON if it contains only JSON-compatible metadata.

```python
import numpy as np

def save_arrays(path, arrays):
    if any(np.asarray(values).dtype.hasobject for values in arrays.values()):
        raise ValueError('Object arrays require an explicit safe serialization choice')
    np.savez_compressed(path, **arrays)
```

Read with `np.load(path, allow_pickle=False)`. Compression does not turn an array
channel into a LAS curve. Unknown missing markers remain untouched until a
vendor-specific rule is supplied. Converting NaN to LAS NULL is reversible only
when the output NULL value cannot also be a valid measurement.

[Official frame/curve API](https://dlisio.readthedocs.io/en/latest/dlis/api.html#dlisio.dlis.Frame.curves),
checked 2026-09-14. The synthetic tests exercise scalar/array separation and
channel identity; they do not cover all RP66 representation codes.
