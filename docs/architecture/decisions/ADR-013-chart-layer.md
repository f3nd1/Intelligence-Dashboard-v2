# ADR-013: Chart layer — Insights vs computed

## Status
Accepted (2026-07-31)

## Context
The direction was to move every chart to Frappe Insights. Working through
all 113 charts showed that only some of them CAN be Insights charts.

## Options considered
1. Every chart through Insights; anything without a query renders empty.
2. Every chart through Insights where possible; the rest render from the
   criterion API, clearly labelled.
3. Keep the hand-rolled renderers everywhere.

## Decision
Option 2, taken by Felix after option 1 was built and its cost was visible.

## Rationale
An Insights query returns rows from a data source. 77 of the 113 charts
measure the criterion engine's own computed metric set — "Control Coverage"
is how many configured controls resolved; "Source Availability" is which
DocTypes the current user may read, which is per-request permission state,
not data. No query can express those. Option 1 would leave two thirds of the
dashboard permanently blank to satisfy a rule that turned out to be
unachievable. Option 3 abandons the migration.

## Consequences
- Two data engines, ONE renderer. Charts are badged "Insights" or
  "Computed live" so nobody has to guess which answered.
- The single-path rule still holds where it applies: a chart with a real
  Insights definition is answered by Insights or shows the failure — it
  never falls back.
- The hand-rolled per-type SVG renderers stay unreachable (ADR: Felix's
  Decision B), so "one renderer" is literal.
- 30 charts have authored Insights specs awaiting a bench build; 6 are
  verified; 77 are computed.

## Revisit triggers
Derived tables or views that make the composite measures queryable would
move charts from computed to Insights without changing the frontend.
