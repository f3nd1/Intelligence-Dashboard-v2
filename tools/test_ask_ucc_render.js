// Behavioural self-check for the Ask UCC answer-zone rules and the settings
// gear's visibility probe. These are the two pieces of the recent UX round
// that are real logic rather than markup, so they are executed here against
// the actual page source instead of grepped.
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
	SRC + "\n;return { renderAnswerZone, initSettingsLink };"
)(win, doc, frappe, { escape: (s) => s });
const { renderAnswerZone, initSettingsLink } = exported;

const MODULE = { key: "student_journey", label: "Student Journey" };
const FACTS_PRESENT = { get_student_profile: { status: "available", nationality: "Singaporean" } };
const FACTS_EMPTY = {};
const FACTS_BLOCKED = { get_student_profile: { status: "permission_denied" } };

// --- UX FIX 2: a plain data lookup must NOT be told AI was turned off -------
for (const status of ["disabled", "unavailable"]) {
	assert.strictEqual(
		renderAnswerZone({ ai_status: status, facts: FACTS_PRESENT }, MODULE), "",
		"ai_status=" + status + " with facts present must render NO ai zone -- the facts answered it");
}

// --- ...but with nothing else to show, the user must not get a blank answer -
for (const status of ["disabled", "unavailable"]) {
	const html = renderAnswerZone({ ai_status: status, facts: FACTS_EMPTY }, MODULE);
	assert.ok(html.includes("AI interpretation unavailable"),
		"ai_status=" + status + " with NO facts must still explain itself");
}
assert.ok(
	renderAnswerZone({ ai_status: "disabled", facts: FACTS_BLOCKED }, MODULE)
		.includes("AI interpretation unavailable"),
	"facts that exist but are permission_denied do not count as an answer");

// --- things that were genuinely LOST are always reported --------------------
const alwaysShown = {
	guardrail_blocked: "withheld",
	error: "could not be produced",
	not_found: "could not be found",
};
for (const [status, phrase] of Object.entries(alwaysShown)) {
	const html = renderAnswerZone({ ai_status: status, facts: FACTS_PRESENT }, MODULE);
	assert.ok(html.includes(phrase),
		"ai_status=" + status + " must be reported EVEN WITH facts present -- something was lost");
}
// The guardrail firing is the one that must never be silently swallowed.
assert.ok(renderAnswerZone({ ai_status: "guardrail_blocked", facts: FACTS_PRESENT }, MODULE).length > 0,
	"a guardrail-blocked answer is never suppressed by the facts-present rule");

// --- an available answer still renders, and is still labelled + escaped -----
const ok = renderAnswerZone(
	{ ai_status: "available", answer: { text: "<img src=x onerror=alert(1)>", model: "gpt-x" }, facts: FACTS_PRESENT },
	MODULE);
assert.ok(ok.includes("AI interpretation"), "an available answer keeps its AI label");
assert.ok(ok.includes("gpt-x"), "the model is named on the label");
assert.ok(!ok.includes("<img src=x"), "model output is escaped before it reaches innerHTML");

// --- a blocked record still wins over everything ----------------------------
const blocked = renderAnswerZone(
	{ ai_status: "disabled", facts: FACTS_PRESENT, sources: [{ status: "permission_denied", doctype: "Student Applicant" }] },
	MODULE);
assert.ok(blocked.includes("PERMISSION-NOTICE"),
	"a permission-denied source still renders the shared notice, suppression rule notwithstanding");

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

console.log("PASS: Ask UCC answer-zone + settings-gear behaviour (" + 20 + " assertions)");
