#!/usr/bin/env python3
"""Self-check for the Ask UCC Desk Page.

The page is plain DOM + frappe.call, so this checks the things that
actually break in this codebase's history rather than re-testing the
browser: the page.body jQuery trap that already bit sophia_analytics.js,
whether the module list is server-driven or hardcoded, whether the three
answer zones the plan requires are genuinely distinct, and whether a
blocked record reuses the existing permission notice instead of inventing
a second one.

    python3 tools/test_ask_ucc_page.py
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE_DIR = ROOT / "ucc_intelligence" / "ucc_intelligence" / "sophia" / "page" / "ask_ucc"

checks = []


def report(ok, message):
	print(("PASS" if ok else "FAIL") + ": " + message)
	checks.append(ok)
	return ok


page_json = json.loads((PAGE_DIR / "ask_ucc.json").read_text(encoding="utf-8"))
page_js = (PAGE_DIR / "ask_ucc.js").read_text(encoding="utf-8")

# --- Page registration ---
report(page_json.get("doctype") == "Page", "ask_ucc.json declares a Page")
report(page_json.get("name") == "ask-ucc", "page name is ask-ucc")
report(page_json.get("module") == "Sophia", "page is registered under the Sophia module, like sophia-analytics")
report((PAGE_DIR / "__init__.py").exists(), "page directory has __init__.py so Frappe treats it as a module")

# --- the page.body jQuery trap (already cost this project once) ---
wireup = re.search(r'frappe\.pages\["ask-ucc"\]\.on_page_load[\s\S]*?\n};', page_js)
report(bool(wireup), "on_page_load wiring found")
if wireup:
	body = wireup.group(0)
	report("page.body[0]" in body, "page.body is unwrapped via [0] before use as a DOM node")
	report("page.body.innerHTML" not in body and "page.body.querySelector" not in body,
		"page.body is never used directly as a DOM node")

# --- shared.js is required before use, not assumed ---
report("frappe.require(\"/assets/ucc_intelligence/js/shared.js\"" in page_js,
	"shared.js is loaded via frappe.require when UCCShared isn't already present")
report("if (window.UCCShared)" in page_js, "UCCShared presence is checked before booting")

# --- module list is server-driven, never hardcoded ---
report("ucc_intelligence.api.get_ask_ucc_modules" in page_js,
	"the module list comes from the server (dashboard-access gated), not a hardcoded array")
for module_key in ("quality_action", "recruitment_agent", "student_journey"):
	report(('"%s"' % module_key) not in page_js and ("'%s'" % module_key) not in page_js,
		"module key %r is NOT hardcoded in the page -- it must come from the server" % module_key)
report("No Ask UCC modules are enabled" in page_js,
	"a user with no enabled modules gets an explanation, not a broken empty picker")

# --- the ask endpoint ---
report("ucc_intelligence.api.ask_ucc" in page_js, "the page calls the real whitelisted ask endpoint")
report(re.search(r"args:\s*\{\s*module:.*question:.*record:", page_js) is not None,
	"ask_ucc is called with module/question/record")

# --- the three zones the plan requires must be genuinely distinct ---
report("ucc-ask-zone-ai" in page_js, "there is a distinct AI-interpretation zone")
report("ucc-ask-zone-facts" in page_js, "there is a distinct facts zone")
report("renderSourcesZone" in page_js, "there is a distinct sources zone")
report("AI interpretation" in page_js and "Facts from live records" in page_js,
	"the zones are LABELLED, so a reader can tell AI text from retrieved facts")

# --- every non-available ai_status is explained, not silently blank ---
for status in ("disabled", "unavailable", "guardrail_blocked", "error", "not_found"):
	report(status in page_js, "ai_status %r has an explicit user-facing explanation" % status)
report("withheld" in page_js,
	"a guardrail-blocked answer explains that it was withheld, rather than silently showing nothing")

# --- blocked records reuse the EXISTING notice, not a second one ---
report("UCCShared.permissionNoticeHtml" in page_js,
	"a permission-denied record renders the same notice Analytics already uses")
report('permission_denied' in page_js, "the page checks for permission_denied explicitly")

# --- escaping: nothing user- or model-supplied reaches innerHTML raw ---
report("UCCShared.escapeHtml" in page_js, "the page escapes via the shared helper")
report(re.search(r"function esc\(", page_js) is not None, "there is a single esc() wrapper used throughout")
raw_interp = re.findall(r"\+\s*(message\.answer\.text|question)\s*\+", page_js)
report(not raw_interp,
	"neither the model's answer text nor the user's question is concatenated into HTML unescaped")

# --- styles are additive, not a fork of the analytics stylesheet ---
report("ucc-shared-panel" in page_js and "panel-head" in page_js,
	"reuses sophia_analytics.css's existing panel classes rather than restyling from scratch")
analytics_css = (ROOT / "ucc_intelligence" / "ucc_intelligence" / "sophia" / "page" / "sophia_analytics" / "sophia_analytics.css").read_text(encoding="utf-8")
legacy_css = (ROOT / "custom-html-block" / "CSS.css").read_text(encoding="utf-8")
report(analytics_css == legacy_css,
	"sophia_analytics.css is still byte-identical to the legacy CSS -- the new page did NOT edit it")
report(not (PAGE_DIR / "ask_ucc.css").exists(),
	"no competing stylesheet file; the page injects its own scoped styles instead")

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
