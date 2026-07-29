#!/usr/bin/env python3
"""Self-check for the Phase 4 Criterion 7 port.

Same two layers as tools/test_ucc_intelligence_criterion_1.py and
tools/test_ucc_intelligence_criterion_3.py (docs/migration/phase-4-plan.md
Section 6):

1. Structural fidelity: re-extracts the exact same line ranges from the live
   legacy server-scripts/UCC Analytics - Criterion 7.py and diffs them
   against the committed analytics/criterion_7.py. Criterion 7's static
   config block (POLICY_REGISTRY..STANDARD_FIELDS) is copied byte-verbatim
   rather than tab-converted -- see the module docstring for why -- so this
   test's static-block check compares raw text, not tab-converted text, and
   the run()-body check re-derives the tab conversion the same way the port
   itself did.

2. A stubbed-frappe smoke test covering every distinct metric mode this
   criterion uses that Criterion 1/3 don't already exercise:
   `falsy`, `all_required` (7-field-group form), `required_value_coverage`,
   `not_in`, `sum`, plus the source-resolution flow, which differs from
   Criterion 1/3's (Criterion 7's `resolve_source` checks
   `frappe.db.exists("DocType", ...)` before `frappe.get_meta`, so the stub
   needs a `frappe.db` too).

    python3 tools/test_ucc_intelligence_criterion_7.py
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEGACY = ROOT / "server-scripts" / "UCC Analytics - Criterion 7.py"

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


def spaces_to_tabs(block_lines):
	out = []
	for line in block_lines:
		if not line.strip():
			out.append("")
			continue
		stripped = line.lstrip(" ")
		n_spaces = len(line) - len(stripped)
		assert n_spaces % 4 == 0, "unexpected indent: %r" % line
		out.append("\t" * (n_spaces // 4) + stripped)
	return out


def indent_one_more(block_lines):
	return ["\t" + l if l.strip() else "" for l in block_lines]


boundary_checks = [
	(63, "POLICY_REGISTRY = {'7.1.1': {'title': 'Measurement of Outcomes',"),
	(1188, 'STANDARD_FIELDS = ["name", "owner", "creation", "modified", "modified_by", "docstatus", "idx"]'),
	(1191, "def clean_text(value):"),
	(1209, "def to_number(value):"),
	(1215, "        return None"),
	(1218, "def is_permission_error(error):"),
	(1220, '    return "permission" in text or "not permitted" in text or "not allowed" in text or "403" in text'),
	(1223, "def display_doctype(doctype):"),
	(1798, "        })"),
	(1800, "def standardise_response_contract(result, criterion_name, api_method, action_name, subcriterion_name, row_limit_value):"),
	(2003, "    return result"),
	(2005, "result = {"), (2037, "}"),
	(2039, 'result = standardise_response_contract(result, "Criterion 7", "ucc_analytics_criterion_7", action, subcriterion, row_limit)'),
	(2041, 'if action == "policy_registry":'),
	(2057, '    result["drilldown"] = evaluate_metric(selected_config, True)'),
	(2059, 'result = standardise_response_contract(result, "Criterion 7", "ucc_analytics_criterion_7", action, subcriterion, row_limit)'),
	(2061, 'frappe.response["message"] = result'),
]
boundaries_ok = True
for n, expected in boundary_checks:
	actual = L(n)
	if actual != expected:
		boundaries_ok = False
		print("FAIL: legacy line %d drifted -- expected %r, got %r" % (n, expected, actual))
report(boundaries_ok, "legacy source line boundaries unchanged since the port was built")

if boundaries_ok:
	# Static block is byte-verbatim in the port -- no tab conversion (see module docstring)
	expected_static_block = "\n".join(extract(63, 1188))
	irregular = sum(
		1 for l in extract(63, 1188)
		if l.strip() and (len(l) - len(l.lstrip(" "))) % 4 != 0
	)
	report(irregular > 100, "static block still has pervasive non-4-space indentation (confirms the byte-verbatim decision is still warranted, not stale)")

	part_to_number = extract(1209, 1215)
	part_engine = extract(1223, 1798)
	part_result_dict = extract(2005, 2037)
	part_dispatch = extract(2041, 2057)

	run_body_raw = part_to_number + [""] + part_engine + [""] + part_result_dict
	run_body_raw += [
		"",
		'result = standardise_response_contract(result, "Criterion 7", "ucc_analytics_criterion_7", action, subcriterion, row_limit)',
		"",
	]
	run_body_raw += part_dispatch
	run_body_raw += [
		"",
		'result = standardise_response_contract(result, "Criterion 7", "ucc_analytics_criterion_7", action, subcriterion, row_limit)',
		"",
		"return result",
	]
	expected_run_body = "\n".join(indent_one_more(spaces_to_tabs(run_body_raw)))

	ported = (ROOT / "ucc_intelligence" / "ucc_intelligence" / "analytics" / "criterion_7.py").read_text(encoding="utf-8")

	report(expected_static_block in ported, "static POLICY_REGISTRY..STANDARD_FIELDS block matches the legacy source byte-verbatim")
	report(expected_run_body in ported, "run() body matches the legacy engine + response-assembly code verbatim (one extra indent level, tabs)")
	report('"api_method": "ucc_analytics_criterion_7"' in ported, "response still reports the legacy api_method string")
	report("frappe.response[" not in ported, "no Server Script response-object assumption left in the port (returns instead)")

report(
	L(33) == 'subcriterion = payload.get("subcriterion") or "7.1.1"',
	"legacy default subcriterion is still 7.1.1",
)
allowed_actions_block = "\n".join(extract(55, 58))
report(
	allowed_actions_block == (
		'ALLOWED_ACTIONS = [\n'
		'    "summary", "source_status", "policy_registry", "requirement_registry",\n'
		'    "question_registry", "drilldown"\n'
		"]"
	),
	"legacy ALLOWED_ACTIONS list unchanged (api.py's CRITERION_7_ALLOWED_ACTIONS mirrors this)",
)
report(
	'"403" in text' in L(1220),
	"Criterion 7's own legacy is_permission_error already checks for '403' -- reusing contracts.py's "
	"shared version here is an exact match, not a broadened one (unlike Criterion 1/3)",
)


# ============================================================
# Layer 2: stubbed-frappe smoke test
# ============================================================

sys.path.insert(0, str(ROOT / "ucc_intelligence"))


class State:
	doctypes_installed = set()
	list_data = {}


class FakeMeta:
	def __init__(self, doctype):
		self.fields = []
		self._doctype = doctype

	def has_field(self, fieldname):
		return fieldname in State.list_data.get(self._doctype, [{}])[0] or fieldname == "name"


class FakeDB:
	@staticmethod
	def exists(doctype_type, name):
		assert doctype_type == "DocType"
		return name in State.doctypes_installed


def _get_meta(doctype):
	if doctype not in State.doctypes_installed:
		raise RuntimeError("DocType %s not found" % doctype)
	return FakeMeta(doctype)


def _get_list(doctype, fields=None, filters=None, limit_start=0, limit_page_length=20, order_by=None):
	rows = State.list_data.get(doctype, [])
	return [dict(r) for r in rows]


class FakeUtils:
	now = staticmethod(lambda: "2026-07-29 00:00:00")
	today = staticmethod(lambda: "2026-07-29")

	@staticmethod
	def add_days(date, days):
		return date


class _FrappeThrow(Exception):
	pass


frappe_stub = types.ModuleType("frappe")
frappe_stub.get_meta = _get_meta
frappe_stub.get_list = _get_list
frappe_stub.db = FakeDB()
frappe_stub.throw = lambda msg, *a, **k: (_ for _ in ()).throw(_FrappeThrow(msg))
frappe_stub.utils = FakeUtils()
frappe_stub.whitelist = lambda *a, **k: (lambda f: f)
sys.modules["frappe"] = frappe_stub

import ucc_intelligence.analytics.criterion_7 as criterion_7  # noqa: E402 - stub must load first

# "Management Review" is deliberately left uninstalled, to exercise the
# source-unavailable path via frappe.db.exists (Criterion 7's own
# resolve_source flow, distinct from Criterion 1/3's).
State.doctypes_installed = {
	"Quality Performance Outcomes", "Quality Goal", "Quality Action",
	"Quality Meeting", "Operational Outcomes Cost Time Saving",
}
State.list_data = {
	"Quality Performance Outcomes": [
		{
			"name": "P-1", "outcome_category": "Student and Graduate Outcomes", "indicator": "Retention Rate",
			"benchmark": "80", "target": "85", "actual": "82", "measurement_date": "2026-01-01", "owner": "Jane",
		},
		{
			"name": "P-2", "outcome_category": "", "indicator": "", "benchmark": "", "target": "",
			"actual": "", "measurement_date": "", "owner": "",
		},
		{
			"name": "P-3", "outcome_category": "Service Quality Outcomes", "indicator": "First-response time",
			"benchmark": "1", "target": "2", "actual": "3", "measurement_date": "2026-02-01", "owner": "Bob",
		},
	],
	"Quality Goal": [{"name": "G-1"}, {"name": "G-2"}],
	"Quality Action": [
		{"name": "QA-1", "custom_status_updates": "Completed"},
		{"name": "QA-2", "custom_status_updates": "Closed"},
		{"name": "QA-3", "custom_status_updates": "Open"},
	],
	"Quality Meeting": [{"name": "M-1"}],
	"Operational Outcomes Cost Time Saving": [
		{"name": "O-1", "total_net_saving": "100", "variance_to_benchmark": "10"},
		{"name": "O-2", "total_net_saving": "250", "variance_to_benchmark": "-5"},
	],
}

result = criterion_7.run(action="summary", subcriterion="7.1.1", filters={}, metric_id=None, page=1, page_size=50, row_limit=2000)
report(result.get("ok") is True, "smoke run returns ok=True")

m = {x["id"]: x for x in result["metrics"]}
report(m["c711-outcomes"]["status"] == "available" and m["c711-outcomes"]["value"] == 3, "c711-outcomes (all) counts all 3 performance rows")
report(m["c711-missing-domain"]["status"] == "available" and m["c711-missing-domain"]["value"] == 1, "c711-missing-domain (falsy) counts 1 of 3 (P-2)")
report(m["c711-missing-owner"]["status"] == "available" and m["c711-missing-owner"]["value"] == 1, "c711-missing-owner (falsy) counts 1 of 3 (P-2)")
report(
	m["c711-core-field-complete"]["status"] == "available" and m["c711-core-field-complete"]["value"] == 2 and m["c711-core-field-complete"]["denominator"] == 3,
	"c711-core-field-complete (all_required, 7 field groups) counts 2 of 3 complete, denominator=3",
)
report(
	m["c711-domain-coverage"]["status"] == "available" and m["c711-domain-coverage"]["value"] == 2 and m["c711-domain-coverage"]["denominator"] == 4
	and set(m["c711-domain-coverage"]["covered_values"]) == {"Student and Graduate Outcomes", "Service Quality Outcomes"}
	and set(m["c711-domain-coverage"]["missing_values"]) == {"Operational Outcomes", "People Development Outcomes"},
	"c711-domain-coverage (required_value_coverage) covers 2 of 4 required domains, by substring alias match",
)
report(m["c711-quality-goals"]["status"] == "available" and m["c711-quality-goals"]["value"] == 2, "c711-quality-goals (all) counts 2 goal rows")
report(m["c711-quality-actions"]["status"] == "available" and m["c711-quality-actions"]["value"] == 3, "c711-quality-actions (all) counts all 3 action rows")
report(m["c711-open-actions"]["status"] == "available" and m["c711-open-actions"]["value"] == 1, "c711-open-actions (not_in Completed/Closed) counts 1 of 3")
report(m["c711-quality-meetings"]["status"] == "available" and m["c711-quality-meetings"]["value"] == 1, "c711-quality-meetings (all) counts 1 meeting row")
report(m["c711-management-reviews"]["status"] == "unavailable", "c711-management-reviews reports unavailable via frappe.db.exists, not a crash (Management Review deliberately uninstalled)")
report(m["c711-net-saving"]["status"] == "available" and m["c711-net-saving"]["value"] == 350.0, "c711-net-saving (sum) totals 100+250=350.0")
report(m["c711-benchmark-variance"]["status"] == "available" and m["c711-benchmark-variance"]["value"] == 5.0, "c711-benchmark-variance (sum) totals 10+(-5)=5.0")
report(m["c711-indicator-coverage"]["status"] == "unsupported", "c711-indicator-coverage (unsupported mode) reports status=unsupported without crashing")

report(
	any(e["id"] == "c711-missing-domain" for e in result["exceptions"]),
	"exceptions list (via EXCEPTION_METRIC_IDS, like Criterion 1's approach not Criterion 3's inline flags) includes c711-missing-domain",
)

q = {x["id"]: x for x in result["questions"]}
report(q["q711-01"]["status"] == "available" and q["q711-01"]["confidence"] == "Live", "q711-01 answers from c711-outcomes with confidence=Live (support_status='Can be implemented now')")

drill = criterion_7.run(action="drilldown", subcriterion="7.1.1", filters={}, metric_id="c711-open-actions", page=1, page_size=50, row_limit=2000)
report(drill["drilldown"]["value"] == 1 and len(drill["drilldown"]["rows"]) == 1, "drilldown on a not_in metric returns the 1 matched row")

drill_unsupported = criterion_7.run(action="drilldown", subcriterion="7.1.1", filters={}, metric_id="c711-indicator-coverage", page=1, page_size=50, row_limit=2000)
report(drill_unsupported["drilldown"]["status"] == "unsupported", "drilldown on an unsupported metric returns the placeholder, not a crash")

try:
	criterion_7.run(action="drilldown", subcriterion="7.1.1", filters={}, metric_id="does-not-exist", page=1, page_size=50, row_limit=2000)
	report(False, "drilldown on an unknown metric_id raises")
except _FrappeThrow:
	report(True, "drilldown on an unknown metric_id raises")

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
