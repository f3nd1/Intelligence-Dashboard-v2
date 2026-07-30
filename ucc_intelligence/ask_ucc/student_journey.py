"""Student Journey tool functions for Ask UCC -- the fixed, named allowlist
this module may call (CLAUDE.md Phase 8).

Ported from server-scripts/UCC Ask - Student Journey.py after a full read
of all 4208 lines. Its ~30 keyword-triggered intents collapse into 4
tools, all sharing one internal context loader (the single largest piece
of reusable logic in the legacy script).

**The legacy AI path is deliberately not ported, and is genuinely
broken.** `ai_route()` builds `payload["model"] = OPENAI_MODEL` at legacy
line 1611, and `OPENAI_MODEL` is never defined anywhere in that file --
confirmed by grep over all 4208 lines, the token appears exactly once.
Worse, the payload dict is constructed *before* the `try:` at line 1625,
so the resulting NameError is raised outside the handler and propagates
all the way out of the request. It only ever fires when a caller supplies
an `openai_api_key` form param (otherwise the empty-key check short-
circuits first), which means that path is dead in normal operation and
hard-crashes the whole endpoint the moment anyone actually uses it. The
new ai/ layer replaces it entirely rather than patching it.

**Deliberately NOT ported** (documented, not silently dropped):

- All six global/cohort intents (`handle_class_today`,
  `handle_cohort_types`, `handle_cohort_count`, `handle_graduation_list`,
  `handle_leave_count`, `handle_cohort_dashboard`) -- cross-record search,
  same deferral as the other two modules. `all_admissions()` alone pulls
  10000 rows.
- **The `student_roll_rows` parameter.** The legacy frontend POSTs
  pre-rendered "Student Roll" report rows, and `build_individual_context`
  merges them with *higher priority than the database*
  (`source_kind == "report"` scores +100 in the dedup). A server-side tool
  must not accept caller-supplied facts as authoritative -- that is the
  whole point of the tool-first design -- so only the DB path is ported.
  Consequence, stated rather than hidden: modules that exist only in that
  report and have no matching admission row will be missing until the
  report is queried server-side.
- `find_student_invoices()` and everything downstream (`handle_finance`,
  `handle_payment_timeline`, and the outstanding-amount blocker inside
  graduation readiness). It loads *every* submitted Sales Invoice (limit
  5000, no student filter) and substring-matches customer names -- both a
  full-table scan and a correctness hazard (a student named "Lee" matches
  every customer containing "lee"). The graduation-readiness tool below
  therefore reports `finance: "unavailable"` explicitly and excludes it
  from the blocker list, rather than silently dropping a blocker that the
  legacy version counted.
- `handle_documents()` -- counts file attachments and calls it document
  compliance; the legacy script's own warning concedes it proves nothing.
- `find_applicant()`'s ~150 lines of Levenshtein name-matching over 5000
  applicants, including a hardcoded typo dictionary with a specific
  student's misspelt name baked into the source. With the record supplied
  by the picker, none of it is needed.
- Dead/shadowed legacy code: `handle_all_results`@2374 and
  `handle_nationality`@2465 (both redefined later), `group_members()`
  (never called), `handle_lifecycle` (unreachable).

Permission model: no ignore_permissions; `load_student_applicant()`
classifies not_found / permission_denied / unavailable rather than the
legacy wrappers' indistinguishable empty result.
"""

import frappe

from ucc_intelligence.analytics.contracts import is_permission_error
from ucc_intelligence.analytics.engine import clean_text, lower_text

ATTENDANCE_WARNING_THRESHOLD = 90

NATIONALITY_CANDIDATES = ["nationality", "country", "citizenship", "custom_nationality"]
COMMENCEMENT_CANDIDATES = ["date_of_commencement", "commencement_date"]
ASSESSMENT_DATE_CANDIDATES = ["assessment_date", "custom_issued_date", "modified"]
GROUP_COURSE_CANDIDATES = ["course", "custom_course_name"]
GROUP_INSTRUCTOR_CANDIDATES = ["custom_instructor_full_name", "custom_instructor"]

PASS_GRADES = ["a", "b", "c", "d", "pass", "passed", "satisfactory"]
FAIL_GRADES = ["f", "fail", "failed", "unsatisfactory"]
UNAPPROVED_WORKFLOW_STATES = ["draft", "rejected", "cancelled", "canceled", "withdrawn"]


def first_value(doc, candidates):
	for fieldname in candidates:
		try:
			value = doc.get(fieldname)
		except Exception:
			value = None
		if value not in [None, ""]:
			return value
	return None


def safe_list(doctype, filters=None, fields=None, order_by=None, limit=1000):
	try:
		return frappe.get_list(
			doctype, filters=filters or {}, fields=fields or ["name"],
			order_by=order_by or "modified desc", limit_page_length=limit,
		) or []
	except Exception:
		return []


def numeric_grade_passed(grade):
	"""Legacy numeric_grade_passed(), ported exactly. Returns True/False, or
	None when the grade can't be classified either way."""
	value = lower_text(grade)
	if not value:
		return None
	if value in FAIL_GRADES:
		return False
	if value in PASS_GRADES:
		return True
	try:
		return float(value) > 0
	except Exception:
		return None


def approved_workflow(value):
	"""Legacy approved_workflow(): anything not explicitly draft/rejected/
	cancelled/withdrawn counts as approved."""
	return lower_text(value) not in UNAPPROVED_WORKFLOW_STATES


def load_student_applicant(student_applicant_name):
	try:
		return {"status": "available", "doc": frappe.get_doc("Student Applicant", student_applicant_name)}
	except frappe.DoesNotExistError:
		return {"status": "not_found", "message": "No Student Applicant named %r." % student_applicant_name}
	except Exception as error:
		status = "permission_denied" if is_permission_error(error) else "unavailable"
		return {"status": status, "message": clean_text(error)}


def student_full_name(doc):
	parts = [clean_text(doc.get("first_name")), clean_text(doc.get("middle_name")), clean_text(doc.get("last_name"))]
	return " ".join(p for p in parts if p) or clean_text(doc.get("name"))


def load_admissions(student_applicant_name):
	return safe_list(
		"Student Admission UCC",
		filters={"student_applicant": student_applicant_name, "docstatus": ["<", 2]},
		fields=[
			"name", "student_applicant", "student", "student_name", "program",
			"commencement_date", "date_of_commencement", "completion_date",
			"application_status", "modified",
		],
		order_by="commencement_date desc, modified desc", limit=20,
	)


def load_assessment_results(student_id):
	"""Two-pass, exactly as the legacy script does it: the primary query
	includes `assessment_date`, and if it returns nothing the same query is
	retried without that field (some sites don't have it) with the date
	back-filled from custom_issued_date/modified. That fallback is the
	script's own strongest signal that the field isn't guaranteed."""
	if not student_id:
		return []
	base_fields = [
		"name", "docstatus", "student", "student_name", "program", "course",
		"assessment_name", "custom_issued_date", "total_score", "maximum_score",
		"grade", "custom_retake", "student_group", "modified",
	]
	rows = safe_list(
		"Assessment Result",
		filters={"student": student_id, "docstatus": ["<", 2]},
		fields=base_fields + ["assessment_date"],
		order_by="assessment_date asc, custom_issued_date asc, modified asc", limit=1000,
	)
	if rows:
		return rows
	rows = safe_list(
		"Assessment Result",
		filters={"student": student_id, "docstatus": ["<", 2]},
		fields=base_fields,
		order_by="custom_issued_date asc, modified asc", limit=1000,
	)
	for row in rows:
		row["assessment_date"] = row.get("custom_issued_date") or row.get("modified")
	return rows


def build_context(student_applicant_name):
	"""Shared loader behind all four tools -- the legacy
	build_individual_context() minus its client-supplied report-row merge
	(see the module docstring)."""
	loaded = load_student_applicant(student_applicant_name)
	if loaded["status"] != "available":
		return loaded
	applicant = loaded["doc"]

	admissions = load_admissions(student_applicant_name)
	student_id = ""
	for admission in admissions:
		if admission.get("student"):
			student_id = clean_text(admission.get("student"))
			break

	student_doc = None
	if student_id:
		try:
			student_doc = frappe.get_doc("Student", student_id)
		except Exception:
			student_doc = None

	modules = []
	for admission in admissions:
		try:
			admission_doc = frappe.get_doc("Student Admission UCC", admission.get("name"))
		except Exception:
			continue
		for row in admission_doc.get("modules") or []:
			modules.append({
				"module_code": clean_text(row.get("module_code")),
				"module_name": clean_text(row.get("module_name")),
				"abbreviation": clean_text(row.get("abbreviation")),
				"start_date": clean_text(row.get("start_date")),
				"end_date": clean_text(row.get("end_date")),
				"score": None,
				"maximum_score": None,
				"grade": "",
				"assessment_result": "",
				"assessment_date": "",
			})

	results = load_assessment_results(student_id)
	for result in results:
		if frappe.utils.cint(result.get("docstatus")) != 1:
			continue
		result_course = lower_text(result.get("course"))
		result_name = lower_text(result.get("assessment_name"))
		for module in modules:
			keys = [lower_text(module.get(k)) for k in ("module_code", "module_name", "abbreviation")]
			keys = [k for k in keys if k]
			matched = False
			for key in keys:
				for candidate in (result_course, result_name):
					if not candidate:
						continue
					if candidate == key:
						matched = True
					elif len(key) >= 4 and key in candidate:
						matched = True
					elif len(candidate) >= 4 and candidate in key:
						matched = True
			if matched:
				# Last match wins, matching the legacy behaviour: results are
				# ordered oldest-first, so this keeps the latest sitting.
				module["score"] = result.get("total_score")
				module["maximum_score"] = result.get("maximum_score")
				module["grade"] = clean_text(result.get("grade"))
				module["assessment_result"] = clean_text(result.get("name"))
				module["assessment_date"] = clean_text(first_value(result, ASSESSMENT_DATE_CANDIDATES))

	return {
		"status": "available",
		"applicant": applicant,
		"student_id": student_id,
		"student_doc": student_doc,
		"admissions": admissions,
		"modules": modules,
	}


def get_student_profile(student_applicant_name):
	"""Tool: identity and enrolment facts. Covers the legacy handle_profile,
	handle_course, handle_commencement, handle_completion,
	handle_nationality, handle_graduation_status and handle_current_module
	intents."""
	context = build_context(student_applicant_name)
	if context.get("status") != "available":
		return context

	applicant = context["applicant"]
	admissions = context["admissions"]
	student_doc = context["student_doc"]
	latest = admissions[0] if admissions else {}
	today = clean_text(frappe.utils.today())

	current_modules = [
		m for m in context["modules"]
		if m.get("start_date") and m.get("end_date") and m["start_date"] <= today <= m["end_date"]
	]

	academic_status = clean_text(student_doc.get("custom_academic_status")) if student_doc else ""
	return {
		"status": "available",
		"student_applicant": student_applicant_name,
		"student_name": student_full_name(applicant),
		"student_id": context["student_id"] or "Not recorded",
		"programme": clean_text(latest.get("program")) or clean_text(applicant.get("program")) or "Not recorded",
		"study_type": clean_text(applicant.get("student_type")) or "Not recorded",
		"nationality": clean_text(first_value(applicant, NATIONALITY_CANDIDATES)) or "Not recorded",
		"academic_status": academic_status or "Not recorded",
		"graduated": lower_text(academic_status) == "graduated",
		"commencement_date": clean_text(first_value(latest, COMMENCEMENT_CANDIDATES)) or "Not recorded",
		"completion_date": clean_text(latest.get("completion_date")) or "Not recorded",
		"application_status": clean_text(latest.get("application_status")) or "Not recorded",
		"current_modules": [m.get("module_name") or m.get("module_code") for m in current_modules],
		"module_count": len(context["modules"]),
	}


def get_student_academic_record(student_applicant_name):
	"""Tool: modules, results and the academic analytics block. Covers the
	legacy handle_all_results, handle_module_result,
	handle_academic_progress, handle_grade_analytics and
	handle_module_completion intents."""
	context = build_context(student_applicant_name)
	if context.get("status") != "available":
		return context

	modules = context["modules"]
	today = clean_text(frappe.utils.today())

	submitted = []
	not_graded = []
	passed = []
	failed = []
	scores = []
	for module in modules:
		if module.get("assessment_result"):
			submitted.append(module)
			score = module.get("score")
			if score is not None:
				try:
					scores.append(float(score))
				except Exception:
					pass
			pass_state = numeric_grade_passed(module.get("grade"))
			if pass_state is True:
				passed.append(module)
			elif pass_state is False:
				failed.append(module)
		else:
			not_graded.append(module)

	total = len(modules)
	completion_percentage = round((len(submitted) / total) * 100, 1) if total else 0
	not_ended = [m for m in modules if not m.get("end_date") or m["end_date"] >= today]

	return {
		"status": "available",
		"student_applicant": student_applicant_name,
		"modules": modules,
		"total_modules": total,
		"submitted_count": len(submitted),
		"not_graded_count": len(not_graded),
		"passed_count": len(passed),
		"failed_count": len(failed),
		"completion_percentage": completion_percentage,
		"average_score": round(sum(scores) / len(scores), 2) if scores else None,
		"highest_score": max(scores) if scores else None,
		"lowest_score": min(scores) if scores else None,
		"modules_not_ended": len(not_ended),
		"modules_missing_results": len(not_graded),
	}


def get_student_attendance_and_leave(student_applicant_name):
	"""Tool: attendance totals, the per-month trend, and leave records.
	Covers the legacy handle_attendance, handle_attendance_trend,
	handle_leave_history and handle_leave_status intents."""
	context = build_context(student_applicant_name)
	if context.get("status") != "available":
		return context

	student_id = context["student_id"]
	today = clean_text(frappe.utils.today())

	attendance = safe_list(
		"Student Attendance",
		filters={"student": student_id, "docstatus": ["<", 2]},
		fields=["name", "student", "date", "status", "custom_type", "modified"],
		order_by="date asc, modified asc", limit=5000,
	) if student_id else []

	present = late = absent = other = 0
	monthly = {}
	for row in attendance:
		state = lower_text(row.get("status"))
		month = clean_text(row.get("date"))[:7] or "Not recorded"
		bucket = monthly.setdefault(month, {"present": 0, "late": 0, "absent": 0})
		if state == "present":
			present += 1
			bucket["present"] += 1
		elif state == "late":
			late += 1
			bucket["late"] += 1
		elif state == "absent":
			absent += 1
			bucket["absent"] += 1
		else:
			other += 1

	total = present + late + absent + other
	# Legacy formula: late counts as attended.
	rate = round(((present + late) / total) * 100, 1) if total else None

	trend = []
	for month in sorted(monthly):
		bucket = monthly[month]
		month_total = bucket["present"] + bucket["late"] + bucket["absent"]
		trend.append({
			"month": month,
			"present": bucket["present"],
			"late": bucket["late"],
			"absent": bucket["absent"],
			"rate": round(((bucket["present"] + bucket["late"]) / month_total) * 100, 1) if month_total else None,
		})

	leaves = safe_list(
		"Student Leave Application",
		filters={"student": student_id, "docstatus": ["<", 2]},
		fields=["name", "student", "workflow_state", "from_date", "to_date", "total_leave_days", "reason", "modified"],
		order_by="from_date asc", limit=1000,
	) if student_id else []

	currently_on_leave = any(
		approved_workflow(leave.get("workflow_state"))
		and clean_text(leave.get("from_date")) <= today <= clean_text(leave.get("to_date"))
		for leave in leaves
		if leave.get("from_date") and leave.get("to_date")
	)

	return {
		"status": "available",
		"student_applicant": student_applicant_name,
		"present": present,
		"late": late,
		"absent": absent,
		"other": other,
		"total_records": total,
		"attendance_rate": rate,
		"below_threshold": (rate is not None and rate < ATTENDANCE_WARNING_THRESHOLD),
		"monthly_trend": trend,
		"leaves": leaves,
		"currently_on_leave": currently_on_leave,
	}


def assess_student_graduation_readiness(student_applicant_name):
	"""Tool: deterministic graduation blockers + risk profile. Covers the
	legacy handle_graduation_readiness and handle_risk_summary intents.

	The legacy version counted an outstanding-fees blocker sourced from
	find_student_invoices(), which is not ported (see module docstring).
	Rather than silently dropping that blocker, finance is reported as
	explicitly unavailable and excluded from the risk count."""
	academic = get_student_academic_record(student_applicant_name)
	if academic.get("status") != "available":
		return academic
	attendance = get_student_attendance_and_leave(student_applicant_name)

	blockers = []
	if academic["total_modules"] == 0:
		blockers.append("No module schedule was found")
	if academic["modules_not_ended"]:
		blockers.append("%d module period(s) have not ended" % academic["modules_not_ended"])
	if academic["modules_missing_results"]:
		blockers.append("%d module result(s) are not submitted" % academic["modules_missing_results"])

	risks = []
	actions = []
	rate = attendance.get("attendance_rate")
	if rate is not None and rate < ATTENDANCE_WARNING_THRESHOLD:
		risks.append("Attendance is below %d%% at %s%%" % (ATTENDANCE_WARNING_THRESHOLD, rate))
		actions.append("Review attendance and intervention records")
	if academic["modules_missing_results"]:
		risks.append("%d module result(s) are not submitted" % academic["modules_missing_results"])
		actions.append("Confirm assessment completion and result submission")
	if attendance.get("currently_on_leave"):
		risks.append("The student is currently on approved leave")
		actions.append("Check whether the leave affects attendance or completion")

	risk_level = "Low"
	if risks:
		risk_level = "High" if len(risks) >= 3 else "Medium"

	return {
		"status": "available",
		"student_applicant": student_applicant_name,
		"blockers": blockers,
		"ready_for_graduation": len(blockers) == 0,
		"risks": risks,
		"recommended_actions": actions,
		"risk_level": risk_level,
		"finance": "unavailable",
		"note": (
			"Rule-based readiness check. The outstanding-fees blocker the legacy "
			"assistant included is deliberately excluded: it was derived from an "
			"unfiltered invoice name-match that is not reliable enough to gate a "
			"graduation decision. Formal graduation still requires authorised verification."
		),
	}


TOOLS = {
	"get_student_profile": get_student_profile,
	"get_student_academic_record": get_student_academic_record,
	"get_student_attendance_and_leave": get_student_attendance_and_leave,
	"assess_student_graduation_readiness": assess_student_graduation_readiness,
}
