#!/usr/bin/env python3
"""Self-check for the Sophia Analytics Desk Page port.

Re-extracts the exact platform-shell (custom-html-block/JAVASCRIPT.js
lines 266-435) and unified-engine (lines 2144-2703) ranges from the live
deployed source, re-applies the same two mechanical transformations Phase 3
made, and diffs the result against the committed page script -- so drift in
either the legacy source or the ported file is caught, not assumed away.

Also verifies: the embedded shell HTML round-trips to exactly what
HTML.html's Analytics section contains (minus the changelog button and the
Explore/Ask nav buttons, the two deliberate Decision-A/B trims), and the
CSS is still a byte-identical copy.

    python3 tools/test_sophia_analytics_page.py
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE_DIR = ROOT / "ucc_intelligence" / "ucc_intelligence" / "sophia" / "page" / "sophia_analytics"

js_lines = (ROOT / "custom-html-block" / "JAVASCRIPT.js").read_text(encoding="utf-8").split("\n")
html_lines = (ROOT / "custom-html-block" / "HTML.html").read_text(encoding="utf-8").split("\n")
ported = (PAGE_DIR / "sophia_analytics.js").read_text(encoding="utf-8")


def report(ok, message):
	print(("PASS" if ok else "FAIL") + ": " + message)
	return ok


checks = []


# Same two helpers the criterion ports' tests use, for the Explore check below.
def spaces_to_tabs_graceful(block_lines):
	out = []
	for text in block_lines:
		if not text.strip():
			out.append("")
			continue
		indent = len(text) - len(text.lstrip(" "))
		out.append("\t" * (indent // 4) + text.lstrip(" ") if indent % 4 == 0 else text)
	return out


def indent_one_more(block_lines):
	return ["\t" + text if text.strip() else "" for text in block_lines]


# --- platform shell: re-extract, re-transform, confirm present verbatim ---
shell_source = "\n".join(js_lines[265:435])
shell_head_original = (
	'(function () {\n"use strict";\nconst root = typeof root_element !== "undefined"\n'
	'? root_element.querySelector("#uccIntelligencePlatform")\n'
	': document.querySelector("#uccIntelligencePlatform");\n'
	'if (!root || root.dataset.platformReady === "1") {\nreturn;\n}\n'
	'root.dataset.platformReady = "1";'
)
checks.append(report(shell_head_original in shell_source, "platform-shell head matches the live deployed source verbatim"))
shell_transformed = shell_source.replace(
	shell_head_original,
	'function initPlatformShell(root) {\n"use strict";\nif (!root || root.dataset.platformReady === "1") {\nreturn;\n}\nroot.dataset.platformReady = "1";',
	1,
)
shell_transformed = shell_transformed.rstrip()[: -len("})();")] + "}"
checks.append(report(shell_transformed in ported, "transformed platform-shell body is present in the ported page verbatim"))

# --- engine: re-extract, re-transform, confirm present verbatim ---
engine_source = "\n".join(js_lines[2143:2703])
engine_head_original = (
	'/* UCC unified dashboard engine v2.0.1 */\n(function(){\n"use strict";\n'
	'const platform=typeof root_element!=="undefined"?root_element.querySelector("#uccIntelligencePlatform"):document.querySelector("#uccIntelligencePlatform");\n'
	'if(!platform||platform.dataset.liveFoundationReady==="1")return;\nplatform.dataset.liveFoundationReady="1";'
)
checks.append(report(engine_head_original in engine_source, "engine head matches the live deployed source verbatim"))
engine_transformed = engine_source.replace(
	engine_head_original,
	'function initAnalyticsEngine(platform){\n"use strict";\nif(!platform||platform.dataset.liveFoundationReady==="1")return;\nplatform.dataset.liveFoundationReady="1";',
	1,
)
checks.append(report(engine_transformed.count('method:"ucc_dashboard_access"') == 1, "legacy access-check method appears exactly once before the endpoint swap"))
engine_transformed = engine_transformed.replace(
	'method:"ucc_dashboard_access"', 'method:"ucc_intelligence.api.get_dashboard_access"', 1
)

# --- PHASE 13 CUTOVER -------------------------------------------------------
# The legacy engine called the Server Scripts by name. Felix disabled them on
# the bench and the system stopped, which is what proved the cutover had never
# been performed. Each criterion now calls the app's own whitelisted method.
# Applied here as a mechanical transform so this test still catches drift
# everywhere else, and so the cutover itself is asserted rather than assumed.
for _criterion_number in range(1, 8):
	_legacy_method = '"apiMethod":"ucc_analytics_criterion_%d"' % _criterion_number
	_app_method = '"apiMethod":"ucc_intelligence.api.get_criterion_%d"' % _criterion_number
	checks.append(report(_legacy_method in engine_transformed,
		"legacy engine really did call the Criterion %d Server Script (baseline for the cutover)" % _criterion_number))
	engine_transformed = engine_transformed.replace(_legacy_method, _app_method, 1)

# --- THE CHART BOXES ARE GONE ----------------------------------------------
# Felix, 2026-08-01: remove the whole chart-box system across all seven
# criteria and replace it with one "+ Add chart" button per tab, embedding real
# Frappe Insights charts the person picks.
#
# What that removed from the legacy engine: the 209-entry LIVE_VISUAL_EXPANSION
# table, the loop that overwrote every section's CONFIG charts with it, the
# chart-card markup and grid mounting, the fifteen hand-rolled SVG renderers
# and their plugin registry, metricRows()/chartForLive(), and both card
# renderers. 222 boxes, of which 16 ever had a real Insights query behind them.
#
# Each removal and each replacement is declared below and applied to the legacy
# text, so the final substring check still catches UNINTENDED drift everywhere
# that was not touched. A region is quoted by its start and resume markers
# rather than in full: the regions run to hundreds of lines, and a marker that
# stops matching fails this test just as loudly as a body that changed.
def region(text, start_marker, resume_marker, label):
	"""Legacy text from start_marker up to (not including) resume_marker."""
	checks.append(report(text.count(start_marker) == 1 and text.count(resume_marker) >= 1,
		"legacy engine has exactly one %s to remove" % label))
	first = text.index(start_marker)
	return text[first:text.index(resume_marker, first)]


def line(text, prefix, label):
	"""One whole legacy line, including its newline."""
	checks.append(report(text.count(prefix) == 1, "legacy engine has exactly one %s" % label))
	first = text.index(prefix)
	return text[first:text.index("\n", first) + 1]


AREA_BLOCK = (
	"// ---------------------------------------------------------------------------\n"
	"// PER-TAB INSIGHTS CHARTS, TAB INTRO, AND THE QUESTION SELECTION")
EMBED_BLOCK = (
	"// ---------------------------------------------------------------------------\n"
	"// PER-TAB CHARTS -- loading, rendering, sizing, picking, removing")

# 1. The box table itself, its global, and the loop that applied it.
engine_transformed = engine_transformed.replace(
	region(engine_transformed, "const LIVE_VISUAL_EXPANSION=", "function esc(value){",
		"LIVE_VISUAL_EXPANSION table + seeding loop"), "", 1)

# 2. Card markup, grid mounting, and every hand-rolled SVG renderer -> the
#    per-tab chart area.
_area = region(ported, AREA_BLOCK, "const RESPONSE_ADAPTERS=new Map();", "per-tab chart area (ported)")
engine_transformed = engine_transformed.replace(
	region(engine_transformed, "function liveChartCardMarkup(chart){", "const RESPONSE_ADAPTERS=new Map();",
		"chart-card markup + grid mounting + SVG renderers"), _area, 1)

# 3. metricRows/blockedSourceNames/chartForLive and both card renderers -> the
#    embed, picker and remove control.
# The same region also swallows the legacy renderKpis() and renderQa(): the KPI
# cards are gone (#3) and the questions table gained its show/hide controls
# (#6). One region, one swap, both declared.
_embed = region(ported, EMBED_BLOCK, "function renderSources(dashboard,result){", "chart embed + picker + questions (ported)")
engine_transformed = engine_transformed.replace(
	region(engine_transformed, "function metricRows(result,chartIndex,chart){",
		"function renderSources(dashboard,result){",
		"criterion-API row extractor, hand-rolled renderers, KPI cards and the old questions table"),
	_embed, 1)

# 4. The old cards' drill-down, and its trigger.
engine_transformed = engine_transformed.replace(
	region(engine_transformed, "async function openRecords(config,chartId,dashboard){",
		"function openReadiness(config,dashboard){", "chart drill-down helper"), "", 1)
for _prefix, _label in [
	('const drill=event.target.closest("[data-demo-drill]");', "chart drill-down handler"),
	('const viewButton=event.target.closest("[data-demo-view]");', "chart diagram/table toggle handler"),
]:
	_first = line(engine_transformed, _prefix, _label)
	_rest = engine_transformed[engine_transformed.index(_first) + len(_first):]
	engine_transformed = engine_transformed.replace(
		_first + _rest[:_rest.index("\n") + 1], "", 1)

# 5. sectionDefinition resolved a section's chart list. Nothing has one now.
engine_transformed = engine_transformed.replace(
	line(engine_transformed, "function sectionDefinition(config,tab){", "sectionDefinition helper"), "", 1)

# 6. Every section's declared boxes, emptied in place. Emptied rather than
#    re-serialised: a json.dumps round-trip re-encodes non-ASCII (the "x" in
#    "3 x 100" became \u00d7 once already, and this test caught it).
def empty_chart_arrays(text):
	out, index, count = [], 0, 0
	while True:
		found = text.find('"charts":[', index)
		if found == -1:
			out.append(text[index:])
			return "".join(out), count
		out.append(text[index:found])
		cursor, depth = found + len('"charts":['), 1
		while depth:
			depth += {"[": 1, "]": -1}.get(text[cursor], 0)
			cursor += 1
		out.append('"charts":[]')
		count += 1
		index = cursor


engine_transformed, _emptied = empty_chart_arrays(engine_transformed)
checks.append(report(_emptied == 60, "all 60 declared chart lists are emptied (%d)" % _emptied))
checks.append(report('"charts":[{' not in ported, "no chart box is declared in the ported CONFIG"))

# 7. The readers: render the tab's chosen charts, mount and show its area.
for _old, _new, _label in [
	("const section=sectionDefinition(config,tab),liveDefinitions="
		"(LIVE_VISUAL_EXPANSION[dashboard.dataset.demoDashboard]?.[tab]||section?.charts||[]);"
		"renderKpis(dashboard,config,result);"
		"liveDefinitions.forEach((chart,index)=>renderLiveChartCard(dashboard,chart,chart.i??index,result));"
		'dashboard.querySelectorAll(`[data-live-section="${CSS.escape(tab)}"] [data-demo-card]`)'
		".forEach(renderLiveChartCardNow);",
		"renderKpis(dashboard,config,result);renderTabCharts(dashboard,config,tab);",
		"renderDashboard's chart pass"),
	("ensureLiveSectionCards(dashboard,config,tab);syncLiveSectionVisibility(dashboard,tab);",
		"ensureTabChartArea(dashboard,config,tab);syncTabChartVisibility(dashboard,tab);",
		"showTab's chart mount"),
	('ensureLiveVisualCards(dashboard,config);syncLiveSectionVisibility(dashboard,"overview");',
		'ensureTabChartArea(dashboard,config,"overview");syncTabChartVisibility(dashboard,"overview");',
		"bootstrap's chart mount"),
	("config:CONFIG,registerResponseAdapter:registerResponseAdapter,registerChartPlugin:registerChartPlugin,refresh:",
		"config:CONFIG,registerResponseAdapter:registerResponseAdapter,refresh:",
		"the public registerChartPlugin hook"),
	('const actionButton=event.target.closest("[data-demo-action]");',
		'const addChart=event.target.closest("[data-add-chart]");\n'
		"if(addChart){event.preventDefault();event.stopPropagation();"
		"openChartPicker(dashboard,config,addChart.dataset.addChart);return;}\n"
		'const removeChart=event.target.closest("[data-remove-chart]");\n'
		"if(removeChart){event.preventDefault();event.stopPropagation();"
		"removeTabChart(dashboard,config,activeSection(dashboard),removeChart.dataset.removeChart);return;}\n"
		'const actionButton=event.target.closest("[data-demo-action]");',
		"the add/remove chart handlers"),
]:
	checks.append(report(engine_transformed.count(_old) == 1, "legacy site found exactly once: %s" % _label))
	engine_transformed = engine_transformed.replace(_old, _new, 1)

# --- WHAT THE MOVE TO INSIGHTS MADE OBSOLETE (2026-08-01) -------------------
# Three things on every criterion tab read the criterion engine's own
# catalogue and could not survive charts moving to Insights:
#   the page-level filter bar   -- an embedded chart is a live view of a SAVED
#       Insights query; this page cannot re-filter it. A filtered view is a
#       second Insights chart, built in Insights and added like any other.
#   the readiness strip         -- "Criterion N live analytics active ·
#       X of X sources available". The ELEMENT stays, because renderError()
#       reports a failed or permission-blocked load through it; only the
#       readiness message is gone, and it is hidden until something breaks.
#   the KPI number cards        -- same era, same source.
engine_transformed = engine_transformed.replace(
	region(engine_transformed, "function normaliseFilterDefinition(raw){", "function analyticsPanelMarkup(",
		"page-level filter markup"), "", 1)
engine_transformed = engine_transformed.replace(
	line(engine_transformed, "function selectedFilterObject(dashboard){", "filter collector"), "", 1)
engine_transformed = engine_transformed.replace(
	region(engine_transformed, "function openReadiness(config,dashboard){", "function showDiagnostics(",
		"readiness modal"), "", 1)
engine_transformed = engine_transformed.replace(
	region(engine_transformed, "function renderReadiness(dashboard,config,result){",
		"function renderError(dashboard,config,error){", "the readiness banner renderer"), "", 1)
for _old, _label in [
	('if(action==="readiness")openReadiness(config,dashboard);', "the readiness action"),
	('dashboard.querySelectorAll("[data-demo-filter]").forEach(input=>input.addEventListener("change",()=>loadLive(dashboard,true)));',
		"the filter change listener"),
]:
	checks.append(report(engine_transformed.count(_old) == 1, "legacy site found exactly once: %s" % _label))
	engine_transformed = engine_transformed.replace(_old, "", 1)

# The card controls added in this round -- Diagram/Table, drill-down, the size
# picker's clear control, the intro editor and the question show/hide -- all
# hang off the SAME delegated listener the add/remove chart handlers use, so
# they are declared as one insertion at that point.
_card_controls = region(ported,
	"// --- Diagram/Table toggle and drill-down (#8) --------------------------",
	'const actionButton=event.target.closest("[data-demo-action]");', "the card and question controls (ported)")
engine_transformed = engine_transformed.replace(
	'const actionButton=event.target.closest("[data-demo-action]");',
	_card_controls + 'const actionButton=event.target.closest("[data-demo-action]");', 1)

# The size <select> fires `change`, not `click`, so it needs its own listener
# rather than a branch in the click one.
_size_listener = region(ported, 'platform.addEventListener("change",function(event){',
	'platform.addEventListener("click",function(event){\nconst sourceButton=', "the size listener (ported)")
engine_transformed = engine_transformed.replace(
	'platform.addEventListener("click",function(event){\nconst sourceButton=',
	_size_listener + 'platform.addEventListener("click",function(event){\nconst sourceButton=', 1)

_intro = region(ported, "function analyticsPanelMarkup(criterionId,key,title){",
	"function sourcesQualityPanelMarkup(", "editable tab intro (ported)")
engine_transformed = engine_transformed.replace(
	region(engine_transformed, "function analyticsPanelMarkup(criterionId,key,title){",
		"function sourcesQualityPanelMarkup(", "hard-coded OVERVIEW heading"), _intro, 1)

for _old, _new, _label in [
	('const filters=(config.filters||[]).map((filter,index)=>filterMarkup(filter,index,criterionId)).join("");\n',
		"", "the filter build in the shell markup"),
	('<div class="sticky-navigation"><section class="controls ucc-shared-controls"><div class="control-grid">${filters}</div></section><nav',
		'<div class="sticky-navigation"><nav', "the filter bar in the shell markup"),
	('<div class="ucc-criterion-notice ucc-readiness-strip" data-demo-readiness data-status="loading">'
		'<div class="ucc-criterion-notice-copy"><strong data-demo-readiness-title>Loading Criterion ${esc(config.number)} analytics…</strong>'
		'<span data-demo-readiness-copy>Current-user permissions and live sources are being checked.</span></div>'
		'<div class="ucc-readiness-actions"><button type="button" class="ucc-readiness-detail" data-demo-action="readiness">View readiness</button>'
		'<button type="button" class="ucc-notice-dismiss" data-demo-action="dismiss-readiness" aria-label="Dismiss Criterion ${esc(config.number)} readiness notification" title="Dismiss">×</button></div></div>',
		'<div class="ucc-criterion-notice ucc-readiness-strip" data-demo-readiness data-status="loading" hidden>'
		'<div class="ucc-criterion-notice-copy"><strong data-demo-readiness-title></strong>'
		'<span data-demo-readiness-copy></span></div></div>', "the readiness strip"),
	('<section class="kpis ucc-shared-kpis" data-demo-kpis></section>', "", "the KPI card strip"),
	("filters:selectedFilterObject(dashboard),", "filters:{},", "the filter payload"),
	('const pmount=dashboard.querySelector("[data-demo-kpis]");\n'
		"if(pmount)pmount.innerHTML=UCCShared.permissionNoticeHtml({view:viewName,source:source,detail:detail});\n"
		"return;", "if(notice)notice.hidden=false;\nreturn;", "renderError's permission branch"),
	('const mount=dashboard.querySelector("[data-demo-kpis]");\n'
		'if(mount)mount.innerHTML=`<article><span>API status</span><strong>Unavailable</strong><small>${esc(detail)}</small></article>`;',
		"if(notice)notice.hidden=false;", "renderError's failure branch"),
	('if(action==="dismiss-readiness"){const notice=dashboard.querySelector("[data-demo-readiness]");'
		'if(notice){notice.dataset.dismissed="1";notice.hidden=true;}return;}', "", "the dismiss-readiness action"),
	("renderKpis(dashboard,config,result);renderTabCharts(dashboard,config,tab);renderQa(dashboard,result,tab);"
		"renderSources(dashboard,result);renderQuality(dashboard,result);renderReadiness(dashboard,config,result);}",
		"renderTabCharts(dashboard,config,tab);renderQa(dashboard,result,tab);"
		"renderSources(dashboard,result);renderQuality(dashboard,result);}", "renderDashboard's render list"),
	('if(!dashboard.classList.contains("ucc-hidden"))loadLive(dashboard);else renderReadiness(dashboard,config,null);',
		'if(!dashboard.classList.contains("ucc-hidden"))loadLive(dashboard);', "the bootstrap readiness call"),
]:
	checks.append(report(engine_transformed.count(_old) == 1,
		"legacy site found exactly once: %s" % _label))
	engine_transformed = engine_transformed.replace(_old, _new, 1)

engine_transformed = engine_transformed.replace(
	"function bootstrapDashboards(){\nmountUnifiedDashboards();",
	"function bootstrapDashboards(){\nmountUnifiedDashboards();\n"
	"// No chart manifest to load: charts are not declared by this app any more,\n"
	"// they are picked per tab from Insights and fetched when the tab renders.\n"
	"injectTabChartStyles();\n", 1
)
engine_transformed = engine_transformed.rstrip()[: -len("})();")] + "}"

# One documented, deliberate divergence from a straight mechanical transform:
# the Option B admission_intelligence embed call inserted into loadLive(), plus
# the new loadAdmissionIntelligenceEmbed() function immediately before it.
# Applying the identical replacement here (rather than dropping/loosening the
# check) keeps this test's actual job -- catching UNINTENDED drift everywhere
# else in the engine -- fully intact.
_LOAD_LIVE_ORIGINAL = (
	'async function loadLive(dashboard,force=false){const config=CONFIG[dashboard.dataset.demoDashboard],'
	'state=dashboardState(dashboard),section=apiSection(config,dashboard,activeSection(dashboard));'
	'ensureLiveSectionCards(dashboard,config,activeSection(dashboard));if(state.loading)return;'
	'if(!force&&state.result&&state.result.meta?.subcriterion===section){renderDashboard(dashboard);return;}'
	'state.loading=true;state.error=null;setLoading(dashboard,true,15,`Loading ${section}`);'
	'try{const result=await callApi(config,dashboard,"summary");setLoading(dashboard,true,80,"Rendering live analytics");'
	'state.result=result;state.error=null;renderDashboard(dashboard);setLoading(dashboard,true,100,"Live analytics ready");'
	'setTimeout(()=>setLoading(dashboard,false),150);}catch(error){state.error=error;'
	'logEvent(dashboard,"ERROR","api_failure",error.message||error);renderDashboard(dashboard);setLoading(dashboard,false);}'
	'finally{state.loading=false;}}'
)
checks.append(report(_LOAD_LIVE_ORIGINAL in engine_transformed, "original loadLive() text found in the transformed engine (before applying the Option B divergence)"))
embed_call_match = re.search(r"// Option B:[\s\S]*?function loadAdmissionIntelligenceEmbed[\s\S]*?\n}\n", ported)
load_live_match = re.search(r"async function loadLive\(.*", ported)  # single-line function, like the rest of this file
if embed_call_match and load_live_match:
	# embed_call_match already ends in "\n}\n" (its own trailing newline), so no
	# extra separator is added here -- confirmed against the real file's byte layout.
	engine_transformed = engine_transformed.replace(_LOAD_LIVE_ORIGINAL, embed_call_match.group(0) + load_live_match.group(0), 1)
checks.append(report(engine_transformed in ported, "transformed engine body (plus the documented Option B, Phase 13 cutover and per-tab chart additions) is present in the ported page verbatim"))

# --- the cutover itself, asserted directly ---------------------------------
for _n in range(1, 8):
	checks.append(report("ucc_analytics_criterion_%d" % _n not in ported.replace("// ucc_analytics_criterion_4 untouched", ""),
		"CUTOVER: the page no longer calls the Criterion %d Server Script" % _n))
	checks.append(report("ucc_intelligence.api.get_criterion_%d" % _n in ported,
		"CUTOVER: the page calls the app's own Criterion %d method" % _n))
checks.append(report("ucc_ask_" not in ported, "CUTOVER: no legacy Ask UCC Server Script method is called"))

checks.append(report('"ucc_dashboard_access"' not in ported, "legacy Server Script method name does not appear in the ported page"))
checks.append(report(ported.count("ucc_intelligence.api.get_dashboard_access") >= 1, "the app's own access endpoint is called"))

# --- shell HTML: rebuild the same way Phase 3 did, confirm it round-trips ---
header_line, nav_line, dashboard_line, criteria_line = html_lines[0], html_lines[1], html_lines[4], html_lines[5]
m = re.search(
	r'^(<div class="ucc-platform ucc-embed-safe"[^>]*id="uccIntelligencePlatform">'
	r'<header class="ucc-platform-shell"><div class="ucc-platform-brand">'
	r'<div aria-hidden="true" class="ucc-platform-mark">UCC</div>'
	r'<div class="ucc-platform-brand-copy"><div class="ucc-platform-brand-title">'
	r'<strong>UCC Intelligence Platform</strong>)'
	r'<button[^>]*data-action="show-changelog"[^>]*>v2\.0\.1</button>'
	r'(</div><small>Analytics, evidence and guided answers</small></div></div>'
	r'<nav aria-label="Platform workspaces" class="ucc-platform-workspaces">)$',
	header_line,
)
checks.append(report(bool(m), "HTML.html header still matches the pattern the page HTML was built from"))
if m:
	header_no_changelog = (m.group(1) + m.group(2)).replace(
		'data-build-id="UCC-PLATFORM-2.0.1-SHARED" data-platform-version="2.0.1"',
		'data-build-id="SOPHIA-ANALYTICS-PAGE" data-platform-version="phase-3"',
	)
	# All three workspace tabs, per the original platform design. Phase 3
	# trimmed Explore/Ask under "Decision A/B"; that was reversed once both
	# workspaces had real implementations to mount, so the shell is rebuilt
	# from the same legacy lines it was always cut from -- lines 1-6 for the
	# header/buttons/analytics panel, 8-56 for the Explore panel.
	explore_panel = "\n".join(html_lines[7:56])
	# One documented addition to the legacy header: a gear that opens the
	# UCC Intelligence Settings doctype, which previously had no entry point
	# anywhere in the UI. It sits immediately AFTER the workspace nav closes
	# -- outside the tab group, with its own spacing and box, so it reads as
	# a separate control rather than a fourth tab. Two earlier placements
	# were wrong: buried among the header controls (invisible), then inside
	# the nav (too small, squeezed against "Ask UCC"). Rebuilt here from the
	# legacy line the same way the engine's Option B addition is, so an
	# *undocumented* edit to the shell still fails this check.
	SETTINGS_GEAR = (
		'<button aria-label="UCC Intelligence Settings" class="ucc-shell-settings-link"'
		' data-ucc-settings-link="" hidden="" title="UCC Intelligence Settings" type="button">'
		'<span aria-hidden="true">&#9881;</span>'
		'<span class="ucc-visually-hidden">UCC Intelligence Settings</span></button>'
	)
	checks.append(report(html_lines[3].endswith('>Ask UCC</button>'),
		"the legacy nav's last tab is Ask UCC -- the gear must come after it, not among it"))
	checks.append(report(dashboard_line.startswith("</nav>"),
		"the legacy nav closes at the start of the next line -- where the gear is inserted"))
	dashboard_line_with_gear = dashboard_line.replace("</nav>", "</nav>" + SETTINGS_GEAR, 1)
	expected_shell_prefix = (
		header_no_changelog + nav_line + html_lines[2] + html_lines[3]
		+ dashboard_line_with_gear + criteria_line + "</section>" + explore_panel
	)
	shell_match = re.search(r'const SHELL_HTML = (".*?");\n', ported, re.S)
	checks.append(report(bool(shell_match), "SHELL_HTML constant found in the ported page"))
	if shell_match:
		embedded = json.loads(shell_match.group(1))
		checks.append(report(embedded.startswith(expected_shell_prefix),
			"shell HTML matches HTML.html's header + all 3 workspace buttons + Analytics + Explore panels verbatim"))
		checks.append(report(embedded.endswith("</main></div>"), "shell HTML closes <main> and the platform wrapper"))
		# The Ask panel is deliberately OURS, not legacy line 57's aja-app markup,
		# which embeds the browser OpenAI key modal CLAUDE.md forbids.
		checks.append(report('data-ucc-workspace-panel="ask"' in embedded, "an Ask workspace panel exists in the shell"))
		checks.append(report("ajaApiKeyInput" not in embedded and "aja-api-modal" not in embedded,
			"the legacy aja-app Ask markup (with its browser API-key modal) is NOT reintroduced"))
		checks.append(report('data-ucc-ask=""' in embedded, "the Ask panel hosts our own server-backed Ask UCC surface"))

checks.append(report(criteria_line.count('data-dashboard-panel="criterion_') == 7, "all seven criterion mount divs present in the source HTML"))
# Both forms count: SHELL_HTML is a JSON-escaped string literal, while the
# Explore code also uses an unescaped selector. "ask" legitimately appears
# only in the shell -- nothing needs to select it by name.
def has_workspace(key):
	return ('data-ucc-workspace="%s"' % key) in ported or ('data-ucc-workspace=\\"%s\\"' % key) in ported


checks.append(report(has_workspace("explore") and has_workspace("ask"),
	"Explore and Ask UCC are workspace TABS in this one page, not separate Frappe Pages"))
checks.append(report(not (ROOT / "ucc_intelligence" / "ucc_intelligence" / "sophia" / "page" / "ask_ucc").exists(),
	"the standalone ask-ucc Page is gone -- one page with tabs, not parallel pages"))
checks.append(report("show-changelog" not in ported, "changelog button correctly excluded (no changelog system ported)"))

# --- CSS: byte-identical copy ---
css_original = (ROOT / "custom-html-block" / "CSS.css").read_text(encoding="utf-8")
css_ported = (PAGE_DIR / "sophia_analytics.css").read_text(encoding="utf-8")
checks.append(report(css_original == css_ported, "sophia_analytics.css is byte-identical to custom-html-block/CSS.css"))

# --- page.body regression guard ---
# Confirmed via live browser inspection (2026-07-26): page.body is jQuery-
# wrapped in this Frappe version, not a raw DOM node, so .innerHTML/
# .querySelector on it directly throws. Guard against reintroducing that.
wireup_match = re.search(r"frappe\.pages\['sophia-analytics'\]\.on_page_load[\s\S]*", ported)
checks.append(report(bool(wireup_match), "on_page_load wiring found in the ported page"))
if wireup_match:
	wireup = wireup_match.group(0)
	checks.append(report("page.body.innerHTML" not in wireup and "page.body.querySelector" not in wireup,
		"page.body is not used directly as a DOM node (must be unwrapped first)"))
	checks.append(report("page.body[0]" in wireup, "page.body is unwrapped via [0] before use as a DOM node"))

# --- Insights pilot iframe glue: retired, must be gone ---
# Superseded by the Option B live embed (admission_intelligence_embed.py) --
# the iframe-embed spike (docs/migration/insights-pilot-findings.md) was
# additive-only by design and is now dead weight, not a second embed
# mechanism sitting alongside the real one. Confirm it's actually gone
# rather than just unused.
checks.append(report(
	"INSIGHTS_PILOT" not in ported and "watchForInsightsPilotTarget" not in ported and "mountInsightsPilotCard" not in ported,
	"retired Insights-pilot iframe glue code is fully removed, not left dormant",
))

# --- Option B live embed: admission_intelligence wiring guard ---
# admission_intelligence_embed.py's get_admission_intelligence must be called
# from loadLive() and merged into the same `result` object callApi() already
# populates, only for criterion_4/4.1.1 -- not a parallel rendering path, and
# must not touch callApi()/renderDashboard()/the chart-plugin registry.
# (embed_call_match / load_live_match were already computed above, reused
# there to build the engine-body-verbatim check's expected divergence.)
checks.append(report(bool(embed_call_match), "loadAdmissionIntelligenceEmbed() found in the ported page"))
if embed_call_match:
	checks.append(report(
		'"ucc_intelligence.api.get_admission_intelligence"' in embed_call_match.group(0),
		"loadAdmissionIntelligenceEmbed() calls the real whitelisted method",
	))
checks.append(report(bool(load_live_match), "loadLive() found in the ported page"))
if load_live_match:
	load_live_body = load_live_match.group(0)
	checks.append(report(
		'dashboard.dataset.demoDashboard==="criterion_4"&&section==="4.1.1"' in load_live_body,
		"admission_intelligence embed call is scoped to criterion_4/4.1.1 only",
	))
	checks.append(report(
		"loadAdmissionIntelligenceEmbed()" in load_live_body and "result.admission_intelligence=embed" in load_live_body,
		"embed result overwrites result.admission_intelligence in place, not a parallel render path",
	))
	checks.append(report(
		"result.sources=(result.sources||[]).concat(embed.sources||[])" in load_live_body,
		"embed's blocked sources are merged into result.sources so the existing permission-notice path picks them up",
	))

# --- Explore (Diagram Explorer): verbatim port of the legacy IIFE ---
# Same technique and same guarantee as the shell/engine ports above: the
# legacy body is re-extracted and re-transformed here, so drift on either
# side is caught rather than assumed away.
explore_source = "\n".join(js_lines[2707:3064])
explore_head_original = (
	'const platformRoot = typeof root_element !== "undefined"\n'
	'? root_element.querySelector("#uccIntelligencePlatform")\n'
	': document.querySelector("#uccIntelligencePlatform");\n'
	'\n'
	'if (!platformRoot || platformRoot.dataset.exploreReady === "1") return;\n'
	'platformRoot.dataset.exploreReady = "1";'
)
checks.append(report(explore_head_original in explore_source,
	"Explore IIFE head matches the live deployed source verbatim"))
explore_transformed = explore_source.replace(
	explore_head_original,
	'if (!platformRoot || platformRoot.dataset.exploreReady === "1") return;\n'
	'platformRoot.dataset.exploreReady = "1";', 1)
# The IIFE's `global` parameter is gone, so its two uses become window.
explore_transformed = explore_transformed.replace("global.UCCLiveVisualDefinitions", "window.UCCLiveVisualDefinitions")
explore_transformed = explore_transformed.replace("global.UCCExplore", "window.UCCExplore")
expected_explore = "\n".join(indent_one_more(spaces_to_tabs_graceful(explore_transformed.split("\n"))))
checks.append(report(expected_explore in ported,
	"Explore body matches the legacy Diagram Explorer verbatim (modulo the documented head/global transforms)"))
checks.append(report("function initDiagramExplorer(platformRoot) {" in ported,
	"Explore is a named init function, not a self-invoking IIFE"))
checks.append(report("initDiagramExplorer(root)" in ported, "initDiagramExplorer is wired into boot()"))
explore_block_src = ported[ported.index("function initDiagramExplorer"):ported.index("// ASK UCC -- the decision-support surface")]
checks.append(report("global." not in explore_block_src,
	"no bare `global.` references survive in the ported Explore (its IIFE parameter is gone)"))
checks.append(report('data-ucc-explore' in ported, "the Explore panel markup is present in the shell"))

passed = all(checks)
print()
print(f"{'PASS' if passed else 'FAIL'}: {sum(checks)}/{len(checks)} checks")
raise SystemExit(0 if passed else 1)
