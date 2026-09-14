Complete the task below in /workspace. This is one small evaluation; do not launch other agents or coding-agent CLIs. Read skill-catalog.json, select the relevant skill(s), and read their SKILL.md before implementation. The provided skills/ library is read-only. Use Python from PATH; lasio, segyio and NumPy are already installed. Do not install packages, download data, access credentials, or modify inputs. Write solution.py, execute it, and create the requested output. After your task checks pass, write evidence.json exactly once as {"selected_skills":["name"],"outputs":["filename"]}, then finish with a brief response. The evaluator already records actual tool commands: do not copy commands into evidence.json or add checks that document the evidence-writing process.

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
