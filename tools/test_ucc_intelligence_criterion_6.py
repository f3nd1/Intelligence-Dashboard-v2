#!/usr/bin/env python3
"""Self-check for the Phase 4 Criterion 6 port.

Same two layers as the other ported criteria's tests
(docs/migration/phase-4-plan.md Section 6):

1. Structural fidelity: re-extracts the exact same line ranges from the live
   legacy server-scripts/UCC Analytics - Criterion 6.py and diffs them
   against the committed analytics/criterion_6.py, using the same
   per-line-graceful spaces-to-tabs conversion introduced for Criterion 2.

2. A stubbed-frappe smoke test focused on what's genuinely new in this
   criterion: the parent/child metric split (`child_count`,
   `child_parent_count`, `child_any_missing`), which calls
   `frappe.get_doc(...).get(table_field)` per matched parent row -- no
   other ported criterion touches child tables -- plus the
   `requirement_registry` action's cross-subcriterion aggregation, which is
   unique to Criterion 6 among the criteria ported so far. The stub also
   needs `frappe.db.exists` (Criterion 6's `resolve_source` checks DocType
   existence before `get_meta`, the same flow as Criterion 7's, not
   Criterion 1/2/3's) -- missed on the first pass here too, same as it was
   for Criterion 7.

    python3 tools/test_ucc_intelligence_criterion_6.py
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEGACY = ROOT / "server-scripts" / "UCC Analytics - Criterion 6.py"

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
	(61, "POLICY_REGISTRY = {'6.1.1': {'title': 'Internal Assessment and Quality Audits',"),
	(1128, "]"),
	(1131, "def clean_text(value):"),
	(1149, "def to_number(value):"),
	(1156, "        return None"),
	(1159, "def is_permission_error(error):"),
	(1161, '    return "permission" in text or "not permitted" in text or "not allowed" in text'),
	(1164, "def display_doctype(doctype):"),
	(1917, '        })'),
	(1919, "def standardise_response_contract(result, criterion_name, api_method, action_name, subcriterion_name, row_limit_value):"),
	(2122, "    return result"),
	(2124, "result = {"), (2171, "}"),
	(2173, 'result = standardise_response_contract(result, "Criterion 6", "ucc_analytics_criterion_6", action, subcriterion, row_limit)'),
	(2175, 'if action == "policy_registry":'),
	(2206, '    result["drilldown"] = evaluate_metric(selected_config, True)'),
	(2208, 'result = standardise_response_contract(result, "Criterion 6", "ucc_analytics_criterion_6", action, subcriterion, row_limit)'),
	(2210, 'frappe.response["message"] = result'),
]
boundaries_ok = True
for n, expected in boundary_checks:
	actual = L(n)
	if actual != expected:
		boundaries_ok = False
		print("FAIL: legacy line %d drifted -- expected %r, got %r" % (n, expected, actual))
report(boundaries_ok, "legacy source line boundaries unchanged since the port was built")

if boundaries_ok:
	expected_static_block = "\n".join(extract(61, 1128))
	irregular = sum(
		1 for l in extract(61, 1128)
		if l.strip() and (len(l) - len(l.lstrip(" "))) % 4 != 0
	)
	report(irregular > 100, "static block still has pervasive non-4-space indentation (confirms the byte-verbatim decision is still warranted)")

	part_to_number = extract(1149, 1156)
	part_engine = extract(1164, 1917)
	part_result_dict = extract(2124, 2171)
	part_dispatch = extract(2175, 2206)

	run_body_raw = part_to_number + [""] + part_engine + [""] + part_result_dict
	run_body_raw += [
		"",
		'result = standardise_response_contract(result, "Criterion 6", "ucc_analytics_criterion_6", action, subcriterion, row_limit)',
		"",
	]
	run_body_raw += part_dispatch
	run_body_raw += [
		"",
		'result = standardise_response_contract(result, "Criterion 6", "ucc_analytics_criterion_6", action, subcriterion, row_limit)',
		"",
		"return result",
	]
	expected_run_body = "\n".join(indent_one_more(spaces_to_tabs_graceful(run_body_raw)))

	ported = (ROOT / "ucc_intelligence" / "ucc_intelligence" / "analytics" / "criterion_6.py").read_text(encoding="utf-8")

	report(expected_static_block in ported, "static POLICY_REGISTRY..STANDARD_FIELDS block matches the legacy source byte-verbatim")
	report(expected_run_body in ported, "run() body matches the legacy engine + response-assembly code verbatim")
	report('"api_method": "ucc_analytics_criterion_6"' in ported, "response still reports the legacy api_method string")
	report("frappe.response[" not in ported, "no Server Script response-object assumption left in the port (returns instead)")

report(
	L(32) == 'subcriterion = payload.get("subcriterion") or "6.1.1"',
	"legacy default subcriterion is still 6.1.1",
)
allowed_actions_block = "\n".join(extract(54, 57))
report(
	allowed_actions_block == (
		'ALLOWED_ACTIONS = [\n'
		'    "summary", "source_status", "policy_registry", "requirement_registry",\n'
		'    "question_registry", "drilldown"\n'
		"]"
	),
	"legacy ALLOWED_ACTIONS list unchanged (api.py's CRITERION_6_ALLOWED_ACTIONS mirrors this)",
)
report(
	"403" not in L(1161),
	"Criterion 6's own legacy is_permission_error does not check '403' -- contracts.py's shared "
	"version (which does) is a documented Phase 2 decision, not re-derived here",
)


# ============================================================
# Layer 2: stubbed-frappe smoke test
# ============================================================

sys.path.insert(0, str(ROOT / "ucc_intelligence"))


class State:
	meta_available = set()
	list_data = {}
	docs = {}


class FakeMeta:
	def __init__(self, doctype):
		self.fields = []
		self._doctype = doctype

	def has_field(self, fieldname):
		return fieldname in State.list_data.get(self._doctype, [{}])[0] or fieldname == "name"

	def get_field(self, fieldname):
		raise RuntimeError("no child-table metadata in this stub -- falls back to the metric's configured child_doctype")


class FakeDoc:
	def __init__(self, data):
		self._data = data

	def get(self, fieldname):
		return self._data.get(fieldname)


def _get_meta(doctype):
	if doctype not in State.meta_available:
		raise RuntimeError("DocType %s not found" % doctype)
	return FakeMeta(doctype)


def _get_list(doctype, fields=None, filters=None, limit_start=0, limit_page_length=20, order_by=None):
	rows = State.list_data.get(doctype, [])
	return [dict(r) for r in rows]


def _get_doc(doctype, name):
	return State.docs.get((doctype, name), FakeDoc({}))


class FakeDB:
	@staticmethod
	def exists(doctype_type, name):
		assert doctype_type == "DocType"
		return name in State.meta_available


class FakeUtils:
	now = staticmethod(lambda: "2026-07-29 00:00:00")
	today = staticmethod(lambda: "2026-07-29")

	@staticmethod
	def getdate(value):
		import datetime
		if isinstance(value, datetime.date):
			return value
		return datetime.date.fromisoformat(str(value)[:10])


class _FrappeThrow(Exception):
	pass


frappe_stub = types.ModuleType("frappe")
frappe_stub.get_meta = _get_meta
frappe_stub.get_list = _get_list
frappe_stub.get_doc = _get_doc
frappe_stub.db = FakeDB()
frappe_stub.throw = lambda msg, *a, **k: (_ for _ in ()).throw(_FrappeThrow(msg))
frappe_stub.utils = FakeUtils()
frappe_stub.whitelist = lambda *a, **k: (lambda f: f)
sys.modules["frappe"] = frappe_stub

import ucc_intelligence.analytics.criterion_6 as criterion_6  # noqa: E402 - stub must load first

# "Oversight Framework" and "Responsibilities" deliberately left unstubbed
# to exercise the source-unavailable path alongside the parent/child metrics.
State.meta_available = {
	"Quality Action", "Management Review", "Quality Action Resolution",
	"Strategic Planning Audit Results", "Strategic Planning Nonconformities and Corrective Actions",
}
State.list_data = {
	"Quality Action": [
		{"name": "QA-1", "resolutions": True},
		{"name": "QA-2", "resolutions": True},
		{"name": "QA-3", "resolutions": True},
	],
	"Management Review": [
		{"name": "MR-1", "table_efwt": True, "nonconformities_corrective_actions": True},
		{"name": "MR-2", "table_efwt": True, "nonconformities_corrective_actions": True},
	],
	# Schema-only stub for the child DocType's has_field checks -- never
	# actually queried via frappe.get_list, only via frappe.get_doc below.
	"Quality Action Resolution": [{"responsible": "x", "target_date": "y", "status": "z", "finding_type": "w"}],
}
State.docs = {
	("Quality Action", "QA-1"): FakeDoc({"resolutions": [
		{"status": "Open", "target_date": "2020-01-01", "finding_type": "NC", "responsible": "Bob"},
		{"status": "Completed", "target_date": "2099-01-01", "finding_type": "", "responsible": ""},
	]}),
	("Quality Action", "QA-2"): FakeDoc({"resolutions": [
		{"status": "Closed", "target_date": "2099-01-01", "finding_type": "Min. NC", "responsible": "Alice"},
	]}),
	("Quality Action", "QA-3"): FakeDoc({"resolutions": []}),
	("Management Review", "MR-1"): FakeDoc({"table_efwt": [{"name": "efwt-1"}], "nonconformities_corrective_actions": []}),
	("Management Review", "MR-2"): FakeDoc({"table_efwt": [], "nonconformities_corrective_actions": [{"name": "nc-1"}]}),
}

result = criterion_6.run(action="summary", subcriterion="6.1.1", filters={}, metric_id=None, page=1, page_size=50, row_limit=2000)
report(result.get("ok") is True, "smoke run returns ok=True")

m = {x["id"]: x for x in result["metrics"]}
report(m["c611-actions"]["status"] == "available" and m["c611-actions"]["value"] == 3, "c611-actions (all, parent-level) counts all 3 Quality Action rows")
report(m["c611-audit-records"]["status"] == "unavailable", "c611-audit-records reports unavailable, not a crash (Oversight Framework deliberately unstubbed)")
report(
	m["c611-open-resolutions"]["status"] == "available" and m["c611-open-resolutions"]["value"] == 1,
	"c611-open-resolutions (child_count, not_in) counts 1 open resolution row across all parents",
)
report(
	m["c611-overdue-resolutions"]["status"] == "available" and m["c611-overdue-resolutions"]["value"] == 1,
	"c611-overdue-resolutions (child_count, date_before_today + not_in chained) counts 1",
)
report(
	m["c611-nonconformities"]["status"] == "available" and m["c611-nonconformities"]["value"] == 2,
	"c611-nonconformities (child_count, in) counts 2 rows (one per parent)",
)
report(
	m["c611-incomplete-cap-control"]["status"] == "available" and m["c611-incomplete-cap-control"]["value"] == 1,
	"c611-incomplete-cap-control (child_any_missing) counts 1 row with a missing required field",
)
report(
	m["c611-review-audit-evidence"]["status"] == "available" and m["c611-review-audit-evidence"]["value"] == 1
	and m["c611-review-audit-evidence"]["unit"] == "parents",
	"c611-review-audit-evidence (child_parent_count) counts 1 parent (MR-1 has a table_efwt row, MR-2 doesn't)",
)
report(
	m["c611-review-nc-evidence"]["status"] == "available" and m["c611-review-nc-evidence"]["value"] == 1,
	"c611-review-nc-evidence (child_parent_count, different child field) counts 1 parent (MR-2, not MR-1)",
)

exc = {x["id"] for x in result["exceptions"]}
report("c611-open-resolutions" in exc, "exceptions list (via EXCEPTION_METRIC_IDS) includes c611-open-resolutions")

drill = criterion_6.run(action="drilldown", subcriterion="6.1.1", filters={}, metric_id="c611-nonconformities", page=1, page_size=50, row_limit=2000)
report(drill["drilldown"]["value"] == 2 and len(drill["drilldown"]["rows"]) == 2, "drilldown on a child_count metric returns the 2 matched child rows")

drill_parent = criterion_6.run(action="drilldown", subcriterion="6.1.1", filters={}, metric_id="c611-review-audit-evidence", page=1, page_size=50, row_limit=2000)
report(drill_parent["drilldown"]["value"] == 1, "drilldown on a child_parent_count metric returns the matched-parent count")

try:
	criterion_6.run(action="drilldown", subcriterion="6.1.1", filters={}, metric_id="does-not-exist", page=1, page_size=50, row_limit=2000)
	report(False, "drilldown on an unknown metric_id raises")
except _FrappeThrow:
	report(True, "drilldown on an unknown metric_id raises")

# requirement_registry: unique to Criterion 6 among criteria ported so far --
# aggregates across EVERY subcriterion's QUESTION_REGISTRY, not just the
# requested one. Requesting 6.1.1 but expecting a 6.2.1 question id proves
# this genuinely different behaviour survived the port, not the more
# common per-subcriterion-scoped behaviour every other criterion has.
registry_result = criterion_6.run(action="requirement_registry", subcriterion="6.1.1", filters={}, metric_id=None, page=1, page_size=50, row_limit=2000)
registry_ids = {r["id"] for r in registry_result["registry"]}
report(
	"q611-01" in registry_ids and "q621-01" in registry_ids and "q653-01" in registry_ids,
	"requirement_registry aggregates across all 5 subcriteria (6.1.1/6.2.1/.../6.5.3), not just the requested 6.1.1",
)

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
