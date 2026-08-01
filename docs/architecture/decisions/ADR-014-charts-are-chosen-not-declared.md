# ADR-014: Charts are chosen, not declared

## Status
Accepted (2026-08-01). Supersedes ADR-013.

## Context
ADR-013 settled how the platform's 113 declared charts should be answered.
Building it out to the actual screen showed the declarations were the problem.

Counting the boxes the page really renders: **222** across the seven criteria,
from a 209-entry `LIVE_VISUAL_EXPANSION` table plus each section's CONFIG
charts. **16** had a bench-verified Insights query behind them; 9 of those 16
had no box on any visible tab, because the expansion table *replaced* the
CONFIG charts rather than adding to them. So the shipped dashboard offered
about 200 boxes that showed nothing, and hid most of what did work.

Every one of those boxes was invented by this app — a title someone wrote in a
config file, hoping a query would exist for it one day. None was asked for by
the person looking at the tab.

## Options considered
1. Keep the declared boxes; keep authoring queries until the blanks fill in.
2. Keep the declared boxes but hide any that are blank.
3. Delete the declarations. Give each tab a "+ Add chart" button and let the
   person embed real Insights charts they can already read.

## Decision
Option 3, decided by Felix.

## Rationale
Option 1 is 200 more queries to author, review and verify, against titles
nobody chose — and the previous rounds showed how that goes: a spec written
from a guessed field name resolves to `docstatus` and renders one bar labelled
"0". Option 2 makes the tab shorter without making it useful, and still leaves
the app maintaining a registry of charts that do not exist.

Option 3 removes the whole class of problem. There is nothing to declare, so
nothing can be declared and then not exist. What appears on a tab is what
someone put there, and it is real by construction: it came from Insights, and
they could already read it.

## Consequences
- **Deleted**, not left unreached: `chart_registry.py` (113 entries),
  `chart_definitions.py`, `chart_service.py`, `LIVE_VISUAL_EXPANSION`, the
  chart-card markup, the fifteen hand-rolled SVG renderers and their plugin
  registry, `metricRows()`, `chartForLive()`, both card renderers, the
  migration badges, and the two bench scripts that authored registry queries.
  About 700 lines of frontend and 1,400 of Python.
- Tabs start empty. That is a real cost on day one: nobody's dashboard has
  charts until they add some. It is the honest version of what was already
  true — the boxes were empty, they just had titles on them.
- The six admission charts (Criterion 4.1.1) lose their fixed boxes with
  everything else. They are real Insights queries, so they can be re-added
  from the picker like anything else. Their **KPIs** are untouched.
- Selections are per user, in `frappe.defaults` — no new DocType, no
  migration. A shared institutional default layout is now a possible feature
  rather than the only model; if UCC wants one, `analytics/tab_charts.py` is
  the single place it would go.
- `sophia_analytics.css` is asserted byte-identical to
  `custom-html-block/CSS.css`, so the rules for the deleted chart types are
  still in it. That file is a historical artefact and is not edited; the new
  styles are injected at runtime, the same pattern the badge styles used.
- The Explore workspace read `window.UCCLiveVisualDefinitions` to index
  criterion charts. That global is gone, the read is guarded, and Explore now
  indexes only its own diagrams. Left as-is deliberately: it is a
  verbatim-ported legacy block outside this change's scope.

## Revisit triggers
- People ask for the same chart on the same tab repeatedly — that is the case
  for a shared default layout, added beside the per-user one.
- Someone confirms `Insights Chart v3`'s execute contract on a bench, at which
  point the picker can offer presentation charts as well as queries.
