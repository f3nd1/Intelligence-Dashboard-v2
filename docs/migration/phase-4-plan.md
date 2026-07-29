# Phase 4 Plan — Migrate Criterion 1 (first of seven)

**Status: plan only, no code written yet.** Per CLAUDE.md §9 Phase 4 goal: "Move the seven Analytics
Server Scripts into version-controlled Python modules without changing result semantics." This plan
covers **Criterion 1 only** — CLAUDE.md's suggested order (1 → 3 → 7 → 2 → 6 → 4 → 5) explicitly says
"adjust based on actual complexity discovered," so before committing to that order for all seven I
checked it against the real files rather than taking it on faith. Findings below; short version:
nothing found that argues against starting with Criterion 1.

## 0. Three decisions this plan does not make silently

**Decision A — one whitelisted method per criterion, or one generic dispatcher?**

CLAUDE.md §11.1 suggests a single endpoint, `ucc_intelligence.api.analytics.get_criterion_summary`.
The current deployed reality is seven separate Server Script methods
(`ucc_analytics_criterion_1` through `_7`), each with genuinely different business logic beneath a
shared shape (see §3). A generic dispatcher (`get_criterion_summary(criterion="1", ...)`) would need
runtime branching to seven different implementations regardless — it doesn't remove any code, it just
moves the branch point.

**Recommending: one whitelisted method per criterion** (`ucc_intelligence.api.analytics.get_criterion_1`,
`get_criterion_2`, ...) for now — matches the existing 1:1 structure exactly, no dispatcher to keep in
sync as each criterion is ported one at a time over multiple phases, and nothing stops a thin
`get_criterion_summary` wrapper being added later, once all seven exist, if a single stable public
surface turns out to matter. Building that wrapper now, before six of the seven implementations exist,
would be exactly the kind of premature abstraction CLAUDE.md's own guidance elsewhere warns against.

**Decision B — does Criterion 1's port change what the frontend calls, in the same change?**

Phase 3's shipped page currently calls the legacy Server Script directly
(`method:"ucc_analytics_criterion_1"` — unchanged from `custom-html-block/JAVASCRIPT.js`, since Phase 3
only swapped the *access-check* endpoint, not the per-criterion data calls; see
`docs/migration/phase-3-plan.md` §3).

**Recommending: ship Criterion 1's port dark** — build and test the new method, but leave the frontend
pointed at the legacy Server Script until parity is actually confirmed on your bench. Cutting the
frontend over is then a separate, one-line, easily-reverted change made once you've compared live
responses and are satisfied, not bundled into the same commit as an unverified port. Matches how every
prior phase in this migration has worked (Phase 2's DocType, Phase 3's page — both additive until
explicitly confirmed, nothing switched over speculatively).

**Decision C — how much of the shared evaluation engine to extract now vs. later**

Real finding, not assumed (see §3): beneath each criterion's own metric/question catalogue sits a
suite of lower-level helpers (`fetch_rows`, `resolve_field`, `evaluate_metric`, `row_matches`, etc.)
that look shared across all seven scripts. I checked this directly rather than guessing, and the
picture is mixed — some functions are byte-identical across all seven, some are identical in most but
diverge in a few, some are genuinely criterion-specific. Extracting the wrong thing as "shared" would
silently change behaviour for whichever criterion actually differs.

**Recommending**: extract only what's *verified* identical as part of Criterion 1's port
(`lower_text`, `is_truthy` — confirmed byte-identical across all seven, zero risk), leave the
"mostly-identical-but-not-quite" functions (`clean_text`, `field_exists`, `resolve_field`,
`safe_fields`) as Criterion-1-local for now, and re-check each one against its own byte-for-byte
diff *at the point each later criterion is actually ported* — pulling a function into
`analytics/engine.py` only once two or more real criteria are confirmed to need the exact same code,
not preemptively. This is slower than extracting everything now on the assumption it's all shared, but
avoids the exact class of mistake CLAUDE.md's own Phase 5 guidance warns about (Criterion 4/5 "special
cases" existing precisely because something looked shared and wasn't).

**This plan is written assuming all three recommendations above. Say so before I write code if any
should go differently — none of them are hard to change.**

---

## 1. What Phase 4 required work actually is (CLAUDE.md §9)

- Copy Criterion 1's logic into an app module.
- Remove Server Script assumptions (`frappe.form_dict`, global-scope execution) where a clearer
  function signature is possible.
- Preserve normal Frappe permission enforcement — same `frappe.get_list` calls, same
  try/except-classify-as-`permission_denied` pattern, nothing bypassed.
- Define a validated request payload and a stable response contract.
- Add unit/integration tests.
- Compare legacy and new responses on the same test data.
- Document known intentional differences.

## 2. Order check — why Criterion 1 first, verified not assumed

| Criterion | Lines | Top-level functions |
|---|---:|---:|
| 1 | 1,846 | 22 |
| 2 | 1,827 | 18 |
| 3 | 2,286 | 25 |
| 4 | 3,288 | 33 |
| 5 | 3,398 | 26 |
| 6 | 2,210 | 23 |
| 7 | 2,061 | 19 |

Raw size alone would put Criterion 2 marginally ahead of Criterion 1 (fewer lines, fewer functions),
but the gap is small (19 lines, 4 functions) and size isn't the only signal — Criterion 4 is already
known (from the Insights pilot work) to carry a large special-cased block
(`build_admission_intelligence`, ~450 lines) that inflates its function count without being
representative of the other six. Criterion 1 has no equivalent special block by the same
`grep -n "^def "` scan — its 22 functions are the plain engine-plus-catalogue shape described in §3,
nothing extra bolted on. Combined with CLAUDE.md's explicit "use Criterion 1 as the pilot," and no
concrete finding here that argues against it, keeping Criterion 1 first.

## 3. What's actually in Criterion 1 — mapped to real code

`server-scripts/UCC Analytics - Criterion 1.py`, 1,846 lines, 22 functions, splits into two layers:

**Request parsing (`:24-60`)** — `payload` (JSON, from `frappe.form_dict.get("payload")`) →
`action`/`subcriterion`/`filters`/`metric_id`/`page`/`page_size`/`row_limit`, each clamped/defaulted.
Diffed this exact block against Criterion 3's: the *only* difference is the default `subcriterion`
string (`"1.1.1"` vs `"3.1.1"`). `ALLOWED_ACTIONS` is identical across six of seven criteria
(`["summary", "source_status", "policy_registry", "requirement_registry", "question_registry",
"drilldown"]`); Criterion 3 alone adds `"question_catalogue"`. This parsing block is a genuine,
low-risk extraction candidate — planned as `analytics/request.py`, parameterised by
`default_subcriterion` and `allowed_actions`, built and verified against Criterion 1 first.

**Evaluation engine + catalogue (`:786-1846`)** — the helper suite plus Criterion 1's own metric,
requirement, and question definitions, ending in `standardise_response_contract` (already ported,
byte-identical, in `analytics/contracts.py` from Phase 2 — Criterion 1's copy will be diffed against
that ported version, not re-ported). Hash-compared the shared-looking helpers across all seven files
directly rather than assuming:

| Function | Result |
|---|---|
| `lower_text`, `is_truthy` | **Byte-identical across all 7** — safe to extract now |
| `clean_text` | Identical in 1,2,3,5,6,7; Criterion 4 differs |
| `field_exists` | Two variants: {1,2,3} vs {4,5,6,7} |
| `resolve_field` | Mostly identical; Criterion 4 and Criterion 5 each have their own variant |
| `safe_fields` | Three variants: {1,2}, {3,5,6,7}, {4} |
| `compare`, `row_matches`, `resolve_field_groups` | Genuinely diverge per criterion, or missing entirely in some (Criteria 6/7 have no `row_matches` at all) — staying criterion-local |

This is the evidence behind Decision C above — a real, mixed picture, not "everything's shared" or
"nothing's shared."

## 4. Files touched / untouched

**New**:
- `ucc_intelligence/ucc_intelligence/analytics/engine.py` — the two/three low-level value helpers
  verified byte-identical (or majority-identical, matching Criterion 1's own copy) across all seven
  legacy scripts (Decision C).
- `ucc_intelligence/ucc_intelligence/analytics/request.py` — shared payload parsing (Decision C).
- `ucc_intelligence/ucc_intelligence/analytics/criterion_1.py` — Criterion 1's engine + catalogue,
  ported.
- `tools/test_ucc_intelligence_criterion_1.py` — see §6.

**Corrected mid-build, not as originally planned**: this section originally said the new whitelisted
method would live in a new `ucc_intelligence/ucc_intelligence/api/analytics.py` module, following
CLAUDE.md §7's illustrative package layout. That's wrong for this install, the same class of mistake
as Phase 3's `public/` nesting bug — `api.py` already exists as a **flat module** (Phase 1), and
`sophia_analytics.js` calls `method:"ucc_intelligence.api.get_dashboard_access"`, confirming it. Adding
an `api/` *directory* alongside the existing `api.py` *file* would be a Python import conflict, not
just an aspirational-vs-real mismatch. Caught this before committing anything broken: `get_criterion_1`
is added to the existing `ucc_intelligence/ucc_intelligence/api.py` instead, alongside `health_check`
and `get_dashboard_access`. Revisiting whether `api.py` should become a real package is a real
question once several more criteria are added and the file gets unwieldy — not decided here, and not
blocking this phase.

**Untouched**: `custom-html-block/`, `server-scripts/` (including `UCC Analytics - Criterion 1.py`
itself — stays live and unmodified, per Decision B), `src/`, `dist/`, `archive/`, and every other
already-ported Phase 2/3 file. `sophia_analytics.js` is not touched this phase (Decision B) —
verified this holds by re-checking the diff against the `cb77320` baseline at every commit, same
standing invariant as every prior phase.

## 5. What's needed from you / your bench

1. **Confirm or override Decisions A/B/C above.**
2. **Test data for parity** — the one thing I genuinely cannot do from this repo. I can (and will)
   verify the *port is structurally faithful to the legacy source* the same way Phase 3 did — extract
   the exact function bodies by range, apply only the specific, asserted transformations, diff the
   result against the committed file. That proves the code says the same thing. It does **not** prove
   the code *computes* the same thing against real data, because I have no bench to run either version
   against. Once the port is written, I'll hand you the exact `bench execute` calls to run both the
   legacy Server Script and the new method with the same payload against the same site, and you
   compare the JSON. Flagging this now rather than implying "parity" is achieved by code-reading alone.
3. Once ported and reviewed: `bench build --app ucc_intelligence` + `bench migrate`, then the parity
   comparison above.

## 6. Verification plan

Two layers, matching what I can and can't do without a bench:

- **Structural fidelity (I can do this)**: same extraction-and-diff technique as Phase 3 — pull the
  exact line ranges for each function being ported, assert the *pre-transformation* text matches the
  live legacy source verbatim (so drift in the legacy file raises an error rather than silently
  producing a wrong port), apply only the named transformations (global-scope → function signature,
  `frappe.form_dict` → parameter), diff against the committed file. Extends
  `tools/test_ucc_intelligence_criterion_1.py` in the same spirit as the existing
  `tools/test_ucc_intelligence_access.py` / `test_ucc_intelligence_contracts.py`.
- **Live parity (needs you)**: `bench execute` calls comparing legacy vs. new method output on the
  same payload/data, per §5.2.

## 7. Exit criteria — copied from CLAUDE.md §9 Phase 4, per-criterion

**Criterion 1: complete as of 2026-07-29** (structural + computational parity both verified; see §10 and
§11 below).

- [x] API contract test passes. (`tools/test_ucc_intelligence_criterion_1.py`, 19/19.)
- [x] Legacy-versus-new parity test is signed off. Verified live on Felix's bench, browser-console
      comparison, real data, `subcriterion="1.1.1"`, full-access role: 27 oversight records, 202
      stakeholder engagements, 675 risk register entries, management reviews, quality actions —
      `EQUAL (excl. generated_at): true`. Legacy Server Script and
      `ucc_intelligence.api.get_criterion_1` produce byte-identical output.
- [ ] Permission tests pass — **open follow-up, not blocking**. What's verified: the happy-path
      full-access parity above, and the stubbed smoke test's *unavailable-metadata* source (a DocType
      that doesn't exist / isn't installed). What's **not yet verified against real data**: a genuine
      *permission-denied* source — a role that lacks read access to one of Criterion 1's underlying
      DocTypes (Risk Register and Mitigation Plans, Policies and Standards Type, etc.), which exercises
      `is_permission_error`'s classification and the blocked-source notice path specifically. Recommended
      before treating Criterion 1 as fully closed, not before moving on to Criterion 3: same
      browser-console comparison as §10/§11, `subcriterion="1.1.1"`, logged in as a role missing one of
      those DocTypes.
- [ ] Frontend rendering matches expected behaviour — not applicable until Decision B's cutover step,
      tracked separately.
- [x] No production-only field name is silently assumed. (Static config block ported verbatim from the
      live legacy source, byte-diffed at test time — see §10.)
- [x] Diagnostics identify missing DocTypes or field mismatches clearly. (Unchanged from legacy —
      `source_status`/`resolve_source` logic ported verbatim; unavailable-source path smoke-tested.)

## 8. Rollback

Nothing here touches `custom-html-block/` or `server-scripts/`, and per Decision B the frontend keeps
calling the legacy method throughout this phase — a revert is a plain `git revert` of the new files,
with zero live-behaviour impact since nothing user-facing points at the new code yet. The eventual
frontend cutover (a later, separate, deliberate step) would need its own one-line rollback note when
it happens.

---

## 9. What I need from you before writing code

1. Decisions A, B, C above — go ahead with the recommendations, or say what should differ.
2. Anything else you want folded into Criterion 1's scope, or held back.

Once confirmed, next step is reading Criterion 1 in full (I've only mapped its shape so far, not
read every line) before writing the actual port.

---

## 10. What was built (Criterion 1 port, this round)

**Files added**:

- `ucc_intelligence/ucc_intelligence/analytics/engine.py` — `clean_text`/`lower_text`/`is_truthy`,
  extracted verbatim from the legacy script, hash-verified byte-identical (`lower_text`, `is_truthy`)
  or majority-identical (`clean_text`, 6 of 7 scripts) across all seven criteria before being shared
  (Decision C). Criterion 4's own `clean_text` differs and must be re-checked, not assumed compatible,
  when Criterion 4 is ported.
- `ucc_intelligence/ucc_intelligence/analytics/request.py` — shared payload parsing
  (`parse_payload`), parameterised by `default_subcriterion` and `allowed_actions` — the only two
  things that differ between Criterion 1's and Criterion 3's equivalent blocks.
- `ucc_intelligence/ucc_intelligence/analytics/criterion_1.py` — the port itself. Static
  config/registry block (legacy lines 63-784) copied verbatim at module scope; the engine and
  response-assembly code (legacy lines 801-1566, 1773-1842) wrapped one indentation level deeper
  inside `run(action, subcriterion, filters, metric_id, page, page_size, row_limit)`, reusing the
  already-ported `is_permission_error` / `standardise_response_contract` from `analytics.contracts`
  (Phase 2) instead of redefining them. Four deliberate differences from the legacy script are
  documented in the module docstring; everything else — every metric, question, condition, field
  candidate list, and the evaluation engine's control flow — is unchanged.
- `tools/test_ucc_intelligence_criterion_1.py` — two-layer self-check (see §6): re-extracts the same
  legacy line ranges at test time, asserts they still match the live source verbatim, then diffs the
  transformed result against the committed files; plus a stubbed-`frappe` smoke test that runs
  `criterion_1.run()` end to end against a small synthetic dataset (mixed available/unavailable
  sources, one "conditions"-mode metric, one "field_compare"-mode metric, drilldown, and an unknown
  `metric_id` error case). **19/19 checks pass.**

**Files changed**:

- `ucc_intelligence/ucc_intelligence/api.py` — added `get_criterion_1()`, a `@frappe.whitelist()`
  method that parses the payload via `request.parse_payload` and calls `criterion_1.run(**parsed)`.
  **Correction mid-build**: the original plan (below) said this would live in a new
  `api/analytics.py` module, following CLAUDE.md §7's illustrative layout. That's wrong for this
  install — `api.py` already exists as a *flat module* from Phase 1 (`sophia_analytics.js` calls
  `ucc_intelligence.api.get_dashboard_access`, a dotted path only possible if `api` is a module, not a
  package), so a new `api/` *directory* alongside it would be a Python import conflict, not just an
  aspirational-vs-real mismatch. Caught before anything broken was committed; `get_criterion_1` was
  added to the existing `api.py` instead. Whether `api.py` should become a real package once several
  more criteria are added is a real question for later, not decided here.

**Two self-check bugs found and fixed while getting to 19/19** (both in the test/docstring, not the
ported logic):

1. The "no Server Script response-object assumption left" check failed because the module docstring
   *mentioned* the legacy response-object assignment in prose, tripping the same substring check meant
   to catch it in code. Reworded the docstring to describe the behaviour without using the literal
   string.
2. The "`engine.py` matches Criterion 1's legacy copies verbatim" check failed because `engine.py` was
   written with PEP8-style double blank lines between top-level functions, while the legacy source (and
   the test's raw extraction) uses single blank lines. Reformatted `engine.py` to single blank lines to
   match the verbatim extraction, consistent with how the static block elsewhere in `criterion_1.py`
   preserves the legacy file's original spacing rather than reformatting it.

**Verification performed**:

- `tools/test_ucc_intelligence_criterion_1.py`: 19/19 (structural fidelity + stubbed smoke test).
- Full existing regression suite re-run: `test_dashboard_access.py`, `test_sophia_analytics_page.py`,
  `test_ucc_intelligence_access.py`, `test_ucc_intelligence_contracts.py` all still pass.
  `test_drop_server_message.py` and `validate_package.py` (94/101) fail — confirmed via `git stash` to
  be **pre-existing failures on the baseline**, unrelated to this round's changes (both concern
  Criterion 5/6 build-manifest matters, not touched here).
- `git diff --stat cb77320 -- custom-html-block/ server-scripts/ src/ dist/ archive/` — empty. Legacy
  directories remain byte-for-byte untouched.
- `python3 -m py_compile` clean on all new/changed Python files.

**Known limitations / not yet done at the time this section was written**: live parity against real
data had not been run yet. See §11 — it has since been run and passed.

- Frontend still calls the legacy Server Script directly (Decision B — shipped dark, not cut over).
- Criteria 2-7 not started. Each will need its own check of which `analytics/engine.py` helpers it can
  actually reuse (Decision C's method), not an assumption that they all match Criterion 1's.

## 11. Live parity result (Criterion 1) — 2026-07-29

Felix ran the comparison from §5/§6 in the browser console on his own logged-in session (full-access
role), matching exactly what the legacy frontend itself calls (`frappe.call({method: "...", args:
{payload}})` for both the legacy Server Script and the new whitelisted method), diffing the JSON with
`meta.generated_at` excluded (the one field expected to legitimately differ by call time):

```
payload: {"action":"summary","subcriterion":"1.1.1"}
EQUAL (excl. generated_at): true
```

Real data volume covered: 27 oversight records, 202 stakeholder engagements, 675 risk register
entries, plus management reviews and quality actions. Legacy `ucc_analytics_criterion_1` and
`ucc_intelligence.api.get_criterion_1` produced byte-identical output.

**Criterion 1 is closed**: structural fidelity (19/19, §10) and computational parity (this section)
both verified. One thing is explicitly *not* covered by this result and is logged as an open
follow-up rather than silently treated as done — see §7's permission-tests row: a genuine
permission-denied source (a role lacking read access to one of Criterion 1's DocTypes) hasn't been
exercised against real data yet, only the happy path and a stubbed unavailable-metadata case. Worth
doing before Criterion 1 is fully signed off end-to-end, not blocking the move to Criterion 3.

Next: Criterion 3 (per CLAUDE.md's suggested order — Criterion 1, then 3, 7, 2, 6, 4, 5).

## 12. What was built (Criterion 3 port, this round)

Read `server-scripts/UCC Analytics - Criterion 3.py` in full (2286 lines — larger than Criterion 1's
1846) before porting, not just mapped by shape. That read surfaced a real architectural difference
from Criterion 1, not just a different `CONFIG`:

- **Two-pass metric evaluation.** Base metrics (`evaluate_base_metric`) are evaluated first; derived
  metrics (`evaluate_derived_metric`, modes `derived_sum`/`derived_percent`) are evaluated second,
  referencing already-computed base metrics by id via `find_metric`/`metrics_by_id`. Criterion 1 has
  no equivalent layer.
- **Inline exception flags** (`"is_exception": True` per metric) instead of a separate
  `EXCEPTION_METRIC_IDS` list.
- **No `REQUIREMENT_REGISTRY`/`evaluate_requirement`** — questions are answered directly from a linked
  metric via `answer_for_metric`.
- **`unsupported_metric(...)`**, a static-catalogue helper (not a runtime mode) that produces a
  placeholder entry for controls the data model can't yet evaluate — used directly inside `CONFIG`'s
  metric lists.
- **`row_cache = {}`** is a genuine correctness concern once ported, not just a style note: in the
  legacy Server Script it's module-global but freshly empty every call (Server Scripts re-execute
  their whole global scope per request); ported as a bare module-level dict in a long-lived worker
  process, it would leak stale rows across requests — and potentially across users in the same worker.
  Nesting the whole engine inside `run()` (the same technique used throughout this phase) gives every
  call its own fresh `row_cache`, so this is preserved correctly by construction, not by extra code.

**Files added**:

- `ucc_intelligence/ucc_intelligence/analytics/criterion_3.py` — the port. Static config/registry
  block (legacy lines 81-1101) verbatim at module scope; engine + response assembly (legacy lines
  1122-1128, 1140-1984, 2191-2282) wrapped in `run()`, reusing `analytics.engine`'s
  `clean_text`/`lower_text`/`is_truthy` (content-diffed against Criterion 3's own copies — identical
  apart from blank-line style, which the extraction already tolerates) and `analytics.contracts`'
  `is_permission_error`/`standardise_response_contract` (content-diffed against Criterion 3's own
  copies too, not just trusted from the Phase 2 hash claim — only cosmetic differences found:
  reworded docstring, `CONTRACT_VERSION`/`ARRAY_KEYS` constants instead of inline literals, trailing
  commas). Five deliberate differences documented in the module docstring.
- `tools/test_ucc_intelligence_criterion_3.py` — same two-layer technique as Criterion 1's test, with
  a dataset built specifically for Criterion 3's shape: an `overview` pass exercising `equals`/`in`/
  `date_next_days` base metrics plus a `derived_sum` and an `unsupported` placeholder, and a `3.1.1`
  pass (agent-only synthetic data) exercising `all`/`in`/`equals`/`truthy`/`all_required`/
  `derived_percent`, plus drilldown across a normal metric, a `derived_sum`, a `derived_percent`, an
  unsupported metric, an unknown `metric_id` (expects the same `frappe.throw` as legacy), and the
  Criterion-3-only `question_catalogue` action. **28/28 checks pass.**

**Files changed**:

- `ucc_intelligence/ucc_intelligence/api.py` — added `CRITERION_3_ALLOWED_ACTIONS` (matches legacy's
  `ALLOWED_ACTIONS`, including `question_catalogue`) and `get_criterion_3()`, same shape as
  `get_criterion_1()`.

**Verification performed**:

- `tools/test_ucc_intelligence_criterion_3.py`: 28/28.
- Full existing regression suite re-run, including `test_ucc_intelligence_criterion_1.py` (still
  19/19 — confirms the shared `engine.py`/`contracts.py`/`api.py` changes didn't regress Criterion 1):
  all still pass.
- `git diff --stat cb77320 -- custom-html-block/ server-scripts/ src/ dist/ archive/` — empty.
- `python3 -m py_compile` clean on all new/changed Python files.

**Known limitations / not yet done**:

- Live parity against real data has not been run for Criterion 3 yet — needs your bench, same
  procedure as §11: run `ucc_analytics_criterion_3` and `ucc_intelligence.api.get_criterion_3` with the
  same payload/user, diff the JSON (`meta.generated_at` excluded). Recommend covering `overview`,
  `3.1.1`, and `3.2.1` at minimum, since `3.2.1` exercises `average_fields`/`sum`/
  `renewal_rule_compliant` modes the smoke test doesn't reach.
- Same open permission-path follow-up as Criterion 1 (§7) — not yet exercised against a real
  permission-denied source.
- Frontend still calls the legacy Server Script directly (Decision B).
- Criteria 7, 2, 6, 4, 5 not started.

## 13. What was built (Criterion 7 port, this round)

Read the full 2061-line `server-scripts/UCC Analytics - Criterion 7.py` before porting. Two real
findings from that read, not assumed from Criteria 1/3's shape:

- **The static config block (POLICY_REGISTRY..STANDARD_FIELDS, legacy lines 63-1188) is not
  hand-authored in the C1/C3 4-space convention.** Checked, not assumed: 245 of its 1118 non-blank
  lines have indentation that isn't a multiple of 4 spaces — it reads as `pprint`/formatter output,
  with continuation lines aligned to bracket columns. The usual mechanical "spaces → tabs" step would
  either throw (on the majority of lines) or silently misalign the block, so this block is copied
  **byte-verbatim, unconverted** — a deliberate, evidence-based exception to the C1/C3 technique, not
  a shortcut. The `run()` body (regular 4-space throughout, checked the same way) still gets the usual
  tab conversion. Mixing the two within one file is syntactically fine in Python 3.
- **The same `row_cache`-shaped correctness issue Felix flagged for Criterion 3 recurred here**:
  `filter_diagnostics = {}` and `fetch_diagnostics = {}` (legacy lines ~1412-1413) are module-level
  dicts in the Server Script, harmless there because the whole global scope re-executes per request.
  Nesting the engine inside `run()` (same technique as before) gives every call fresh copies, so this
  is handled correctly by construction — worth continuing to check for on each remaining criterion,
  not assumed solved once and done.

Other architectural facts confirmed by the read: single-pass metric evaluation (no derived-metric
layer like Criterion 3); exceptions via a separate `EXCEPTION_METRIC_IDS` list (like Criterion 1, not
Criterion 3's inline flags); a `required_value_coverage` metric mode not present in either earlier
criterion; a `display_doctype()` helper (`SOURCE_DISPLAY_NAMES`) neither earlier criterion has;
`resolve_source` checks `frappe.db.exists("DocType", ...)` before `frappe.get_meta`, a different
resolution flow from Criterion 1/3's. Criterion 7's own legacy `is_permission_error` already checks
for `"403"` — the one criterion where reusing `contracts.py`'s shared version is an **exact** match,
not a broadened one (that shared version was generalised from Criterion 7's copy back in Phase 2).

**Files added**:

- `ucc_intelligence/ucc_intelligence/analytics/criterion_7.py` — the port, with the static-block
  exception above documented in the module docstring alongside the usual deliberate-differences list.
- `tools/test_ucc_intelligence_criterion_7.py` — same two-layer technique, adapted: the structural
  check compares the static block as raw (untransformed) text instead of tab-converted text, and
  includes an explicit "is the block still irregular" sanity check so the byte-verbatim decision would
  visibly fail loud if the legacy file were ever reformatted underneath it. The smoke test's stub gains
  a `frappe.db.exists` fake (Criterion 7-specific) and covers `falsy`, `all_required` (7-field-group
  form), `required_value_coverage`, `not_in`, and `sum` — the modes Criteria 1/3's tests don't reach.
  **28/28 checks pass.**

**Files changed**:

- `ucc_intelligence/ucc_intelligence/api.py` — added `CRITERION_7_ALLOWED_ACTIONS` and
  `get_criterion_7()`, same shape as the other two.

**Verification performed**:

- `tools/test_ucc_intelligence_criterion_7.py`: 28/28.
- Full existing regression suite re-run, including both prior criterion tests (Criterion 1 still
  19/19, Criterion 3 still 28/28 — confirms the shared `api.py` edit didn't regress either): all pass.
- `git diff --stat cb77320 -- custom-html-block/ server-scripts/ src/ dist/ archive/` — empty.
- `python3 -m py_compile` clean on all new/changed Python files.

**Known limitations / not yet done**:

- Live parity against real data not yet run for Criterion 7 — same procedure as §11, only one
  subcriterion (`7.1.1`) exists for this criterion so there's no additional subcriterion sweep needed,
  but worth trying a `drilldown` on a `required_value_coverage` metric and a `sum` metric specifically
  since those are the modes unique to this criterion.
- Same open permission-path follow-up as Criteria 1 and 3.
- Frontend still calls the legacy Server Script directly (Decision B).
- Criteria 2, 6, 4, 5 not started.
