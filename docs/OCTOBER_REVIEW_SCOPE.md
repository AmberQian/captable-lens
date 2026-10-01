# October 2026 compute frontloading: first reversible slice

Baseline: upstream main commit ca18fcc747272b92bc8de91c77dc3ac808bc22ef.
Selected project: CapTable Lens reliability and reusable Agent evaluation boundary.
Repository inspection found only main and no issues/open PRs for this repository.

Implemented:
- Conservative annual companyfacts extraction instead of filing-order sampling.
- Comparable prior annual period and newest restatement handling.
- Matched-period FCF and same-date debt-component aggregation.
- Pure scoring (input flags are no longer changed).
- Offline JSON evaluation with finite numeric validation and review status.
- Seven reliability regressions and a documented interface.

Validation: seven unittest regressions, six pre-existing test functions executed
directly (pytest is absent), demo rendering, and JSON CLI success/error subprocess checks.
No live SEC calls or paid-model calls were performed.

Next substantial slice: financing-event lifecycle and deduplication, traceable
metric provenance, filing evidence fixtures, and evaluated structured extraction.
Those require further implementation; this PR does not claim completion of the full upgrade.
