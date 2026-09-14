Complete the task below in /workspace using Python from PATH. This is one small evaluation: do not launch other coding-agent CLIs or additional agents. The scientific Python environment is already available; do not install packages or download data. Do not access credentials or modify the input files. Write solution.py, execute it, check the requested scientific outputs, and finish with a brief response. Do not create a separate evidence report; the evaluator records actual execution events.

# SEG-Y subset preserving geometry

Read `inputs/survey.sgy` without changing it. Write a reproducible `solution.py`
and execute it with the supplied Python environment. Produce `subset.sgy` with
all traces whose `INLINE_3D` is inclusively between 310 and 315, preserving their
original file order and every sample amplitude.

Preserve the text header, IEEE float sample format, binary sample interval and
sample count. For every selected trace preserve `INLINE_3D`, `CROSSLINE_3D`,
`CDP`, `SourceX`, `SourceY`, `SourceGroupScalar`, `CoordinateUnits`,
`DelayRecordingTime`, `TRACE_SAMPLE_COUNT`, and `TRACE_SAMPLE_INTERVAL`.
The input deliberately interleaves inline numbers; do not assume traces in the
requested interval occupy one contiguous slice. Input coordinates are stored
with their SEG-Y scalar, and the sample interval is expressed in microseconds.
