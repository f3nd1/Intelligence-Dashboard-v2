#!/usr/bin/env python3
"""ONE command, ONE pass/fail report, for the whole platform.

    python3 tools/test_end_to_end.py

WHAT THIS IS
The offline end-to-end gate. It runs every self-check in the repository,
then adds cross-cutting assertions that no individual suite covers because
each one only sees its own module -- chiefly the Phase 13 cutover: that
NOTHING in the running app reaches a legacy Server Script any more.

WHAT THIS IS NOT
It does not touch a bench, a database or OpenAI. Two things therefore
cannot be settled here, and both have their own bench script:

  docs/migration/scripts/verify_cutover.py
      disables every Server Script on a real site and re-exercises every
      surface. That is the acceptance test for "the app stands alone";
      this file proves the code no longer NAMES a Server Script, which is
      necessary but not sufficient.

  docs/migration/scripts/verify_ai_live.py
      one real OpenAI call, AI on vs AI off.

Exit code 0 = everything green.
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "ucc_intelligence" / "ucc_intelligence"
PAGE = APP / "sophia" / "page" / "sophia_analytics" / "sophia_analytics.js"

# Known-failing and NOT ours: targets a function deliberately removed from
# server-scripts/ in 30db7af (2026-07-25), before this migration's baseline.
# server-scripts/ is historical reference and must not be edited, so this
# cannot be fixed without breaking that rule. Excluded explicitly rather
# than silently, so it stays visible.
KNOWN_UNFIXABLE = {"test_drop_server_message.py"}

results = []


def report(ok, message, detail=""):
	results.append((bool(ok), message, detail))
	print("%s  %s%s" % ("PASS" if ok else "FAIL", message, ("\n        " + detail) if detail and not ok else ""))
	return bool(ok)


def section(title):
	print("\n" + "=" * 74)
	print(title)
	print("=" * 74)


# ===========================================================================
section("1. Every module self-check")
# ===========================================================================
suites = sorted(
	[p for p in (ROOT / "tools").glob("test_*.py") if p.name != "test_end_to_end.py"]
	+ list((ROOT / "tools").glob("test_*.js"))
	+ list((APP / "tests").glob("test_*.js"))
)
for suite in suites:
	if suite.name in KNOWN_UNFIXABLE:
		print("SKIP  %s (known-unfixable, targets historical server-scripts/)" % suite.name)
		continue
	runner = ["node", str(suite)] if suite.suffix == ".js" else [sys.executable, str(suite)]
	proc = subprocess.run(runner, capture_output=True, text=True, cwd=str(ROOT))
	tail = (proc.stdout or proc.stderr or "").strip().splitlines()
	report(proc.returncode == 0, "%-46s %s" % (suite.name, tail[-1] if tail else ""),
		"\n        ".join([line for line in tail if line.startswith("FAIL")][:6]))


# ===========================================================================
section("2. PHASE 13 CUTOVER -- no runtime dependency on any Server Script")
# ===========================================================================
page_source = PAGE.read_text(encoding="utf-8")

config_match = re.search(r"const CONFIG=(\{.*?\});\n", page_source, re.S)
report(bool(config_match), "the dashboard CONFIG block is present")
config = json.loads(config_match.group(1)) if config_match else {}

for key in sorted(config):
	method = config[key].get("apiMethod") or ""
	report(method.startswith("ucc_intelligence.api."),
		"%s calls the app, not a Server Script (%s)" % (key, method or "MISSING"),
		"still points at %r" % method)

# Every frappe.call in the page must name an app method. A Server Script is
# called by its bare name, so anything without the app prefix is suspect.
called = set(re.findall(r'method:\s*"([^"]+)"', page_source))
for method in sorted(called):
	report(method.startswith("ucc_intelligence.") or method.startswith("frappe."),
		"frappe.call target %r is an app or framework method" % method,
		"looks like a Server Script name")

LEGACY_NAMES = [
	"ucc_analytics_criterion_1", "ucc_analytics_criterion_2", "ucc_analytics_criterion_3",
	"ucc_analytics_criterion_4", "ucc_analytics_criterion_5", "ucc_analytics_criterion_6",
	"ucc_analytics_criterion_7", "ucc_dashboard_access", "ucc_ask_student_journey",
	"ucc_ask_recruitment_agent", "ucc_ask_quality_action", "ucc_analytics_bootstrap",
	"ucc_analytics_drilldown", "ucc_shared_record_search", "ucc_shared_diagnostics",
]


def strip_comments_and_strings(source, is_python):
	"""A legacy name inside a comment or a docstring is documentation, not a
	dependency -- the whole codebase explains what it was ported FROM. Only
	executable references count."""
	out = []
	for line in source.splitlines():
		stripped = line.strip()
		if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
			continue
		out.append(line)
	text = "\n".join(out)
	if is_python:
		text = re.sub(r'"""[\s\S]*?"""', "", text)
	return text


runtime_hits = []
for path in list(APP.rglob("*.py")) + list(APP.rglob("*.js")) + list(APP.rglob("*.json")):
	if "__pycache__" in str(path):
		continue
	body = strip_comments_and_strings(path.read_text(encoding="utf-8", errors="replace"), path.suffix == ".py")
	for name in LEGACY_NAMES:
		# A CALL or a method reference -- not a label inside a response dict,
		# which is metadata the app stamps over anyway.
		for pattern in ('method:"%s"' % name, 'method: "%s"' % name, '"method": "%s"' % name,
				"frappe.call('%s'" % name, 'frappe.call("%s"' % name):
			if pattern in body:
				runtime_hits.append("%s -> %s" % (path.relative_to(ROOT), pattern))
report(not runtime_hits, "no file in the app CALLS a legacy Server Script method",
	"\n        ".join(runtime_hits))

report("ucc_dashboard_access" not in re.findall(r'method:\s*"([^"]+)"', page_source),
	"dashboard access comes from the app, not the Server Script")

# The legacy directories must still EXIST (historical reference) but nothing
# in the app may import or read them.
report((ROOT / "server-scripts").is_dir(), "server-scripts/ is still present as historical reference")
report((ROOT / "custom-html-block").is_dir(), "custom-html-block/ is still present as historical reference")
app_source = "\n".join(
	p.read_text(encoding="utf-8", errors="replace")
	for p in list(APP.rglob("*.py")) + list(APP.rglob("*.js")) if "__pycache__" not in str(p)
)
for legacy_dir in ("server-scripts/", "custom-html-block/"):
	report(('open("%s' % legacy_dir) not in app_source and ("Path('%s" % legacy_dir) not in app_source,
		"the app never reads %s at runtime" % legacy_dir)


# ===========================================================================
section("3. Chart layer: Insights charts, picked per tab")
# ===========================================================================
# The 222 fixed chart boxes are gone -- the table that declared them, the
# 113-entry registry behind them, the fifteen hand-rolled SVG renderers, and
# the two card renderers. A tab now starts empty with a "+ Add chart" button.
#
# These checks are about the two things that could go quietly wrong: dead code
# left behind pretending to be deleted, and a picker that hands someone a chart
# they were never allowed to read.
sys.path.insert(0, str(ROOT / "ucc_intelligence"))
import types  # noqa: E402
sys.modules.setdefault("frappe", types.ModuleType("frappe"))

TAB_CHARTS = APP / "analytics" / "tab_charts.py"
tab_charts_source = TAB_CHARTS.read_text(encoding="utf-8")
api_source = (APP / "api.py").read_text(encoding="utf-8")

# --- DELETED, not merely unreached -----------------------------------------
for gone in ("chart_registry.py", "chart_definitions.py", "chart_service.py"):
	report(not (APP / "analytics" / gone).exists(), "%s is deleted from the app" % gone)
for gone in ("build_insights_charts_from_specs.py", "build_placeholder_insights_charts.py"):
	report(not (ROOT / "docs" / "migration" / "scripts" / gone).exists(),
		"%s is deleted -- it existed only to author registry charts" % gone)

# Comments legitimately explain what was removed, so code only.
page_code = "\n".join(l for l in page_source.splitlines() if not l.strip().startswith("//"))
for symbol, what in [
	("LIVE_VISUAL_EXPANSION", "the 209-box table"),
	("liveChartCardMarkup", "the chart-card markup"),
	("ensureLiveSectionCards", "the card-grid mounting"),
	("renderLiveChartCardNow", "the card renderer"),
	("renderInsightsChartInto", "the old per-box Insights fetch"),
	("paintChartEmpty", "the blank-box state"),
	("chartForLive", "the hand-rolled SVG dispatcher"),
	("registerChartPlugin", "the SVG plugin registry"),
	("metricRows", "the criterion-API row extractor"),
	("chartDefinitions", "the chart manifest"),
	("applyInsightsBadge", "the migration badge"),
	("openRecords", "the card drill-down"),
]:
	report(symbol not in page_code, "%s is gone from the page (%s)" % (symbol, what))
report('"charts":[{' not in page_source, "no chart box is declared anywhere in CONFIG")
report("get_chart_definitions" not in api_source and "get_chart_data" not in api_source,
	"the registry's two endpoints are removed from the API")

# --- WHAT REPLACED THEM ----------------------------------------------------
report(TAB_CHARTS.exists(), "analytics/tab_charts.py holds the whole per-tab chart layer")
for method in ("search_insights_charts", "get_tab_charts", "add_tab_chart",
		"remove_tab_chart", "get_tab_chart_data", "set_tab_chart_size", "set_tab_intro",
		"set_tab_question"):
	report("def %s(" % method in api_source and "ucc_intelligence.api.%s" % method in page_source,
		"%s is whitelisted and called by the page" % method)
report('data-add-chart' in page_source and "+ Add chart" in page_source,
	'every tab area carries a "+ Add chart" button')
report("data-remove-chart" in page_source and "removeTabChart" in page_source,
	"each embedded chart carries a remove control")
report("openChartPicker" in page_source and "data-chart-picker-search" in page_source,
	"the picker is a searchable list, not a free-text chart id")

# --- PER TAB, AND PERSISTED ------------------------------------------------
report('criterion+"::"+tab' in page_source or 'criterionId+"::"+tab' in page_source,
	"chart state is keyed by criterion AND tab, so tabs do not share charts")
# --- INSTITUTION-WIDE, NOT PER USER (2026-08-02, Felix) ---------------------
# Sophia is an institutional dashboard used as EduTrust evidence, not a
# personal workspace: what one person configures is what the auditor sees. The
# two assertions that used to be here required the opposite (frappe.defaults,
# no new DocType) and are deliberately reversed.
report('"%s::%s" % (criterion, tab)' in tab_charts_source,
	"the stored key is criterion::tab, with NO user in it")
report("set_user_default" not in tab_charts_source,
	"nothing is written to the per-user store any more")
report((APP / "sophia" / "doctype" / "ucc_analytics_tab" / "ucc_analytics_tab.json").exists(),
	"UCC Analytics Tab is the shared record -- one per criterion+tab")

tab_doctype = json.loads(
	(APP / "sophia" / "doctype" / "ucc_analytics_tab" / "ucc_analytics_tab.json").read_text(encoding="utf-8"))
report(tab_doctype.get("autoname") == "format:{criterion}::{tab}",
	"autoname makes the name the key, so a duplicate configuration cannot exist")
fieldnames = [field["fieldname"] for field in tab_doctype["fields"]]
for fieldname, what in [("charts", "the charts"), ("intro", "the tab intro"),
		("hidden_questions", "the hidden questions")]:
	report(fieldname in fieldnames, "%s is stored in UCC Analytics Tab.%s" % (what, fieldname))
report(tab_doctype.get("issingle") == 0,
	"it is one record per tab, not a Single holding everything")

# The edit gate is the DocType's own write permission -- the same shape
# UCC Dashboard Access uses, so widening it is a Desk change.
report('frappe.has_permission(CONFIG_DOCTYPE, "write")' in tab_charts_source,
	"editing is gated on write permission on the config DocType, not a hardcoded role")
report(tab_charts_source.count("_require_edit()") >= 6,
	"every write endpoint asks first (5 endpoints + the definition)")
report('"can_edit": can_edit()' in tab_charts_source,
	"the response tells the page whether to show the edit controls at all")
report("can_edit" in page_source and "state.canEdit" in page_source,
	"and the page reads it rather than assuming everyone may edit")

# Nothing already configured may be lost.
patch = APP / "patches" / "v1_0" / "migrate_tab_config_to_shared.py"
report(patch.exists(), "a patch migrates the existing per-user records")
patch_source = patch.read_text(encoding="utf-8")
report("LEGACY_DEFAULTS_PREFIX" in patch_source,
	"the patch reads the old per-user keys by their real prefix")
report("if frappe.db.exists(CONFIG_DOCTYPE, name):" in patch_source and "continue" in patch_source,
	"and is idempotent -- a re-run never overwrites a shared record someone has since edited")
report("ucc_intelligence.patches.v1_0.migrate_tab_config_to_shared"
	in (APP / "patches.txt").read_text(encoding="utf-8"),
	"the patch is registered in patches.txt, so bench migrate runs it")

# --- PERMISSIONS -----------------------------------------------------------
# Three gates. Each one is a single line in tab_charts.py, so each is asserted.
report('access.build_response()["criteria"].get(criterion)' in tab_charts_source,
	"gate 1: the criterion tab must be visible to this user (ucc_dashboard_access)")
report("frappe.get_list(" in tab_charts_source and "frappe.get_all(" not in tab_charts_source,
	"gate 2: the picker lists through get_list, which APPLIES permissions (get_all does not)")
report('doc.check_permission("read")' in tab_charts_source,
	"gate 3: every execute re-checks read permission at that moment")
add_body = tab_charts_source[tab_charts_source.index("def add("):tab_charts_source.index("def remove(")]
report("readable([chart])" in add_body and add_body.index("readable([chart])") < add_body.index("_stored("),
	"a chart is permission-checked BEFORE it is stored, not after")
get_body = tab_charts_source[tab_charts_source.index("def get_tab("):tab_charts_source.index("def add(")]
report("readable([item[\"chart\"] for item in config[\"charts\"]])" in get_body,
	"stored ids are re-filtered through permissions on every read -- an id is a preference, not a grant")
report("is_public" not in tab_charts_source,
	"the public-dashboard mechanism is never used -- it applies no permissions at all")
report('CHART_DOCTYPE = "Insights Query v3"' in tab_charts_source,
	"only the record type we can execute AND permission-check is offered")

# Input validation: a tab key becomes part of a defaults key, so it cannot be
# free text, and a criterion cannot be invented.
report("access.CRITERION_KEYS" in tab_charts_source, "the criterion is checked against the real list")
report("TAB_CHARACTERS" in tab_charts_source, "the tab key is character-constrained before it becomes a stored key")
report("MAX_PER_TAB" in tab_charts_source, "a tab is bounded, so one person cannot grow an unbounded stored value")

# --- WHAT MUST NOT HAVE MOVED ----------------------------------------------
# Felix's requirement 4: charts only. These are the neighbours.
for kept, what in [
	("renderQa", "Management Questions and Data-Based Answers"),
	("extendedQuestionRows", "the Q&A row builder"),
	("renderSources", "Source Availability"),
	("renderQuality", "Data Quality Checks"),
]:
	report(kept in page_source, "untouched: %s" % what)
report("Management Questions and Data-Based Answers" in page_source,
	"the Q&A panel markup is unchanged")

# --- WHAT THE MOVE TO INSIGHTS MADE OBSOLETE (2026-08-01, Felix) ------------
# Three surfaces on every criterion tab read the criterion engine's own
# catalogue and could not survive charts moving to Insights. Two assertions
# above used to require the opposite; they are deliberately reversed, and the
# reason is here rather than in a commit nobody will read.
#
#   the page-level filter bar -- an embedded chart is a live view of a SAVED
#       Insights query. This page cannot re-filter it, and pretending to
#       (a control that changes nothing) is worse than not offering it. A
#       filtered view is a second Insights chart, built in Insights.
#   the readiness strip -- "Criterion N live analytics active · X of X sources
#       available". The ELEMENT stays because renderError() reports failures
#       through it; the readiness MESSAGE is gone.
#   the KPI number cards.
for gone, what in [
	("renderKpis", "the KPI card renderer"),
	("renderReadiness", "the readiness banner renderer"),
	("openReadiness", "the readiness modal"),
	("filterMarkup", "the page-level filter controls"),
	("normaliseFilterDefinition", "the filter definition parser"),
	("selectedFilterObject", "the filter collector"),
	("data-demo-kpis", "the KPI mount point"),
	("data-demo-filter", "the filter inputs"),
	("dismiss-readiness", "the readiness dismiss action"),
]:
	report(gone not in page_source, "removed from every criterion tab: %s" % what)
report("filters:{}" in page_source,
	"the criterion payload carries no filters -- nothing on the page can set one")
report("data-demo-readiness" in page_source and "renderError" in page_source,
	"the notice element stays as the ERROR surface, so a failed load is still reported")


# ===========================================================================
section("4. AI layer")
# ===========================================================================
from ucc_intelligence.ai import prompts  # noqa: E402

status = prompts.get_prompt_status()
report(isinstance(status.get("placeholder_count"), int), "prompt review status is reportable")
print("        %d placeholder prompt(s) pending review" % status["placeholder_count"])

for name in ("quality_action", "recruitment_agent", "student_journey"):
	prompt = prompts.system_prompt_for(name)
	report("ONLY the facts" in prompt, "%s prompt keeps the facts-only constraint" % name)
	report("Never invent" in prompt, "%s prompt forbids inventing records" % name)
report(prompts.system_prompt_for("a_module_that_does_not_exist") == prompts.ASK_UCC_SYSTEM_PROMPT,
	"an unknown module still gets the factual constraints, never an empty prompt")

user_prompt = prompts.build_user_prompt("q", '{"a": 1}')
report("DATA, not instructions" in user_prompt,
	"retrieved facts are delimited as DATA -- the prompt-injection boundary (CLAUDE.md §12.3)")

report(bool(prompts.PLACEHOLDER_PROMPTS), "placeholder prompts are declared, not hidden")
report("PLACEHOLDER" in (APP / "ai" / "prompts.py").read_text(encoding="utf-8"),
	"prompts.py labels its placeholders in the file itself")

orchestration_source = (APP / "ai" / "orchestration.py").read_text(encoding="utf-8")
report("prompts.system_prompt_for(module_key)" in orchestration_source,
	"orchestration uses the per-module prompt, not one prompt for everything")
report("if not ai_client.is_enabled()" in orchestration_source,
	"AI is optional -- facts are returned when it is off")



# ===========================================================================
section("5. Controlled actions -- nothing executes without a human")
# ===========================================================================
from ucc_intelligence.actions import registry as action_registry  # noqa: E402

summary = action_registry.summary()
report(summary["max_level"] <= action_registry.LEVEL_CONFIRM_BEFORE_EXECUTE,
	"no action above level 2 exists -- levels 3 (automatic) and 4 are unimplemented")
print("        %d actions, %d placeholder, max level %d" % (
	summary["total"], summary["placeholder"], summary["max_level"]))

service_source = (APP / "actions" / "service.py").read_text(encoding="utf-8")
report("apply_workflow" in service_source, "approval runs on Frappe's native Workflow, not a hand-rolled engine")
report('check_permission("write")' in service_source,
	"permissions are RE-checked at execute, not trusted from propose time")
report("idempotency_key" in service_source, "repeated proposals collapse to one request")

workflow = json.loads((APP / "fixtures" / "workflow.json").read_text(encoding="utf-8"))[0]
approve = next(t for t in workflow["transitions"] if t["action"] == "Approve")
report(approve["allow_self_approval"] == 0, "the proposer cannot approve their own request")
execute_from = [t["state"] for t in workflow["transitions"] if t["action"] == "Execute"]
report(execute_from == ["Approved"], "Execute is reachable ONLY from Approved")

# ===========================================================================
section("6. Monitoring -- all 7 CLAUDE.md use cases, scheduled")
# ===========================================================================
from ucc_intelligence.monitoring import engine as monitoring_engine  # noqa: E402
from ucc_intelligence.monitoring import rule_registry as monitoring_rules  # noqa: E402

report(len(monitoring_rules.RULES) >= 7, "all seven §11 use cases have a rule (%d)" % len(monitoring_rules.RULES))
placeholders = monitoring_rules.placeholder_rules()
print("        %d rule(s) on PLACEHOLDER field mappings: %s" % (len(placeholders), placeholders))
for rule_id in placeholders:
	report(monitoring_rules.RULES[rule_id]["version"].endswith("placeholder"),
		"%s declares a placeholder version, so a finding traces to provisional logic" % rule_id)
covered = set()
for cadence in ("daily", "weekly", "quarterly"):
	due = monitoring_engine.rules_due(cadence)
	covered.update(due)
	print("        %-10s %s" % (cadence, due))
report(covered == set(monitoring_rules.RULES),
	"EVERY rule is on a schedule -- none is on-demand only",
	"unscheduled: %s" % sorted(set(monitoring_rules.RULES) - covered))
for entry in ("run_daily", "run_weekly", "run_quarterly"):
	report(hasattr(monitoring_engine, entry), "scheduler entry point %s() exists" % entry)
hooks_doc = (ROOT / "docs" / "migration" / "hooks-reference.md").read_text(encoding="utf-8")
report("scheduler_events" in hooks_doc and "run_daily" in hooks_doc,
	"the hooks.py entries needed to actually schedule it are documented")

# ===========================================================================
section("7. Document knowledge -- full ingest path")
# ===========================================================================
from ucc_intelligence.knowledge import ingestion  # noqa: E402

for function in ("register_source", "index_source", "supersede", "extract_text", "reindex_stale"):
	report(hasattr(ingestion, function), "ingestion.%s() exists" % function)
samples = sorted((ROOT / "docs" / "samples" / "knowledge").glob("SAMPLE-*.md"))
report(len(samples) >= 2, "sample documents exist so the flow is testable (%d)" % len(samples))
for path in samples:
	report("SAMPLE" in path.read_text(encoding="utf-8").splitlines()[0].upper(),
		"%s is labelled SAMPLE on its first line" % path.name)
ingestion_source = (APP / "knowledge" / "ingestion.py").read_text(encoding="utf-8")
report("UNSUPPORTED_NOTE" in ingestion_source,
	"an unsupported file type is refused with an explanation, never half-extracted")
report((ROOT / "docs" / "migration" / "scripts" / "load_sample_knowledge.py").exists(),
	"a bench script loads the samples and retrieves them back")



# ===========================================================================
section("8. Installability -- can Frappe load the app at all?")
# ===========================================================================
# This section used to start at the DocTypes. It should have started one step
# earlier: on 2026-08-01 the bench failed on `No module named
# 'ucc_intelligence.hooks'` -- the app's own manifest had never been in this
# repository, so a mirroring sync deleted it from the bench and Frappe could
# not load the app at all. Every suite here checked what the code DOES; none
# checked that it could be reached. tools/test_app_loads.py is that check and
# runs in section 1 with the rest; these are the cross-cutting parts.
for required, why in [
	("ucc_intelligence/hooks.py", "frappe.get_hooks() imports it before any app code"),
	("ucc_intelligence/modules.txt", "the module list installs the DocTypes and the Page"),
	("ucc_intelligence/patches.txt", "bench migrate reads it on every run"),
	("pyproject.toml", "bench setup requirements and any reinstall need it"),
]:
	report((APP.parent / required).exists(),
		"load-critical file present: %s -- %s" % (required, why),
		"MISSING -- bench migrate aborts for EVERY app on the bench, not just this one")

# The app-export branch is what the bench actually receives. Anything
# load-critical must sit at a path that survives `git subtree split
# --prefix=ucc_intelligence`, i.e. under ucc_intelligence/ in this repo.
report((ROOT / "ucc_intelligence" / "pyproject.toml").exists(),
	"pyproject.toml is INSIDE ucc_intelligence/, so it reaches app-export's root",
	"a copy at the repo root would never reach the bench")


# ===========================================================================
section("8b. Installability -- every DocType can actually migrate")
# ===========================================================================
# bench migrate aborted at 38% on a missing controller module. Checked here
# structurally so the next omission fails in a second, not half way through
# a migration. test_doctype_completeness.py holds the detail; this is the
# headline.
doctype_dirs = sorted(d for d in (APP / "sophia" / "doctype").iterdir()
	if d.is_dir() and d.name != "__pycache__")
incomplete = [d.name for d in doctype_dirs
	if not (d / ("%s.py" % d.name)).exists() or not (d / "__init__.py").exists()
	or not (d / ("%s.json" % d.name)).exists()]
report(not incomplete, "every DocType has json + __init__.py + controller (%d DocTypes)" % len(doctype_dirs),
	"incomplete: %s -- bench migrate will abort on these" % incomplete)


# ===========================================================================
section("9. Bench scripts exist for what cannot be proved offline")
# ===========================================================================
for name, purpose in [
	("verify_cutover.py", "Server Scripts disabled, every surface re-exercised"),
	("verify_ai_live.py", "one real OpenAI call, AI on vs off"),
	("build_admission_intelligence_embed.py", "build + permission-test the real Insights charts"),
	("load_sample_knowledge.py", "load + retrieve the sample documents"),
]:
	path = ROOT / "docs" / "migration" / "scripts" / name
	report(path.exists(), "bench script present: %-42s (%s)" % (name, purpose))


# ===========================================================================
passed = sum(1 for ok, _, _ in results if ok)
print("\n" + "=" * 74)
print("%s -- %d/%d checks across %d suites" % (
	"PASS" if passed == len(results) else "FAIL", passed, len(results), len(suites)))
if passed != len(results):
	print("\nFailures:")
	for ok, message, detail in results:
		if not ok:
			print("  - %s" % message)
			if detail:
				print("      %s" % detail)
else:
	print("\nOffline gate is green. Two things still need a bench:")
	print("  bench console -> docs/migration/scripts/verify_cutover.py   (the real cutover proof)")
	print("  bench console -> docs/migration/scripts/verify_ai_live.py   (the real AI proof)")
print("=" * 74)
raise SystemExit(0 if passed == len(results) else 1)
