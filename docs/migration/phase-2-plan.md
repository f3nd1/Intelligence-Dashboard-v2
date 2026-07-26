# Phase 2 Plan — Migrate access and shared runtime services

Plan only. **No code has been written for this phase.** Per CLAUDE.md §9 Phase 2 goal: "Move shared
permission and runtime logic before moving dashboards."

## 0. Scope check against your instruction

You asked to "migrate `ucc_dashboard_access`... and start bringing in the actual dashboard/analytics
logic." CLAUDE.md §9 Phase 2's required-work list is five bullets, and none of them is dashboard or
analytics logic — that's Phase 3 ("Migrate Analytics frontend shell") and Phase 4 ("Migrate Criterion
APIs one at a time"). §23's final direction is explicit: "Do not reverse this order by adding an
impressive AI layer on top of unstable, untested, or insecure data access" — the whole document is
built around not skipping ahead.

Reading your instruction as "the substantive migration work starts now" (as opposed to Phase 0/1
scaffolding) rather than "do Phase 3/4 work inside Phase 2" — **this plan scopes strictly to CLAUDE.md
§9 Phase 2's five bullets.** No criterion API, no chart engine, no Desk Page shell. If you meant
something closer to Phase 3/4 starting in parallel, say so explicitly — I'm not deciding that
silently by picking the narrow reading and moving on.

## 1. What Phase 2 required work actually is (CLAUDE.md §9)

- Migrate `ucc_dashboard_access` from Server Script to app Python.
- Preserve the current access DocType or replace it with an app-managed equivalent.
- Migrate shared error classification and blocked-source presentation.
- Establish common API response and error contracts.
- Add audit-safe logging and redaction.
- Create tests for role combinations and denied sources.

## 2. What gets built, mapped to real legacy code (re-read in full for this plan)

| # | Required-work bullet | Source (verified this session) | New owner (proposed) |
|---|---|---|---|
| 1 | Migrate `ucc_dashboard_access` | `server-scripts/UCC Dashboard Access.py` (260 lines, read in full). Pure functions: `load_rows`, `resolve_default`, `union_of`, `assigned_roles`, `role_key`, `build_response`, all fail-open on error. | `ucc_intelligence/ucc_intelligence/permissions/access.py`, one whitelisted `get_dashboard_access()` wrapping the same `build_response()` logic |
| 2 | Preserve or replace the access DocType | `UCC Dashboard Access` — exists only as a manually-created DocType on the live site, not in this repo (parity-matrix.md O7, still open) | **Blocking decision — §5 below** |
| 3 | Migrate shared error classification + blocked-source presentation (JS) | `src/js/00-shared-runtime.js` (251 lines, read in full): `errorText`, `classifyError`, `isPermissionError`, `permissionSource`, `permissionNoticeHtml`, `renderPermissionNotice`, `installPermissionMessageFilter`, `noteBlockedSource`/`blockedSources`. Frozen `window.UCCShared` export. | `ucc_intelligence/public/js/shared.js` — straight port, `[REUSE]` per parity-matrix.md X8 |
| 4 | Common API response and error contracts (Python) | `standardise_response_contract` — **verified byte-identical across all seven** `server-scripts/UCC Analytics - Criterion *.py` (confirmed by hash this session, not just cited from the prior reports). `is_permission_error` — identical in six, **Criterion 7 alone also matches the substring `"403"`** (confirmed by direct diff this session). | `ucc_intelligence/ucc_intelligence/analytics/contracts.py` — one deduped copy of each, ready for Phase 4 criterion scripts to call. Not wired to any live script yet — none are touched this phase. |
| 5 | Audit-safe logging and redaction | No legacy equivalent — new work. CLAUDE.md §12.4 (audit trail fields) and §14.2 (log levels, structured logs, diagnostic ID) | `ucc_intelligence/ucc_intelligence/logging/audit.py`, `redaction.py` — minimal: log user, method, applied outcome, error reference; no full payloads |
| 6 | Tests for role combinations and denied sources | `tools/test_dashboard_access.py` — 20 scenarios incl. the role-leak regression fixed in `49361a8`, already passing against the legacy script. `tools/test_permission_notice.js` — 28 assertions against the real shared runtime, already passing. | Port both into `ucc_intelligence/ucc_intelligence/tests/test_access.py` (Frappe `FrappeTestCase`, real DocType fixtures instead of a stubbed `frappe`) and a JS self-check alongside `public/js/shared.js` |

## 3. Files left untouched

Same list as `phase-1-plan.md` §2, unchanged: `custom-html-block/`, `server-scripts/` (all 17 files,
including `UCC Dashboard Access.py` itself — it keeps running in production until parity is proven
and Phase 13 cutover), `src/`, `dist/`, `archive/`, `reference/`, `documentation/`, `tools/`. Phase 2
adds a second, independently-running implementation; it does not touch or disable the first.

No criterion Server Script is edited or read as input to new code this phase — `contracts.py` is
built from the shared function bodies verified in §2 row 4, not from any one criterion's surrounding
logic.

## 4. Explicit call-outs (not decided silently)

**`ignore_permissions=True` continues.** `UCC Dashboard Access.py:103` and `:159` use it, with an
in-line justification: the DocType holds interface-composition checkboxes only, no business data,
and must stay readable by the very users it configures. Porting the logic means porting that bypass
too. CLAUDE.md §1.1.10: "Permission bypasses require an explicit documented reason and approval." The
reason is already documented (and carries over verbatim); **the approval is yours to give, not mine
to assume** — confirm before this ships.

**Criterion 7's extra `"403"` check in `is_permission_error`.** Deduping into one shared function
means picking one behaviour. Recommendation: include it universally — a broader match only makes more
genuine permission errors resolve to the correct notice, and no other criterion's text triggers a
false positive from it (verified: none of the other six scripts' error paths pass raw HTTP status
codes through `is_permission_error`'s input). Not silently applied — noted here per §19's spirit even
though this specific item isn't on the §19 list.

## 5. Blocking decision — the access DocType (required-work bullet 2)

CLAUDE.md §9 names this Phase 2's own decision, not deferred to later. Two options:

- **Option A (recommended)** — keep reading the *same* site `UCC Dashboard Access` DocType, unmanaged
  by the app, exactly as the Server Script does today. Zero config migration, zero risk of losing
  Felix's existing rows. `get_dashboard_access()` in the new app points at the identical DocType name
  and fields.
- **Option B** — convert it into an app-managed DocType with a fixture (matches CLAUDE.md §7's target
  structure, `doctype/ucc_dashboard_access/`). Requires exporting the live configuration, defining the
  DocType in the app, and a migration path for existing rows — real work, and a real chance to get the
  field list subtly wrong relative to what's on the site now.

Recommending **Option A** for this phase, same pattern as Phase 1's role choice: smallest safe
reversible step, stated rather than assumed. Confirm before I build against it.

## 6. Environment / logistics gap this plan surfaces

The `ucc_intelligence` app that Phase 1 verified lives in your local bench's `apps/ucc_intelligence`
(its own git repo, created by `bench new-app`). **This repository does not contain that app tree.**
Everything I write for Phase 2 has to land somewhere — either:

- I write it into this repo at `ucc_intelligence/` (matching CLAUDE.md §7's intended structure, where
  this repo eventually *is* the app), and you copy/sync it into your bench's `apps/ucc_intelligence`
  before running `bench migrate`/tests; or
- some other sync mechanism you already have in mind (e.g. your local `apps/ucc_intelligence` gets
  re-pointed at this GitHub repo as its remote).

This blocks nothing about *writing* the plan or the code, but it blocks you being able to actually run
and verify it without knowing which. Tell me which, or say to just proceed with the first option and
you'll handle the copy.

## 7. Tests to run (once code exists and the sync question is answered)

- `bench --site ucc-sms.orb.local run-tests --app ucc_intelligence` — new `test_access.py`, ported
  from `tools/test_dashboard_access.py`'s 20 scenarios
- JS self-check for the ported `shared.js`, same assertions as `tools/test_permission_notice.js`
- Existing repo self-checks unaffected, same as Phase 1 §7: `python3 tools/validate_package.py`,
  `python3 tools/test_dashboard_access.py`, `node tools/test_permission_notice.js`,
  `node tools/test_roll_fallback.js` — baseline must not move, since `server-scripts/` isn't touched
- Manual, per CLAUDE.md §9 Phase 2 exit criteria: confirm hidden criteria are genuinely not mounted or
  queried (not just hidden by CSS) once there's a page to check this on — likely spills into Phase 3
  if no interim page exists yet; flagged, not solved, here

## 8. Archive plan

Nothing moves to `archive/`. `UCC Dashboard Access.py` keeps running in production; the new
`permissions/access.py` is a second, parallel, unwired implementation until parity is proven per
CLAUDE.md §1.1.15 and the legacy path is disabled at Phase 13 cutover — not this phase.

## 9. Rollback

Same shape as Phase 1 §9: nothing here touches `server-scripts/` or `custom-html-block/`, so a git
revert on the app-tree changes is sufficient on the code side. If Option A is chosen (§5), no site
DocType is touched either — this phase only adds a second reader of the same configuration. If Option
B is chosen, the DocType conversion needs its own backup-before-migrate step, same as Phase 1 §9's
`bench backup` requirement.

## 10. Exit criteria — copied verbatim from CLAUDE.md §9 Phase 2 (not yet attempted)

- [ ] Existing role behaviour is reproduced.
- [ ] Hidden criteria are not mounted or queried.
- [ ] Backend permissions remain authoritative.
- [ ] Permission errors do not reveal stack traces or sensitive details to ordinary users.
- [ ] Administrator diagnostics remain available in a controlled manner.

Note on "Hidden criteria are not mounted or queried": this genuinely can't be checked until there's a
page mounting dashboards at all, which is Phase 3 territory. Phase 2 can prove `get_dashboard_access()`
returns correct role-based visibility (via the ported test suite); proving nothing hidden gets mounted
needs a consumer, which doesn't exist yet. Flagging now so it isn't forgotten, not solving it early.

---

## 11. What I need from you before writing code

1. **Scope confirmation** (§0) — Phase 2 = access + shared runtime only, per CLAUDE.md §9, not
   analytics logic.
2. **Code sync mechanism** (§6) — write into this repo's `ucc_intelligence/` and you copy it into your
   bench, or something else.
3. **DocType decision** (§5) — Option A (reuse existing site DocType, recommended) vs. Option B
   (convert to app-managed).
4. **Approval to continue `ignore_permissions=True`** (§4) on the ported access-check reads, same
   justification as today.

Everything else in this plan (the C7 `"403"` handling, the shared-contract dedup shape, the
audit-logging minimum fields) has a stated default and doesn't need an answer to start — say so if
any of those defaults are wrong.
