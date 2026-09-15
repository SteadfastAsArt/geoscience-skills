---
name: cross-validation-reviewer
description: >-
  Review geoscience model validation for spatial, temporal and grouped leakage,
  independence of reference data, fair baselines and uncertainty claims. Use
  when judging predictive or inversion-validation evidence, not as a required
  gate for ordinary data loading.
---

# Cross-validation Reviewer

This is an optional Markdown role guide, not a portable subagent registration.
A single agent may apply it directly; do not require delegation or an unavailable
companion skill to finish a review.

## Establish what the evaluation is meant to predict

Identify the prediction target, its units/support, deployment location/time,
available predictors and the independent observational unit. A sample, trace,
well, station, survey line and site are different grouping units. Record whether
the claim concerns interpolation, an unseen location, future observations,
physical forward modelling, or inversion recovery.

Request the split membership, preprocessing/fitting sequence, metric definitions
and data lineage needed to assess that claim. If unavailable, state that the
independence claim is unverified and review the evidence that is present; do not
invent missing folds or treat a training fit as held-out performance.

## Inspect leakage at the operation where it can occur

- **Time:** forecasts cannot use future measurements, centred filters spanning
  the boundary, future-fitted climatologies or target aggregates crossing the
  split. Include response warmup and feature/target lookback in the split design.
- **Space:** keep correlated locations in suitable blocks or buffers when the
  claim is transfer away from observed sites. Evaluate split distances in a
  meaningful CRS; random neighbouring points can make an easy test misleading.
- **Groups:** repeated measurements, duplicated traces, windows from the same
  event and samples from the same well should follow the deployment grouping.
  A same-station future forecast and an unseen-station forecast need different
  splits; grouping is a decision, not a universal prohibition.
- **Fitted processing:** learn imputation, scaling, feature selection, variograms,
  trends, regularisation and hyperparameters on training data. Use inner folds
  for tuning and preserve the outer evaluation set. A physically specified unit
  conversion does not need fitting, but document its datum/scale provenance.
- **Reference data:** boreholes or models used to choose priors are not independent
  validation observations. Reusing one solver/discretisation for synthetic data
  generation and inversion can make recovery unrealistically easy; disclose it
  and test perturbations or independent forward discretisations when relevant.

## Judge the evidence and propose the smallest repair

Check metrics in physical units and by scientifically relevant subgroup, against
a suitable baseline. Inspect failure cases and coverage/extrapolation, not only
an aggregate score. Uncertainty should reflect dependent observations, model
choices and measurement error where the claim requires them; a narrow fitted
parameter interval is not automatically prediction uncertainty.

For each finding, report the claim affected, concrete data/code/split evidence,
severity, and a repair with a measurable acceptance check. Separate demonstrated
leakage from a plausible issue requiring missing evidence. Do not discard data,
change published metrics or rerun expensive models without the task's existing
authorization. Structural checks and a review of this guide alone do not certify
a model's scientific validity.
