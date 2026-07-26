# UCC Dashboard Access — app-managed DocType (draft, not placed)

Per your answer #3: reuse the existing "UCC Dashboard Access" DocType, convert it to app-managed,
keep its fields and behaviour exactly as-is. This directory is a **draft**, deliberately not placed
inside `ucc_intelligence/` yet, because two things about it can't be confirmed from this repo:

## 1. Where the doctype folder actually goes

Frappe resolves a DocType's folder path from its `module` field (snake-cased), under
`ucc_intelligence/ucc_intelligence/<module_name>/doctype/ucc_dashboard_access/`. Phase 1 confirmed
`ucc_intelligence/ucc_intelligence/api.py` and `.../tests/` sit at the package root (2 levels), but
that tells us nothing about the module name `bench new-app` assigned for DocTypes/Pages/Workspaces —
by far the most common default is a third folder matching the app name again (i.e.
`ucc_intelligence/ucc_intelligence/ucc_intelligence/doctype/...`), but it isn't guaranteed, and a
DocType placed at the wrong depth is silently never picked up by `bench migrate` — a worse failure
than asking.

**Need:** `cat ucc_intelligence/modules.txt` from the real bench, and `ls ucc_intelligence/ucc_intelligence/`
(does a third `ucc_intelligence/` folder already exist there, e.g. from the Workspace/Page scaffolding
`bench new-app` may have created?).

## 2. Fields I'm confident about vs. fields I'm not

Confident (from the Server Script's own field references — `ACCESS_FIELDS`, `WORKSPACE_FIELDS`,
`CRITERION_KEYS`, `SHOW_EVERYTHING`/`SHOW_NOTHING`, all read in full this session): the eleven fields
in `ucc_dashboard_access.json` below, their fieldnames, and that `default_when_unconfigured` is a
Select with exactly the two options `Show everything` / `Show nothing`.

**Not confident, not guessed, left as `<<CONFIRM>>` markers below:**
- `autoname` — how a row's `name` is generated. The legacy script never creates rows, only reads
  them, so nothing in the code confirms this.
- `permissions` — which roles can read/write/create rows. This is a permission-configuration
  DocType; getting this wrong is a real security question, not a cosmetic one.
- Field `label`s as shown in the Desk UI, and field order — cosmetic, lower risk, but "keep
  behaviour exactly as-is" should mean the form looks the same too.
- Whether `role` is unique per row (the legacy code doesn't require it — `union_of` would harmlessly
  double-apply a duplicate — but the live DocType's own constraint may be stricter).

**Fastest way to fill these in:** on the real bench, `bench --site ucc-sms.orb.local console` then:

```python
import json
print(json.dumps(frappe.get_doc("DocType", "UCC Dashboard Access").as_dict(), indent=2, default=str))
```

Paste that back and I'll complete `ucc_dashboard_access.json` exactly, then place both files at the
confirmed path in a follow-up commit.

## What's in this directory

- `ucc_dashboard_access.json` — draft DocType definition, `<<CONFIRM>>` markers where noted above.
- `ucc_dashboard_access.py` — draft controller (empty `Document` subclass; the legacy script has no
  validation hooks, so there's nothing to port into it unless the live DocType has customisations
  this repo doesn't know about).

Once both open items are answered, these move to their real path and this directory is deleted.
