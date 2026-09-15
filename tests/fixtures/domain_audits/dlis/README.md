# Synthetic DLIS audit fixture

`synthetic.dlis` contains project-created observations, not field measurements.
The fixture, numeric arrays, generator and descriptions are licensed under the
repository's MIT license. No third-party DLIS file is redistributed; the
writer's software license is not being used to infer rights over external data.
`provenance.json` records the committed binary's checksum and expected values.

Generate with the isolated domain-audit environment:

```bash
python tests/fixtures/domain_audits/dlis/generate.py
```

The generator uses dliswriter 1.2.0 to encode actual RP66 records. Each channel
belongs to one frame. It writes two independent logical files and appends the
second file's records after removing its 80-byte storage-unit label, producing
one physical file. Equal-length ASCII channel labels are replaced to exercise
two objects with identical mnemonics and different origin identifiers. Numeric
payload bytes and encoded string lengths are unchanged by this replacement.
The fixture is read by dlisio 1.0.4 without reader mocks or relaxed parsing.

The principal frame includes irregular metre depth, two same-named gamma
channels, one NaN, a legitimate −999.25 observation and an array channel with
four values per sample. A second frame and a separate logical file with feet
depth ensure selection is tested instead of accidental concatenation. Tests
also generate descending/duplicate/time-axis and fine-precision cases in a
temporary directory. A four-element array channel verifies a retained trailing
dimension; arbitrary vendor image geometries are not covered.

Regeneration can change writer metadata bytes; compare decoded invariants and
update the committed checksum deliberately rather than assuming all generated
DLIS files are byte-identical. Synthetic format coverage does not establish
compatibility with every vendor record or damaged file.

Writer source: https://github.com/well-id/dliswriter (MIT software).
Reader API: https://dlisio.readthedocs.io/en/latest/dlis/api.html.
Checked 2026-09-14.
