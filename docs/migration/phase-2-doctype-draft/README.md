# UCC Dashboard Access — app-managed DocType (draft, not placed)

**Revised 2026-07-26.** The original plan was "reuse the existing DocType, convert it to
app-managed." Verified via `bench console` on `ucc.local`:

```
DoesNotExistError: DocType UCC Dashboard Access not found
```

There is nothing to convert — this DocType doesn't exist on that site. Whether it exists on whatever
site the legacy Custom HTML Block deployment actually runs against (if different from `ucc.local`) is
unconfirmed. Either way, on `ucc.local` this now needs to be **created fresh**, matching the Server
Script's documented field shape (that part of the plan is unaffected). This directory is still a
**draft**, deliberately not placed inside `ucc_intelligence/` yet, for two reasons — one unchanged by
this finding, one now different in kind.

## 1. Where the doctype folder actually goes (unaffected by the DocType finding)

Frappe resolves a DocType's folder path from its `module` field (snake-cased), under
`ucc_intelligence/ucc_intelligence/<module_name>/doctype/ucc_dashboard_access/`. Phase 1 confirmed
`ucc_intelligence/ucc_intelligence/api.py` and `.../tests/` sit at the package root (2 levels), but
that tells us nothing about the module name `bench new-app` assigned for DocTypes/Pages/Workspaces —
by far the most common default is a third folder matching the app name again (i.e.
`ucc_intelligence/ucc_intelligence/ucc_intelligence/doctype/...`), but it isn't guaranteed, and a
DocType placed at the wrong depth is silently never picked up by `bench migrate` — a worse failure
than asking.

**Need:** `cat ucc_intelligence/modules.txt` from the real bench, and `ls ucc_intelligence/ucc_intelligence/`
(does a third `ucc_intelligence/` folder already exist there, e.g. from Workspace/Page scaffolding
`bench new-app` may have created?).

## 2. Fields — now split into "confirmed from the script" and "a design decision," not "confirmed vs. needs a live dump"

Confident (from the Server Script's own field references — `ACCESS_FIELDS`, `WORKSPACE_FIELDS`,
`CRITERION_KEYS`, `SHOW_EVERYTHING`/`SHOW_NOTHING`, all read in full this session, unaffected by the
DocType finding): the eleven fields in `ucc_dashboard_access.json` below, their fieldnames, and that
`default_when_unconfigured` is a Select with exactly the two options `Show everything` /
`Show nothing`.

**Not confirmable from the script, and now a genuine design decision rather than something to copy
from a live schema** (there is no live schema):

- `autoname` — **proposed: `hash`.** The legacy code never requires `role` to be unique per row —
  `union_of` would harmlessly double-apply a duplicate — so there's no natural unique field to
  autoname from. `hash` is Frappe's own default for exactly this shape of DocType.
- `permissions` — **proposed: read/write/create restricted to `System Manager`.** This DocType
  controls who sees what in the platform; it should not be broadly editable. This is the one real
  security decision here — flagging it as a proposal, not shipping it unconfirmed.
- Field `label`s and order — cosmetic, proposed as plain-English versions of the fieldnames below
  (already in the JSON), lower stakes than the two above.

**These need Felix's sign-off, not a live-bench command** — there's nothing left to dump and copy.

## What's in this directory

- `ucc_dashboard_access.json` — draft DocType definition. `<<CONFIRM>>` markers remain only for the
  module name (§1); `autoname`/`permissions` now carry proposed values instead of markers, pending
  sign-off rather than a live dump.
- `ucc_dashboard_access.py` — draft controller (empty `Document` subclass; the legacy script has no
  validation hooks to port).

Once the module name is confirmed and `autoname`/`permissions` are signed off, these move to their
real path and this directory is deleted.
