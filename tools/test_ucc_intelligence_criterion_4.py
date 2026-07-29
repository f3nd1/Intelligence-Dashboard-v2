#!/usr/bin/env python3
"""Self-check for the Criterion 4 admission_intelligence module.

Not the same shape as tools/test_ucc_intelligence_criterion_{1,2,3,6,7}.py.
Those five are verbatim ports of a legacy Server Script, so their tests
re-extract the exact same legacy line ranges and diff them against the
committed file (structural fidelity) before a stubbed-frappe smoke test.
Criterion 4 is a deliberately different, Insights-informed architecture
(see analytics/criterion_4.py's module docstring) -- there is no legacy
line range to diff against, so this test instead checks behavioural
equivalence directly: synthetic data, hand-computed expected values that
mirror the exact formulas legacy build_admission_intelligence() used
(group-by-count, success_rate = admitted/total*100, duration averaging),
and the source-unavailable / permission-denied / filter-passthrough paths
every other criterion's test also covers.

    python3 tools/test_ucc_intelligence_criterion_4.py
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]

checks = []


def report(ok, message):
	print(("PASS" if ok else "FAIL") + ": " + message)
	checks.append(ok)
	return ok


sys.path.insert(0, str(ROOT / "ucc_intelligence"))


class State:
	meta_available = set()
	list_data = {}
	list_permission_denied = set()


class FakeMeta:
	def __init__(self, doctype):
		self.fields = []
		self._doctype = doctype

	def has_field(self, fieldname):
		return fieldname in State.list_data.get(self._doctype, [{}])[0] or fieldname == "name"


def _get_meta(doctype):
	if doctype not in State.meta_available:
		raise RuntimeError("DocType %s not found" % doctype)
	return FakeMeta(doctype)


def _row_matches_filters(row, filters):
	for key, value in (filters or {}).items():
		if row.get(key) != value:
			return False
	return True


def _get_list(doctype, fields=None, filters=None, limit_start=0, limit_page_length=20, order_by=None):
	if doctype in State.list_permission_denied:
		raise RuntimeError("PermissionError: not permitted to read " + doctype)
	rows = State.list_data.get(doctype, [])
	return [dict(r) for r in rows if _row_matches_filters(r, filters)]


class FakeUtils:
	now = staticmethod(lambda: "2026-07-29 00:00:00")
	cint = staticmethod(lambda v: int(v) if str(v).strip().lstrip("-").isdigit() else 0)

	@staticmethod
	def date_diff(end, start):
		import datetime
		e = datetime.date.fromisoformat(str(end)[:10])
		s = datetime.date.fromisoformat(str(start)[:10])
		return (e - s).days


frappe_stub = types.ModuleType("frappe")
frappe_stub.get_meta = _get_meta
frappe_stub.get_list = _get_list
frappe_stub.utils = FakeUtils()
frappe_stub.whitelist = lambda *a, **k: (lambda f: f)
sys.modules["frappe"] = frappe_stub

import ucc_intelligence.analytics.criterion_4 as criterion_4  # noqa: E402 - stub must load first

# ============================================================
# Full dataset: applicants + admissions, exercising every chart series
# ============================================================
State.meta_available = {"Student Applicant", "Student Admission UCC"}
State.list_data = {
	"Student Applicant": [
		{"name": "A-1", "application_status": "Admitted", "academic_year": "2023", "nationality": "Singaporean", "program": "Diploma in Business", "agent": "Agent A"},
		{"name": "A-2", "application_status": "Admitted", "academic_year": "2023", "nationality": "Malaysian", "program": "Diploma in Business", "agent": "Agent B"},
		{"name": "A-3", "application_status": "Approved", "academic_year": "2024", "nationality": "Singaporean", "program": "Diploma in IT", "agent": "Agent A"},
		{"name": "A-4", "application_status": "Rejected", "academic_year": "2024", "nationality": "Indonesian", "program": "Diploma in IT", "agent": ""},
		{"name": "A-5", "application_status": "Admitted", "academic_year": "2024", "nationality": "Singaporean", "program": "Diploma in IT", "agent": "Agent A"},
	],
	"Student Admission UCC": [
		{"name": "AD-1", "student_applicant": "A-1", "pre_course_counseling": "2023-01-01", "student_signed_date": "2023-01-15", "docstatus": 1},
		{"name": "AD-2", "student_applicant": "A-2", "pre_course_counseling": "2023-02-01", "student_signed_date": "2023-02-11", "docstatus": 1},
		{"name": "AD-3", "student_applicant": "A-5", "pre_course_counseling": "2024-01-01", "student_signed_date": "2024-01-21", "docstatus": 1},
		{"name": "AD-4", "student_applicant": "A-3", "pre_course_counseling": "2024-01-01", "student_signed_date": "2024-01-11", "docstatus": 0},
	],
}

result = criterion_4.run(action="summary", subcriterion="4.1.1", filters={}, metric_id=None, page=1, page_size=50, row_limit=2000)
report(result.get("ok") is True, "run() returns ok=True")

ai = result["admission_intelligence"]
report(ai["status"] == "available", "admission_intelligence status is available")

kpis = {k["id"]: k["value"] for k in ai["kpis"]}
report(kpis["c411-applicants-total"] == 5, "c411-applicants-total counts all 5 applicant rows")
report(kpis["c411-shortlisted-approved"] == 1, "c411-shortlisted-approved counts 1 (A-3, Approved)")
report(kpis["c411-enrolled-admitted"] == 3, "c411-enrolled-admitted counts 3 (A-1, A-2, A-5, Admitted)")
report(kpis["c411-success-rate"] == 60.0, "c411-success-rate = 3/5*100 = 60.0, matching the legacy formula exactly")

charts = ai["charts"]
report(charts["applicants_by_year"] == [{"label": "2023", "value": 2}, {"label": "2024", "value": 3}],
	"applicants_by_year groups and sorts by year: 2023=2, 2024=3")
report(charts["enrolled_by_year"] == [{"label": "2023", "value": 2}, {"label": "2024", "value": 1}],
	"enrolled_by_year is applicants_by_year filtered to Admitted only: 2023=2 (A-1,A-2), 2024=1 (A-5)")
report(
	charts["applicants_by_country"] == [{"label": "Indonesian", "value": 1}, {"label": "Malaysian", "value": 1}, {"label": "Singaporean", "value": 3}],
	"applicants_by_country resolves the nationality field and sorts alphabetically",
)
report(
	charts["programmes"] == [{"label": "Diploma in Business", "value": 2}, {"label": "Diploma in IT", "value": 3}],
	"programmes resolves the program field and sorts alphabetically",
)
report(
	charts["agents"] == [{"label": "Agent A", "value": 3}, {"label": "Agent B", "value": 1}, {"label": "Not specified", "value": 1}],
	"agents resolves the agent field, blank agent (A-4) buckets under 'Not specified'",
)
report(
	charts["counselling_to_admission"] == [
		{"label": "2023", "value": 12.0, "record_count": 2},
		{"label": "2024", "value": 20.0, "record_count": 1},
	],
	"counselling_to_admission averages duration per year via the linked applicant's academic_year, "
	"excludes the docstatus=0 (unsubmitted) admission row (AD-4)",
)
report(ai["chart_status"]["counselling_to_admission"] == "available", "duration chart status is available when all three required fields resolve")

# ============================================================
# Filter passthrough: the concrete benefit over the pilot's iframe embed --
# same-request filters flow into the query, no separate wiring needed.
# ============================================================
filtered = criterion_4.run(action="summary", subcriterion="4.1.1", filters={"academic_year": "2023"}, metric_id=None, page=1, page_size=50, row_limit=2000)
filtered_kpis = {k["id"]: k["value"] for k in filtered["admission_intelligence"]["kpis"]}
report(filtered_kpis["c411-applicants-total"] == 2, "academic_year filter reaches the query directly: only 2023's 2 rows counted")

# ============================================================
# Subcriterion guard: admission_intelligence only populates for 4.1.1,
# matching the legacy build_admission_intelligence() guard exactly.
# ============================================================
other_sub = criterion_4.run(action="summary", subcriterion="4.2.1", filters={}, metric_id=None, page=1, page_size=50, row_limit=2000)
report(other_sub["admission_intelligence"] == {}, "admission_intelligence is empty for any subcriterion other than 4.1.1")
report(other_sub.get("ok") is True, "the response is still contract-valid for other subcriteria, just with admission_intelligence empty")

# ============================================================
# Source-unavailable and permission-denied paths
# ============================================================
State.meta_available = set()
State.list_data = {}
unavailable = criterion_4.run(action="summary", subcriterion="4.1.1", filters={}, metric_id=None, page=1, page_size=50, row_limit=2000)
report(
	unavailable["admission_intelligence"]["status"] == "unavailable" and unavailable["admission_intelligence"]["kpis"] == [],
	"Student Applicant unavailable (DocType not installed) reports unavailable, not a crash",
)

State.meta_available = {"Student Applicant"}
State.list_data = {"Student Applicant": [{"name": "A-1", "application_status": "Admitted", "academic_year": "2023"}]}
State.list_permission_denied = {"Student Applicant"}
denied = criterion_4.run(action="summary", subcriterion="4.1.1", filters={}, metric_id=None, page=1, page_size=50, row_limit=2000)
report(denied["admission_intelligence"]["status"] == "permission_denied", "a permission-denied source reports permission_denied, not a silent bypass")
State.list_permission_denied = set()

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
