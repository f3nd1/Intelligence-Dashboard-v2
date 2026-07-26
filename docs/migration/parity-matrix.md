# Parity Matrix — Phase 0

Every user-visible behaviour of the legacy system, its current owner file, its intended owner in
`ucc_intelligence`, and **how parity will be proven**. A row cannot be marked done — and its legacy
owner cannot be archived — until its verification passes.

> **Update.** The real 13-phase `CLAUDE.md` now exists at repo root (`a4b8641` / merged in `f7f7286`);
> the format caveat that used to be here is resolved.

Legend: `[REUSE]` portable as-is · `[ADAPT]` logic portable, contract changes · `[REBUILD]`
requirement survives, implementation does not.

New-owner paths are **proposed**, not built. Nothing in this matrix exists yet except the Phase 1
scaffold rows.

---

## 1. Analytics workspace

| # | Behaviour | Legacy owner | Class | Proposed new owner | Parity verification |
|---|---|---|---|---|---|
| A1 | Seven criterion dashboards, one visible at a time | `custom-html-block/JAVASCRIPT.js:2144-2703` + `HTML.html:6` | `[ADAPT]` | `ucc_intelligence/public/js/analytics/engine.js` | All seven selectable; each renders its shell without console errors |
| A2 | Per-criterion `CONFIG` (titles, subcriteria, filters, apiSections, panelMap) | `JAVASCRIPT.js:2150` | `[ADAPT]` | `ucc_intelligence/public/js/analytics/config.js` | Diff the ported literal against the deployed one — must be value-identical |
| A3 | Summary fetch per subcriterion | `callApi` `JAVASCRIPT.js:2334` | `[ADAPT]` | app JS + whitelisted method | Same request shape reaches the server for all 7×N sections |
| A4 | Result caching on `meta.subcriterion` | `loadLive` `:2570` | `[ADAPT]` | same | Switching tab and back issues exactly the legacy number of calls (incl. the C5 5.4/5.5 refetch, item O5) |
| A5 | Tab switching; Sources & Data Quality never fetches | `showTab` `:2571` | `[ADAPT]` | same | Network trace: 0 calls on switching to `sources` |
| A6 | Two-stage lazy chart render (defer, then draw once) | `renderLiveChartCard` `:2469` / `renderLiveChartCardNow` `:2491` | `[ADAPT]` | same | A card draws at most once; off-screen sections do not draw |
| A7 | 16 chart renderers dispatched by `chart.type` | `CHART_PLUGINS` `:2298-2315` | `[ADAPT]` | `ucc_intelligence/public/js/analytics/charts/` | Each of the 16 types renders; unknown type falls back to `bar` |
| A8 | Chart failure ladder (blocked → no rows → non-numeric → render error) | `chartForLive` `:2447` | `[ADAPT]` | same | Four synthetic responses, one per rung, produce the four distinct UIs |
| A9 | KPI strip, 6-column, blocked notice spans full row | `renderKpis` `:2501` + `CSS.css:2105` | `[ADAPT]` | same | Visual check + blocked-source case |
| A10 | Readiness banner, shared across all 7 | `renderReadiness` + `.ucc-readiness-strip` `CSS.css:1862` | `[ADAPT]` | same | `data-status` variants render for available/warning/error/loading |
| A11 | Q&A table merging `questions` with unreferenced `metrics` | `extendedQuestionRows` | `[ADAPT]` | same | Synthetic response with an unreferenced metric produces the synthesised row |
| A12 | Sources + Data Quality tables | `renderSources` / `renderQuality` | `[ADAPT]` | same | Row counts match the response arrays |
| A13 | Drill-down to records | `openRecords` / `openMetricRecords` `:2662` | `[ADAPT]` | same | Opens the same DocType route for the same metric |
| A14 | Per-dashboard diagnostics ring buffer (500 entries) + export | `logEvent` `:2229`, `showDiagnostics` `:2597` | `[ADAPT]` | same | Events logged for request/success/error; export produces the same columns |
| A15 | Archived visuals stay defined but hidden | `enabled:false` filter `:2257` | `[ADAPT]` | same | Active counts stay 30/30/30/30/28/30/30 |

## 2. Analytics server contract

| # | Behaviour | Legacy owner | Class | Proposed new owner | Parity verification |
|---|---|---|---|---|---|
| S1 | `ucc_analytics_criterion_1` | `server-scripts/UCC Analytics - Criterion 1.py` | `[ADAPT]` | `ucc_intelligence/api/analytics/criterion_1.py` | Golden-response diff vs legacy for every action × subcriterion |
| S2 | `ucc_analytics_criterion_2` | `…Criterion 2.py` | `[ADAPT]` | `…/criterion_2.py` | as S1 |
| S3 | `ucc_analytics_criterion_3` (7 actions) | `…Criterion 3.py` | `[ADAPT]` | `…/criterion_3.py` | as S1, plus `question_catalogue` |
| S4 | `ucc_analytics_criterion_4` | `…Criterion 4.py` | `[ADAPT]` | `…/criterion_4.py` | as S1 |
| S5 | `ucc_analytics_criterion_5` | `…Criterion 5.py` | `[ADAPT]` | `…/criterion_5.py` | as S1, plus alias handling for 5.4/5.5 |
| S6 | `ucc_analytics_criterion_6` | `…Criterion 6.py` | `[ADAPT]` | `…/criterion_6.py` | as S1 |
| S7 | `ucc_analytics_criterion_7` | `…Criterion 7.py` | `[ADAPT]` | `…/criterion_7.py` | as S1 |
| S8 | Shared response contract `2.1.0` | `standardise_response_contract` ×7 (byte-identical) | `[ADAPT]` | **Built** `ucc_intelligence/ucc_intelligence/analytics/contracts.py` (Phase 2) | Diffed against the live legacy function across 3 fixtures — outputs equal, not just similar (`tools/test_ucc_intelligence_contracts.py`, passing). Not wired to any criterion script yet — that's Phase 4. |
| S9 | Ordered candidate source resolution + fallback | `resolve_source` ×7 | `[ADAPT]` | Deferred to Phase 4 — out of Phase 2's scope | Same alias→DocType winner and same `resolution_attempts` for a given site |
| S10 | Permission-error classification | `is_permission_error` ×7 (C7 also matches `"403"`) | `[ADAPT]` | **Built** `ucc_intelligence/ucc_intelligence/analytics/contracts.py` (Phase 2) — decided: `"403"` check applied universally, verified against the one input where legacy C1–C6 and C7 genuinely diverge (`tools/test_ucc_intelligence_contracts.py`, passing) | |
| S11 | Field allow-listing | `SAFE_FIELDS` + `safe_fields()` ×7 | `[REUSE]` | shared helper | No field requested that isn't on the resolved DocType |
| S12 | Page-size / row-limit clamps (200 / 2000–5000) | preamble ×7 | `[REUSE]` | shared helper | Out-of-range values clamp identically |
| S13 | Action allow-list rejection | `ALLOWED_ACTIONS` ×7 | `[REUSE]` | shared helper | Unknown action throws, does not 500 |

## 3. Access, diagnostics, shared services

| # | Behaviour | Legacy owner | Class | Proposed new owner | Parity verification |
|---|---|---|---|---|---|
| X1 | Role → visible workspaces/criteria (UI composition only) | `server-scripts/UCC Dashboard Access.py` | `[ADAPT]` | **Built** `ucc_intelligence/ucc_intelligence/permissions/access.py` + `api.py` shim (Phase 2) | All 20 scenarios from `tools/test_dashboard_access.py`, re-run against the real ported module in `tools/test_ucc_intelligence_access.py`, passing incl. the role-leak regression |
| X2 | `UCC Dashboard Access` configuration DocType | manually created on site (not in repo) | `[REBUILD]` | **Decided (O7 resolved): reuse + convert to app-managed.** Drafted at `docs/migration/phase-2-doctype-draft/`, not yet placed — module-name folder depth and `autoname`/`permissions` need one live-site confirmation, see `phase-2-plan.md` §5 | DocType installs with the app; existing site rows still resolve |
| X3 | Fail-open on access-check failure (8 s client timeout) | `fetchDashboardAccess` `:2604` | `[ADAPT]` | Deferred — this is frontend consumer behaviour, out of Phase 2's scope (no page mounts dashboards until Phase 3) | Server 500 / timeout still yields a usable UI |
| X4 | Hidden criteria removed from DOM **and** `CONFIG` before mount | `applyDashboardAccess` `:2625` | `[ADAPT]` | app JS | A hidden criterion has no tab bar and no config entry |
| X5 | Source Mapping Report | `UCC Shared - Diagnostics.py` + `JAVASCRIPT.js:3199` | `[ADAPT]` | `ucc_intelligence/api/diagnostics.py` | Same candidate/metadata/field inventory for the same criterion |
| X6 | Approved-DocType boundary (no arbitrary DocType from browser) | `APPROVED_SOURCE_GROUPS` | `[REUSE]` | same | Request for an unlisted DocType is rejected |
| X7 | Record search for selectors | `UCC Shared - Record Search.py` | `[ADAPT]` | `ucc_intelligence/api/record_search.py` | Same `ENTITY_CONFIG` results |
| X8 | Shared permission-denied notice | `JAVASCRIPT.js:1-265` (`UCCShared`) | `[REUSE]` | **Built** `ucc_intelligence/public/js/shared.js` (Phase 2) — byte-identical copy of `src/js/00-shared-runtime.js`, diffed to confirm | `tools/test_permission_notice.js` (28 assertions) still passes against the source unchanged; new loader smoke test at `ucc_intelligence/ucc_intelligence/tests/test_shared_runtime.js` confirms the ported copy resolves and initialises |
| X9 | Suppression of Frappe's raw permission dialog | `installPermissionMessageFilter` | `[REUSE]` | same (ported unchanged in the same file) | Raw `PermissionError` text never reaches the visible body |
| X10 | Filter options bootstrap | `UCC Analytics - Bootstrap.py` | `[ADAPT]` | deferred | **Confirm a caller exists first** — none in deployed JS |
| X11 | Generic drilldown endpoint | `UCC Analytics - Drilldown.py` | `[ADAPT]` | deferred | **Confirm a caller exists first** — none in deployed JS |
| X12 | Criterion catalogue | `UCC Analytics - Criterion Catalogue.py` | `[ADAPT]` | deferred | No known caller |
| X13 | Dummy preview data | `UCC Analytics - Placeholder Preview.py` | `[ADAPT]` | **none — archive candidate** | Confirm no caller, then archive; all target criteria are live |

## 4. Ask UCC

| # | Behaviour | Legacy owner | Class | Proposed new owner | Parity verification |
|---|---|---|---|---|---|
| Q1 | Student Journey assistant | `UCC Ask - Student Journey.py` (4,208 ln) | `[ADAPT]` | `ucc_intelligence/api/ask/student_journey.py` | Same answer for the same question × pinned student on the same data |
| Q2 | Recruitment Agent assistant | `UCC Ask - Recruitment Agent.py` (2,153 ln) | `[ADAPT]` | `…/recruitment_agent.py` | as Q1, per agent contract |
| Q3 | Quality Action assistant, incl. portfolio modes | `UCC Ask - Quality Action.py` (911 ln) | `[ADAPT]` | `…/quality_action.py` | as Q1, plus `global_open`/`global_overdue`/`global_nc`/`global_ofi` |
| Q4 | Ask UCC frontend, 3 modules + HR "coming soon" | `JAVASCRIPT.js:438-2114` | `[ADAPT]` | `ucc_intelligence/public/js/ask/` | Module switch, pin, recent list, guided questions all work |
| Q5 | Student roll fallback on failure | `handleRollFailure` / `loadStudentDirectoryFallback` | `[REUSE]` | same | `tools/test_roll_fallback.js` (5 cases) passes unchanged |
| Q6 | **Request convention** — flat `form_dict` keys, not the analytics `payload` JSON string | all 3 Ask scripts | `[REBUILD]` | one convention app-wide | **Decision required** — see O2 |
| Q7 | Optional AI routing with deterministic fallback | `UCC Ask - Student Journey.py:1627` | `[ADAPT]` | Phase ≥2 | Guided mode returns identical answers with no key present |
| Q8 | **OpenAI key supplied by the browser per request** | `…Student Journey.py:4024` | `[REBUILD]` | site config / Frappe secrets | Key never crosses the client boundary; no key in any request payload |

## 5. Explore workspace

| # | Behaviour | Legacy owner | Class | Proposed new owner | Parity verification |
|---|---|---|---|---|---|
| E1 | Diagram Explorer search/filter across catalogues | `JAVASCRIPT.js:2704-3065` | `[ADAPT]` | `ucc_intelligence/public/js/explore/` | Same result set for the same query |
| E2 | Visual hover menus | `JAVASCRIPT.js:3066-3343` | `[ADAPT]` | `…/visual_navigation.js` | Menu opens scoped inside the platform root |
| E3 | Invalid-SVG / blank-visual guard | `invalidSvgReason` | `[REUSE]` | same | `NaN`/`undefined`/`Infinity` in a path is caught before render |

## 6. Phase 1 scaffold rows (this session's scope)

| # | Behaviour | Legacy owner | Class | New owner | Parity verification |
|---|---|---|---|---|---|
| P1 | App exists and installs/uninstalls cleanly | — (new) | — | `ucc_intelligence/` | `bench --site <dev> install-app` then `uninstall-app`, both exit 0 |
| P2 | One module | — (new) | — | `ucc_intelligence/ucc_intelligence/` | Module appears in the app's `modules.txt` |
| P3 | One role-restricted workspace | conceptually X1 | `[REBUILD]` | **Descoped from Phase 1** (Felix, 2026-07-26) — not built, not tracked. `phase-1-plan.md` §6 | N/A |
| P4 | Health-check whitelisted method | — (new) | — | `ucc_intelligence/api.py` | `frappe.call` returns `ok` |
| P5 | Zep adapter interface stub | — (new) | — | **Deferred out of Phase 1** — CLAUDE.md §9 Phase 1's required-work list has no memory/Zep item; that's Phase 10 ("Support one of the following after a documented decision" / "Implement provider interface"). See `phase-1-plan.md` §1. | N/A this phase |

---

## 7. Open decisions this matrix cannot make

These change more than one row and must be answered before the phases that touch them. None is
decided here.

| ID | Decision | Blocks |
|---|---|---|
| O1 | Frontend delivery: keep a Custom HTML Block, or serve app-bundled assets via a Frappe Page/Workspace? | A1–A15, E1–E3, Q4 |
| O2 | One request convention app-wide, or preserve both (`payload` JSON string for analytics, flat `form_dict` for Ask)? | S1–S7, Q1–Q3, Q6 |
| O3 | Dedupe the seven copies of `standardise_response_contract`/`resolve_source` during the port, or port verbatim and dedupe in a later phase? Porting verbatim keeps golden-response diffs clean; deduping early risks silent drift. | S1–S10 |
| O4 | Does the `dashboard_studio` "Publish to Sophia" contract write into the same DocTypes as X2, or its own? **Assumption stated, not decided:** the publish contract is a *separate inbound* surface and shares no DocType with `UCC Dashboard Access`. Nothing in Phase 1 depends on it; do not name a DocType `Dashboard` or `Publish*` until the contract is known. | X2, all future publish work |
| O5 | Keep the C5 5.4/5.5 cache-defeating behaviour bug-for-bug during parity, then fix in a named phase? | A4, S5 |
| O6 | Do `ucc_analytics_bootstrap`, `ucc_analytics_drilldown`, `ucc_analytics_criterion_catalogue` and `ucc_analytics_placeholder_preview` have callers outside this repo? | X10–X13 |
| O7 | **Resolved (Felix, 2026-07-26):** reuse the existing `UCC Dashboard Access` DocType, convert it to app-managed, keep fields/behaviour exactly as-is. Drafted, not yet placed — two facts (module-name folder depth, `autoname`/`permissions`) still need one live-site confirmation before the draft can move to its real path. See `phase-2-plan.md` §5. | X1, X2 |
