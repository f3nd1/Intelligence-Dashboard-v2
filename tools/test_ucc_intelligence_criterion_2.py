#!/usr/bin/env python3
"""Self-check for the Phase 4 Criterion 2 port.

Same two layers as the other ported criteria's tests
(docs/migration/phase-4-plan.md Section 6):

1. Structural fidelity: re-extracts the exact same line ranges from the live
   legacy server-scripts/UCC Analytics - Criterion 2.py and diffs them
   against the committed analytics/criterion_2.py. Uses the same
   per-line-graceful spaces-to-tabs conversion the port itself uses, so this
   test also proves the "warnings" list pocket (legacy lines 1795-1798,
   irregularly indented even though it's inside the otherwise-regular
   run()-body range) survives byte-verbatim.

2. A stubbed-frappe smoke test covering `all`/`equals`/`in`/`unsupported`
   (subcriterion 2.1.1) and `conditions`/`average_fields` (subcriterion
   2.4.2) -- the modes the other three ported criteria's tests don't reach.

    python3 tools/test_ucc_intelligence_criterion_2.py
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEGACY = ROOT / "server-scripts" / "UCC Analytics - Criterion 2.py"

checks = []


def report(ok, message):
	print(("PASS" if ok else "FAIL") + ": " + message)
	checks.append(ok)
	return ok


# ============================================================
# Layer 1: structural fidelity
# ============================================================

legacy_lines = LEGACY.read_text(encoding="utf-8").split("\n")


def L(n):
	return legacy_lines[n - 1]


def extract(start, end):
	return legacy_lines[start - 1:end]


def spaces_to_tabs_graceful(block_lines):
	out = []
	for line in block_lines:
		if not line.strip():
			out.append("")
			continue
		stripped = line.lstrip(" ")
		n_spaces = len(line) - len(stripped)
		if n_spaces % 4 == 0:
			out.append("\t" * (n_spaces // 4) + stripped)
		else:
			out.append(line)
	return out


def indent_one_more(block_lines):
	return ["\t" + l if l.strip() else "" for l in block_lines]


boundary_checks = [
	(63, "POLICY_REGISTRY = {'2.1.1': {'title': 'Staff Selection and Management',"),
	(974, "]"),
	(976, "def clean_text(value):"),
	(991, "def to_number(value):"),
	(997, "        return None"),
	(999, "def is_permission_error(error):"),
	(1005, "    )"),
	(1007, "def resolve_source(alias):"),
	(1553, "        available_metrics = available_metrics + 1"),
	(1555, "def standardise_response_contract(result, criterion_name, api_method, action_name, subcriterion_name, row_limit_value):"),
	(1758, "    return result"),
	(1760, "result = {"), (1799, "}"),
	(1801, 'result = standardise_response_contract(result, "Criterion 2", "ucc_analytics_criterion_2", action, subcriterion, row_limit)'),
	(1803, 'if action == "policy_registry":'),
	(1823, '    result["drilldown"] = evaluate_metric(selected_config, True)'),
	(1825, 'result = standardise_response_contract(result, "Criterion 2", "ucc_analytics_criterion_2", action, subcriterion, row_limit)'),
	(1827, 'frappe.response["message"] = result'),
]
boundaries_ok = True
for n, expected in boundary_checks:
	actual = L(n)
	if actual != expected:
		boundaries_ok = False
		print("FAIL: legacy line %d drifted -- expected %r, got %r" % (n, expected, actual))
report(boundaries_ok, "legacy source line boundaries unchanged since the port was built")

if boundaries_ok:
	expected_static_block = "\n".join(extract(63, 974))
	irregular = sum(
		1 for l in extract(63, 974)
		if l.strip() and (len(l) - len(l.lstrip(" "))) % 4 != 0
	)
	report(irregular > 100, "static block still has pervasive non-4-space indentation (confirms the byte-verbatim decision is still warranted)")

	part_to_number = extract(991, 997)
	part_engine = extract(1007, 1553)
	part_result_dict = extract(1760, 1799)
	part_dispatch = extract(1803, 1823)

	run_body_raw = part_to_number + [""] + part_engine + [""] + part_result_dict
	run_body_raw += [
		"",
		'result = standardise_response_contract(result, "Criterion 2", "ucc_analytics_criterion_2", action, subcriterion, row_limit)',
		"",
	]
	run_body_raw += part_dispatch
	run_body_raw += [
		"",
		'result = standardise_response_contract(result, "Criterion 2", "ucc_analytics_criterion_2", action, subcriterion, row_limit)',
		"",
		"return result",
	]
	expected_run_body = "\n".join(indent_one_more(spaces_to_tabs_graceful(run_body_raw)))

	ported = (ROOT / "ucc_intelligence" / "ucc_intelligence" / "analytics" / "criterion_2.py").read_text(encoding="utf-8")

	report(expected_static_block in ported, "static POLICY_REGISTRY..STANDARD_FIELDS block matches the legacy source byte-verbatim")
	report(expected_run_body in ported, "run() body matches the legacy engine + response-assembly code verbatim, incl. the irregular 'warnings' pocket preserved as-is")
	report('"api_method": "ucc_analytics_criterion_2"' in ported, "response still reports the legacy api_method string")
	report("frappe.response[" not in ported, "no Server Script response-object assumption left in the port (returns instead)")
	report(
		"\t 'Custom DocTypes are resolved only from approved policy-referenced candidates.'," in ported,
		"the irregularly-indented 'warnings' list line survives with exactly one added tab, original spacing untouched",
	)

report(
	L(32) == 'subcriterion = payload.get("subcriterion") or "2.1.1"',
	"legacy default subcriterion is still 2.1.1",
)
allowed_actions_block = "\n".join(extract(56, 59))
report(
	allowed_actions_block == (
		'ALLOWED_ACTIONS = [\n'
		'    "summary", "source_status", "policy_registry", "requirement_registry",\n'
		'    "question_registry", "drilldown"\n'
		"]"
	),
	"legacy ALLOWED_ACTIONS list unchanged (api.py's CRITERION_2_ALLOWED_ACTIONS mirrors this)",
)
report(
	"403" not in "\n".join(extract(999, 1005)),
	"Criterion 2's own legacy is_permission_error does not check '403' -- contracts.py's shared "
	"version (which does) is a documented Phase 2 decision, not re-derived here",
)


# ============================================================
# Layer 2: stubbed-frappe smoke test
# ============================================================

sys.path.insert(0, str(ROOT / "ucc_intelligence"))


class State:
	meta_available = set()
	list_data = {}


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


def _get_list(doctype, fields=None, filters=None, limit_start=0, limit_page_length=20, order_by=None):
	rows = State.list_data.get(doctype, [])
	return [dict(r) for r in rows]


class FakeUtils:
	now = staticmethod(lambda: "2026-07-29 00:00:00")
	today = staticmethod(lambda: "2026-07-29")


class _FrappeThrow(Exception):
	pass


frappe_stub = types.ModuleType("frappe")
frappe_stub.get_meta = _get_meta
frappe_stub.get_list = _get_list
frappe_stub.throw = lambda msg, *a, **k: (_ for _ in ()).throw(_FrappeThrow(msg))
frappe_stub.utils = FakeUtils()
frappe_stub.whitelist = lambda *a, **k: (lambda f: f)
sys.modules["frappe"] = frappe_stub

import ucc_intelligence.analytics.criterion_2 as criterion_2  # noqa: E402 - stub must load first

# --- 2.1.1: all / equals / in / unsupported, job_applicant deliberately unavailable ---
State.meta_available = {"Employee", "Job Requisition", "Interview Feedback"}
State.list_data = {
	"Employee": [
		{"name": "E-1", "status": "Active"},
		{"name": "E-2", "status": "Inactive"},
		{"name": "E-3", "status": "Active"},
	],
	"Job Requisition": [
		{"name": "JR-1", "status": "Open"},
		{"name": "JR-2", "status": "Closed"},
	],
	"Interview Feedback": [{"name": "IF-1"}],
}

result_211 = criterion_2.run(action="summary", subcriterion="2.1.1", filters={}, metric_id=None, page=1, page_size=50, row_limit=2000)
report(result_211.get("ok") is True, "2.1.1 smoke run returns ok=True")
m = {x["id"]: x for x in result_211["metrics"]}
report(m["c211-employees"]["status"] == "available" and m["c211-employees"]["value"] == 3, "c211-employees (all) counts all 3 employee rows")
report(m["c211-active-employees"]["status"] == "available" and m["c211-active-employees"]["value"] == 2, "c211-active-employees (equals) counts 2 of 3 (Active)")
report(m["c211-requisitions"]["status"] == "available" and m["c211-requisitions"]["value"] == 2, "c211-requisitions (all) counts both requisitions")
report(m["c211-open-requisitions"]["status"] == "available" and m["c211-open-requisitions"]["value"] == 1, "c211-open-requisitions (in) counts 1 of 2 (Open)")
report(m["c211-applicants"]["status"] == "unavailable", "c211-applicants reports unavailable, not a crash (Job Applicant deliberately unstubbed)")
report(m["c211-competency-threshold"]["status"] == "unsupported", "c211-competency-threshold (unsupported mode) reports status=unsupported without crashing")

exc = {x["id"] for x in result_211["exceptions"]}
report("c211-open-requisitions" in exc, "exceptions list (via EXCEPTION_METRIC_IDS) includes c211-open-requisitions")

drill = criterion_2.run(action="drilldown", subcriterion="2.1.1", filters={}, metric_id="c211-open-requisitions", page=1, page_size=50, row_limit=2000)
report(drill["drilldown"]["value"] == 1 and len(drill["drilldown"]["rows"]) == 1, "drilldown on an 'in' metric returns the 1 matched row")

drill_unsupported = criterion_2.run(action="drilldown", subcriterion="2.1.1", filters={}, metric_id="c211-competency-threshold", page=1, page_size=50, row_limit=2000)
report(drill_unsupported["drilldown"]["status"] == "unsupported", "drilldown on an unsupported metric returns the placeholder, not a crash")

try:
	criterion_2.run(action="drilldown", subcriterion="2.1.1", filters={}, metric_id="does-not-exist", page=1, page_size=50, row_limit=2000)
	report(False, "drilldown on an unknown metric_id raises")
except _FrappeThrow:
	report(True, "drilldown on an unknown metric_id raises")

# --- 2.4.2: conditions (contains + in) and average_fields, student-satisfaction-survey shape ---
State.meta_available = {"Survey Tracking"}
State.list_data = {
	"Survey Tracking": [
		{"name": "T-1", "respondent_type": "Student Survey", "status": "Completed", "rating": "4"},
		{"name": "T-2", "respondent_type": "Student Survey", "status": "Submitted", "rating": "5"},
		{"name": "T-3", "respondent_type": "Student Survey", "status": "Draft", "rating": "2"},
		{"name": "T-4", "respondent_type": "Staff Survey", "status": "Completed", "rating": "1"},
	],
}

result_242 = criterion_2.run(action="summary", subcriterion="2.4.2", filters={}, metric_id=None, page=1, page_size=50, row_limit=2000)
m2 = {x["id"]: x for x in result_242["metrics"]}
report(m2["c242-responses"]["status"] == "available" and m2["c242-responses"]["value"] == 3,
	"c242-responses (conditions: contains 'student') counts 3 of 4 (excludes the Staff Survey row)")
report(m2["c242-completed"]["status"] == "available" and m2["c242-completed"]["value"] == 2,
	"c242-completed (conditions: contains 'student' AND status in [Completed, Submitted]) counts 2 of 4")
report(m2["c242-rating"]["status"] == "available" and m2["c242-rating"]["value"] == 3.67,
	"c242-rating (average_fields, gated by the same 'student' condition) averages (4+5+2)/3 = 3.67")

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
