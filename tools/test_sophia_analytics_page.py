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

# --- INSIGHTS CHART LAYER ---------------------------------------------------
# Two documented additions: the badge call inside renderLiveChartCard, and the
# manifest load inside bootstrapDashboards.
_insights_block = re.search(
	r"// -+\n// INSIGHTS CHART LAYER\n[\s\S]*?\n(?=function renderLiveChartCard\()", ported)
checks.append(report(bool(_insights_block), "the Insights chart-layer block is present in the ported page"))
if _insights_block:
	engine_transformed = engine_transformed.replace(
		"function renderLiveChartCard(dashboard, chart, index, result) {",
		_insights_block.group(0) + "function renderLiveChartCard(dashboard, chart, index, result) {", 1)
engine_transformed = engine_transformed.replace(
	'        heading.textContent = chart.title || "Live visual";\n',
	'        heading.textContent = chart.title || "Live visual";\n        applyInsightsBadge(heading, chart.id);\n', 1
)

# --- SINGLE RENDERING PATH --------------------------------------------------
# Felix's decision: everything through Insights, no dual path, no fallback to
# the hand-rolled SVG renderers. The legacy renderLiveChartCardNow() derived
# rows from the criterion API and drew them with chartForLive(); it is
# replaced wholesale. Applied here as an explicit swap so this test still
# catches drift in the rest of the engine, and so the replacement itself is
# asserted rather than assumed.
_LEGACY_RENDER_NOW = re.search(
	r"function renderLiveChartCardNow\(card\)\{[\s\S]*?\ncard\.dataset\.liveCardRendered=\"1\";\n\}",
	engine_transformed)
checks.append(report(bool(_LEGACY_RENDER_NOW),
	"legacy renderLiveChartCardNow() found in the transformed engine (baseline for the swap)"))
if _LEGACY_RENDER_NOW:
	checks.append(report("metricRows(" in _LEGACY_RENDER_NOW.group(0),
		"the legacy renderer really did derive rows from the criterion API"))
	checks.append(report("chartForLive(" in _LEGACY_RENDER_NOW.group(0),
		"the legacy renderer really did call the hand-rolled SVG renderer"))
	_new_render = re.search(
		r"// DOCUMENTED DIVERGENCE FROM THE PORT[\s\S]*?\n\}(?=\nfunction renderKpis\()", ported)
	checks.append(report(bool(_new_render), "the Insights-only chart renderer is present in the ported page"))
	if _new_render:
		engine_transformed = engine_transformed.replace(
			_LEGACY_RENDER_NOW.group(0), _new_render.group(0), 1)
# --- VERIFIED CHARTS REACH A TAB -------------------------------------------
# LIVE_VISUAL_EXPANSION overwrites a section's CONFIG charts, so 9 of the 16
# bench-verified Insights charts had no box on any visible tab. Four sites
# change: the seeding loop keeps the pre-expansion list, and the three readers
# go through one chartsForTab() helper. Applied as explicit swaps, same as
# every other documented divergence, so drift elsewhere still fails.
_CHART_TAB_SWAPS = [
	(
		"config.sections[section]=config.sections[section]||{title:section,charts:[]};"
		"config.sections[section].charts=LIVE_VISUAL_EXPANSION[criterion][section];",
		"config.sections[section]=config.sections[section]||{title:section,charts:[]};"
		"config.sections[section].configCharts=config.sections[section].charts;"
		"config.sections[section].charts=LIVE_VISUAL_EXPANSION[criterion][section];",
	),
	(
		'grid.innerHTML=(definitions[sectionKey]||[]).filter(function(chart){return chart.enabled!==false;})'
		'.map(liveChartCardMarkup).join("");\ngrid.dataset.liveCardsMounted="1";',
		'grid.innerHTML=chartsForTab(dashboard.dataset.demoDashboard,config,sectionKey)'
		'.filter(function(chart){return chart.enabled!==false;}).map(liveChartCardMarkup).join("");\n'
		"// Cards mount synchronously; the chart manifest arrives over the wire. Stay\n"
		"// unmounted until it lands, or the verified charts chartsForTab() appends\n"
		"// would be missing from this grid for the rest of the session.\n"
		'if(chartDefinitions.loaded)grid.dataset.liveCardsMounted="1";',
	),
	(
		"const section=sectionDefinition(config,tab),liveDefinitions="
		"(LIVE_VISUAL_EXPANSION[dashboard.dataset.demoDashboard]?.[tab]||section?.charts||[]);",
		"const liveDefinitions=chartsForTab(dashboard.dataset.demoDashboard,config,tab);",
	),
	(
		"tab=activeSection(dashboard),section=sectionDefinition(config,tab),definitions="
		"(LIVE_VISUAL_EXPANSION[dashboard.dataset.demoDashboard]?.[tab]||section?.charts||[])",
		"tab=activeSection(dashboard),definitions=chartsForTab(dashboard.dataset.demoDashboard,config,tab)",
	),
]
for _old, _new in _CHART_TAB_SWAPS:
	checks.append(report(engine_transformed.count(_old) == 1,
		"legacy chart-placement site found exactly once: %r" % _old[:48]))
	engine_transformed = engine_transformed.replace(_old, _new, 1)

_charts_for_tab = re.search(r"// The chart boxes for one tab[\s\S]*?\n\}(?=\nfunction ensureLiveSectionCards\()", ported)
checks.append(report(bool(_charts_for_tab), "chartsForTab() is present in the ported page"))
if _charts_for_tab:
	engine_transformed = engine_transformed.replace(
		"function ensureLiveSectionCards(dashboard,config,sectionKey){",
		_charts_for_tab.group(0) + "\nfunction ensureLiveSectionCards(dashboard,config,sectionKey){", 1)

engine_transformed = engine_transformed.replace(
	"function bootstrapDashboards(){\nmountUnifiedDashboards();",
	"function bootstrapDashboards(){\nmountUnifiedDashboards();\n"
	"// Load the Insights chart manifest once, then repaint the headings so the\n"
	"// badges appear. Deliberately non-blocking: if the manifest never arrives\n"
	"// the dashboard still renders, just without the migration badges.\n"
	"injectInsightsBadgeStyles();\n"
	"loadChartDefinitions(function(){\n"
	'platform.querySelectorAll("[data-demo-chart]").forEach(function(node){\n'
	'const card=node.closest("[data-demo-card]");\n'
	'const heading=card&&card.querySelector("h2");\n'
	"if(heading)applyInsightsBadge(heading,node.dataset.demoChart);\n"
	"});\n"
	"});", 1
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
checks.append(report(engine_transformed in ported, "transformed engine body (plus the documented Option B, Phase 13 cutover and Insights-badge additions) is present in the ported page verbatim"))

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
explore_block_src = ported[ported.index("function initDiagramExplorer"):ported.index("// ASK UCC -- the chat surface")]
checks.append(report("global." not in explore_block_src,
	"no bare `global.` references survive in the ported Explore (its IIFE parameter is gone)"))
checks.append(report('data-ucc-explore' in ported, "the Explore panel markup is present in the shell"))

passed = all(checks)
print()
print(f"{'PASS' if passed else 'FAIL'}: {sum(checks)}/{len(checks)} checks")
raise SystemExit(0 if passed else 1)
