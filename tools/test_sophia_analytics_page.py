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
engine_transformed = engine_transformed.rstrip()[: -len("})();")] + "}"
checks.append(report(engine_transformed in ported, "transformed engine body is present in the ported page verbatim"))
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
	expected_shell_html = header_no_changelog + nav_line + dashboard_line + criteria_line + "</section>"
	shell_match = re.search(r'const SHELL_HTML = (".*?");\n\n', ported, re.S)
	checks.append(report(bool(shell_match), "SHELL_HTML constant found in the ported page"))
	if shell_match:
		embedded = json.loads(shell_match.group(1))
		checks.append(report(embedded == expected_shell_html, "embedded shell HTML matches HTML.html's Analytics section minus the changelog/Explore/Ask trims"))

checks.append(report(criteria_line.count('data-dashboard-panel="criterion_') == 7, "all seven criterion mount divs present in the source HTML"))
checks.append(report('data-ucc-workspace="explore"' not in ported and 'data-ucc-workspace="ask"' not in ported, "Explore/Ask workspace buttons correctly excluded (Decision A/B)"))
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

# --- Insights pilot: additive-only guard ---
# The pilot (docs/migration/insights-pilot-findings.md) must never touch the
# existing chart-plugin registry or renderer, and must only ever target the
# single pilot chart id -- if either of those stop being true the pilot has
# stopped being a feasibility spike and started being a silent migration.
pilot_match = re.search(r"INSIGHTS PILOT[\s\S]*?(?=frappe\.pages\['sophia-analytics'\]\.on_page_load)", ported)
checks.append(report(bool(pilot_match), "Insights pilot block found in the ported page"))
if pilot_match:
	pilot_block = pilot_match.group(0)
	rest_of_file = ported[: pilot_match.start()] + ported[pilot_match.end() :]
	checks.append(report(
		"CHART_PLUGINS." not in pilot_block and "registerChartPlugin(" not in pilot_block,
		"Insights pilot block does not touch CHART_PLUGINS or register a chart plugin",
	))
	checks.append(report(
		pilot_block.count('data-demo-card="') <= 1,
		"Insights pilot block targets at most one existing chart card",
	))
	checks.append(report(
		"watchForInsightsPilotTarget(root)" in rest_of_file,
		"pilot mount is wired into boot() alongside the existing shell/engine init",
	))

passed = all(checks)
print()
print(f"{'PASS' if passed else 'FAIL'}: {sum(checks)}/{len(checks)} checks")
raise SystemExit(0 if passed else 1)
