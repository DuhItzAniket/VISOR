# VISOR development rules

- Read `docs/IMPLEMENTATION_STATUS.md` and `docs/IMPROVEMENT_PLAN.md` before changing the project.
- Keep vision algorithms independent of Qt; use typed domain results across layers.
- Never turn a failed fit into a successful localization using unverified correspondences or invented metrics.
- A fitted transform and an accurate localization are different claims. Ground-truth error requires ground truth.
- Preserve descriptor-specific matching norms and classical regression fixtures. Explain intentional correctness changes.
- Optional learned dependencies must remain optional; core validation must work without model downloads.
- Keep expensive processing off the UI thread. Cancellation must be cooperative and observable.
- Update the implementation log, status, and improvement task ledger with each completed task and its verification evidence.
- Run focused regressions for changed behavior, then the relevant suite and lint/build checks.
- Use focused commits on `main`, push verified work, and report push failures accurately.
- Do not commit credentials, local environments, downloaded weights, caches, or generated builds.
