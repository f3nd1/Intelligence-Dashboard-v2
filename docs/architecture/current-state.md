# Current-State Architecture — Phase 0

How the UCC Intelligence Platform works **today**, as deployed, before any migration work. Static
reading only — nothing was executed against a Frappe site.

> **Update.** The real 13-phase `CLAUDE.md` now exists at repo root (`a4b8641` / merged in `f7f7286`);
> the format caveat that used to be here is resolved.

Corroborated by two prior independent read-only investigations,
`docs/investigation_analytics_report.md` and `docs/analytics_workspace_report_2.md`, which agree on
every structural claim below. Where they flagged something as unverified, it is marked here too.

---

## 1. Deployment model

There is no application. There are two kinds of pasted artefact on a live Frappe/ERPNext site:

```
Frappe site
├── ONE Custom HTML Block                     ← the entire frontend
│     ├── HTML field       ← custom-html-block/HTML.html      (57 lines, 16 KB)
│     ├── CSS field        ← custom-html-block/CSS.css        (2,105 lines, 151 KB)
│     └── JavaScript field ← custom-html-block/JAVASCRIPT.js  (3,343 lines, 227 KB)
│
└── 17 independent Server Scripts (type: API, Allow Guest disabled)
      ├── ucc_analytics_criterion_1 … _7      ← the seven dashboards
      ├── ucc_ask_student_journey / _recruitment_agent / _quality_action
      ├── ucc_dashboard_access                ← UI composition gate
      ├── ucc_shared_diagnostics / _record_search
      └── ucc_analytics_bootstrap / _drilldown / _criterion_catalogue / _placeholder_preview
```

Consequences that shape the migration:

- **No imports, no shared module.** Each Server Script is self-contained by necessity; that is why
  `standardise_response_contract` exists byte-identically in seven files.
- **RestrictedPython (`safe_exec`) constrains the Python.** `frappe`, `json` and `frappe.utils` are
  pre-provided. No imports, no leading-underscore names, no `next()`/`id()`. Subscript augmented
  assignment has caused a production break before (`c914c6e`); running totals are written as
  `x = x + 1`. Module-level "caches" in C5 live for one request only.
- **Deployment is copy-paste.** Three fields replaced together, plus each script individually.
  There is no build step on the server and no versioning beyond what the files declare about
  themselves — which is inconsistent (§6).

---

## 2. Frontend runtime

`JAVASCRIPT.js` is seven concatenated IIFEs. Each scopes itself to `root_element` (the variable
Frappe injects into a Custom HTML Block) falling back to `document`, and each is guarded by a
`dataset.<name>Ready === "1"` flag so a double-injection is a no-op.

| Lines | Module |
|---|---|
| 1–265 | `UCC SHARED RUNTIME v1.7.0` — `window.UCCShared` |
| 266–437 | Platform shell — workspace switching, dashboard picker |
| 438–2114 | Ask UCC (`#ajaApp`) |
| 2115–2143 | Criterion 4 markers, placeholder tab controls |
| 2144–2703 | `UCC unified dashboard engine v2.0.1` — the Analytics workspace |
| 2704–3065 | `UCC DIAGRAM EXPLORER v1.9.9` |
| 3066–3343 | `UCC universal visual diagnostics v1.9.9` |

### 2.1 Boot sequence

```
Custom HTML Block renders HTML.html (7 empty divs) + CSS + JS
 └─ platform shell IIFE (266)
     ├─ localStorage["ucc.dashboard"] ?? "criterion_5"
     ├─ ?dashboard= query param overrides it
     ├─ validate against the 7 known ids, else force criterion_5
     ├─ setWorkspace("analytics")        ← unconditional
     └─ setDashboard(resolved)
 └─ engine IIFE (2144) — runs on script evaluation, NOT on DOMContentLoaded
     └─ fetchDashboardAccess()  ──frappe.call──► ucc_dashboard_access   (8 s timeout, fail-open)
         └─ applyDashboardAccess()  removes hidden panels from the DOM *and* deletes their CONFIG entries
             └─ bootstrapDashboards()
                 ├─ mountUnifiedDashboards()   dashboard.innerHTML = dashboardShellMarkup(...)
                 ├─ bind tab / filter / delegated click handlers
                 └─ loadLive(visible dashboard only)
```

**Only one criterion fetches on load** — the one without `.ucc-hidden`. The other six mount their
shell and sit in `renderReadiness(..., null)` until selected.

Selecting a criterion goes: `<select>` native `change` → `setDashboard` (class toggle, localStorage
write, scroll, **then** dispatch `ucc:dashboard-change`) → the engine's listener → `loadLive`.

### 2.2 The single API call shape

One function, `callApi` (`:2334`):

```js
frappe.call({
  method: config.apiMethod,                       // "ucc_analytics_criterion_N"
  args: { payload: JSON.stringify({
    action,                                       // default "summary"
    subcriterion: apiSection(...),
    filters: selectedFilterObject(dashboard),
    page_size: 100
  }) }
})
```

The **entire request is one JSON string in one arg named `payload`.** The response passes through
`normaliseApiMessage` (unwraps up to three levels of JSON-string nesting), then `adaptApiResponse`
(all seven criteria currently use `baseResponseAdapter`; the per-criterion registration hook exists
but has no call site), then a hard `if (message && message.ok)` gate.

`apiSection` never sends `"overview"` — every criterion's Overview tab requests its **first
subcriterion** instead.

### 2.3 Rendering

`dashboardShellMarkup(criterionId, config)` generates everything: loading overlay, hero, filters,
tab bar, readiness strip, empty KPI mount, panel stack. **The static HTML contributes only seven
empty divs** — every Analytics CSS class is emitted from a JS template literal and appears nowhere
in `HTML.html`, so a renamed class silently stops matching CSS with no build-time check.

Charts are hand-written HTML/inline-SVG string builders registered into a `CHART_PLUGINS` Map —
16 types, dispatched on `chart.type`, silently falling back to `bar` for an unknown type. **No
charting library and no D3 in the deployed file.**

Two independent lazy mechanisms:

1. **Tab-level** — a section's cards are built once (`ensureLiveSectionCards`), and a new
   subcriterion tab triggers a fetch unless `state.result.meta.subcriterion` already matches.
   Switching to Sources & Data Quality never fetches.
2. **Card-level** — `renderLiveChartCard` stores `_liveCardPending` and draws nothing;
   `renderLiveChartCardNow` draws once and latches `dataset.liveCardRendered = "1"`. Triggered by
   being in the visible section at render time, or by clicking the card's Diagram/Table toggle.

### 2.4 Failure presentation

`chartForLive` degrades in a fixed order: blocked-source permission notice → "no live metric is
readable" → "returned metrics are not numeric" (explicitly stopping before an invalid SVG path can
be produced) → try/catch render-error panel. `UCCShared` additionally suppresses Frappe's own raw
permission dialog and keeps raw exception text out of the visible body (retained in a `title`
attribute for support).

---

## 3. Server contract

Every criterion script follows the same skeleton: parse `payload` → clamp `page`/`page_size`
(≤200)/`row_limit` (≤2000–5000) → reject anything outside `ALLOWED_ACTIONS` → registries →
helpers → `resolve_source` → metric evaluation → `standardise_response_contract` →
`frappe.response["message"] = result`.

`ALLOWED_ACTIONS` = `summary`, `source_status`, `policy_registry`, `requirement_registry`,
`question_registry`, `drilldown` — identical in six; C3 adds `question_catalogue`.

The shared contract guarantees `ok` (defaulting to **`True`**), a `meta` block carrying
`contract_version: "2.1.0"`, and coerces ~14 response keys to lists. It is called **twice** per
request in every script.

### 3.1 Source resolution is a real read, not an introspection

```python
rows = frappe.get_list(doctype, fields=["name"], limit_start=0,
                       limit_page_length=1, order_by="modified desc") or []
```

Each alias maps to an **ordered candidate list**; the first readable candidate wins, and
`resolution_attempts` / `fallback_used` record what happened. Status vocabulary:
`checking` → `available` | `permission_denied` | `unavailable` | `query_error`.

Metric status is derived from source status and config: `unsupported` (declared, never attempted) →
inherited source status → `unsupported_field` → inherited fetch status → `available`.
`partial` exists but as an **evidence status on requirement rows**, not a metric status.

**101 distinct candidate DocTypes** across the seven criteria. Zero occurrences of
`ignore_permissions` or `frappe.has_permission` in any criterion script — enforcement is entirely
implicit via `frappe.get_list`, with exceptions caught generically and classified by string-matching
the error text.

### 3.2 Where the seven diverge

- **C5** has no `CONFIG`; it uses `METRIC_CONFIG` + `SOURCES_BY_SECTION` + `SUPPORTING_CONFIG`, plus
  `SUBCRITERION_ALIASES` (`5.4`→`5.4.1`, `5.5`→`5.5.1`) and per-request memo caches.
- **C1 and C4** carry a standalone `REQUIREMENT_REGISTRY`; **C6** rebuilds one at request time;
  the rest reflect `result["requirements"]` back.
- **`fetch_rows` has three different signatures** across the seven.
- **C1–C4** chain bare `if action ==` statements; **C5–C7** use `if/elif`.
- **C6/C7** own `unsupported_filter` and `partial_truncated`; **C1–C5** own
  `unsupported`/`unsupported_field`.
- **C7's `is_permission_error`** uniquely also matches the substring `"403"`.

---

## 4. Access model

`ucc_dashboard_access` resolves the signed-in user's roles against a `UCC Dashboard Access`
configuration DocType and returns `{workspaces: {...}, criteria: {...}}` booleans.

This is **UI composition only.** Its own docstring is explicit: it does not read, filter or expose
business data, and it neither consults nor modifies Frappe's permission system. Hiding a tab grants
nothing; a user reaching a hidden area another way is still stopped by Frappe's own DocType
permissions. The client is fail-open — an 8-second timeout or any error yields a fully composed UI.

Note for the port: this script (unlike the criterion scripts) does use
`frappe.get_all(..., ignore_permissions=True)` against `Has Role`, and its configuration DocType
exists only as a manually-created site object — it is not in this repository.

---

## 5. Ask UCC

Three deterministic assistants (Student Journey 4,208 lines; Recruitment Agent 2,153; Quality Action
911) plus a `comingSoon` HR stub in the frontend `MODULE_CONFIG`.

They use a **different request convention** from the analytics scripts: flat `frappe.form_dict` keys
(`question`, `student_applicant` / `agent_contract` / `quality_action`, `conversation`,
`student_roll_rows`), not a `payload` JSON string.

Only Student Journey has an AI path. It reads `openai_api_key` from `form_dict` — i.e. **the browser
supplies the provider key per request** — and issues a server-side
`frappe.make_post_request` to `https://api.openai.com/v1/responses` with a strict `json_schema`
format and `store: False`. The module default is an empty string; **no key is committed to the
repository** (verified). Without a key the assistants run in guided mode and still answer.

---

## 6. Known divergences in the repository itself

1. **`src/` is not the source of the deployed build.** The deployed `custom-html-block/` is the
   *newer* artefact (engine `v2.0.1`, 7 criteria, 16 chart plugins, 0 D3 refs); `src/js/` is the
   *older* one (`v1.9.6`, 5 criteria, 0 plugin registrations, 57 D3 refs). Running
   `tools/build_custom_block.py` would revert the deployed engine. Recent commits hand-patched
   `custom-html-block/`, mirroring into `src/` only sometimes.
2. **`tools/validate_package.py` fails 7 of 101 checks** on a clean tree — that is the baseline.
3. **`dist/`, `custom-html-block/` and `PACKAGE_CHECKSUMS.json` are three-way divergent.**
4. **Version numbers disagree in eight places** (`1.9.5`, `1.9.6`, `1.7.0`, `1.9.9`, `1.9.15`,
   `2.0.1`, `2.0.2-…`, contract `2.1.0`).
5. **`ucc_analytics_bootstrap` and `ucc_analytics_drilldown` have no discoverable caller**;
   `ucc_analytics_placeholder_preview` targets criteria that are now all live.
6. **C4/C5 `overview` metric sets appear unreachable** — the client rewrites `overview` to the first
   subcriterion for all seven criteria.
7. **C5 tabs 5.4 and 5.5 refetch on every visit** — the server returns the canonicalised
   `meta.subcriterion` (`5.4.1`) while the client caches against `"5.4"`.
8. **Two fragile couplings**: `panelInsertPoint` anchors on the literal heading text
   `Management Questions and Data-Based Answers`; `metricRows` selects a chart's data source by
   regex on the human-readable chart title.

---

## 7. What this means for the target app

The system's real assets are its **domain content** — 101 mapped DocTypes, per-criterion policy and
question registries, the evidence-status state machine, the 16 chart renderers, and the honest
"missing ≠ zero, denied ≠ empty" presentation. All of that is portable.

What does not survive the move is the **packaging**: RestrictedPython constraints, copy-paste
deployment, seven duplicated copies of the shared contract, a browser-supplied API key, and a
frontend whose only source of truth is a 227 KB file pasted into a database field.
