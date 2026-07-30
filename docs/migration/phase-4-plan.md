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

## 14. What was built (Criterion 2 port, this round)

Read the full 1827-line `server-scripts/UCC Analytics - Criterion 2.py` before porting. Same
static-block finding as Criterion 7 (pprint-style, 498 of 905 non-blank lines in
POLICY_REGISTRY..STANDARD_FIELDS indented to something other than a multiple of 4 spaces — copied
byte-verbatim, same rationale), plus one new wrinkle this read surfaced:

- **The irregular indentation isn't confined to the static block.** The result dict's `"warnings"`
  list (legacy lines 1795-1798) is *also* pprint-style — 3 of its 4 lines aren't 4-space-indented —
  even though it sits inside the otherwise cleanly-indented `run()`-body range. Rather than carve out
  another special-cased sub-range (what the Criterion 7 approach would have required), the conversion
  step was made **per-line** instead of per-block: any line whose indent is a clean multiple of 4 is
  tab-converted as usual; any line that isn't is left exactly as in the legacy source. This is more
  robust than Criterion 7's all-or-nothing per-block decision — it would have caught this same wrinkle
  without needing to spot it by eye first, and it's the technique used for all remaining criteria going
  forward. Checked, not assumed: confirmed the `"warnings"` line lands in the port with exactly one
  added tab and its original single-space indentation otherwise untouched.
- **Checked for the `row_cache`-style module-global risk flagged in Criteria 3 and 7 — none found
  here.** `fetch_rows` has no request-scoped cache dict in this criterion. Every module-scope loop and
  intermediate variable still becomes a local of `run()` via the standard technique regardless (the
  correct general handling for a function called repeatedly in a warm worker), but there was no
  specific cache-leak bug to avoid this time. Worth continuing to check per-criterion rather than
  assuming either way.

Other architectural facts confirmed by the read: single-pass `evaluate_metric`, closest in shape to
Criterion 1's of the three criteria ported so far (`resolve_field_groups`, `metric_required_fields`,
`row_matches` all present); exceptions via `EXCEPTION_METRIC_IDS` (like Criterion 1 and 7); no
requirement registry (like Criterion 3 and 7); **eight subcriteria** configured
(2.1.1/2.1.2/2.2.1/2.3.1/2.3.2/2.4.1/2.4.2/2.4.3) — more than any criterion ported so far, though only
2 were needed for adequate mode coverage in the smoke test. Criterion 2's own `is_permission_error`
does not check `"403"` (same broadened-by-reuse case as Criterion 1 and 3, not Criterion 7's exact
match).

**Files added**:

- `ucc_intelligence/ucc_intelligence/analytics/criterion_2.py` — the port, with the static-block and
  warnings-list indentation exceptions documented in the module docstring.
- `tools/test_ucc_intelligence_criterion_2.py` — same two-layer technique with the per-line-graceful
  conversion; covers `all`/`equals`/`in`/`unsupported` (subcriterion 2.1.1, including an unstubbed
  source to exercise the unavailable path) and `conditions`/`average_fields` (subcriterion 2.4.2,
  `contains` + `in` condition chaining, and an averaged numeric field gated by the same condition).
  **24/24 checks pass.**

**Files changed**:

- `ucc_intelligence/ucc_intelligence/api.py` — added `CRITERION_2_ALLOWED_ACTIONS` and
  `get_criterion_2()`, same shape as the others.

**Verification performed**:

- `tools/test_ucc_intelligence_criterion_2.py`: 24/24.
- Full existing regression suite re-run, including all three prior criterion tests (Criterion 1 still
  19/19, Criterion 3 still 28/28, Criterion 7 still 28/28): all pass.
- `git diff --stat cb77320 -- custom-html-block/ server-scripts/ src/ dist/ archive/` — empty.
- `python3 -m py_compile` clean on all new/changed Python files.

**Known limitations / not yet done**:

- Live parity against real data not yet run for Criterion 2 — same procedure as §11/§13. Recommend
  covering at least 2.1.1, one of the `average_fields`/`conditions` subcriteria (2.4.1/2.4.2/2.4.3),
  and 2.2.1 (the only subcriterion using `all_required`), since those exercise the widest mode spread.
- Same open permission-path follow-up as Criteria 1, 3, and 7.
- Frontend still calls the legacy Server Script directly (Decision B).
- Criteria 6, 4, 5 not started.

## 15. What was built (Criterion 6 port, this round)

Read the full 2210-line `server-scripts/UCC Analytics - Criterion 6.py` before porting. Same
pprint-style static block (61-1128, 252 of 1058 non-blank lines not 4-space-indented — byte-verbatim,
same rationale as Criteria 2 and 7). The per-line-graceful conversion introduced for Criterion 2 was
used again as the default technique; checked explicitly this time whether the `run()`-body range had
any irregular pockets of its own (like Criterion 2's "warnings" list) — none found, so the graceful
fallback never actually triggers for this criterion, but it costs nothing to keep as the standard.

The read surfaced the most structurally distinct engine of the four criteria ported so far:

- **A genuine parent/child metric split** — `evaluate_metric` dispatches to `evaluate_parent_metric`
  (the familiar shape) or `evaluate_child_metric` based on mode. For `child_count`/
  `child_parent_count`/`child_any_missing`, `evaluate_child_metric` calls
  `frappe.get_doc(parent_doctype, parent_name)` **per matched parent row** — not just
  `frappe.get_list` — to walk that parent's child table (`doc.get(table_field)`) and evaluate
  conditions per child row. No other criterion ported so far touches child tables or calls
  `frappe.get_doc` at all; the port's smoke test needed a new `frappe.get_doc` stub and, on the first
  run, was missing `frappe.db.exists` too (Criterion 6's `resolve_source` uses the same
  exists-then-get_meta flow as Criterion 7's, not Criteria 1/2/3's plain get_meta-first flow) — same
  mistake made and caught the same way as it was for Criterion 7's test.
- **`requirement_registry` aggregates across every subcriterion**, not just the requested one (legacy
  lines 2177-2193 loop `for criterion_key in QUESTION_REGISTRY`, unscoped by the request's
  `subcriterion`). Every other ported criterion's `requirement_registry` stays scoped to the current
  subcriterion — this is a genuine behavioural difference between criteria in the legacy system, not
  something to "fix" to match the others. Caught by reading the dispatch block carefully rather than
  assuming it matched the pattern from Criteria 1/2/3/7, and specifically tested (request 6.1.1's
  registry, assert it contains a 6.2.1 question id).
- `filter_diagnostics = {}` (legacy line ~1371) is the same module-global-but-request-fresh shape
  flagged in Criteria 3 and 7 — third time this pattern has recurred, becomes a `run()` local via the
  same technique.
- `to_number` strips `","`/`"SGD"`/`"$"` (like Criterion 7's, unlike Criteria 1-3's plain `float()`).

**Files added**:

- `ucc_intelligence/ucc_intelligence/analytics/criterion_6.py` — the port, with the static-block
  exception, the parent/child split, and the cross-subcriterion `requirement_registry` behaviour
  documented in the module docstring.
- `tools/test_ucc_intelligence_criterion_6.py` — same two-layer technique, with a synthetic dataset
  built specifically to exercise every child-table mode: `child_count` (with chained `not_in`/
  `date_before_today` conditions), `child_any_missing`, and `child_parent_count` across two different
  child-table fields on the same parent DocType, plus the `requirement_registry` cross-subcriterion
  check. **23/23 checks pass** (after fixing the missing `frappe.db.exists` stub found on first run).

**Files changed**:

- `ucc_intelligence/ucc_intelligence/api.py` — added `CRITERION_6_ALLOWED_ACTIONS` and
  `get_criterion_6()`, same shape as the others.

**Verification performed**:

- `tools/test_ucc_intelligence_criterion_6.py`: 23/23.
- Full existing regression suite re-run, including all four prior criterion tests (1: 19/19, 2: 24/24,
  3: 28/28, 7: 28/28): all pass.
- `git diff --stat cb77320 -- custom-html-block/ server-scripts/ src/ dist/ archive/` — empty.
- `python3 -m py_compile` clean on all new/changed Python files.

**Known limitations / not yet done**:

- Live parity against real data not yet run for Criterion 6 — same procedure as before. Recommend
  covering 6.1.1 (all three child modes), and at least one of 6.3.1/6.4.1 (the only subcriteria using
  `average`/`sum`/`number_gte`/`number_lt`), since those are the modes this port's smoke test doesn't
  reach (only tested against the "all"/"equals"/"in" family in prior criteria's tests, not this
  criterion's specific numeric-threshold operators).
- Same open permission-path follow-up as Criteria 1, 2, 3, and 7.
- Frontend still calls the legacy Server Script directly (Decision B).
- Criteria 4, 5 not started.

## 16. Direction change for Criteria 4 and 5 — Insights-informed, not verbatim ports

**Confirmed with Felix, 2026-07-29: Criteria 1, 2, 3, 6, and 7 stay exactly as already built** (the
verbatim-extraction technique documented in §§10-15). **Criteria 4 and 5 switch approach entirely.**
This section records why and what changed; it does not revise anything already shipped for the other
five.

### Why

A read-through of Criterion 4 (§ below) found it structurally unlike the other five in ways that made
a verbatim port a poor fit specifically for this criterion: none of `analytics/engine.py`'s shared
value helpers were reusable (its own `clean_text` uses `frappe.utils.cstr`, not `str()`), eleven
module-level caches existed purely to make ~40 generically-evaluated metrics cheap per request, and a
~130-line separate `admission_intelligence` subsystem — the exact chart the earlier Insights pilot
(`docs/migration/insights-pilot-findings.md`) already spiked — sat alongside the generic engine. That
pilot had already done real, live-verified work (`docs/migration/scripts/create_insights_pilot.py`
confirmed `Student Applicant.academic_year` as a real field against the live bench) that a verbatim
port would have thrown away in favour of re-deriving the same query from legacy Python.

### The model: Insights authors, `ucc_intelligence` executes — live, every request

**Not an embed.** The pilot's own permission test (`insights-pilot-findings.md` §4(b)) found a public
Insights dashboard has zero row/column permission enforcement — a genuinely unauthenticated request
got the full record. That rules out Insights' own dashboard/sharing mechanism for anything
`ucc_dashboard_access` gates; it is not a configuration to fix, it is Insights' own design.

Instead: Insights is a **design-time query-authoring and verification tool only**, with no runtime
footprint. Someone builds and verifies a chart's query in the Insights UI against real data; the
verified query is then **hand-translated once** into `ucc_intelligence`'s own Python, executed inside
the same whitelisted API method every other criterion uses (`frappe.get_list`, no
`ignore_permissions=True`). The query still runs live against the site database on every request —
same as the legacy script always did — it is simply designed via Insights rather than hand-written
from scratch. Permission enforcement is the two mechanisms already built and tested for every other
criterion, nothing new: `ucc_dashboard_access` gates whether Criterion 4 mounts for this user at all,
and ordinary Frappe DocType/row permissions apply to the `frappe.get_list` calls exactly as they did
in the legacy script. No iframe, no Insights public link, no call into Insights' API at request time,
no frontend change — the API response shape (`admission_intelligence.charts.applicants_by_year`, etc.)
is unchanged, so `renderAdmissionLine()` keeps working as-is.

A concrete benefit this buys over the pilot's iframe-embed spike: §4(a) of the pilot (filter
behaviour) was left explicitly untested, with a documented expectation that an embedded chart would
not receive the page's filter strip state, since an iframe has no mechanism to carry it. That concern
doesn't apply here — `admission_intelligence` computes inside the same `run()` call as the rest of
Criterion 4, so `filters.academic_year` reaches the query the same way every other criterion's filters
always have. Tested directly (see below).

### Scope, confirmed explicitly — not assumed from "use Insights for Criterion 4"

**Only `admission_intelligence`** — the 4 KPIs and 6 chart series from legacy
`build_admission_intelligence()` (`server-scripts/UCC Analytics - Criterion 4.py:2359-2489`) — moves
to this approach. Criterion 4's other ~40 metrics/questions/requirements (contract, fee protection,
movement, refund, support services, attendance) are **not** covered here and are **not** deferred to
Insights either — they stay planned as regular hand-ported code, same verbatim technique as Criteria
1/2/3/6/7, built later in the normal pattern. Until then, `run()` returns a contract-valid response
(via the same `standardise_response_contract` every other criterion uses) with `admission_intelligence`
populated and everything else defaulted empty.

### What's actually verified vs. faithfully translated but not yet independently checked

Stated plainly rather than implying uniform confidence across all six series:

- **`applicants_by_year` and `enrolled_by_year`** are grounded in the pilot's own tested query:
  `Student Applicant.academic_year` is a confirmed real Link field (62 rows, 0 blank, live bench), and
  the base query genuinely has no `WHERE` clause until a filter is applied — both used directly, not
  assumed.
- **`applicants_by_country`, `programmes`, `agents`, and `counselling_to_admission`** were never
  independently authored/verified in the Insights UI — the pilot only ever built the one chart. These
  four are faithful translations of `build_admission_intelligence()`'s own field-candidate logic
  (the same candidate lists the legacy script used), which is why a small, uncached `resolve_field`/
  `get_meta` still exists in `criterion_4.py` even though the point of this approach was moving away
  from defensive field probing — dropping that probing for a field nobody has confirmed exists would
  trade verified behaviour for an unverified guess. These four should still go through the
  author-and-verify-in-Insights step once Felix has bench time; whichever turn out to use a single
  confirmed field can drop `resolve_field` the way `academic_year` already has.

### What's dropped, and why that's not a loss

The legacy script's eleven module-level caches (`meta_cache`, `resolved_field_cache`, `row_cache`,
etc. — see §15's Criterion 6 write-up for where this pattern started) existed to keep ~40+
generically-evaluated metrics cheap per request. Six purpose-built queries evaluated once per request
have nothing to cache — the new `get_meta`/`resolve_field` are plain and uncached, correct by not
needing the caching problem to exist in the first place.

### What was built

**Files added**:

- `ucc_intelligence/ucc_intelligence/analytics/criterion_4.py` — fresh implementation (not extracted
  from the legacy script), computing `admission_intelligence`'s 4 KPIs and 6 chart series. Reuses
  `analytics.engine`'s `clean_text`/`lower_text`/`is_truthy` and `analytics.contracts`'
  `is_permission_error`/`standardise_response_contract` directly — the `cstr`-vs-`str()` divergence
  that ruled out reuse in the abandoned verbatim-port attempt doesn't apply to fresh code, only to
  byte-faithful reproduction of legacy behaviour.
- `tools/test_ucc_intelligence_criterion_4.py` — not the structural-fidelity-plus-smoke-test shape
  used for the other five (there's no legacy line range to diff against). Instead: synthetic
  applicant/admission data, hand-computed expected values that mirror the legacy formulas exactly
  (`success_rate = admitted/total*100`, group-by-count, duration averaging), plus source-unavailable,
  permission-denied, filter-passthrough, and subcriterion-guard checks. **18/18 checks pass.**
- `docs/migration/scripts/cleanup_insights_pilot.py` — unrelated to the migration approach itself: the
  pilot's public `Insights Dashboard v3`/`Chart v3` records were confirmed exposed with zero
  authentication (§4(b)) and needed cleaning up on their own, independent of which direction Criterion
  4 took. Two-phase (find + unpublish, then an explicit separate delete step), following the same
  commit-after-every-mutation discipline the pilot's own persistence debugging saga established was
  necessary in `bench console`.

**Files changed**:

- `ucc_intelligence/ucc_intelligence/api.py` — added `get_criterion_4()`. `CRITERION_4_ALLOWED_ACTIONS
  = ["summary"]` only, not the usual six — the other actions (`drilldown`, `policy_registry`, etc.)
  have no real data behind them yet at this partial scope, so they're not claimed as supported.

**Verification performed**:

- `tools/test_ucc_intelligence_criterion_4.py`: 18/18.
- Full existing regression suite re-run, including all five verbatim-ported criteria's tests: all
  still pass unchanged (Criterion 1: 19/19, Criterion 2: 24/24, Criterion 3: 28/28, Criterion 6:
  23/23, Criterion 7: 28/28).
- `git diff --stat cb77320 -- custom-html-block/ server-scripts/ src/ dist/ archive/` — empty.
- `python3 -m py_compile` clean on all new/changed Python files.

**Known limitations / not yet done**:

- **`applicants_by_country`, `programmes`, `agents`, and `counselling_to_admission` still need the
  author-and-verify-in-Insights step** — see above. Not blocking (they're faithful translations of
  already-live legacy logic, not guesses), but not yet independently confirmed the way
  `applicants_by_year` is.
- Live parity against real data (comparing this module's output to the legacy Server Script's
  `admission_intelligence` block for the same live data) has not been run — same bench-dependent step
  every other criterion still needs, same procedure (§5/§6/§11).
- Criterion 4's other ~40 metrics/questions/requirements are not built (by design, out of scope this
  round — see above).
- The pilot's cleanup script (`cleanup_insights_pilot.py`) has not been run — needs Felix's bench
  access, same as every bench-dependent step in this migration.
- Frontend still calls the legacy Server Script directly — no cutover decision has been made or is
  implied by this work.
- Criterion 5 not started — needs its own read-through first to confirm whether it has an
  `admission_intelligence`-equivalent block before assuming the same approach applies unchanged.

## 17. Option B — real live embed of admission_intelligence (2026-07-29)

Direction confirmed with Felix after `test_insights_private_permissions.py` proved the private-query
permission pattern safe on the real bench (0 rows restricted, 6 rows with real access): Sophia embeds
live Insights charts directly, not a copy of their logic. §16's plain-Python `criterion_4.py` module is
now dead code for these 6 series specifically — kept in place per Felix's instruction, not deleted, not
extended, not called by the frontend for `admission_intelligence` anymore.

**Files added**:

- `docs/migration/scripts/build_admission_intelligence_embed.py` — creates the 5 remaining Insights
  Query v3/Chart v3 records (`enrolled_by_year`, `applicants_by_country`, `programmes`, `agents`,
  `counselling_to_admission`; `applicants_by_year` already existed from the earlier pilot and is only
  verified, not recreated). Field candidates taken directly from `criterion_4.py`'s own field-candidate
  lists; the real field is discovered live against this site's schema (`frappe.get_meta`) before each
  query is authored, not guessed. `filter`/`join`/`mutate` operation shapes verified against the real,
  unabridged Insights v3.12.2 source (`ibis_utils.py`'s `IbisQueryBuilder`) — the same discipline as
  every prior script, not assumed from the one `source`+`summarize` pattern the pilot proved. One
  exception, stated plainly: the `counselling_to_admission` chart's date-difference `mutate` expression
  uses ibis's own documented `TemporalColumn.delta(other, unit)` method rather than an Insights-specific
  helper, because `get_functions()` (a separate, unfetched file) wasn't independently confirmed to
  provide one — if that's wrong, the script's own execute() verification stage will surface a loud,
  explicit Python error, not silently wrong data. Also runs self-QA (a) and (b): all 6 charts executed
  as Administrator with real row counts, and the restricted-vs-control permission test re-run against 2
  of the 5 newly-created charts (not just the original pilot one).
- `ucc_intelligence/ucc_intelligence/analytics/admission_intelligence_embed.py` — the runtime module:
  looks up each chart's Insights Query v3 by title, calls `check_permission("read")` + `execute()`
  directly (not `insights.api.run_doc_method`, which also calls `is_valid_http_method()`/
  `add_data_to_monitor()` — irrelevant to what's being tested and needs a real `frappe.request` that
  doesn't exist in bench console, though it would exist for a real production HTTP call; the direct
  call is simpler and does identical permission work either way), converts Insights' row shape into the
  same `{label, value}` shape `criterion_4.py`'s `group_count_rows()` already produced, and reports
  blocked sources by the real underlying DocType so the existing `permissionNoticeHtml` blocked-source
  UI picks them up unchanged. 3 of 4 KPIs are summed from the Insights-sourced chart series; the 4th
  (`shortlisted-approved`, an Approved-status count that doesn't correspond to any of the 6 chart
  series) is one small `frappe.get_list` count call, same permission model, not worth a 7th Insights
  query for one scalar. **Prominently documents the `Insights Settings.apply_user_permissions`
  dependency** in its module docstring — a site-wide, not per-chart, toggle; if a future admin disables
  it, every chart here silently stops filtering by the viewer's permissions.

**Files changed**:

- `ucc_intelligence/ucc_intelligence/api.py` — adds `get_admission_intelligence()`. Unlike every other
  method in this file, this one IS wired into the frontend (see below) — Criterion 4's other ~40
  metrics still come from the legacy Server Script, untouched.
- `ucc_intelligence/ucc_intelligence/sophia/page/sophia_analytics/sophia_analytics.js` —
  `loadLive()` now calls the new method (scoped to `criterion_4`/`4.1.1` only) and overwrites
  `result.admission_intelligence` with the embed's response, concatenating its blocked-source entries
  into `result.sources` so the existing `chartForLive`/`renderLiveChartCardNow` blocked-notice path
  triggers correctly — no new notice UI, no changes to `callApi`, `renderDashboard`, `renderKpis`,
  `metricRows`, or the chart-plugin registry. The dormant Insights-pilot iframe glue code
  (`INSIGHTS_PILOT_CHART_ID`, `watchForInsightsPilotTarget`, `mountInsightsPilotCard`,
  `injectInsightsPilotStyles`) is fully removed, not left dormant — superseded by this real embed, not
  a second mechanism sitting alongside it.
- `tools/test_sophia_analytics_page.py` — the verbatim-engine-body regression guard now applies the one
  documented `loadLive()` addition to its expected string before the substring check, rather than
  weakening or dropping the check; still catches unrelated drift everywhere else in the engine. Added
  checks confirming the pilot iframe code is gone and the new embed wiring is scoped/shaped correctly.

**Known, explicit gap versus the pre-Insights engine**: the `academic_year` request filter no longer
applies to these 6 charts. Insights' `execute()` accepts an `adhoc_filters` parameter that could
plausibly restore this, but its exact shape wasn't verified against live source in the time available
this round — flagged, not silently dropped.

**Self-QA — reported explicitly per the task's success criteria, not summarized as "done"**:

| # | Check | Result |
|---|---|---|
| (a) | All 6 charts execute as Administrator with real row counts | **Bench-pending** — `build_admission_intelligence_embed.py` Stage 3 does this; needs Felix to run it |
| (b) | Restricted-vs-control permission test on 2+ newly-built charts | **Bench-pending** — same script's Stage 4 |
| (c) | Existing `criterion_4.py` non-Insights path unaffected (regression) | **PASS** — `tools/test_ucc_intelligence_criterion_4.py` 18/18, untouched by this round (`git diff` on the file itself is empty) |
| (d) | `custom-html-block/`, `server-scripts/`, Criteria 1/2/3/6/7 byte-for-byte untouched | **PASS** — `git diff --stat` against baseline and against this round's start, both empty for those paths |
| — | Full existing regression suite (all prior criteria + access + contracts + page tests) | **PASS** — every suite still green, including the updated `test_sophia_analytics_page.py` (25/25) |
| 3 | Live browser render of all 6 series on `/app/sophia-analytics` | **Bench-pending** — requires an actual browser session Felix has and this repo-only session doesn't |

Everything checkable without bench access has been checked and passes. Everything requiring bench
access is handed off as one complete, ready-to-run script
(`docs/migration/scripts/build_admission_intelligence_embed.py`) plus the live browser check, per the
task's explicit instruction not to do this in multiple back-and-forth rounds.

### Update, 2026-07-29 (later same day) — scoped down to 2 of 6 pending review

Felix: build/self-QA all 6 in one pass was too much to review at once. Rescoped
`build_admission_intelligence_embed.py` to build only ONE more chart this round —
`enrolled_by_year` (lowest risk: reuses the already-verified `academic_year` field, adds one
verified `filter` operation) — alongside the already-existing `applicants_by_year`. The other 4
(`applicants_by_country`, `programmes`, `agents`, `counselling_to_admission`) have their verified
specs kept in the script (`DEFERRED_SERIES`, and `build_counselling_duration()` still defined) but
are not built or self-QA'd this round — resuming later is moving a spec back into `ACTIVE_SERIES`,
not redoing the verification work.

No changes were needed in `admission_intelligence_embed.py` (the runtime module) or the frontend
wiring — both already degrade gracefully when a chart's Query v3 record doesn't exist yet
(`status: "unavailable"`, generic empty state, not an error and not a false permission notice), so a
2-of-6 build is safely reviewable on the real page without touching anything beyond the
chart-creation script itself.

**Also confirmed, not yet decided**: Criterion 5 has NOT been given the Option B treatment and
nothing should be assumed about it — that's a separate future call, not implied by Criterion 4's
direction. And the original CLAUDE.md scope beyond the 7 criteria — Ask UCC, Zep/conversation memory,
document/policy search, monitoring, controlled AI actions — is all still unstarted; everything built
across every phase so far is foundation work under CLAUDE.md's Phase 0-6 umbrella, not a signal those
later phases have begun.

### Update, 2026-07-30 — real bug found running the scoped-down script: `exec()` namespace split

Felix hit `NameError: name 'stage_1b_check_existing' is not defined` inside `run()` at Stage 1, on a
real bench run. The function is correctly defined at module level and correctly called by name — this
wasn't a rename/typo mismatch. Root cause, confirmed by reproducing it locally (not just theorized):
bare `exec(open(path).read())`, the invocation this and two other scripts' docstrings instructed,
inherits whatever `globals()`/`locals()` are active at its own call site. If bench console evaluates
pasted input from inside some internal method (where `globals() != locals()`), every top-level `def`
in the exec'd source gets written to that call's *locals* dict, but each function's own `__globals__`
still points at that call's *globals* dict — so any function calling a sibling top-level function (via
`LOAD_GLOBAL`, which only ever checks `__globals__`) fails to find it, while bare top-level code
(`LOAD_NAME`, checks locals then globals) works fine. This also explains, retroactively, why
`test_insights_private_permissions.py`'s earlier `TEST_USER_EMAIL` bug looked inconsistent with
everything else in that script working — that script is mostly bare top-level code; the one actual
`def` referencing a sibling top-level name was the only place it could have broken, and did.

**Fix**: `exec(open(path).read(), globals())` — passing a single explicit dict forces Python to use it
for both globals and locals (documented `exec()` behaviour), eliminating the two-dict split outright.
Applied to the usage instructions in `build_admission_intelligence_embed.py`,
`test_insights_private_permissions.py`, and `cleanup_insights_pilot.py` — the three scripts using this
invocation pattern. `create_insights_pilot.py` was told to be pasted directly rather than via `exec()`
and never hit this, so it was left as-is.

Not yet re-run on the real bench — needs Felix to confirm the fixed invocation actually gets past
Stage 1 this time.
