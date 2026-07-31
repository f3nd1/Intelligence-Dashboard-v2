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

# --- record picker autocomplete (gap 1) ---
# The first version searched only `name` -- the record id -- so typing a
# human name matched nothing and the box looked dead. It must go through
# the server endpoint, which searches the module registry's declared
# fields, and it must never fall back to a client-driven get_list.
report("ucc_intelligence.api.search_ask_ucc_records" in page_js,
	"the picker searches via the server endpoint, not a client-side name-only query")
report("frappe.client.get_list" not in ask_block,
	"the Ask block does NOT reach for a raw client get_list to power the picker")
report(re.search(r"args:\s*\{\s*module:\s*module\.key,\s*term:", page_js) is not None,
	"the search is called with the module key and the typed term")
report("setTimeout" in ask_block and "clearTimeout" in ask_block,
	"typing is debounced rather than firing a request per keystroke")
report("ucc-ask-suggestion" in page_js, "matches render as a suggestion list under the input")
report("r.label" in page_js and "r.id" in page_js,
	"a suggestion shows the human label AND the record id, so the id stays visible")
report(re.search(r'askEsc\(r\.label\)', page_js) is not None and re.search(r'askEsc\(r\.id\)', page_js) is not None,
	"suggestion text is escaped -- record labels are user-entered data")
report("hideSuggestions" in page_js, "the suggestion list closes again (blur/no-match/module change)")

# --- guided question buttons (gap 2) ---
report("[data-ask-guided]" in page_js, "there is a guided-question panel in the Ask surface")
report("data-ask-category" in page_js and "data-ask-question-text" in page_js,
	"guided questions render as category pills plus question buttons")
report("module.categories" in page_js or "module && module.categories" in page_js,
	"the guided questions come from the server payload, not a hardcoded list in the page")
guided_start = page_js.index("function renderGuided(")
guided_block = page_js[guided_start:guided_start + 4000]
for legacy_label in ("Student Journey", "Quality Action", "Attendance and Leave"):
	report(legacy_label not in guided_block,
		"category label %r is NOT hardcoded in the page -- it is ported server-side" % legacy_label)
report("Select a record first." in page_js,
	"clicking a guided question with no record chosen prompts for one instead of firing a doomed request")
report(re.search(r"questionInput\.value = text;", page_js) is not None and "ask();" in page_js,
	"a guided question is sent on click (legacy one-click behaviour), not merely typed into the box")

# The buttons must match the ported set exactly -- the page renders whatever
# the server sends, so this checks the server side is the ported module.
api_py = (ROOT / "ucc_intelligence" / "ucc_intelligence" / "api.py").read_text(encoding="utf-8")
report("guided_questions" in api_py and "supported_questions" in api_py,
	"get_ask_ucc_modules serves the ported legacy question maps, not an invented set")

# --- settings link (gap 3) ---
report("[data-ucc-settings-link]" in page_js, "the platform header carries a settings control")
shell_html = page_js[page_js.index("const SHELL_HTML"):page_js.index("function initPlatformShell(")]
report("data-ucc-settings-link" in shell_html,
	"the settings control lives in SHELL_HTML, not injected ad hoc after boot")
report("ucc-shell-collapse-toggle" in shell_html,
	"the gear reuses the shell's existing header button class rather than a new control style")
report('frappe.set_route("Form", "UCC Intelligence Settings")' in page_js,
	"the settings control navigates to the real UCC Intelligence Settings doctype form")
report("initSettingsLink(root)" in page_js, "the settings link is wired into boot()")
report("frappe.model.can_read" in page_js,
	"gear visibility is decided from frappe.boot's permissions, not a table query")
settings_dir = ROOT / "ucc_intelligence" / "ucc_intelligence" / "sophia" / "doctype" / "ucc_intelligence_settings"
report(settings_dir.exists(), "the UCC Intelligence Settings doctype the link points at really exists")
settings_json = json.loads((settings_dir / "ucc_intelligence_settings.json").read_text(encoding="utf-8"))
report(settings_json.get("name") == "UCC Intelligence Settings",
	"the doctype name in the route matches the doctype's actual name")
# The bug: get_count on a Single queries tab<DocType>, which Singles do not
# have -- it threw on every page load and left the gear hidden. Any probe
# that reads/counts rows of this doctype is wrong for the same reason.
report(settings_json.get("issingle") == 1,
	"UCC Intelligence Settings really is a Single -- which is why no table probe may be used")
report('method: "frappe.client.get_count"' not in page_js,
	"the page does NOT call get_count on the Settings Single (it has no table to count)")
report("frappe.client.get_list" not in page_js and "frappe.db.count" not in page_js,
	"no row-reading probe of any kind is used against the Settings Single")

# --- gear placement: with the tabs, where it is findable (UX FIX 4) ---
report("ucc-shell-settings-link" in shell_html,
	"the gear has its own class rather than masquerading as another shell control")
nav = shell_html[shell_html.index("ucc-platform-workspaces"):shell_html.index("</nav>")]
report("data-ucc-settings-link" not in nav,
	"the gear is NOT inside the tab row -- it is a separate control, not a fourth tab")
report(shell_html.index("</nav>") < shell_html.index("data-ucc-settings-link"),
	"the gear comes immediately after the tab row closes, where it is findable")
report(re.search(r"\.ucc-shell-settings-link\{[^}]*margin-left:\s*\d+px", page_js) is not None,
	"the gear is visually separated from the tabs by its own margin, not butted against them")
report(re.search(r"\.ucc-shell-settings-link\{[^}]*font-size:\s*1[6-9]px", page_js) is not None,
	"the gear is rendered large enough to find (>=16px)")

# --- compact layout (UX FIX 1) ---
# The controls were three stacked panels each with its own heading block,
# which pushed the guided questions below the fold. Module, record, question
# and the guided buttons must now sit in one panel.
ask_panel = shell_html[shell_html.index('data-ucc-workspace-panel=\\"ask\\"'):]
report(ask_panel.count("panel-head") == 0,
	"the Ask surface no longer stacks full panel-head blocks -- that was the vertical space")
report(ask_panel.count("ucc-shared-panel") == 1,
	"module, record, question and guided questions share ONE panel, not three")
controls = ask_panel[:ask_panel.index("ucc-ask-thread")]
for anchor in ("data-ask-module", "data-ask-record", "data-ask-question", "data-ask-guided"):
	report(anchor in controls,
		"%s is inside the single controls panel, so it is visible without scrolling" % anchor)
report("<textarea" not in ask_panel,
	"the question box is a single-line input -- the 2-row textarea was part of the height problem")

# --- clear chat (UX FIX 3) ---
report("data-ask-clear" in page_js, "there is a Clear chat control")
report(">Clear chat</button>" in shell_html, "the control is labelled Clear chat")
report('thread.innerHTML = "";' in page_js, "Clear chat empties the on-screen thread")
report("clearButton.hidden = false" in page_js and "clearButton.hidden = true" in page_js,
	"Clear chat appears once there is something to clear and hides again afterwards")
report("delete_conversation" not in page_js and "frappe.client.delete" not in page_js,
	"Clear chat does NOT delete stored conversation records -- it is a display control only")

# --- the AI notice is no longer shown on plain data lookups (UX FIX 2) ---
report('if (hasFacts && (status === "disabled" || status === "unavailable")) return "";' in page_js,
	"a config-level AI-off state is not announced when the facts already answered the question")
report('reasons = {' in page_js and "guardrail_blocked" in page_js,
	"states where AI ran and its output was lost are still explained")

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
