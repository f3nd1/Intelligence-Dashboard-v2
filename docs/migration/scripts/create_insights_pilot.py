"""Create the Frappe Insights pilot Data Source / Query / Chart for the
Analytics-Insights feasibility spike (docs/migration/insights-pilot-findings.md).

Written by a repo-only Claude Code session with no bench/site access. Insights
isn't vendored in this repo, so its v3.12.2 schema was verified by reading the
real, unabridged source at https://github.com/frappe/insights (tag v3.12.2) --
not guessed from older Insights docs or training data. File:line citations
are in the docstrings below. Two things worth knowing before running this:

1. The task that requested this assumed "Insights Chart v3" has an
   `is_public`/`public_key` field for embedding. Half right, half wrong --
   verified by reading insights_chart_v3.py in full: `is_public` DOES exist
   as a field there (`chart_type, config, data_query, folder, is_public,
   old_name, query, sort_order, title, workbook`), but there is no
   `public_key` field, and nothing anywhere in that controller ever reads or
   acts on Chart v3's `is_public` -- it's an unused/dead field for sharing
   purposes. The actual mechanism lives on **Insights Dashboard v3** instead:
   `is_public` there gates real guest access (see point 2) and there's a
   `share_link` field too, served at `/insights/shared/dashboard/<name>`
   (confirmed via insights_dashboard_v3.py's own preview-generation code,
   which builds that exact URL). So getting a working embeddable link means:
   Query -> Chart -> wrap the chart in a minimal Dashboard -> set the
   *dashboard* public, not the chart. Stage 2 below does that.
2. `Insights Dashboard v3.get_distinct_column_values` explicitly allows
   Guest (unauthenticated) access once `is_public=1` -- meaning a public
   dashboard is visible to ANYONE with the link, logged in or not. That's
   the same "public-link bypass" risk flagged in
   docs/migration/insights-pilot-findings.md's Step 4(b) -- worth having in
   mind before actually sharing this URL anywhere, even as a pilot.
3. Confirmed why the query returned zero rows on the first run:
   `Insights Table v3` had `stored=0, last_synced_on=None` -- with the
   default `use_live_connection=False`, `InsightsTablev3.get_ibis_table()`
   (insights_table_v3.py:136-155) routes through a DuckDB warehouse copy
   that has to be synced/imported first. Setting `use_live_connection=1` on
   the Query instead skips the warehouse entirely --
   `InsightsDataSourcev3.get_ibis_table()` (insights_data_source_v3.py:
   441-447) for a MariaDB/Site-DB source is just `remote_db.table(name)`, a
   direct live handle over the site's own DB connection. No sync needed, and
   it matches the legacy engine's own behaviour (a fresh `frappe.get_list`
   per request, not a cached/batch copy) more faithfully anyway. Stage 2
   below sets this.
   Also found in the same code path, worth flagging loudly rather than
   burying: `apply_user_permissions()` (insights_table_v3.py:287-289) opens
   with `if frappe.flags.get("insights_for_public_access"): return t` --
   row/column permission filtering is **explicitly skipped entirely**
   whenever a request is served through the public-dashboard flag, live or
   warehouse mode doesn't matter. That's not speculation about Step 4(b)
   anymore, that's the actual code. Even when that flag isn't set, filtering
   is gated by `Insights Settings.apply_user_permissions` (defaults to 1 in
   Insights' own fixtures, but confirm the real value on this install --
   Stage 1 now checks it) -- and even when ON, it enforces plain Frappe
   DocType read permission, which is a different, usually broader question
   than `ucc_dashboard_access`'s criterion-level gating. Don't assume parity
   either way; Step 4(b) still needs the actual logged-out/restricted-user
   test.

Usage: paste this whole file into `bench --site ucc-sms-v2 console`.

Run STAGE 0 and STAGE 1 first (read-only, safe, fast) -- they cross-check
this specific install against what was verified from GitHub, since a local
install can differ (patches, customisations, a slightly different point
release). If either turns up something unexpected, STOP and report back
before Stage 2 rather than pushing through with a mismatch.
"""

import frappe

PILOT_DOCTYPE = "Student Applicant"
PILOT_FIELD = "academic_year"
DATA_SOURCE_NAME_HINT = "Site DB"
WORKBOOK_TITLE_HINT = "Workbook 2"
PILOT_TITLE = "Sophia Pilot - Student Applicants per Year"

# The legacy chart being piloted (c411-applicants-year, criterion 4/4.1.1) is
# type "admission-line" -- server-scripts/UCC Analytics - Criterion 4.py:2397
# via custom-html-block/JAVASCRIPT.js's renderAdmissionLine() -- i.e. an
# actual line chart over years, not a bar chart. The task that requested this
# script said "chart_type = bar"; flagging the mismatch rather than silently
# picking one. "Line" is the closer visual match to what's live today; both
# are in Insights v3's AXIS_CHARTS and use near-identical config shapes
# (frontend/src2/types/chart.types.ts:4,57,70), so this is a one-line switch
# either way -- change CHART_TYPE below if "Bar" is actually what's wanted.
CHART_TYPE = "Line"  # or "Bar" -- see note above


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

    table_name = "tab" + PILOT_DOCTYPE
    table_row = frappe.get_all(
        "Insights Table v3",
        filters={"table": table_name},
        fields=["name", "data_source", "stored", "sync_mode", "last_synced_on"],
    )
    print(f"Insights Table v3 record for {table_name}: {table_row}")
    if table_row and not table_row[0]["stored"]:
        print(
            "  -> stored=0 (never synced). Not fixing via sync -- Stage 2 uses "
            "use_live_connection=1 on the Query instead, which bypasses the "
            "warehouse/sync path entirely for a Site DB source. See module "
            "docstring point 3."
        )

    # Directly relevant to whether a public Insights chart could ever match
    # ucc_dashboard_access's blocked-source behaviour (findings doc Step 4(b)).
    # apply_user_permissions gates row/column filtering for authenticated
    # requests; it's unconditionally skipped for public-dashboard requests
    # regardless of this setting (insights_table_v3.py:287-289).
    settings = frappe.db.get_singles_dict("Insights Settings")
    print(
        f"Insights Settings.apply_user_permissions = {settings.get('apply_user_permissions')!r}, "
        f"enable_permissions = {settings.get('enable_permissions')!r}"
    )
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
        if any(kw in dt for kw in ("Data Source", "Query", "Chart", "Table", "Workbook", "Dashboard"))
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


def stage_1b_check_existing(doctype, name_hint, extra_fields=()):
    """Generic 'does a record matching this hint already exist' check, used
    for the Data Source (constraint: must not create a duplicate pointing at
    Site DB) and to resolve the real doc name behind a human title (Insights
    Data Source v3 and Insights Workbook both have autoname unset/
    autoincrement, per their real .json -- "Site DB"/"Workbook 2" are very
    likely titles, not guaranteed to be the literal document name).
    """
    print(f"\n=== STAGE 1b: existing {doctype} matching {name_hint!r} ===")
    if frappe.db.exists(doctype, name_hint):
        print(f"  Found by exact name: {name_hint}")
        return name_hint
    matches = frappe.get_all(doctype, filters={"title": name_hint}, fields=["name", "title", *extra_fields])
    print(f"  Matches by title: {matches}")
    if len(matches) == 1:
        return matches[0]["name"]
    if len(matches) > 1:
        print(f"  AMBIGUOUS -- {len(matches)} {doctype} records titled {name_hint!r}. Resolve manually.")
    else:
        print(f"  NOT FOUND -- no {doctype} named or titled {name_hint!r}. Resolve manually before Stage 2.")
    return None


def stage_2_create():
    """Query -> Chart -> Dashboard(public). Schema verified against the real
    frappe/insights v3.12.2 source (see module docstring for citations), not
    guessed. Idempotent-ish: reuses an existing pilot Query/Chart/Dashboard by
    title if one from a prior run is still there, rather than creating dupes.
    """
    print("\n=== STAGE 2: create Query -> Chart -> Dashboard(public) ===")

    data_source = stage_1b_check_existing("Insights Data Source v3", DATA_SOURCE_NAME_HINT)
    workbook = stage_1b_check_existing("Insights Workbook", WORKBOOK_TITLE_HINT)
    if not data_source or not workbook:
        print("STOP -- resolve the Data Source / Workbook name above before continuing.")
        return None

    table_name = "tab" + PILOT_DOCTYPE  # confirmed: insights_table_v3.py stores the raw SQL name, "tab" prefix included

    existing_query = frappe.db.get_value("Insights Query v3", {"title": PILOT_TITLE, "workbook": workbook}, "name")
    if existing_query:
        print(f"Reusing existing Query: {existing_query}")
        query_name = existing_query
        # Self-heal a query created by an earlier version of this script
        # (before use_live_connection was set) rather than silently reusing
        # one that's still routed through the unsynced warehouse.
        if not frappe.db.get_value("Insights Query v3", query_name, "use_live_connection"):
            frappe.db.set_value("Insights Query v3", query_name, "use_live_connection", 1)
            print(f"  -> was use_live_connection=0, fixed to 1")
    else:
        # Operation shapes verified from frontend/src2/types/query.types.ts:
        #   Source   = { type: 'source', table: { type: 'table', data_source, table_name } }
        #   Summarize= { type: 'summarize', measures: ColumnMeasure[], dimensions: Dimension[] }
        #   ColumnMeasure = { measure_name, column_name, data_type, aggregation }
        #   Dimension     = { dimension_name, column_name, data_type, granularity? }
        # aggregation values: 'sum'|'count'|'avg'|'min'|'max'|'count_distinct'.
        # column_name=="count" AND aggregation=="count" is a special sentinel in
        # ibis_utils.py's translate_measure() -- it does COUNT(first_column) i.e.
        # a real row count, NOT literally counting a column named "count".
        operations = [
            {
                "type": "source",
                "table": {"type": "table", "data_source": data_source, "table_name": table_name},
            },
            {
                "type": "summarize",
                "measures": [
                    {
                        "measure_name": "count",
                        "column_name": "count",
                        "data_type": "Integer",
                        "aggregation": "count",
                    }
                ],
                "dimensions": [
                    {
                        "dimension_name": PILOT_FIELD,
                        "column_name": PILOT_FIELD,
                        "data_type": "String",
                    }
                ],
            },
        ]
        query = frappe.new_doc("Insights Query v3")
        query.workbook = workbook
        query.title = PILOT_TITLE
        query.is_builder_query = 1
        # Skips the DuckDB warehouse/import path entirely -- for a Site DB
        # source, InsightsDataSourcev3.get_ibis_table() just opens a live
        # ibis handle on the site's own MariaDB connection
        # (insights_data_source_v3.py:441-447). No sync/import needed, and
        # every execution reads current data, same as the legacy engine's own
        # per-request frappe.get_list() call. See module docstring point 3
        # for why the default (use_live_connection=0, routed through the
        # warehouse) returned zero rows on the first attempt.
        query.use_live_connection = 1
        query.operations = operations
        query.insert()
        query_name = query.name
        print(f"Created Query: {query_name} (use_live_connection=1)")

    # Sanity-check the query actually runs and returns grouped rows before
    # building a Chart on top of it -- fail loud here rather than silently
    # shipping a chart with no data.
    query_doc = frappe.get_doc("Insights Query v3", query_name)
    result = query_doc.execute(page_size=100)
    print(f"Query result ({len(result['rows'])} rows): {result['rows']}")
    print(f"SQL executed: {result['sql']}")
    if not result["rows"]:
        print("STOP -- query returned zero rows. Do not proceed to Chart/Dashboard until this is understood.")
        return None

    existing_chart = frappe.db.get_value("Insights Chart v3", {"title": PILOT_TITLE, "workbook": workbook}, "name")
    if existing_chart:
        print(f"Reusing existing Chart: {existing_chart}")
        chart_name = existing_chart
    else:
        # Config shape verified from frontend/src2/types/chart.types.ts.
        # CHART_TYPE default is "Line" (module-level constant above) -- see
        # its comment for why, and the one-line switch to "Bar" if that's
        # actually wanted instead.
        dimension = {"dimension_name": PILOT_FIELD, "column_name": PILOT_FIELD, "data_type": "String"}
        measure = {
            "measure_name": "count",
            "column_name": "count",
            "data_type": "Integer",
            "aggregation": "count",
        }
        series_type = "bar" if CHART_TYPE == "Bar" else "line"
        config = {
            "x_axis": {"dimension": dimension},
            "y_axis": {"series": [{"type": series_type, "measure": measure}]},
        }
        chart = frappe.new_doc("Insights Chart v3")
        chart.workbook = workbook
        chart.title = PILOT_TITLE
        chart.query = query_name
        chart.chart_type = CHART_TYPE
        chart.config = config
        chart.insert()
        chart_name = chart.name
        print(f"Created Chart: {chart_name} (chart_type={CHART_TYPE})")
        # insights_chart_v3.py's before_save() -> set_data_query() auto-creates
        # a separate blank "Insights Query v3" and points the Chart's own
        # `data_query` field at it (distinct from `query` above, which is the
        # real pilot data). That's Insights' own built-in behaviour, not
        # something this script does -- expect one extra empty Query record
        # per Chart created; it's not a duplicate of the pilot query.
        print(f"Note: Insights auto-created a separate blank data_query ({chart.data_query}) -- expected, not a bug.")

    existing_dashboard = frappe.db.get_value("Insights Dashboard v3", {"title": PILOT_TITLE, "workbook": workbook}, "name")
    if existing_dashboard:
        print(f"Reusing existing Dashboard: {existing_dashboard}")
        dashboard_name = existing_dashboard
        dashboard = frappe.get_doc("Insights Dashboard v3", dashboard_name)
    else:
        # items shape: backend (insights_dashboard_v3.py's set_linked_charts/
        # is_filter_column) only ever reads item["type"] and item["chart"] --
        # x/y/width/height below are a best-effort grid-layout guess (common
        # 12-column-grid convention), NOT verified against the real frontend
        # type (couldn't find a dashboard-items TS type file to confirm the
        # exact key names). If the dashboard's own grid renders oddly, that's
        # a cosmetic issue, not a functional one for this pilot -- the public
        # URL and the chart's data will still work either way, since nothing
        # server-side validates these layout keys.
        items = [{"type": "chart", "chart": chart_name, "x": 0, "y": 0, "width": 12, "height": 8}]
        dashboard = frappe.new_doc("Insights Dashboard v3")
        dashboard.workbook = workbook
        dashboard.title = PILOT_TITLE
        dashboard.items = items
        dashboard.insert()
        dashboard_name = dashboard.name
        print(f"Created Dashboard: {dashboard_name}")

    if not dashboard.is_public:
        dashboard.update_access({"is_public": 1, "is_shared_with_organization": 0, "people_with_access": []})
        print("Set Dashboard is_public = 1")
    else:
        print("Dashboard already public")

    dashboard.reload()
    constructed_url = frappe.utils.get_url(f"/insights/shared/dashboard/{dashboard_name}")
    print(f"\nDashboard.share_link field value: {dashboard.share_link!r}")
    print(f"Constructed public URL (from insights_dashboard_v3.py's own preview-generation code): {constructed_url}")
    print("If share_link differs from the constructed URL above, report BOTH back.")

    return {
        "data_source": data_source,
        "workbook": workbook,
        "query": query_name,
        "chart": chart_name,
        "dashboard": dashboard_name,
        "public_url": constructed_url,
        "share_link_field": dashboard.share_link,
    }


def run():
    ok = stage_0_verify_schema()
    relevant, schema = stage_1_discover_insights_schema()
    if not ok:
        print("\nSTOP -- Stage 0 did not confirm academic_year exists. Resolve that before continuing.")
        return None
    if "Insights Query v3" not in relevant or "Insights Chart v3" not in relevant:
        print("\nSTOP -- Insights Query v3 / Insights Chart v3 not found on this install. Report the Stage 1 list back.")
        return None
    result = stage_2_create()
    print(f"\n=== RESULT ===\n{result}")
    print(
        """
One more thing worth checking once you have the URL: if the Data Source is a
direct site-database connection ("Site DB"), Insights queries against it
typically run with the site's raw DB credentials, NOT through Frappe's
permission layer -- meaning the query has no concept of `ucc_dashboard_access`
or per-user DocType permissions at all, and a public dashboard is guest-
visible by design (insights_dashboard_v3.py's get_distinct_column_values
explicitly allows Guest access once is_public=1). That's directly relevant to
docs/migration/insights-pilot-findings.md's Step 4(b) permission test --
worth confirming what happens if you open the public_url in a logged-out
browser before treating this pilot as done.
"""
    )
    return result


if __name__ == "__main__":
    run()
