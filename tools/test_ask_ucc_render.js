// Behavioural self-check for Ask UCC: which card a response renders as, what
// stays collapsed, what the layout does at each width, and the settings gear's
// visibility probe. These are the pieces that are real logic rather than
// markup, so they are EXECUTED here against the actual page source rather than
// grepped -- a label that says "verified" is worth nothing if the renderer
// that produced it can also be reached by a model answer.
//
//   node tools/test_ask_ucc_render.js
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const SRC = fs.readFileSync(
	path.join(__dirname, "..", "ucc_intelligence", "ucc_intelligence", "sophia",
		"page", "sophia_analytics", "sophia_analytics.js"),
	"utf8");

// Minimal stubs: the page only touches these at module scope / inside the
// functions under test. on_page_load is assigned but never invoked here.
const escapeHtml = (v) => String(v == null ? "" : v)
	.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
	.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
const win = {
	UCCShared: {
		escapeHtml,
		permissionNoticeHtml: (o) => "<PERMISSION-NOTICE view=" + o.view + " source=" + o.source + ">",
		doctypeRoute: (dt) => "/app/" + dt.toLowerCase().replace(/ /g, "-"),
		errorText: (e) => String(e),
	},
};
const frappe = { pages: { "sophia-analytics": {} }, model: {}, boot: {} };
win.frappe = frappe;
const doc = { getElementById: () => null, createElement: () => ({}), head: { appendChild() {} }, addEventListener() {} };

const exported = new Function("window", "document", "frappe", "CSS",
	SRC + "\n;return { renderAnswerCard, renderVerifiedCard, renderAiCard, initSettingsLink };"
)(win, doc, frappe, { escape: (s) => s });
const { renderAnswerCard, renderVerifiedCard, renderAiCard, initSettingsLink } = exported;

const MODULE = { key: "student_journey", label: "Student Journey" };
const FACTS_PRESENT = { get_student_profile: { status: "available", student_name: "MENG, JINYANG", nationality: "China" } };
const FACTS_EMPTY = {};
const FACTS_BLOCKED = { get_student_profile: { status: "permission_denied" } };
const CHECKED = "2026-08-01 15:14:00";
const CONTEXT = { doctype: "Student Applicant", record: "UCC-APP-250019", fields: [
	{ key: "student_name", label: "Name", value: "MENG, JINYANG" },
	{ key: "nationality", label: "Nationality", value: "China" },
	{ key: "graduated", label: "Graduated", value: "No" },
] };

function verified(extra) {
	return Object.assign({ answer_kind: "verified_record", ai_status: "not_required",
		facts: FACTS_PRESENT, checked_at: CHECKED, warnings: [], record_context: CONTEXT }, extra || {});
}
function analysis(text, extra) {
	return Object.assign({ answer_kind: "ai_analysis", ai_status: "available",
		answer: { text: text, model: "gpt-x", latency_ms: 900 },
		facts: FACTS_PRESENT, checked_at: CHECKED, warnings: [] }, extra || {});
}

// --- THE ONE RULE: a reader can always tell which is which ------------------
const v = renderAnswerCard("What is this student's nationality?", verified(), MODULE);
const a = renderAnswerCard("Is this student ready to graduate?", analysis("Not ready to confirm yet."), MODULE);
assert.ok(v.includes("Verified record answer") && v.includes("is-verified"),
	"a record lookup renders the verified card, labelled in words");
assert.ok(a.includes("AI analysis") && a.includes("is-ai"),
	"an interpretive question renders the AI card, labelled in words");
assert.ok(!v.includes("AI analysis") && !/\bAI\b/.test(v),
	"a verified answer carries NO AI label anywhere -- this is the whole point");
assert.ok(!a.includes("Verified record answer"), "and an AI answer is not labelled verified");
assert.ok(v.includes("China"), "the verified answer leads with the value from the record");
assert.ok(v.includes("read from the live record"),
	"and names where it came from, so the value is never a claim floating free");

// The card type is the SERVER's decision. A response that says ai_analysis
// renders as AI even if its text looks like a bare fact, and vice versa.
assert.ok(renderAnswerCard("q", analysis("China."), MODULE).includes("AI analysis"),
	"answer_kind decides the card, not what the text happens to look like");
assert.ok(renderAnswerCard("q", verified({ facts: FACTS_PRESENT }), MODULE).includes("Verified record answer"),
	"...and the same in reverse");

// --- the model belongs in the audit trail, not the headline ----------------
const head = a.slice(a.indexOf("ucc-ask-card-head"), a.indexOf("ucc-ask-card-body"));
assert.ok(!head.includes("gpt-x"), "the model name is NOT in the AI card header");
assert.ok(a.includes("gpt-x") && a.includes("Technical details"),
	"it is in Technical details instead");
assert.ok(a.includes("Based on 1 live record check"),
	"the header states how many record checks stand behind the analysis");

// --- everything underneath is collapsed ------------------------------------
for (const html of [v, a]) {
	assert.ok(html.includes("<details class=\"ucc-ask-collapse\">"),
		"evidence is in a collapsible");
	assert.ok(!html.includes("ucc-ask-collapse\" open"),
		"and nothing is open by default -- the answer must stand without it");
}
assert.ok(v.includes("View supporting facts") && v.includes("Record details"),
	"a verified answer offers supporting facts and record details");
assert.ok(a.includes("View supporting facts") && a.includes("Technical details"),
	"an AI answer offers supporting facts and technical details");

// --- a warning is neither a fact nor an answer -----------------------------
const warned = renderAnswerCard("q", verified({
	warnings: [{ message: "The completion date has been reached. Confirm whether the graduation status needs updating." }],
}), MODULE);
assert.ok(warned.includes("ucc-ask-warning") && warned.includes("Data check"),
	"a data-consistency warning is labelled as a data check, in words, not just in amber");
assert.ok(warned.indexOf("ucc-ask-warning") > warned.indexOf("ucc-ask-answer"),
	"and it sits below the answer, not in place of it");

// --- escaping --------------------------------------------------------------
const nasty = renderAnswerCard("q", analysis("<img src=x onerror=alert(1)>"), MODULE);
assert.ok(!nasty.includes("<img src=x"), "model output is escaped before it reaches innerHTML");
const nastyFact = renderAnswerCard("q", verified({
	facts: { t: { status: "available", nationality: "<script>alert(1)</script>" } } }), MODULE);
assert.ok(!nastyFact.includes("<script>"), "record values are escaped too");

// --- things that were genuinely LOST are always reported --------------------
const alwaysShown = {
	guardrail_blocked: "withheld",
	error: "could not be produced",
	not_found: "could not be found",
};
for (const [status, phrase] of Object.entries(alwaysShown)) {
	const html = renderAnswerCard("q", { answer_kind: "unavailable", ai_status: status, facts: FACTS_PRESENT }, MODULE);
	assert.ok(html.includes(phrase),
		"ai_status=" + status + " must be reported EVEN WITH facts present -- something was lost");
}
// "enabled and BROKEN" is a fault and must always be visible. This is the
// reported "Enable AI is on but no AI text ever appears" bug: the status
// carries the exact missing piece and suppressing it made it undiagnosable.
const misconfigured = renderAnswerCard("q", {
	answer_kind: "unavailable", ai_status: "unavailable", facts: FACTS_PRESENT,
	answer_error: "No API key configured (site_config.json: ucc_intelligence_ai_api_key).",
}, MODULE);
assert.ok(misconfigured.includes("could not run"),
	"the notice says AI was enabled but could not run, not that it is switched off");
assert.ok(misconfigured.includes("site_config.json"),
	"the specific missing piece reaches the screen, so it is actionable rather than mysterious");

// --- ...but a deliberate switch-off with facts present is NOT an event ------
const switchedOff = renderAnswerCard("q", {
	answer_kind: "unavailable", ai_status: "disabled", facts: FACTS_PRESENT, checked_at: CHECKED }, MODULE);
assert.ok(switchedOff.includes("Verified record answer"),
	"AI off + facts present renders the facts as a verified answer, not an apology");
assert.ok(!switchedOff.includes("turned off"),
	"and does not announce a setting nobody asked about");
assert.ok(renderAnswerCard("q", { answer_kind: "unavailable", ai_status: "disabled", facts: FACTS_EMPTY }, MODULE)
	.includes("Answer unavailable"),
	"with NO facts either, it must still explain itself rather than render blank");
assert.ok(renderAnswerCard("q", { answer_kind: "unavailable", ai_status: "disabled", facts: FACTS_BLOCKED }, MODULE)
	.includes("Answer unavailable"),
	"facts that exist but are permission_denied do not count as an answer");

// --- a blocked record still wins over everything ----------------------------
const blocked = renderAnswerCard("q", {
	answer_kind: "verified_record", facts: FACTS_PRESENT,
	sources: [{ status: "permission_denied", doctype: "Student Applicant" }] }, MODULE);
assert.ok(blocked.includes("PERMISSION-NOTICE"),
	"a permission-denied source still renders the shared notice, whatever the answer kind says");

// --- BUG: the settings probe must not query a table Singles do not have -----
// Matches the call, not the comment that explains why the call is banned.
assert.ok(!/method:\s*"frappe\.client\.get_count"/.test(SRC),
	"get_count must NOT be used: UCC Intelligence Settings is a Single (issingle:1) and has no tab<DocType> table");

function fakeGear() {
	const button = { dataset: {}, hidden: true, addEventListener() {} };
	return { button, querySelector: () => button };
}
// can_read true -> visible
let g = fakeGear();
frappe.model.can_read = (dt) => {
	assert.strictEqual(dt, "UCC Intelligence Settings", "probes the right doctype");
	return true;
};
initSettingsLink(g);
assert.strictEqual(g.button.hidden, false, "a user who can read Settings sees the gear");

// can_read false -> hidden
g = fakeGear();
frappe.model.can_read = () => false;
initSettingsLink(g);
assert.strictEqual(g.button.hidden, true, "a user who cannot read Settings does not see the gear");

// perm API absent -> show it and let the form's own permissions answer,
// rather than repeating the old failure where the gear was never revealed.
g = fakeGear();
delete frappe.model.can_read;
initSettingsLink(g);
assert.strictEqual(g.button.hidden, false,
	"with no perm API to ask, the gear is shown -- it must not silently vanish like the get_count version did");

// --- UX FIX 3: clear chat wipes the screen, not the stored conversation -----
assert.ok(/thread\.innerHTML = "";/.test(SRC), "clear chat empties the on-screen thread");
assert.ok(!/delete_conversation|frappe\.client\.delete/.test(SRC),
	"clear chat must NOT delete stored UCC AI Conversation records -- it is a display control");

// --- clear chat asks first, and is a DISPLAY control ----------------------
assert.ok(/window\.confirm\(/.test(SRC), "clearing the conversation confirms first");
assert.ok(/thread\.innerHTML = "";/.test(SRC), "clear chat empties the on-screen thread");

// --- category tabs and FAQ chips must be visually distinct -----------------
// The brief: tabs are underlined navy text with no pill background; FAQ chips
// are outlined white buttons with a verified dot. Two rows, two jobs.
const catStyle = SRC.match(/\.ucc-ask-category\{([^}]*)\}/)[1];
const qStyle = SRC.match(/\.ucc-ask-question\{([^}]*)\}/)[1];
assert.ok(/border:\s*0/.test(catStyle) && /border:1px solid/.test(qStyle),
	"categories are borderless tabs; FAQs are outlined chips -- different shapes, not two pill rows");
assert.ok(!/background:(?!\s*transparent)/.test(catStyle),
	"a category tab has no pill background of its own");
assert.ok(/\.ucc-ask-category\.is-active\{[^}]*border-bottom-color/.test(SRC),
	"the selected category is marked by an underline");
assert.ok(/\.ucc-ask-category\.is-active\{[^}]*font-weight:600/.test(SRC),
	"...and by weight, so the state is not carried by colour alone");
assert.ok(/\.ucc-ask-question::before\{[^}]*border-radius:50%/.test(SRC),
	"an FAQ chip carries a verified dot, so 'verified' is visible on the button itself");

// --- touch targets and focus ----------------------------------------------
for (const [selector, name] of [
	["\\.ucc-ask-submit", "Ask"], ["\\.ucc-ask-clear", "Clear chat"],
	["\\.ucc-ask-question", "an FAQ chip"], ["\\.ucc-ask-category", "a category tab"],
	["\\.ucc-ask-suggested-item", "a suggested question"],
	["\\.ucc-ask-context-action", "a context action"],
]) {
	const rule = SRC.match(new RegExp(selector + "\\{([^}]*)\\}"))[1];
	const height = Number((rule.match(/min-height:(\d+)px/) || [])[1] || 0);
	assert.ok(height >= 40, name + " has a >=40px touch target (got " + height + ")");
}
assert.ok(/focus-visible\{[^}]*outline:2px solid/.test(SRC),
	"keyboard focus is visible, and it is an outline rather than a colour swap");

// --- the two-column layout collapses rather than squeezing -----------------
assert.ok(/\.ucc-ask-layout\{[^}]*grid-template-columns:minmax\(0,1fr\) 280px/.test(SRC),
	"desktop is main + a 280px context column");
assert.ok(/@media\(max-width:1100px\)\{[\s\S]*?250px/.test(SRC),
	"the context column narrows on tablet before it is dropped");
assert.ok(/@media\(max-width:860px\)\{[\s\S]*?grid-template-columns:minmax\(0,1fr\)/.test(SRC),
	"and stacks to one column on mobile");
assert.ok(/@media\(max-width:860px\)\{[\s\S]*?\.ucc-ask-context\{position:static/.test(SRC),
	"the sticky context panel stops being sticky once it is stacked");
assert.ok(/\.ucc-ask-context\{position:sticky/.test(SRC),
	"on desktop the selected record stays visible while the conversation scrolls");

// --- nothing in Ask UCC may restyle the rest of the platform ---------------
// Every rule is scoped under .ucc-ask, with one documented exception: the
// settings gear, whose rules have always lived here because this is the only
// style injection that runs on boot.
const styleBlock = SRC.slice(SRC.indexOf("const ASK_STYLE_TEXT = `"), SRC.indexOf("function injectAskStyles"));
const selectors = styleBlock.split("\n")
	.filter((line) => /^[.\[@]/.test(line.trim()) && line.includes("{"))
	.map((line) => line.trim().split("{")[0]);
const leaked = selectors.filter((sel) =>
	!sel.includes(".ucc-ask") && !sel.includes(".ucc-shell-settings-link") && !sel.startsWith("@"));
assert.deepStrictEqual(leaked, [],
	"no Ask UCC rule escapes into the rest of Sophia: " + leaked.join(", "));

// --- no emoji anywhere in the Ask surface ---------------------------------
const askBlock = SRC.slice(SRC.indexOf("// ASK UCC -- the decision-support surface"),
	SRC.indexOf("// SETTINGS LINK --"));
assert.ok(!/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u.test(askBlock),
	"icons are inline SVG, not emoji");
assert.ok(askBlock.includes("aria-hidden=\"true\""), "and every icon is hidden from assistive tech");

// --- the settings form must never take a key from the browser --------------
const SETTINGS_JS = fs.readFileSync(path.join(__dirname, "..", "ucc_intelligence", "ucc_intelligence",
	"sophia", "doctype", "ucc_intelligence_settings", "ucc_intelligence_settings.js"), "utf8");
assert.ok(/ucc_intelligence\.api\.fetch_ai_models/.test(SETTINGS_JS),
	"the model list is fetched through the server method, never called from the browser");
assert.ok(!/api\.openai\.com/.test(SETTINGS_JS),
	"the browser NEVER talks to the provider directly -- that would need a key client-side");
assert.ok(!/api_key|apiKey|sk-/.test(SETTINGS_JS),
	"there is no API key entry, storage, or reference anywhere in the settings form");
assert.ok(/set_headline_alert\(\s*__\("Could not fetch models/.test(SETTINGS_JS),
	"a failed fetch shows an inline message rather than crashing the form");

console.log("PASS: Ask UCC verified-vs-AI cards, evidence collapse, layout, a11y, settings gear");
