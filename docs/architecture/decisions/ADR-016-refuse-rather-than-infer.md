# ADR-016: Refuse rather than infer — chart axes, config keys, and undrawable types

## Status

Accepted — 2026-08-03. Decided autonomously during an overnight round, under a
standing instruction to decide rather than stall. Felix's own steer on the
first case was "refusing is probably right, but you decide."

## Context

Three separate questions came up in one round, and they turned out to be the
same question wearing three hats:

1. **A Chart with no `x_axis` set.** Sophia refuses to draw and says so. Should
   it instead fall back to the Query's own summarize dimension?
2. **Builder controls with unknown config keys.** The v3 chart builder exposes
   Rotate Values, Overlap, Normalize, Show Data Labels, the Show Axis Label
   toggle, Show Scrollbar, Y-Min, Y-Max and Split Series. The live probe
   confirmed only six keys. The UI labels suggest obvious key names.
3. **Chart types Sophia cannot draw.** Map, Bubble and Sankey are real v3
   types with no renderer here.

In each case there is an inference available that would be right most of the
time, and a refusal that is right every time.

## Decision

**Refuse, in all three.**

1. **No `x_axis` → no chart.** The card falls back to the table and names the
   controls to set: *"Open it in Insights, set X Axis Column and Y Axis
   Series."*
2. **No confirmed key → no implementation.**
   `docs/migration/scripts/probe_insights_chart_config.py` was written to
   establish the real names. Nothing is read until it has run.
3. **No honest renderer → labelled table.** Map, Bubble and Sankey keep saying
   their rows are shown instead. Funnel was built, because an ordered
   label/value series IS a funnel and nothing has to be invented.

## Rationale

**The summarize dimension is not the x-axis.** It is what the query *grouped
by*; `x_axis` is what the author *chose to plot*. They usually coincide, and
there is no way to detect when they do not — a two-dimension query, or one
where the author deliberately plotted the second, would silently draw the wrong
chart with no signal that anything was wrong.

**Inference also hides the unfinished state.** Felix built four charts without
setting their axes. Under a fallback he would have seen four plausible charts
and never learned they were misconfigured. Under a refusal he saw four
messages, went to Insights, and fixed them. The refusal was the more useful
behaviour, not merely the safer one.

**A UI label is not a field name.** Guessing `rotate_values` from "Rotate
Values" is precisely the class of guess that produced 13 `TableNotFound`
errors earlier in this migration, where an operations shape was written from
plausibility rather than copied from something proven on a bench. The cost of
being wrong is not a missing feature; it is a feature that appears to work.

**A wrong diagram is read as fact.** This is the asymmetry that decides case 3.
A table is understood as raw rows and invites scrutiny. A chart is understood
as a finding. Drawing a "map" that is really a list of place names, or a
"bubble chart" with two of its three dimensions invented, would misrepresent
institutional data on a dashboard used as EduTrust evidence. The fallback is
not a degraded chart — it is a real view of real rows, plus an honest sentence
about why it is not a diagram.

## Consequences

**Positive**
- Nothing on a criterion tab is ever drawn from a value nobody chose.
- Unfinished configuration is visible instead of disguised.
- Every refusal names the thing to do next, so it is actionable rather than
  merely correct.

**Negative, and accepted**
- More states where a card shows a table than a system that guessed would have.
  Accepted: each one states its reason, and the rows are real.
- Sophia will not match Insights visually for Map, Bubble or Sankey. Accepted
  for the same reason.
- Extending presentation now needs a bench round trip. Accepted: that is the
  cost of not guessing, and it is one probe.

**Operational**
- `probe_insights_chart_config.py` needs a chart with those controls actually
  changed from their defaults, or it will report nothing useful. Its own
  output says so.

## Revisit triggers

- The probe returns real key names → implement those controls, from the output.
- Sophia's series contract gains multiple measures per category → Bubble and
  stacking become expressible, and both should be revisited together.
- A geographic library is approved for this app → Map becomes possible; until
  then it stays a refusal, not a backlog item.
