#!/usr/bin/env python3
"""Self-check for the Phase 4 Criterion 3 port.

Same two layers as tools/test_ucc_intelligence_criterion_1.py
(docs/migration/phase-4-plan.md Section 6):

1. Structural fidelity: re-extracts the exact same line ranges from the live
   legacy server-scripts/UCC Analytics - Criterion 3.py, asserts the
   pre-transformation text still matches verbatim, applies only the named
   mechanical transformations (spaces -> tabs, one extra indent level for
   the run() body), and diffs the result against the committed
   analytics/criterion_3.py.

2. A stubbed-frappe smoke test: proves the wired-together module actually
   runs end to end -- base metrics, the two-pass derived-metric evaluation
   (derived_sum and derived_percent), the unsupported-metric placeholder
   path, and drilldown across all three of those metric shapes -- against a
   small synthetic dataset. Not a substitute for real bench-side parity
   testing, but catches wiring/logic mistakes this repo can verify on its
   own. Criterion 3's engine has a genuinely different shape from
   Criterion 1's (two-pass base/derived evaluation, no requirement
   registry), so this is a fresh test, not a copy of Criterion 1's.

    python3 tools/test_ucc_intelligence_criterion_3.py
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEGACY = ROOT / "server-scripts" / "UCC Analytics - Criterion 3.py"

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
	(81, "POLICY_REGISTRY = {"), (1101, "]"),
	(1104, "def clean_text(value):"), (1119, "    return True"),
	(1122, "def to_number(value):"), (1128, "        return None"),
	(1131, "def is_permission_error(error):"), (1137, "    )"),
	(1140, "def clone_dict(source):"),
	(1984, "        unavailable_questions = unavailable_questions + 1"),
	(1986, "def standardise_response_contract(result, criterion_name, api_method, action_name, subcriterion_name, row_limit_value):"),
	(2189, "    return result"),
	(2191, "result = {"), (2250, "}"),
	(2252, 'result = standardise_response_contract(result, "Criterion 3", "ucc_analytics_criterion_3", action, subcriterion, row_limit)'),
	(2254, 'if action == "policy_registry":'),
	(2282, '        result["drilldown"] = evaluate_base_metric(selected_config, True)'),
	(2284, 'result = standardise_response_contract(result, "Criterion 3", "ucc_analytics_criterion_3", action, subcriterion, row_limit)'),
	(2286, 'frappe.response["message"] = result'),
]
boundaries_ok = True
for n, expected in boundary_checks:
	actual = L(n)
	if actual != expected:
		boundaries_ok = False
		print("FAIL: legacy line %d drifted -- expected %r, got %r" % (n, expected, actual))
report(boundaries_ok, "legacy source line boundaries unchanged since the port was built")

if boundaries_ok:
	expected_static_block = "\n".join(spaces_to_tabs(extract(81, 1101)))

	part_to_number = extract(1122, 1128)
	part_engine = extract(1140, 1984)
	part_result_dict = extract(2191, 2250)
	part_dispatch = extract(2254, 2282)

	run_body_raw = part_to_number + [""] + part_engine + [""] + part_result_dict
	run_body_raw += [
		"",
		'result = standardise_response_contract(result, "Criterion 3", "ucc_analytics_criterion_3", action, subcriterion, row_limit)',
		"",
	]
	run_body_raw += part_dispatch
	run_body_raw += [
		"",
		'result = standardise_response_contract(result, "Criterion 3", "ucc_analytics_criterion_3", action, subcriterion, row_limit)',
		"",
		"return result",
	]
	expected_run_body = "\n".join(indent_one_more(spaces_to_tabs(run_body_raw)))

	ported = (ROOT / "ucc_intelligence" / "ucc_intelligence" / "analytics" / "criterion_3.py").read_text(encoding="utf-8")

	report(expected_static_block in ported, "static CONFIG/registry block matches the legacy source verbatim (tabs, unchanged content)")
	report(expected_run_body in ported, "run() body matches the legacy engine + response-assembly code verbatim (one extra indent level, tabs)")
	report(
		'"api_method": "ucc_analytics_criterion_3"' in ported,
		"response still reports the legacy api_method string (Decision B: ship dark, byte-comparable during parity testing)",
	)
	report("frappe.response[" not in ported, "no Server Script response-object assumption left in the port (returns instead)")

# request.py / api.py: default_subcriterion and allowed_actions match what was verified
report(
	L(50) == 'subcriterion = payload.get("subcriterion") or "3.1.1"',
	"legacy default subcriterion is still 3.1.1",
)
allowed_actions_block = "\n".join(extract(74, 77))
report(
	allowed_actions_block == (
		'ALLOWED_ACTIONS = [\n'
		'    "summary", "source_status", "policy_registry", "requirement_registry",\n'
		'    "question_registry", "question_catalogue", "drilldown"\n'
		"]"
	),
	"legacy ALLOWED_ACTIONS list unchanged (api.py's CRITERION_3_ALLOWED_ACTIONS mirrors this, incl. question_catalogue)",
)

# engine.py / contracts.py: reused-not-redefined helpers match Criterion 3's own legacy copies
engine_py = (ROOT / "ucc_intelligence" / "ucc_intelligence" / "analytics" / "engine.py").read_text(encoding="utf-8")
report(
	"def clean_text" in engine_py and "def lower_text" in engine_py and "def is_truthy" in engine_py,
	"engine.py defines clean_text/lower_text/is_truthy (reused by criterion_3.py, not redefined)",
)
report(
	L(1131) == "def is_permission_error(error):" and "403" not in "\n".join(extract(1131, 1137)),
	"Criterion 3's own legacy is_permission_error does not check '403' -- contracts.py's shared version "
	"(which does) is a documented Phase 2 decision, not re-derived here",
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

	@staticmethod
	def add_months(date, months):
		import datetime
		d = FakeUtils.getdate(date)
		month = d.month - 1 + int(months)
		year = d.year + month // 12
		month = month % 12 + 1
		return datetime.date(year, month, min(d.day, 28))


class _FrappeThrow(Exception):
	pass


frappe_stub = types.ModuleType("frappe")
frappe_stub.get_meta = _get_meta
frappe_stub.get_list = _get_list
frappe_stub.throw = lambda msg, *a, **k: (_ for _ in ()).throw(_FrappeThrow(msg))
frappe_stub.utils = FakeUtils()
frappe_stub.whitelist = lambda *a, **k: (lambda f: f)
sys.modules["frappe"] = frappe_stub

import ucc_intelligence.analytics.criterion_3 as criterion_3  # noqa: E402 - stub must load first

# --- overview: base metrics (equals/in/date_next_days) + derived_sum + unsupported ---
State.meta_available = {"Agent", "Agent Contract"}
State.list_data = {
	"Agent": [
		{"name": "A-1", "status": "Under Review", "workflow_state": "Under Review"},
		{"name": "A-2", "status": "Suspended", "workflow_state": "Suspended"},
		{"name": "A-3", "status": "Active", "workflow_state": "Active"},
	],
	"Agent Contract": [
		{"name": "C-1", "end_date": "2026-08-01"},   # within 90 days of 2026-07-29
		{"name": "C-2", "end_date": "2030-01-01"},   # far in the future
	],
}

overview = criterion_3.run(action="summary", subcriterion="overview", filters={}, metric_id=None, page=1, page_size=50, row_limit=2000)
report(overview.get("ok") is True, "overview smoke run returns ok=True")
m = {x["id"]: x for x in overview["metrics"]}
report(m["ov-under-review"]["status"] == "available" and m["ov-under-review"]["value"] == 1, "ov-under-review (equals) counts 1 of 3 agents")
report(m["ov-noncontinuing"]["status"] == "available" and m["ov-noncontinuing"]["value"] == 1, "ov-noncontinuing (in) counts 1 of 3 agents")
report(m["ov-expiring-90"]["status"] == "available" and m["ov-expiring-90"]["value"] == 1, "ov-expiring-90 (date_next_days) counts 1 of 2 contracts")
report(m["ov-known-attention-total"]["status"] == "available" and m["ov-known-attention-total"]["value"] == 3,
	"ov-known-attention-total (derived_sum) sums the three referenced base metrics (1+1+1)")
report(m["ov-requirement-evidence-coverage"]["status"] == "unsupported",
	"ov-requirement-evidence-coverage (unsupported_metric placeholder) reports status=unsupported without crashing")

drill_sum = criterion_3.run(action="drilldown", subcriterion="overview", filters={}, metric_id="ov-known-attention-total", page=1, page_size=50, row_limit=2000)
report(drill_sum["drilldown"]["value"] == 3, "drilldown on a derived_sum metric returns the already-computed metric object")

# --- 3.1.1: all / in / equals / truthy / all_required / derived_percent, agent-only dataset ---
State.meta_available = {"Agent"}
State.list_data = {
	"Agent": [
		{"name": "A-1", "status": "Active", "custom_ra_application_form_date": "2024-01-01", "agent_search_type": "Referral"},
		{"name": "A-2", "status": "Under Review", "custom_ra_application_form_date": "2024-02-01"},
		{"name": "A-3", "status": "Active"},
	],
}

c311 = criterion_3.run(action="summary", subcriterion="3.1.1", filters={}, metric_id=None, page=1, page_size=50, row_limit=2000)
m3 = {x["id"]: x for x in c311["metrics"]}
report(m3["c311-agents"]["status"] == "available" and m3["c311-agents"]["value"] == 3, "c311-agents (all) counts all 3 agents")
report(m3["c311-screening"]["status"] == "available" and m3["c311-screening"]["value"] == 1, "c311-screening (in) counts 1 of 3 (Under Review)")
report(m3["c311-active"]["status"] == "available" and m3["c311-active"]["value"] == 2, "c311-active (equals) counts 2 of 3 (Active)")
report(m3["c311-formal-selection-population"]["status"] == "available" and m3["c311-formal-selection-population"]["value"] == 2,
	"c311-formal-selection-population (truthy) counts 2 of 3 (have an application date)")
report(m3["c311-identification-complete"]["status"] == "available" and m3["c311-identification-complete"]["value"] == 1,
	"c311-identification-complete (all_required) counts 1 of 3 (both fields truthy)")
report(m3["c311-identification-completeness-proxy"]["status"] == "available" and m3["c311-identification-completeness-proxy"]["value"] == 50.0,
	"c311-identification-completeness-proxy (derived_percent) computes 1/2 = 50.0%")

other_sources_unavailable = [s for s in c311["sources"] if s.get("key") != "agent" and s.get("status") != "available"]
report(len(other_sources_unavailable) == 7, "the other 7 sources in 3.1.1's list correctly report unavailable, not a crash")

drill_pct = criterion_3.run(action="drilldown", subcriterion="3.1.1", filters={}, metric_id="c311-identification-completeness-proxy", page=1, page_size=50, row_limit=2000)
report(drill_pct["drilldown"]["value"] == 50.0, "drilldown on a derived_percent metric returns the already-computed metric object")

drill_unsupported = criterion_3.run(action="drilldown", subcriterion="3.1.1", filters={}, metric_id="c311-background-approval-compliance", page=1, page_size=50, row_limit=2000)
report(drill_unsupported["drilldown"]["status"] == "unsupported", "drilldown on an unsupported metric returns the placeholder, not a crash")

drill_active = criterion_3.run(action="drilldown", subcriterion="3.1.1", filters={}, metric_id="c311-active", page=1, page_size=50, row_limit=2000)
report(drill_active["drilldown"]["value"] == 2 and len(drill_active["drilldown"]["rows"]) == 2, "drilldown on a normal base metric (equals) returns the 2 matched rows")

try:
	criterion_3.run(action="drilldown", subcriterion="3.1.1", filters={}, metric_id="does-not-exist", page=1, page_size=50, row_limit=2000)
	report(False, "drilldown on an unknown metric_id raises")
except _FrappeThrow:
	report(True, "drilldown on an unknown metric_id raises")

# question_catalogue action, Criterion 3-specific (not present in Criterion 1's ALLOWED_ACTIONS)
catalogue = criterion_3.run(action="question_catalogue", subcriterion="3.1.1", filters={}, metric_id=None, page=1, page_size=50, row_limit=2000)
report("registry" in catalogue and "catalogue" in catalogue and len(catalogue["catalogue"]["3.1.1"]) == 7,
	"question_catalogue action returns the QUESTION_REGISTRY under both registry and catalogue keys")

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
