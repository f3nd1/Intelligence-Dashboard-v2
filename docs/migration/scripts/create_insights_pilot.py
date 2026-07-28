"""Create the Frappe Insights pilot Data Source / Query / Chart for the
Analytics-Insights feasibility spike (docs/migration/insights-pilot-findings.md).

Written by a repo-only Claude Code session with no bench/site access -- it
cannot verify Frappe Insights v3.12.2's actual DocType/field schema (Insights
isn't vendored in this repo), so this deliberately DISCOVERS the real schema
first and prints it before attempting to create anything, rather than
hardcoding field names guessed from older Insights docs or training data.

Usage: paste this whole file into `bench --site ucc-sms-v2 console`, or:
    bench --site ucc-sms-v2 execute docs.migration.scripts.create_insights_pilot.run
(the latter requires this file to be importable from the bench's Python path --
console paste is simpler and doesn't require that).

Run STAGE 0 and STAGE 1 first (read-only, safe, fast). If either turns up
something unexpected -- academic_year isn't a real field, or the Insights
DocType names below don't match what's actually installed -- STOP and report
back rather than pushing through Stage 2 with guessed names. That mirrors the
approach this migration has used throughout: verify against the live system,
don't assume.
"""

import frappe

PILOT_DOCTYPE = "Student Applicant"
PILOT_FIELD = "academic_year"


def stage_0_verify_schema():
    """Confirm the field the legacy JS/Python code assumes exists actually
    does -- server-scripts/UCC Analytics - Criterion 4.py never checks this
    itself (unlike nationality/program/agent, which go through
    resolve_field() with a candidate list); it just uses "academic_year"
    literally. If it's wrong, group_count_rows() silently buckets every row
    under "Not specified" instead of erroring -- worth knowing before
    building a query around it.
    """
    print("=== STAGE 0: verify Student Applicant.academic_year ===")
    meta = frappe.get_meta(PILOT_DOCTYPE)
    has_field = meta.has_field(PILOT_FIELD)
    print(f"{PILOT_DOCTYPE}.{PILOT_FIELD} exists: {has_field}")
    if not has_field:
        candidates = [
            f.fieldname
            for f in meta.fields
            if any(kw in f.fieldname.lower() for kw in ("year", "academic", "batch", "cohort", "intake"))
        ]
        print(f"academic_year NOT found. Similarly-named fields on {PILOT_DOCTYPE}: {candidates}")
        print("STOP -- do not proceed to Stage 2 until the real field name is confirmed.")
        return False
    field_meta = meta.get_field(PILOT_FIELD)
    print(f"fieldtype: {field_meta.fieldtype}, label: {field_meta.label!r}")
    sample = frappe.get_all(
        PILOT_DOCTYPE, fields=[PILOT_FIELD], filters={PILOT_FIELD: ["is", "set"]}, limit=5, distinct=True
    )
    print(f"sample non-empty values: {[r[PILOT_FIELD] for r in sample]}")
    total = frappe.db.count(PILOT_DOCTYPE)
    blank = frappe.db.count(PILOT_DOCTYPE, filters={PILOT_FIELD: ["in", [None, ""]]})
    print(f"total {PILOT_DOCTYPE} rows: {total}, rows with blank {PILOT_FIELD}: {blank}")
    return True


def stage_1_discover_insights_schema():
    """List the real Insights DocTypes and their fields on THIS install,
    rather than assuming v3.12.2 matches whatever schema older docs (or an
    LLM's training data) describe. Insights v3 is a significant rewrite
    (ibis-based query engine) from earlier versions -- don't assume names.
    """
    print("\n=== STAGE 1: discover real Insights schema ===")
    insights_doctypes = frappe.get_all(
        "DocType", filters={"module": ["like", "%Insight%"]}, pluck="name", order_by="name"
    )
    print(f"Insights-module DocTypes found: {insights_doctypes}")

    relevant = [
        dt
        for dt in insights_doctypes
        if any(kw in dt for kw in ("Data Source", "Query", "Chart", "Table"))
    ]
    schema = {}
    for dt in relevant:
        meta = frappe.get_meta(dt)
        fields = [(f.fieldname, f.fieldtype) for f in meta.fields]
        schema[dt] = fields
        print(f"\n--- {dt} ---")
        for fieldname, fieldtype in fields:
            print(f"  {fieldname}: {fieldtype}")
    return relevant, schema


def stage_1b_check_existing_data_source(data_source_doctype):
    """Constraint: must not create a duplicate Data Source pointing at Site
    DB. Check what's already there first.
    """
    print(f"\n=== STAGE 1b: existing {data_source_doctype} records ===")
    existing = frappe.get_all(data_source_doctype, fields=["name"], limit=50)
    print(f"Existing: {existing}")
    for row in existing:
        doc = frappe.get_doc(data_source_doctype, row["name"])
        as_dict = doc.as_dict()
        # Print only fields that look identifying, skip noise (metadata/timestamps).
        interesting = {
            k: v
            for k, v in as_dict.items()
            if k in ("name", "title", "database_type", "database_name", "status", "connection_string")
        }
        print(f"  {row['name']}: {interesting}")
    return existing


def stage_2_guidance():
    print(
        """
=== STAGE 2: creation -- do this by hand once Stage 0/1 output is confirmed ===

I'm deliberately NOT auto-creating records here. Field/child-table shapes for
Insights v3's Query Builder (the "assisted query" JSON structure -- filters,
group-bys, aggregates as a nested list, not flat DocFields) vary enough
between Insights versions that a guessed structure is more likely to create a
malformed Query than a working one. Once Stage 1's real field list is in
hand, report it back and the actual creation call (matching the confirmed
schema exactly) will be written from that, not from a guess.

What to report back:
  1. Stage 0 output (does academic_year exist, sample values, blank count)
  2. Stage 1 output (the real DocType names + field lists for whichever
     Data Source / Query / Chart doctypes actually exist on this install)
  3. Stage 1b output (does a Site DB data source already exist, and its name)
  4. Whether "Student Applicant" appears as a queryable table once a Site DB
     source is confirmed (Insights typically auto-discovers all
     `tab<DocType>` tables for a database-type source -- confirm this one
     isn't excluded/hidden for some reason before assuming it'll just work)

One more thing worth flagging while you're in there: if the Data Source is
configured as a direct site-database connection ("Site DB"), Insights queries
against it typically run with the site's raw DB credentials, NOT through
Frappe's permission layer -- meaning the query has no concept of
`ucc_dashboard_access` or per-user DocType permissions at all. That's not
something to fix in this task, but it's directly relevant to the pilot's own
Step 4(b) permission test (docs/migration/insights-pilot-findings.md) --
worth having front of mind once you get that far.
"""
    )


def run():
    ok = stage_0_verify_schema()
    relevant, schema = stage_1_discover_insights_schema()
    data_source_doctypes = [dt for dt in relevant if "Data Source" in dt]
    if data_source_doctypes:
        stage_1b_check_existing_data_source(data_source_doctypes[0])
    else:
        print("\nNo '*Data Source*' DocType found under the Insights module -- report the full Stage 1 list back.")
    stage_2_guidance()
    if not ok:
        print("\nReminder: Stage 0 did not confirm academic_year exists. Resolve that before Stage 2.")


if __name__ == "__main__":
    run()
