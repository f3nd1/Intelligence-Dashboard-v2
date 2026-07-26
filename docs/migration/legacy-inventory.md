# Legacy Inventory — Phase 0

Read-only inventory of everything in `f3nd1/Intelligence-Dashboard-v2` at commit `1b2f84c`, ahead of
the `ucc_intelligence` Frappe app migration. Nothing was modified, moved or archived to produce this
document.

> **Update.** This document was originally written before the real `CLAUDE.md` (13-phase migration
> spec) existed in this repository; the format caveat that used to be here is resolved — the real
> spec landed at repo root in `a4b8641` / merged into this branch in `f7f7286`. Structure and content
> below now match CLAUDE.md §20 Phase 0. One §19 item this inventory could not resolve on its own is
> recorded in §6.

## Classification tags

| Tag | Meaning |
|---|---|
| `[REUSE]` | Portable as-is. Copy the file/function into the app with no logic change. |
| `[ADAPT]` | Logic is portable; the surrounding contract changes (entrypoint, permissions, packaging). |
| `[REBUILD]` | Cannot be carried across. The requirement survives, the implementation does not. |

The tag describes the **code**, not the priority. Disposition (port now / port after a caller is
confirmed / archive candidate) is called out separately where it differs.

---

## 1. Server Scripts (`server-scripts/`, 17 files, ~1.05 MB)

All are Frappe **Script type: API**, executed top-to-bottom under `safe_exec` (RestrictedPython).
None is a module: no `def main()`, no `@frappe.whitelist()`, no imports. Each terminates by
assigning `frappe.response["message"]`. Every docstring states `Allow Guest must remain disabled`.

The common migration shape for all of them: the **body is portable Python**; the **wrapper is not**.
`frappe.form_dict.get("payload")` → a whitelisted function signature, and
`frappe.response["message"] = result` → a `return`. That wrapper swap is why almost nothing here is
`[REUSE]`.

### 1.1 Criterion analytics scripts

| File | Method | Lines | Class | Notes driving the classification |
|---|---|---:|---|---|
| `UCC Analytics - Criterion 1.py` | `ucc_analytics_criterion_1` | 1,846 | `[ADAPT]` | `CONFIG`-driven. Owns `REQUIREMENT_REGISTRY` (only C1 and C4 do). |
| `UCC Analytics - Criterion 2.py` | `ucc_analytics_criterion_2` | 1,827 | `[ADAPT]` | `CONFIG`-driven. Largest source surface — 43 candidate DocTypes. |
| `UCC Analytics - Criterion 3.py` | `ucc_analytics_criterion_3` | 2,286 | `[ADAPT]` | Only script with a **7th action** (`question_catalogue`). Metric evaluation split into `evaluate_base_metric` + `evaluate_derived_metric`. |
| `UCC Analytics - Criterion 4.py` | `ucc_analytics_criterion_4` | 3,288 | `[ADAPT]` | `fetch_rows` carries a 4th param (`excluded_filter_keys`) no other script has. Owns `QUESTION_DRILLDOWN_METRICS`, `C4_VISUAL_REGISTRY`. |
| `UCC Analytics - Criterion 5.py` | `ucc_analytics_criterion_5` | 3,398 | `[ADAPT]` | **Structurally the odd one out.** No `CONFIG`; uses `METRIC_CONFIG` + `SOURCES_BY_SECTION` + `SUPPORTING_CONFIG`. Only script with module-level caches and `SUBCRITERION_ALIASES`. |
| `UCC Analytics - Criterion 6.py` | `ucc_analytics_criterion_6` | 2,210 | `[ADAPT]` | Pre-computes `readiness`/`source_mapping` itself. Owns `CHILD_SAFE_FIELDS`. Rebuilds `requirement_registry` at request time — a third implementation of that action. |
| `UCC Analytics - Criterion 7.py` | `ucc_analytics_criterion_7` | 2,061 | `[ADAPT]` | Same shape as C6. Its `is_permission_error` uniquely also matches `"403"`. |

Shared across all seven and the single highest-value dedup target — **but not in Phase 1**:

- `standardise_response_contract(...)` — byte-identical in all seven files. Emits
  `meta.contract_version = "2.1.0"`. Called **twice** per request (before and after action dispatch).
- `is_permission_error(error)` — near-identical, string-matches lower-cased error text rather than
  catching an exception class.
- The payload-parse / clamp / `ALLOWED_ACTIONS` preamble — identical boilerplate ×7.

`ALLOWED_ACTIONS` is `["summary", "source_status", "policy_registry", "requirement_registry",
"question_registry", "drilldown"]` in six of seven; C3 adds `"question_catalogue"`.

### 1.2 Ask UCC scripts

| File | Method | Lines | Class | Notes |
|---|---|---:|---|---|
| `UCC Ask - Student Journey.py` | `ucc_ask_student_journey` | 4,208 | `[ADAPT]` | Largest single file in the repo. 85 functions. **Contains the only outbound network call in the codebase.** |
| `UCC Ask - Recruitment Agent.py` | `ucc_ask_recruitment_agent` | 2,153 | `[ADAPT]` | 48 functions. Deterministic — no AI path. |
| `UCC Ask - Quality Action.py` | `ucc_ask_quality_action` | 911 | `[ADAPT]` | 33 functions. Deterministic. Has portfolio modes (`global_open`, `global_overdue`, `global_nc`, `global_ofi`). |

**Contract divergence, important for the migration:** the Ask scripts do **not** use the
`payload`-JSON-string convention the analytics scripts use. They read flat `frappe.form_dict` keys
directly — `question`, `student_applicant` / `agent_contract` / `quality_action`, `conversation`,
`student_roll_rows`, `openai_api_key`. Two request conventions exist in the legacy system and the
app must decide deliberately which survives (see `parity-matrix.md` §4).

**AI key handling — `[REBUILD]`, not `[ADAPT]`.**
`UCC Ask - Student Journey.py:4024` reads `frappe.form_dict.get("openai_api_key")` and assigns it
over the module default, which is an empty string literal (`OPENAI_API_KEY = ""` — **no secret is
committed**, verified). That key is then used at `:1627` for a server-side
`frappe.make_post_request("https://api.openai.com/v1/responses", ...)` with an
`Authorization: Bearer` header, model pinned by `OPENAI_MODEL`, `store: False`, strict
`json_schema` response format, `max_output_tokens: 350`.

The browser supplying the provider key per request cannot be carried into the app. The requirement
(optional AI routing with a deterministic fallback — the scripts run guided-mode without a key)
survives; the key transport must be rebuilt onto site config / Frappe secrets. This is a Phase ≥2
item and is listed here only so it is not silently ported.

### 1.3 Shared and auxiliary scripts

| File | Method | Lines | Class | Disposition |
|---|---|---:|---|---|
| `UCC Dashboard Access.py` | `ucc_dashboard_access` | 259 | `[ADAPT]` | **Ported (Phase 2, `ucc_intelligence/ucc_intelligence/permissions/access.py`).** Depends on a `UCC Dashboard Access` DocType — **verified 2026-07-26 not to exist** on `ucc.local` (`DoesNotExistError` via `bench console`), contradicting the "manually created on site" assumption this row originally carried from the script's docstring alone. Whether it exists on the actual legacy Custom HTML Block's production site (if different from `ucc.local`) is unconfirmed. Uses `frappe.get_all(..., ignore_permissions=True)` on `Has Role`; carried forward as-is, approved by Felix 2026-07-26, review before Phase 13. Fail-open by design (`default_when_unconfigured`) — on a site with no such DocType, fail-open is not an edge case, it is the only path ever taken. |
| `UCC Shared - Diagnostics.py` | `ucc_shared_diagnostics` | 433 | `[ADAPT]` | Port. Confirmed live caller (`JAVASCRIPT.js:3199`). Enforces an approved-DocType allow-list (`APPROVED_SOURCE_GROUPS`) — that boundary must survive verbatim. |
| `UCC Shared - Record Search.py` | `ucc_shared_record_search` | 125 | `[ADAPT]` | Port. `ENTITY_CONFIG` allow-list. |
| `UCC Analytics - Bootstrap.py` | `ucc_analytics_bootstrap` | 90 | `[ADAPT]` | **Port only after a caller is confirmed.** No `frappe.call` to this method exists in the deployed JS. Returns filter options + a hard-coded dashboard/module status list that already disagrees with reality. |
| `UCC Analytics - Drilldown.py` | `ucc_analytics_drilldown` | 128 | `[ADAPT]` | **Port only after a caller is confirmed.** No call site in deployed JS; the criterion scripts' own `action:"drilldown"` appears to serve the UI instead. |
| `UCC Analytics - Criterion Catalogue.py` | `ucc_analytics_criterion_catalogue` | 146 | `[ADAPT]` | Static `CRITERIA` data, trivially portable. No known caller. Reports platform version `1.9.5`. |
| `UCC Analytics - Placeholder Preview.py` | `ucc_analytics_placeholder_preview` | 869 | `[ADAPT]` | **Archive candidate.** Returns dummy preview data for "Criteria 1–3 and 6–7", all of which are now live. Pinned at `1.8.4` while everything else is `1.9.5+`. Confirm dead, then archive — do not port. |
| `server-scripts/README.md` | — | 34 | `[REUSE]` | Records the shared-contract decisions; fold into app docs. |

### 1.4 Source surface

**101 distinct candidate DocTypes** are referenced across the seven criterion scripts'
`SOURCE_CANDIDATES` maps (C1 14, C2 43, C3 17, C4 17, C5 21, C6 17, C7 6; overlapping).

Resolution is deliberate and must be preserved: each alias maps to an **ordered candidate list**, and
`resolve_source` probes each candidate with a real 1-row `frappe.get_list` read — not a permission
introspection — recording `resolution_attempts` and `fallback_used`. Source status is one of
`checking` / `available` / `permission_denied` / `unavailable` / `query_error`.

Confirmed mappings that must not regress (from `AI_CONTEXT.md`, enforced by
`tools/validate_package.py`): staff goals → `Goal`; training → `Training Needs Analysis`;
communication approval → `Material Vetting Form`; provider evaluation → `Provider Rating` with
`Supplier Rating` as an approved fallback **in Criteria 3 and 6 only**.

Zero occurrences of `ignore_permissions` or `frappe.has_permission` in any of the seven criterion
scripts — permission enforcement is entirely implicit via `frappe.get_list`.

---

## 2. Deployed frontend (`custom-html-block/`)

Three files pasted into one Frappe Custom HTML Block. **This is the live system**, not `src/` — see
§4.

### 2.1 `JAVASCRIPT.js` — 3,343 lines / 227 KB, seven concatenated IIFEs

| Lines | Module | Class | Notes |
|---|---|---|---|
| 1–265 | `UCC SHARED RUNTIME v1.7.0` | `[REUSE]` | Pure helpers, no Frappe coupling beyond `frappe.call` error shapes: `escapeHtml`, `csvCell`, `tableToCsv`, `download`, `doctypeRoute`, `openDoctype`, `errorText`, `classifyError`, `isPermissionError`, `permissionSource`, `permissionNoticeHtml`, `renderPermissionNotice`, `installPermissionMessageFilter`, `noteBlockedSource`, `blockedSources`, `readStorage`, `writeStorage`. Already covered by two Node self-checks. |
| 266–437 | Platform shell | `[ADAPT]` | Workspace switching, `#uccDashboardSelect`, `localStorage["ucc.dashboard"]`, `?dashboard=` deep-link, `ucc:dashboard-change` custom event. Becomes app routing. |
| 438–2114 | Ask UCC (`#ajaApp`) | `[ADAPT]` | `MODULE_CONFIG` for 3 live modules + 1 `comingSoon` HR stub. Five `frappe.call` sites. |
| 2115–2143 | C4 markers / placeholder tab controls | `[ADAPT]` | Small. |
| **2144–2703** | **`UCC unified dashboard engine v2.0.1`** | `[ADAPT]` | **The entire Analytics workspace.** See below. |
| 2704–3065 | `UCC DIAGRAM EXPLORER v1.9.9` | `[ADAPT]` | Search across visual catalogues. |
| 3066–3343 | `UCC universal visual diagnostics v1.9.9` | `[ADAPT]` | Visual hover menus, invalid-SVG guard, Source Mapping Report (calls `ucc_shared_diagnostics`). |

The unified engine's reusable assets:

- **`CONFIG`** (`:2150`) — one literal declaring all seven criteria: titles, subcriteria, filters,
  `apiMethod`, `defaultSection`, `apiSections`, `panelMap`, and per-section chart definitions.
  Directly portable as data.
- **`CHART_PLUGINS`** (`:2298`) — a `Map` with **16 registered renderers** (`bar`, `donut`, `funnel`,
  `lifecycle`, `flow`, `matrix`, `radar`, `trend`, `gauge`, `admission-line`, `admission-column`,
  `decision`, `network`, `reconciliation`, `ladder`, `risk-matrix`), dispatched by `renderChart`
  with a silent fallback to `bar`. **Hand-written HTML/inline-SVG string builders — no charting
  library, no D3 in the deployed file** (`grep -c 'd3\.'` → 0). This is why the frontend is portable
  without picking a chart dependency.
- **Failure ladder** in `chartForLive` (`:2447`) — blocked-source notice → no-readable-metric notice
  → non-numeric guard → try/catch render error. `[REUSE]` conceptually; this is the behaviour the
  parity tests must pin.
- **Two-stage lazy render** — `renderLiveChartCard` (metadata only, stashes `_liveCardPending`) then
  `renderLiveChartCardNow` (draws once, caches via `dataset.liveCardRendered`).

Known fragilities to fix on port, not carry across (all `[REBUILD]`, all small):

- `panelInsertPoint` (`:2238`) locates its DOM anchor by regex-matching the literal string
  `Management Questions and Data-Based Answers` against `textContent`.
- `metricRows` (`:2407`) selects a chart's data source by regex on the **human-readable title**
  (`/source availability|evidence readiness|source readiness/`).
- `standardise_response_contract` defaults `ok` to `True`, so a script failing before setting `ok`
  still satisfies the client's `if (message && message.ok)` gate.

### 2.2 `CSS.css` — 2,105 lines / 151 KB — `[REUSE]` with rescoping

Organised as dated patch bands, not components. Everything is scoped via the `.ucc-platform` class;
`#uccIntelligencePlatform` has no ID selector anywhere. **Every Analytics CSS class is emitted from a
JS template literal — none appears in `HTML.html`**, so there is no build-time check tying them
together. Brand tokens `#26345B` (UCC Blue) / `#CE9E5D` (UCC Gold); chart palette wraps at six via
`--ucc-chart-0..5`.

### 2.3 `HTML.html` — 57 lines / 16 KB — `[REBUILD]`

Static shell only: platform chrome, workspace nav, `#uccDashboardSelect` with seven hard-coded
options, **seven empty mount divs**, Explore markup, Ask UCC markup, changelog overlay. All
Analytics DOM is generated at runtime. Small enough that rebuilding it as an app page/workspace
template is cheaper than porting.

### 2.4 `custom-html-block/DEPLOYMENT_NOTES.md` — `[REUSE]`

13 KB, includes the practical "How to Add or Remove Graphs" guide and the three-graph-architecture
table. Fold into app docs.

---

## 3. Supporting assets

| Path | Class | Notes |
|---|---|---|
| `reference/*.json` (10 files) | `[REUSE]` | Machine-readable registries: dashboards, field mappings (18 KB), policies, guided questions, DocTypes, C4 visual registry, Ask module registry, shared components, package manifest. Portable as app fixtures/data. |
| `documentation/` (78 files) | `[REUSE]` | Per-criterion field references, DocType inventories, open items, API contracts. Several top-level files are version-stamped stale and open with a self-correcting "current-state notice". |
| `tools/test_permission_notice.js` | `[REUSE]` | 28 assertions against the real shared runtime. |
| `tools/test_roll_fallback.js` | `[REUSE]` | 5 cases, Ask UCC roll-failure path. |
| `tools/test_dashboard_access.py` | `[REUSE]` | 20 scenarios incl. a role-leak regression. |
| `tools/test_drop_server_message.py` | `[REBUILD]` | **Currently failing.** Asserts a `drop_server_message()` that was deliberately deleted in `30db7af`. Delete the test; do not restore the function. |
| `tools/validate_package.py` | `[ADAPT]` | Some checks survive (Python/JSON parse, brand colours, secret markers); the build-output-matches-source checks become meaningless once the app bundles assets. |
| `tools/build_custom_block.py` | `[REBUILD]` | Obsolete under an app: `bench build` replaces it. **Do not run it** — see §4. |
| `VERSION.json`, `build-manifest.json`, `PACKAGE_CHECKSUMS.json` | `[REBUILD]` | Replaced by app metadata. All three are stale (§4). |

---

## 4. State-of-the-repo findings that constrain the migration

These are not opinions; each is verified and each changes how Phase 1+ must proceed.

1. **`src/` is NOT the source of the deployed build.** Both independent reports in `docs/` and my own
   byte comparison agree. The deployed `custom-html-block/JAVASCRIPT.js` is the *newer* artefact
   (`unified dashboard engine v2.0.1`, all 7 criteria in `CONFIG`, 16 chart plugins, 0 D3 refs, 227 KB);
   `src/js/` is the *older* world (`v1.9.6`, 5 criteria, 0 plugin registrations, 57 D3 refs, 465 KB).
   **Running `tools/build_custom_block.py` would overwrite the deployed engine with the pre-2.0.1
   one.** Recent commits (`ae75295`, `a142e69`, `f377c5f`, `242ef3b`, `49361a8`) patched
   `custom-html-block/` by hand, sometimes mirroring into `src/`, sometimes not.
   → **The migration's frontend source of truth is `custom-html-block/`, and `src/` is
   `[ARCHIVE]`.** It must not be deleted (final-state rule) and must not be treated as input.

2. **`tools/validate_package.py` fails 7 of 101 checks on a clean tree** — the three
   built-matches-source checks plus four source-string assertions. That is the pre-existing baseline,
   not a regression to chase.

3. **Version metadata disagrees across at least eight places**: `VERSION.json` `1.9.5`,
   `build-manifest.json` `1.9.5`, deployed HTML/engine `2.0.1`, shared runtime banner `1.7.0`,
   changelog overlay `1.9.9`, `CHANGELOG.md` newest entry `1.9.8-c531-migrate`, Bootstrap script
   `1.9.15`, C5 `meta.platform_version` `2.0.2-intake-expanded-questions`, response
   `contract_version` `2.1.0`. The app needs one version source; `CHANGELOG.md` + git log are the
   only trustworthy history today.

4. **`dist/`, `custom-html-block/` and `PACKAGE_CHECKSUMS.json` are three-way divergent.**
   `dist/checksums.json` matches `dist/` only.

5. **Two Server Scripts have no discoverable caller** (`ucc_analytics_bootstrap`,
   `ucc_analytics_drilldown`) and one is very likely dead (`ucc_analytics_placeholder_preview`).
   Confirm against the live site before porting — a caller may exist outside this repo.

6. **`overview` sections in C4/C5 appear unreachable.** Both scripts define full `overview` metric
   sets, but the frontend's `apiSections` rewrites `overview` → first subcriterion for all seven
   criteria. No caller sends `subcriterion:"overview"`.

7. **C5 tabs 5.4 and 5.5 defeat the client result cache.** `SUBCRITERION_ALIASES` canonicalises
   `5.4`→`5.4.1`, the contract writes the canonical value into `meta.subcriterion`, and the client
   caches on `meta.subcriterion === section` where section is `"5.4"`. They refetch every visit.
   Port the behaviour, then decide — do not silently "fix" it during a parity phase.

---

## 5. Not inventoried this pass

- Runtime behaviour of anything. Everything above is static reading; nothing was executed against a
  Frappe site.
- Full line-level read of the three Ask UCC scripts (7,272 lines combined) — headers, request
  params, action surfaces, function counts and the OpenAI path were read; the per-question answer
  logic was not.
- `UCC Analytics - Placeholder Preview.py` internals (869 lines) — classified from its docstring and
  the fact that its target criteria are all live.
- `archive/legacy-source/` and `custom-html-block/archive/` contents (pre-existing archives, 148 KB).

## 6. §19 item this inventory surfaces but cannot resolve

**"Which current Server Scripts are actually deployed"** (CLAUDE.md §19). Everything in §1 above is
classified from the 17 files present in `server-scripts/` in this repository — that is repo
presence, not confirmed deployment. `docs/analytics_workspace_report_2.md` independently confirmed
two live call sites from the deployed JS (`ucc_shared_diagnostics`, `ucc_dashboard_access`) and the
seven `ucc_analytics_criterion_N` methods via `config.apiMethod`; the three Ask UCC methods are
confirmed live via `MODULE_CONFIG.apiMethod` in the same deployed file. That leaves four scripts
(`ucc_analytics_bootstrap`, `ucc_analytics_drilldown`, `ucc_analytics_criterion_catalogue`,
`ucc_analytics_placeholder_preview`, §1.3) whose presence in this repo does not by itself mean they
are installed as enabled Server Scripts on the live site, or that the live site doesn't have
*additional* scripts not mirrored into this repo at all. This is genuinely unresolvable from static
repo reading — it needs a Server Script list view export from the actual site, which is exactly the
`docs/environment-discovery-template.md` §4 row "Server Scripts present on the site" and the two rows
below it ("in this repo not on site" / "on site not in this repo"). Not decided here; carried
forward as an open blocker rather than assumed either way.
