"""Criterion 4 (Student Protection and Support) -- `admission_intelligence`
only, Insights-informed rather than a verbatim port of
`server-scripts/UCC Analytics - Criterion 4.py`.

**This is a deliberate architecture change, confirmed with Felix, not a
continuation of the Phase 4 verbatim-porting technique used for Criteria 1,
2, 3, 6 and 7.** Those five stay as-is; Criterion 4 (and, separately,
Criterion 5) switch to: author and verify each chart's query in the
Frappe Insights UI against real live data, then hand-translate the
verified query into this module -- so the SQL that answers a chart still
runs live, every request, against the site's own database (same as the
legacy script always did), just designed via Insights instead of hand-
written from scratch. Insights itself has no runtime footprint here: no
iframe, no public dashboard, no call into Insights' own API at request
time (the pilot's own permission test proved a public Insights dashboard
has zero row/column permission enforcement -- see
`docs/migration/insights-pilot-findings.md` Section 4(b) -- so nothing
about this module goes anywhere near that mechanism). Permission
enforcement is the same two mechanisms every other criterion already
relies on: `ucc_dashboard_access` gates whether Criterion 4 mounts for
this user at all (unchanged), and the `frappe.get_list` calls below run
without `ignore_permissions=True`, so ordinary Frappe DocType/row
permissions apply exactly as they did in the legacy script.

**Scope, confirmed with Felix**: only `admission_intelligence` -- the 4
KPIs and 6 chart series from legacy `build_admission_intelligence()`
(`server-scripts/UCC Analytics - Criterion 4.py:2359-2489`) -- moves to
this approach. Criterion 4's other ~40 metrics/questions/requirements
(contract, fee protection, movement, refund, support services, attendance)
are explicitly NOT covered here. They stay planned as regular hand-ported
code, same technique as Criteria 1/2/3/6/7, built later in the normal
pattern -- not deferred to Insights, just not built yet. Until then, `run()`
returns a contract-valid response with `admission_intelligence` populated
and everything else defaulted empty by `standardise_response_contract`
(the same defaulting every other criterion's response already relies on).

**What's genuinely verified against live data vs. faithfully translated but
not yet independently re-verified** -- stated plainly rather than implying
uniform confidence across all 6 series:

- `applicants_by_year` and `enrolled_by_year` are grounded in the pilot's
  actual tested query (`docs/migration/scripts/create_insights_pilot.py`,
  `docs/migration/insights-pilot-findings.md` Section 3's Stage 0/1/1b
  update): `Student Applicant.academic_year` is a confirmed real Link
  field (62 rows, 0 blank, sample values 2021-2025 on the live bench), and
  the base query genuinely has no `WHERE` clause until a filter is applied
  -- both used directly here, not assumed.
- `applicants_by_country`, `programmes`, `agents`, and
  `counselling_to_admission` (the duration chart) were never independently
  authored/verified in the Insights UI -- the pilot only ever built the one
  chart. These four are faithful translations of
  `build_admission_intelligence()`'s own field-candidate logic
  (`resolve_field` with the same candidate lists the legacy script used:
  `["nationality", "country"]`, `["program", "course",
  "course_applying_for"]`, `["agent", "custom_agent",
  "recruitment_agent"]`, and the admission-duration field set), which is
  why `resolve_field`/`get_meta` are still present in this file even though
  the goal was to move away from defensive field-candidate probing --
  dropping that probing for a field nobody has actually confirmed exists on
  this site would be trading verified behaviour for an unverified guess,
  the opposite of what "moved to Insights" is supposed to buy. These four
  should still go through the author-and-verify-in-Insights step Felix has
  bench access for; once that happens, whichever of them turn out to use
  a single confirmed field can drop `resolve_field` the same way
  `academic_year` already has.

**What's dropped, not because it's unimportant but because it no longer
serves a purpose at this smaller scope**: the legacy script's eleven
module-level caches (`meta_cache`, `resolved_field_cache`, `row_cache`,
etc.) existed to keep ~40+ generically-evaluated metrics cheap per request.
Six purpose-built queries evaluated once per request have nothing to
cache -- `get_meta`/`resolve_field` below are plain, uncached functions,
correct by not needing the caching problem to exist in the first place,
not by solving it more simply.

**A concrete benefit of this approach the pilot itself couldn't test**:
the pilot's iframe-embed spike left Section 4(a) (filter behaviour)
explicitly untested, with a documented expectation that an embedded
Insights chart would NOT receive the page's filter strip state, since an
iframe has no mechanism to pass it through. That concern doesn't apply
here -- `admission_intelligence` is computed inside the same whitelisted
`run()` call as the rest of Criterion 4, so `filters.academic_year` from
the request payload flows straight into the query below the same way
`ucc_analytics_criterion_1` through `_7`'s filters always have.
"""

import frappe

from ucc_intelligence.analytics.contracts import is_permission_error, standardise_response_contract
from ucc_intelligence.analytics.engine import clean_text, is_truthy, lower_text

SOURCE_CANDIDATES = {
	"applicant": ["Student Applicant"],
	"admission": ["Student Admission UCC"],
}


def get_meta(doctype):
	try:
		return frappe.get_meta(doctype)
	except Exception:
		return None


def field_exists(meta, fieldname):
	if not fieldname or not meta:
		return False
	try:
		for meta_field in meta.fields or []:
			if meta_field.fieldname == fieldname:
				return True
	except Exception:
		pass
	try:
		return bool(meta.has_field(fieldname))
	except Exception:
		return False


def resolve_field(doctype, candidates):
	meta = get_meta(doctype)
	if not meta:
		return ""
	for fieldname in candidates or []:
		if field_exists(meta, fieldname):
			return fieldname
	return ""


def resolve_source(alias):
	candidates = SOURCE_CANDIDATES.get(alias) or []
	attempts = []
	for candidate_index in range(len(candidates)):
		doctype = candidates[candidate_index]
		if not get_meta(doctype):
			attempts.append({"doctype": doctype, "status": "unavailable", "message": "DocType metadata is unavailable."})
			continue
		try:
			frappe.get_list(doctype, fields=["name"], limit_start=0, limit_page_length=1, order_by="modified desc")
			return {"key": alias, "doctype": doctype, "status": "available", "candidates": candidates, "fallback_used": candidate_index > 0}
		except Exception as error:
			message = clean_text(error)
			status = "permission_denied" if is_permission_error(error) else "unavailable"
			attempts.append({"doctype": doctype, "status": status, "message": message})
			if status == "permission_denied":
				return {"key": alias, "doctype": doctype, "status": "permission_denied", "message": message, "candidates": candidates}
	return {
		"key": alias, "doctype": None, "status": "unavailable",
		"message": "No approved candidate DocType could be resolved.",
		"candidates": candidates, "resolution_attempts": attempts,
	}


def group_count_rows(rows, fieldname, status_value=None):
	grouped = {}
	expected_status = lower_text(status_value) if status_value else ""
	for row in rows or []:
		if expected_status and lower_text(row.get("application_status")) != expected_status:
			continue
		label = clean_text(row.get(fieldname)) or "Not specified"
		grouped[label] = grouped.get(label, 0) + 1
	return [{"label": label, "value": grouped.get(label) or 0} for label in grouped]


def sort_group_rows(rows, year_mode=False):
	output = list(rows or [])
	if year_mode:
		def year_key(item):
			label = clean_text(item.get("label"))
			try:
				return (0, int(label))
			except Exception:
				return (1, label.lower())
		output.sort(key=year_key)
	else:
		output.sort(key=lambda item: lower_text(item.get("label")))
	return output


def build_admission_intelligence(filters, row_limit):
	applicant_source = resolve_source("applicant")
	if applicant_source.get("status") != "available":
		return {
			"status": applicant_source.get("status") or "unavailable",
			"message": applicant_source.get("message") or "Student Applicant is unavailable.",
			"kpis": [],
			"charts": {},
		}

	applicant_doctype = applicant_source.get("doctype")

	active_filters = {}
	requested_year = filters.get("academic_year")
	if requested_year not in [None, "", "All", "all"]:
		active_filters["academic_year"] = requested_year

	applicant_fields = [
		"name", "application_status", "academic_year", "nationality",
		"country", "program", "course", "agent", "intake",
	]
	try:
		applicant_rows = frappe.get_list(
			applicant_doctype, fields=applicant_fields, filters=active_filters,
			limit_page_length=row_limit + 1, order_by="modified desc",
		) or []
	except Exception as error:
		status = "permission_denied" if is_permission_error(error) else "query_error"
		return {"status": status, "message": clean_text(error), "kpis": [], "charts": {}}

	truncated = len(applicant_rows) > row_limit
	if truncated:
		applicant_rows = applicant_rows[:row_limit]

	admitted_rows = [row for row in applicant_rows if lower_text(row.get("application_status")) == "admitted"]
	approved_rows = [row for row in applicant_rows if lower_text(row.get("application_status")) == "approved"]
	applicant_by_name = {row.get("name"): row for row in applicant_rows if row.get("name")}

	applicant_total = len(applicant_rows)
	admitted_total = len(admitted_rows)
	success_rate = round((float(admitted_total) / float(applicant_total)) * 100.0, 2) if applicant_total else 0.0

	applicants_by_year = sort_group_rows(group_count_rows(applicant_rows, "academic_year"), True)
	enrolled_by_year = sort_group_rows(group_count_rows(applicant_rows, "academic_year", "Admitted"), True)

	nationality_field = resolve_field(applicant_doctype, ["nationality", "country"])
	applicants_by_country = sort_group_rows(group_count_rows(applicant_rows, nationality_field), False) if nationality_field else []

	program_field = resolve_field(applicant_doctype, ["program", "course", "course_applying_for"])
	programmes = sort_group_rows(group_count_rows(applicant_rows, program_field), False) if program_field else []

	agent_field = resolve_field(applicant_doctype, ["agent", "custom_agent", "recruitment_agent"])
	agents = sort_group_rows(group_count_rows(applicant_rows, agent_field), False) if agent_field else []

	duration_chart, duration_status, duration_message = build_counselling_duration_chart(applicant_by_name, row_limit)

	return {
		"status": "available",
		"calculation_basis": "Query authored and verified in Frappe Insights, hand-translated into this module -- see the module docstring for which of these six series that applies to today.",
		"truncated": truncated,
		"kpis": [
			{"id": "c411-applicants-total", "label": "No. of Student Applicants", "value": applicant_total, "unit": "records"},
			{"id": "c411-shortlisted-approved", "label": "No. of Shortlisted", "value": len(approved_rows), "unit": "records"},
			{"id": "c411-enrolled-admitted", "label": "No. of Enrolled Students", "value": admitted_total, "unit": "records"},
			{"id": "c411-success-rate", "label": "Success Rate", "value": success_rate, "unit": "percent"},
		],
		"charts": {
			"applicants_by_year": applicants_by_year,
			"enrolled_by_year": enrolled_by_year,
			"applicants_by_country": applicants_by_country,
			"programmes": programmes,
			"agents": agents,
			"counselling_to_admission": duration_chart,
		},
		"chart_status": {
			"applicants_by_year": "available",
			"enrolled_by_year": "available",
			"applicants_by_country": "available" if nationality_field else "unsupported_field",
			"programmes": "available" if program_field else "unsupported_field",
			"agents": "available" if agent_field else "unsupported_field",
			"counselling_to_admission": duration_status,
		},
		"notes": [
			"No. of Shortlisted follows the supplied Metabase rule: application_status equals Approved.",
			"No. of Enrolled Students follows the supplied Metabase rule: application_status equals Admitted.",
			"Number of Students per Agent counts Student Applicant records, not only admitted students.",
			duration_message,
		],
	}


def build_counselling_duration_chart(applicant_by_name, row_limit):
	admission_source = resolve_source("admission")
	if admission_source.get("status") != "available":
		return [], admission_source.get("status") or "unavailable", admission_source.get("message") or "Student Admission UCC is unavailable."

	admission_doctype = admission_source.get("doctype")
	counselling_field = resolve_field(admission_doctype, ["pre_course_counseling"])
	signed_field = resolve_field(admission_doctype, ["student_signed_date", "contract_signed_by_student_date"])
	applicant_link_field = resolve_field(admission_doctype, ["student_applicant"])
	docstatus_field = resolve_field(admission_doctype, ["docstatus"])
	own_year_field = resolve_field(admission_doctype, ["academic_year"])

	if not (counselling_field and signed_field and applicant_link_field):
		return [], "unsupported_field", "Student Admission UCC requires pre_course_counseling, student_signed_date and student_applicant fields."

	duration_fields = ["name", counselling_field, signed_field, applicant_link_field]
	for extra_field in [docstatus_field, own_year_field]:
		if extra_field and extra_field not in duration_fields:
			duration_fields.append(extra_field)

	try:
		duration_rows = frappe.get_list(
			admission_doctype, fields=duration_fields, filters={},
			limit_page_length=row_limit + 1, order_by="modified desc",
		) or []
	except Exception as error:
		status = "permission_denied" if is_permission_error(error) else "query_error"
		return [], status, clean_text(error)

	duration_by_year = {}
	duration_counts = {}
	for row in duration_rows[:row_limit]:
		if docstatus_field and frappe.utils.cint(row.get(docstatus_field)) != 1:
			continue
		applicant_row = applicant_by_name.get(row.get(applicant_link_field)) or {}
		year_label = clean_text(applicant_row.get("academic_year")) or clean_text(row.get(own_year_field)) or "Not specified"
		try:
			duration_days = frappe.utils.date_diff(row.get(signed_field), row.get(counselling_field))
		except Exception:
			duration_days = None
		if duration_days is None or duration_days < 0:
			continue
		duration_by_year[year_label] = duration_by_year.get(year_label, 0.0) + float(duration_days)
		duration_counts[year_label] = duration_counts.get(year_label, 0) + 1

	duration_chart = []
	for year_label in duration_by_year:
		count = duration_counts.get(year_label) or 0
		average_days = round(duration_by_year.get(year_label, 0.0) / float(count), 2) if count else 0.0
		duration_chart.append({"label": year_label, "value": average_days, "record_count": count})

	message = "Average calendar days from pre-course counselling to student signature for submitted Student Admission UCC records."
	return sort_group_rows(duration_chart, True), "available", message


def run(action, subcriterion, filters, metric_id, page, page_size, row_limit):
	"""Partial Criterion 4 response -- admission_intelligence only, populated
	for subcriterion 4.1.1 (matching the legacy `build_admission_intelligence`
	guard). Every other field defaults empty via `standardise_response_contract`,
	the same mechanism every other criterion's response already relies on;
	the other ~40 metrics/questions/requirements are not implemented yet, see
	the module docstring."""
	admission_intelligence = {}
	if subcriterion == "4.1.1":
		admission_intelligence = build_admission_intelligence(filters, row_limit)

	result = {
		"ok": True,
		"meta": {
			"api_method": "ucc_analytics_criterion_4",
			"status": "partial_admission_intelligence_only",
			"generated_at": frappe.utils.now(),
			"action": action,
			"subcriterion": subcriterion,
			"row_limit": row_limit,
		},
		"admission_intelligence": admission_intelligence,
		"filters": filters,
		"data": {
			"admission_intelligence": admission_intelligence,
		},
		"warnings": [
			"This is a partial Criterion 4 implementation: only admission_intelligence "
			"(the Student Applicant KPIs and their six chart series) is built so far. "
			"The other Criterion 4 metrics, questions and requirements (contract, fee "
			"protection, movement, refund, support services, attendance) are not yet "
			"implemented and will be added as regular hand-ported code, not through Insights.",
		],
	}
	result = standardise_response_contract(result, "Criterion 4", "ucc_analytics_criterion_4", action, subcriterion, row_limit)
	return result
