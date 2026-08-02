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
// The embed sizes itself against the window and checks the chrome on a timer,
// so both are captured rather than stubbed away -- a deferred check nobody can
// run is a check that was never written.
win.innerHeight = 900;
win.listeners = {};
win.addEventListener = (name, fn) => { (win.listeners[name] = win.listeners[name] || []).push(fn); };
win.deferred = [];
win.setTimeout = (fn, ms) => { win.deferred.push({ fn, ms }); return win.deferred.length; };
const doc = { getElementById: () => null, createElement: () => ({}), head: { appendChild() {} },
	addEventListener() {}, querySelectorAll: () => [] };

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
	"renderChartTable", "embeddedChartMarkup", "syncExploreCatalogue", "qaQuestionId",
	"paletteOf", "seriesColour", "segmentButton", "paintBarSeries", "paintLineSeries",
	"paintDonutSeries", "paintNumberSeries", "paintFunnelSeries", "paintChartSeries",
	"paintTableOnly", "sortForDisplay", "embeddedDashboardMarkup", "loadVisibleEmbeds",
	"hideInsightsChrome", "insightsDocument", "insightsChromeReport", "sizeEmbedFrame",
	"bindEmbedResize", "insightsContentHeight", "markEmbedClipped", "watchEmbedContent"];
// Module-level consts, which lift() cannot reach because it looks for
// `function <name>(`. Taken from the real source VERBATIM rather than retyped,
// so a painter or a threshold changed on the page cannot silently disagree
// with what this harness tests.
const CONSTS = ["CHART_PAINTERS", "DONUT_LABEL_MIN_SHARE", "SORTED_BY_VALUE",
	"INSIGHTS_CHROME_CSS", "EMBED_MIN_HEIGHT", "embedResizeBound"]
	// EMBED_MIN_HEIGHT's declaration carries EMBED_MAX_SCREENS and the rest on
	// the same statement, so they arrive with it.
	.map(function (name) {
		const found = (SRC.match(new RegExp("(?:const|let) " + name + "=[\\s\\S]*?;\\n")) || [])[0];
		assert.ok(found, "the page declares " + name);
		return found;
	}).join("\n");

const exported = new Function("window", "document", "frappe", "CSS",
	"const tabChartState={};let lastView=null;function setChartView(c,v){lastView=v;}\n"
	+ "const uccLog=[];function logEvent(card,level,event,detail){uccLog.push({level,event,detail});}\n"
	+ CONSTS + "\n" + NEEDED.map(lift).join("\n")
	+ "\n;return { " + NEEDED.join(", ")
	+ ", INSIGHTS_CHROME_CSS, EMBED_MIN_HEIGHT, tabChartState, uccLog,"
	+ " viewAfterPaint: () => lastView };"
)(win, doc, frappe, { escape: (s) => s });
const { renderIntroMarkdown, renderChartTable, embeddedChartMarkup,
	syncExploreCatalogue, tabChartState, qaQuestionId, paletteOf, seriesColour,
	paintBarSeries, paintLineSeries, paintDonutSeries, paintNumberSeries, sortForDisplay,
	paintFunnelSeries, paintChartSeries, embeddedDashboardMarkup } = exported;

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


// --- chart shapes driven by the Insights Chart record ----------------------
// Sophia embeds Insights QUERIES, which carry no presentation. The server
// reads the separate Chart record and hands down a `presentation` block. What
// matters here: every shape stays clickable (drill-down is the requirement
// that outranks the visuals), nothing emits SVG, and colour comes from the
// palette rather than being hardcoded.
const SERIES = [{ label: "Consultative", value: 40 }, { label: "Collaborative", value: 16 },
	{ label: "Empowering", value: 7 }];

function cardWith(presentation) {
	return { _chartData: { presentation }, querySelector: () => null };
}
function node() { return { innerHTML: "", insertAdjacentHTML(_, html) { this.innerHTML += html; } }; }

const CHART = cardWith({ status: "available", render_as: "bar",
	palette: ["#111111", "#222222", "#333333"] });

assert.deepStrictEqual(paletteOf(CHART), ["#111111", "#222222", "#333333"],
	"the palette comes off the presentation block");
assert.strictEqual(seriesColour(CHART, 4), "#222222",
	"and wraps rather than running out on the fourth series");
assert.deepStrictEqual(paletteOf(cardWith({})), ["#2563EB"],
	"a card with no palette still has a colour rather than none");

for (const [name, painter] of [["bar", paintBarSeries], ["line", paintLineSeries],
		["donut", paintDonutSeries], ["funnel", paintFunnelSeries]]) {
	const target = node();
	painter(CHART, target, SERIES);
	assert.ok(target.innerHTML.includes('data-chart-segment="Consultative"'),
		name + ": every segment is still a clickable drill-down target");
	assert.ok(!/<svg|<path|<polyline/i.test(target.innerHTML),
		name + ": no SVG is generated -- the deleted renderers stay deleted");
	assert.ok(target.innerHTML.includes("#111111"),
		name + ": the first series uses the palette's first colour");
	assert.ok(target.innerHTML.includes("<button"),
		name + ": segments are buttons, so they are keyboard-reachable");
}

// A number has no dimension, so there is nothing to drill into.
const numberNode = node();
paintNumberSeries(CHART, numberNode, [{ label: "Total", value: 62 }]);
assert.ok(!numberNode.innerHTML.includes("data-chart-segment"),
	"a single-figure chart offers no segment to drill into");
assert.ok(numberNode.innerHTML.includes("62"), "...but it does show the figure");

// Escaping holds inside every shape, including the conic-gradient one.
const hostileChart = node();
paintDonutSeries(CHART, hostileChart, [{ label: '<img src=x onerror=alert(1)>', value: 1 }]);
assert.ok(!hostileChart.innerHTML.includes("<img"),
	"a hostile label cannot become markup in a chart");

// --- #1 legend_position, #2 labels on the ring, #3 largest slice first -----
const DONUT = [{ label: "Diploma", value: 10 }, { label: "Advanced", value: 60 },
	{ label: "Certificate", value: 30 }];

// #1. The donut is the only shape with a legend, and it moves.
for (const [position, expected] of [["bottom", 'data-legend="bottom"'],
		["left", 'data-legend="left"'], ["top", 'data-legend="top"']]) {
	const placed = node();
	paintDonutSeries(cardWith({ palette: ["#111111"], legend_position: position }), placed, DONUT);
	assert.ok(placed.innerHTML.includes(expected),
		"legend_position " + position + " reaches the markup the CSS keys off");
}
const noLegend = node();
paintDonutSeries(cardWith({ palette: ["#111111"], legend_position: "none" }), noLegend, DONUT);
assert.ok(!noLegend.innerHTML.includes("ucc-insights-donut-legend"),
	'legend_position "none" removes the legend rather than hiding it with CSS');
const defaultLegend = node();
paintDonutSeries(cardWith({ palette: ["#111111"] }), defaultLegend, DONUT);
assert.ok(defaultLegend.innerHTML.includes('data-legend="right"'),
	"...and an unset legend_position falls back to right, not to nothing");

// #2. The percentage sits ON the ring, not only in the list beneath it.
const ringed = node();
paintDonutSeries(cardWith({ palette: ["#111111"] }), ringed, DONUT);
assert.ok(ringed.innerHTML.includes("ucc-insights-donut-mark"),
	"the donut draws its shares on the ring itself");
assert.ok(/>60%</.test(ringed.innerHTML) && />30%</.test(ringed.innerHTML),
	"...with each slice's own share: " + (ringed.innerHTML.match(/>\d+%</g) || []).join(" "));
assert.ok(!ringed.innerHTML.includes("<svg"),
	"...and still no SVG -- the marks are positioned spans");
assert.ok(ringed.innerHTML.includes('aria-hidden="true"'),
	"the ring marks are hidden from screen readers, which read the legend buttons instead");
// A sliver would collide with its neighbours, and its value is in the legend
// and the table regardless.
const slivers = node();
paintDonutSeries(cardWith({ palette: ["#111111"] }), slivers,
	[{ label: "Big", value: 97 }, { label: "Tiny", value: 2 }, { label: "Tinier", value: 1 }]);
assert.strictEqual((slivers.innerHTML.match(/class="ucc-insights-donut-mark"/g) || []).length, 1,
	"only slices with room for a label get one");
assert.ok(slivers.innerHTML.includes("Tiny"),
	"...and the unlabelled slices are still in the legend, so nothing is lost");

// #3. Largest first on the ring; every other shape keeps the query's order.
assert.deepStrictEqual(sortForDisplay("donut", DONUT).map((r) => r.value), [60, 30, 10],
	"a donut is drawn largest slice first");
assert.deepStrictEqual(sortForDisplay("line", DONUT).map((r) => r.value), [10, 60, 30],
	"a line keeps the query's order -- sorting it would stop it being a time series");
assert.deepStrictEqual(sortForDisplay("bar", DONUT).map((r) => r.value), [10, 60, 30],
	"a bar keeps the order its author chose in Insights");
assert.deepStrictEqual(DONUT.map((r) => r.value), [10, 60, 30],
	"sorting copies rather than reordering the card's own data");

// The limit is applied BEFORE the sort, so a "top 10" chart still shows the
// ten rows Insights picked -- reordered, not replaced.
const limited = node();
paintChartSeries(limited, [{ label: "First", value: 1 }, { label: "Second", value: 99 }],
	cardWith({ status: "available", render_as: "donut", palette: ["#111111"], limit: 1 }));
assert.ok(limited.innerHTML.includes("First") && !limited.innerHTML.includes("Second"),
	"a limited donut keeps the rows Insights chose, not the largest ones");

// --- PHASE 1 PILOT: the lazy embed --------------------------------------
//
// THE property. Every sub-criterion panel is in the DOM at once and switching
// tabs only toggles `hidden`, so an iframe carrying a src in the markup would
// boot one Insights SPA per sub-criterion the moment a criterion opens. The
// URL therefore waits in data-embed-src until the tab is actually shown.
const embedOk = embeddedDashboardMarkup({ embeddedDashboard: "dash-1",
	embeddedDashboardReadable: true });
assert.ok(!/\ssrc=/.test(embedOk),
	"the embed markup carries NO src -- a hidden iframe with one still loads");
assert.ok(embedOk.includes('data-embed-src="/insights/dashboards/dash-1"'),
	"the URL waits in data-embed-src");
assert.ok(!embedOk.includes("/insights/shared/"),
	"and it is the AUTHENTICATED route, never the is_public shared one");

// THE RECORDS STRIP IS GONE (Felix, 2026-08-04), and gone means the markup
// too: a strip that renders and then fails to load would be worse than none.
assert.ok(!/ucc-records-strip|data-records-strip|data-ask-dashboard/.test(embedOk),
	"the embed renders no Records strip and no Ask link");
assert.ok(!/ucc-records-strip|data-records-chart|data-ask-dashboard/.test(SRC),
	"...and nothing anywhere in the page renders or handles one");

const embedDenied = embeddedDashboardMarkup({ embeddedDashboard: "dash-2",
	embeddedDashboardReadable: false });
assert.ok(!embedDenied.includes("<iframe"),
	"a dashboard this user cannot open renders no frame at all...");
assert.ok(embedDenied.includes("cannot open"),
	"...and says so, rather than leaving a blank rectangle");

// A DOM small enough to hand-build and real enough to prove the promotion.
function el(tag, attrs) {
	const node = { tag, dataset: {}, hidden: false, children: [], listeners: {},
		parentNode: null, src: "", style: {},
		getBoundingClientRect() { return { top: 240 }; },
		addEventListener(name, fn) { (this.listeners[name] = this.listeners[name] || []).push(fn); },
		closest(sel) {
			let at = this;
			while (at) {
				if (sel === "[data-tab-charts]" && at.dataset.tabCharts !== undefined) return at;
				if (sel.startsWith("[data-dashboard-panel]")
					&& at.dataset.dashboardPanel !== undefined) return at;
				at = at.parentNode;
			}
			return null;
		},
		querySelector(sel) {
			let hit = null;
			(function walk(n) {
				if (hit) return;
				if (sel === "[data-embed-scroll]" && n.dataset.embedScroll !== undefined) { hit = n; return; }
				n.children.forEach(walk);
			})(this);
			return hit;
		},
		querySelectorAll(sel) {
			const out = [];
			(function walk(n) {
				if (sel === "iframe.ucc-embed-frame" && n.tag === "iframe") out.push(n);
				n.children.forEach(walk);
			})(this);
			return out;
		} };
	Object.assign(node.dataset, attrs || {});
	return node;
}
function area(tab, hidden, url) {
	const a = el("section", { tabCharts: tab });
	a.hidden = hidden;
	const frame = el("iframe", { embedSrc: url, embedName: tab });
	frame.parentNode = a;
	a.children.push(frame);
	return { area: a, frame };
}
const shown = area("4.1.1", false, "/insights/dashboards/dash-1");
const stillHidden = area("4.1.2", true, "/insights/dashboards/dash-2");
const root = el("div", {});
root.children.push(shown.area, stillHidden.area);
shown.area.parentNode = root;
stillHidden.area.parentNode = root;

exported.loadVisibleEmbeds(root);
assert.strictEqual(shown.frame.src, "/insights/dashboards/dash-1",
	"the VISIBLE tab's frame gets its src and loads");
assert.strictEqual(stillHidden.frame.src, "",
	"the HIDDEN tab's frame does not -- this is the whole point of the step");
assert.strictEqual(stillHidden.frame.dataset.embedSrc, "/insights/dashboards/dash-2",
	"...and its URL is still waiting for the tab to be opened");

// Promoted once. Returning to a tab must reuse the frame someone waited for.
shown.frame.src = "";
exported.loadVisibleEmbeds(root);
assert.strictEqual(shown.frame.src, "",
	"a second pass does not re-set src -- switching back never reloads the dashboard");

// ...and the hidden one loads when it is finally shown.
stillHidden.area.hidden = false;
exported.loadVisibleEmbeds(root);
assert.strictEqual(stillHidden.frame.src, "/insights/dashboards/dash-2",
	"showing the tab is what loads it, and only then");

// --- Insights' own app shell, hidden from the frame ------------------------
// App.vue wraps every authenticated route in <AppSidebar/>, and Dashboard.vue
// adds a breadcrumb header, so an embed arrives carrying Insights' navigation.
// The frame is same-origin, so it is hidden with a stylesheet in the frame's
// own document. Nothing here touches permissions -- the route still runs as
// the signed-in user.
function fakeFrame(contentDocument) {
	const frame = el("iframe", { embedSrc: "/insights/dashboards/dash-3", embedName: "4.2.1" });
	Object.defineProperty(frame, "contentDocument", { get: contentDocument });
	return frame;
}
// A frame document real enough to answer both questions the live bench asked:
// did the stylesheet go in, and did it MATCH anything. `shown` decides whether
// the sidebar/header report as visible.
function fakeInsights(opts) {
	const o = opts || {};
	const styles = [];
	const observed = [];
	const node = (tag, className) => ({ tagName: tag, className,
		style: { display: o.shown === false ? "none" : "" } });
	const sidebar = o.sidebar === false ? null : node("DIV", "h-full border-r bg-gray-50");
	const header = o.header === false ? null : node("HEADER", "flex h-12 items-center border-b");
	const appRoot = { children: o.appChildren
		|| [node("DIV", "flex h-screen w-screen overflow-hidden bg-white")] };
	// The grid Insights renders inside its scroll container. Its height is its
	// ROWS' height -- it does not stretch to the frame -- which is why it, and
	// not the container, is what gets measured.
	const grid = { tagName: "DIV", className: "h-fit w-full",
		getBoundingClientRect: () => ({ height: o.contentHeight }) };
	const scroller = o.content === false ? null
		: { className: "flex-1 overflow-y-auto p-4", firstElementChild: o.emptyGrid ? null : grid };
	// AppSidebar.vue wraps its link list in an overflow-y-auto too, and it comes
	// FIRST in document order. This is the element that broke the sizing twice:
	// querySelector returned it, so the "dashboard height" was a hidden menu's.
	// Kept in the fake, in the real order, so the bug cannot come back unseen.
	const sidebarScroller = { className: "flex flex-col overflow-y-auto",
		firstElementChild: { tagName: "DIV", className: "sidebar-links",
			getBoundingClientRect: () => ({ height: o.sidebarHeight === undefined ? 0 : o.sidebarHeight }) } };
	const scrollers = [sidebarScroller].concat(scroller ? [scroller] : []);
	return { styles, observed, head: { appendChild: (n) => styles.push(n) },
		createElement: () => ({ setAttribute() {}, textContent: "" }),
		defaultView: { getComputedStyle: (n) => n.style,
			ResizeObserver: o.noObserver ? undefined : function (fn) {
				this.observe = (target) => observed.push({ target, fn }); } },
		querySelector(sel) {
			if (sel === "style[data-ucc-embed-chrome]") return styles[0] || null;
			if (sel === "div.border-r.bg-gray-50") return sidebar;
			if (sel === "#app header") return header;
			if (sel === "#app .overflow-y-auto") return scrollers[0] || null;
			if (sel === "#app") return o.appRoot === false ? null : appRoot;
			return null;
		},
		querySelectorAll(sel) {
			return sel === "#app .overflow-y-auto" ? scrollers : [];
		} };
}
const insightsDoc = fakeInsights({});
const sameOrigin = fakeFrame(() => insightsDoc);
assert.strictEqual(exported.hideInsightsChrome(sameOrigin), true,
	"a same-origin frame accepts the stylesheet");
assert.strictEqual(insightsDoc.styles.length, 1, "...exactly one, appended to its head");
assert.strictEqual(exported.hideInsightsChrome(sameOrigin), true,
	"a second call is a no-op, not a second stylesheet");
assert.strictEqual(insightsDoc.styles.length, 1, "...still one");
// #1 from the live bench: the FIRST selectors asked for a whole tree shape
// (#app > div > div.border-r:first-child) and matched nothing on the real
// build. These name the elements and nothing else.
assert.ok(!/>/.test(exported.INSIGHTS_CHROME_CSS),
	"no child-combinator chains -- a selector that asserts the tree shape is a "
	+ "selector that fails silently when the tree moves");
assert.ok(!/:first-child|:nth-child/.test(exported.INSIGHTS_CHROME_CSS),
	"...and no positional guesses either");
assert.ok(/div\.border-r\.bg-gray-50\{display:none!important\}/
	.test(exported.INSIGHTS_CHROME_CSS), "the AppSidebar wrapper is hidden by its own classes");
assert.ok(/#app header\{display:none!important\}/.test(exported.INSIGHTS_CHROME_CSS),
	"...and Dashboard.vue's breadcrumb header too");
assert.ok(!/insights\/shared|is_public/.test(exported.INSIGHTS_CHROME_CSS),
	"hiding chrome is a stylesheet, never a switch to the public/shared route");

// Cross-origin, or Insights not yet parsed: refuse quietly, never throw. A
// dashboard nobody can see because the injection blew up is far worse than a
// dashboard with a menu beside it.
const crossOrigin = fakeFrame(() => { throw new Error("SecurityError"); });
assert.strictEqual(exported.hideInsightsChrome(crossOrigin), false,
	"a frame whose document cannot be reached returns false rather than throwing");
assert.strictEqual(exported.hideInsightsChrome(fakeFrame(() => ({ head: null }))), false,
	"...and so does one with no head yet");

// The report is the part that would have caught this round's bug. Injecting is
// not hiding: the check looks at what the rules actually did.
assert.strictEqual(exported.insightsChromeReport(fakeFrame(() => fakeInsights({ shown: false }))),
	"hidden", "chrome that is really gone reports hidden");
const stillThere = exported.insightsChromeReport(fakeFrame(() => fakeInsights({ shown: true })));
assert.ok(stillThere.startsWith("still visible"),
	"chrome the rules missed reports as still visible, not as success");
assert.ok(stillThere.includes("border-r") && stillThere.includes("header"),
	"...naming the real class names, so the next attempt has the DOM not a guess");
const nothingMatched = exported.insightsChromeReport(fakeFrame(() => fakeInsights(
	{ sidebar: false, header: false })));
assert.ok(nothingMatched.includes("#app children:") && nothingMatched.includes("h-screen"),
	"and when NOTHING matches, the report carries the app root's real children");
assert.strictEqual(exported.insightsChromeReport(crossOrigin),
	"the frame's document could not be reached from Sophia",
	"an unreachable document says so plainly rather than reporting success");

// And the loader is what calls it: promoting src without stripping the chrome
// would pass every assertion above and still ship the sidebar.
const chromeArea = area("4.2.2", false, "/insights/dashboards/dash-4");
const chromeRoot = el("div", { dashboardPanel: "criterion_4" });
chromeRoot.children.push(chromeArea.area);
chromeArea.area.parentNode = chromeRoot;
const loaderDoc = fakeInsights({ shown: true });
Object.defineProperty(chromeArea.frame, "contentDocument", { get: () => loaderDoc });
win.deferred.length = 0;
exported.uccLog.length = 0;
exported.loadVisibleEmbeds(chromeRoot);
(chromeArea.frame.listeners.load || []).forEach((fn) => fn.call(chromeArea.frame));
assert.strictEqual(loaderDoc.styles.length, 1,
	"the frame's load handler is what hides the chrome, on the real path");
assert.strictEqual(win.deferred.length, 1,
	"...and schedules the check for after Vue has mounted, not at load");
assert.ok(win.deferred[0].ms >= 1000,
	"the check waits long enough for the shell to render");
win.deferred[0].fn();
// The NUMBERS, logged every time -- not only when watching fails. Two rounds
// were spent asking why the frame was short when the log could have said what
// it measured.
const heightLog = exported.uccLog.filter((row) => row.event === "embed_height");
assert.strictEqual(heightLog.length, 1, "the measured height is logged on every embed");
assert.ok(/dashboard content \d+px, frame \d+px/.test(heightLog[0].detail),
	"...as both numbers, so a content height of 0 is the diagnosis rather than a mystery");

const chromeLog = exported.uccLog.filter((row) => row.event === "embed_chrome");
assert.strictEqual(chromeLog.length, 1, "the check logs its result once");
assert.strictEqual(chromeLog[0].level, "WARNING",
	"chrome still showing is a WARNING in the diagnostics log, not a silent pass");
assert.ok(chromeLog[0].detail.includes("border-r"),
	"...carrying what it actually found");

// --- the frame is sized to the dashboard, not to a guess -------------------
// Three rounds of this: 620px fixed cut charts in half; window-filling landed
// two rows and a sliced third, which reads as broken rather than scrollable.
// The dashboard's own height is what decides now, capped so a huge one does
// not bury the Records strip.
function sizedFrame(contentHeight, opts) {
	const built = area("4.3.1", false, "/insights/dashboards/dash-5");
	const scrollNote = el("span", { embedScroll: "" });
	scrollNote.textContent = "";
	built.area.children.push(scrollNote);
	built.frame.parentNode = built.area;
	const doc = fakeInsights(Object.assign({ contentHeight }, opts || {}));
	Object.defineProperty(built.frame, "contentDocument", { get: () => doc });
	return { frame: built.frame, note: scrollNote, doc };
}
// Frame top is 240 and the window 900, so the window-filling fallback is 572.
const shortDash = sizedFrame(300);
exported.sizeEmbedFrame(shortDash.frame);
assert.strictEqual(shortDash.frame.style.height, exported.EMBED_MIN_HEIGHT + "px",
	"a short dashboard does not leave the frame padded out with empty space "
	+ "(the floor is what stops it, not the window)");
assert.strictEqual(shortDash.note.textContent, "",
	"...and nothing tells anyone to scroll through content that all fits");

const tallDash = sizedFrame(900);
exported.sizeEmbedFrame(tallDash.frame);
assert.strictEqual(tallDash.frame.style.height, "936px",
	"a dashboard taller than the window gets a frame its own size -- 900 of "
	+ "content plus its padding -- rather than a window-shaped slice of itself");
assert.strictEqual(tallDash.note.textContent, "",
	"...and still says nothing about scrolling, because nothing is cut off");

// UNCAPPED (2026-08-04). A 1.6-window cap was tried and a real dashboard still
// needed scrolling, which is the thing being fixed. Show everything; the page
// gets longer, and the Records strip moves below the fold with it.
const hugeDash = sizedFrame(4000);
exported.sizeEmbedFrame(hugeDash.frame);
assert.strictEqual(hugeDash.frame.style.height, "4036px",
	"even a very tall dashboard gets a frame its own size -- nothing is cut off");
assert.strictEqual(hugeDash.note.textContent, "",
	"...and nothing tells anyone to scroll inside it, because nothing is hidden");
assert.ok(!/EMBED_MAX_SCREENS/.test(SRC), "the height cap is gone from the page");

// Unmeasurable: fall back to filling the window, and warn rather than assume
// it all fits. This path needs nothing from inside the frame.
const blindDash = sizedFrame(0, { content: false });
exported.sizeEmbedFrame(blindDash.frame);
assert.strictEqual(blindDash.frame.style.height, "572px",
	"a frame whose content cannot be measured still fills the window");
assert.ok(blindDash.note.textContent.includes("scroll inside it"),
	"...and says there may be more below, because it cannot prove otherwise");

win.innerHeight = 500;                    // a short laptop window
exported.sizeEmbedFrame(blindDash.frame);
assert.strictEqual(blindDash.frame.style.height, exported.EMBED_MIN_HEIGHT + "px",
	"never collapsing below the floor, however short the window");
win.innerHeight = 900;
assert.ok(!/height:\s*620px/.test(SRC), "and the fixed 620px height is gone from the page CSS");

// The scrollbar itself. Overlay scrollbars are invisible until you already
// know to scroll, which is exactly how the cut-off looked like a bug.
// Measured in Chromium: ::-webkit-scrollbar rules alone reserved 0px and left
// the bar an invisible overlay; the gutter reserved 12px and made it real. The
// webkit rules only colour a bar the gutter has already created.
assert.ok(/#app \.overflow-y-auto\{scrollbar-gutter:stable\}/.test(exported.INSIGHTS_CHROME_CSS),
	"the scroll container reserves a real scrollbar gutter, not an overlay bar");
assert.ok(/::-webkit-scrollbar\{width:12px/.test(exported.INSIGHTS_CHROME_CSS),
	"...and the bar itself is given a width");
assert.ok(/::-webkit-scrollbar-thumb\{background:#94A3B8/.test(exported.INSIGHTS_CHROME_CSS),
	"...with a thumb dark enough to see against the track");

// The height follows the grid as charts arrive -- a dashboard measured before
// its charts render measures nearly nothing.
const watched = sizedFrame(900);
assert.strictEqual(exported.watchEmbedContent(watched.frame), true,
	"the frame watches its dashboard's grid for changes");
assert.ok(watched.doc.observed.every((row) => row.target.className !== "flex-1 overflow-y-auto p-4"),
	"...observing the GRID inside each candidate, whose height is its rows -- not "
	+ "the scroll container, which is as tall as the frame and would pin the frame "
	+ "to whatever it already was");
assert.ok(watched.doc.observed.some((row) => row.target.className === "h-fit w-full"),
	"...and the dashboard's grid is among them");
assert.strictEqual(exported.watchEmbedContent(sizedFrame(900, { noObserver: true }).frame), false,
	"a browser without ResizeObserver reports the failure rather than pretending");

// THE BUG THAT SURVIVED TWO ROUNDS. AppSidebar.vue's link list is also an
// `#app .overflow-y-auto`, and it comes first, so querySelector handed the
// sizing a hidden menu's height and every dashboard fell back to the floor.
const sidebarFirst = sizedFrame(1400, { sidebarHeight: 40 });
assert.strictEqual(exported.insightsContentHeight(sidebarFirst.frame), 1436,
	"the DASHBOARD's grid is measured, not the sidebar's link list that precedes it");
exported.sizeEmbedFrame(sidebarFirst.frame);
assert.strictEqual(sidebarFirst.frame.style.height, "1436px",
	"...so a tall dashboard gets a tall frame instead of collapsing to the floor");
assert.strictEqual(exported.watchEmbedContent(sidebarFirst.frame), true,
	"and the observer watches every candidate, not only the first");
assert.ok(sidebarFirst.doc.observed.some((row) => row.target.className === "h-fit w-full"),
	"...including the dashboard grid, which is the one that changes as charts arrive");

// A frame someone loaded in a narrow window is re-sized when its tab is shown
// again -- the sizing pass must not be gated on the src promotion.
const reshown = sizedFrame(900).frame;
reshown.style.height = "";
const sizedArea = el("section", { tabCharts: "4.3.1" });
reshown.parentNode = sizedArea;
sizedArea.children.push(reshown);
delete reshown.dataset.embedSrc;
const sizedRoot = el("div", {});
sizedRoot.children.push(sizedArea);
sizedArea.parentNode = sizedRoot;
exported.loadVisibleEmbeds(sizedRoot);
assert.strictEqual(reshown.style.height, "936px",
	"an ALREADY-loaded frame is re-sized when its tab is shown again");
assert.ok((win.listeners.resize || []).length >= 1,
	"and the window resize is bound, so the frame follows the window");

// The labelled fallback: never blank, never broken, always says why.
const fallback = node();
const fallbackCard = cardWith({ status: "table_only", chart_type: "Sankey",
	reason: "Chart type 'Sankey' is not supported here yet.", palette: ["#2563EB"] });
paintChartSeries(fallback, SERIES, fallbackCard);
assert.ok(fallback.innerHTML.includes("Sankey"),
	"an unsupported chart type says which type it was");
assert.ok(!fallback.innerHTML.includes("data-chart-segment"),
	"...and does not pretend to be a chart");
assert.strictEqual(exported.viewAfterPaint(), "table",
	"...it switches the card to the table, which is a real view of real rows");

// The axis label from the Chart record is rendered, once.
const labelled = node();
paintChartSeries(labelled, SERIES, cardWith({ status: "available", render_as: "bar",
	palette: ["#2563EB"], axis_label: "Engagements" }));
assert.ok(labelled.innerHTML.includes("Engagements"), "the axis label from Insights is shown");

// An unknown render_as must not throw -- it falls back to bars, which are
// always drawable from a label/value series.
const unknown = node();
paintChartSeries(unknown, SERIES, cardWith({ status: "available", render_as: "treemap",
	palette: ["#2563EB"] }));
assert.ok(unknown.innerHTML.includes("data-chart-segment"),
	"an unrecognised renderer degrades to bars rather than throwing");

// --- #4: a drawable chart opens as the DIAGRAM, not the table --------------
const drawable = node();
const drawableCard = cardWith({ status: "available", render_as: "bar", palette: ["#2563EB"] });
paintChartSeries(drawable, SERIES, drawableCard);
assert.strictEqual(exported.viewAfterPaint(), "diagram",
	"a chart that CAN be drawn opens as the diagram");
const undrawable = node();
paintChartSeries(undrawable, SERIES, cardWith({ status: "table_only",
	reason: "No Insights chart has been built for this query.", palette: ["#2563EB"] }));
assert.strictEqual(exported.viewAfterPaint(), "table",
	"...and the table stays the automatic state only when nothing can be drawn");

// --- #4: the rename control, editors only ----------------------------------
const editable = embeddedChartMarkup({ chart: "q-1", title: "Chart 1", span: 6 }, true);
const readOnly = embeddedChartMarkup({ chart: "q-1", title: "Chart 1", span: 6 }, false);
assert.ok(editable.includes("data-retitle-chart"), "an editor can rename a card");
assert.ok(!readOnly.includes("data-retitle-chart"), "a viewer cannot");

// --- the picker lists both kinds, marked -----------------------------------
assert.ok(SRC.includes("Table only"),
	"the picker marks chart-less queries rather than hiding them");
assert.ok(SRC.includes("data-recolour-chart"),
	"an editor can recolour a chart");

console.log("PASS: tab intro, chart sizes, table view, drill-down, chart shapes, palette, Explore catalogue, question ids");
