"""Create the remaining Insights Query v3 / Chart v3 records for Criterion
4's admission_intelligence (Option B: Sophia embeds live Insights queries
directly, confirmed with Felix after the real permission test in
test_insights_private_permissions.py proved private query execution
respects real per-user Frappe permissions -- 0 rows restricted, 6 rows
with real access, on the actual bench).

**Full build, 2026-07-30**: builds ALL remaining series --
`applicants_by_country`, `programmes`, `agents` (via ACTIVE_SERIES) and
`counselling_to_admission` (via build_counselling_duration) -- alongside
the two already proven live on the real bench (`applicants_by_year` from
the original pilot, `enrolled_by_year` from the 2026-07-29 scoped-down
run). Both of those are verified, not recreated.

Earlier runs deliberately built one series at a time so the pattern could
be reviewed live before committing to the rest; that review passed (both
charts confirmed rendering real data through the real embed path on
/app/sophia-analytics), so the remaining 4 are built together now.

Stage 4's permission test correspondingly covers the newly-built charts,
not just one -- every chart this script creates gets a real
restricted-vs-control comparison before it's called done, matching the
discipline every capability built tonight has followed.

The runtime module (admission_intelligence_embed.py) and the frontend
wiring already tolerate a partial build gracefully -- a chart whose Query
v3 record doesn't exist yet reports `status: "unavailable"` and renders
the existing generic empty state, not an error and not a permission
notice. That means a partial failure here (e.g. a field candidate that
doesn't exist on this site) degrades to "that one card is empty", not a
broken page.

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

# Reused, not reimplemented: this is the same classifier the Analytics
# frontend already uses to decide whether an error is a permission denial
# (analytics/contracts.py, itself ported verbatim from the legacy Criterion 7
# script). A second copy here could drift from it, and then the permission
# test and the running product would disagree about what "denied" means.
from ucc_intelligence.analytics.contracts import is_permission_error

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
# All simple (single-table, optional-filter, group-by-count) series are now
# active; counselling_to_admission is separate only because it needs a join
# and a computed duration column, so it has its own builder below.
#
# `dimension_candidates` is a list, not one fieldname, deliberately: the
# legacy engine probed these candidates at runtime because the real field
# varies by site, and this session has never verified nationality/program/
# agent against the live schema the way academic_year was verified by the
# original pilot. resolve_field_live() picks the first that genuinely
# exists on THIS site's meta before the query is authored -- a candidate
# that doesn't exist yields a clean "SKIP" line, not a broken query.
ACTIVE_SERIES = [
	{
		"data_key": "enrolled_by_year",
		"doctype": APPLICANT_DOCTYPE,
		"dimension_candidates": ["academic_year"],
		"filter_field_candidates": None,  # academic_year already verified by the pilot; used as literal here
		"filter": {"column": "application_status", "operator": "=", "value": "Admitted"},
		"chart_type": "Line",
	},
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
	test_insights_private_permissions.py against EVERY chart that executed
	successfully -- including `applicants_by_year`, which the original pilot
	already proved, because re-proving it costs one extra iteration and
	catches the case where a site-wide setting (Insights Settings.
	apply_user_permissions) drifted since that proof. Permission enforcement
	is the one property worth re-verifying rather than trusting a prior run
	for, since it fails silently and site-wide."""
	print("\n" + "=" * 70)
	print("STAGE 4 -- restricted-vs-control permission test on every executing chart")
	print("=" * 70)

	candidates = [dk for dk in CHART_TITLES if execute_results.get(dk, {}).get("status") == "pass"]
	if not candidates:
		print("No chart executed successfully in Stage 3 -- nothing to test. Skipping Stage 4.")
		return {}
	print("Testing %d chart(s): %s" % (len(candidates), ", ".join(candidates)))

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

	def execute_as_test_user(query_name):
		frappe.set_user(test_user_email)
		try:
			doc = frappe.get_doc("Insights Query v3", query_name)
			doc.check_permission("read")
			return len(doc.execute(page_size=1000).get("rows") or [])
		except Exception as error:
			return "error: %s" % error
		finally:
			frappe.set_user("Administrator")

	def classify_restricted(outcome):
		"""What the restricted user's result actually tells us.

		Insights can deny at either of two layers, and BOTH are passes:

		  filtered  the query ran and row-level filtering
		            (Insights Settings.apply_user_permissions) removed every
		            row -> 0 rows.
		  denied    the query was refused outright at the table/document
		            layer, before executing at all.

		`denied` is not weaker than `filtered`. Both disclose zero rows;
		`denied` refuses earlier, without running the query. Insights moved
		from the first to the second, which is why this test started
		reporting NEEDS REVIEW on charts that had previously been proved.

		The distinction that matters is NOT error-vs-rows, it is
		permission-vs-anything-else. A timeout, a missing table or a syntax
		error ALSO returns no data to the restricted user, and would sail
		through a check that merely accepted "an error". Those stay
		inconclusive, because they prove nothing about permissions -- they
		would look identical for a fully authorised user.
		"""
		if isinstance(outcome, int):
			# The one genuinely bad outcome, and it deserves its own name:
			# rows reached a user with no access to the underlying DocType.
			return "filtered" if outcome == 0 else "breach"
		if is_permission_error(outcome):
			return "denied"
		return "inconclusive"

	query_names = {dk: frappe.db.get_value("Insights Query v3", {"title": CHART_TITLES[dk]}, "name") for dk in candidates}
	for query_name in query_names.values():
		if query_name and not is_shared("Insights Query v3", query_name, test_user_email):
			frappe.share.add("Insights Query v3", query_name, user=test_user_email, read=1)
	frappe.db.commit()

	# Two phases, NOT one loop doing restricted-then-control per chart: the
	# control step grants System Manager to the test user, which is a
	# permanent change to that user for the rest of the run. Doing it inside
	# a per-chart loop means chart 2 onwards would run its "restricted" test
	# as an already-elevated user and report real rows -- a false failure
	# that looks exactly like a genuine permission breach. So: every
	# restricted read first, THEN grant once, THEN every control read.
	print("\n--- Phase 1: restricted user (no Student Applicant access) ---")
	restricted_rows_by_key = {}
	for data_key in candidates:
		restricted_rows_by_key[data_key] = execute_as_test_user(query_names[data_key])
		print("%-26s %s" % (data_key, restricted_rows_by_key[data_key]))

	if not frappe.db.exists("Has Role", {"parent": test_user_email, "role": "System Manager"}):
		user_doc = frappe.get_doc("User", test_user_email)
		user_doc.append("roles", {"role": "System Manager"})
		user_doc.save(ignore_permissions=True)
		frappe.db.commit()
	frappe.clear_cache(user=test_user_email)

	print("\n--- Phase 2: control (same user, now granted System Manager) ---")
	permission_results = {}
	for data_key in candidates:
		control_rows = execute_as_test_user(query_names[data_key])
		restricted_rows = restricted_rows_by_key[data_key]
		enforcement = classify_restricted(restricted_rows)

		# The control read is what makes any of this evidence. Restricted and
		# control are the SAME query, the SAME chart and the SAME user
		# account -- the only variable is the System Manager role. So if the
		# restricted read was denied and the control read returns real rows,
		# the denial is caused by the permission state and cannot be a broken
		# query, a renamed table or an empty result set: those would fail the
		# control read too.
		control_ok = isinstance(control_rows, int) and control_rows > 0

		if not control_ok:
			verdict = "NEEDS REVIEW"
			reason = "control read returned no rows -- cannot tell a real denial from a broken query"
		elif enforcement == "breach":
			verdict = "PERMISSION BREACH"
			reason = "restricted user received %s rows of data they have no access to" % restricted_rows
		elif enforcement == "filtered":
			verdict = "GO"
			reason = "row-level filtering removed every row"
		elif enforcement == "denied":
			verdict = "GO"
			reason = "refused at the table layer, before the query ran"
		else:
			verdict = "NEEDS REVIEW"
			reason = "restricted read failed for a NON-permission reason; proves nothing about access"

		print("%-26s restricted=%-58s control=%-5s -> %s (%s)" % (
			data_key, restricted_rows, control_rows, verdict, reason))
		permission_results[data_key] = {
			"restricted_rows": restricted_rows,
			"control_rows": control_rows,
			"enforcement": enforcement,
			"verdict": verdict,
			"reason": reason,
		}

	# When denial happens at the TABLE layer, the query never runs, so this
	# run has not exercised row-level filtering at all. That is fine for
	# safety -- nothing was disclosed -- but it means the site-wide setting is
	# now the only remaining evidence that the second layer still exists. If
	# the table gate is ever relaxed (a legitimate share, a role grant), row
	# filtering becomes the thing standing between a user and the data, so it
	# is checked explicitly rather than assumed.
	apply_user_permissions = bool(frappe.db.get_singles_dict("Insights Settings").get("apply_user_permissions"))
	denied_only = [k for k, r in permission_results.items() if r["enforcement"] == "denied"]
	if denied_only and not apply_user_permissions:
		print("\nWARNING -- %d chart(s) were denied at the table layer, so row-level filtering was never"
			" exercised, AND Insights Settings.apply_user_permissions is OFF. The second layer is"
			" both unproven and disabled. Turn it back on." % len(denied_only))
		for data_key in denied_only:
			permission_results[data_key]["verdict"] = "NEEDS REVIEW"
			permission_results[data_key]["reason"] = (
				"denied at the table layer, but apply_user_permissions is OFF -- row filtering unproven and disabled")
	elif denied_only:
		print("\nNote: %d chart(s) were denied at the TABLE layer rather than returning 0 filtered rows."
			" Both deny equally; the table layer refuses earlier. apply_user_permissions is ON, so"
			" row-level filtering remains in place as the second layer." % len(denied_only))

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
	print("STAGE 2 -- create/reuse all remaining series (%s, counselling_to_admission)" % (
		", ".join(spec["data_key"] for spec in ACTIVE_SERIES)))
	print("=" * 70)
	for spec in ACTIVE_SERIES:
		build_simple_series(spec, data_source, workbook)
	build_counselling_duration(data_source, workbook)

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
