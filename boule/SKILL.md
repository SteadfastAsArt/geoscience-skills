---
name: boule
description: Calculate reference-ellipsoid geometry, normal gravity and geodetic/geocentric coordinate conversions with Boule. Use for gravity reference corrections and planetary ellipsoids; this does not transform between geodetic datums or compute terrain corrections.
license: MIT
metadata:
  version: "1.0.0"
  author: Geoscience Skills
  skill_type: domain
  tags: '["Geodesy", "Gravity", "Reference Ellipsoid"]'
  dependencies: '["boule==0.6.0"]'
  complements: '["harmonica", "ensaio", "verde"]'
  workflow_role: processing
---

# Boule

Use the ellipsoid and coordinate convention attached to the actual observations.
An ellipsoid is a reference surface; choosing WGS84 does not transform coordinates
from another datum or reference epoch.

## Inputs and conventions

For the 0.6 API, coordinates are a tuple `(longitude, latitude, height)` for
geodetic input: angles in degrees, ellipsoidal height in metres. Spherical input
uses geocentric latitude and radius in metres, not elevation. Orthometric height
above a geoid requires a separate geoid model before use as ellipsoidal height.

Choose an existing ellipsoid such as `WGS84` or `GRS80` from source metadata, or
define a documented body with consistent parameters. Do not infer the ellipsoid
from a column merely called `height`.

## Gravity and coordinate conversion

```python
# example: ellipsoid-gravity
import numpy as np
import boule

longitude_deg = np.array([0.0, 10.0, 0.0])
latitude_deg = np.array([0.0, 45.0, 90.0])
height_m = np.zeros(3)
geodetic = (longitude_deg, latitude_deg, height_m)
gravity_mgal = boule.WGS84.normal_gravity(geodetic)
gravity_si = boule.WGS84.normal_gravity(geodetic, si_units=True)
spherical = boule.WGS84.geodetic_to_spherical(geodetic)
roundtrip = boule.WGS84.spherical_to_geodetic(spherical)
```

Default gravity is mGal: 1 mGal = 10⁻⁵ m/s². At zero height, reference gravity is
about 9.7803253 m/s² at the equator and 9.8321849 m/s² at the poles. Mid-latitude
geocentric latitude differs from geodetic latitude. Check both units and limits.

## Applying corrections

Specify whether the requested quantity is observed gravity, normal gravity,
disturbance or anomaly, with its height and sign convention. Subtraction of normal
gravity alone is not a Bouguer, terrain or tide correction. Preserve instrument
units and datum/epoch provenance through any handoff to a potential-field model.

Read the [normal gravity guide](https://www.fatiando.org/boule/latest/user_guide/normal_gravity.html)
and [API](https://www.fatiando.org/boule/latest/api/index.html) for the selected body.
