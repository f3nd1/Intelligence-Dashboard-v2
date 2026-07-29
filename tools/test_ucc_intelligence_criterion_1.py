#!/usr/bin/env python3
"""Self-check for the Phase 4 Criterion 1 port.

Two layers, matching what can and can't be verified without a bench
(docs/migration/phase-4-plan.md Section 6):

1. Structural fidelity: re-extracts the exact same line ranges from the live
   legacy server-scripts/UCC Analytics - Criterion 1.py, asserts the
   pre-transformation text still matches verbatim (so drift in the legacy
   file raises an error rather than silently producing a stale comparison),
   applies only the named mechanical transformations (spaces -> tabs, one
   extra indent level for the run() body), and diffs the result against the
   committed analytics/criterion_1.py, analytics/engine.py, and
   analytics/request.py. Same technique Phase 3 used for the frontend port.

2. A stubbed-frappe smoke test: proves the wired-together module actually
   runs end to end (source resolution, metric evaluation across several
   modes, the response contract) against a small synthetic dataset -- not a
   substitute for real parity testing against live data (still needs a
   bench, see the plan), but catches wiring/logic mistakes this repo can
   verify on its own.

    python3 tools/test_ucc_intelligence_criterion_1.py
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEGACY = ROOT / "server-scripts" / "UCC Analytics - Criterion 1.py"

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
	(63, "POLICY_REGISTRY = {"), (784, "]"), (785, ""), (786, "def clean_text(value):"),
	(801, "def to_number(value):"), (807, "        return None"), (808, ""),
	(809, "def is_permission_error(error):"), (816, ""),
	(817, "def resolve_source(alias):"),
	(1566, "        available_metrics = available_metrics + 1"), (1567, ""),
	(1568, "def standardise_response_contract(result, criterion_name, api_method, action_name, subcriterion_name, row_limit_value):"),
	(1773, "result = {"), (1817, "}"), (1818, ""),
	(1819, 'result = standardise_response_contract(result, "Criterion 1", "ucc_analytics_criterion_1", action, subcriterion, row_limit)'),
	(1820, ""), (1821, 'if action == "source_status":'),
	(1842, '    result["drilldown"] = evaluate_metric(selected_config, True)'), (1843, ""),
]
boundaries_ok = True
for n, expected in boundary_checks:
	actual = L(n)
	if actual != expected:
		boundaries_ok = False
		print("FAIL: legacy line %d drifted -- expected %r, got %r" % (n, expected, actual))
report(boundaries_ok, "legacy source line boundaries unchanged since the port was built")

if boundaries_ok:
	expected_static_block = "\n".join(spaces_to_tabs(extract(63, 784)))

	part_to_number = extract(801, 807)
	part_engine = extract(817, 1566)
	part_result_dict = extract(1773, 1817)
	part_dispatch = extract(1821, 1842)

	run_body_raw = part_to_number + [""] + part_engine + [""] + part_result_dict
	run_body_raw += [
		"",
		'result = standardise_response_contract(result, "Criterion 1", "ucc_analytics_criterion_1", action, subcriterion, row_limit)',
		"",
	]
	run_body_raw += part_dispatch
	run_body_raw += [
		"",
		'result = standardise_response_contract(result, "Criterion 1", "ucc_analytics_criterion_1", action, subcriterion, row_limit)',
		"",
		"return result",
	]
	expected_run_body = "\n".join(indent_one_more(spaces_to_tabs(run_body_raw)))

	ported = (ROOT / "ucc_intelligence" / "ucc_intelligence" / "analytics" / "criterion_1.py").read_text(encoding="utf-8")

	report(expected_static_block in ported, "static CONFIG/registry block matches the legacy source verbatim (tabs, unchanged content)")
	report(expected_run_body in ported, "run() body matches the legacy engine + response-assembly code verbatim (one extra indent level, tabs)")
	report(
		'"api_method": "ucc_analytics_criterion_1"' in ported,
		"response still reports the legacy api_method string (Decision B: ship dark, byte-comparable during parity testing)",
	)
	report("frappe.response[" not in ported, "no Server Script response-object assumption left in the port (returns instead)")

# request.py: default_subcriterion / allowed_actions parameterisation matches what was verified
report(
	L(32) == 'subcriterion = payload.get("subcriterion") or "1.1.1"',
	"legacy default subcriterion is still 1.1.1 (request.py's default_subcriterion argument for this criterion)",
)
allowed_actions_block = "\n".join(extract(56, 59))
report(
	allowed_actions_block == (
		'ALLOWED_ACTIONS = [\n'
		'    "summary", "source_status", "policy_registry", "requirement_registry",\n'
		'    "question_registry", "drilldown"\n'
		"]"
	),
	"legacy ALLOWED_ACTIONS list unchanged (api.py's CRITERION_1_ALLOWED_ACTIONS mirrors this)",
)

# engine.py: lower_text/is_truthy verified byte-identical, clean_text majority-identical
engine_expected = "\n".join(spaces_to_tabs(extract(786, 799)))
engine_py = (ROOT / "ucc_intelligence" / "ucc_intelligence" / "analytics" / "engine.py").read_text(encoding="utf-8")
report(engine_expected in engine_py, "engine.py's clean_text/lower_text/is_truthy match Criterion 1's legacy copies verbatim")


# ============================================================
# Layer 2: stubbed-frappe smoke test
# ============================================================

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


def _get_list(doctype, fields=None, filters=None, limit_start=0, limit_page_length=20, order_by=None):
	if doctype in State.list_permission_denied:
		raise RuntimeError("PermissionError: not permitted to read " + doctype)
	rows = State.list_data.get(doctype, [])
	return [dict(r) for r in rows]


class FakeUtils:
	now = staticmethod(lambda: "2026-07-29 00:00:00")
	today = staticmethod(lambda: "2026-07-29")

	@staticmethod
	def getdate(value):
		import datetime
		if isinstance(value, datetime.date):
			return value
		return datetime.date.fromisoformat(str(value)[:10])

	@staticmethod
	def add_days(date, days):
		import datetime
		d = FakeUtils.getdate(date)
		return d + datetime.timedelta(days=int(days))


class _FrappeThrow(Exception):
	pass


frappe_stub = types.ModuleType("frappe")
frappe_stub.get_meta = _get_meta
frappe_stub.get_list = _get_list
frappe_stub.throw = lambda msg, *a, **k: (_ for _ in ()).throw(_FrappeThrow(msg))
frappe_stub.utils = FakeUtils()
frappe_stub.whitelist = lambda *a, **k: (lambda f: f)
sys.modules["frappe"] = frappe_stub

import ucc_intelligence.analytics.criterion_1 as criterion_1  # noqa: E402 - stub must load first

# Wire up a deliberately mixed dataset for the "overview" subcriterion:
# - risk_register available, with one open-high-risk row and one closed row
#   (exercises the "conditions" mode's actual counting logic)
# - policy_control available, with one overdue-review row
# - esg_tracker available, with one below-target row (exercises "field_compare")
# - everything else in "overview"'s source list left unavailable, to exercise
#   that path too without having to fabricate 13 datasets by hand
State.meta_available = {"Risk Register and Mitigation Plans", "Policies and Standards Type", "ESG Impact Tracker"}
State.list_data = {
	"Risk Register and Mitigation Plans": [
		{"name": "R-1", "risk_level": "High", "status": "Open", "target_date": "2020-01-01"},
		{"name": "R-2", "risk_level": "Low", "status": "Closed", "target_date": "2099-01-01"},
	],
	"Policies and Standards Type": [
		{"name": "P-1", "next_review_date": "2020-01-01", "status": "Active"},
	],
	"ESG Impact Tracker": [
		{"name": "E-1", "actual": "5", "target": "10"},
		{"name": "E-2", "actual": "15", "target": "10"},
	],
}

result = criterion_1.run(
	action="summary", subcriterion="overview", filters={}, metric_id=None,
	page=1, page_size=50, row_limit=2000,
)

report(result.get("ok") is True, "smoke run returns ok=True")
report(isinstance(result.get("metrics"), list) and len(result["metrics"]) == 7, "overview subcriterion evaluates all 7 configured metrics")
report(isinstance(result.get("source_summary"), dict) and result["source_summary"]["total"] == 13, "source_summary reflects all 13 overview sources")

metric_by_id = {m["id"]: m for m in result["metrics"]}
report(metric_by_id["o-open-high-risks"]["status"] == "available" and metric_by_id["o-open-high-risks"]["value"] == 1,
	"o-open-high-risks correctly counts 1 (High + Open) of 2 risk rows, not both")
report(metric_by_id["o-overdue-policy-review"]["status"] == "available" and metric_by_id["o-overdue-policy-review"]["value"] == 1,
	"o-overdue-policy-review correctly counts the 1 row with a past next_review_date")
report(metric_by_id["o-esg-off-track"]["status"] == "available" and metric_by_id["o-esg-off-track"]["value"] == 1,
	"o-esg-off-track's field_compare mode correctly counts 1 of 2 rows (actual < target)")
report(metric_by_id["o-overdue-oversight-review"]["status"] == "unavailable",
	"a source with no stubbed metadata correctly reports unavailable, not a crash")

report(any(dq["status"] == "unavailable" for dq in result["data_quality"]), "unavailable sources are surfaced in data_quality")
report(len(result["exceptions"]) > 0 and all(e["id"] in criterion_1.EXCEPTION_METRIC_IDS for e in result["exceptions"]),
	"exceptions list is populated and scoped to EXCEPTION_METRIC_IDS")

# drilldown action, exercising the second code path (include_rows=True, pagination)
drill = criterion_1.run(
	action="drilldown", subcriterion="overview", filters={}, metric_id="o-open-high-risks",
	page=1, page_size=50, row_limit=2000,
)
report(drill["drilldown"]["value"] == 1 and len(drill["drilldown"]["rows"]) == 1, "drilldown returns the matched row for a live metric")

# Unknown metric_id on drilldown should throw, matching the legacy frappe.throw behaviour
try:
	criterion_1.run(action="drilldown", subcriterion="overview", filters={}, metric_id="does-not-exist", page=1, page_size=50, row_limit=2000)
	report(False, "drilldown on an unknown metric_id raises")
except _FrappeThrow:
	report(True, "drilldown on an unknown metric_id raises")

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
