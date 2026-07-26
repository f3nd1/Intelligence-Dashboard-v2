# Phase 2 Plan — Migrate access and shared runtime services

**Status: code written and self-verified (2026-07-26); one deliverable (the app-managed DocType)
staged as a draft — see §5. Live-bench check on 2026-07-26 found the DocType doesn't exist on
`ucc.local`, revising that deliverable from "convert existing" to "create fresh."** Per CLAUDE.md §9
Phase 2 goal: "Move shared permission and runtime logic before moving dashboards."

## 0. Scope — confirmed

Felix confirmed (2026-07-26): Phase 2 = access + shared error/permission-notice logic only, per
CLAUDE.md §9's five bullets. Not Phase 3/4 analytics/dashboard content. This is what got built.

## 1. What Phase 2 required work actually is (CLAUDE.md §9)

- Migrate `ucc_dashboard_access` from Server Script to app Python.
- Preserve the current access DocType or replace it with an app-managed equivalent.
- Migrate shared error classification and blocked-source presentation.
- Establish common API response and error contracts.
- Add audit-safe logging and redaction.
- Create tests for role combinations and denied sources.

## 2. What was built, mapped to real legacy code (re-read in full for this plan)

| # | Required-work bullet | Source (verified this session) | Built at |
|---|---|---|---|
| 1 | Migrate `ucc_dashboard_access` | `server-scripts/UCC Dashboard Access.py` (260 lines, read in full). Pure functions: `load_rows`, `resolve_default`, `union_of`, `assigned_roles`, `role_key`, `build_response`, all fail-open on error. | `ucc_intelligence/ucc_intelligence/permissions/access.py` — ported verbatim; `get_dashboard_access()` wraps `build_response()` with the fail-open try/except and adds audit logging. Whitelisted shim in `ucc_intelligence/ucc_intelligence/api.py`. |
| 2 | Preserve or replace the access DocType | `UCC Dashboard Access` — **verified 2026-07-26 not to exist** on `ucc.local` (`DoesNotExistError` via `bench console`); assumed live on the site until checked | **Revised: create fresh, not convert. Drafted, not placed — §5.** |
| 3 | Migrate shared error classification + blocked-source presentation (JS) | `src/js/00-shared-runtime.js` (251 lines, read in full) | `ucc_intelligence/public/js/shared.js` — byte-identical straight copy (diffed, confirmed identical). Smoke test at `ucc_intelligence/ucc_intelligence/tests/test_shared_runtime.js`. |
| 4 | Common API response and error contracts (Python) | `standardise_response_contract` — **verified byte-identical across all seven** `server-scripts/UCC Analytics - Criterion *.py` (hash-compared this session). `is_permission_error` — identical in six, **Criterion 7 alone also matches `"403"`** (diff-compared this session). | `ucc_intelligence/ucc_intelligence/analytics/contracts.py` — deduped copy of each. Not wired to any live script yet. |
| 5 | Audit-safe logging and redaction | No legacy equivalent — new work | `ucc_intelligence/ucc_intelligence/logging/audit.py` (`log_access_check`: user, applied outcome, matched roles, redacted error) + `redaction.py` (truncates + strips secret-shaped substrings from error text before logging) |
| 6 | Tests for role combinations and denied sources | `tools/test_dashboard_access.py` (20 scenarios) and `tools/test_permission_notice.js` (28 assertions) | `tools/test_ucc_intelligence_access.py` (all 20 scenarios re-run against the real ported module, passing), `tools/test_ucc_intelligence_contracts.py` (parity-diffed against the live legacy function, passing), `ucc_intelligence/ucc_intelligence/tests/test_access.py` (FrappeTestCase smoke test — needs bench to actually run), `ucc_intelligence/ucc_intelligence/tests/test_shared_runtime.js` (loader smoke test, passing) |

## 3. Verification performed in this sandbox (no bench needed for any of it)

- `tools/test_ucc_intelligence_access.py`: imports the real `ucc_intelligence.permissions.access`
  module (via a stubbed `frappe` in `sys.modules`, the same technique the legacy `tools/test_dashboard_access.py`
  already uses) and runs all 20 legacy scenarios, **including the fail-open path through the real
  `get_dashboard_access()` wrapper**, not just `build_response()`. Passing.
- `tools/test_ucc_intelligence_contracts.py`: extracts `standardise_response_contract` live from
  `server-scripts/UCC Analytics - Criterion 1.py` and diffs its output against the ported version
  across 3 fixtures (empty, populated with metrics/sources/questions/data-quality/evidence-gaps, and
  a non-dict input) — outputs are equal, not just similar. `is_permission_error` checked against 8
  cases including the one input (`"HTTP 403 Forbidden"`) where C1–C6 and C7 genuinely diverge — the
  ported version matches C7's superset behaviour everywhere. Passing.
- `ucc_intelligence/ucc_intelligence/tests/test_shared_runtime.js`: loads the ported `shared.js` from
  its real app path and confirms all 17 `UCCShared` exports are present and functional. Passing.
- Full regression sweep: `tools/validate_package.py` still 94/101 (unchanged baseline),
  `tools/test_dashboard_access.py`, `tools/test_permission_notice.js`, `tools/test_roll_fallback.js`
  all still passing. `git diff --stat` against the pre-Phase-0 commit shows zero changes to
  `custom-html-block/`, `server-scripts/`, `src/`, `dist/`, `archive/`.
- A real import-path bug (`ucc_intelligence.ucc_intelligence.X` instead of `ucc_intelligence.X`) was
  introduced in three files while writing this and caught by the verification harness before commit
  — the exact same class of bug Felix corrected in `phase-1-plan.md` §12.2's test. Fixed in all three
  before anything shipped.

**Not verified**: nothing here has run against a real Frappe site. `bench run-tests`,
`get_dashboard_access()` over HTTP, and the DocType itself all still need the real bench.

## 4. Files left untouched

Same list as `phase-1-plan.md` §2: `custom-html-block/`, `server-scripts/` (all 17 files, including
`UCC Dashboard Access.py` itself — it keeps running in production until parity is proven and Phase 13
cutover), `src/`, `dist/`, `archive/`, `reference/`, `documentation/`. Phase 2 adds a second,
independently-running implementation; it does not touch or disable the first.

## 5. The one remaining item — the app-managed DocType (revised 2026-07-26)

Original plan: reuse the existing "UCC Dashboard Access" DocType, convert it to app-managed, keep
fields/behaviour exactly as-is. That assumed the DocType exists on the live site — never actually
checked until now, only inferred from the Server Script's own docstring.

**Verified on `ucc.local` via `bench console`:**

```
DoesNotExistError: DocType UCC Dashboard Access not found
```

So there is nothing to "convert." Two live possibilities, and this doesn't distinguish between them:

- `ucc.local` is Felix's development/local bench (used throughout Phase 1–2), and the DocType exists
  on whatever site the legacy Custom HTML Block deployment actually runs against, if that's a
  different site.
- The DocType has never existed anywhere, meaning `load_rows()` has always hit its `except Exception`
  fallback in production too — `resolve_default([])` on an empty row list resolves to
  `default_show_everything`, so role-based dashboard visibility restriction may never have actually
  applied. Every user has always seen every workspace and criterion.

**Practical consequence either way**: the DocType needs to be **created fresh** on `ucc.local` (and
possibly reconciled with a production site later, if a different one turns out to have real
configured rows). This doesn't change anything about the ported Python logic in
`permissions/access.py` — it's already correctly generic and its fail-open path is already the
best-tested part of it. It does change two things about the DocType artefact:

1. **Folder depth — unrelated to this finding, still open.** Frappe resolves a DocType's path from
   its `module` field (`ucc_intelligence/ucc_intelligence/<module_name>/doctype/ucc_dashboard_access/`).
   Phase 1 only confirmed the 2-level path for `api.py`/`tests/`. **Still need:**
   `cat ucc_intelligence/modules.txt` and `ls ucc_intelligence/ucc_intelligence/` from the real bench.
2. **`autoname` and `permissions` — now a design decision, not a live-schema lookup.** There's no
   existing DocType to dump and copy from. Proposed, not assumed:
   - `autoname`: `hash` (Frappe's default for a DocType with no single obviously-unique field; the
     legacy code doesn't require `role` to be unique — `union_of` would harmlessly double-apply a
     duplicate row for the same role).
   - `permissions`: read/write/create restricted to `System Manager` (this DocType controls who sees
     what in the platform; it should not be broadly editable).
   **Need Felix's sign-off on both**, not a live dump — this is now a real decision, not verification.

Everything else in the draft (all eleven fields, the Select's two option strings — `Show everything`
/ `Show nothing`) is still confirmed from the Server Script's own field references, unaffected by
this finding. See `docs/migration/phase-2-doctype-draft/README.md`, updated to match.

## 6. `ignore_permissions=True` — confirmed, carried forward with a review marker

Felix confirmed (2026-07-26): carry forward as-is for migration parity, out of Phase 2's scope to
remove. `ucc_intelligence/ucc_intelligence/permissions/access.py`'s `load_rows()` and
`assigned_roles()` both keep the exact bypass and its original justification, plus a new comment
pointing at this decision so it isn't silently made permanent: *"Inherited from the legacy Server
Script as-is for migration parity (Felix, 2026-07-26). Review before Phase 13 cutover rather than
carrying it forward unexamined."*

## 7. Criterion 7's `"403"` check — applied universally, verified against real divergence

Not objected to when flagged, so applied as recommended: `is_permission_error` in
`analytics/contracts.py` includes the `"403"` substring check for all criteria, not just Criterion 7.
`tools/test_ucc_intelligence_contracts.py` specifically checks the one input where this changes
behaviour (`"HTTP 403 Forbidden"` — `False` for legacy C1–C6, `True` for legacy C7 and for the ported
version) so this deliberate deviation from six of the seven originals is pinned by a test, not just
asserted in prose.

## 8. Environment / logistics gap — confirmed

Felix confirmed (2026-07-26): same model as Phase 1. Code lands in this repo, committed to `main`;
Felix relays to the other Claude Code session with real bench access, which pulls from GitHub and
applies it to `ucc-sms.orb.local`.

**One consequence worth being explicit about**: this repo previously had no `ucc_intelligence/`
directory at all — Phase 1's `api.py`/`hooks.py`/`modules.txt`/etc. exist only on the bench, never
synced back. To make Phase 2's new files importable and testable, this commit also adds
`ucc_intelligence/ucc_intelligence/__init__.py` and `api.py` to this repo, reconstructed from the
confirmed-working content in `phase-1-plan.md` §12.1/§12.2 plus the new `get_dashboard_access` shim.
**`hooks.py`, `modules.txt`, `pyproject.toml` and any other bench-generated scaffold files are still
not in this repo** — CLAUDE.md §7 says those must come from the installed Frappe version, not be
hand-authored, so they weren't reproduced here. The other session applying this needs to merge these
new files into the real tree it already has, not treat this repo as a complete, installable copy of
the app.

## 9. Tests to run on the real bench

- `bench --site ucc-sms.orb.local run-tests --app ucc_intelligence` — `test_api.py` (Phase 1,
  unaffected) and the new `test_access.py` smoke test
- Existing repo self-checks, unaffected baseline: `python3 tools/validate_package.py` (94/101, known
  baseline), `python3 tools/test_dashboard_access.py`, `python3 tools/test_ucc_intelligence_access.py`,
  `python3 tools/test_ucc_intelligence_contracts.py`, `node tools/test_permission_notice.js`,
  `node ucc_intelligence/ucc_intelligence/tests/test_shared_runtime.js`, `node tools/test_roll_fallback.js`
- Manual, per CLAUDE.md §9 Phase 2 exit criteria: confirm hidden criteria are genuinely not mounted or
  queried once there's a page to check this on — this needs a consumer, which doesn't exist until
  Phase 3. Flagged, not solved, here (see §10).

## 10. Archive plan

Nothing moves to `archive/`. `UCC Dashboard Access.py` keeps running in production; the new
`permissions/access.py` is a second, parallel, unwired implementation until parity is proven per
CLAUDE.md §1.1.15 and the legacy path is disabled at Phase 13 cutover — not this phase.

## 11. Rollback

Nothing here touches `server-scripts/` or `custom-html-block/`, so a git revert on the app-tree
changes is sufficient on the code side. The DocType conversion (§5), once its two open facts are
confirmed and it's actually placed and migrated, needs its own `bench backup` before `bench migrate`
— same requirement as Phase 1 §9.

## 12. Exit criteria — copied verbatim from CLAUDE.md §9 Phase 2

- [x] Existing role behaviour is reproduced. — all 20 legacy scenarios pass against the ported
      module (`tools/test_ucc_intelligence_access.py`), including the role-leak regression.
- [ ] Hidden criteria are not mounted or queried. — **can't be checked yet.** No page mounts
      dashboards until Phase 3; `get_dashboard_access()` returning correct visibility is necessary
      but not sufficient for this criterion.
- [x] Backend permissions remain authoritative. — `get_dashboard_access()` still only composes the
      UI; no data read anywhere was changed, added, or bypassed by this phase.
- [x] Permission errors do not reveal stack traces or sensitive details to ordinary users. — ported
      `shared.js` unchanged (byte-identical), so `UCCShared`'s existing notice/redaction behaviour is
      unaffected; `analytics/contracts.py`'s `is_permission_error` is a classifier only, doesn't
      itself expose anything.
- [ ] Administrator diagnostics remain available in a controlled manner. — **not exercised.** The
      legacy `ucc_shared_diagnostics` script is untouched; nothing new was built or tested for
      administrator-facing diagnostics this phase.

Not marking this phase DONE — two boxes are unchecked for real reasons (one needs Phase 3 to exist,
one wasn't in scope this round), not glossed over.

---

## 13. What's still needed from you

1. **One fact, unaffected by the DocType finding** (§5): `cat ucc_intelligence/modules.txt` and
   `ls ucc_intelligence/ucc_intelligence/` from the real bench, to place the DocType folder correctly.
2. **Two design decisions, now that there's no live schema to copy** (§5): sign off on the proposed
   `autoname: hash` and `permissions: System Manager only`, or give different ones.
3. **Optional but worth knowing**: is `ucc.local` the same site the legacy Custom HTML Block actually
   runs against, or a separate development/local bench? Doesn't block placing the DocType either way,
   but affects whether "role-based visibility has possibly never been configured anywhere" is a fact
   about production or just about this dev site.

Once 1 and 2 are answered: I place the DocType at its confirmed path with the agreed `autoname`/
`permissions`, and this becomes a normal commit — no further decision needed.
