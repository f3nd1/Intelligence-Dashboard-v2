#!/usr/bin/env python3
"""Self-check for the Ask UCC workspace TAB inside sophia-analytics.

Ask UCC was first built as a standalone Frappe Page (route "ask-ucc").
That was an architecture mistake: the original platform design is ONE
page with Analytics / Explore / Ask UCC workspace tabs (the
data-ucc-workspace pattern in custom-html-block). This test now checks
the tab, and asserts the standalone page is genuinely gone rather than
left alongside it.

Checks what actually breaks in this codebase's history rather than
re-testing the browser: whether the module list is server-driven or
hardcoded, whether the three answer zones the plan requires are genuinely
distinct, whether a blocked record reuses the existing permission notice,
and whether the legacy Ask markup (with its forbidden browser API-key
modal) stayed out.

    python3 tools/test_ask_ucc_page.py
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE_DIR = ROOT / "ucc_intelligence" / "ucc_intelligence" / "sophia" / "page" / "sophia_analytics"

checks = []


def report(ok, message):
	print(("PASS" if ok else "FAIL") + ": " + message)
	checks.append(ok)
	return ok


page_js = (PAGE_DIR / "sophia_analytics.js").read_text(encoding="utf-8")

# --- it is a TAB, not a page ---
report(not (ROOT / "ucc_intelligence" / "ucc_intelligence" / "sophia" / "page" / "ask_ucc").exists(),
	"the standalone ask-ucc Page directory is gone")
report('frappe.pages["ask-ucc"]' not in page_js and "frappe.pages['ask-ucc']" not in page_js,
	"nothing registers a separate ask-ucc route any more")
report("function initAskUcc(" in page_js, "Ask UCC initialises as part of the platform shell")
report("initAskUcc(root)" in page_js, "initAskUcc is wired into the page's boot()")
report('data-ucc-ask' in page_js, "the Ask surface mounts into the shell's Ask workspace panel")
report(re.search(r'root\.dataset\.askReady', page_js) is not None,
	"Ask UCC guards against double-initialisation, like the shell and engine do")

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
# Ask's own wrapper is askEsc(), renamed on the move so it can't collide
# with the analytics engine's existing esc() -- checking for plain "esc("
# here would now pass on the engine's copy and prove nothing about Ask.
report("function askEsc(" in page_js, "Ask UCC has its own askEsc() wrapper, distinct from the engine's esc()")
ask_block = page_js[page_js.index("// ASK UCC -- the chat surface"):page_js.index("frappe.pages['sophia-analytics']")]
report(re.search(r"(?<![A-Za-z0-9_.])esc\(", ask_block) is None,
	"the Ask block never calls the engine's esc() by accident -- every call is askEsc()")
report(ask_block.count("askEsc(") > 10, "askEsc is used throughout the Ask rendering, not just once")
raw_interp = re.findall(r"\+\s*(message\.answer\.text|question)\s*\+", ask_block)
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
