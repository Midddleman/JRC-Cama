# Project Instructions

## Changelog

When making code changes, update the repository-root `CHANGELOG.md` only for
important changes that can affect scientific judgment, interpretation, or the
meaning of generated results.

Record changes such as:

- Changes to classification criteria, algorithms, data-processing logic, or
  quality/confidence rules.
- Changes to default thresholds or parameters when they alter the meaning or
  comparability of normal outputs.
- Changes to input data sources, spatial or temporal coverage, units,
  coordinate handling, aggregation methods, or output schemas.
- Bug fixes that can change previously generated results or conclusions.
- New analysis stages, validation methods, or major user-facing workflows.

Do not record:

- Temporary experimental parameter adjustments or one-off run values.
- Small numeric tuning that does not change the established default method or
  interpretation of results.
- Formatting, comments, renaming, cleanup, plotting cosmetics, or debug output.
- Read-only investigation, explanation, or test execution without a meaningful
  code change.

Use judgment when the boundary is unclear: record the change if a future reader
would need to know about it to correctly compare, reproduce, or interpret
results. Add the changelog entry in the same task as the code change. Keep
entries concise, put the newest entry first, and do not rewrite old entries
except to correct factual errors.

Each entry should state:

- The date and a short title.
- What changed and why it matters for interpretation or decisions.
- The main affected files or outputs.
- The relevant verification performed.
