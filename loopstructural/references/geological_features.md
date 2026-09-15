# Conditional fault and fold modelling

## Faults

A fault needs geometry, displacement, slip direction and influence extent in a
consistent coordinate system. In 1.8.0, `create_and_add_fault` requires a
`displacement` argument. Calling it with just a feature name does not define a
working fault model. Set whether displacement describes throw, net slip or a
model parameter and reconcile it with the selected slip vector/convention.

Construct the fault before affected foliations, verify the fault frame and
which features receive it, then test corresponding points on both sides.
Fault chronology and network interactions are geological inputs; dictionary
insertion order alone is not a validated geological history. The CSV helper
intentionally handles foliations only and rejects a supplied fault table.

## Folds

A fold frame requires spatial constraints on its component coordinates. A
string containing a frame name is not a substitute for a configured frame
object. Folded foliations also need fold orientation/rotation information and
sufficient observations. Inspect the installed `create_and_add_fold_frame`
and `create_and_add_folded_foliation` signatures and follow an upstream example
with data matching the intended fold assumptions.

The domain audit does not execute a configured fault/fold model. These are
selection and setup requirements, not a claimed runnable fault tutorial.

## Ensembles

LoopStructural model construction does not automatically quantify geological
uncertainty. Specify uncertain observations/parameters and sampling priors,
rebuild an ensemble, and separate numerical variation from geological
uncertainty. Preserve each member's configuration and random seed.

[Official fault/fold model API source](https://github.com/Loop3D/LoopStructural/blob/master/LoopStructural/modelling/core/geological_model.py),
checked 2026-09-14. Consult version-matched upstream examples before extending
the tested foliation path.
