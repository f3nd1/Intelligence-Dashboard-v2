# Analytics Workspace — Technical Report

Scope: the "Analytics" workspace only (`[data-ucc-workspace="analytics"]`), covering the seven
criterion dashboards. Explore and Ask UCC are out of scope and mentioned only where a file/function
is shared with them.

**Source-of-truth statement.** All claims below are read from `custom-html-block/HTML.html`,
`custom-html-block/CSS.css`, `custom-html-block/JAVASCRIPT.js` (the deployed "unified dashboard
engine v2.0.1", banner at `custom-html-block/JAVASCRIPT.js:2144`) and `server-scripts/UCC Analytics -
Criterion 1.py` through `Criterion 7.py`. `src/` was **not** used as a basis for any claim; see
§4 for the specific ways it disagrees with the deployed build.

---

## 1. Data Flow

### 1.1 Page load → workspace shown

- Root element: `<div id="uccIntelligencePlatform" class="ucc-platform ucc-embed-safe" ...>` —
  `HTML.html:1`.
- The **platform-shell IIFE** (`JAVASCRIPT.js:266`–`438`) runs first. On load it:
  - Reads `localStorage.getItem("ucc.dashboard")`, falling back to `"criterion_5"` — `JAVASCRIPT.js:417-418`.
  - Reads `?dashboard=` from the URL query string, overriding the stored value if present —
    `JAVASCRIPT.js:419-421`.
  - Validates the resolved id against the 7 known criterion keys, else forces `criterion_5` —
    `JAVASCRIPT.js:422`.
  - Calls `setWorkspace("analytics")` unconditionally — `JAVASCRIPT.js:423` — then
    `setDashboard(savedDashboard)` — `JAVASCRIPT.js:424`.
  - **So the Analytics workspace, with Criterion 5, is what a fresh page load always lands on**,
    unless a different `dashboard=` query param is present or a prior visit stored a different
    choice in `localStorage`.
- `setWorkspace(workspace)` (`JAVASCRIPT.js:284-304`) toggles `.is-active`/`aria-pressed` on
  `[data-ucc-workspace]` buttons and sets `panel.hidden` on `[data-ucc-workspace-panel]` sections
  via the native `hidden` attribute (confirmed: no CSS rule targets `[data-ucc-workspace-panel]` —
  zero matches in `CSS.css`).
- `setDashboard(dashboard)` (`JAVASCRIPT.js:345-…`) toggles the `.ucc-hidden` class (defined twice
  in `CSS.css:1`, `display:none!important`) on each `[data-dashboard-panel]` container and
  syncs `#uccDashboardSelect`'s value — `JAVASCRIPT.js:346-347`.

### 1.2 Static HTML at rest vs. JS-constructed markup

All seven `[data-dashboard-panel="criterion_N"]` containers exist as **empty** `<div>`s in
`HTML.html:6` — e.g. `<div class="ucc-criterion-dashboard" data-dashboard-architecture="shared-v2"
data-dashboard-panel="criterion_5" data-demo-active-tab="overview"
data-demo-dashboard="criterion_5"></div>`. None has child markup in the raw HTML. `criterion_5`
is the only one without the `.ucc-hidden` class pre-set; the other six carry it, and five of
those six (`criterion_1,2,3,6,7`, not `4`) additionally carry `data-live-api="1"` in the static
markup.

Full tab/panel/hero/KPI/readiness markup is generated per-criterion by
`dashboardShellMarkup(criterionId, config)` — `JAVASCRIPT.js:2176-2182` — and injected via
`dashboard.innerHTML = dashboardShellMarkup(...)` inside `mountUnifiedDashboards()` —
`JAVASCRIPT.js:2183-2194`. This one function call is what actually builds: the loading overlay
(`[data-demo-loading-overlay]`), the hero (`.hero.ucc-shared-hero.ucc-standard-criterion-hero`),
the filter controls, the tab bar (`[data-demo-tabs]`, one button per `[overview, ...config.subcriteria,
sources]`), the readiness strip (`.ucc-criterion-notice.ucc-readiness-strip[data-demo-readiness]`),
the empty KPI mount (`<section class="kpis ucc-shared-kpis" data-demo-kpis></section>`), and the
panel stack (`.ucc-unified-panel-stack`), one panel per subcriterion via
`analyticsPanelMarkup(criterionId, key, title)` (`JAVASCRIPT.js:2169-2170`) plus one
Sources-and-Quality panel via `sourcesQualityPanelMarkup(criterionId)` (`JAVASCRIPT.js:2173-2174`).

### 1.3 Gating pass BEFORE mounting: `ucc_dashboard_access`

Before `mountUnifiedDashboards()` ever runs, the engine calls a whitelisted method to decide which
criteria/workspaces to build at all:

- `fetchDashboardAccess()` — `JAVASCRIPT.js:2604-2623` — calls `frappe.call({method:
  "ucc_dashboard_access", args: {}, ...})`. Resolves `null` (fail-open) on any `frappe` absence,
  an `error` callback, a thrown exception, or an 8-second timeout (`JAVASCRIPT.js:2610-2611`).
- `applyDashboardAccess(access)` — `JAVASCRIPT.js:2625-2658` — for each `criterion_N` where
  `access.criteria[criterion_N] === false`, it **removes the `[data-dashboard-panel]` DOM node
  entirely** (`node.parentNode.removeChild(node)`) and **deletes the `CONFIG[criterionId]` entry**
  (`JAVASCRIPT.js:2630-2636`), so `mountUnifiedDashboards()` (which iterates
  `platform.querySelectorAll('[data-dashboard-panel]')` and looks up `CONFIG[criterionId]`) can
  neither find the node nor find a config for it even if it did. It also prunes the matching
  `<option>` from `#uccDashboardSelect` and re-points the selection if the removed option was
  selected (`JAVASCRIPT.js:2638-2644`), and removes hidden workspace buttons/panels entirely
  (`JAVASCRIPT.js:2646-2656`).
- Only after this resolves does `bootstrapDashboards()` run —
  `JAVASCRIPT.js:2660` call site at `JAVASCRIPT.js:2696-2702`.
- Server side: `server-scripts/UCC Dashboard Access.py`, API method `ucc_dashboard_access`. Not a
  Criterion script; it resolves `frappe.session.user`'s roles against the `UCC Dashboard Access`
  DocType and returns `{workspaces:{...}, criteria:{...}}` booleans. This governs UI composition
  only — it does not touch or duplicate Frappe's own data-permission checks (see the file's own
  docstring, lines 13-21).

### 1.4 `bootstrapDashboards()` — initial per-dashboard load

`bootstrapDashboards()` — `JAVASCRIPT.js:2660-2695` — for every surviving
`[data-demo-dashboard]` node:

1. `ensureLiveVisualCards(dashboard, config)` — `JAVASCRIPT.js:2261-2267` — hides any static
   `.ucc-demo-visual-card` not also `.ucc-live-generated-card`, then calls
   `ensureLiveSectionCards(dashboard, config, activeSection(dashboard))` for the current tab
   (`"overview"` at boot).
2. `syncLiveSectionVisibility(dashboard, "overview")` — `JAVASCRIPT.js:2270-2273` — sets
   `grid.hidden = grid.dataset.liveSection !== "overview"` on every `[data-live-section]` grid.
3. Wires click listeners for `[data-demo-tab]` → `showTab(dashboard, tab)`, `[data-demo-filter]`
   change → `loadLive(dashboard, true)`, and one delegated `click` listener on the dashboard
   covering `[data-live-source-doctype]`, `[data-live-qa-records]`, `[data-demo-action]`,
   `[data-demo-drill]`, and `[data-demo-view]` (`JAVASCRIPT.js:2661-2694`).
4. Sets the active tab/panel to `"overview"`, then, **if the dashboard is not `.ucc-hidden`**,
   calls `loadLive(dashboard)`; otherwise it only calls `renderReadiness(dashboard, config, null)`
   (loading placeholder, no API call) — `JAVASCRIPT.js:2694`.

**Consequence, verified by reading the code exactly:** because `bootstrapDashboards()` iterates
*every* `[data-demo-dashboard]` node and only the currently-selected criterion lacks `.ucc-hidden`,
**only the one visible criterion's "overview" summary is fetched on page load.** The other six
remain in the `renderReadiness(..., null)` loading-placeholder state until the user picks them
from `#uccDashboardSelect`. Picking a new option fires the select's native `change` listener
(`JAVASCRIPT.js:364`), which calls `setDashboard(value)` (platform-shell module, `JAVASCRIPT.js:345`).
`setDashboard` toggles `.ucc-hidden` on the panels, writes `localStorage["ucc.dashboard"]`, scrolls
to the newly-shown panel, and — as its **last statement** — dispatches a custom
`ucc:dashboard-change` event on the root platform element (`JAVASCRIPT.js:362`). The engine
module's own listener for that event, registered inside `bootstrapDashboards()`
(`JAVASCRIPT.js:2685`), is what actually calls `loadLive(dashboard)` for the newly-selected
criterion. So the `<select>`'s native `change` is the ultimate user action, but the fetch itself is
triggered one indirection layer later, via the custom event — confirmed by tracing both ends of
the dispatch/listener pair (see also §4, item 2).

### 1.5 `frappe.call` — request shape

`callApi(config, dashboard, action="summary", extra={})` — `JAVASCRIPT.js:2334-2361`:

```
method: config.apiMethod                         // e.g. "ucc_analytics_criterion_5"
args: { payload: JSON.stringify({
  action,                                         // "summary" for the main load
  subcriterion: apiSection(config, dashboard, activeSection(dashboard)),
  filters: selectedFilterObject(dashboard),        // {} of [data-demo-filter] values
  page_size: 100,
  ...extra
}) }
```

- `config.apiMethod` per criterion, read directly from the `CONFIG` literal at
  `JAVASCRIPT.js:2150`: `ucc_analytics_criterion_1` … `_7` — one string per key, all seven
  confirmed present.
- `apiSection(config, dashboard, tab)` — `JAVASCRIPT.js:2330-2333` — for `tab in {"quality",
  "sources"}` reuses `state.lastSection` (the last real subcriterion visited) or
  `config.defaultSection`; for a real subcriterion tab it looks up `config.apiSections[tab]` and
  remembers it as `state.lastSection`.
- On success (`message.ok === true`), the raw response passes through
  `normaliseApiMessage(response)` (`JAVASCRIPT.js:2196-2210`, unwraps up to 3 levels of
  `response.message`) then `adaptApiResponse(config, dashboard, payload, rawMessage)`
  (`JAVASCRIPT.js:2325-2327`), which looks up a per-criterion adapter in `RESPONSE_ADAPTERS`
  (`JAVASCRIPT.js:2320`, populated via `registerResponseAdapter`, `JAVASCRIPT.js:2321`) or falls
  back to `baseResponseAdapter` (`JAVASCRIPT.js:2313-2319`), which normalises `metrics`, `sources`,
  `questions` (accepting a legacy `qa` alias), `exceptions`, `data_quality` (accepting a legacy
  `quality` alias), and derives `source_summary`/`metric_summary` via `summaryFromRows` if absent.
  No `registerResponseAdapter(...)` call was found for any `criterion_N` inside the engine module
  itself (grep for the literal within lines 2144-2704 found only the registration *function*, not
  a call site) — i.e. as deployed, **every criterion currently uses `baseResponseAdapter`**, not a
  bespoke adapter.
- On failure, `apiErrorMessage(error)` (`JAVASCRIPT.js:2296-2309`) builds a detail string,
  preferring the shared `UCCShared.errorText(error)` helper when it returns something other than
  the literal `"Request failed"`, else falling back to `error.message`, `_server_messages`
  parsing, or `error.exc_type`/`statusText`.

### 1.6 Server Script → response

Each `UCC Analytics - Criterion N.py` parses `frappe.form_dict.get("payload")` as JSON, validates
`action` against `ALLOWED_ACTIONS`, resolves sources via `frappe.get_list(...)` (permission-aware,
no `ignore_permissions` anywhere in these 7 files), evaluates metrics/questions, and assigns the
final dict to `frappe.response["message"]`. Full structural detail in §2.

### 1.7 Response → rendered UI

`loadLive(dashboard, force=false)` — `JAVASCRIPT.js:2570` — the orchestrator:

```
ensureLiveSectionCards(...)                 // late-mount cards for the active tab if not yet built
if state.loading: return
if !force && state.result && state.result.meta?.subcriterion === section:
    renderDashboard(dashboard); return       // cache hit, no network call
state.loading = true; setLoading(..., 15, `Loading ${section}`)
try:
    result = await callApi(config, dashboard, "summary")
    setLoading(..., 80, "Rendering live analytics")
    state.result = result; renderDashboard(dashboard)
    setLoading(..., 100, "Live analytics ready"); setTimeout(() => setLoading(false), 150)
catch (error):
    state.error = error; logEvent(...); renderDashboard(dashboard); setLoading(false)
finally: state.loading = false
```

`renderDashboard(dashboard)` — `JAVASCRIPT.js:2569` — the render dispatcher, called both after a
successful/failed load and directly by `showTab`:

```
config = CONFIG[dashboard.dataset.demoDashboard]
if state.error && !result: renderError(...); return       // dashboard-level failure UI, see below
tab = activeSection(dashboard)
updateDashboardIdentity(dashboard, config, tab)             // hero title/kicker text swap
section = sectionDefinition(config, tab)
liveDefinitions = LIVE_VISUAL_EXPANSION[dashboardId]?.[tab] || section?.charts || []
renderKpis(dashboard, config, result)
liveDefinitions.forEach((chart, i) => renderLiveChartCard(dashboard, chart, chart.i ?? i, result))
dashboard.querySelectorAll(`[data-live-section="${tab}"] [data-demo-card]`).forEach(renderLiveChartCardNow)
renderQa(dashboard, result, tab)
renderSources(dashboard, result)
renderQuality(dashboard, result)
renderReadiness(dashboard, config, result)
```

Per-target renderers, each keyed off a `data-demo-*` attribute set by `dashboardShellMarkup`:

| Target | Renderer | Line | Reads from response |
|---|---|---|---|
| KPI tiles | `renderKpis` | `JAVASCRIPT.js:2501` | title-pattern-matched against `result.source_summary`/`metric_summary`/`metrics` inside `metricRows` |
| Chart card (pending) | `renderLiveChartCard` | `JAVASCRIPT.js:2469-2489` | sets card title/description text; stores `card._liveCardPending = {chart, index, result}` — does **not** draw yet |
| Chart card (draw) | `renderLiveChartCardNow` | `JAVASCRIPT.js:2491-2500` | consumes `card._liveCardPending`; calls `metricRows(result, index, chart)` then `chartForLive(node, chart, rows)` |
| Q&A table | `renderQa` | (2429-2451 range per function map) | `extendedQuestionRows(result, tab)` — merges `result.questions` with any `result.metrics` entry not already referenced by a question, synthesising a row |
| Sources table | `renderSources` | `JAVASCRIPT.js:2531-2544` (per range) | `result.sources` |
| Data-quality table | `renderQuality` | `JAVASCRIPT.js:…2547` | `result.data_quality` |
| Readiness banner | `renderReadiness` | `JAVASCRIPT.js:…2556` | `result.source_summary`, `result.metric_summary` |
| Dashboard-level error | `renderError` | `JAVASCRIPT.js:2563-2580` | `state.error` only (no `result`) |

### 1.8 Lazy-load / click-to-render behaviour

Two distinct lazy mechanisms were found, confirmed by reading the actual code rather than assumed:

1. **Tab-level lazy fetch.** `showTab(dashboard, tab)` — `JAVASCRIPT.js:2571`:
   ```
   dashboard.dataset.demoActiveTab = tab
   toggle .active on the clicked [data-demo-tab] button
   toggle .hidden on [data-demo-panel] to show only the matching panel
   ensureLiveSectionCards(dashboard, config, tab)      // build cards for this tab if not yet built
   syncLiveSectionVisibility(dashboard, tab)
   if tab is "quality" or "sources": renderDashboard(dashboard)   // reuse cached state.result, no fetch
   else: loadLive(dashboard)                                       // fetch iff section changed (loadLive's own cache check)
   ```
   So switching to a **new subcriterion tab** triggers a fresh `frappe.call` (unless
   `state.result.meta.subcriterion` already equals the target section); switching to
   **Sources & Data Quality** never triggers a fetch — it only re-renders already-cached data.

2. **Card-level click-to-render.** Even once a tab's data has loaded, chart cards are only fully
   drawn when either (a) they belong to the section named in the currently-visible
   `[data-live-section]` grid at `renderDashboard` time (`JAVASCRIPT.js:2569`, the
   `.forEach(renderLiveChartCardNow)` line), or (b) the user clicks a card's `Diagram`/`Table`
   toggle button (`[data-demo-view]`), handled by the delegated click listener at
   `JAVASCRIPT.js:2683-2684`: `renderLiveChartCardNow(card)` is called there explicitly, guarded
   inside the function itself by `if (!card._liveCardPending || card.dataset.liveCardRendered ===
   "1") return;` (`JAVASCRIPT.js:2492`) — i.e. a card renders at most once, on first reveal.

---

## 2. Server Script Architecture

*(Compiled from an independent full-file pass across all seven scripts; every line number below
was read directly, not inferred.)*

### 2.1 Per-criterion summary

| Crit | API method | Pattern | `ALLOWED_ACTIONS` | Notable unique constructs |
|---|---|---|---|---|
| 1 | `ucc_analytics_criterion_1` | `CONFIG` + `POLICY_REGISTRY`/`QUESTION_REGISTRY`/`REQUIREMENT_REGISTRY`; `evaluate_metric` | 6: `summary, source_status, policy_registry, requirement_registry, question_registry, drilldown` | Has its own `REQUIREMENT_REGISTRY` constant (one of only 2 files that do) |
| 2 | `ucc_analytics_criterion_2` | Same as C1 | Same 6 | No `REQUIREMENT_REGISTRY` — that action reflects `result.get("requirements")` back |
| 3 | `ucc_analytics_criterion_3` | `CONFIG`, but metric evaluation **split** into `evaluate_base_metric` + `evaluate_derived_metric(metric, metrics_by_id)` (an aggregate/derived-metric concept absent elsewhere) | 7: adds `question_catalogue`, folded into the same branch as `question_registry` | `fetch_rows(source_alias, source, requested_fields=None)` |
| 4 | `ucc_analytics_criterion_4` | `CONFIG` + `evaluate_metric`; unique `QUESTION_DRILLDOWN_METRICS` | Same 6 | `fetch_rows(source_alias, source, requested_fields=None, excluded_filter_keys=None)` — only file with this 4th param; has its own `REQUIREMENT_REGISTRY` |
| 5 | `ucc_analytics_criterion_5` | **Distinct**: `METRIC_CONFIG` + `SOURCES_BY_SECTION` + `SUPPORTING_CONFIG` + `QUESTION_REGISTRY`, keyed by subcriterion code; `evaluate_direct_metric(metric, source_map, include_rows=False)`; module-level caches `SOURCE_CACHE`/`META_CACHE`/`FIELD_CACHE`/`ROW_CACHE`/`ROW_ERROR_CACHE` (present in no other file) | Same 6 (confirmed identical to C1/2/4/6/7 post the earlier makeQA-migration revert — see §4) | `SUBCRITERION_ALIASES = {"5.4": "5.4.1", "5.5": "5.5.1"}` with a `canonical_subcriterion` resolution step threaded through meta/drilldown/contract calls — no other criterion remaps legacy codes |
| 6 | `ucc_analytics_criterion_6` | `CONFIG` + `evaluate_metric`; unique `CHILD_SAFE_FIELDS` (child-table field safelist, e.g. `Quality Action Resolution`) | Same 6 | Pre-computes `resolved_filters, unresolved_filters, source_mapping, requirements, readiness, criterion_overview` directly in the initial response dict (bypassing the shared function's generic derivation for those keys) |
| 7 | `ucc_analytics_criterion_7` | `CONFIG` + `evaluate_metric`, same shape as C6 | Same 6 | Same pre-computation pattern as C6 |

Every file calls a `standardise_response_contract(result, criterion_name, api_method,
action_name, subcriterion_name, row_limit_value)` function **twice** — once before the
`if action == ...` dispatch, once after, immediately before `frappe.response["message"] = result`
(e.g. C1: `Criterion 1.py:1819` and `:1844`; C5: `Criterion 5.py:3363` and `:3396`). The function
body itself is byte-identical across all seven files (only the surrounding `result = {...}`
literal differs). It always normalises the final payload onto:

```
ok, meta{api_method, criterion, contract_version:"2.1.0", action, subcriterion, row_limit},
filters, resolved_filters, unresolved_filters, sources, source_mapping, metrics,
supporting_metrics, questions, requirements, exceptions, evidence_gaps, data_quality,
warnings, source_summary, metric_summary, question_summary, readiness,
data{ mirrors of most of the above }
```

### 2.2 Evidence-status vocabulary

| Status | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `available` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `checking` (in-progress marker during source resolution) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `unavailable` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `permission_denied` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `query_error` (non-permission fetch exception) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `partial` | ✓ | (text only, not a `status` literal) | ✓ (as `support_status`) | ✓ | ✓ | ✓ | ✓ |
| `unsupported` / `unsupported_field` | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| `unsupported_filter` | — | — | — | — | — | ✓ | ✓ |
| `partial_truncated` | — | — | — | — | — | ✓ | ✓ |
| `not_installed` | — | — | — | — | — | — | — |

Meta-level `meta.status` catalogue label (a different namespace — one free-text string per file,
not shared vocabulary): C1 `decision_useful_catalogue`, C2 `live_foundation`, C3
`revised_management_catalogue`, C4 `decision_useful_catalogue`, C5
`translation_aligned_foundation`, C6/C7 `policy_aligned_foundation`.

The core vocabulary (`available/checking/unavailable/permission_denied/query_error/partial`) is
shared by all seven. `unsupported`/`unsupported_field` (C1-C5) vs `unsupported_filter` (C6/C7
only) is a real split between the earlier and later criteria; `partial_truncated` is exclusive to
C6/C7.

### 2.3 Structural differences worth flagging

- **`REQUIREMENT_REGISTRY`**: standalone constant only in C1 and C4. C2/C3/C5/C7 reflect
  `result.get("requirements")` back for that action; **C6 rebuilds it at request time** by
  iterating `QUESTION_REGISTRY` — a third distinct implementation of the same action name.
- **`fetch_rows` signature** varies: `(source, requested_fields=None)` in C1/C2/C6/C7;
  `(source_alias, source, requested_fields=None)` in C3/C5; `(source_alias, source,
  requested_fields=None, excluded_filter_keys=None)` in C4 only.
- **Dispatch style**: C1-C4 chain independent `if action == "X":` statements (no `elif`); C5/C6/C7
  use `if / elif`. Functionally near-equivalent (single-valued, pre-validated `action`), but a
  real code-pattern inconsistency.
- **C3's pre-seeded summary keys** (`metric_summary`/`question_summary` using `unavailable` as a
  key name) are set in its initial dict, but the shared `standardise_response_contract` function
  unconditionally re-assigns `metric_summary`/`question_summary`/`source_summary` at its tail — so
  the shared function's own key names (using `issues`, not `unavailable`) are what actually reach
  the client for C3 as well. Flagged as a discrepancy in §4, not fixed.
- **C5's bespoke `readiness` object** (`type: "technical_data_readiness"`,
  `not_operational_compliance: True`) is built independently of the shared function's own
  `readiness` derivation. Based on reading the shared function's merge logic (it reads
  `result.get("readiness")`, defaults to `{}` only if not a dict, then only *adds* keys like
  `status`/`source_total`), C5's `type`/`label`/`not_operational_compliance` keys likely survive
  the second call rather than being overwritten — flagged as unverified in §4 since it was not
  traced against a live response.

### 2.4 RestrictedPython-relevant patterns

- All seven use `frappe.get_list(...)` exclusively for data reads — zero occurrences of
  `frappe.db.get_list` or `frappe.get_all` in any of the 7 criterion scripts (contrast with `UCC
  Dashboard Access.py`, which does use `frappe.get_all(..., ignore_permissions=True)` — that file
  is not a criterion script and is out of this report's scope).
- **Zero occurrences of `ignore_permissions` or `frappe.has_permission`** in any of the 7 files —
  permission enforcement is entirely implicit via `frappe.get_list`'s own row/doctype filtering,
  caught as a generic `Exception`.
- Identical `is_permission_error(error)` helper in every file, string-matching the lower-cased
  error text rather than catching a permission exception class by name — e.g. `Criterion 1.py:809`,
  `Criterion 5.py:2249`. **C7's version additionally checks for the substring `"403"`**
  (`Criterion 7.py`) — the only one of the seven with this extra check; C1-C6 do not have it.
- No leading-underscore identifiers, no `next()`/`id()`, no subscript augmented assignment
  (`x["y"] += 1`) observed anywhere sampled — running totals use plain rebinding
  (`metric_available = metric_available + 1`, e.g. `Criterion 1.py:1707`), consistent with
  RestrictedPython constraints.
- `payload` parsing is identical boilerplate in all seven: `frappe.form_dict.get("payload")` →
  `json.loads(...)` inside a broad `try/except Exception: payload = {}`, then an `isinstance(dict)`
  guard.

---

## 3. Custom HTML Block Structure

### 3.1 `HTML.html` (57 lines; heavily minified onto few lines)

- Root: `<div id="uccIntelligencePlatform" class="ucc-platform ucc-embed-safe"
  data-build-id="UCC-PLATFORM-2.0.1-SHARED" data-platform-version="2.0.1">` — `HTML.html:1`.
- Workspace switcher `<nav class="ucc-platform-workspaces">` inside `<header
  class="ucc-platform-shell">`, three `[data-ucc-workspace]` buttons: `analytics` (pre-marked
  `is-active`/`aria-pressed="true"`), `explore`, `ask` — `HTML.html:1-4`.
- `#uccDashboardSelect` lives inside `[data-ucc-dashboard-control]`, `HTML.html:5`. Seven
  `<option>`s in DOM order, `criterion_1` through `criterion_7`, labels exactly:
  "Criterion 1 · Leadership and Strategic Planning", "Criterion 2 · Corporate Administration",
  "Criterion 3 · External Recruitment Agents", "Criterion 4 · Student Protection and Support
  Services", "Criterion 5 · Academic Systems and Processes" (**`selected`**), "Criterion 6 ·
  Quality Assurance, Innovation and Continual Improvement", "Criterion 7 · Performance Outcomes".
- The `analytics` workspace panel, `<section class="ucc-platform-workspace"
  data-ucc-workspace-panel="analytics">`, has **no `hidden` attribute** in the raw markup —
  `explore` and `ask` do (`HTML.html:8`, `:57`) — consistent with Analytics being the default
  workspace.
- The seven `[data-dashboard-panel]` containers are siblings on `HTML.html:6`, all empty at rest
  (see §1.2 table for the exact per-container attribute set).
- No static loading-overlay, readiness-banner, hero, or KPI markup exists anywhere in `HTML.html`
  for Analytics — everything of that kind is generated by `dashboardShellMarkup` at runtime (§1.2).
- The only other Analytics-adjacent static element is a platform-wide changelog modal,
  `[data-changelog-overlay]` (`HTML.html:57`, outside `<main>`) — not Analytics-specific.

### 3.2 `CSS.css` (2105 lines; line 1 alone holds most base/reset rules, minified)

- `#uccIntelligencePlatform` has **no dedicated ID selector** anywhere — everything is scoped via
  the `.ucc-platform` class.
- `.ucc-hidden{display:none!important}` (defined twice, both on `CSS.css:1`) is the mechanism
  `setDashboard` uses to switch the visible criterion.
- **Card layout** (title + description + Diagram/Table toggle): the actual class is
  `.ucc-live-generated-card`, **not** `.ucc-demo-card` — that literal string has zero matches.
  `mini-toggle` likewise has zero matches; `data-card-view` likewise has zero matches (the toggle
  state is driven by `.active`/`.is-active` classes on the button, and by
  `.ucc-demo-chart`/`[data-demo-chart-table]` visibility, not a data attribute).
  - Card shell, header, accent bar: `CSS.css:1092-1116`.
  - Title `.ucc-card-heading-copy>h2`: `CSS.css:1120-1128`. Description `.ucc-card-description`:
    `CSS.css:1129-1136`.
  - Toggle `.ucc-card-view-toggle` and buttons: `CSS.css:1137-1169`.
  - Chart pane `.ucc-live-generated-card>.ucc-demo-chart`: `CSS.css:1173-1177`. Table pane
    `.ucc-live-generated-card>[data-demo-chart-table]:not(.hidden)`: `CSS.css:1178-1181`.
  - Drill-down button `[data-demo-drill]`: `CSS.css:1182-1216`.
  - A second, older card wrapper class `.ucc-demo-visual-card` coexists (`CSS.css:724`, `:751`) —
    `ensureLiveVisualCards` (`JAVASCRIPT.js:2261`) explicitly hides any node with that class that
    is *not also* `.ucc-live-generated-card`, implying it's a legacy class being phased out.
- **Chart containers**: `.ucc-live-expanded-grid` (`CSS.css:832-835`, `:891-905`); empty-state
  `.ucc-live-empty` (`CSS.css:794-799`); criterion_4-only SVG chart classes
  (`.ucc-admission-svg` and children) scoped under `[data-dashboard-panel="criterion_4"]
  .ucc-admission-intelligence` (`CSS.css:2023-2074`).
- **KPI tiles**: base grid `.kpis{grid-template-columns:repeat(6,minmax(0,1fr))}` (`CSS.css:1`);
  shared border/shadow rule scoped to `.ucc-platform [data-dashboard-panel].ucc-criterion-dashboard`
  (`CSS.css:745`); criterion-4-only `.ucc-admission-kpi` variant (`CSS.css:2005-2016`); a blocked
  permission notice inside a KPI grid is forced full-width via `.kpis .ucc-perm-notice,
  .ucc-shared-kpis .ucc-perm-notice{grid-column:1/-1}` (`CSS.css:2105`).
- **Readiness / status banners** — two separate components:
  1. `.ucc-readiness-strip`, explicitly commented "Shared readiness bar: Criteria 1 to 7 use this
     exact component" (`CSS.css:1862`), full block `CSS.css:1863-1946`. Status-variant styling via
     `[data-status="warning"|"error"|"loading"|"available"]` attribute selectors
     (`CSS.css:1879-1897`) — this is the same `[data-demo-readiness]` element `renderError` and
     `renderReadiness` both write `dataset.status` on.
  2. `.ucc-demo-status`, a small inline pill badge (not a full banner) with `.good/.warning/.risk`
     tone classes (`CSS.css:721-722`).
- **Permission-notice component** `.ucc-perm-notice`, full block `CSS.css:2091-2105`, comment at
  `CSS.css:2088-2090` describing it as "Shared permission-denied notice: one look for every
  blocked view across all…". Not scoped to any specific criterion — global/shared, matching its
  use in `renderError` (`JAVASCRIPT.js:2569-…`, via `UCCShared.permissionNoticeHtml(...)`) and in
  the card-level empty-table fallback (`JAVASCRIPT.js:2497` `blockedSourceNames(result).length ?
  UCCShared.permissionNoticeHtml(...) : ...`).
- **Scoping summary**: global/shared rules (`.ucc-live-generated-card`, `.ucc-readiness-strip`,
  `.ucc-perm-notice`, `.kpis`, `.ucc-demo-*` family) apply to any criterion's rendered output
  unconditionally. Generic `[data-dashboard-panel]`-scoped rules (`CSS.css:730-750`,
  `:824-826`) apply to all seven. Criterion-**specific** overrides exist only for
  `[data-dashboard-panel="criterion_3"]` (Sources & Quality layout, `CSS.css:1237-1374`) and
  `[data-dashboard-panel="criterion_4"].ucc-admission-intelligence` (Admission Intelligence
  KPI/SVG overrides, `CSS.css:1998-2087`). `[data-demo-dashboard]` (present on every panel in the
  HTML, mirroring `data-dashboard-panel`) has **zero** CSS selectors referencing it — it is a
  JS-only hook.

### 3.3 `JAVASCRIPT.js` — Analytics-relevant module (lines 2144-2704, banner "UCC unified dashboard
engine v2.0.1")

This is one of eight top-level IIFEs in the 3343-line deployed file (banners/boundaries found at
lines 1, 266, 438, 1972, 2118 "placeholder dashboard tab controls", **2144-2704 "unified dashboard
engine v2.0.1"**, 2705 "DIAGRAM EXPLORER v1.9.9", 3067 "universal visual diagnostics v1.9.9"). Only
the 2144-2704 module and the platform-shell module (266-438, workspace switching) are relevant to
Analytics; the shared runtime module (1-265) is used by all workspaces (e.g. `UCCShared.errorText`,
`UCCShared.permissionNoticeHtml`, both called from inside this module — §1.5, §1.7).

Function inventory of the engine module, with responsibility, in the order they appear:
markup builders (`esc`, `normaliseFilterDefinition`, `filterMarkup`, `analyticsPanelMarkup`,
`sourcesQualityPanelMarkup`, `dashboardShellMarkup`, `mountUnifiedDashboards`,
`liveChartCardMarkup`) → response normalisation (`normaliseApiMessage`, `apiErrorMessage`,
`baseResponseAdapter`, `adaptApiResponse`, `registerResponseAdapter`) → chart rendering
(`renderBars/Donut/Funnel/Lifecycle/Matrix/Radar/Trend/Gauge/AdmissionLine/AdmissionColumns/
RiskMatrix/Decision/Network/Reconciliation/Ladder`, all registered into a `CHART_PLUGINS` Map via
`registerChartPlugin`, dispatched by `renderChart` on `chart.type`, default `"bar"`) → state/API
(`dashboardState`, `logEvent`, `selectedFilterObject`, `apiSection`, `callApi`, `setLoading`) →
value/display helpers (`metricValue`, `statusBadge`, `displayDoctypeName`, `doctypeListRoute`,
`metricById`, `sourceCalculation`, `extendedQuestionRows`, `metricRows`, `blockedSourceNames`) →
per-target renderers (`chartForLive`, `renderLiveChartCard`, `renderLiveChartCardNow`,
`renderKpis`, `renderQa`, `renderSources`, `renderQuality`, `renderReadiness`, `renderError`,
`updateDashboardIdentity`, `renderDashboard`) → orchestration (`loadLive`, `showTab`, modal/export
helpers (`ensureModal`, `openModal`, `tableFromRows`, `openMetricRecords`, `openRecords`,
`openReadiness`, `showDiagnostics`, `handleAction`), access gating (`fetchDashboardAccess`,
`applyDashboardAccess`), and finally `bootstrapDashboards()` plus the top-level init call chain
(`fetchDashboardAccess().then(...)`) that ties everything together.

**How the three files interact**, concretely:

1. `HTML.html` supplies the empty mount points (`[data-dashboard-panel]`, `#uccDashboardSelect`,
   `[data-ucc-workspace]`) and the platform shell chrome.
2. `JAVASCRIPT.js`'s platform-shell module (266-438) wires the workspace switcher and dashboard
   picker against those mount points, using only class/attribute toggling — it injects no new
   markup of its own.
3. `JAVASCRIPT.js`'s engine module (2144-2704) is the only code that writes into a
   `[data-dashboard-panel]` node's `innerHTML`; every subsequent render call operates on elements
   that markup already created (`querySelector` against `[data-demo-kpis]`,
   `[data-demo-readiness]`, `[data-demo-chart]`, etc.), never re-building the shell.
4. `CSS.css` has no dependency the other direction — it defines rules keyed off the class names
   and `data-*` attributes that `dashboardShellMarkup`/`liveChartCardMarkup`/`analyticsPanelMarkup`
   emit, so any renamed attribute or class in the JS would silently stop matching CSS with no
   build-time check.
5. `JAVASCRIPT.js` talks to the Server Scripts exclusively via `frappe.call({method:
   config.apiMethod, args: {payload: JSON.stringify(...)}})` inside `callApi` — no other
   client/server coupling exists for Analytics (confirmed: no direct REST/URL fetch calls found in
   the engine module).

---

## 4. Open Questions / Discrepancies Found

1. **`src/` does not reflect the deployed engine.** `src/js/10-platform-runtime.js` (not read in
   full for this report, per scope) is known from this session's prior work to contain an entirely
   different, non-unified per-criterion rendering approach with no `mountUnifiedDashboards`,
   `CONFIG`-driven shell, or `ucc_dashboard_access` gating call. The "unified dashboard engine
   v2.0.1" documented in §1 and §3.3 exists **only** in `custom-html-block/JAVASCRIPT.js`; running
   the repo's own build script against `src/` would not reproduce it. This report deliberately
   describes only the deployed file.

2. ~~Dispatch mechanism for a shown-but-not-yet-loaded dashboard~~ — **resolved on a second pass,
   not left open.** `#uccDashboardSelect`'s native `change` listener,
   `dashboardSelect.addEventListener("change", () => setDashboard(dashboardSelect.value))`
   (`JAVASCRIPT.js:364`), calls `setDashboard`, whose **last statement**
   (`JAVASCRIPT.js:362`, past the range originally quoted in §1.1) is
   `root.dispatchEvent(new CustomEvent("ucc:dashboard-change", {detail: {dashboard}}))`. The
   engine module's listener at `JAVASCRIPT.js:2685` (`platform.addEventListener("ucc:dashboard-change",
   event => {...loadLive(dashboard)})`) catches that dispatch (event bubbles from `root` — the
   `setDashboard` closure's own `#uccIntelligencePlatform` reference — up to `platform`) and
   fetches the newly-selected criterion's data if it hasn't been loaded yet. So the full chain for
   picking a new criterion from the dropdown is: native `change` → `setDashboard` (class toggle +
   `localStorage` write + `scrollDashboardToTop` + event dispatch) → `ucc:dashboard-change` listener
   → `loadLive(dashboard)`.

3. **Every criterion currently uses `baseResponseAdapter`.** `registerResponseAdapter(criterionId,
   adapter)` exists and is exported on `window.UCCLiveAnalytics` (`JAVASCRIPT.js:2701`), but no
   call site registering a per-criterion adapter was found inside the engine module. This may be
   intentional (extensibility hook, currently unused) or a leftover from an earlier design where
   criteria had bespoke adapters — not something this read-only pass can distinguish.

4. **C5's dispatch/action surface is no longer structurally distinct from C1/2/4/6/7 — only its
   internal config pattern is.** The task's carried-forward context states "Criterion 5's server
   script currently uses POLICY_REGISTRY + METRIC_CONFIG + QUESTION_REGISTRY per subcriterion,
   after an earlier partial JS-to-server migration was reverted." Verified true for the
   config/evaluator layer (§2.1, §2.3), but `ALLOWED_ACTIONS` and the dispatch block are now
   byte-for-byte the same 6-action set as C1, C2, C4, C6, C7 (only C3 differs, by having a 7th
   action). Worth noting precisely so the two levels (action surface vs. internal metric-config
   pattern) aren't conflated.

5. **C5's bespoke `readiness` object survival through `standardise_response_contract`'s second
   call was not empirically verified** — reasoned from reading the shared function's merge logic
   only (§2.3, last bullet). Confirming this would require either a live API call or fully tracing
   the function body against C5's specific `readiness` literal, which was out of the time/scope
   budget for this pass.

6. **C3's pre-seeded `metric_summary`/`question_summary` key names (`unavailable`) are shadowed by
   the shared function's own key names (`issues`) at the point `frappe.response["message"]` is
   assigned**, since the shared function unconditionally re-sets those three summary keys on its
   second call. Not a runtime error, but the pre-seeded values are dead code from the client's
   perspective — flagged as an observation only, not fixed.

7. **`Criterion 7.py`'s `is_permission_error` includes an extra `"403"` substring check** that
   C1-C6 lack. Whether this is deliberate (C7's data sources return numeric-status-only errors more
   often) or drift was not determinable from static reading alone.

8. **This report's HTML/CSS section and JS-function-inventory section were partly produced by two
   parallel read-only sub-investigations**, cross-checked against this document's own independent
   line-level reads of `mountUnifiedDashboards`, `bootstrapDashboards`, `fetchDashboardAccess`,
   `applyDashboardAccess`, `callApi`, `renderDashboard`, `loadLive`, `showTab`,
   `renderLiveChartCardNow`, `dashboardShellMarkup`, `analyticsPanelMarkup`, and
   `sourcesQualityPanelMarkup`, plus a full independent pass over all seven Server Scripts'
   `ALLOWED_ACTIONS`, `is_permission_error`, `CHILD_SAFE_FIELDS`/`SOURCES_BY_SECTION` presence, and
   `evaluate_metric` vs `evaluate_direct_metric` naming. No contradictions were found between the
   independent checks and the sub-investigation reports; all figures presented above reflect that
   agreement.
