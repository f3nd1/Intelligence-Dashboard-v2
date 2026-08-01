# ADR-015: Sophia owns chart colour; it is not read from Insights

## Status

Accepted — 2026-08-02. Confirmed by Felix in the same exchange that produced
the finding below.

## Context

Sophia's criterion tabs embed `Insights Query v3` records. A Query carries data
and no presentation, which is why every embedded chart rendered as a table.
Chart type, axis assignment, axis labels and legend position live on a separate
`Insights Chart v3` record.

Reading that record was the obvious plan, and it works — for everything except
colour.

**The finding that forced this decision.** The live probe on 2026-08-02
(`docs/migration/scripts/probe_insights_chart_v3.py`) dumped all seven
`Insights Chart v3` records on the site in full. There is **no colour field, no
palette and no series colour on any of them.** The `config` JSON holds
`chart_type`, `x_axis`, `y_axis`, `legend_position`, `axis_label`, `stack`,
`limit`, `order_by` and `filters` — and nothing about colour.

Insights therefore applies a palette at render time from somewhere it does not
save on the document. So "read the colours from the Chart record" is not an
option that exists.

## Options considered

1. **Sophia's own palette.** A default stored in `UCC Intelligence Settings`,
   overridable per chart.
2. **Hardcode a palette matching Insights' current defaults**, presented as
   though it tracked Insights.
3. **Read Insights' frontend default at runtime**, by parsing the palette array
   out of its built JavaScript bundle.

## Decision

**Option 1.** The institution's default lives in
`UCC Intelligence Settings.chart_palette` (one hex value per line, blank for
the shipped default). A single chart on a single tab can override it, stored as
a `palette` key on that tab's chart entry in `UCC Analytics Tab.charts` —
institution-wide like every other tab setting, gated by the same write
permission, and written to the same audit trail as `chart_recoloured`.

**The shipped default was CHOSEN TO RESEMBLE Insights' current palette. It is
not read from Insights and will not track changes to it.**

That sentence is the point of this ADR. The divergence is a stated fact, not an
assumption for someone to trip over in a year.

## Rationale

Option 3 is the one that looks most correct and is the worst. Insights' built
assets are hash-named and rebuilt on every upgrade; a parser for them would
break silently, and "read the palette from their bundle" is really "recall
their source code" wearing a probe's clothes. It also introduces a runtime
dependency on another app's internals for a cosmetic value.

Option 2 is worse than option 1 while looking identical to it: same code, same
colours, but with a hidden claim that it matches Insights. The moment Insights
changes its palette, option 2 is quietly wrong and nothing says so. Option 1 is
the same code with the claim removed and an owner named.

Option 1 also gives UCC something the other two cannot: the ability to set an
institutional palette at all. These tabs are EduTrust evidence; a college that
wants its own colours on them should not have to ask Insights.

## Consequences

**Positive**
- Colour is testable, versioned and owned. `normalise_palette()` rejects
  anything that is not a hex value, so nothing arbitrary reaches the browser.
- Survives an Insights upgrade untouched.
- A per-chart override exists without a new DocType.

**Negative, and accepted**
- **The same chart can look different in Sophia and in Insights.** This is the
  real cost. It is accepted because the alternative is a hidden dependency, and
  because the figures are identical either way — only the colours differ.
- If Insights later starts storing colours on the Chart record, this decision
  should be revisited (see below). It will not self-correct.

**Operational**
- The setting is a Small Text somebody types into, so it is validated on read
  as well as on write: the stored value is re-validated every time it is used,
  because Desk lets an administrator edit it directly.

**Security**
- Palette values are hex-validated before they are interpolated into a `style`
  attribute. That check is not cosmetic — it is what stops a stored value from
  becoming markup.

## Revisit triggers

- An Insights upgrade adds a colour or palette field to `Insights Chart v3`.
  Re-run `probe_insights_chart_v3.py` after any Insights upgrade; section 2
  dumps the records in full and would show it.
- UCC decides the two systems must match exactly, in which case the honest
  implementation is still option 1 with the palette set by hand to match, not
  option 3.
