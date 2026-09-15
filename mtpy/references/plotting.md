# MT response plotting

Read and QC the transfer function before plotting. This MTpy-v2 2.1.4 path is
executed by the bundled helper and regression suite:

```python
from mtpy import MT
import matplotlib.pyplot as plt

station = MT("station.edi")
station.read(get_elevation=False)
response = station.plot_mt_response(show_plot=False)
response.plot()
response.fig.savefig("response.png", dpi=150)
plt.close(response.fig)
```

For batch jobs, set `MPLBACKEND=Agg` and use a temporary `MPLCONFIGDIR` to avoid
user-specific plotting settings. Plot creation failure must fail a requested
plotting task. A response figure is a diagnostic, not a resolved depth model.

Check signed phases, component orientation, error bars and omitted or masked
values against the exported QC table. Retain native frequency coverage. The
library may display yx phases shifted by 180 degrees; the CSV keeps signed
component phases. Changes of display convention must not silently alter data.

Single-station response plots do not certify dimensionality or resolve strike.
Survey pseudosections, phase-tensor maps and induction vectors need survey
geometry, appropriate period selection and explicit angle/arrow conventions.
For those tasks use the installed-version
[imaging API](https://mtpy-v2.readthedocs.io/en/latest/mtpy.imaging.html), checking
its actual constructor arguments instead of importing v1 snippets.
