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
// #4: these two were the bug. "# Heading" and "1. item" came out as literal
// text, which is what "typed markdown and it came out unformatted" meant.
assert.ok(renderIntroMarkdown("# Title").includes("<h3>Title</h3>"), "a heading renders");
assert.ok(renderIntroMarkdown("## Sub").includes("<h4>Sub</h4>"), "and a subheading, one level down");
assert.ok(!/<h1|<h2/.test(renderIntroMarkdown("# Title")),
	"but never as h1/h2 -- a tab intro must not out-shout the page");
assert.ok(renderIntroMarkdown("1. one\n2. two").includes("<ol><li>one</li><li>two</li></ol>"),
	"a numbered list renders as an ordered list");
assert.ok(renderIntroMarkdown("- a\n1. b").includes("</ul><ol>"),
	"switching list type closes the first list rather than mixing them");
assert.ok(renderIntroMarkdown("> quoted").includes("<blockquote>quoted</blockquote>"), "a quote renders");
assert.ok(renderIntroMarkdown("---").includes("<hr>"), "a rule renders");
assert.ok(renderIntroMarkdown("# **Bold** title").includes("<h3><strong>Bold</strong> title</h3>"),
	"inline formatting still works inside a heading");
// ...and none of it weakened the escaping. Markdown is applied to text esc()
// has ALREADY escaped, so the two requirements never conflict.
assert.ok(renderIntroMarkdown("# <script>alert(1)</script>")
	.includes("&lt;script&gt;") , "a heading containing raw HTML still escapes it");
assert.ok(!renderIntroMarkdown("# <img src=x onerror=alert(1)>").includes("<img"),
	"and cannot smuggle a tag in through a heading");
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

// --- chart width, now dragged rather than picked (#3) ----------------------
// The Small/Medium/Large/Full dropdown is gone. A card carries its span as a
// number, and the handle is a slider so the arrow keys do what the drag does.
for (const span of [1, 3, 6, 9, 12]) {
	const html = embeddedChartMarkup({ chart: "q1", title: "T", span }, true);
	assert.ok(html.includes("grid-column:span " + span), span + " columns reaches the style attribute");
	assert.ok(html.includes('data-span="' + span + '"'), "and the card records it for the drag to read");
	assert.ok(html.includes('aria-valuenow="' + span + '"'), "and the slider reports it to assistive tech");
}
const card = embeddedChartMarkup({ chart: "q1", title: "T", span: 6 }, true);
assert.ok(!card.includes("data-chart-size") && !card.includes("<select"),
	"the size dropdown is gone, not merely hidden");
assert.ok(card.includes('data-resize-chart="q1"') && card.includes('role="slider"'),
	"a drag handle replaces it, and it is a slider so it is keyboard-operable");
assert.ok(card.includes('aria-valuemin="1"') && card.includes('aria-valuemax="12"'),
	"bounded to the 12-column grid");
assert.ok(!/grid-column:span (NaN|undefined|0|13)/.test(
	embeddedChartMarkup({ chart: "q1", title: "T" }, true)),
	"a missing or out-of-range span never reaches the style attribute");
assert.ok(embeddedChartMarkup({ chart: "q1", title: "T", span: 99 }, true).includes("grid-column:span 12"),
	"an over-wide span is clamped rather than breaking the grid");

// --- reorder (#2) -----------------------------------------------------------
assert.ok(card.includes('draggable="true"') && card.includes("data-drag-grip"),
	"an editable card is draggable and shows a grip");

// --- Edit vs View mode (#5) -------------------------------------------------
// View is the default and must look finished: no x, no grip, no handle.
const viewing = embeddedChartMarkup({ chart: "q1", title: "T", span: 6 }, false);
for (const control of ["data-remove-chart", "data-drag-grip", "data-resize-chart",
		'draggable="true"', "is-editable"]) {
	assert.ok(!viewing.includes(control), "View mode shows no " + control);
}
assert.ok(viewing.includes('data-demo-view="table"') && viewing.includes("Diagram"),
	"but keeps both views -- looking at the data is not editing");
assert.ok(card.includes("data-remove-chart") && card.includes("data-resize-chart"),
	"Edit mode shows them all");

// The mode is derived from BOTH the permission and the toggle, so a viewer can
// never reach Edit mode by clicking anything.
const editingBlock = SRC.slice(SRC.indexOf("function isEditing("), SRC.indexOf("function tabChartAreaMarkup("));
assert.ok(/state\.canEdit&&tabEditModes\[/.test(editingBlock),
	"isEditing() requires the permission AND the toggle");
const actionsBlock = SRC.slice(SRC.indexOf("function renderTabActions("), SRC.indexOf("function ensureTabChartArea("));
assert.ok(/canEdit\s*\n?\?`<button[^`]*data-toggle-edit/.test(actionsBlock.replace(/\s+/g, " "))
	|| actionsBlock.includes("(canEdit"),
	"the Edit toggle itself is only rendered for someone who may edit");
assert.ok(actionsBlock.includes("data-export-pdf") && actionsBlock.includes('editing?"":'),
	"Export PDF is offered in View mode only");
assert.ok(actionsBlock.includes("data-tab-history"),
	"and the History view is offered to everyone");

// --- PDF export (#6) --------------------------------------------------------
const pdfBlock = SRC.slice(SRC.indexOf("function exportTabPdf("), SRC.indexOf("// --- Explore auto-population"));
assert.ok(/tabEditModes\[dashboard\.dataset\.demoDashboard\]=false/.test(pdfBlock),
	"exporting forces View mode first, so no edit control can reach the PDF");
assert.ok(pdfBlock.includes("ucc-print-stamp") && pdfBlock.includes("as at"),
	"the export is stamped with an as-at time");
assert.ok(pdfBlock.includes("config.number") && pdfBlock.includes("config.title"),
	"and names the criterion");
assert.ok(pdfBlock.includes("window.print()"), "it prints, which is where Save as PDF lives");
assert.ok(pdfBlock.includes('window.addEventListener("afterprint"') && pdfBlock.includes("setTimeout(cleanup"),
	"and cleans up afterwards, even if afterprint never fires");
assert.ok(SRC.includes("@media print"), "there is a print stylesheet");
for (const hidden of ["ucc-tab-charts-actions", "ucc-remove-chart", "ucc-drag-grip",
		"ucc-resize-handle", "ucc-add-chart", "ucc-qa-tools", "ucc-qa-hide"]) {
	assert.ok(new RegExp("\\." + hidden + "[,{]").test(SRC.slice(SRC.indexOf("@media print"))),
		"the print sheet hides ." + hidden);
}

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
