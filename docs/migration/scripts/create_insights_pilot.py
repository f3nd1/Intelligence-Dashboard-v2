"""Create the Frappe Insights pilot Data Source / Query / Chart for the
Analytics-Insights feasibility spike (docs/migration/insights-pilot-findings.md).

Written by a repo-only Claude Code session with no bench/site access. Insights
isn't vendored in this repo, so its v3.12.2 schema was verified by reading the
real, unabridged source at https://github.com/frappe/insights (tag v3.12.2) --
not guessed from older Insights docs or training data. File:line citations
are in the docstrings below. Worth knowing before running this:

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
4. Dashboard `items` shape: the real `WorkbookDashboardChart` type
   (`frontend/src2/types/workbook.types.ts:131-142`,
   `frontend/src2/dashboard/dashboard.ts:62-71`) nests grid position under a
   `layout` key (`{"i": <unique str>, "x", "y", "w", "h"}`) and requires that
   unique `i` -- not flat `x/y/width/height` with no wrapper, which is what
   an earlier version of this script guessed and which is malformed enough
   to break the frontend's chart resolution (404 on `insights.api.get_doc`
   for the chart, even as Administrator). Fixed below; also now verifies
   `Dashboard.linked_charts` (the auto-derived `Insights Dashboard Chart v3`
   child table that `insights/api/shared.py`'s `get_public_charts()` actually
   queries for guest chart access) contains the chart, not just that `items`
   looks right.
5. **If you're pasting this into an interactive `bench console` session,
   the writes below will not survive you closing that session unless
   something commits them.** Confirmed in Frappe's own source
   (`frappe/commands/utils.py:_console_cleanup`, registered via `atexit`):
   closing a console session calls `frappe.db.rollback()` explicitly, by
   design. Without a commit, every record this script creates lives only
   inside that session's open transaction -- reads from that *same* session
   (including this script's own verification checks) see it fine, which is
   exactly why a prior run could show every check passing and then have both
   the Chart and the Dashboard 404 moments later from a real browser request
   (a different DB connection, same as any other Frappe web worker). Fixed
   by committing at each milestone below rather than trusting the session to
   stay open. If you're instead running this via
   `bench --site <site> execute <path>.run` (a single process that exits
   after `run()` returns), this isn't a concern the same way, but the
   explicit commits are harmless either way.
6. **`--site ucc-sms-v2` (what every instruction up to this point, including
   this file's own examples, used) is very possibly the WRONG site name.**
   After the commit fix still didn't resolve persistence, a `bench execute`
   check using `--site ucc-sms-v2.orb.local` instead found records that a
   raw-SQL check against (presumably) plain `ucc-sms-v2` could not. If this
   bench has two separate site folders under `sites/` -- `ucc-sms-v2` and
   `ucc-sms-v2.orb.local` -- every prior run of this script (pasted into a
   console opened with bare `ucc-sms-v2`) would have written real, committed
   rows into the *empty* `ucc-sms-v2` site, while the browser -- almost
   certainly resolving whatever `*.orb.local` hostname it's actually being
   accessed through -- reads from `ucc-sms-v2.orb.local` instead. That would
   explain every single symptom so far without needing anything wrong in
   `insights.api.get_doc` or the web layer at all: commits genuinely work,
   the row genuinely persists, it's just in the wrong site's database the
   whole time. Confirm with `ls sites/` from the bench root before assuming
   this is it, then always invoke `bench --site <name>` with whatever that
   listing actually shows -- this docstring no longer hardcodes one, and
   Stage 3 below prints `frappe.local.site` (the live, unambiguous truth for
   whatever session you're actually in) rather than assuming a name.

Usage: paste this whole file into `bench --site <your-site-name> console` --
confirm the exact site name with `ls sites/` first if there's any doubt
which one is correct (see point 6 above).

Run STAGE 0 and STAGE 1 first (read-only, safe, fast) -- they cross-check
this specific install against what was verified from GitHub, since a local
install can differ (patches, customisations, a slightly different point
release). If either turns up something unexpected, STOP and report back
before Stage 2 rather than pushing through with a mismatch.
"""

import os
import shutil
import subprocess

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


def raw_sql_row_exists(doctype, name):
    """Bypass Frappe's Python DB layer entirely -- shell out to a genuinely
    separate mysql/mariadb CLI process, the same way `bench --site <name>
    mariadb` does (frappe/database/__init__.py:96-136's get_command: tries
    the "mariadb" binary before falling back to "mysql", reads connection
    details from frappe.conf -- so this always targets whatever site THIS
    running script is actually connected to, never a hardcoded name) --
    and ask it directly
    whether a row exists. This is the same class of check already confirmed
    by hand via raw SQL (table verified empty); running it from inside this
    script, right after each frappe.db.commit() call, pinpoints exactly
    which commit (if any) the row fails to survive, rather than only being
    able to check well after the fact in a separate session.

    Uses MYSQL_PWD (an env var passed only to this one subprocess) rather
    than a --password= CLI arg, so the password never appears in `ps aux` --
    a small improvement over bench mariadb's own approach, not a security
    problem with it. Never logs the password itself.
    """
    binary = shutil.which("mariadb") or shutil.which("mysql")
    if not binary:
        return "NO_CLIENT_FOUND (neither mariadb nor mysql binary on PATH)"
    table = "tab" + doctype
    escaped_name = name.replace("'", "''")
    sql = f"SELECT COUNT(*) FROM `{table}` WHERE name = '{escaped_name}'"
    args = [binary, f"--user={frappe.conf.db_name}"]
    if frappe.conf.get("db_socket"):
        args.append(f"--socket={frappe.conf.db_socket}")
    elif frappe.conf.get("db_host"):
        args.append(f"--host={frappe.conf.db_host}")
        if frappe.conf.get("db_port"):
            args.append(f"--port={frappe.conf.db_port}")
    args += [frappe.conf.db_name, "--skip-column-names", "-e", sql]
    env = dict(os.environ)
    if frappe.conf.get("db_password"):
        env["MYSQL_PWD"] = frappe.conf.db_password
    try:
        result = subprocess.run(args, capture_output=True, text=True, env=env, timeout=15)
        if result.returncode != 0:
            return f"CLI_ERROR: {result.stderr.strip()[:300]}"
        return result.stdout.strip()
    except Exception as e:
        return f"EXCEPTION: {e}"


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

    # bench console does NOT auto-commit between statements, and its own
    # exit handler explicitly ROLLS BACK anything uncommitted
    # (frappe/commands/utils.py:_console_cleanup -> frappe.db.rollback()) --
    # confirmed in Frappe's own source, not Insights'. Without an explicit
    # commit, every record this script creates is only visible within this
    # same console session (which is why the script's own verification
    # checks below can pass) and disappears the moment the session closes,
    # even though nothing here ever errored. Commit at each milestone rather
    # than only at the very end, so a later STOP still preserves whatever
    # succeeded so far instead of losing all of it to the same rollback.
    frappe.db.commit()
    print("Committed (Query).")
    print(f"Raw-SQL (separate mysql process) row count for Query {query_name!r}: {raw_sql_row_exists('Insights Query v3', query_name)}")

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

    frappe.db.commit()
    print("Committed (Chart).")
    print(f"Raw-SQL (separate mysql process) row count for Chart {chart_name!r}: {raw_sql_row_exists('Insights Chart v3', chart_name)}")
    print(f"Raw-SQL (separate mysql process) row count for Query {query_name!r} (re-check after Chart commit): {raw_sql_row_exists('Insights Query v3', query_name)}")

    # items shape verified from frontend/src2/dashboard/dashboard.ts:62-71 and
    # frontend/src2/types/workbook.types.ts:131-142 (Layout / WorkbookDashboardChart)
    # -- the previous version of this script had this WRONG: flat x/y/width/
    # height keys and no "layout" wrapper, and no "i" (unique widget id) at
    # all. That's very likely why the chart never rendered (404 on
    # insights.api.get_doc even as Administrator, reported after the first
    # run): VueGridLayout needs a stable per-item "i" and the real key names
    # are w/h nested under layout, not width/height at the top level. Real
    # shape: {"type": "chart", "chart": <name>, "layout": {"i": <unique str>,
    # "x", "y", "w", "h"}}.
    chart_layout_item = {
        "type": "chart",
        "chart": chart_name,
        "layout": {"i": "pilot-chart-1", "x": 0, "y": 0, "w": 10, "h": 8},
    }

    existing_dashboard = frappe.db.get_value("Insights Dashboard v3", {"title": PILOT_TITLE, "workbook": workbook}, "name")
    if existing_dashboard:
        print(f"Reusing existing Dashboard: {existing_dashboard}")
        dashboard_name = existing_dashboard
        dashboard = frappe.get_doc("Insights Dashboard v3", dashboard_name)
        # Self-heal: always recompute items from the CURRENT chart_name and
        # correct shape, rather than trusting whatever was stored by an
        # earlier (possibly wrong-shaped, or now-stale-chart-referencing) run.
        current_items = frappe.parse_json(dashboard.items) or []
        if current_items != [chart_layout_item]:
            print(f"  -> stored items differ from expected, correcting: {current_items} -> {[chart_layout_item]}")
            dashboard.items = [chart_layout_item]
            dashboard.save()
    else:
        dashboard = frappe.new_doc("Insights Dashboard v3")
        dashboard.workbook = workbook
        dashboard.title = PILOT_TITLE
        dashboard.items = [chart_layout_item]
        dashboard.insert()
        dashboard_name = dashboard.name
        print(f"Created Dashboard: {dashboard_name}")

    frappe.db.commit()
    print("Committed (Dashboard + items).")
    print(f"Raw-SQL (separate mysql process) row count for Dashboard {dashboard_name!r}: {raw_sql_row_exists('Insights Dashboard v3', dashboard_name)}")
    print(f"Raw-SQL (separate mysql process) row count for Chart {chart_name!r} (re-check after Dashboard commit): {raw_sql_row_exists('Insights Chart v3', chart_name)}")

    # Verify the wiring server-side the same way insights.api.get_doc would
    # for a real viewer, instead of trusting the write succeeded silently --
    # this is exactly the check that would have caught the previous bug
    # before it reached the browser.
    dashboard.reload()
    stored_items = frappe.parse_json(dashboard.items) or []
    print(f"Dashboard.items after save: {stored_items}")
    linked_chart_names = [i["chart"] for i in stored_items if i.get("type") == "chart"]
    if chart_name not in linked_chart_names:
        print(f"STOP -- chart_name {chart_name!r} not found in dashboard.items {stored_items!r} after save.")
        return None
    try:
        frappe.get_doc("Insights Chart v3", chart_name)
        print(f"Verified: Insights Chart v3 {chart_name!r} resolves via frappe.get_doc (mirrors insights.api.get_doc's direct-fetch path).")
    except frappe.DoesNotExistError:
        print(f"STOP -- Insights Chart v3 {chart_name!r} does not exist via frappe.get_doc. This would 404 for every viewer, admin included.")
        return None
    # linked_charts (Insights Dashboard Chart v3 child table) is what
    # get_public_charts() in insights/api/shared.py actually queries to decide
    # guest access to an individual chart record -- it's auto-derived from
    # items by set_linked_charts() on every save, but confirm it actually took.
    linked_charts_child_table = [d.chart for d in dashboard.linked_charts]
    print(f"Dashboard.linked_charts (child table, drives guest chart-fetch access): {linked_charts_child_table}")
    if chart_name not in linked_charts_child_table:
        print(f"STOP -- {chart_name!r} not in linked_charts child table -- guest access to this chart's record would still fail even though items looks right.")
        return None

    if not dashboard.is_public:
        dashboard.update_access({"is_public": 1, "is_shared_with_organization": 0, "people_with_access": []})
        print("Set Dashboard is_public = 1")
    else:
        print("Dashboard already public")

    frappe.db.commit()
    print("Committed (is_public).")
    print(f"Raw-SQL (separate mysql process) FINAL row count for Dashboard {dashboard_name!r}: {raw_sql_row_exists('Insights Dashboard v3', dashboard_name)}")
    print(f"Raw-SQL (separate mysql process) FINAL row count for Chart {chart_name!r}: {raw_sql_row_exists('Insights Chart v3', chart_name)}")
    print(
        "If any of the raw-SQL counts printed above ever show 1 and a LATER "
        "one for the same record shows 0, that pinpoints exactly which "
        "commit() the row failed to survive past -- something between those "
        "two points is reverting it. If EVERY raw-SQL count is 0 from the "
        "very first check onward, the row never reached the table at all, "
        "even within this same process -- which would mean frappe.db.commit() "
        "is not actually persisting inserts issued via Document.insert() on "
        "this install, a much stranger finding worth its own investigation "
        "(a customised hook, a monkey-patched db_insert, or a non-standard "
        "commit/connection setup) rather than another guess from here."
    )

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


def stage_3_diagnose_persistence(result):
    """The commit fix (frappe.db.commit() at each milestone in stage_2_create)
    didn't resolve the 404s on a prior run -- confirmed frappe.db.commit()
    itself is a real SQL COMMIT (frappe/database/database.py:1173-1184, not
    guessed), and the RESULT dict being fully populated means the code path
    that calls commit() did run. That rules out "commit is a no-op in
    console" but does NOT prove these records are visible outside this
    session -- print exactly what's needed to settle that, in this session,
    right now, per Felix's own diagnostic question.
    """
    if not result:
        return
    print("\n=== STAGE 3: persistence diagnostics ===")
    print(f"This console session's site: {frappe.local.site!r}")
    print(f"This console session's db_name (frappe.conf): {frappe.conf.get('db_name')!r}")
    print(f"This console session's actual connected database: {frappe.db.sql('select database()')[0][0]!r}")
    same_session_dashboard = frappe.db.exists("Insights Dashboard v3", result["dashboard"])
    same_session_chart = frappe.db.exists("Insights Chart v3", result["chart"])
    print(f"frappe.db.exists('Insights Dashboard v3', {result['dashboard']!r}) in THIS session: {same_session_dashboard}")
    print(f"frappe.db.exists('Insights Chart v3', {result['chart']!r}) in THIS session: {same_session_chart}")
    print(
        f"""
If both came back True just now: this session's transaction has the records
committed. The decisive next test is from a COMPLETELY SEPARATE process --
not this console session, not even a new console session started from the
same shell without exiting this one first (exiting THIS one is exactly what
triggers _console_cleanup's rollback, so don't exit yet). From a fresh
terminal, run:

    bench --site {frappe.local.site} execute frappe.db.exists --args '["Insights Dashboard v3", "{result['dashboard']}"]'
    bench --site {frappe.local.site} execute frappe.db.exists --args '["Insights Chart v3", "{result['chart']}"]'

`bench execute` inits a brand-new site connection per invocation
(frappe/commands/utils.py:execute -> frappe.init+frappe.connect), the same
way a real web worker does -- if THIS returns True but your browser's
insights.api.get_doc still 404s, the records are genuinely persisted and the
bug is somewhere in the web/API layer (site routing for the domain you're
browsing, a permission check, something in insights.api.get_doc itself) --
not a database transaction issue anymore, and worth reporting back so I can
dig into that layer specifically rather than the database layer again. If
`bench execute` ALSO returns False, that's decisive the other way -- still a
persistence problem, and worth re-checking whether the site name really
matches everywhere (this session reported {frappe.local.site!r} above --
confirm that's the exact site name your browser is actually pointed at).
"""
    )


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
    stage_3_diagnose_persistence(result)
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
