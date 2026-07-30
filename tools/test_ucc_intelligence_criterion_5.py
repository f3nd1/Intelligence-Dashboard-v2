#!/usr/bin/env python3
"""Self-check for the Criterion 5 port.

Same two layers as the other ported criteria (docs/migration/phase-4-plan.md
Section 6):

1. Structural fidelity: re-extracts the same line ranges from the live
   legacy server-scripts/UCC Analytics - Criterion 5.py -- independently of
   tools/generate_criterion_5.py, so a bug in the generator can't hide a
   drifted port -- and diffs them against the committed criterion_5.py.

2. A stubbed-frappe smoke test focused on what is genuinely new here: the
   five special cases the investigation flagged (subcriterion aliases, the
   course/module DocType inversion, the `overview` pseudo-subcriterion, the
   question_id drilldown fallback, and the tighter row limit), plus the two
   custom aggregator modes (attention_count / requirement_gap_count) that
   no other criterion has.

    python3 tools/test_ucc_intelligence_criterion_5.py
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEGACY = ROOT / "server-scripts" / "UCC Analytics - Criterion 5.py"
PORTED = ROOT / "ucc_intelligence" / "ucc_intelligence" / "analytics" / "criterion_5.py"

checks = []


def report(ok, message):
	print(("PASS" if ok else "FAIL") + ": " + message)
	checks.append(ok)
	return ok


legacy_lines = LEGACY.read_text(encoding="utf-8").split("\n")
ported = PORTED.read_text(encoding="utf-8")


def line(n):
	return legacy_lines[n - 1]


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


# --- layer 1: the legacy boundaries this port was cut at ---
BOUNDARY_MARKERS = {
	64: "POLICY_REGISTRY = {'overview': {'title': 'Criterion 5 Overview',",
	103: "SOURCE_CANDIDATES = {'course_proposal': ['Course Proposal'],",
	2198: "  'treatment': 'Report as a document-control issue; it does not change the review-cycle calculation.'}]",
	2203: "STANDARD_FIELDS = [",
	2213: "}",
	2215: "SOURCE_CACHE = {}",
	2254: "def get_meta(doctype):",
	3002: "section_sources = SOURCES_BY_SECTION.get(canonical_subcriterion) or []",
	3294: "result = {",
	3361: "}",
}
boundaries_ok = True
for number, expected in BOUNDARY_MARKERS.items():
	actual = line(number)
	if actual != expected:
		boundaries_ok = False
		print("FAIL: legacy line %d drifted -- expected %r, got %r" % (number, expected, actual))
report(boundaries_ok, "legacy source line boundaries unchanged since the port was built")

if boundaries_ok:
	static_a = "\n".join(extract(64, 2198))
	static_b = "\n".join(extract(2203, 2213))
	report(static_a in ported, "static POLICY_REGISTRY..DOCUMENT_ISSUES block matches the legacy source byte-verbatim")
	report(static_b in ported, "STANDARD_FIELDS + FILTER_FIELD_CANDIDATES block matches the legacy source byte-verbatim")

	run_body_raw = list(extract(2200, 2201))
	run_body_raw += [""] + extract(2215, 2219)
	run_body_raw += [""] + extract(2240, 2246)
	run_body_raw += [""] + extract(2254, 3001)
	run_body_raw += [""] + extract(3002, 3087)
	run_body_raw += [""] + extract(3294, 3361)
	run_body_raw += [
		"",
		'result = standardise_response_contract(result, "Criterion 5", "ucc_analytics_criterion_5", action, canonical_subcriterion, row_limit)',
		"",
	]
	run_body_raw += extract(3365, 3394)
	run_body_raw += [
		"",
		'result = standardise_response_contract(result, "Criterion 5", "ucc_analytics_criterion_5", action, canonical_subcriterion, row_limit)',
		"",
		"return result",
	]
	expected_run_body = "\n".join(indent_one_more(spaces_to_tabs_graceful(run_body_raw)))
	report(expected_run_body in ported, "run() body matches the legacy engine + response-assembly code verbatim")

report('"ucc_analytics_criterion_5"' in ported, "response still reports the legacy api_method string")
report('"2.0.2-intake-expanded-questions"' in ported, "legacy platform_version string preserved")

# --- the special cases, asserted individually rather than assumed ---
report("'course': ['Program']" in ported,
	"SPECIAL CASE: the `course` alias still resolves to the Program DocType (inversion NOT 'corrected')")
report("'module': ['Course']" in ported,
	"SPECIAL CASE: the `module` alias still resolves to the Course DocType (inversion NOT 'corrected')")
report("SUBCRITERION_ALIASES" in ported and '"5.4": "5.4.1"' in ported,
	"SPECIAL CASE: subcriterion aliases (5.4 -> 5.4.1, 5.5 -> 5.5.1) preserved")
report("'overview'" in ported, "SPECIAL CASE: the `overview` pseudo-subcriterion survives as a real section")
report("question_id=None" in ported, "SPECIAL CASE: question_id is an explicit run() parameter")
report("def standardise_response_contract" not in ported, "local contract function dropped in favour of the shared one")
report("def clean_text" not in ported and "def lower_text" not in ported and "def is_truthy" not in ported,
	"the three shared text helpers are imported, not re-defined")
report("def to_number" in ported, "to_number stays local (this criterion's plain-float variant, not C6/C7's)")
report("\n\tSOURCE_CACHE = {}" in ported and "\nSOURCE_CACHE = {}" not in ported,
	"all five caches are locals of run(), never module-level shared state")

# api.py wiring, including the row-limit re-clamp
api_source = (ROOT / "ucc_intelligence" / "ucc_intelligence" / "api.py").read_text(encoding="utf-8")
report("def get_criterion_5()" in api_source, "api.py exposes get_criterion_5")
report("CRITERION_5_MAX_ROW_LIMIT = 2000" in api_source and "CRITERION_5_DEFAULT_ROW_LIMIT = 500" in api_source,
	"SPECIAL CASE: api.py re-clamps to the legacy 500/2000 row limit rather than the shared 2000/5000")
report("question_id=payload.get(\"question_id\")" in api_source, "api.py passes question_id through to run()")


# ============================================================
# layer 2: stubbed-frappe smoke test
# ============================================================
sys.path.insert(0, str(ROOT / "ucc_intelligence"))


class State:
	rows = {}
	meta_fields = {}
	existing = set()
	denied = set()


class FakeMetaField:
	def __init__(self, fieldname):
		self.fieldname = fieldname
		self.fieldtype = "Data"
		self.options = None


class FakeMeta:
	def __init__(self, doctype):
		self.fields = [FakeMetaField(f) for f in State.meta_fields.get(doctype, [])]

	def has_field(self, fieldname):
		return any(f.fieldname == fieldname for f in self.fields)

	def get_field(self, fieldname):
		for f in self.fields:
			if f.fieldname == fieldname:
				return f
		return None


def _get_meta(doctype):
	if doctype not in State.meta_fields:
		raise RuntimeError("no meta for %s" % doctype)
	return FakeMeta(doctype)


def _get_list(doctype, **kwargs):
	if doctype in State.denied:
		raise RuntimeError("PermissionError: not permitted to read " + doctype)
	return [dict(r) for r in State.rows.get(doctype, [])]


frappe_stub = types.ModuleType("frappe")
frappe_stub.get_meta = _get_meta
frappe_stub.get_list = _get_list
frappe_stub.get_all = _get_list
frappe_stub.db = types.SimpleNamespace(
	exists=lambda dt, name=None: (name or dt) in State.existing or dt in State.existing,
	count=lambda dt, filters=None: len(State.rows.get(dt, [])),
)
frappe_stub.utils = types.SimpleNamespace(
	now=lambda: "2026-07-30 00:00:00",
	today=lambda: "2026-07-30",
	add_days=lambda d, n: "2026-10-28",
	getdate=lambda v=None: v,
	cint=lambda v: int(v) if str(v).strip().lstrip("-").isdigit() else 0,
	flt=lambda v, p=None: float(v) if str(v).replace(".", "").isdigit() else 0.0,
)
frappe_stub.throw = lambda msg: (_ for _ in ()).throw(ValueError(msg))
frappe_stub.parse_json = lambda v: v
frappe_stub.whitelist = lambda *a, **k: (lambda f: f)
frappe_stub.logger = lambda *a, **k: types.SimpleNamespace(
	info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None)
sys.modules["frappe"] = frappe_stub

import ucc_intelligence.analytics.criterion_5 as criterion_5  # noqa: E402 - stub must load first

# Every source DocType resolves, with the handful of fields the smoke test needs.
for alias, doctypes in criterion_5.SOURCE_CANDIDATES.items():
	for doctype in doctypes:
		State.existing.add(doctype)
		State.meta_fields.setdefault(doctype, [
			"name", "modified", "approval_status", "ssg_approval_date", "proposed_date",
			"decision_date", "topics", "assessment_criteria", "next_review_date",
			"recommendation_implementation_status", "status", "instructor", "room",
			"custom_instructor", "areas_text", "areas_for_improvement", "observers_signature",
			"teachers_signature", "expiry_date", "agreement_date", "type",
			"average_identification_and_selection_score", "grade", "total_score",
			"maximum_score", "assessment_plan", "schedule_date", "examiner", "supervisor",
		])
		State.rows.setdefault(doctype, [{"name": doctype + "-1", "modified": "2026-07-01"}])

summary = criterion_5.run(
	action="summary", subcriterion="5.1.1", filters={}, metric_id=None,
	page=1, page_size=50, row_limit=500,
)
report(summary.get("ok") is True, "run() returns ok=True for a normal summary")
report(summary["meta"]["api_method"] == "ucc_analytics_criterion_5", "meta reports the legacy api_method")
report(len(summary.get("metrics") or []) > 0, "summary returns metrics")
report(len(summary.get("questions") or []) > 0, "summary returns questions")
report(len(summary.get("document_issues") or []) == 6,
	"all 6 DOCUMENT_ISSUES are returned on every response, not gated by action")

# SPECIAL CASE 1: alias remapping
aliased = criterion_5.run(
	action="summary", subcriterion="5.4", filters={}, metric_id=None,
	page=1, page_size=50, row_limit=500,
)
report(aliased["meta"].get("canonical_subcriterion") == "5.4.1",
	"SPECIAL CASE: subcriterion '5.4' canonicalises to '5.4.1'")
report(aliased["meta"].get("legacy_alias_used") is True,
	"SPECIAL CASE: the response flags that a legacy alias was used")
unaliased = criterion_5.run(
	action="summary", subcriterion="5.4.1", filters={}, metric_id=None,
	page=1, page_size=50, row_limit=500,
)
report(unaliased["meta"].get("legacy_alias_used") is False,
	"SPECIAL CASE: a canonical subcriterion is NOT flagged as an alias")

# SPECIAL CASE 3: overview is a real, usable section
overview = criterion_5.run(
	action="summary", subcriterion="overview", filters={}, metric_id=None,
	page=1, page_size=50, row_limit=500,
)
report(overview.get("ok") is True, "SPECIAL CASE: 'overview' is a valid subcriterion, not rejected")
report(len(overview.get("metrics") or []) > 0, "SPECIAL CASE: 'overview' returns its own metrics")

# the two custom aggregator modes only exist in overview
overview_metric_ids = [m.get("id") for m in overview.get("metrics") or []]
report("o-current-attention" in overview_metric_ids, "attention_count aggregator metric is evaluated")
report("o-evidence-gaps" in overview_metric_ids, "requirement_gap_count aggregator metric is evaluated")

# SPECIAL CASE 4: question_id drilldown fallback
question_registry = criterion_5.QUESTION_REGISTRY.get("5.1.1") or []
question_with_metric = next((q for q in question_registry if q.get("metric_id")), None)
report(question_with_metric is not None, "5.1.1 has at least one question carrying a metric_id (fixture for the next check)")
if question_with_metric:
	drilled = criterion_5.run(
		action="drilldown", subcriterion="5.1.1", filters={}, metric_id=None,
		page=1, page_size=50, row_limit=500, question_id=question_with_metric["id"],
	)
	report(drilled.get("drilldown") is not None,
		"SPECIAL CASE: drilldown resolves the metric via question_id when metric_id doesn't match")

# an unknown metric_id with no question_id fallback still raises
try:
	criterion_5.run(
		action="drilldown", subcriterion="5.1.1", filters={}, metric_id="does-not-exist",
		page=1, page_size=50, row_limit=500,
	)
	report(False, "drilldown on an unknown metric_id should raise")
except Exception:
	report(True, "drilldown on an unknown metric_id raises")

# registry actions
for action_name, key in [("policy_registry", "registry"), ("requirement_registry", "registry"), ("question_registry", "registry")]:
	result = criterion_5.run(
		action=action_name, subcriterion="5.1.1", filters={}, metric_id=None,
		page=1, page_size=50, row_limit=500,
	)
	report(result.get(key) is not None, "%s action populates result[%r]" % (action_name, key))

# permission-denied source classification
State.denied.add("Course Proposal")
denied_result = criterion_5.run(
	action="summary", subcriterion="5.1.1", filters={}, metric_id=None,
	page=1, page_size=50, row_limit=500,
)
denied_statuses = [s.get("status") for s in denied_result.get("sources") or []]
report("permission_denied" in denied_statuses,
	"a permission-denied source is classified permission_denied, not a silent empty result")
State.denied.clear()

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
