#!/usr/bin/env python3
"""Self-check for the Criterion 4 port.

Two layers now, the same as the other six ported criteria -- it did not used
to have the first one, because until 2026-08-02 this module was
`admission_intelligence` and nothing else and there was no legacy range to
diff against.

1. Structural fidelity: re-extracts the same line ranges from the live legacy
   server-scripts/UCC Analytics - Criterion 4.py -- INDEPENDENTLY of
   tools/generate_criterion_4.py, so a bug in the generator cannot hide a
   drifted port -- and diffs them against the committed criterion_4.py. It
   also asserts the ONE excluded range is genuinely absent, so the declared
   divergence stays a divergence rather than quietly becoming two copies of
   the admission block.

2. A stubbed-frappe behaviour test of admission_intelligence: synthetic data,
   hand-computed expected values mirroring the formulas legacy
   build_admission_intelligence() used (group-by-count, success_rate =
   admitted/total*100, duration averaging), plus the source-unavailable,
   permission-denied and filter-passthrough paths -- and, since the port,
   that the ported engine actually runs and answers the 40 questions.

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


# ============================================================
# LAYER 1: structural fidelity against the live legacy source
# ============================================================
# These ranges are stated here independently of tools/generate_criterion_4.py.
# If the generator ever extracts something different, this fails.
LEGACY = ROOT / "server-scripts" / "UCC Analytics - Criterion 4.py"
PORTED = ROOT / "ucc_intelligence" / "ucc_intelligence" / "analytics" / "criterion_4.py"
ADMISSION = ROOT / "ucc_intelligence" / "ucc_intelligence" / "analytics" / "criterion_4_admission.py"

legacy_lines = LEGACY.read_text(encoding="utf-8").split("\n")
ported_source = PORTED.read_text(encoding="utf-8")


def extract(start, end):
	return legacy_lines[start - 1:end]


def spaces_to_tabs_graceful(block):
	out = []
	for text in block:
		if not text.strip():
			out.append("")
			continue
		indent = len(text) - len(text.lstrip(" "))
		out.append("\t" * (indent // 4) + text.lstrip(" ") if indent % 4 == 0 else text)
	return out


def indent_one_more(block):
	return ["\t" + text if text.strip() else "" for text in block]


# The boundaries this port was cut at. Asserted by content, so a legacy edit
# that shifts the line numbers fails loudly here instead of silently porting
# the wrong range.
BOUNDARY_MARKERS = {
	66: "POLICY_REGISTRY = {'overview': {'title': 'Criterion 4 Overview',",
	323: "CONFIG = {'overview': {'sources': ['counselling',",
	789: "REQUIREMENT_REGISTRY = [{'id': '4.1.1.1',",
	1020: "QUESTION_REGISTRY = {'overview': [{'id': 'O-01',",
	1421: "]",
	1480: "def get_meta(doctype):",
	2359: "def build_admission_intelligence():",
	2489: "    }",
	2492: "admission_intelligence = build_admission_intelligence()",
	3208: "result = {",
}
for number, expected in BOUNDARY_MARKERS.items():
	report(legacy_lines[number - 1] == expected,
		"legacy line %d is still %r" % (number, expected[:52]))

# The registries, module-level and verbatim.
report("\n".join(extract(66, 1421)) in ported_source,
	"POLICY_REGISTRY .. CHILD_SAFE_FIELDS ported verbatim (1,356 legacy lines)")

# The engine, indented one level into run().
for label, start, end in (
	("the five local helpers (clean_text .. is_permission_error)", 1424, 1457),
	("the twelve caches", 1460, 1478),
	("get_meta .. sort_group_rows", 1480, 2357),
	("evaluate_requirement .. the summary counters", 2493, 3002),
	("the result contract", 3208, 3259),
	("the action dispatch", 3263, 3284),
):
	block = "\n".join(indent_one_more(spaces_to_tabs_graceful(extract(start, end))))
	report(block in ported_source, "%s ported verbatim (legacy %d-%d)" % (label, start, end))

# The one declared divergence, asserted as an ABSENCE. Two copies of the
# admission block -- the legacy one and the Insights-informed one -- is the
# failure this guards against.
report("def build_admission_intelligence(" not in ported_source,
	"the legacy build_admission_intelligence() is NOT in the port")
report("criterion_4_admission.build_admission_intelligence(" in ported_source,
	"...the Insights-informed one is called instead")
report('if subcriterion == "4.1.1":' in ported_source,
	"...and the guard from inside the excluded function is reinstated at the call site")
report(ADMISSION.exists() and "def build_admission_intelligence(" in ADMISSION.read_text(encoding="utf-8"),
	"the Insights-informed implementation still exists, in its own module")

# The counts Felix quoted from his own live Criterion 4 output.
import ast  # noqa: E402

registries = {}
for node in ast.parse(ported_source).body:
	if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
		try:
			registries[node.targets[0].id] = ast.literal_eval(node.value)
		except Exception:
			pass
questions = registries.get("QUESTION_REGISTRY") or {}
config = registries.get("CONFIG") or {}
report(len(questions) == 8 and sum(len(v) for v in questions.values()) == 40,
	"40 management questions across 8 sections")
report(sum(len(v.get("metrics") or []) for v in config.values()) == 81,
	"81 metrics")
metric_ids = [m["id"] for v in config.values() for m in (v.get("metrics") or [])]
for wanted in ("c411-applicants-total", "c411-enrolled-admitted", "c411-success-rate",
		"c411-counselling", "c411-conditional"):
	report(wanted in metric_ids, "the metric %s survived the port" % wanted)
report(len(registries.get("REQUIREMENT_REGISTRY") or []) == 31, "31 requirements")
report(len(registries.get("SOURCE_CANDIDATES") or {}) == 19, "19 source aliases")
report(len(registries.get("SAFE_FIELDS") or {}) == 19, "19 safe-field maps")

run_functions = [n.name for n in ast.parse(ported_source).body
	if isinstance(n, ast.FunctionDef) and n.name == "run"]
report(run_functions == ["run"], "run() is the single entry point")


# ============================================================
# LAYER 2: behaviour, against a stubbed frappe
# ============================================================


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
	# The verbatim port uses this criterion's OWN clean_text/to_number, which
	# are the frappe.utils.cstr/flt variants -- not analytics.engine's str()
	# ones. See criterion_4.py's module docstring.
	cstr = staticmethod(lambda v: "" if v is None else str(v))

	@staticmethod
	def flt(value):
		try:
			return float(value)
		except (TypeError, ValueError):
			return 0.0

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


def _throw(message, exc=None):
	raise RuntimeError(message)


frappe_stub.throw = _throw
frappe_stub.get_doc = lambda doctype, name: None
frappe_stub.get_all = _get_list
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

# ============================================================
# THE RESTORATION ITSELF: the questions Criterion 4 never had
# ============================================================
# The port's whole point. Felix's live output showed 62 Student Applicant
# records, 60 admitted, 96.77% success rate, 52 counselling declarations and
# 3 conditional admissions -- answers the app could not produce at all,
# because this module held admission_intelligence and nothing else.
State.meta_available = {"Student Applicant", "Student Admission UCC"}
State.list_data = {
	"Student Applicant": [
		{"name": "A-%d" % i, "application_status": "Admitted", "academic_year": "2024"}
		for i in range(1, 8)
	],
	"Student Admission UCC": [],
}

for subcriterion, expected in (
		("overview", 2), ("4.1.1", 8), ("4.2.1", 4), ("4.2.2", 6),
		("4.3.1", 5), ("4.4.1", 5), ("4.5.1", 4), ("4.6.1", 6)):
	answered = criterion_4.run(action="summary", subcriterion=subcriterion, filters={},
		metric_id=None, page=1, page_size=50, row_limit=2000)
	questions = answered.get("questions") or []
	report(len(questions) == expected,
		"subcriterion %s answers %d questions (got %d)" % (subcriterion, expected, len(questions)))
	report(all(q.get("id") and q.get("question") and q.get("status") for q in questions),
		"...each one carries an id, the question text and a status")

summary = criterion_4.run(action="summary", subcriterion="4.1.1", filters={}, metric_id=None,
	page=1, page_size=50, row_limit=2000)
answers = {q["id"]: q for q in summary["questions"]}
live = [q for q in summary["questions"] if q.get("status") == "available"]
report(bool(live), "at least one question answers from live rows rather than reporting unavailable")
report(any("7" in str(q.get("answer") or "") for q in live),
	"...and the answer contains the count from the stubbed rows, not a placeholder")
# Derived from CONFIG rather than hardcoded, so this asserts "every metric
# this subcriterion declares gets evaluated" instead of a number I guessed.
expected_metrics = len(config["4.1.1"]["metrics"])
report(len(summary.get("metrics") or []) == expected_metrics,
	"4.1.1 evaluates all %d of its configured metrics (got %d)"
	% (expected_metrics, len(summary.get("metrics") or [])))
report(bool(summary.get("requirements")), "the requirement registry is evaluated too")
report(summary["admission_intelligence"]["status"] == "available",
	"and admission_intelligence still works alongside all of it")

# The actions the endpoint newly allows must actually return something.
for action, key in (("policy_registry", "registry"), ("requirement_registry", "registry"),
		("question_registry", "registry")):
	response = criterion_4.run(action=action, subcriterion="4.1.1", filters={}, metric_id=None,
		page=1, page_size=50, row_limit=2000)
	report(bool(response.get(key)), "action %r returns a populated %s" % (action, key))

drill = criterion_4.run(action="drilldown", subcriterion="4.1.1", filters={},
	metric_id="c411-applicants-total", page=1, page_size=50, row_limit=2000)
report(bool(drill.get("drilldown")), "action 'drilldown' resolves a real metric id")

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
