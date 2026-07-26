# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The UCC Intelligence Platform: an EduTrust Criterion 1–7 analytics dashboard that runs **inside a Frappe/ERPNext site**, not as a standalone app. There is no npm, no bundler, no framework. It ships as exactly two kinds of artifact:

1. **One Frappe Custom HTML Block** — three fields (HTML, CSS, JavaScript) pasted into the ERPNext UI. Built by concatenating `src/` files.
2. **Standalone Frappe API Server Scripts** — each `server-scripts/*.py` is pasted into ERPNext as a separate Server Script of type API. They share no imports and no module; each is fully self-contained.

Nothing here can be run locally end to end. Verification is static checks + Node/Python self-checks; the real flow only exists on the live Frappe site.

## Commands

```bash
python3 tools/build_custom_block.py     # concat src/ -> custom-html-block/ + dist/  (see warning below)
python3 tools/validate_package.py       # 100+ static checks; the project's main gate
python3 tools/test_dashboard_access.py  # role -> visible-dashboard resolution
node tools/test_permission_notice.js    # shared permission-denied notice (runs real 00-shared-runtime.js)
node tools/test_roll_fallback.js        # Ask UCC student-roll failure path
```

Each `tools/test_*` file is a standalone self-check with no framework — run one by invoking it directly. They work by reading the real source and `exec`/`new Function`-ing the function under test against a stubbed `frappe`, so they break when a function is renamed or removed (this is intended: `test_drop_server_message.py` currently fails because `drop_server_message()` was deliberately deleted in 30db7af — delete the test, don't restore the function).

## Build outputs have drifted from source — read before editing

`custom-html-block/` and `dist/` are **committed build outputs, and they no longer match `src/`**. Recent hotfixes were applied by hand to the deployed build (e.g. ae75295 "Apply Ask UCC permission fix directly to the deployed build"), and `custom-html-block/HTML.html` reports `data-platform-version="2.0.1"` while `src/html/platform.html` reports `1.9.6`.

Consequences:

- **Running `build_custom_block.py` overwrites `custom-html-block/` with the older `src/` content and destroys deployed fixes.** Do not run it as a routine step. Only run it if you have confirmed `src/` is genuinely ahead.
- The prevailing pattern in recent commits is to make the same edit **twice** — once in `src/js/…` and once in `custom-html-block/JAVASCRIPT.js` (and `src/css/platform.css` + `custom-html-block/CSS.css`). Follow it unless told otherwise.
- `validate_package.py` therefore fails ~7 checks on a clean tree (the three "built X matches source manifest" checks plus a few source-string assertions). Compare against the pre-existing failures rather than expecting a green run.

Version metadata is also inconsistent across `VERSION.json` (1.9.5), `src/html/platform.html` (1.9.6), the deployed block (2.0.1), the Bootstrap script (1.9.15) and `CHANGELOG.md` (1.9.8-*). Treat `CHANGELOG.md` and git log as the truth about what actually changed; treat `VERSION.json` as a validator fixture.

## Frontend architecture

`build-manifest.json` defines the concatenation order, and the order matters — `00-shared-runtime.js` must define `window.UCCShared` first, and `30-live-foundation-runtime.js` must define `UCCLiveVisualDefinitions` before `20-explore-runtime.js` consumes it.

| File | Role |
|---|---|
| `src/js/00-shared-runtime.js` | `window.UCCShared`: escaping, CSV, downloads, DocType routing, `classifyError`/`errorText`, the permission-denied notice, storage. New code reuses this — per-criterion copies of exports, dialogs or D3 loaders are not permitted. |
| `src/js/10-platform-runtime.js` | ~6k lines: platform shell, Criterion 4, Criterion 5, Ask UCC. The bulk of everything. |
| `src/js/30-live-foundation-runtime.js` | `CONFIG`-driven generic dashboard for Criteria 1, 2, 3, 6, 7 — one `frappe.call` shape for all five. |
| `src/js/20-explore-runtime.js` | Diagram Explorer, reads the visual definitions from the other runtimes. |
| `src/js/40-visual-navigation-runtime.js` | Visual hover menus, blank/invalid-SVG guard, Source Mapping Report dialog. |

Each runtime is an IIFE guarded by a `platform.dataset.<name>Ready === "1"` flag and scopes itself to `root_element` (the Custom HTML Block element) falling back to `document`. Anything appended to the document body escapes Frappe's scoped CSS and loses its styling — overlays must stay inside `#uccIntelligencePlatform`.

**Three coexisting dashboard architectures.** Do not assume one pattern generalises:

- Criteria 1, 2, 3, 6, 7 — generated from `LIVE_VISUAL_EXPANSION` in `30-live-foundation-runtime.js`.
- Criterion 4 — generated from `C4_VISUAL_EXPANSION` in `10-platform-runtime.js`, plus exact metric/stage diagrams from `C4_VISUAL_REGISTRY` in `UCC Analytics - Criterion 4.py`.
- Criterion 5 — hand-written static cards in `src/html/platform.html` (`data-chart="…"`) with D3 draw functions in `10-platform-runtime.js`, plus a `C5_DISABLED_VISUALS` set. It's the odd one out and the reference implementation the others copied CSS from.

Retired visuals are **not deleted**: they carry `enabled:false` (LIVE/C4) or sit in `C5_DISABLED_VISUALS`, and are documented in `documentation/archived-visuals.md`. `validate_package.py` asserts exact active counts per criterion (30/30/30/30/28/30/30) — adding or removing a visual means updating `EXPECTED_VISUALS` and `VERSION.json.visual_targets` together.

## Server Script architecture

Naming is contractual: file `UCC Analytics - Criterion 1.py` → API method `ucc_analytics_criterion_1`. Prefixes are `UCC Analytics - …` (`ucc_analytics_*`), `UCC Ask - …` (`ucc_ask_*`), `UCC Shared - …` (`ucc_shared_*`).

Every analytics script follows the same shape: read `frappe.form_dict["payload"]` (a JSON string), clamp `page`/`page_size`/`limit`, reject anything outside `ALLOWED_ACTIONS` (`summary`, `source_status`, `policy_registry`, `requirement_registry`, `question_registry`, `drilldown`), then assign the result to `frappe.response["message"]`. The frontend always calls with `args: {payload: JSON.stringify({action, subcriterion, filters, …})}`.

Scripts run under Frappe's `safe_exec` (RestrictedPython). `frappe`, `json` and `frappe.utils` are pre-provided; **no imports, no leading-underscore names, no `next()`, no `id()`**, and augmented assignment to a subscript has bitten this codebase before (c914c6e). Test by exec'ing the function against a stubbed `frappe`, as `tools/test_*.py` do.

`UCC Dashboard Access.py` (`ucc_dashboard_access`) gates **UI composition only** — which tabs get built for a user's roles. It is not a permission system; every data read is still enforced by Frappe DocType permissions. Never let it be described or used as access control.

## Domain rules that bite

- **Confirmed DocType mappings** (from `AI_CONTEXT.md`): staff goals → `Goal`; training → `Training Needs Analysis`; communication approval → `Material Vetting Form`; provider evaluation → `Provider Rating`, with `Supplier Rating` as an approved fallback in Criteria 3 and 6 only. Do not reintroduce the retired Criterion 2 source aliases — `validate_package.py` checks for them.
- Resolve an optional DocType with `frappe.db.exists` **before** querying it; a missing DocType raises `DoesNotExistError` (HTTP 404) and produces a misleading permission-flavoured error otherwise.
- **Missing ≠ zero. Permission denied ≠ no records.** A blocked source renders the shared `UCCShared.renderPermissionNotice` explanation in place of the chart, never an empty/0 state. Raw Frappe exception text must not reach the visible body (it's kept in a `title` attribute for support).
- Brand: UCC Blue `#26345B`, UCC Gold `#CE9E5D`, white text on blue, dark text on gold. Styles scope under `.ucc-platform`, `.ucc-c5-v41` or `.aja-app`. Validation asserts both hex values are present.
- Never accept an arbitrary DocType from the browser; approved allow-lists only (`UCC Shared - Diagnostics.py` documents this boundary explicitly).

## Where to look things up

`documentation/` carries per-criterion folders (`criterion-N/` with field references, DocType inventories, open items) plus cross-cutting guides. Several top-level docs are stamped with old version numbers and open with a "current-state notice" correcting themselves — read the notice first. `reference/*.json` holds the machine-readable registries (dashboards, field mappings, policies, guided questions). `custom-html-block/DEPLOYMENT_NOTES.md` is the practical "how to add or remove a graph" guide.
