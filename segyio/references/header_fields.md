# SEG-Y Trace Header Fields

## Table of Contents
- [Commonly Used Fields](#commonly-used-fields)
- [Coordinate Fields](#coordinate-fields)
- [Geometry Fields](#geometry-fields)
- [Time and Sampling Fields](#time-and-sampling-fields)
- [Source/Receiver Fields](#sourcereceiver-fields)
- [All Trace Header Fields](#all-trace-header-fields)

## Commonly Used Fields

| segyio Field | Bytes | Type | Description |
|--------------|-------|------|-------------|
| `TRACE_SEQUENCE_LINE` | 1-4 | int32 | Trace sequence number within line |
| `TRACE_SEQUENCE_FILE` | 5-8 | int32 | Trace sequence number within file |
| `FieldRecord` | 9-12 | int32 | Original field record number |
| `TraceNumber` | 13-16 | int32 | Trace number within original field record |
| `CDP` | 21-24 | int32 | Ensemble number (CDP, CMP, etc.) |
| `TRACE_SAMPLE_COUNT` | 115-116 | int16 | Number of samples in this trace |
| `TRACE_SAMPLE_INTERVAL` | 117-118 | int16 | Sample interval (microseconds) |

## Coordinate Fields

| segyio Field | Bytes | Type | Description |
|--------------|-------|------|-------------|
| `SourceX` | 73-76 | int32 | Source coordinate X |
| `SourceY` | 77-80 | int32 | Source coordinate Y |
| `GroupX` | 81-84 | int32 | Receiver group coordinate X |
| `GroupY` | 85-88 | int32 | Receiver group coordinate Y |
| `CDP_X` | 181-184 | int32 | X coordinate of ensemble (CDP) |
| `CDP_Y` | 185-188 | int32 | Y coordinate of ensemble (CDP) |
| `SourceGroupScalar` | 71-72 | int16 | Scalar for coordinates (if negative, divide) |

### Coordinate Scaling

Coordinates are stored as integers. Apply the scalar from bytes 71-72:
```python
scalar = header[segyio.TraceField.SourceGroupScalar]
if scalar < 0:
    x = header[segyio.TraceField.CDP_X] / abs(scalar)
else:
    x = header[segyio.TraceField.CDP_X] * scalar
```

## Geometry Fields

| segyio Field | Bytes | Type | Description |
|--------------|-------|------|-------------|
| `INLINE_3D` | 189-192 | int32 | Inline number (3D surveys) |
| `CROSSLINE_3D` | 193-196 | int32 | Crossline number (3D surveys) |
| `ShotPoint` | 197-200 | int32 | Shotpoint number |
| `offset` | 37-40 | int32 | Source-receiver offset |

### Opening 3D Files

Specify inline/crossline byte positions when opening:
```python
# Standard locations (bytes 189 and 193)
with segyio.open('file.sgy', iline=189, xline=193) as f:
    ...

# Non-standard locations (check headers first)
with segyio.open('file.sgy', iline=9, xline=21) as f:
    ...
```

## Time and Sampling Fields

| segyio Field | Bytes | Type | Description |
|--------------|-------|------|-------------|
| `DelayRecordingTime` | 109-110 | int16 | Delay recording time (ms) |
| `TRACE_SAMPLE_COUNT` | 115-116 | int16 | Number of samples |
| `TRACE_SAMPLE_INTERVAL` | 117-118 | int16 | Sample interval (microseconds) |

## Source/Receiver Fields

| segyio Field | Bytes | Type | Description |
|--------------|-------|------|-------------|
| `EnergySourcePoint` | 17-20 | int32 | Energy source point number |
| `SourceDepth` | 49-52 | int32 | Source depth below surface |
| `ReceiverDatumElevation` | 53-56 | int32 | Datum elevation at receiver group |
| `SourceDatumElevation` | 57-60 | int32 | Datum elevation at source |
| `SourceWaterDepth` | 61-64 | int32 | Water depth at source |
| `GroupWaterDepth` | 65-68 | int32 | Water depth at receiver group |

## All Trace Header Fields

Complete list of segyio.TraceField constants:

```python
import segyio

# Print all available fields
for field in segyio.TraceField.enums():
    print(f"{field.name}: bytes {int(field)}")
```

| segyio Constant | Byte Position |
|-----------------|---------------|
| `TRACE_SEQUENCE_LINE` | 1 |
| `TRACE_SEQUENCE_FILE` | 5 |
| `FieldRecord` | 9 |
| `TraceNumber` | 13 |
| `EnergySourcePoint` | 17 |
| `CDP` | 21 |
| `CDP_TRACE` | 25 |
| `TraceIdentificationCode` | 29 |
| `NSummedTraces` | 31 |
| `NStackedTraces` | 33 |
| `DataUse` | 35 |
| `offset` | 37 |
| `ReceiverGroupElevation` | 41 |
| `SourceSurfaceElevation` | 45 |
| `SourceDepth` | 49 |
| `ReceiverDatumElevation` | 53 |
| `SourceDatumElevation` | 57 |
| `SourceWaterDepth` | 61 |
| `GroupWaterDepth` | 65 |
| `ElevationScalar` | 69 |
| `SourceGroupScalar` | 71 |
| `SourceX` | 73 |
| `SourceY` | 77 |
| `GroupX` | 81 |
| `GroupY` | 85 |
| `CoordinateUnits` | 89 |
| `WeatheringVelocity` | 91 |
| `SubWeatheringVelocity` | 93 |
| `SourceUpholeTime` | 95 |
| `GroupUpholeTime` | 97 |
| `SourceStaticCorrection` | 99 |
| `GroupStaticCorrection` | 101 |
| `TotalStaticApplied` | 103 |
| `LagTimeA` | 105 |
| `LagTimeB` | 107 |
| `DelayRecordingTime` | 109 |
| `MuteTimeStart` | 111 |
| `MuteTimeEND` | 113 |
| `TRACE_SAMPLE_COUNT` | 115 |
| `TRACE_SAMPLE_INTERVAL` | 117 |
| `GainType` | 119 |
| `InstrumentGainConstant` | 121 |
| `InstrumentInitialGain` | 123 |
| `Correlated` | 125 |
| `SweepFrequencyStart` | 127 |
| `SweepFrequencyEnd` | 129 |
| `SweepLength` | 131 |
| `SweepType` | 133 |
| `SweepTraceTaperLengthStart` | 135 |
| `SweepTraceTaperLengthEnd` | 137 |
| `TaperType` | 139 |
| `AliasFilterFrequency` | 141 |
| `AliasFilterSlope` | 143 |
| `NotchFilterFrequency` | 145 |
| `NotchFilterSlope` | 147 |
| `LowCutFrequency` | 149 |
| `HighCutFrequency` | 151 |
| `LowCutSlope` | 153 |
| `HighCutSlope` | 155 |
| `YearDataRecorded` | 157 |
| `DayOfYear` | 159 |
| `HourOfDay` | 161 |
| `MinuteOfHour` | 163 |
| `SecondOfMinute` | 165 |
| `TimeBaseCode` | 167 |
| `TraceWeightingFactor` | 169 |
| `GeophoneGroupNumberRoll1` | 171 |
| `GeophoneGroupNumberFirstTraceOrigField` | 173 |
| `GeophoneGroupNumberLastTraceOrigField` | 175 |
| `GapSize` | 177 |
| `OverTravel` | 179 |
| `CDP_X` | 181 |
| `CDP_Y` | 185 |
| `INLINE_3D` | 189 |
| `CROSSLINE_3D` | 193 |
| `ShotPoint` | 197 |
| `ShotPointScalar` | 201 |
| `TraceValueMeasurementUnit` | 203 |
| `TransductionConstantMantissa` | 205 |
| `TransductionConstantPower` | 209 |
| `TransductionUnit` | 211 |
| `TraceIdentifier` | 213 |
| `ScalarTraceHeader` | 215 |
| `SourceType` | 217 |
| `SourceEnergyDirectionMantissa` | 219 |
| `SourceEnergyDirectionExponent` | 223 |
| `SourceMeasurementMantissa` | 225 |
| `SourceMeasurementExponent` | 229 |
| `SourceMeasurementUnit` | 231 |
| `UnassignedInt1` | 233 |
| `UnassignedInt2` | 237 |

## Binary Header Fields

Access via `f.bin[segyio.BinField.FieldName]`:

| Field | Bytes | Description |
|-------|-------|-------------|
| `JobID` | 3201-3204 | Job identification number |
| `LineNumber` | 3205-3208 | Line number |
| `ReelNumber` | 3209-3212 | Reel number |
| `Traces` | 3213-3214 | Traces per ensemble |
| `AuxTraces` | 3215-3216 | Auxiliary traces per ensemble |
| `Interval` | 3217-3218 | Sample interval (microseconds) |
| `IntervalOriginal` | 3219-3220 | Original sample interval |
| `Samples` | 3221-3222 | Samples per trace |
| `SamplesOriginal` | 3223-3224 | Original samples per trace |
| `Format` | 3225-3226 | Data sample format code |
| `EnsembleFold` | 3227-3228 | Ensemble fold |
| `SortingCode` | 3229-3230 | Trace sorting code |
