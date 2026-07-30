"""Create ONE more Insights Query v3 / Chart v3 record for Criterion 4's
admission_intelligence (Option B: Sophia embeds live Insights queries
directly, confirmed with Felix after the real permission test in
test_insights_private_permissions.py proved private query execution
respects real per-user Frappe permissions -- 0 rows restricted, 6 rows
with real access, on the actual bench).

**Scoped down deliberately, 2026-07-29**: rather than building and
self-QA'ing all 6 series in one pass, this round builds just ONE more --
`enrolled_by_year` -- alongside the already-proven `applicants_by_year`,
so the pattern can be reviewed live on the real page before committing to
the other 4. `applicants_by_country`, `programmes`, `agents`, and
`counselling_to_admission` are deliberately NOT built by this run (their
verified operation specs are still defined below, in DEFERRED_SERIES /
build_counselling_duration, just not called from run() yet) -- picking
this back up later is a one-line change (move a spec from
DEFERRED_SERIES to ACTIVE_SERIES, or add the build_counselling_duration()
call back into run()), not a rewrite.

`enrolled_by_year` was chosen as "one more" because it's the lowest-risk
of the remaining 5: same table and the SAME already-verified
`academic_year` field as `applicants_by_year` (62 rows, 0 blank,
confirmed on this bench by the earlier pilot), plus one `filter` operation
(verified against real Insights source, see below) -- nothing depends on
a field candidate that hasn't been checked against this site's live
schema yet, unlike the other 4.

The runtime module (admission_intelligence_embed.py) and the frontend
wiring already tolerate a partial build gracefully -- a chart whose Query
v3 record doesn't exist yet reports `status: "unavailable"` and renders
the existing generic empty state, not an error and not a permission
notice. No code changes were needed there for this scope-down; only this
script's ACTIVE_SERIES list changed.

`applicants_by_year` already exists and is proven (the original pilot
chart, title "Sophia Pilot - Student Applicants per Year", dataKey
applicants_by_year) -- this script does NOT recreate it, only verifies it
still resolves and executes, same as everything else here.

Field candidates for each series are taken directly from
ucc_intelligence/ucc_intelligence/analytics/criterion_4.py's
build_admission_intelligence()/build_counselling_duration_chart() --
that's the source of truth for what each chart needs to compute, per the
task. Unlike that Python engine, an Insights Query's operations JSON
needs ONE fixed field name chosen at authoring time, not a runtime
candidate list -- so this script discovers the real field live against
THIS site's schema (frappe.get_meta) before building each query, the same
verify-before-build discipline create_insights_pilot.py's Stage 0 used for
academic_year, rather than guessing which candidate is real.

Operation shapes (source/summarize were already proven by the pilot;
filter/join/mutate are new for this script) verified by reading the real,
unabridged Insights v3.12.2 source directly -- not guessed:
- filter: insights_data_source_v3/ibis_utils.py's IbisQueryBuilder.apply_filter
  -> make_filter_condition: {"type":"filter","column":{"column_name":...},
  "operator":"=", "value":...}. Operators are literal symbols confirmed from
  get_operator's dict: "=", "!=", ">", "<", ">=", "<=", "in", "not_in",
  "is_set", "is_not_set", "contains", "not_contains", "starts_with",
  "ends_with", "between", "within".
- join: apply_join/get_right_table/translate_join_condition, confirmed:
  {"type":"join","join_type":"inner"|"left"|"right"|"full",
  "table":{"type":"table","data_source":...,"table_name":...},
  "join_condition":{"left_column":{"column_name":...},
  "right_column":{"column_name":...}}, "select_columns":[{"column_name":...}]}.
  left_column is a column on the query built so far (the "source" table),
  right_column is a column on the joined-in table.
- mutate (counselling_to_admission's day-count only): apply_mutate ->
  evaluate_expression, confirmed to exec() a Python-like expression string
  against a context where every current column name is bound directly to
  its ibis column expression. The exact date-difference helper inside
  get_functions() (a separate file, insights_data_source_v3/ibis/utils.py,
  not fetched this round -- diminishing returns past a certain point of
  verification) was NOT independently confirmed, so this uses ibis's own
  documented TemporalColumn.delta(other, unit) method directly instead of
  assuming an Insights-specific helper exists. This is the one operation
  in this whole script built on general ibis API knowledge rather than
  Insights-source-confirmed usage -- flagged loudly here and again at its
  call site below. STAGE 3's execute() check will surface a clear Python
  exception immediately if this is wrong; it will not silently return
  wrong data, so treat a Stage 3 failure on this one query as informative,
  not alarming, and report the exact error back.

Usage -- paste into `bench --site <your-site> console` (confirm the real
site name via `ls sites/` first, same as every script tonight):

    exec(open("docs/migration/scripts/build_admission_intelligence_embed.py").read(), globals())

The trailing `globals()` argument matters -- bare `exec(open(...).read())`
(no explicit globals/locals) inherits whatever globals()/locals() are
active at ITS OWN call site, and if bench console evaluates pasted input
from inside some internal method (globals() != locals() there), every
top-level `def` in this file gets written to that call's locals dict while
still capturing that call's globals dict as its own __globals__ -- so
`run()` (and any other function here) calling a sibling top-level function
resolves it via LOAD_GLOBAL against __globals__, which never got it,
raising exactly `NameError: name '...' is not defined` for whichever
cross-function call happens first. Confirmed by reproducing this exact
failure locally with a stub frappe module, and confirmed it goes away with
`exec(source, globals())`, which forces a single shared namespace instead
of a silent two-dict split -- not just theorized. Passing `globals()`
explicitly costs nothing when this isn't the issue and fixes it outright
when it is.

Runs STAGE 1 (create/reuse) through STAGE 4 (restricted-permission test on
the one new chart) automatically. Each STAGE prints its own pass/fail.
"""

import frappe
import frappe.share

DATA_SOURCE_NAME_HINT = "Site DB"
WORKBOOK_TITLE_HINT = "Workbook 2"

APPLICANT_DOCTYPE = "Student Applicant"
ADMISSION_DOCTYPE = "Student Admission UCC"

EXISTING_APPLICANTS_BY_YEAR_TITLE = "Sophia Pilot - Student Applicants per Year"

# Must stay in sync with the CHART_TITLES dict in
# ucc_intelligence/ucc_intelligence/analytics/admission_intelligence_embed.py --
# both hardcode the same 6 titles because a bench-console script and the
# installed app module can't share Python state at runtime. Six short
# strings duplicated once is simpler than shared config infra for it.
CHART_TITLES = {
	"applicants_by_year": EXISTING_APPLICANTS_BY_YEAR_TITLE,
	"enrolled_by_year": "Sophia AI - Enrolled Students per Year",
	"applicants_by_country": "Sophia AI - Applicants per Country",
	"programmes": "Sophia AI - Popular Courses of Full Qualification",
	"agents": "Sophia AI - Number of Students per Agent",
	"counselling_to_admission": "Sophia AI - Counselling to Admission Duration",
}

# From criterion_4.py's build_admission_intelligence() field-candidate lists.
# ACTIVE_SERIES is built by this run; DEFERRED_SERIES is kept (specs already
# verified against real Insights operation shapes) but NOT called from run()
# -- see the module docstring's "Scoped down deliberately" note. Moving one
# back into ACTIVE_SERIES later is the only change needed to resume.
ACTIVE_SERIES = [
	{
		"data_key": "enrolled_by_year",
		"doctype": APPLICANT_DOCTYPE,
		"dimension_candidates": ["academic_year"],
		"filter_field_candidates": None,  # academic_year already verified by the pilot; used as literal here
		"filter": {"column": "application_status", "operator": "=", "value": "Admitted"},
		"chart_type": "Line",
	},
]

DEFERRED_SERIES = [
	{
		"data_key": "applicants_by_country",
		"doctype": APPLICANT_DOCTYPE,
		"dimension_candidates": ["nationality", "country"],
		"filter": None,
		"chart_type": "Bar",
	},
	{
		"data_key": "programmes",
		"doctype": APPLICANT_DOCTYPE,
		"dimension_candidates": ["program", "course", "course_applying_for"],
		"filter": None,
		"chart_type": "Bar",
	},
	{
		"data_key": "agents",
		"doctype": APPLICANT_DOCTYPE,
		"dimension_candidates": ["agent", "custom_agent", "recruitment_agent"],
		"filter": None,
		"chart_type": "Bar",
	},
]

results = {}


def resolve_field_live(doctype, candidates):
	meta = frappe.get_meta(doctype)
	for fieldname in candidates:
		if meta.has_field(fieldname):
			return fieldname
	return None


def stage_1b_check_existing(doctype, name_hint):
	if frappe.db.exists(doctype, name_hint):
		return name_hint
	matches = frappe.get_all(doctype, filters={"title": name_hint}, fields=["name"])
	if len(matches) == 1:
		return matches[0]["name"]
	if len(matches) > 1:
		print("  AMBIGUOUS -- %d %s records titled %r. Resolve manually." % (len(matches), doctype, name_hint))
	else:
		print("  NOT FOUND -- no %s named or titled %r." % (doctype, name_hint))
	return None


def get_or_create_query(title, workbook, operations, use_live_connection=1):
	existing = frappe.db.get_value("Insights Query v3", {"title": title, "workbook": workbook}, "name")
	if existing:
		print("  Reusing existing Query: %s" % existing)
		if not frappe.db.get_value("Insights Query v3", existing, "use_live_connection"):
			frappe.db.set_value("Insights Query v3", existing, "use_live_connection", 1)
			print("  -> was use_live_connection=0, fixed to 1")
		return existing
	query = frappe.new_doc("Insights Query v3")
	query.workbook = workbook
	query.title = title
	query.is_builder_query = 1
	query.use_live_connection = use_live_connection
	query.operations = operations
	query.insert()
	frappe.db.commit()
	print("  Created Query: %s" % query.name)
	return query.name


def get_or_create_chart(title, workbook, query_name, chart_type, dimension, measure):
	existing = frappe.db.get_value("Insights Chart v3", {"title": title, "workbook": workbook}, "name")
	if existing:
		print("  Reusing existing Chart: %s" % existing)
		return existing
	series_type = "bar" if chart_type == "Bar" else "line"
	config = {
		"x_axis": {"dimension": dimension},
		"y_axis": {"series": [{"type": series_type, "measure": measure}]},
	}
	chart = frappe.new_doc("Insights Chart v3")
	chart.workbook = workbook
	chart.title = title
	chart.query = query_name
	chart.chart_type = chart_type
	chart.config = config
	chart.insert()
	frappe.db.commit()
	print("  Created Chart: %s" % chart.name)
	return chart.name


def build_simple_series(spec, data_source, workbook):
	data_key = spec["data_key"]
	title = CHART_TITLES[data_key]
	print("\n=== %s (%s) ===" % (data_key, title))

	dimension_field = resolve_field_live(spec["doctype"], spec["dimension_candidates"])
	if not dimension_field:
		print("  SKIP -- none of %r exist on %s (live schema check)." % (spec["dimension_candidates"], spec["doctype"]))
		results[data_key] = {"status": "skipped_no_field"}
		return

	table_name = "tab" + spec["doctype"]
	operations = [
		{"type": "source", "table": {"type": "table", "data_source": data_source, "table_name": table_name}},
	]
	if spec.get("filter"):
		f = spec["filter"]
		field_meta = frappe.get_meta(spec["doctype"])
		if not field_meta.has_field(f["column"]):
			print("  SKIP -- filter column %r does not exist on %s." % (f["column"], spec["doctype"]))
			results[data_key] = {"status": "skipped_no_filter_field"}
			return
		operations.append({
			"type": "filter",
			"column": {"column_name": f["column"]},
			"operator": f["operator"],
			"value": f["value"],
		})
	operations.append({
		"type": "summarize",
		"measures": [{"measure_name": "count", "column_name": "count", "data_type": "Integer", "aggregation": "count"}],
		"dimensions": [{"dimension_name": dimension_field, "column_name": dimension_field, "data_type": "String"}],
	})

	query_name = get_or_create_query(title, workbook, operations)
	dimension = {"dimension_name": dimension_field, "column_name": dimension_field, "data_type": "String"}
	measure = {"measure_name": "count", "column_name": "count", "data_type": "Integer", "aggregation": "count"}
	chart_name = get_or_create_chart(title, workbook, query_name, spec["chart_type"], dimension, measure)
	results[data_key] = {"status": "created_or_reused", "query": query_name, "chart": chart_name}


def build_counselling_duration(data_source, workbook):
	data_key = "counselling_to_admission"
	title = CHART_TITLES[data_key]
	print("\n=== %s (%s) ===" % (data_key, title))

	counselling_field = resolve_field_live(ADMISSION_DOCTYPE, ["pre_course_counseling"])
	signed_field = resolve_field_live(ADMISSION_DOCTYPE, ["student_signed_date", "contract_signed_by_student_date"])
	applicant_link_field = resolve_field_live(ADMISSION_DOCTYPE, ["student_applicant"])
	docstatus_field = resolve_field_live(ADMISSION_DOCTYPE, ["docstatus"])
	applicant_year_field = resolve_field_live(APPLICANT_DOCTYPE, ["academic_year"])
	admission_own_year_field = resolve_field_live(ADMISSION_DOCTYPE, ["academic_year"])

	print("  Fields: counselling=%r signed=%r applicant_link=%r docstatus=%r applicant.academic_year=%r" % (
		counselling_field, signed_field, applicant_link_field, docstatus_field, applicant_year_field))
	if admission_own_year_field:
		print("  NOTE: %s also has its own %r field -- if the join below collides on that column "
			"name, Insights' rename_duplicate_columns should disambiguate it automatically, but "
			"this is exactly the kind of edge case Stage 3's execute() check exists to catch "
			"rather than assume away." % (ADMISSION_DOCTYPE, admission_own_year_field))

	if not (counselling_field and signed_field and applicant_link_field and applicant_year_field):
		print("  SKIP -- required fields not found on this site's live schema.")
		results[data_key] = {"status": "skipped_no_field"}
		return

	table_name = "tab" + ADMISSION_DOCTYPE
	applicant_table_name = "tab" + APPLICANT_DOCTYPE
	operations = [
		{"type": "source", "table": {"type": "table", "data_source": data_source, "table_name": table_name}},
	]
	if docstatus_field:
		operations.append({
			"type": "filter",
			"column": {"column_name": docstatus_field},
			"operator": "=",
			"value": 1,
		})
	operations.append({
		"type": "join",
		"join_type": "inner",
		"table": {"type": "table", "data_source": data_source, "table_name": applicant_table_name},
		"join_condition": {
			"left_column": {"column_name": applicant_link_field},
			"right_column": {"column_name": "name"},
		},
		"select_columns": [{"column_name": applicant_year_field}],
	})
	# Built on ibis's own documented TemporalColumn.delta(other, unit) API, NOT
	# confirmed against Insights' own get_functions() helpers (a separate,
	# unfetched file this round) -- see module docstring. If this specific
	# operation is the one that fails in Stage 3, that's why.
	operations.append({
		"type": "mutate",
		"new_name": "duration_days",
		"data_type": "Integer",
		"expression": {"expression": "%s.delta(%s, 'day')" % (signed_field, counselling_field)},
	})
	operations.append({
		"type": "summarize",
		"measures": [
			{"measure_name": "avg_duration", "column_name": "duration_days", "data_type": "Decimal", "aggregation": "avg"},
			{"measure_name": "count", "column_name": "count", "data_type": "Integer", "aggregation": "count"},
		],
		"dimensions": [{"dimension_name": applicant_year_field, "column_name": applicant_year_field, "data_type": "String"}],
	})

	try:
		query_name = get_or_create_query(title, workbook, operations)
	except Exception as error:
		print("  FAILED to create/save query: %s" % error)
		results[data_key] = {"status": "create_failed", "message": str(error)}
		return

	dimension = {"dimension_name": applicant_year_field, "column_name": applicant_year_field, "data_type": "String"}
	measure = {"measure_name": "avg_duration", "column_name": "duration_days", "data_type": "Decimal", "aggregation": "avg"}
	try:
		chart_name = get_or_create_chart(title, workbook, query_name, "Line", dimension, measure)
		results[data_key] = {"status": "created_or_reused", "query": query_name, "chart": chart_name}
	except Exception as error:
		print("  FAILED to create/save chart: %s" % error)
		results[data_key] = {"status": "chart_create_failed", "query": query_name, "message": str(error)}


def stage_3_verify_execute_as_admin():
	print("\n" + "=" * 70)
	print("STAGE 3 -- Administrator: execute() every one of the 6 queries, real row counts")
	print("=" * 70)
	frappe.set_user("Administrator")
	execute_results = {}
	for data_key, title in CHART_TITLES.items():
		query_name = frappe.db.get_value("Insights Query v3", {"title": title}, "name")
		if not query_name:
			print("%-24s SKIP -- no Query record (see Stage 1/2 output above)" % data_key)
			execute_results[data_key] = {"status": "no_query"}
			continue
		try:
			doc = frappe.get_doc("Insights Query v3", query_name)
			result = doc.execute(page_size=1000)
			row_count = len(result.get("rows") or [])
			print("%-24s PASS -- %d row(s). Sample: %s" % (data_key, row_count, (result["rows"][:2] if result["rows"] else [])))
			execute_results[data_key] = {"status": "pass", "row_count": row_count}
		except Exception as error:
			print("%-24s FAIL -- %s" % (data_key, error))
			execute_results[data_key] = {"status": "fail", "message": str(error)}
	return execute_results


def stage_4_permission_test(execute_results):
	"""Re-run the exact restricted-user / control-user pattern from
	test_insights_private_permissions.py against enrolled_by_year -- the one
	genuinely new Query record this scoped-down round creates -- confirms the
	proven-safe pattern holds for it specifically, not just the original
	pilot chart. Scoped to 1 chart, not 2, to match ACTIVE_SERIES; extend
	this list when more series move out of DEFERRED_SERIES."""
	print("\n" + "=" * 70)
	print("STAGE 4 -- restricted-vs-control permission test on the new chart")
	print("=" * 70)

	candidates = [dk for dk in ("enrolled_by_year",) if execute_results.get(dk, {}).get("status") == "pass"]
	if not candidates:
		print("enrolled_by_year did not execute successfully in Stage 3 -- nothing new to test. Skipping Stage 4.")
		return {}

	test_user_email = "insights-permission-test@ucc-intelligence.local"
	test_role = "Insights Permission Test Role"

	if not frappe.db.exists("Role", test_role):
		role = frappe.new_doc("Role")
		role.role_name = test_role
		role.desk_access = 1
		role.insert(ignore_permissions=True)
	if not frappe.db.exists("User", test_user_email):
		user = frappe.new_doc("User")
		user.email = test_user_email
		user.first_name = "Insights Permission Test"
		user.send_welcome_email = 0
		user.append("roles", {"role": test_role})
		user.insert(ignore_permissions=True)
	frappe.db.commit()

	can_read = frappe.has_permission("Student Applicant", "read", user=test_user_email)
	if can_read:
		print("STOP -- test user unexpectedly has Student Applicant read access. Not a valid test.")
		return {}

	def is_shared(dt, dn, email):
		return any(u.user == email for u in frappe.share.get_users(dt, dn))

	permission_results = {}
	for data_key in candidates:
		title = CHART_TITLES[data_key]
		query_name = frappe.db.get_value("Insights Query v3", {"title": title}, "name")
		print("\n--- %s (query %s) ---" % (data_key, query_name))

		for dt, dn in [("Insights Query v3", query_name)]:
			if not is_shared(dt, dn, test_user_email):
				frappe.share.add(dt, dn, user=test_user_email, read=1)
		frappe.db.commit()

		frappe.set_user(test_user_email)
		try:
			doc = frappe.get_doc("Insights Query v3", query_name)
			doc.check_permission("read")
			result = doc.execute(page_size=1000)
			restricted_rows = len(result.get("rows") or [])
		except Exception as error:
			restricted_rows = "error: %s" % error
		finally:
			frappe.set_user("Administrator")
		print("Restricted user (no Student Applicant access): %s" % restricted_rows)

		if not frappe.db.exists("Has Role", {"parent": test_user_email, "role": "System Manager"}):
			doc = frappe.get_doc("User", test_user_email)
			doc.append("roles", {"role": "System Manager"})
			doc.save(ignore_permissions=True)
			frappe.db.commit()
		frappe.clear_cache(user=test_user_email)

		frappe.set_user(test_user_email)
		try:
			doc = frappe.get_doc("Insights Query v3", query_name)
			doc.check_permission("read")
			result = doc.execute(page_size=1000)
			control_rows = len(result.get("rows") or [])
		except Exception as error:
			control_rows = "error: %s" % error
		finally:
			frappe.set_user("Administrator")
		print("Control (same user, granted System Manager): %s" % control_rows)

		verdict = "GO" if restricted_rows == 0 and isinstance(control_rows, int) and control_rows > 0 else "NEEDS REVIEW"
		print("Verdict for %s: %s" % (data_key, verdict))
		permission_results[data_key] = {"restricted_rows": restricted_rows, "control_rows": control_rows, "verdict": verdict}

	for dt, dn in [("Insights Query v3", frappe.db.get_value("Insights Query v3", {"title": CHART_TITLES[dk]}, "name")) for dk in candidates]:
		if is_shared(dt, dn, test_user_email):
			frappe.share.remove(dt, dn, test_user_email)
	if frappe.db.exists("User", test_user_email):
		frappe.delete_doc("User", test_user_email, ignore_permissions=True, force=True)
	if frappe.db.exists("Role", test_role):
		frappe.delete_doc("Role", test_role, ignore_permissions=True, force=True)
	frappe.db.commit()
	print("\nTest user/role cleaned up.")
	return permission_results


def run():
	print("=" * 70)
	print("STAGE 1 -- resolve Data Source / Workbook, verify existing pilot chart")
	print("=" * 70)
	data_source = stage_1b_check_existing("Insights Data Source v3", DATA_SOURCE_NAME_HINT)
	workbook = stage_1b_check_existing("Insights Workbook", WORKBOOK_TITLE_HINT)
	if not data_source or not workbook:
		print("STOP -- resolve Data Source / Workbook before continuing.")
		return None
	existing_pilot = frappe.db.get_value("Insights Query v3", {"title": EXISTING_APPLICANTS_BY_YEAR_TITLE}, "name")
	if not existing_pilot:
		print("STOP -- the original pilot Query (%r) was not found. Expected it to already exist." % EXISTING_APPLICANTS_BY_YEAR_TITLE)
		return None
	print("Existing applicants_by_year Query confirmed: %s" % existing_pilot)
	results["applicants_by_year"] = {"status": "already_existed", "query": existing_pilot}

	settings = frappe.db.get_singles_dict("Insights Settings")
	print("Insights Settings.apply_user_permissions = %r (MUST be 1 for any of this to enforce permissions)" % settings.get("apply_user_permissions"))

	print("\n" + "=" * 70)
	print("STAGE 2 -- create ACTIVE_SERIES only (%s); %d series deferred pending review" % (
		", ".join(spec["data_key"] for spec in ACTIVE_SERIES), len(DEFERRED_SERIES) + 1))
	print("=" * 70)
	for spec in ACTIVE_SERIES:
		build_simple_series(spec, data_source, workbook)
	print("\nDeferred, not built this round: %s, counselling_to_admission -- see module docstring." % (
		", ".join(spec["data_key"] for spec in DEFERRED_SERIES)))

	execute_results = stage_3_verify_execute_as_admin()
	permission_results = stage_4_permission_test(execute_results)

	print("\n" + "=" * 70)
	print("SUMMARY")
	print("=" * 70)
	print("Creation results:", results)
	print("Execute (admin) results:", execute_results)
	print("Permission-test results:", permission_results)
	return {"creation": results, "execute": execute_results, "permission_test": permission_results}


run()
