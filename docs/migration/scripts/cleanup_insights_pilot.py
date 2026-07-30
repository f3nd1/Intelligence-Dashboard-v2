"""Unpublish and delete the Frappe Insights pilot's Query/Chart/Dashboard v3
records (docs/migration/insights-pilot-findings.md Section 4(b)).

Why this exists: the pilot's own permission test proved the pilot Dashboard
is readable by a genuinely unauthenticated request -- full record, including
the underlying query config, no partial redaction (see the findings doc,
Section 4(b), "Confirmed -- the worst outcome"). That's a live data-exposure
risk on the real site independent of whatever direction the Criterion 4/5
migration takes, so it gets cleaned up on its own, not bundled into that work.

What this does NOT touch: the "Site DB" Insights Data Source and the
"Workbook 2" Insights Workbook. create_insights_pilot.py's own
stage_1b_check_existing() calls confirm both were *reused*, not created by
the pilot -- they're shared infrastructure other things may depend on, so
deleting them here would be a scope overreach this script explicitly avoids.

Finds every record by title, not by one hardcoded name, because the pilot
went through several record names across its debugging saga
(tt5b9kk0bn/tt51l7mma3, qinmiinfrs/qinaqei0rn, ionf4ct5je/ionlk6l8mn) --
create_insights_pilot.py's own reuse-existing-by-title logic means there
should be at most one of each on a given site, but this looks them up by
title rather than assuming which specific name survived.

Usage -- paste into `bench --site <your-site> console` (confirm the real
site name via `ls sites/` first; a prior session in this same pilot lost
significant time to an assumed-vs-real site-name mismatch, see the findings
doc's "root cause has moved to the site name itself" update):

    exec(open("docs/migration/scripts/cleanup_insights_pilot.py").read(), globals())

The trailing `globals()` matters: bare `exec(open(...).read())` inherits
whatever globals()/locals() are active at its own call site, and if bench
console evaluates pasted input from inside some internal method
(globals() != locals() there), a `def` function referencing a sibling
top-level name resolves it via LOAD_GLOBAL against __globals__, which
never received it -- silent NameError (this exact bug hit a near-identical
script tonight, see build_admission_intelligence_embed.py's usage note).
`exec(source, globals())` forces one shared namespace instead, closing it
off here too.

Two-phase by design, matching the lesson learned building the pilot itself
(bench console rolls back uncommitted work on exit, frappe/commands/utils.py
_console_cleanup): STAGE_1 only prints what it found and does nothing
mutating. Read that output, confirm it's actually the pilot records, then
set CONFIRM_DELETE = True below (or just call stage_2_delete() directly) to
actually remove them -- each deletion is followed by frappe.db.commit() and
an independent frappe.db.exists() re-check, not assumed to have worked.
"""

import frappe

PILOT_TITLE = "Sophia Pilot - Student Applicants per Year"

TARGET_DOCTYPES = ["Insights Dashboard v3", "Insights Chart v3", "Insights Query v3"]

CONFIRM_DELETE = False  # flip to True (or call stage_2_delete() directly) after reviewing STAGE_1's output


def stage_1_find():
    print("=" * 70)
    print("STAGE 1 -- find pilot records by title (read-only, nothing changes)")
    print("=" * 70)
    found = {}
    for doctype in TARGET_DOCTYPES:
        rows = frappe.get_all(
            doctype,
            filters={"title": PILOT_TITLE},
            fields=["name", "title"] + (["is_public", "share_link"] if doctype == "Insights Dashboard v3" else []),
        )
        found[doctype] = rows
        print("\n%s: %d found" % (doctype, len(rows)))
        for row in rows:
            print("  ", row)
    total = sum(len(v) for v in found.values())
    print("\nTotal records matching title %r: %d" % (PILOT_TITLE, total))
    if total == 0:
        print("Nothing found -- either already cleaned up, or the title above doesn't match.")
        print("If you know the pilot's record names directly, check frappe.db.exists(doctype, name) for those instead.")
    return found


def stage_1b_unpublish(found):
    """Safe, reversible first step: clear public exposure immediately,
    before the (permanent) delete in stage 2. Dashboard v3 is the only
    doctype with is_public/share_link (see the module docstring's citation
    of insights_dashboard_v3.py)."""
    print("\n" + "=" * 70)
    print("STAGE 1b -- unpublish (is_public=0, share_link cleared), immediate")
    print("=" * 70)
    for row in found.get("Insights Dashboard v3", []):
        if not row.get("is_public"):
            print("  %s already not public, skipping" % row["name"])
            continue
        doc = frappe.get_doc("Insights Dashboard v3", row["name"])
        doc.is_public = 0
        doc.share_link = None
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        still_public = frappe.db.get_value("Insights Dashboard v3", row["name"], "is_public")
        print("  %s -> is_public=%s (unpublished)" % (row["name"], still_public))


def stage_2_delete(found):
    print("\n" + "=" * 70)
    print("STAGE 2 -- delete (permanent)")
    print("=" * 70)
    # Delete children before the record they reference: Dashboard first
    # (it links to the Chart), then Chart (links to the Query), then Query.
    for doctype in ["Insights Dashboard v3", "Insights Chart v3", "Insights Query v3"]:
        for row in found.get(doctype, []):
            name = row["name"]
            frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
            frappe.db.commit()
            still_exists = frappe.db.exists(doctype, name)
            status = "FAILED -- still exists" if still_exists else "deleted, confirmed gone"
            print("  %s %s: %s" % (doctype, name, status))


found = stage_1_find()
if sum(len(v) for v in found.values()) > 0:
    stage_1b_unpublish(found)
    print("\nReview the STAGE 1 / 1b output above.")
    print("To permanently delete, run: stage_2_delete(found)")
    if CONFIRM_DELETE:
        stage_2_delete(found)
