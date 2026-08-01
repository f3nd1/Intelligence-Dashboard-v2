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
section("3. Chart layer runs through Insights")
# ===========================================================================
sys.path.insert(0, str(ROOT / "ucc_intelligence"))
import types  # noqa: E402
sys.modules.setdefault("frappe", types.ModuleType("frappe"))
from ucc_intelligence.analytics import chart_registry  # noqa: E402

counts = chart_registry.counts()
report(counts["total"] >= 107, "every chart in the platform is registered (%d)" % counts["total"])
report(counts["real"] >= 6, "at least the 6 bench-verified admission charts are REAL (%d)" % counts["real"])
print("        real=%(real)d authored=%(authored)d computed=%(computed)d placeholder=%(placeholder)d total=%(total)d" % counts)

per = chart_registry.per_criterion()
print("\n        %-14s %6s %5s %9s %10s %12s" % ("criterion", "total", "real", "authored", "computed", "unspecified"))
for key, row in per.items():
	print("        %-14s %6d %5d %9d %10d %12d" % (
		key, row["total"], row["real"], row["authored"], row["computed"], row["unspecified"]))
	report(row["unspecified"] == 0,
		"%s: every chart is classified (real / authored / computed), none left unexamined" % key,
		"%d unclassified" % row["unspecified"])

report(counts["placeholder"] == 0,
	"no chart is left as a bare placeholder -- every one is real, authored or computed")

# An authored chart must carry a runnable spec, not just a promise.
for chart_id, spec in chart_registry.CHARTS.items():
	if spec["status"] != "authored":
		continue
	detail = spec.get("spec") or {}
	if not (detail.get("doctype") and detail.get("dimension_candidates")):
		report(False, "authored chart %r carries a complete spec" % chart_id, str(detail))
		break
else:
	report(True, "every AUTHORED chart carries a doctype + dimension candidates the builder can resolve")

# The first bench run rejected 17 of 30 specs on a single guessed field name.
# Candidate lists are the fix; one candidate is the old failure mode.
single_guess = [c for c, s in chart_registry.CHARTS.items()
	if s["status"] == "authored" and len(s["spec"]["dimension_candidates"]) < 2]
report(not single_guess,
	"every authored chart offers MULTIPLE dimension candidates, resolved against the live schema",
	"single-guess charts: %s" % single_guess[:5])

# --- docstatus must be UNREACHABLE as a dimension ------------------------
# The second bench run promoted nothing by accident, but ten charts had
# resolved to `docstatus` -- Frappe's internal draft/submitted flag -- and
# rendered a single bar labelled "0". A chart that looks like analysis and
# isn't is the exact failure class this project keeps guarding against.
docstatus_specs = [c for c, spec in chart_registry.CHARTS.items()
	if spec.get("spec") and "docstatus" in spec["spec"]["dimension_candidates"]]
report(not docstatus_specs, "NO chart offers docstatus as a dimension candidate",
	"still offering it: %s" % docstatus_specs[:5])

builder = (ROOT / "docs" / "migration" / "scripts" / "build_insights_charts_from_specs.py").read_text(encoding="utf-8")
report("BANNED_DIMENSIONS" in builder and '"docstatus"' in builder.split("BANNED_DIMENSIONS")[1][:200],
	"the builder BANS docstatus outright, so a stray spec cannot reintroduce it")
report('ALWAYS_PRESENT = {"name", "creation", "modified"}' in builder,
	"docstatus is no longer in the always-present list -- that bypass is what let it win")
report("single_bar" in builder,
	"the builder flags single-category results, which is what a wrong dimension looks like")
report("rows_to_chart_series(rows)" in builder,
	"the builder previews through the SAME normaliser the dashboard uses, so blanks read as 'Not specified'")

# Promotion must stay a deliberate, reviewed act.
verified = chart_registry.BENCH_VERIFIED_CHARTS
report(len(verified) == 16, "16 charts are bench-verified: 6 admission + 10 reviewed on 2026-08-01 (%d)" % len(verified))
authored_left = [c for c, s in chart_registry.CHARTS.items() if s["status"] == "authored"]
report(len(authored_left) == 20,
	"the 20 charts whose dimension was NOT confirmed stay unpromoted (%d)" % len(authored_left))
report(all(chart_registry.CHARTS[c]["status"] == "real" for c in verified),
	"every verified chart is actually marked real")

report('"tab" + spec["doctype"]' in builder,
	"the builder addresses tab<DocType> -- the bare DocType name caused 13 TableNotFound errors")
report('"measure_name": "count"' in builder and '"dimension_name": dimension_field' in builder,
	"the builder uses the measure/dimension shape already proven on the bench")
report("is_builder_query" in builder and "use_live_connection" in builder,
	"the builder sets is_builder_query and use_live_connection, as the proven pilot does")

# A composite chart still records WHY it cannot be a single query -- that is
# the migration record. It just no longer RENDERS anything (see below).
computed_charts = [c for c, s in chart_registry.CHARTS.items() if s["status"] == "computed"]
report(all(chart_registry.CHARTS[c].get("composite_reason", "").startswith("COMPOSITE:") for c in computed_charts),
	"every computed chart records why it is not an Insights chart (%d)" % len(computed_charts))
report(all(not chart_registry.CHARTS[c]["insights_query_title"] for c in computed_charts),
	"a computed chart claims NO Insights query -- it must not look like one that failed")

# "real" means the runtime WILL execute the query. A chart promoted without
# anyone seeing it return data produces an error card on a live dashboard.
actually_real = {c for c, s in chart_registry.CHARTS.items() if s["status"] == "real"}
report(actually_real == chart_registry.BENCH_VERIFIED_CHARTS,
	"only bench-VERIFIED charts are marked real (%d)" % len(actually_real),
	"unverified charts claiming real: %s" % sorted(actually_real - chart_registry.BENCH_VERIFIED_CHARTS)[:5])

real_titles = [s["insights_query_title"] for s in chart_registry.CHARTS.values() if s["status"] == "real"]
report(all("PLACEHOLDER" not in t.upper() for t in real_titles),
	"no REAL chart is mislabelled as a placeholder")

chart_service_source = (APP / "analytics" / "chart_service.py").read_text(encoding="utf-8")
report("is_public" not in chart_service_source,
	"the chart runtime never touches Insights' public-dashboard mechanism")
report("run_chart_query" in chart_service_source,
	"real charts execute through the bench-proved permission-checked path")

# --- INSIGHTS OR BLANK -----------------------------------------------------
# The rule, in the one place a chart's data is decided. Everything that is not
# a verified Insights query collapses to a single wordless empty status: an
# unknown id, an authored-but-unverified query, and a composite alike.
service_body = chart_service_source[chart_service_source.index("def get_chart("):]
service_body = service_body[:service_body.index("def get_definitions(")]
report('status="computed"' not in service_body and '"unknown_chart"' not in service_body,
	"the chart endpoint has no computed and no unknown-chart status left")
report("No chart is registered" not in chart_service_source,
	"the 'No chart is registered under that id' message is gone -- it read as a broken lookup")
report(service_body.count('status="empty"') + service_body.count('"status": "empty"') == 2,
	"both non-real paths (unregistered id, unverified definition) return the SAME empty status")
report('status="placeholder"' not in service_body,
	"nothing returns a placeholder status the card would have to explain")

# --- THE SINGLE RENDERING PATH ---------------------------------------------
# The hand-rolled SVG renderers must be unreachable: charts come from
# Insights or they come up empty, with nothing in between.
render_block = page_source[page_source.index("function renderLiveChartCardNow("):]
render_block = render_block[:render_block.index("function renderKpis(")]
# Decision B: the hand-rolled per-type SVG renderers stay unreachable. One
# renderer, two data engines -- metricRows() is a DATA extractor and is
# legitimately used by the computed path; chartForLive() is the renderer and
# must never run again.
report("chartForLive(" not in render_block,
	"the hand-rolled SVG renderer is unreachable (chartForLive never called)")
report("paintComputedChart" not in page_source,
	"the computed rendering path is GONE, not merely unreachable")
report(render_block.count("paintChartSeries(") >= 2,
	"Insights charts and admission charts share ONE table painter -- paintChartSeries")

# The whole rule lives in this one function, so this is where it is proved.
# Strip comment lines first: the block explains the removed path in prose, and
# a mention of metricRows in a comment is documentation, not a call.
insights_branch = render_block[render_block.index("function renderInsightsChartInto("):]
insights_branch = insights_branch[:insights_branch.index("function paintChartEmpty(")]
insights_code = "\n".join(
	line for line in insights_branch.splitlines() if not line.strip().startswith("//"))
report("metricRows(" not in insights_code,
	"NO chart box reads criterion-engine rows -- the second data engine is out of the render path")
report('definition.definition_status!=="real"' in insights_code
	and "paintChartEmpty" in insights_code,
	"anything not marked real renders the empty state, with no other branch")
report(insights_code.count("paintChartEmpty(") >= 4,
	"every non-Insights outcome -- no definition, unverified, no data, error -- lands on the empty state")
# Scoped to renderInsightsChartInto's OWN body: the wider slice also contains
# paintAdmissionChart's definition, so deleting the CALL and leaving the dead
# function behind passed an earlier version of this check.
dispatch = insights_code[:insights_code.index("function paintAdmissionChart(")]
report("chart.dataKey" in dispatch and "paintAdmissionChart(" in dispatch,
	"the 6 admission charts keep their Insights source (get_admission_intelligence)")
report("admission_intelligence" in insights_code,
	"admission chart data is read from the Insights-backed embed, not recomputed")
report("ucc_intelligence.api.get_chart_data" in page_source,
	"charts are fetched from Insights through the app's own endpoint")
report("renderInsightsChartInto" in page_source, "there is exactly one chart renderer, and it is the Insights one")

# An empty box must be genuinely empty. These strings put words in it -- and
# they are checked against CODE only, since the comments legitimately name the
# statuses that were removed in order to explain why.
page_code = "\n".join(l for l in page_source.splitlines() if not l.strip().startswith("//"))
report("paintChartPlaceholder" not in page_code,
	"the labelled 'pending' placeholder is gone from the page")
report("Insights definition pending" not in page_code,
	"no box announces a pending Insights definition")
report('badge.textContent = "Computed live"' not in page_code,
	"no box is badged 'Computed live' -- that classification no longer reaches the screen")
report("ucc-chart-empty" in page_source, "the empty state has its own quiet style, not a warning style")

# --- NO VERIFIED CHART IS ORPHANED -----------------------------------------
# LIVE_VISUAL_EXPANSION REPLACES a tab's CONFIG charts, and every visible tab
# has an expansion entry -- so 9 of the 16 bench-verified charts had no box at
# all. Verifying a chart and then not showing it is silent lost work, and once
# every other box is blank there is nothing left to notice it by. This walks
# the tabs the page actually builds (overview + subcriteria) and checks each
# real chart lands on one.
def _js_object(name):
	start = page_source.index("const %s=" % name) + len("const %s=" % name)
	depth = 0
	for end in range(start, len(page_source)):
		if page_source[end] == "{":
			depth += 1
		elif page_source[end] == "}":
			depth -= 1
			if depth == 0:
				break
	return json.loads(page_source[start:end + 1])

dash_config, expansion = _js_object("CONFIG"), _js_object("LIVE_VISUAL_EXPANSION")
real_ids = {c for c, s in chart_registry.CHARTS.items() if s["status"] == "real"}
placed, box_total, box_real = set(), 0, 0
for criterion, criterion_config in dash_config.items():
	for tab in ["overview"] + [row[0] for row in criterion_config.get("subcriteria") or []]:
		tab_section = criterion_config["sections"].get(tab) or {}
		expanded = expansion.get(criterion, {}).get(tab)
		# chartsForTab(): the expansion list, plus this tab's own CONFIG charts
		# that are verified and not already in it.
		boxes = list(expanded or tab_section.get("charts") or [])
		if expanded:
			shown = {b["id"] for b in expanded}
			boxes += [b for b in (tab_section.get("charts") or []) if b["id"] not in shown and b["id"] in real_ids]
		box_total += len(boxes)
		for box in boxes:
			if box.get("dataKey") or box["id"] in real_ids:
				box_real += 1
				placed.add(box["id"])

# The 6 admission charts are placed by dataKey, under ids of their own.
orphans = sorted(real_ids - placed - {c for c in real_ids if c.startswith("criterion_4-admission-")})
report(not orphans, "every bench-verified Insights chart appears on a visible tab",
	"verified but rendered nowhere: %s" % orphans)
report("configCharts" in page_source,
	"the pre-expansion CONFIG charts are preserved, which is what makes that possible")
print("        %d chart boxes across all 7 criteria: %d Insights, %d blank"
	% (box_total, box_real, box_total - box_real))

page_has_badge = "ucc-insights-badge" in page_source
report(page_has_badge, "the dashboard badges each chart with its Insights status")
badge_fn = page_source[page_source.index("function applyInsightsBadge("):]
badge_fn = badge_fn[:badge_fn.index("const INSIGHTS_BADGE_STYLE_ID")]
report(badge_fn.count("badge.textContent") == 1 and 'badge.textContent = "Insights"' in badge_fn,
	"exactly ONE badge exists, and it means 'this came from Insights'")


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
section("8. Installability -- every DocType can actually migrate")
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
	("build_placeholder_insights_charts.py", "materialise placeholder Insights definitions"),
	("build_admission_intelligence_embed.py", "build + permission-test the real Insights charts"),
	("build_insights_charts_from_specs.py", "build the 30 authored chart queries"),
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
