// Behavioural self-check for the criterion tab surface: the Table view and its
// drill-down, the tab intro's Markdown subset, the chart size spans, and the
// Explore catalogue. Executed against the real page source, not grepped -- an
// escaping rule that is only asserted by a regex over source text has not been
// tested, it has been described.
//
//   node tools/test_tab_surface_render.js
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const SRC = fs.readFileSync(
	path.join(__dirname, "..", "ucc_intelligence", "ucc_intelligence", "sophia",
		"page", "sophia_analytics", "sophia_analytics.js"),
	"utf8");

const escapeHtml = (v) => String(v == null ? "" : v)
	.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
	.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
const win = {
	UCCShared: {
		escapeHtml,
		permissionNoticeHtml: (o) => "<PERMISSION-NOTICE source=" + o.source + ">",
		doctypeRoute: (dt) => "/app/" + dt.toLowerCase().replace(/ /g, "-"),
		errorText: (e) => String(e),
	},
};
const frappe = { pages: { "sophia-analytics": {} }, model: {}, boot: {} };
win.frappe = frappe;
const doc = { getElementById: () => null, createElement: () => ({}), head: { appendChild() {} }, addEventListener() {} };

// These live INSIDE initAnalyticsEngine(), which cannot be run headlessly (it
// boots the whole dashboard). So the functions under test are lifted out of
// the real source by brace-matching and evaluated together -- the code
// executed here is byte-for-byte the code that ships, and a rename breaks this
// harness loudly rather than silently testing a copy.
function lift(name) {
	const start = SRC.indexOf("function " + name + "(");
	assert.notStrictEqual(start, -1, "function " + name + " exists in the page");
	let depth = 0;
	let seen = false;
	for (let i = start; i < SRC.length; i++) {
		if (SRC[i] === "{") { depth += 1; seen = true; }
		else if (SRC[i] === "}") {
			depth -= 1;
			if (seen && depth === 0) return SRC.slice(start, i + 1);
		}
	}
	throw new Error("unbalanced braces in " + name);
}

const NEEDED = ["esc", "tabChartNotice", "humaniseColumn", "renderIntroMarkdown",
	"renderChartTable", "embeddedChartMarkup", "syncExploreCatalogue", "qaQuestionId"];
const exported = new Function("window", "document", "frappe", "CSS",
	"const tabChartState={};\n" + NEEDED.map(lift).join("\n")
	+ "\n;return { " + NEEDED.join(", ") + ", tabChartState };"
)(win, doc, frappe, { escape: (s) => s });
const { renderIntroMarkdown, renderChartTable, embeddedChartMarkup,
	syncExploreCatalogue, tabChartState, qaQuestionId } = exported;

// --- the tab intro's Markdown subset (#4) ----------------------------------
// Escaped FIRST, formatted after, so nothing a person types can become markup.
assert.ok(renderIntroMarkdown("**Scope.** Agents only.")
	.includes("<strong>Scope.</strong>"), "bold renders");
assert.ok(renderIntroMarkdown("*careful*").includes("<em>careful</em>"), "italic renders");
assert.ok(renderIntroMarkdown("`c4`").includes("<code>c4</code>"), "code renders");
assert.ok(renderIntroMarkdown("- one\n- two").includes("<ul><li>one</li><li>two</li></ul>"),
	"bullets render as a list");
assert.ok(renderIntroMarkdown("[docs](https://ucc.edu.sg)")
	.includes('<a href="https://ucc.edu.sg" target="_blank" rel="noopener">docs</a>'),
	"an http link renders");

const nasty = renderIntroMarkdown('<img src=x onerror=alert(1)> <script>alert(2)</script>');
assert.ok(!nasty.includes("<img") && !nasty.includes("<script>"),
	"raw HTML in the intro is escaped, never rendered");
// The text still SAYS "javascript:alert(1)" -- escaped, in a paragraph. What
// it must never be is an href, which is what this checks.
const jsLink = renderIntroMarkdown("[x](javascript:alert(1))");
assert.ok(!jsLink.includes("<a "), "a javascript: link is not turned into a link at all");
assert.ok(!/href=/.test(jsLink), "and no href is emitted for it -- only http(s) match");
const quoteBreak = renderIntroMarkdown('[x](" onmouseover="alert(1))');
assert.ok(!quoteBreak.includes("<a ") && !quoteBreak.includes("onmouseover=\"alert"),
	"a quote-breaking href cannot escape the attribute, because it never becomes one");

// --- chart sizes (#5) -------------------------------------------------------
for (const [size, span] of [["small", 3], ["medium", 6], ["large", 9], ["full", 12]]) {
	const html = embeddedChartMarkup({ chart: "q1", title: "T", size, span }, ["small", "medium", "large", "full"]);
	assert.ok(html.includes("grid-column:span " + span),
		size + " spans " + span + " of the 12-column grid");
	assert.ok(html.includes('value="' + size + '" selected'), size + " is the selected option");
}
const card = embeddedChartMarkup({ chart: "q1", title: "T", size: "medium", span: 6 }, ["medium"]);
assert.ok(!/grid-column:span (NaN|undefined)/.test(card), "a missing span never reaches the style attribute");
assert.ok(embeddedChartMarkup({ chart: "q1", title: "T", size: "medium" }, ["medium"])
	.includes("grid-column:span 6"), "a span that did not arrive falls back to a half-width card");

// --- the card carries what Explore and the toggle need ---------------------
assert.ok(card.includes('data-demo-card="q1"') && card.includes('data-demo-chart="q1"'),
	"the card keeps the data-demo-card/data-demo-chart hooks Explore resolves entries through");
assert.ok(card.includes('data-demo-view="diagram"') && card.includes('data-demo-view="table"'),
	"and both view buttons, which is also how Explore reveals a chart");

// --- the Table view and its drill-down (#8) --------------------------------
function fakeCard(data) {
	const table = { innerHTML: "" };
	return {
		_chartData: data,
		querySelector: (sel) => (sel === "[data-embedded-chart-table]" ? table : null),
		table,
	};
}
const DATA = {
	status: "available",
	columns: ["status", "count"],
	rows: [{ status: "Consultative", count: 40 }, { status: "Informative", count: 12 }],
};

let c = fakeCard(DATA);
renderChartTable(c, null);
assert.ok(c.table.innerHTML.includes("Consultative") && c.table.innerHTML.includes("Informative"),
	"the unfiltered table shows every row the query returned");
assert.ok(c.table.innerHTML.includes("<th>Status</th>"), "columns are the query's own, humanised");
assert.ok(!c.table.innerHTML.includes("Showing rows for"), "and it is not labelled as filtered");

c = fakeCard(DATA);
renderChartTable(c, "Consultative");
assert.ok(c.table.innerHTML.includes("Consultative"), "the drill-down keeps the clicked segment");
assert.ok(!c.table.innerHTML.includes("Informative"), "and drops the rest");
assert.ok(c.table.innerHTML.includes("Showing rows for") && c.table.innerHTML.includes("data-clear-segment"),
	"a filtered table says so and offers a way back");

c = fakeCard(DATA);
renderChartTable(c, "Nothing matches this");
assert.ok(c.table.innerHTML.includes("No rows matched"),
	"a segment with no rows says so rather than rendering an empty table");

c = fakeCard({ status: "query_error", message: "Table not found", rows: [], columns: [] });
renderChartTable(c, null);
assert.ok(c.table.innerHTML.includes("Table not found"),
	"a failed query's own message reaches the table view, not a blank box");

c = fakeCard(DATA);
renderChartTable(c, '<img src=x onerror=alert(1)>');
assert.ok(!c.table.innerHTML.includes("<img src=x"), "the segment label is escaped in the filter banner");

// The table is the query's OWN rows. Nothing here recomputes them, so it
// cannot disagree with the diagram.
const tableBlock = SRC.slice(SRC.indexOf("function renderChartTable("), SRC.indexOf("function humaniseColumn("));
assert.ok(!tableBlock.includes("frappe.call"),
	"the table view issues NO second request -- one execute feeds both views");

// --- Explore auto-populates (#7) -------------------------------------------
Object.keys(tabChartState).forEach((key) => delete tabChartState[key]);
tabChartState["criterion_3::overview"] = { charts: [{ chart: "q1", title: "Agents by Country" }] };
tabChartState["criterion_6::6.1.1"] = { charts: [{ chart: "q2", title: "Audit Findings" }] };
tabChartState["criterion_1::overview"] = { charts: [] };
let rebuilt = 0;
win.UCCExplore = { rebuild: () => { rebuilt += 1; } };
syncExploreCatalogue();
assert.deepStrictEqual(Object.keys(win.UCCLiveVisualDefinitions).sort(), ["criterion_3", "criterion_6"],
	"only criteria with charts appear in the Explore catalogue");
assert.strictEqual(win.UCCLiveVisualDefinitions.criterion_3.overview[0].id, "q1",
	"a chart added to a tab IS the Explore entry -- no separate list to maintain");
assert.strictEqual(win.UCCLiveVisualDefinitions.criterion_6["6.1.1"][0].title, "Audit Findings",
	"and it is catalogued under the tab it was added to");
assert.strictEqual(rebuilt, 1, "Explore is told to rebuild, so it repopulates without a manual step");

win.UCCExplore = undefined;
assert.doesNotThrow(syncExploreCatalogue,
	"and publishing the catalogue works even before Explore has initialised");

// --- question identity (#6) -------------------------------------------------
assert.strictEqual(qaQuestionId({ metric_id: "m-1", question: "Q?" }, 0), "m-1",
	"a question is identified by its metric id where it has one");
assert.strictEqual(qaQuestionId({ question: "Q?" }, 3), "Q?",
	"...its text where it does not");
assert.strictEqual(qaQuestionId({}, 3), "row-3", "...and its position as a last resort");

console.log("PASS: tab intro, chart sizes, table view, drill-down, Explore catalogue, question ids");
