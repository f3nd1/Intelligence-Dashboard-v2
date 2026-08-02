// Sophia -- Analytics (Phase 3 Desk Page port)
//
// Ported from custom-html-block/JAVASCRIPT.js's platform-shell module
// (lines 266-435) and unified dashboard engine module (lines 2144-2703),
// scoped to the Analytics workspace only -- Explore and Ask UCC are
// deferred (docs/migration/phase-3-plan.md, Decision A/B). Both modules
// are ported with exactly two classes of change from the deployed source,
// verified by diff against the exact extracted ranges before this file was
// assembled:
//   1. `root_element` / a document-wide `#uccIntelligencePlatform` lookup
//      is replaced by this page's own wrapper-scoped element, per CLAUDE.md
//      Phase 3's "remove reliance on root_element" requirement.
//   2. The dashboard-access check calls the app's own
//      ucc_intelligence.api.get_dashboard_access (Phase 2) instead of the
//      legacy ucc_dashboard_access Server Script -- Phase 2 built this
//      specifically to be Phase 3's consumer.
// No other logic was changed. CSS is a byte-identical copy of
// custom-html-block/CSS.css (sophia_analytics.css, same folder) loaded
// page-scoped, not site-wide -- see the plan doc for why.

const SHELL_HTML = "<div class=\"ucc-platform ucc-embed-safe\" data-build-id=\"SOPHIA-ANALYTICS-PAGE\" data-platform-version=\"phase-3\" id=\"uccIntelligencePlatform\"><header class=\"ucc-platform-shell\"><div class=\"ucc-platform-brand\"><div aria-hidden=\"true\" class=\"ucc-platform-mark\">UCC</div><div class=\"ucc-platform-brand-copy\"><div class=\"ucc-platform-brand-title\"><strong>UCC Intelligence Platform</strong></div><small>Analytics, evidence and guided answers</small></div></div><nav aria-label=\"Platform workspaces\" class=\"ucc-platform-workspaces\"><button aria-pressed=\"true\" class=\"is-active\" data-ucc-workspace=\"analytics\" type=\"button\">Analytics</button><button aria-pressed=\"false\" data-ucc-workspace=\"explore\" type=\"button\">Explore</button><button aria-pressed=\"false\" data-ucc-workspace=\"ask\" type=\"button\">Ask UCC</button><button aria-pressed=\"false\" data-ucc-workspace=\"operations\" type=\"button\">Operations</button></nav><button aria-label=\"UCC Intelligence Settings\" class=\"ucc-shell-settings-link\" data-ucc-settings-link=\"\" hidden=\"\" title=\"UCC Intelligence Settings\" type=\"button\"><span aria-hidden=\"true\">&#9881;</span><span class=\"ucc-visually-hidden\">UCC Intelligence Settings</span></button><div class=\"ucc-platform-dashboard-control\" data-ucc-dashboard-control=\"\"><label for=\"uccDashboardSelect\">Dashboard</label><select id=\"uccDashboardSelect\"><option value=\"criterion_1\">Criterion 1 \u00b7 Leadership and Strategic Planning</option><option value=\"criterion_2\">Criterion 2 \u00b7 Corporate Administration</option><option value=\"criterion_3\">Criterion 3 \u00b7 External Recruitment Agents</option><option value=\"criterion_4\">Criterion 4 \u00b7 Student Protection and Support Services</option><option selected=\"\" value=\"criterion_5\">Criterion 5 \u00b7 Academic Systems and Processes</option><option value=\"criterion_6\">Criterion 6 \u00b7 Quality Assurance, Innovation and Continual Improvement</option><option value=\"criterion_7\">Criterion 7 \u00b7 Performance Outcomes</option></select></div><button aria-expanded=\"true\" aria-label=\"Minimise UCC navigation\" class=\"ucc-shell-collapse-toggle\" data-shell-toggle=\"\" title=\"Minimise navigation\" type=\"button\"><span aria-hidden=\"true\" class=\"ucc-shell-toggle-icon\" data-shell-toggle-icon=\"\">\u2039</span><span class=\"ucc-visually-hidden\" data-shell-toggle-label=\"\">Minimise navigation</span></button></header><main class=\"ucc-platform-main\"><section class=\"ucc-platform-workspace\" data-ucc-workspace-panel=\"analytics\"><div class=\"ucc-criterion-dashboard\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_5\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_5\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_4\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_4\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_1\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_1\" data-live-api=\"1\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_2\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_2\" data-live-api=\"1\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_3\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_3\" data-live-api=\"1\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_6\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_6\" data-live-api=\"1\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_7\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_7\" data-live-api=\"1\"></div></section><section class=\"ucc-platform-workspace\" data-ucc-workspace-panel=\"explore\" hidden=\"\">\n<div class=\"ucc-explore-hub\" data-ucc-explore=\"\">\n<header class=\"ucc-explore-hero\">\n<div>\n<span class=\"ucc-explore-kicker\">DIAGRAM EXPLORER</span>\n<h1>Find live diagrams without opening another dashboard page</h1>\n<p>Search all Criterion 1\u20137 visual catalogues. Criteria 1, 2, 3, 6 and 7 use permission-aware live API foundations; Criteria 4 and 5 retain their established live implementations.</p>\n</div>\n<div class=\"ucc-explore-summary\">\n<article><span>Criterion 4</span><strong data-ucc-explore-count=\"criterion_4\">0</strong><small>live visuals</small></article>\n<article><span>Criterion 5</span><strong data-ucc-explore-count=\"criterion_5\">0</strong><small>live visuals</small></article>\n<article><span>Live foundations</span><strong>5</strong><small>permission-aware APIs</small></article>\n</div>\n</header>\n<div class=\"ucc-explore-controls\">\n<label><span>Search</span><input autocomplete=\"off\" data-ucc-explore-search=\"\" placeholder=\"Search diagram, section, type or source\" role=\"searchbox\" spellcheck=\"false\" type=\"text\"/></label>\n<label><span>Section</span><select data-ucc-explore-section=\"\"><option value=\"\">All sections</option></select></label>\n<label><span>Visual type</span><select data-ucc-explore-type=\"\"><option value=\"\">All visual types</option></select></label>\n<button data-ucc-explore-clear=\"\" type=\"button\">Clear</button>\n</div>\n<div class=\"ucc-explore-layout\">\n<aside class=\"ucc-explore-catalogue\">\n<div class=\"ucc-explore-catalogue-head\">\n<div><strong>Available diagrams</strong><small data-ucc-explore-result-count=\"\">Scanning platform\u2026</small></div>\n<span class=\"ucc-explore-live-pill\">Live</span>\n</div>\n<div class=\"ucc-explore-list\" data-ucc-explore-list=\"\"></div>\n</aside>\n<section class=\"ucc-explore-guide\">\n<div class=\"ucc-explore-guide-card\">\n<span class=\"ucc-explore-step\">1</span>\n<div><strong>Choose the dashboard</strong><p>Use the existing Criterion selector in the top bar.</p></div>\n</div>\n<div class=\"ucc-explore-guide-card\">\n<span class=\"ucc-explore-step\">2</span>\n<div><strong>Search or filter</strong><p>The catalogue is generated from the real chart elements, so future diagrams appear automatically.</p></div>\n</div>\n<div class=\"ucc-explore-guide-card\">\n<span class=\"ucc-explore-step\">3</span>\n<div><strong>Open the live card</strong><p>One click takes you to the original analytics card. No duplicate rendering logic or copied data.</p></div>\n</div>\n<div class=\"ucc-explore-note\">\n<strong>Why this approach scales</strong>\n<p>Explore is a fast index over the existing dashboards\u2014not a second dashboard system. Criterion-specific calculations, D3 renderers, tables, exports and record links remain in their original tested components.</p>\n</div>\n</section>\n</div>\n</div>\n</section><section class=\"ucc-platform-workspace\" data-ucc-workspace-panel=\"ask\" hidden=\"\"><div class=\"ucc-ask\" data-ucc-ask=\"\"><div class=\"ucc-ask-layout\"><div class=\"ucc-ask-main\"><header class=\"ucc-ask-head\"><div class=\"ucc-ask-head-copy\"><h2 id=\"uccAskTitle\">Ask UCC</h2><p>Ask about a selected record, or use a verified FAQ for a direct answer.</p></div><aside class=\"ucc-ask-assurance\" data-ask-assurance=\"\"></aside></header><section class=\"ucc-ask-controls\" aria-labelledby=\"uccAskTitle\"><div class=\"ucc-ask-row\"><label class=\"ucc-ask-field\"><span>Module</span><select data-ask-module=\"\"></select></label><label class=\"ucc-ask-field ucc-ask-field-grow\"><span>Record</span><input autocomplete=\"off\" data-ask-record=\"\" placeholder=\"Search by name or ID\u2026\" type=\"text\"/><div class=\"ucc-ask-suggestions\" data-ask-suggestions=\"\" hidden=\"\" role=\"listbox\"></div></label><div class=\"ucc-ask-field\"><span id=\"uccAskStatusLabel\">Status</span><p aria-labelledby=\"uccAskStatusLabel\" class=\"ucc-ask-record-status\" data-ask-record-status=\"\" data-state=\"none\">No record selected</p></div></div><label class=\"ucc-ask-field\"><span>Question</span><textarea data-ask-question=\"\" rows=\"2\" placeholder=\"Ask a question about the selected record\"></textarea></label><div class=\"ucc-ask-actions\"><button class=\"ucc-ask-submit\" data-ask-submit=\"\" type=\"button\"></button><button class=\"ucc-ask-clear\" data-ask-clear=\"\" hidden=\"\" type=\"button\"></button></div></section><div class=\"ucc-ask-guided\" data-ask-guided=\"\" hidden=\"\"><div aria-label=\"Question categories\" class=\"ucc-ask-categories\" data-ask-categories=\"\" role=\"tablist\"></div><div class=\"ucc-ask-faq-head\"><h3>Verified FAQs</h3><p>Direct answers from live records, no AI interpretation</p></div><div class=\"ucc-ask-questions\" data-ask-questions=\"\"></div></div><div class=\"ucc-ask-status\" data-ask-status=\"\" hidden=\"\" role=\"status\"></div><section aria-label=\"Answers\" aria-live=\"polite\" class=\"ucc-ask-thread\" data-ask-thread=\"\"></section></div><aside aria-label=\"Record context\" class=\"ucc-ask-context\" data-ask-context=\"\"></aside></div></div></section><section class=\"ucc-platform-workspace\" data-ucc-workspace-panel=\"operations\" hidden=\"\"><div class=\"ucc-ops\" data-ucc-ops=\"\"><header class=\"ucc-ops-head\"><div><h2>Operations</h2><p>What needs dealing with, and what this institution knows.</p></div><div class=\"ucc-ops-tabs\" role=\"tablist\"><button type=\"button\" class=\"is-active\" data-ops-tab=\"monitoring\" aria-selected=\"true\" role=\"tab\">Monitoring</button><button type=\"button\" data-ops-tab=\"knowledge\" aria-selected=\"false\" role=\"tab\">Document knowledge</button></div></header><div class=\"ucc-ops-panel\" data-ops-panel=\"monitoring\"></div><div class=\"ucc-ops-panel\" data-ops-panel=\"knowledge\" hidden=\"\"></div></div></section></main></div>";

function initPlatformShell(root) {
"use strict";
if (!root || root.dataset.platformReady === "1") {
return;
}
root.dataset.platformReady = "1";
const workspaceButtons = Array.from(
root.querySelectorAll("[data-ucc-workspace]")
);
const workspacePanels = Array.from(
root.querySelectorAll("[data-ucc-workspace-panel]")
);
const dashboardControl = root.querySelector("[data-ucc-dashboard-control]");
const status = root.querySelector("[data-ucc-platform-status]");
const dashboardSelect = root.querySelector("#uccDashboardSelect");
function setWorkspace(workspace) {
workspaceButtons.forEach(function (button) {
const active = button.dataset.uccWorkspace === workspace;
button.classList.toggle("is-active", active);
button.setAttribute("aria-pressed", active ? "true" : "false");
});
workspacePanels.forEach(function (panel) {
panel.hidden = panel.dataset.uccWorkspacePanel !== workspace;
});
if (dashboardControl) {
dashboardControl.hidden = workspace !== "analytics" && workspace !== "explore";
}
// Operations loads on first entry rather than at boot: two extra round trips
// most sessions never need, and a criterion tab should not wait on the
// monitoring engine to render.
if (workspace === "operations" && window.UCCOperations) {
window.UCCOperations.open(root);
}
if (status) {
if (workspace === "analytics") {
status.textContent = "Analytics is active. Criteria 1–7 now use permission-aware live sources or live API foundations; unavailable fields are shown explicitly.";
} else if (workspace === "explore") {
status.textContent = "Explore is active. Search the visual catalogue and open the original live diagram in one click.";
} else {
status.textContent = "Ask UCC is active. Choose the assistant and record first; guided questions work without OpenAI.";
}
}
}
workspaceButtons.forEach(function (button) {
button.addEventListener("click", function () {
setWorkspace(button.dataset.uccWorkspace);
});
});
const dashboardPanels = Array.from(root.querySelectorAll("[data-dashboard-panel]"));
const shell = root.querySelector(".ucc-platform-shell");
const shellToggle = root.querySelector("[data-shell-toggle]");
const shellToggleIcon = root.querySelector("[data-shell-toggle-icon]");
const shellToggleLabel = root.querySelector("[data-shell-toggle-label]");
const CRITERION_LABELS = Object.freeze({"criterion_1": "Criterion 1 · Leadership and Strategic Planning", "criterion_2": "Criterion 2 · Corporate Administration", "criterion_3": "Criterion 3 · External Recruitment Agents", "criterion_4": "Criterion 4 · Student Protection and Support Services", "criterion_5": "Criterion 5 · Academic Systems and Processes", "criterion_6": "Criterion 6 · Quality Assurance, Innovation and Continual Improvement", "criterion_7": "Criterion 7 · Performance Outcomes"});
let shellCollapsed = false;

function activeWorkspaceName() {
const active = workspaceButtons.find(function (button) { return button.classList.contains("is-active"); });
return active ? active.dataset.uccWorkspace : "analytics";
}
function scrollDashboardToTop(dashboard) {
const panel = dashboardPanels.find(function (item) { return item.dataset.dashboardPanel === dashboard; });
const target = panel ? (panel.querySelector(".hero") || panel) : root;
requestAnimationFrame(function () {
try {
target.scrollIntoView({ behavior: "smooth", block: "start", inline: "nearest" });
} catch (error) {
try { target.scrollIntoView(true); } catch (ignored) {}
}
let current = root.parentElement;
while (current && current !== document.body) {
const style = window.getComputedStyle(current);
const scrollable = /(auto|scroll)/.test(style.overflowY || "") && current.scrollHeight > current.clientHeight;
if (scrollable) {
const top = Math.max(0, target.getBoundingClientRect().top - current.getBoundingClientRect().top + current.scrollTop - 12);
try { current.scrollTo({ top: top, behavior: "smooth" }); } catch (error) { current.scrollTop = top; }
break;
}
current = current.parentElement;
}
});
}
function setDashboard(dashboard) {
dashboardPanels.forEach(function (panel) { panel.classList.toggle("ucc-hidden", panel.dataset.dashboardPanel !== dashboard); });
if (dashboardSelect && dashboardSelect.value !== dashboard) dashboardSelect.value = dashboard;
if (status) {
const workspace = activeWorkspaceName();
if (workspace === "explore") status.textContent = "Explore is active. Search the live visual catalogue for the selected criterion.";
else if (workspace === "ask") status.textContent = "Ask UCC is active. Choose the assistant and record first.";
else {
const label = CRITERION_LABELS[dashboard] || dashboard;
const fullLive = dashboard === "criterion_4" || dashboard === "criterion_5";
status.textContent = fullLive
? label + " is active with mature live, permission-aware analytics."
: label + " is active with a permission-aware live API foundation. Unsupported fields are shown explicitly.";
}
}
try { localStorage.setItem("ucc.dashboard", dashboard); } catch (error) {}
scrollDashboardToTop(dashboard);
try { root.dispatchEvent(new CustomEvent("ucc:dashboard-change", { detail: { dashboard: dashboard } })); } catch (error) {}
}
if (dashboardSelect) dashboardSelect.addEventListener("change", function () { setDashboard(dashboardSelect.value); });
function applyShellState() {
if (!shell || !shellToggle) return;
shell.classList.toggle("is-collapsed", shellCollapsed);
shellToggle.setAttribute("aria-expanded", shellCollapsed ? "false" : "true");
shellToggle.setAttribute("aria-label", shellCollapsed ? "Expand UCC navigation" : "Minimise UCC navigation");
shellToggle.setAttribute("title", shellCollapsed ? "Expand navigation" : "Minimise navigation");
if (shellToggleIcon) shellToggleIcon.textContent = shellCollapsed ? "›" : "‹";
if (shellToggleLabel) shellToggleLabel.textContent = shellCollapsed ? "Expand navigation" : "Minimise navigation";
}
let shellPlaceholder = null;
function frappeTopOffset() {
const navbar = document.querySelector(".navbar.navbar-expand, header.navbar, .desk-navbar, .navbar");
if (!navbar) return 8;
const rect = navbar.getBoundingClientRect();
return rect.bottom > 0 ? Math.max(8, Math.round(rect.bottom + 8)) : 8;
}
function syncFloatingShell() {
if (!shell || !root.isConnected) return;
if (!shellPlaceholder) {
shellPlaceholder = document.createElement("div");
shellPlaceholder.className = "ucc-platform-shell-placeholder";
shell.parentNode.insertBefore(shellPlaceholder, shell);
}
const top = frappeTopOffset();
const rootRect = root.getBoundingClientRect();
const anchorRect = shellPlaceholder.getBoundingClientRect();
const shellHeight = Math.max(58, Math.round(shell.getBoundingClientRect().height || shell.offsetHeight || 58));
const shouldFloat = anchorRect.top <= top && rootRect.bottom > top + shellHeight + 16;
shell.classList.toggle("is-floating", shouldFloat);
root.classList.toggle("has-floating-shell", shouldFloat);
root.style.setProperty("--ucc-dashboard-sticky-top", String(top + shellHeight + 10) + "px");
if (shouldFloat) {
const width = shellCollapsed ? Math.min(108, rootRect.width) : Math.min(1500, rootRect.width);
const left = shellCollapsed ? rootRect.left : rootRect.left + Math.max(0, (rootRect.width - width) / 2);
shell.style.setProperty("--ucc-shell-floating-top", String(top) + "px");
shell.style.setProperty("--ucc-shell-floating-left", String(Math.round(left)) + "px");
shell.style.setProperty("--ucc-shell-floating-width", String(Math.round(width)) + "px");
shellPlaceholder.style.height = String(shellHeight + 10) + "px";
} else {
shell.style.removeProperty("--ucc-shell-floating-top");
shell.style.removeProperty("--ucc-shell-floating-left");
shell.style.removeProperty("--ucc-shell-floating-width");
shellPlaceholder.style.height = "0px";
}
}
if (shellToggle) shellToggle.addEventListener("click", function (event) {
event.preventDefault();
event.stopPropagation();
shellCollapsed = !shellCollapsed;
applyShellState();
requestAnimationFrame(syncFloatingShell);
});
let savedDashboard = "criterion_5";
try { savedDashboard = localStorage.getItem("ucc.dashboard") || savedDashboard; } catch (error) {}
try {
const urlDashboard = new URLSearchParams(location.search).get("dashboard");
if (urlDashboard) savedDashboard = urlDashboard;
} catch (error) {}
if (!["criterion_1", "criterion_2", "criterion_3", "criterion_4", "criterion_5", "criterion_6", "criterion_7"].includes(savedDashboard)) savedDashboard = "criterion_5";
setWorkspace("analytics");
setDashboard(savedDashboard);
applyShellState();
requestAnimationFrame(syncFloatingShell);
document.addEventListener("scroll", syncFloatingShell, true);
window.addEventListener("resize", syncFloatingShell);
if (typeof ResizeObserver !== "undefined") {
const shellResizeObserver = new ResizeObserver(syncFloatingShell);
shellResizeObserver.observe(root);
shellResizeObserver.observe(shell);
}
}

function initAnalyticsEngine(platform){
"use strict";
if(!platform||platform.dataset.liveFoundationReady==="1")return;
platform.dataset.liveFoundationReady="1";
const CONFIG={"criterion_1":{"number":"1","title":"Leadership and Strategic Planning","description":"Live, permission-aware analytics foundation for leadership, governance and strategic planning. Source and metric availability is resolved from ERPNext permissions.","subcriteria":[["1.1.1","Leadership and Corporate Governance"],["1.2.1","Strategic Planning"]],"sections":{"overview":{"title":"Overview","charts":[]},"1.1":{"title":"Leadership and Corporate Governance","charts":[]},"1.2":{"title":"Strategic Planning","charts":[]},"1.1.1":{"title":"Leadership and Corporate Governance","charts":[]},"1.2.1":{"title":"Strategic Planning","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_1","defaultSection":"1.1.1","apiSections":{"overview":"1.1.1","1.1.1":"1.1.1","1.2.1":"1.2.1","quality":"1.1.1","sources":"1.1.1"},"panelMap":{"overview":"overview","1.1.1":"1.1.1","1.2.1":"1.2.1","sources":"sources","quality":"sources"},"filters":[["academic_year","Academic Year",["All Academic Years","2026","2025"]],["student_group","Module Class Details",["All Module Classes"]],["program","Course",["All Courses"]],{"key":"month","label":"Month","type":"month"}]},"criterion_2":{"number":"2","title":"Corporate Administration","description":"Live, permission-aware analytics foundation for human resources, communication, knowledge management and feedback. Unsupported fields are shown explicitly.","subcriteria":[["2.1.1","Staff Selection and Management"],["2.1.2","Staff Training and Development"],["2.2.1","Internal and External Communication"],["2.3.1","Data and Information Management"],["2.3.2","Knowledge Management"],["2.4.1","Feedback Management"],["2.4.2","Student Satisfaction Survey"],["2.4.3","Staff Satisfaction Survey"]],"sections":{"overview":{"title":"Overview","charts":[]},"2.1":{"title":"Human Resource","charts":[]},"2.2":{"title":"Communication","charts":[]},"2.3":{"title":"Data, Information and Knowledge Management","charts":[]},"2.4":{"title":"Feedback Management","charts":[]},"2.1.1":{"title":"Human Resource","charts":[]},"2.1.2":{"title":"Staff Training and Development","charts":[]},"2.2.1":{"title":"Communication","charts":[]},"2.3.1":{"title":"Data, Information and Knowledge Management","charts":[]},"2.3.2":{"title":"Knowledge Management","charts":[]},"2.4.1":{"title":"Feedback Management","charts":[]},"2.4.2":{"title":"Student Satisfaction Survey","charts":[]},"2.4.3":{"title":"Staff Satisfaction Survey","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_2","defaultSection":"2.1.1","apiSections":{"overview":"2.1.1","2.1.1":"2.1.1","2.1.2":"2.1.2","2.2.1":"2.2.1","2.3.1":"2.3.1","2.3.2":"2.3.2","2.4.1":"2.4.1","2.4.2":"2.4.2","2.4.3":"2.4.3","quality":"2.1.1","sources":"2.1.1"},"panelMap":{"overview":"overview","2.1.1":"2.1.1","2.1.2":"2.1.2","2.2.1":"2.2.1","2.3.1":"2.3.1","2.3.2":"2.3.2","2.4.1":"2.4.1","2.4.2":"2.4.2","2.4.3":"2.4.3","sources":"sources","quality":"sources"},"filters":[["academic_year","Academic Year",["All Academic Years","2026","2025"]],["student_group","Module Class Details",["All Module Classes"]],["program","Course",["All Courses"]],{"key":"month","label":"Month","type":"month"}]},"criterion_3":{"number":"3","title":"External Recruitment Agents","description":"Policy-aligned live analytics foundation for agent selection, appointment, onboarding, performance evaluation, renewal and offboarding. Unsupported fields are shown explicitly.","policy_set":[{"code":"PPD-SES-SL-3.1.1","version":"1.2","title":"Selection and Appointment of External Recruitment Agents","updated":"15 January 2026"},{"code":"PPD-SES-SL-3.2.1","version":"1.2","title":"Management and Evaluation of Recruitment Agents","updated":"15 January 2026"}],"subcriteria":[["3.1.1","Selection and Appointment"],["3.2.1","Management and Evaluation"]],"filters":[["review_year","Review Year",["All Review Years","2026","2025"]],["agent_status","Agent Status",["All Agent Statuses","Active","Pending","Inactive"]],["market","Market / Region",["All Markets","Southeast Asia","South Asia","Greater China","Other"]],["renewal_cycle","Renewal Cycle",["All Renewal Cycles","June","December"]]],"sections":{"overview":{"title":"Criterion 3 Overview","charts":[]},"3.1.1":{"title":"Selection and Appointment of External Recruitment Agents","charts":[]},"3.2.1":{"title":"Management and Evaluation of Recruitment Agents","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_3","defaultSection":"3.1.1","apiSections":{"overview":"3.1.1","3.1.1":"3.1.1","3.2.1":"3.2.1","quality":"3.1.1","sources":"3.1.1"},"panelMap":{"overview":"overview","3.1.1":"3.1.1","3.2.1":"3.2.1","sources":"sources","quality":"sources"}},"criterion_4":{"number":"4","title":"Student Protection and Support Services","description":"Live, permission-aware analytics for admissions, contracts, fees, student movement, refunds, student support, conduct and attendance.","subcriteria":[["4.1.1","Pre-Course Counselling, Selection and Admissions"],["4.2.1","Student Contract"],["4.2.2","Fee Collection and Fee Protection Scheme"],["4.3.1","Course Transfer, Deferment and Withdrawal"],["4.4.1","Refund"],["4.5.1","Student Support Services"],["4.6.1","Student Conduct and Attendance"]],"filters":[["academic_year","Academic Year",["All Academic Years"]],["program","Programme",["All Programmes"]],["intake","Intake",["All Intakes"]],["status","Status",["All Statuses"]],["nationality","Country / Nationality",["All Countries"]],["agent","Recruitment Agent",["All Agents"]]],"sections":{"overview":{"title":"Overview","charts":[]},"4.1.1":{"title":"Pre-Course Counselling, Selection and Admissions","charts":[]},"4.2.1":{"title":"Student Contract","charts":[]},"4.2.2":{"title":"Fee Collection and Fee Protection Scheme","charts":[]},"4.3.1":{"title":"Course Transfer, Deferment and Withdrawal","charts":[]},"4.4.1":{"title":"Refund","charts":[]},"4.5.1":{"title":"Student Support Services","charts":[]},"4.6.1":{"title":"Student Conduct and Attendance","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_4","defaultSection":"4.1.1","apiSections":{"overview":"4.1.1","4.1.1":"4.1.1","4.2.1":"4.2.1","4.2.2":"4.2.2","4.3.1":"4.3.1","4.4.1":"4.4.1","4.5.1":"4.5.1","4.6.1":"4.6.1","quality":"4.1.1","sources":"4.1.1"},"panelMap":{"overview":"overview","4.1.1":"4.1.1","4.2.1":"4.2.1","4.2.2":"4.2.2","4.3.1":"4.3.1","4.4.1":"4.4.1","4.5.1":"4.5.1","4.6.1":"4.6.1","sources":"sources","quality":"sources"}},"criterion_5":{"number":"5","title":"Academic Systems and Processes","description":"Live, permission-aware analytics for course design, review, planning, delivery, partnerships, student feedback, learning support and assessment.","subcriteria":[["5.1.1","Course Design and Development"],["5.1.2","Course Review"],["5.2.1","Course Planning"],["5.2.2","Course Delivery"],["5.3.1","Partnership Management"],["5.4","Student Feedback and Learning Support"],["5.5","Assessment"]],"sections":{"overview":{"title":"Overview","charts":[]},"5.1.1":{"title":"Course Design and Development","charts":[]},"5.1.2":{"title":"Course Review","charts":[]},"5.2.1":{"title":"Course Planning","charts":[]},"5.2.2":{"title":"Course Delivery","charts":[]},"5.3.1":{"title":"Partnerships","charts":[]},"5.4":{"title":"Student Feedback and Learning Support","charts":[]},"5.5":{"title":"Assessment","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_5","defaultSection":"5.1.1","apiSections":{"overview":"5.1.1","5.1.1":"5.1.1","5.1.2":"5.1.2","5.2.1":"5.2.1","5.2.2":"5.2.2","5.3.1":"5.3.1","5.4":"5.4","5.5":"5.5","quality":"5.1.1","sources":"5.1.1"},"panelMap":{"overview":"overview","5.1.1":"5.1.1","5.1.2":"5.1.2","5.2.1":"5.2.1","5.2.2":"5.2.2","5.3.1":"5.3.1","5.4":"5.4","5.5":"5.5","sources":"sources","quality":"sources"},"filters":[["year","Academic Year",["All Academic Years"]],["student_group","Module Class Details",["All Module Classes"]],["program","Course",["All Courses"]],["status","Status",["All Statuses"]]]},"criterion_6":{"number":"6","title":"Quality Assurance, Innovation and Continual Improvement","description":"Policy-aligned live analytics foundation for audits, management review, innovation, providers, risk and business continuity. Unsupported fields are shown explicitly.","policy_set":[{"code":"PPD-SGL-SQ-6.1.1","version":"1.2","title":"Internal Assessment and Quality Audits","updated":"15 January 2026"},{"code":"PPD-SGL-SQ-6.2.1","version":"1.3","title":"Management Review","updated":"10 April 2026"},{"code":"PPD-SGL-SQ-6.3.1","version":"1.2","title":"Innovation and Continual Improvement","updated":"15 January 2026"},{"code":"PPD-OE-FN-6.4.1","version":"1.2","title":"Provider's Accreditation and Evaluation","updated":"15 January 2026"},{"code":"PPD-SGL-SQ-6.5.3","version":"1.2","title":"Hazard Identification and Risk Assessment","updated":"15 January 2026"}],"subcriteria":[["6.1.1","Internal Assessment and Quality Audits"],["6.2.1","Management Review"],["6.3.1","Innovation and Continual Improvement"],["6.4.1","Provider Accreditation and Evaluation"],["6.5.3","Hazard Identification and Risk Assessment"]],"filters":[["review_year","Review Year",["All Review Years","2026","2025"]],["department","Department",["All Departments","SGL / SQ","Academic","Student Services","Finance"]],["quality_area","Quality Area",["All Quality Areas","Audit","Management Review","Innovation","Providers","Risk"]],["month","Month",["All Months","January 2026","April 2026","July 2026","December 2026"]]],"sections":{"overview":{"title":"Criterion 6 Overview","charts":[]},"6.1.1":{"title":"Internal Assessment and Quality Audits","charts":[]},"6.2.1":{"title":"Management Review","charts":[]},"6.3.1":{"title":"Innovation and Continual Improvement","charts":[]},"6.4.1":{"title":"Provider's Accreditation and Evaluation","charts":[]},"6.5.3":{"title":"Hazard Identification and Risk Assessment","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_6","defaultSection":"6.1.1","apiSections":{"overview":"6.1.1","6.1.1":"6.1.1","6.2.1":"6.2.1","6.3.1":"6.3.1","6.4.1":"6.4.1","6.5.3":"6.5.3","quality":"6.1.1","sources":"6.1.1"},"panelMap":{"overview":"overview","6.1.1":"6.1.1","6.2.1":"6.2.1","6.3.1":"6.3.1","6.4.1":"6.4.1","6.5.3":"6.5.3","sources":"sources","quality":"sources"}},"criterion_7":{"number":"7","title":"Performance Outcomes","description":"Live, permission-aware analytics foundation for outcome measurement, target achievement and stakeholder performance. Unsupported fields are shown explicitly.","subcriteria":[["7.1.1","Measurement of Outcomes"]],"sections":{"overview":{"title":"Overview","charts":[]},"7.1":{"title":"Measurement of Outcomes","charts":[]},"7.1.1":{"title":"Measurement of Outcomes","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_7","defaultSection":"7.1.1","apiSections":{"overview":"7.1.1","7.1.1":"7.1.1","quality":"7.1.1","sources":"7.1.1"},"panelMap":{"overview":"overview","7.1.1":"7.1.1","sources":"sources","quality":"sources"},"filters":[["academic_year","Academic Year",["All Academic Years","2026","2025"]],["student_group","Module Class Details",["All Module Classes"]],["program","Course",["All Courses"]],{"key":"month","label":"Month","type":"month"}]}};
function esc(value){return String(value==null?"":value).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");}

function analyticsPanelMarkup(criterionId,key,title){
const isOverview=key==="overview";
return`<section class="panel-view${isOverview?"":" hidden"}" data-demo-panel="${esc(key)}"><div class="ucc-tab-intro" data-tab-intro="${esc(key)}"></div><div class="ucc-section-visual-anchor" data-live-anchor="${esc(key)}"></div><article class="panel ucc-shared-panel ucc-management-panel"><div class="panel-head"><h2>Management Questions and Data-Based Answers</h2></div><div class="table-wrap"><table class="qa-table"><thead><tr><th>Criterion</th><th>Question</th><th>Answer</th><th>Source / Calculation</th><th>Status</th></tr></thead><tbody data-demo-qa="${esc(criterionId+":"+key)}"></tbody></table></div></article></section>`;
}
function sourcesQualityPanelMarkup(criterionId){
return`<section class="panel-view hidden ucc-sources-quality-panel" data-demo-panel="sources"><div class="ucc-sources-quality-grid"><article class="panel ucc-shared-panel"><div class="panel-head"><div><h2>Source Availability</h2><p class="panel-subtitle">Resolved against the signed-in user's permissions.</p></div></div><div class="table-wrap"><table><thead><tr><th>Resolved DocType</th><th>Source key</th><th>Status</th><th>Records</th></tr></thead><tbody data-demo-sources="${esc(criterionId)}"></tbody></table></div></article><article class="panel ucc-shared-panel"><div class="panel-head"><div><h2>Data Quality Checks</h2><p class="panel-subtitle">Unavailable sources, permissions and unsupported fields are shown explicitly.</p></div></div><div class="table-wrap"><table><thead><tr><th>Check</th><th>Source</th><th>Status</th><th>Detail</th></tr></thead><tbody data-demo-quality="${esc(criterionId)}"></tbody></table></div></article></div></section>`;
}
function dashboardShellMarkup(criterionId,config){
const tabs=[['overview','Overview']].concat(config.subcriteria||[]).concat([['sources','Sources & Data Quality']]);
const tabMarkup=tabs.map((item,index)=>`<button type="button" class="${index===0?"active":""}" data-demo-tab="${esc(item[0])}">${esc(item[0]==="overview"||item[0]==="sources"?item[1]:item[0]+" "+item[1])}</button>`).join("");
const panels=[analyticsPanelMarkup(criterionId,'overview',config.sections?.overview?.title||'Overview')].concat((config.subcriteria||[]).map(item=>analyticsPanelMarkup(criterionId,item[0],item[1]))).join("")+sourcesQualityPanelMarkup(criterionId);
return`<div class="ucc-unified-dashboard"><div class="loading-overlay hidden" data-demo-loading-overlay><div class="loading-card"><div class="spinner"></div><strong data-demo-loading-title>Loading Criterion ${esc(config.number)}</strong><div class="progress-track"><div class="progress-fill" data-demo-progress-fill></div></div><div class="progress-text"><span data-demo-progress-value>0%</span> · <span>Permission-aware sources</span></div></div></div><header class="hero ucc-shared-hero ucc-standard-criterion-hero"><div class="hero-copy"><span class="ucc-criterion-kicker">EDUTRUST CRITERION ${esc(config.number)}</span><h1>Criterion ${esc(config.number)} · ${esc(config.title)}</h1><p>${esc(config.description)}</p></div><div class="hero-action-card ucc-shared-action-card ucc-standard-hero-actions" aria-label="Criterion ${esc(config.number)} analytics actions"><button type="button" class="primary-btn" data-demo-action="refresh">Refresh</button><button type="button" data-demo-action="export-qa">Export Q&amp;A CSV</button><button type="button" data-demo-action="export-exceptions">Export Exceptions CSV</button><button type="button" data-demo-action="diagnostics">Diagnostics Log (<span data-demo-log-count>0</span>)</button></div></header><div class="sticky-navigation"><nav class="tabs ucc-shared-tabs" data-demo-tabs aria-label="Criterion ${esc(config.number)} sections">${tabMarkup}</nav></div><div class="ucc-criterion-notice ucc-readiness-strip" data-demo-readiness data-status="loading" hidden><div class="ucc-criterion-notice-copy"><strong data-demo-readiness-title></strong><span data-demo-readiness-copy></span></div></div><div class="ucc-unified-panel-stack">${panels}</div></div>`;
}
function mountUnifiedDashboards(){
platform.querySelectorAll('[data-dashboard-panel]').forEach(function(dashboard){
const criterionId=dashboard.dataset.dashboardPanel,criterionConfig=CONFIG[criterionId];
if(!criterionConfig)return;
dashboard.classList.add('ucc-criterion-dashboard','ucc-demo-dashboard');
dashboard.classList.remove('ucc-c4-dashboard','ucc-c5-v41');
dashboard.dataset.demoDashboard=criterionId;
dashboard.dataset.demoActiveTab='overview';
dashboard.dataset.dashboardArchitecture='shared-v2';
dashboard.innerHTML=dashboardShellMarkup(criterionId,criterionConfig);
});
}
function finiteNumber(value,fallback=0){const number=Number(value);return Number.isFinite(number)?number:fallback;}
function normaliseApiMessage(response){
let message=response&&response.message!==undefined?response.message:response;
for(let depth=0;depth<3;depth++){
if(typeof message==="string"){
try{message=JSON.parse(message);}catch(error){break;}
continue;
}
if(message&&typeof message==="object"&&!message.ok&&message.message&&typeof message.message==="object"){
message=message.message;
continue;
}
break;
}
return message;
}
function apiErrorMessage(error){
if(!error)return"Analytics request failed.";
if(typeof error==="string")return error;
// Read the xhr the same way the shared helper does, so a 403/PermissionError
// carried on responseJSON survives to the point where it can be classified.
const shared=UCCShared.errorText(error);
if(shared&&shared!=="Request failed")return shared;
if(error.message)return String(error.message);
if(error._server_messages){
try{
const messages=JSON.parse(error._server_messages);
if(Array.isArray(messages)&&messages.length){
const parsed=JSON.parse(messages[0]);
return parsed.message||String(messages[0]);
}
}catch(parseError){}
}
return error.exc_type||error.statusText||"Analytics request failed.";
}
function csvCell(value){const text=String(value==null?"":value);return/[",\n]/.test(text)?`"${text.replaceAll('"','""')}"`:text;}
function download(name,content,type="text/csv;charset=utf-8"){const blob=new Blob(["\ufeff",content],{type});const url=URL.createObjectURL(blob);const link=document.createElement("a");link.href=url;link.download=name;document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);}
function statusBadge(status){const raw=String(status||"available"),label=raw.replaceAll("_"," ");const cls=/risk|error|denied|unavailable|failed/i.test(raw)?"risk":/warn|unsupported|partial|pending|overdue/i.test(raw)?"warning":"good";const tip=/denied|not permitted/i.test(raw)?' title="Your account does not have read access to this. Ask an administrator to grant access if you need to see this."':"";return`<span class="ucc-demo-status ${cls}"${tip}>${esc(label)}</span>`;}
function activeSection(dashboard){return dashboard.dataset.demoActiveTab||"overview";}
// ---------------------------------------------------------------------------
// PER-TAB INSIGHTS CHARTS, TAB INTRO, AND THE QUESTION SELECTION
//
// A tab starts with NO charts and one "+ Add chart" button. Whatever a person
// adds is theirs, on that tab, at the size they chose, and is stored
// server-side (analytics/tab_charts.py -- frappe.defaults, per user). The same
// record holds the tab's intro text and which management questions it hides,
// because they are all "what this tab looks like to me".
//
// This replaced 222 fixed chart boxes declared in this file: 16 had a real
// Insights query behind them, 206 were blank. Nothing is declared here now, so
// nothing can be declared and then not exist.
//
// It also replaced three things that pre-dated the move to Insights and could
// not survive it:
//   - the page-level filter bar. An embedded chart is a live view of a SAVED
//     Insights query; this page cannot re-filter it. A filtered view is a
//     second Insights chart, built in Insights and added here like any other.
//   - the "Criterion N live analytics active · X of X sources" readiness strip
//   - the KPI number cards
// All three read the criterion engine's own catalogue, which no longer answers
// anything on screen.
// ---------------------------------------------------------------------------
const tabChartState={};

// #5: View is the default. A tab full of x buttons and drag handles reads as a
// draft, and these tabs are shown to auditors. The mode is per criterion and
// deliberately NOT persisted -- it is how you are looking at the tab right
// now, not how the tab is configured, and leaving someone in Edit mode across
// sessions is how a stray click becomes a change nobody meant.
const tabEditModes={};
function isEditing(dashboard,tab){
const state=tabConfig(dashboard,tab);
return !!(state&&state.canEdit&&tabEditModes[dashboard.dataset.demoDashboard]);
}

function tabChartKey(criterionId,tab){return criterionId+"::"+tab;}
function tabConfig(dashboard,tab){
return tabChartState[tabChartKey(dashboard.dataset.demoDashboard,tab)]||null;
}

function tabChartAreaMarkup(tab){
return`<section class="ucc-tab-charts" data-tab-charts="${esc(tab)}">`
+`<div class="ucc-tab-charts-head"><h2>Charts</h2>`
+`<div class="ucc-tab-charts-actions" data-tab-actions="${esc(tab)}"></div></div>`
+`<div class="ucc-tab-charts-grid" data-tab-charts-grid="${esc(tab)}"></div></section>`;
}

// The head is rebuilt whenever the mode or the permission changes, so a
// control is never left on screen for someone who cannot use it.
function renderTabActions(dashboard,tab){
const area=dashboard.querySelector(`.ucc-tab-charts[data-tab-charts="${CSS.escape(tab)}"]`);
const mount=area&&area.querySelector("[data-tab-actions]");
if(!mount)return;
const state=tabConfig(dashboard,tab);
const canEdit=!!(state&&state.canEdit);
const editing=isEditing(dashboard,tab);
mount.innerHTML=
`<button type="button" class="ucc-tab-action" data-tab-history="${esc(tab)}">History</button>`
+(editing?"":`<button type="button" class="ucc-tab-action" data-export-pdf="${esc(tab)}">Export PDF</button>`)
+(canEdit
?`<button type="button" class="ucc-tab-action ucc-tab-mode${editing?" is-editing":""}" `
+`data-toggle-edit="${esc(tab)}" aria-pressed="${editing}">${editing?"Done editing":"Edit tab"}</button>`
:"")
+(editing?`<button type="button" class="ucc-add-chart" data-add-chart="${esc(tab)}">+ Add chart</button>`:"");
area.classList.toggle("is-editing",editing);
}

// analyticsPanelMarkup() already emits an empty [data-live-anchor] between the
// tab intro and the Management Questions panel. Mounting there puts the charts
// between the two without this function needing to know about either.
function ensureTabChartArea(dashboard,config,tab){
const panelKey=(config.panelMap&&config.panelMap[tab])||tab;
if(panelKey==="quality"||panelKey==="sources")return null;
const anchor=dashboard.querySelector(`[data-live-anchor="${CSS.escape(panelKey)}"]`);
if(!anchor)return null;
let area=anchor.querySelector(`:scope > .ucc-tab-charts[data-tab-charts="${CSS.escape(tab)}"]`);
if(!area){
const holder=document.createElement("div");
holder.innerHTML=tabChartAreaMarkup(tab);
area=holder.firstElementChild;
anchor.appendChild(area);
}
renderTabActions(dashboard,tab);
return area;
}

// panelMap can point two tabs at one panel, so an anchor can hold more than
// one area. Only the active tab's is shown.
function syncTabChartVisibility(dashboard,tab){
dashboard.querySelectorAll("[data-tab-charts]").forEach(function(area){
area.hidden=area.dataset.tabCharts!==tab;
});
loadVisibleEmbeds(dashboard);
}

// EVERY SUB-CRITERION PANEL IS IN THE DOM AT ONCE.
//
// analyticsPanelMarkup() builds them all up front and switching tabs only
// toggles `hidden`. A hidden iframe with a src STILL LOADS, so putting the URL
// straight into the markup would boot one Insights SPA per sub-criterion the
// moment a criterion opens -- eight at once on Criterion 4. Measured on the
// live bench: four together took 3,823 ms and completed one after another,
// because same-origin frames share the parent's main thread.
//
// So the URL waits in data-embed-src and is promoted to src when the tab is
// actually shown. Promoted ONCE: the flag is removed with the attribute, so
// returning to a tab reuses the frame someone already waited for.
function loadVisibleEmbeds(root){
(root||document).querySelectorAll("iframe[data-embed-src]").forEach(function(frame){
const area=frame.closest("[data-tab-charts]");
if(area&&area.hidden)return;
const url=frame.dataset.embedSrc;
delete frame.dataset.embedSrc;
const started=(window.performance&&performance.now)?performance.now():0;
frame.addEventListener("load",function(){
const ms=started?Math.round(performance.now()-started):0;
const note=frame.parentNode&&frame.parentNode.querySelector("[data-embed-timing]");
if(note)note.textContent="Loaded in "+ms+" ms";
// Into the diagnostics log too, so the number survives the page being
// used rather than living only in a caption nobody screenshots.
const card=frame.closest("[data-dashboard-panel],.ucc-criterion-dashboard");
if(card)logEvent(card,"INFO","embed_loaded",
frame.dataset.embedName+" · "+ms+" ms");
},{once:true});
frame.src=url;
});
}


const RESPONSE_ADAPTERS=new Map();
function registerResponseAdapter(criterionId,adapter){if(criterionId&&typeof adapter==="function")RESPONSE_ADAPTERS.set(criterionId,adapter);}
function summaryFromRows(rows){const list=Array.isArray(rows)?rows:[],available=list.filter(item=>item&&item.status==="available").length,total=list.length;return{available,total,issues:Math.max(0,total-available)};}
function baseResponseAdapter(message,context){const raw=message&&typeof message==="object"?message:{};const metrics=Array.isArray(raw.metrics)?raw.metrics:[],sources=Array.isArray(raw.sources)?raw.sources:[];return{...raw,ok:raw.ok===true,meta:{...(raw.meta||{}),subcriterion:raw.meta?.subcriterion||context.subcriterion},metrics,sources,questions:Array.isArray(raw.questions)?raw.questions:(Array.isArray(raw.qa)?raw.qa:[]),exceptions:Array.isArray(raw.exceptions)?raw.exceptions:[],data_quality:Array.isArray(raw.data_quality)?raw.data_quality:(Array.isArray(raw.quality)?raw.quality:[]),source_summary:raw.source_summary||summaryFromRows(sources),metric_summary:raw.metric_summary||summaryFromRows(metrics)};}
registerResponseAdapter("criterion_4",function(message,context){const adapted=baseResponseAdapter(message,context);adapted.questions=adapted.questions.length?adapted.questions:(Array.isArray(message?.management_questions)?message.management_questions:[]);adapted.data_quality=adapted.data_quality.length?adapted.data_quality:(Array.isArray(message?.quality_checks)?message.quality_checks:[]);return adapted;});
function adaptApiResponse(config,dashboard,payload,message){const criterionId=dashboard.dataset.demoDashboard,adapter=RESPONSE_ADAPTERS.get(criterionId)||baseResponseAdapter;return adapter(message,{criterionId,config,payload,subcriterion:payload.subcriterion});}


const STATE=new Map();
const SAFE_COMPLEX_TYPES=new Set(["donut","funnel","trend"]);
function dashboardState(dashboard){if(!STATE.has(dashboard))STATE.set(dashboard,{loading:false,result:null,error:null,logs:[],lastSection:""});return STATE.get(dashboard);}
function logEvent(dashboard,level,event,detail){const state=dashboardState(dashboard);state.logs.push({time:new Date().toISOString(),level,event,detail:String(detail||"")});if(state.logs.length>500)state.logs.shift();const count=dashboard.querySelector("[data-demo-log-count]");if(count)count.textContent=String(state.logs.length);}
function apiSection(config,dashboard,tab){const state=dashboardState(dashboard);if(tab==="quality"||tab==="sources")return state.lastSection||config.defaultSection;const mapped=config.apiSections&&config.apiSections[tab];if(mapped&&tab!=="overview")state.lastSection=mapped;return mapped||state.lastSection||config.defaultSection;}
function callApi(config,dashboard,action="summary",extra={}){
return new Promise((resolve,reject)=>{
if(!(window.frappe&&frappe.call)){reject(new Error("Frappe API client is unavailable."));return;}
const payload={action,subcriterion:apiSection(config,dashboard,activeSection(dashboard)),filters:{},page_size:100};
Object.keys(extra||{}).forEach(key=>payload[key]=extra[key]);
logEvent(dashboard,"INFO","api_request",`${config.apiMethod} · ${payload.subcriterion} · ${action}`);
frappe.call({
method:config.apiMethod,
args:{payload:JSON.stringify(payload)},
callback(response){
const rawMessage=normaliseApiMessage(response);
const message=adaptApiResponse(config,dashboard,payload,rawMessage);
if(message&&message.ok){
logEvent(dashboard,"INFO","api_success",`${message.source_summary?.available||0}/${message.source_summary?.total||0} sources · ${message.metric_summary?.available||0}/${message.metric_summary?.total||0} metrics`);
resolve(message);
return;
}
const detail=message&&message.message?message.message:"Analytics response did not contain ok=true.";
logEvent(dashboard,"ERROR","api_invalid_response",detail);
reject(new Error(detail));
},
error(error){
const detail=apiErrorMessage(error);
logEvent(dashboard,"ERROR","api_error",detail);
reject(new Error(detail));
}
});
});
}
function setLoading(dashboard,active,progress=0,task="Loading live analytics"){const overlay=dashboard.querySelector("[data-demo-loading-overlay]");if(overlay)overlay.classList.toggle("hidden",!active);const title=dashboard.querySelector("[data-demo-loading-title]")||dashboard.querySelector("[data-demo-loading-overlay] strong");if(title)title.textContent=task;const fill=dashboard.querySelector("[data-demo-progress-fill]");if(fill)fill.style.width=Math.max(0,Math.min(100,progress))+"%";const value=dashboard.querySelector("[data-demo-progress-value]");if(value)value.textContent=Math.round(progress)+"%";const note=dashboard.querySelector("[data-demo-loading-overlay] .progress-text span:last-child");if(note)note.textContent="Permission-aware sources";}
function metricValue(metric){if(!metric||metric.status!=="available")return"—";const value=metric.value==null?0:metric.value;if(metric.unit==="SGD")return"SGD "+Number(value).toLocaleString();if(metric.unit==="rating")return String(value)+"/5";if(metric.unit==="percent")return String(value)+"%";return Number(value).toLocaleString();}
const DOCTYPE_DISPLAY_NAMES=Object.freeze({"Supplier Rating":"Provider Rating","Student Admission UCC":"Shortlisted Applicants","Student Group":"Module Class Details","Module Class Details":"Module Class Details","Student Batch Name":"Student Intake No","Student Intake No":"Student Intake No","Program":"Course","Course":"Module"});
function displayDoctypeName(doctype){return DOCTYPE_DISPLAY_NAMES[doctype]||doctype||"Source";}
function doctypeListRoute(doctype){return"/app/"+String(doctype||"").trim().toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");}
function metricById(result,metricId){return(result?.metrics||[]).find(item=>item.id===metricId)||null;}
function sourceCalculation(question,metric){
if(question?.source_logic)return question.source_logic;
if(question?.source)return question.source;
if(!metric)return"Live API calculation";
const fields=(metric.resolved_fields||[]).filter(Boolean);
const source=metric.doctype||metric.source||"Live source";
return fields.length?`${source}.${fields.join(" / ")}`:`${source} · ${metric.unit||"records"} calculation`;
}
function extendedQuestionRows(result,tab){
const base=(result?.questions||[]).map(row=>({...row}));
const used=new Set(base.map(row=>row.metric_id).filter(Boolean));
(result?.metrics||[]).forEach(metric=>{
if(!metric?.id||used.has(metric.id))return;
const available=metric.status==="available";
const count=Number(metric.record_count??metric.total??0);
base.push({
id:"extended-"+metric.id,
criterion:result?.meta?.subcriterion||result?.policy?.criterion||tab,
question:`What is the current ${String(metric.label||"metric").toLowerCase()}?`,
answer:available?`${metricValue(metric)} from ${count.toLocaleString()} matching record(s).`:`Unavailable: ${metric.message||String(metric.status||"required source or field is unavailable").replaceAll("_"," ")}`,
metric_id:metric.id,
status:metric.status||"unavailable",
confidence:available?"Live":"Unavailable",
doctype:metric.doctype||"",
source_logic:sourceCalculation(null,metric),
record_count:count
});
});
return base;
}
// ---------------------------------------------------------------------------
// PER-TAB CHARTS -- loading, rendering, sizing, picking, removing
//
// Every chart here is a real Frappe Insights Query v3, executed server-side
// with check_permission("read") -- the mechanism proved on the bench for the
// admission charts. The public-dashboard mechanism is never used; it applies
// no permissions at all.
//
// Three gates, none of them in this file: the criterion tab must be visible to
// the user (ucc_dashboard_access), the picker lists only what frappe.get_list
// lets them read, and every execute re-checks read permission at that moment.
// A stored chart id is a preference, never a grant.
// ---------------------------------------------------------------------------
function tabChartNotice(message){
return'<div class="ucc-tab-charts-notice">'+esc(message)+"</div>";
}

// ONE execute per chart feeds BOTH views, so the number in the table is by
// construction the number in the bar. See tab_charts.chart_data().
function embeddedChartMarkup(chart,editing){
const span=Math.max(1,Math.min(Number(chart.span)||6,12));
return`<article class="ucc-embedded-chart${editing?" is-editable":""}" data-embedded-chart="${esc(chart.chart)}" `
+`data-demo-card="${esc(chart.chart)}" data-span="${span}"${editing?' draggable="true"':""} `
+`style="grid-column:span ${span}">`
+`<div class="ucc-embedded-chart-head"><h3>${esc(chart.title)}</h3>`
+`<div class="ucc-embedded-chart-tools">`
+`<div class="ucc-embedded-views" role="group" aria-label="View">`
+`<button type="button" data-demo-view="diagram" class="is-active" aria-pressed="true">Diagram</button>`
+`<button type="button" data-demo-view="table" aria-pressed="false">Table</button></div>`
+(editing
?`<button type="button" class="ucc-tab-action ucc-retitle" data-retitle-chart="${esc(chart.chart)}" `
+`title="Give this card its own title">Rename</button>`
+`<span class="ucc-palette-control"><input type="color" data-recolour-chart="${esc(chart.chart)}" `
+`value="${esc((chart.palette&&chart.palette[0])||"#2563EB")}" `
+`title="Series colour for this chart" aria-label="Series colour for ${esc(chart.title)}"></span>`
+`<span class="ucc-drag-grip" data-drag-grip title="Drag to reorder" aria-hidden="true">&#8942;&#8942;</span>`
+`<button type="button" class="ucc-remove-chart" data-remove-chart="${esc(chart.chart)}" `
+`title="Remove this chart from the tab" aria-label="Remove ${esc(chart.title)} from this tab">&times;</button>`
:"")
+`</div></div>`
+`<div class="ucc-embedded-chart-body" data-demo-chart="${esc(chart.chart)}" data-embedded-chart-body>`
+tabChartNotice("Loading…")+"</div>"
+`<div class="ucc-embedded-chart-table hidden" data-embedded-chart-table></div>`
// #3: the width is dragged, not chosen from a list. The handle carries the
// keyboard equivalent too -- a drag that only works with a mouse is not an
// accessible control (CLAUDE.md §10.5).
+(editing
?`<button type="button" class="ucc-resize-handle" data-resize-chart="${esc(chart.chart)}" `
+`aria-label="Width of ${esc(chart.title)}: ${span} of 12 columns. Use the arrow keys to change." `
+`role="slider" aria-valuemin="1" aria-valuemax="12" aria-valuenow="${span}"></button>`
:"")
+`</article>`;
}

// PHASE 1 PILOT. One Insights dashboard, embedded, instead of the painted
// cards. Nothing about the painted path changes: a tab without
// embedded_dashboard set behaves exactly as before, and clearing the field
// puts this tab back too.
//
// The URL is built here rather than sent by the server, so nothing but an id
// crosses the wire. `/insights/dashboards/<id>` is the AUTHENTICATED route --
// the frame carries the viewer's own session and Insights runs its own
// permission query. The `/insights/shared/...` route is never used: it is
// is_public-only and would need a permission bypass to work at all.
function embeddedDashboardMarkup(state){
const id=state.embeddedDashboard;
if(!state.embeddedDashboardReadable){
return tabChartNotice("This tab is set to show the Insights dashboard "
+esc(id)+", which your account cannot open. Ask whoever owns it in Insights "
+"to share it with you.");
}
return'<div class="ucc-embed-dashboard">'
+'<iframe class="ucc-embed-frame" title="Insights dashboard '+esc(id)+'" '
+'loading="lazy" data-embed-name="'+esc(id)+'" '
+'data-embed-src="/insights/dashboards/'+encodeURIComponent(id)+'"></iframe>'
+'<p class="ucc-embed-note"><span data-embed-timing>Loading…</span> · '
+'Drawn by Frappe Insights, with your own permissions. '
+'<a href="/insights/dashboards/'+encodeURIComponent(id)+'" target="_blank" '
+'rel="noopener">Open in Insights</a></p></div>';
}

function renderTabCharts(dashboard,config,tab){
const area=ensureTabChartArea(dashboard,config,tab);
if(!area)return;
const grid=area.querySelector("[data-tab-charts-grid]");
const state=tabConfig(dashboard,tab);
if(!state){grid.innerHTML=tabChartNotice("Loading your charts…");loadTabCharts(dashboard,config,tab);return;}
if(state.loading){grid.innerHTML=tabChartNotice("Loading your charts…");return;}
if(state.error){grid.innerHTML=tabChartNotice(state.error);return;}
if(state.embeddedDashboard){
grid.innerHTML=embeddedDashboardMarkup(state);
loadVisibleEmbeds(dashboard);
return;
}
if(!state.charts.length){
grid.innerHTML=tabChartNotice(isEditing(dashboard,tab)
?"No charts on this tab yet. Use “+ Add chart” to embed one from Frappe Insights."
:"No charts have been added to this tab yet.");
return;
}
const editing=isEditing(dashboard,tab);
grid.innerHTML=state.charts.map(function(chart){return embeddedChartMarkup(chart,editing);}).join("");
state.charts.forEach(function(chart){paintEmbeddedChart(grid,chart,dashboard,tab);});
initChartDragging(dashboard,config,tab,grid);
initChartResizing(dashboard,config,tab,grid);
initChartRecolouring(dashboard,config,tab,grid);
}

function applyTabConfig(dashboard,config,tab,response){
tabChartState[tabChartKey(dashboard.dataset.demoDashboard,tab)]={
charts:(response&&response.charts)||[],
intro:(response&&response.intro)||"",
hiddenQuestions:((response&&response.questions)||{}).hidden||[],
sizes:(response&&response.sizes)||["small","medium","large","full"],
// The server decides. This only hides controls that would fail anyway --
// every write endpoint checks again, so a hidden button is a courtesy and
// never the gate (CLAUDE.md §3.3: hiding is interface composition).
canEdit:!!(response&&response.can_edit),
embeddedDashboard:(response&&response.embedded_dashboard)||"",
embeddedDashboardReadable:!!(response&&response.embedded_dashboard_readable),
loading:false,error:null};
renderTabCharts(dashboard,config,tab);
renderTabActions(dashboard,tab);
renderTabIntro(dashboard,config,tab);
renderQa(dashboard,dashboardState(dashboard).result,tab);
syncExploreCatalogue();
}

function loadTabCharts(dashboard,config,tab){
const key=tabChartKey(dashboard.dataset.demoDashboard,tab);
if(tabChartState[key])return;
if(!(window.frappe&&frappe.call)){
tabChartState[key]={charts:[],intro:"",hiddenQuestions:[],loading:false,error:"Frappe API client unavailable."};return;}
tabChartState[key]={charts:[],intro:"",hiddenQuestions:[],loading:true,error:null};
frappe.call({
method:"ucc_intelligence.api.get_tab_charts",
args:{criterion:dashboard.dataset.demoDashboard,tab:tab},
callback(response){applyTabConfig(dashboard,config,tab,(response&&response.message)||{});},
error(error){
tabChartState[key]={charts:[],intro:"",hiddenQuestions:[],loading:false,error:apiErrorMessage(error)};
renderTabCharts(dashboard,config,tab);
},
});
}

// One embedded chart. A failure is SHOWN as a failure -- there is no second
// data source to quietly fall back to.
// dashboard/tab are threaded in so the server can resolve THIS tab's colour
// override -- the same chart on two criteria may legitimately differ.
function paintEmbeddedChart(grid,chart,dashboard,tab){
const card=grid.querySelector(`[data-embedded-chart="${CSS.escape(chart.chart)}"]`);
const body=card&&card.querySelector("[data-embedded-chart-body]");
if(!body)return;
if(!(window.frappe&&frappe.call)){body.innerHTML=tabChartNotice("Frappe API client unavailable.");return;}
frappe.call({
method:"ucc_intelligence.api.get_tab_chart_data",
args:{chart:chart.chart,criterion:dashboard.dataset.demoDashboard,tab:tab},
callback(response){
const data=(response&&response.message)||{};
card._chartData=data;
if(data.status==="available"&&(data.series||[]).length){
paintChartSeries(body,data.series,card);
renderChartTable(card,null);
loadDrilldown(card,chart.chart);
return;
}
// Worth saying out loud: the chart exists and this user may not read it.
// That is not the same as the query returning nothing.
if(data.status==="permission_denied"){
body.innerHTML=window.UCCShared.permissionNoticeHtml({
view:chart.title||"This chart",source:"Frappe Insights",detail:data.message,compact:true});
return;
}
body.innerHTML=tabChartNotice(data.message||"This Insights query returned no rows.");
},
error(error){body.innerHTML=tabChartNotice(apiErrorMessage(error));},
});
}

// ONE renderer, a horizontal bar list, for every embedded chart. Deliberately
// one shape: an Insights query returns label/value rows, and inventing a radar
// or a funnel from two columns is decoration, not information.
//
// Each bar carries its own label so the Table view can be filtered to it --
// see selectChartSegment().
// --- how a chart LOOKS ------------------------------------------------------
// Sophia embeds Insights QUERIES, which carry data and no presentation. Chart
// type, axis assignment, labels and legend live on a separate Insights Chart
// v3 record; the server reads it (analytics/chart_presentation.py) and hands
// down a `presentation` block with everything already resolved and validated
// against the columns the query really returned.
//
// COLOUR IS SOPHIA'S. The live probe dumped all seven Chart records in full
// and there is no colour field on any of them -- Insights applies a palette at
// render time from somewhere it does not save. So the palette comes from
// UCC Intelligence Settings, overridable per chart, and is documented as
// CHOSEN TO RESEMBLE Insights rather than read from it. See ADR-015.
//
// NO HAND-ROLLED SVG. `chartForLive` and `registerChartPlugin` were deleted
// earlier in this migration and test_end_to_end.py asserts they stay gone.
// Every shape below is CSS on real DOM nodes -- which is also what keeps
// drill-down working, because a bar stays a <button> we own and can attach a
// click to. An iframe of Insights' own renderer would have taken that away.
function paletteOf(card){
const palette=((card&&card._chartData&&card._chartData.presentation)||{}).palette;
return (palette&&palette.length)?palette:["#2563EB"];
}

function seriesColour(card,index){
const palette=paletteOf(card);
return palette[index%palette.length];
}

function segmentButton(card,row,index,inner,extraClass){
return'<button type="button" class="'+extraClass+'" data-chart-segment="'+esc(row.label)+'" '
+'title="Show the rows behind '+esc(row.label)+'">'+inner+"</button>";
}

function paintBarSeries(card,node,series){
const max=Math.max.apply(null,series.map(row=>Number(row.value)||0).concat([1]));
node.innerHTML='<div class="ucc-insights-series">'+series.map((row,index)=>{
const value=Number(row.value)||0;
const width=Math.max(1,Math.round((value/max)*100));
return segmentButton(card,row,index,
'<span class="ucc-insights-bar-label">'+esc(row.label)+"</span>"
+'<span class="ucc-insights-bar-track"><span class="ucc-insights-bar-fill" style="width:'+width+"%;background:"+esc(seriesColour(card,index))+'"></span></span>'
+'<span class="ucc-insights-bar-value">'+esc(value.toLocaleString())+"</span>",
"ucc-insights-bar");
}).join("")+"</div>";
}

// A line is the same bars laid out along the x axis -- one column per point,
// each a button, with the fill height carrying the value. Not a polyline,
// because a polyline is not clickable per point and drill-down is the
// requirement that outranks the flourish.
function paintLineSeries(card,node,series){
const max=Math.max.apply(null,series.map(row=>Number(row.value)||0).concat([1]));
const colour=seriesColour(card,0);
node.innerHTML='<div class="ucc-insights-plot">'+series.map((row,index)=>{
const value=Number(row.value)||0;
const height=Math.max(2,Math.round((value/max)*100));
return segmentButton(card,row,index,
'<span class="ucc-insights-plot-value">'+esc(value.toLocaleString())+"</span>"
// The fill's height is a percentage, so it needs a parent with a definite
// height to resolve against. The track is that parent -- without it every
// column collapses to a hairline, which is exactly what it did first time.
+'<span class="ucc-insights-plot-track">'
+'<span class="ucc-insights-plot-fill" style="height:'+height+"%;background:"+esc(colour)+'"></span></span>'
+'<span class="ucc-insights-plot-label">'+esc(row.label)+"</span>",
"ucc-insights-point");
}).join("")+"</div>";
}

// One conic-gradient, and a legend of buttons beside it. The gradient is the
// browser drawing a pie; the clickable part is the legend, so every segment is
// still reachable by keyboard as well as mouse.
const DONUT_LABEL_MIN_SHARE=8;

function paintDonutSeries(card,node,series){
const total=series.reduce((sum,row)=>sum+(Number(row.value)||0),0)||1;
// legend_position is READ from the Insights Chart record and now DRAWN. The
// donut is the only shape here that has a legend, so it is the only one it can
// mean anything for. "none" hides it entirely, which is a real setting a
// person can choose in Insights and expect to see honoured.
const legend=((card&&card._chartData&&card._chartData.presentation)||{}).legend_position||"right";
let cursor=0;
// The share each slice occupies, kept alongside the gradient stop so the
// on-ring label sits at the middle of its OWN slice rather than at an angle
// worked out a second time from the same numbers.
const slices=series.map((row,index)=>{
const share=((Number(row.value)||0)/total)*100;
const start=cursor;cursor+=share;
return {index:index,start:start,end:cursor,share:share,
colour:seriesColour(card,index)};
});
const stops=slices.map(slice=>
esc(slice.colour)+" "+slice.start.toFixed(2)+"% "+slice.end.toFixed(2)+"%").join(",");
// #2: the percentage ON the ring, not only in the list beside it. A conic
// gradient cannot carry text, so each label is a positioned span rotated onto
// the middle of its slice and rotated back upright -- CSS transforms on real
// DOM nodes, no SVG.
//
// Only slices with room for it. Below about a twelfth of the ring the labels
// collide with their neighbours and the chart becomes less readable, not more,
// and every value is in the legend and the table regardless.
//
// NOT gated on show_inline_labels. That key exists on DonutChartConfig, but
// what it does is still unproven, and gating on an unproven key means an
// unproven key can hide data. Felix asked for "visible if unset" and for a
// Donut it is always unset in the sense that matters: show_data_labels is an
// AXIS-chart key and a Donut has no axes. One line to gate it later.
const marks=slices.filter(slice=>slice.share>=DONUT_LABEL_MIN_SHARE).map(function(slice){
const angle=(slice.start+slice.end)/2*3.6;
return'<span class="ucc-insights-donut-mark" style="transform:translate(-50%,-50%) '
+"rotate("+angle.toFixed(2)+"deg) translateY(-50px) rotate("+(-angle).toFixed(2)+'deg)">'
+Math.round(slice.share)+"%</span>";
}).join("");
node.innerHTML='<div class="ucc-insights-donut-wrap" data-legend="'+esc(legend)+'">'
+'<div class="ucc-insights-donut-plot">'
+'<div class="ucc-insights-donut" style="background:conic-gradient('+stops+')" aria-hidden="true"></div>'
// aria-hidden: the legend buttons already carry every label and value as real
// text, so announcing the ring's percentages again is duplication for a screen
// reader, not extra information.
+(marks?'<div class="ucc-insights-donut-marks" aria-hidden="true">'+marks+"</div>":"")
+"</div>"
+(legend==="none"?"":'<div class="ucc-insights-donut-legend">'+series.map((row,index)=>{
const value=Number(row.value)||0;
return segmentButton(card,row,index,
'<span class="ucc-insights-swatch" style="background:'+esc(seriesColour(card,index))+'"></span>'
+'<span class="ucc-insights-legend-label">'+esc(row.label)+"</span>"
+'<span class="ucc-insights-legend-value">'+esc(value.toLocaleString())+" ("
+Math.round((value/total)*100)+"%)</span>","ucc-insights-legend-item");
}).join("")+"</div>")+"</div>";
}

// A funnel: ordered stages, each drawn as a proportion of the largest, with
// the drop from the stage above stated rather than left to be eyeballed. This
// is the only one of the four undrawn types that a label/value series can
// express honestly -- Map needs geography, Bubble needs three numbers per
// point, Sankey needs flow pairs. See chart_presentation.SUPPORTED_TYPES.
function paintFunnelSeries(card,node,series){
const max=Math.max.apply(null,series.map(row=>Number(row.value)||0).concat([1]));
node.innerHTML='<div class="ucc-insights-funnel">'+series.map((row,index)=>{
const value=Number(row.value)||0;
const width=Math.max(6,Math.round((value/max)*100));
const previous=index?(Number(series[index-1].value)||0):0;
const drop=(index&&previous)?Math.round(((previous-value)/previous)*100):0;
return segmentButton(card,row,index,
'<span class="ucc-insights-funnel-label">'+esc(row.label)+"</span>"
+'<span class="ucc-insights-funnel-bar" style="width:'+width+"%;background:"
+esc(seriesColour(card,index))+'"><span>'+esc(value.toLocaleString())+"</span></span>"
+(index&&drop>0?'<span class="ucc-insights-funnel-drop">&#8722;'+drop+"%</span>":""),
"ucc-insights-funnel-stage");
}).join("")+"</div>";
}

// A single figure. Insights' "Number" type is one measure with no dimension,
// so there is nothing to drill into and no segment button is offered.
function paintNumberSeries(card,node,series){
const value=series.length?(Number(series[0].value)||0):0;
node.innerHTML='<div class="ucc-insights-number"><strong>'+esc(value.toLocaleString())+"</strong>"
+'<span>'+esc(series.length?series[0].label:"")+"</span></div>";
}

const CHART_PAINTERS={bar:paintBarSeries,line:paintLineSeries,donut:paintDonutSeries,
number:paintNumberSeries,funnel:paintFunnelSeries};

// A donut's slices have no natural order, so the query's row order is an
// accident of the GROUP BY rather than a decision anyone made -- largest first
// is what makes a ring readable. Everything else keeps the order it arrived in:
// a line sorted by value stops being a time series, and a bar chart's order is
// something its author chose in Insights.
//
// This runs AFTER the `limit` slice, deliberately. Sorting first would change
// WHICH rows a "top 10" chart shows -- from the ten Insights picked to the ten
// with the largest values -- and that is a change to the data on an evidence
// card, not a change to its appearance. Same rows, better order.
const SORTED_BY_VALUE=["donut"];

function sortForDisplay(renderAs,series){
if(SORTED_BY_VALUE.indexOf(renderAs)<0)return series;
// Copied, not sorted in place: `series` is the card's own data, and the table
// view beside it shows the query's real order.
return series.slice().sort(function(a,b){
return (Number(b.value)||0)-(Number(a.value)||0);
});
}

function paintChartSeries(node,series,card){
const presentation=((card&&card._chartData)||{}).presentation||{};
// Unsupported or unresolvable -> the table, LABELLED. chart_type is a free
// text field in Insights, so an unknown value is expected, not exceptional.
if(presentation.status==="table_only"){
paintTableOnly(card,node,presentation);
return;
}
// The chart's own `limit` -- "top 10" means ten, and drawing forty bars on a
// card configured for ten shows something its author did not ask for. Said out
// loud on the card, because a truncated chart that looks complete is worse
// than one that admits it.
const limit=Number(presentation.limit)||0;
const shown=(limit&&series.length>limit)?series.slice(0,limit):series;
const painter=CHART_PAINTERS[presentation.render_as]||paintBarSeries;
painter(card,node,sortForDisplay(presentation.render_as,shown));
// #4: a drawable chart OPENS as the diagram. Table stays one click away and
// stays the automatic state only when nothing can be drawn -- which is what
// paintTableOnly() does. Set explicitly rather than relying on the markup's
// initial classes, so a re-render cannot leave a chart card showing a table.
setChartView(card,"diagram");
if(limit&&series.length>limit){
node.insertAdjacentHTML("beforeend",
'<p class="ucc-insights-axis-label">Top '+limit+" of "+series.length
+" — this chart is limited in Insights. The table shows all rows.</p>");
}
if(presentation.axis_label){
node.insertAdjacentHTML("beforeend",
'<p class="ucc-insights-axis-label">'+esc(presentation.axis_label)+"</p>");
}
}

// Never a blank card and never a broken one: the rows are real, and the notice
// says exactly why this is a table rather than the chart Insights would show.
function paintTableOnly(card,node,presentation){
node.innerHTML='<div class="ucc-insights-table-only">'
+'<p class="ucc-insights-table-note">'+esc(presentation.reason||"Shown as a table.")
+(presentation.chart_type?" ":"")+"</p></div>";
setChartView(card,"table");
}

// --- Table view and drill-down ---------------------------------------------
// The table is the query's OWN result rows, from the same single execute() the
// diagram used. Nothing is recomputed here.
//
// An Insights Query v3's execute() returns the SUMMARISED rows -- one row per
// dimension value, with its measure. Clicking "Consultative" filters this
// table to the Consultative row. Opening the 40 records BEHIND that row is a
// second, permission-applying fetch: see analytics/drilldown.py, which was
// written from the live probe output rather than from memory.
//
// The button only appears on charts the server says are drillable, so a chart
// whose records cannot be resolved never offers a click that will fail.
function renderChartTable(card,segment){
const table=card.querySelector("[data-embedded-chart-table]");
const data=card._chartData;
if(!table)return;
if(!data||data.status!=="available"||!(data.rows||[]).length){
table.innerHTML=tabChartNotice((data&&data.message)||"No rows to show.");
return;
}
const columns=data.columns||[];
const rows=segment
?data.rows.filter(function(row){
return columns.some(function(column){return String(row[column])===String(segment);});
})
:data.rows;
const drill=card._drilldown;
table.innerHTML=(segment
?'<div class="ucc-embedded-chart-filter">Showing rows for <strong>'+esc(segment)+"</strong>"
+(drill&&drill.status==="available"
?'<button type="button" class="ucc-open-records" data-drill-records="'+esc(segment)+'">'
+"Open the "+esc(drill.doctype)+" records</button>"
:"")
+'<button type="button" data-clear-segment>Clear</button></div>'
:"")
+'<div class="table-wrap"><table><thead><tr>'
+columns.map(function(column){return"<th>"+esc(humaniseColumn(column))+"</th>";}).join("")
+"</tr></thead><tbody>"
+(rows.length?rows.map(function(row){
return"<tr>"+columns.map(function(column){
const value=row[column];
return"<td>"+esc(value==null||value===""?"—":value)+"</td>";
}).join("")+"</tr>";
}).join(""):'<tr><td colspan="'+columns.length+'">No rows matched.</td></tr>')
+"</tbody></table></div>";
}

function humaniseColumn(key){
return String(key).replace(/_/g," ").replace(/\b\w/g,function(c){return c.toUpperCase();});
}

// Clicking a bar switches the card to Table view already filtered to it, which
// is what "drill down" means to the person clicking.
function selectChartSegment(card,segment){
setChartView(card,"table");
renderChartTable(card,segment);
}

// Asked once per chart, when it renders. The answer decides whether the
// "Open the records" button is offered at all -- a chart the server cannot
// resolve to a DocType never shows a click that would then explain itself.
function loadDrilldown(card,chart){
if(!(window.frappe&&frappe.call))return;
frappe.call({
method:"ucc_intelligence.api.get_chart_drilldown",
args:{chart:chart},
callback(response){card._drilldown=(response&&response.message)||null;},
error(){card._drilldown=null;},
});
}

function recordRoute(doctype,name){
return doctypeListRoute(doctype)+"/"+encodeURIComponent(name);
}

// The records behind one segment. Paged, because a segment counting 4,000
// records is not something to put in a modal in one go, and permission-applied
// on the server -- this renders whatever came back and never filters it here.
let activeDrill=null;

function openDrilldown(card,segment,page){
const drill=card._drilldown;
if(!drill||drill.status!=="available")return;
activeDrill={card:card,segment:segment};
const column=(drill.columns||[])[0];
const title=drill.doctype+" · "+(segment||"(blank)");
openModal(title,tabChartNotice("Loading…"));
if(!(window.frappe&&frappe.call))return;
frappe.call({
method:"ucc_intelligence.api.get_chart_records",
args:{chart:drill.chart,column:column,value:segment,page:page||1,page_size:20},
callback(response){
const data=(response&&response.message)||{};
if(data.status==="permission_denied"){
openModal(title,window.UCCShared.permissionNoticeHtml({
view:drill.doctype+" records",source:"ERPNext",detail:data.message,compact:true}));
return;
}
if(data.status!=="available"){
openModal(title,tabChartNotice(data.message||"These records cannot be opened."));
return;
}
const rows=data.records||[];
if(!rows.length){
openModal(title,tabChartNotice(data.page>1
?"No further records."
:"No records here that you have permission to see."));
return;
}
const fields=data.fields||["name"];
card._drilldownPage=data.page;
openModal(title,
'<p class="ucc-chart-picker-note">Live '+esc(drill.doctype)+" records, filtered to "
+"<strong>"+esc(segment||"(blank)")+"</strong>. Only records you have permission to "
+"see are listed, so this may be fewer than the chart's count.</p>"
+'<div class="table-wrap"><table class="ucc-history-table"><thead><tr>'
+fields.map(function(field){return"<th>"+esc(humaniseColumn(field))+"</th>";}).join("")
+"</tr></thead><tbody>"
+rows.map(function(row){
return"<tr>"+fields.map(function(field){
const value=row[field];
if(field==="name"){
return'<td><a href="'+esc(recordRoute(drill.doctype,row.name))+'">'+esc(row.name)+"</a></td>";
}
return"<td>"+esc(value==null||value===""?"—":value)+"</td>";
}).join("")+"</tr>";
}).join("")+"</tbody></table></div>"
+'<div class="ucc-drilldown-paging">'
+(data.page>1?'<button type="button" data-drill-page="'+(data.page-1)+'">&#8249; Previous</button>':"")
+"<span>Page "+data.page+"</span>"
+(data.has_more?'<button type="button" data-drill-page="'+(data.page+1)+'">Next &#8250;</button>':"")
+"</div>");
},
error(error){openModal(title,tabChartNotice(apiErrorMessage(error)));},
});
}

function setChartView(card,view){
const body=card.querySelector("[data-embedded-chart-body]");
const table=card.querySelector("[data-embedded-chart-table]");
if(body)body.classList.toggle("hidden",view==="table");
if(table)table.classList.toggle("hidden",view!=="table");
card.querySelectorAll("[data-demo-view]").forEach(function(button){
const active=button.dataset.demoView===view;
button.classList.toggle("is-active",active);
button.setAttribute("aria-pressed",active?"true":"false");
});
}

// --- the tab intro (#4) -----------------------------------------------------
// Replaces the hard-coded "OVERVIEW / Permission-aware live evidence, visual
// analysis and management questions" every tab used to carry. Empty by
// default: a tab with nothing to say says nothing.
// #4: the intro renders Markdown. It did not before -- headings and numbered
// lists came out as literal "# Heading" and "1. item" text, which is what
// "typed markdown and it came out unformatted" meant. Bold, italic, code,
// links and - bullets already worked; the rest is added here.
//
// THE ESCAPING IS NOT WEAKENED TO DO IT, and the two requirements do not
// conflict. Every rule below runs on text that esc() has ALREADY escaped, so
// "<script>" is "&lt;script&gt;" before any pattern sees it and can never
// become a tag. The markdown patterns only ever match characters escaping
// leaves alone (#, *, `, -, digits, brackets). The XSS assertion in
// tools/test_tab_surface_render.js is untouched and still passes.
function renderIntroMarkdown(text){
let html=esc(text);
// Inline first, so a heading or list item can contain them.
html=html.replace(/\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)/g,
'<a href="$2" target="_blank" rel="noopener">$1</a>');
html=html.replace(/\*\*([^*\n]+)\*\*/g,"<strong>$1</strong>");
html=html.replace(/(^|[^*])\*([^*\n]+)\*/g,"$1<em>$2</em>");
html=html.replace(/`([^`\n]+)`/g,"<code>$1</code>");

const out=[];
let list=null;      // the <li> items collected so far
let listTag="";     // "ul" or "ol" -- switching between them closes the first
function closeList(){
if(list){out.push("<"+listTag+">"+list.join("")+"</"+listTag+">");list=null;listTag="";}
}
function openItem(tag,content){
if(listTag&&listTag!==tag)closeList();
if(!list){list=[];listTag=tag;}
list.push("<li>"+content+"</li>");
}

html.split("\n").forEach(function(line){
const heading=/^\s*(#{1,6})\s+(.*)$/.exec(line);
if(heading){
closeList();
// Capped at h6 by the pattern; rendered as h3-h6 so a tab intro can never
// out-shout the page's own headings.
const level=Math.min(6,heading[1].length+2);
out.push("<h"+level+">"+heading[2]+"</h"+level+">");
return;
}
const bullet=/^\s*[-*]\s+(.*)$/.exec(line);
if(bullet){openItem("ul",bullet[1]);return;}
const numbered=/^\s*\d+[.)]\s+(.*)$/.exec(line);
if(numbered){openItem("ol",numbered[1]);return;}
const quote=/^\s*&gt;\s?(.*)$/.exec(line);   // ">" is already escaped by now
if(quote){closeList();out.push("<blockquote>"+quote[1]+"</blockquote>");return;}
if(/^\s*(-{3,}|\*{3,})\s*$/.test(line)){closeList();out.push("<hr>");return;}
closeList();
if(line.trim())out.push("<p>"+line+"</p>");
});
closeList();
return out.join("");
}

function renderTabIntro(dashboard,config,tab){
const panelKey=(config.panelMap&&config.panelMap[tab])||tab;
const mount=dashboard.querySelector(`[data-tab-intro="${CSS.escape(panelKey)}"]`);
if(!mount)return;
const state=tabConfig(dashboard,tab);
const text=(state&&state.intro)||"";
if(mount.dataset.editing==="1")return;
const canEdit=isEditing(dashboard,tab);
if(!text&&!canEdit){mount.innerHTML="";return;}
mount.innerHTML=(text
?'<div class="ucc-tab-intro-text">'+renderIntroMarkdown(text)+"</div>"
:'<p class="ucc-tab-intro-empty">No introduction for this tab yet.</p>')
+(canEdit
?'<button type="button" class="ucc-tab-intro-edit" data-edit-intro="'+esc(tab)+'">'
+(text?"Edit intro":"Add an introduction")+"</button>"
:"");
}

function openIntroEditor(dashboard,config,tab){
const panelKey=(config.panelMap&&config.panelMap[tab])||tab;
const mount=dashboard.querySelector(`[data-tab-intro="${CSS.escape(panelKey)}"]`);
if(!mount)return;
const state=tabConfig(dashboard,tab);
mount.dataset.editing="1";
mount.innerHTML='<label class="ucc-tab-intro-editor"><span class="ucc-visually-hidden">Tab introduction</span>'
+'<textarea data-intro-text rows="4" placeholder="Introduce this tab. **bold**, *italic*, `code`, [links](https://…) and - bullets work.">'
+esc((state&&state.intro)||"")+"</textarea></label>"
+'<div class="ucc-tab-intro-actions">'
+'<button type="button" class="ucc-intro-save" data-save-intro="'+esc(tab)+'">Save</button>'
+'<button type="button" class="ucc-intro-cancel" data-cancel-intro="'+esc(tab)+'">Cancel</button></div>';
const box=mount.querySelector("[data-intro-text]");
if(box)box.focus();
}

function saveTabIntro(dashboard,config,tab){
const panelKey=(config.panelMap&&config.panelMap[tab])||tab;
const mount=dashboard.querySelector(`[data-tab-intro="${CSS.escape(panelKey)}"]`);
const box=mount&&mount.querySelector("[data-intro-text]");
if(!box||!(window.frappe&&frappe.call))return;
frappe.call({
method:"ucc_intelligence.api.set_tab_intro",
args:{criterion:dashboard.dataset.demoDashboard,tab:tab,intro:box.value},
callback(response){
mount.dataset.editing="";
applyTabConfig(dashboard,config,tab,(response&&response.message)||{});
},
error(error){logEvent(dashboard,"ERROR","tab_intro_save_failed",apiErrorMessage(error));},
});
}

// --- #2: drag to reorder ---------------------------------------------------
// HTML5 drag and drop, not a library: the cards are already grid items, the
// browser supplies the drag image and the drop target, and the stored list IS
// the order so there is nothing to reconcile afterwards.
function chartOrderFrom(grid){
return Array.from(grid.querySelectorAll("[data-embedded-chart]"))
.map(function(card){return card.dataset.embeddedChart;});
}

function initChartDragging(dashboard,config,tab,grid){
if(grid.dataset.dragReady==="1")return;
grid.dataset.dragReady="1";
let dragged=null;

grid.addEventListener("dragstart",function(event){
const card=event.target.closest("[data-embedded-chart]");
if(!card||!card.draggable)return;
dragged=card;
card.classList.add("is-dragging");
event.dataTransfer.effectAllowed="move";
// Firefox refuses to start a drag unless data is set.
event.dataTransfer.setData("text/plain",card.dataset.embeddedChart);
});

grid.addEventListener("dragover",function(event){
if(!dragged)return;
event.preventDefault();
const over=event.target.closest("[data-embedded-chart]");
if(!over||over===dragged)return;
// Before or after, depending on which half was entered, so a card can be
// dropped at either end of a row rather than only ever landing left.
const box=over.getBoundingClientRect();
const after=(event.clientX-box.left)>box.width/2;
grid.insertBefore(dragged,after?over.nextSibling:over);
});

grid.addEventListener("dragend",function(){
if(!dragged)return;
dragged.classList.remove("is-dragging");
dragged=null;
const order=chartOrderFrom(grid);
const state=tabConfig(dashboard,tab);
const before=((state&&state.charts)||[]).map(function(chart){return chart.chart;});
if(order.join(" ")===before.join(" "))return;
if(!(window.frappe&&frappe.call))return;
frappe.call({
method:"ucc_intelligence.api.set_tab_chart_order",
args:{criterion:dashboard.dataset.demoDashboard,tab:tab,order:JSON.stringify(order)},
callback(response){applyTabConfig(dashboard,config,tab,(response&&response.message)||{});},
error(error){
logEvent(dashboard,"ERROR","tab_chart_order_failed",apiErrorMessage(error));
// The DOM has already moved. Re-render from what the server still holds,
// so the screen never shows an order that was not saved.
renderTabCharts(dashboard,config,tab);
},
});
});
}

// --- #3: drag to resize, snapped to the 12-column grid ----------------------
// The Small/Medium/Large/Full dropdown is gone. The handle drags in real
// pixels but only ever commits a whole number of columns, because a card at
// 37.4% width would break the grid every other card lines up against.
function columnWidth(grid){
const style=window.getComputedStyle(grid);
const gap=parseFloat(style.columnGap||style.gap||"0")||0;
return (grid.getBoundingClientRect().width-gap*11)/12+gap;
}

function applySpan(card,span){
card.dataset.span=String(span);
card.style.gridColumn="span "+span;
const handle=card.querySelector("[data-resize-chart]");
if(handle)handle.setAttribute("aria-valuenow",String(span));
}

function commitSpan(dashboard,config,tab,chart,span){
if(!(window.frappe&&frappe.call))return;
frappe.call({
method:"ucc_intelligence.api.set_tab_chart_size",
args:{criterion:dashboard.dataset.demoDashboard,tab:tab,chart:chart,span:span},
callback(response){applyTabConfig(dashboard,config,tab,(response&&response.message)||{});},
error(error){
logEvent(dashboard,"ERROR","tab_chart_size_failed",apiErrorMessage(error));
renderTabCharts(dashboard,config,tab);
},
});
}

function initChartResizing(dashboard,config,tab,grid){
if(grid.dataset.resizeReady==="1")return;
grid.dataset.resizeReady="1";
let active=null;

grid.addEventListener("pointerdown",function(event){
const handle=event.target.closest("[data-resize-chart]");
if(!handle)return;
event.preventDefault();
const card=handle.closest("[data-embedded-chart]");
active={card:card,chart:handle.dataset.resizeChart,
startX:event.clientX,startSpan:Number(card.dataset.span)||6,
unit:columnWidth(grid)};
handle.setPointerCapture(event.pointerId);
grid.classList.add("is-resizing");
});

grid.addEventListener("pointermove",function(event){
if(!active)return;
const moved=Math.round((event.clientX-active.startX)/active.unit);
const span=Math.max(1,Math.min(active.startSpan+moved,12));
if(span!==Number(active.card.dataset.span))applySpan(active.card,span);
});

function finish(){
if(!active)return;
const card=active.card;
const chart=active.chart;
const span=Number(card.dataset.span)||6;
const started=active.startSpan;
active=null;
grid.classList.remove("is-resizing");
if(span!==started)commitSpan(dashboard,config,tab,chart,span);
}
grid.addEventListener("pointerup",finish);
grid.addEventListener("pointercancel",finish);

// The handle is a slider, so the arrow keys do what the drag does. A resize
// that only works with a mouse is not a control everyone can use
// (CLAUDE.md §10.5). Committed on keyup, so holding an arrow is one save.
grid.addEventListener("keydown",function(event){
const handle=event.target.closest("[data-resize-chart]");
if(!handle)return;
const step=event.key==="ArrowRight"?1:event.key==="ArrowLeft"?-1:0;
if(!step)return;
event.preventDefault();
const card=handle.closest("[data-embedded-chart]");
applySpan(card,Math.max(1,Math.min((Number(card.dataset.span)||6)+step,12)));
handle.dataset.pendingSpan=card.dataset.span;
});
grid.addEventListener("keyup",function(event){
const handle=event.target.closest("[data-resize-chart]");
if(!handle||!handle.dataset.pendingSpan)return;
const span=Number(handle.dataset.pendingSpan);
handle.dataset.pendingSpan="";
const card=handle.closest("[data-embedded-chart]");
commitSpan(dashboard,config,tab,card.dataset.embeddedChart,span);
});
}


// #2 (colour): a per-chart override, committed on change so dragging the OS
// colour picker is one save. Colour is Sophia's -- Insights stores none. The
// override is scoped to THIS tab; the same chart elsewhere keeps its own.
function initChartRecolouring(dashboard,config,tab,grid){
if(grid.dataset.colourReady==="1")return;
grid.dataset.colourReady="1";
grid.addEventListener("change",function(event){
const input=event.target.closest("[data-recolour-chart]");
if(!input||!(window.frappe&&frappe.call))return;
frappe.call({
method:"ucc_intelligence.api.set_tab_chart_palette",
args:{criterion:dashboard.dataset.demoDashboard,tab:tab,
chart:input.dataset.recolourChart,palette:input.value},
callback(response){applyTabConfig(dashboard,config,tab,(response&&response.message)||{});},
error(error){
logEvent(dashboard,"ERROR","tab_chart_palette_failed",apiErrorMessage(error));
renderTabCharts(dashboard,config,tab);
},
});
});
}


// ===========================================================================
// OPERATIONS -- monitoring findings and document knowledge, made visible
//
// Both engines were complete and neither was reachable outside a bench
// console. Nothing here detects or retrieves anything; it lists what the
// engines produced and lets someone act on it.
//
// One workspace for both because they are two halves of one question -- what
// needs dealing with, and what this institution knows -- and two tabs for two
// half-features would cost more navigation than they are worth.
//
// Every control that CHANGES something is gated on a server-supplied
// can_manage flag, and the endpoint re-checks it. The flag decides what is
// drawn; the server decides what is allowed.
// ===========================================================================
function opsPanel(dashboardRoot,name){
return dashboardRoot.querySelector('[data-ops-panel="'+name+'"]');
}

function opsNotice(message){
return'<p class="ucc-ops-empty">'+esc(message)+"</p>";
}

function opsDate(value){
if(!value)return "—";
const parsed=new Date(String(value).replace(" ","T"));
if(isNaN(parsed.getTime()))return esc(String(value));
return esc(parsed.toLocaleString(undefined,{day:"numeric",month:"short",
year:"numeric",hour:"numeric",minute:"2-digit"}));
}

function renderMonitoring(root,data){
const panel=opsPanel(root,"monitoring");
if(!panel)return;
if(!data||data.ok===false){panel.innerHTML=opsNotice((data&&data.message)||"Monitoring is unavailable.");return;}
const severities=data.open_by_severity||{};
const rules=data.rules||[];
const runs=data.runs||[];
panel.innerHTML=
(data.enabled?"":'<div class="ucc-ops-banner">Monitoring is switched off in UCC Intelligence Settings. '
+"Existing findings are shown; no new run will happen until it is enabled.</div>")
+'<div class="ucc-ops-stats">'
+["High","Medium","Low"].map(function(level){
const count=severities[level]||0;
// The severity accent is a warning stripe, so a ZERO must not carry one --
// "0 High severity" with a red bar reads as an alert about nothing.
return'<article class="ucc-ops-stat'+(count?" is-"+level.toLowerCase():"")+'"><strong>'
+esc(String(count))+"</strong><span>"+level+" severity</span></article>";
}).join("")
+'<article class="ucc-ops-stat"><strong>'+esc(String(data.open_total||0))
+"</strong><span>open in total</span></article></div>"
+'<div class="ucc-ops-section"><div class="ucc-ops-section-head"><h3>Rules</h3>'
+(data.can_manage
?'<button type="button" class="ucc-ops-primary" data-run-monitoring>Run all rules now</button>'
:"")+"</div>"
+'<p class="ucc-ops-help"><strong>Rules are built into Sophia and cannot be added here.</strong> '
+"Ask your developer to add a new one. You can turn each rule on or off, and change "
+"its severity, in the <em>UCC Monitoring Rule</em> list in Settings. "
+'<strong>“Run”</strong> checks that one rule against your live records straight away '
+"and updates its Open count and Last run. It only reads — it never changes a record.</p>"
+(rules.length?'<div class="table-wrap"><table class="ucc-history-table"><thead><tr>'
+'<th class="ucc-col-rule">Rule</th><th>Looks at</th><th>Severity</th><th>State</th>'
+'<th>Last run</th><th class="ucc-col-open">Open</th>' 
+(data.can_manage?"<th></th>":"")+"</tr></thead><tbody>"
+rules.map(function(rule){
return"<tr><td><strong>"+esc(rule.title)+"</strong><br><small>"+esc(rule.purpose||"")+"</small></td>"
+"<td>"+esc(rule.target_doctype||"—")+"</td>"
+'<td><span class="ucc-ops-pill is-'+esc((rule.severity||"low").toLowerCase())+'">'
+esc(rule.severity||"—")+"</span></td>"
// "Not configured" is not the same as "disabled". A rule with no record has
// never been set up either way, and saying "disabled" would invent an intent.
+'<td><span class="ucc-ops-state is-'
+(rule.configured?(rule.enabled?"on":"off"):"unset")+'">'
+(rule.configured?(rule.enabled?"Enabled":"Disabled"):"Not configured yet")+"</span></td>"
+"<td>"+opsDate(rule.last_run)+"</td>"
+"<td>"+esc(String(rule.open_findings||0))+"</td>"
+(data.can_manage
?'<td><button type="button" class="ucc-tab-action" data-run-monitoring="'
+esc(rule.rule_id)+'">Run</button></td>':"")+"</tr>";
}).join("")+"</tbody></table></div>":opsNotice("No monitoring rules are registered."))
+"</div>"
+'<div class="ucc-ops-section"><div class="ucc-ops-section-head"><h3>Open findings</h3>'
+'<div class="ucc-ops-filters">'
+'<label>Status <select data-ops-status><option value="Open">Open</option>'
+'<option value="Resolved">Resolved</option><option value="Suppressed">Suppressed</option>'
+'<option value="All">All</option></select></label>'
+'<label>Severity <select data-ops-severity><option value="">Any</option>'
+["High","Medium","Low"].map(function(level){return'<option value="'+level+'">'+level+"</option>";}).join("")
+"</select></label></div></div>"
+'<div data-ops-findings>'+opsNotice("Loading…")+"</div></div>"
+'<div class="ucc-ops-section"><h3>Recent runs</h3>'
+(runs.length?'<div class="table-wrap"><table class="ucc-history-table"><thead><tr>'
+"<th>Started</th><th>Rule</th><th>Status</th><th>Records checked</th>"
+"<th>Opened</th><th>Resolved</th></tr></thead><tbody>"
+runs.map(function(run){
return"<tr><td>"+opsDate(run.started_at)+"</td>"
+"<td>"+esc(run.rule||"—")+"</td><td>"+esc(run.status||"—")
+(run.error_message?"<br><small>"+esc(run.error_message)+"</small>":"")+"</td>"
+"<td>"+esc(String(run.records_evaluated||0))+"</td>"
+"<td>"+esc(String(run.findings_opened||0))+"</td>"
+"<td>"+esc(String(run.findings_resolved||0))+"</td></tr>";
}).join("")+"</tbody></table></div>"
// "Nothing found" and "never ran" look identical if you only show a zero.
// Said apart explicitly, because Felix could not tell them apart.
:opsNotice("No monitoring run has ever been recorded. The counts above are "
+"zero because nothing has been checked yet, not because nothing is wrong. "
+(data.can_manage?"Use “Run all rules now” above to check for the first time."
:"An administrator needs to run it for the first time.")))
+"</div>";
}

function renderFindings(root,data){
const mount=opsPanel(root,"monitoring");
const target=mount&&mount.querySelector("[data-ops-findings]");
if(!target)return;
if(!data||data.ok===false){target.innerHTML=opsNotice((data&&data.message)||"Findings are unavailable.");return;}
const rows=data.findings||[];
if(!rows.length){
target.innerHTML=opsNotice("Nothing to deal with here. Findings you have permission to see would appear in this list.");
return;
}
const canManage=!!data.can_manage;
target.innerHTML='<div class="table-wrap"><table class="ucc-history-table"><thead><tr>'
+"<th>Severity</th><th>Finding</th><th>Record</th><th>Seen</th>"
+(canManage?"<th>Action</th>":"")+"</tr></thead><tbody>"
+rows.map(function(row){
const record=row.target_record
?'<a href="'+esc(doctypeListRoute(row.target_doctype)+"/"+encodeURIComponent(row.target_record))+'">'
+esc(row.target_record)+"</a>":"—";
return'<tr><td><span class="ucc-ops-pill is-'+esc((row.severity||"low").toLowerCase())+'">'
+esc(row.severity||"—")+"</span></td>"
+"<td><strong>"+esc(row.rule_title||row.rule||"")+"</strong><br><small>"+esc(row.detail||"")+"</small>"
+(row.remediation?'<br><small class="ucc-ops-fix">Fix: '+esc(row.remediation)+"</small>":"")+"</td>"
+"<td>"+record+"</td><td>"+opsDate(row.modified)
+(row.occurrence_count>1?"<br><small>"+esc(String(row.occurrence_count))+" runs</small>":"")+"</td>"
+(canManage?'<td class="ucc-ops-actions">'
+(row.status==="Open"
?'<button type="button" data-finding-action="Resolved" data-finding="'+esc(row.name)+'">Resolve</button>'
+'<button type="button" data-finding-action="Suppressed" data-finding="'+esc(row.name)+'">Suppress</button>'
:'<button type="button" data-finding-action="Open" data-finding="'+esc(row.name)+'">Reopen</button>')
+"</td>":"")+"</tr>";
}).join("")+"</tbody></table></div>";
}

function renderKnowledge(root,data){
const panel=opsPanel(root,"knowledge");
if(!panel)return;
if(!data||data.ok===false){panel.innerHTML=opsNotice((data&&data.message)||"Document knowledge is unavailable.");return;}
const sources=data.sources||[];
panel.innerHTML=
(data.enabled?"":'<div class="ucc-ops-banner">Document knowledge is switched off in UCC Intelligence Settings. '
+"Sources can be registered here; search stays unavailable until it is enabled.</div>")
+'<div class="ucc-ops-stats">'
+'<article class="ucc-ops-stat"><strong>'+esc(String(data.total||0))+"</strong><span>sources</span></article>"
+'<article class="ucc-ops-stat"><strong>'+esc(String(data.indexed||0))+"</strong><span>indexed</span></article>"
+'<article class="ucc-ops-stat'+(data.stale?" is-medium":"")+'"><strong>'
+esc(String(data.stale||0))+"</strong><span>stale</span></article>"
+'<article class="ucc-ops-stat"><strong>'+esc(String(data.chunks||0))+"</strong><span>sections</span></article>"
+"</div>"
+(data.can_manage
?'<p class="ucc-ops-help"><strong>This is the institution&#39;s knowledge base.</strong> '
+"A document registered here becomes part of what the whole platform can draw on - "
+"Ask UCC, the criterion dashboards, monitoring, and any report or alert built on "
+"them - not a private index for one screen. Policies, procedures, course documents "
+"and compliance requirements belong here.</p>"
+'<div class="ucc-ops-section"><h3>Register a document</h3>'
+'<div class="ucc-ops-form">'
+'<label>Title<input type="text" data-source-title placeholder="e.g. Student Support Services Procedure"></label>'
+'<label>Type<select data-source-type><option>Policy</option><option>Procedure</option>'
+"<option>Course Document</option><option>Compliance Requirement</option>"
+"<option>Meeting Decision</option><option>Other</option></select></label>"
+'<label class="ucc-ops-form-wide">Text<textarea data-source-text rows="4" '
+'placeholder="Paste the document text. It is split into sections and indexed for search with citations."></textarea></label>'
+'<button type="button" class="ucc-ops-primary" data-add-source>Register and index</button>'
+"</div>"
+'<p class="ucc-ops-hint" data-source-status></p></div>'
:"")
+'<div class="ucc-ops-section"><div class="ucc-ops-section-head"><h3>Registered sources</h3>'
+(data.can_manage&&data.stale?'<button type="button" class="ucc-tab-action" data-reindex-stale>Re-index stale</button>':"")
+"</div>"
// No documents is stated, never disguised. An index that claimed to hold
// policies it does not hold would be worse than an empty panel.
+(sources.length?'<div class="table-wrap"><table class="ucc-history-table"><thead><tr>'
+"<th>Title</th><th>Type</th><th>Version</th><th>Status</th><th>Sections</th><th>Last indexed</th>"
+(data.can_manage?"<th></th>":"")+"</tr></thead><tbody>"
+sources.map(function(row){
return"<tr><td><strong>"+esc(row.title||row.name)+"</strong>"
+(row.superseded_by?'<br><small>superseded by '+esc(row.superseded_by)+"</small>":"")+"</td>"
+"<td>"+esc(row.source_type||"—")+"</td><td>"+esc(row.version||"—")+"</td>"
+"<td>"+esc(row.sync_status||(row.last_indexed?"Indexed":"Not indexed"))+"</td>"
+"<td>"+esc(String(row.chunks||0))+"</td><td>"+opsDate(row.last_indexed)+"</td>"
+(data.can_manage?'<td><button type="button" class="ucc-tab-action" data-reindex-source="'
+esc(row.name)+'">Re-index</button></td>':"")+"</tr>";
}).join("")+"</tbody></table></div>"
:opsNotice("No documents are registered yet. The retrieval engine is built and waiting - "
+"permission-aware search with citations, ready the moment real documents arrive. Nothing is indexed until you add one above."))
+"</div>";
}

function loadOperations(root){
if(!(window.frappe&&frappe.call))return;
frappe.call({method:"ucc_intelligence.api.get_monitoring_overview",
callback(response){renderMonitoring(root,(response&&response.message)||{});loadFindings(root);},
error(error){renderMonitoring(root,{ok:false,message:apiErrorMessage(error)});}});
frappe.call({method:"ucc_intelligence.api.get_knowledge_overview",
callback(response){renderKnowledge(root,(response&&response.message)||{});},
error(error){renderKnowledge(root,{ok:false,message:apiErrorMessage(error)});}});
}

function loadFindings(root){
const panel=opsPanel(root,"monitoring");
if(!panel||!(window.frappe&&frappe.call))return;
const status=(panel.querySelector("[data-ops-status]")||{}).value||"Open";
const severity=(panel.querySelector("[data-ops-severity]")||{}).value||"";
frappe.call({method:"ucc_intelligence.api.get_monitoring_findings_list",
args:{status:status,severity:severity,limit:100},
callback(response){renderFindings(root,(response&&response.message)||{});},
error(error){renderFindings(root,{ok:false,message:apiErrorMessage(error)});}});
}

// Exposed on window for the same reason the Explore catalogue is: the shell's
// workspace switcher lives in a different IIFE from the panel it opens, and a
// named handoff is clearer than reaching across scopes.
window.UCCOperations={open:function(root){initOperations(root);loadOperations(root);}};

function initOperations(root){
const ops=root.querySelector("[data-ucc-ops]");
if(!ops||ops.dataset.ready==="1")return;
ops.dataset.ready="1";

ops.addEventListener("click",function(event){
const tab=event.target.closest("[data-ops-tab]");
if(tab){
ops.querySelectorAll("[data-ops-tab]").forEach(function(button){
const active=button===tab;
button.classList.toggle("is-active",active);
button.setAttribute("aria-selected",active?"true":"false");
});
ops.querySelectorAll("[data-ops-panel]").forEach(function(panel){
panel.hidden=panel.dataset.opsPanel!==tab.dataset.opsTab;
});
return;
}

const run=event.target.closest("[data-run-monitoring]");
if(run){
const rule=run.dataset.runMonitoring||"";
run.disabled=true;run.textContent="Running…";
frappe.call({method:"ucc_intelligence.api.run_monitoring",
args:rule?{rule:rule}:{},
callback(){loadOperations(root);},
error(error){openModal("Could not run monitoring",tabChartNotice(apiErrorMessage(error)));
loadOperations(root);}});
return;
}

const action=event.target.closest("[data-finding-action]");
if(action){
// Suppression silences a finding for good, so it asks for a reason and
// the server refuses without one. Resolve and reopen do not.
let note=null;
if(action.dataset.findingAction==="Suppressed"){
note=window.prompt("Why is this being suppressed? A suppressed finding never comes back on a later run.");
if(!note)return;
}
frappe.call({method:"ucc_intelligence.api.set_monitoring_finding_status",
args:{finding:action.dataset.finding,status:action.dataset.findingAction,note:note},
callback(){loadOperations(root);},
error(error){openModal("Could not update the finding",tabChartNotice(apiErrorMessage(error)));}});
return;
}

const addSource=event.target.closest("[data-add-source]");
if(addSource){
const title=(ops.querySelector("[data-source-title]")||{}).value||"";
const type=(ops.querySelector("[data-source-type]")||{}).value||"Policy";
const text=(ops.querySelector("[data-source-text]")||{}).value||"";
const status=ops.querySelector("[data-source-status]");
// #3: one combined message read as "something is not set up". It is form
// validation, so it says WHICH field, beside that field. There is no
// connector to configure here -- nothing external is involved.
ops.querySelectorAll("[data-field-error]").forEach(function(node){node.remove();});
let missing=false;
[["[data-source-title]","Title is required."],
["[data-source-text]","Text is required — paste the document's content here."]]
.forEach(function(pair){
const field=ops.querySelector(pair[0]);
if(!field||field.value.trim())return;
missing=true;
field.insertAdjacentHTML("afterend",
'<span class="ucc-field-error" data-field-error>'+esc(pair[1])+"</span>");
field.setAttribute("aria-invalid","true");
});
if(missing){
if(status)status.textContent="";
return;
}
ops.querySelectorAll("[aria-invalid]").forEach(function(node){node.removeAttribute("aria-invalid");});
if(status)status.textContent="Registering…";
frappe.call({method:"ucc_intelligence.api.add_knowledge_source",
args:{title:title,source_type:type,text:text},
callback(response){
const result=(response&&response.message)||{};
// Never silent. Every outcome says which one it was, including the one
// where the document registered but could not be indexed.
if(status){
status.textContent=result.ok===false
?("Could not register: "+(result.message||"unknown reason"))
:result.indexed
?("Registered and indexed — "+(result.sections||0)+" section(s).")
:("Registered, but not indexed: "+(result.message||"unknown reason"));
}
if(result.ok!==false){
const titleField=ops.querySelector("[data-source-title]");
const textField=ops.querySelector("[data-source-text]");
if(titleField)titleField.value="";
if(textField)textField.value="";
}
loadOperations(root);
},
error(error){if(status)status.textContent=apiErrorMessage(error);}});
return;
}

const reindex=event.target.closest("[data-reindex-source]");
const reindexAll=event.target.closest("[data-reindex-stale]");
if(reindex||reindexAll){
frappe.call({method:"ucc_intelligence.api.reindex_knowledge",
args:reindex?{source:reindex.dataset.reindexSource}:{},
callback(){loadOperations(root);},
error(error){openModal("Could not re-index",tabChartNotice(apiErrorMessage(error)));}});
}
});

ops.addEventListener("change",function(event){
if(event.target.closest("[data-ops-status]")||event.target.closest("[data-ops-severity]"))loadFindings(root);
});
}


// ===========================================================================
// SETTINGS -- sections 2 and 4 of the agreed split
//
// 1 AI & providers, 3 presentation, 5 knowledge policy  -> the Frappe form
// 2 access & visibility, 4 monitoring rules             -> here
//
// NO NEW PERMISSION CONCEPTS. Access shows what UCC Dashboard Access already
// decides, plus a read-only mirror of the two DocType permissions that govern
// editing tabs and closing findings -- so the whole model is legible in one
// place without inventing a second one.
// ===========================================================================
// ONE surface, all five sections. The gear used to make you CHOOSE between a
// Sophia page and the Frappe form, which meant three of the five sections were
// always somewhere you were not -- a dead end whichever you picked.
window.UCCSettings={open:function(){
openModal("Sophia settings",tabChartNotice("Loading…"));
if(!(window.frappe&&frappe.call))return;
const collected={};
let waiting=3;
function done(){if(--waiting===0)renderSettings(collected);}
frappe.call({method:"ucc_intelligence.api.get_platform_settings",
callback(r){collected.platform=(r&&r.message)||{};done();},
error(e){collected.platform={ok:false,message:apiErrorMessage(e)};done();}});
frappe.call({method:"ucc_intelligence.api.get_access_overview",
callback(r){collected.access=(r&&r.message)||{};done();},
error(e){collected.access={ok:false,message:apiErrorMessage(e)};done();}});
frappe.call({method:"ucc_intelligence.api.get_monitoring_overview",
callback(r){collected.monitoring=(r&&r.message)||{};done();},
error(){collected.monitoring={};done();}});
}};

function settingsField(field){
const id="set-"+field.fieldname;
// humaniseColumn is shared with the chart columns, so the acronym is fixed
// here rather than teaching it a settings-only special case.
const label=humaniseColumn(field.fieldname.replace(/^enable_/,"enable ")).replace(/\bAi\b/g,"AI");
if(field.fieldtype==="Check"){
return'<label class="ucc-set-check"><input type="checkbox" id="'+esc(id)+'" '
+'data-setting="'+esc(field.fieldname)+'" data-kind="Check"'
+(field.value?" checked":"")+"> "+esc(label)+"</label>";
}
const type=(field.fieldtype==="Int"||field.fieldtype==="Float")?"number":"text";
// ai_provider is a Select on the DocType. A free-text box beside it would let
// someone type a provider the app cannot call, and only find out at ask time.
// ai_model is also a Select but ships with NO options, so it falls through to
// a text box rather than an empty dropdown nobody can pick a model from.
const options=String(field.options||"").split("\n").filter(function(v){return v!=="";});
if(field.fieldtype==="Select"&&options.length){
return'<label class="ucc-set-field"><span>'+esc(label)+"</span>"
+'<select data-setting="'+esc(field.fieldname)+'" data-kind="Select">'
+options.map(function(option){
return'<option'+(String(field.value||"")===option?" selected":"")+">"+esc(option)+"</option>";
}).join("")+"</select></label>";
}
if(field.fieldtype==="Small Text"){
return'<label class="ucc-set-field"><span>'+esc(label)+"</span>"
+'<textarea rows="4" data-setting="'+esc(field.fieldname)+'" data-kind="Small Text">'
+esc(field.value==null?"":field.value)+"</textarea></label>";
}
return'<label class="ucc-set-field"><span>'+esc(label)+"</span>"
+'<input type="'+type+'" data-setting="'+esc(field.fieldname)+'" '
+'data-kind="'+esc(field.fieldtype)+'" value="'+esc(field.value==null?"":field.value)+'"></label>';
}

function settingsRow(label,allowed,note){
return'<tr><td>'+esc(label)+"</td>"
+'<td><span class="ucc-ops-state is-'+(allowed?"on":"off")+'">'
+(allowed?"Yes":"No")+"</span></td>"
+"<td><small>"+esc(note||"")+"</small></td></tr>";
}

function renderSettings(data){
const access=data.access||{};
const platform=data.platform||{};
const criteria=access.criteria||[];
const rules=(data.monitoring||{}).rules||[];
const sections=platform.sections||[];
openModal("Sophia settings",
'<p class="ucc-chart-picker-note">Everything that is set once for the whole '
+"institution, in one place. Anything that belongs to a single tab — its charts, "
+"its introduction, which questions it shows — stays on that tab.</p>"
+'<nav class="ucc-settings-nav">'
+["ai","presentation","knowledge","monitoring","access"].map(function(key){
const labels={ai:"AI and providers",presentation:"Presentation",
knowledge:"Document knowledge",monitoring:"Monitoring rules",access:"Access and visibility"};
return'<a href="#ucc-set-'+key+'">'+labels[key]+"</a>";
}).join("")+"</nav>"
+(platform.ok===false
?tabChartNotice(platform.message||"These settings are not available to your account.")
:sections.map(function(section){
return'<h4 class="ucc-settings-heading" id="ucc-set-'+esc(section.key)+'">'
+esc(section.label)+"</h4>"
+'<div class="ucc-ops-form">'+(section.fields||[]).map(settingsField).join("")+"</div>";
}).join("")
+'<div class="ucc-settings-save"><button type="button" class="ucc-ops-primary" '
+'data-save-settings>Save these settings</button>'
+'<span class="ucc-ops-hint" data-settings-saved></span></div>')
+'<h4 class="ucc-settings-heading" id="ucc-set-access">Access and visibility</h4>'
+(access.ok===false?tabChartNotice(access.message||"Access settings are unavailable.")
:'<p class="ucc-ops-help">'+esc(access.note||"")+"</p>"
+'<div class="table-wrap"><table class="ucc-history-table"><thead><tr>'
+"<th>What</th><th>You can see it</th><th>Decided by</th></tr></thead><tbody>"
+criteria.map(function(row){
return settingsRow(row.key.replace("criterion_","Criterion "),row.visible,"UCC Dashboard Access");
}).join("")
+Object.keys(access.modules||{}).map(function(key){
return settingsRow("Ask UCC · "+key.replace("ask_","").replace(/_/g," "),
access.modules[key],"UCC Dashboard Access");
}).join("")
+settingsRow("Edit tabs (charts, intro, questions)",access.can_edit_tabs,
"Write on UCC Analytics Tab — Role Permission Manager")
+settingsRow("Resolve or suppress findings",access.can_manage_findings,
"Write on UCC Monitoring Finding — Role Permission Manager")
+settingsRow("Register knowledge documents",access.can_manage_sources,
"Write on UCC Knowledge Source — Role Permission Manager")
+"</tbody></table></div>")
+'<h4 class="ucc-settings-heading">Monitoring rules</h4>'
+'<p class="ucc-ops-help"><strong>Rules are built into Sophia and cannot be added '
+"here.</strong> Ask your developer to add a new one. You can turn each rule on or "
+"off and change how serious it is — that is all that is editable, because a rule "
+"an auditor cannot trust is not worth running.</p>"
+(rules.length?'<div class="table-wrap"><table class="ucc-history-table"><thead><tr>'
+'<th class="ucc-col-rule">Rule</th><th>Looks at</th><th>On</th><th>Severity</th>'
+"</tr></thead><tbody>"
+rules.map(function(rule){
return"<tr><td><strong>"+esc(rule.title)+"</strong></td>"
+"<td>"+esc(rule.target_doctype||"—")+"</td>"
+'<td><input type="checkbox" data-rule-enabled="'+esc(rule.rule_id)+'"'
+(rule.enabled?" checked":"")+"></td>"
+'<td><select data-rule-severity="'+esc(rule.rule_id)+'">'
+["High","Medium","Low"].map(function(level){
return'<option'+(rule.severity===level?" selected":"")+">"+level+"</option>";
}).join("")+"</select></td></tr>";
}).join("")+"</tbody></table></div>"
:tabChartNotice("No monitoring rules are registered."))
+'<p class="ucc-ops-hint" data-settings-status></p>'
// The Frappe form stays reachable as an ESCAPE HATCH, not a destination --
// every section above is editable here, so nothing is lost by never clicking
// it, and nothing is hidden if you do.
+'<p class="ucc-ops-hint">Advanced: the same settings are also on the '
+'<a href="/app/ucc-intelligence-settings">Frappe form</a>.</p>');
}

// One delegated handler for both controls. The server re-checks the
// permission; this only decides what is drawn.
document.addEventListener("click",function(event){
const save=event.target.closest("[data-save-settings]");
if(!save||!(window.frappe&&frappe.call))return;
const values={};
document.querySelectorAll("[data-setting]").forEach(function(field){
values[field.dataset.setting]=field.type==="checkbox"
?(field.checked?"1":"0"):field.value;
});
const saved=document.querySelector("[data-settings-saved]");
if(saved)saved.textContent="Saving…";
frappe.call({method:"ucc_intelligence.api.save_platform_settings",
args:{values:JSON.stringify(values)},
callback(response){
const result=(response&&response.message)||{};
if(saved)saved.textContent=result.ok
?("Saved "+((result.written||[]).length)+" setting(s).")
:"Could not save.";
},
error(error){if(saved)saved.textContent=apiErrorMessage(error);}});
});

document.addEventListener("change",function(event){
const toggle=event.target.closest("[data-rule-enabled]");
const severity=event.target.closest("[data-rule-severity]");
if(!toggle&&!severity)return;
if(!(window.frappe&&frappe.call))return;
const status=document.querySelector("[data-settings-status]");
const args=toggle
?{rule_id:toggle.dataset.ruleEnabled,enabled:toggle.checked?"1":"0"}
:{rule_id:severity.dataset.ruleSeverity,severity:severity.value};
if(status)status.textContent="Saving…";
frappe.call({method:"ucc_intelligence.api.set_monitoring_rule",args:args,
callback(){if(status)status.textContent="Saved.";},
error(error){if(status)status.textContent=apiErrorMessage(error);}});
});

// --- #1: the change history, somewhere readable -----------------------------
// The records are in Desk as UCC Analytics Tab Change, but "open the list view
// and filter it" is not an answer for the person who owns the tab. This is the
// same information, where the tab is.
function tabTimestamp(value){
if(!value)return "";
const parsed=new Date(String(value).replace(" ","T"));
if(isNaN(parsed.getTime()))return String(value);
return parsed.toLocaleString(undefined,{day:"numeric",month:"short",year:"numeric",
hour:"numeric",minute:"2-digit"});
}

function openTabHistory(dashboard,tab){
openModal("Tab history",tabChartNotice("Loading…"));
if(!(window.frappe&&frappe.call))return;
frappe.call({
method:"ucc_intelligence.api.get_tab_history",
args:{criterion:dashboard.dataset.demoDashboard,tab:tab,limit:100},
callback(response){
const changes=((response&&response.message)||{}).changes||[];
openModal("Tab history",changes.length
?'<p class="ucc-chart-picker-note">Every change to how this tab is set up. '
+"Configuration only — no figures are recorded here.</p>"
+'<div class="table-wrap"><table class="ucc-history-table"><thead><tr>'
+"<th>When</th><th>Who</th><th>What changed</th></tr></thead><tbody>"
+changes.map(function(change){
return"<tr><td>"+esc(tabTimestamp(change.changed_at))+"</td>"
+"<td>"+esc(change.changed_by)+"</td>"
+"<td>"+esc(change.summary||change.action)+"</td></tr>";
}).join("")+"</tbody></table></div>"
:tabChartNotice("Nothing has been changed on this tab yet."));
},
error(error){openModal("Tab history",tabChartNotice(apiErrorMessage(error)));},
});
}

// --- #6: export the tab as a PDF -------------------------------------------
// window.print() with a print stylesheet, not a PDF library and not a
// server-side render. The charts are live DOM; the browser already knows how
// to put exactly what is on screen onto a page, and "Save as PDF" is in every
// print dialog. A server-side renderer would have to re-execute every query
// and re-draw every chart to produce a worse copy of what the user is looking
// at, and would need its own permission story to do it.
//
// Forced into View mode first, so no x, grip, handle or Add button can reach
// the page an auditor is handed.
function exportTabPdf(dashboard,config,tab){
tabEditModes[dashboard.dataset.demoDashboard]=false;
renderTabCharts(dashboard,config,tab);
renderTabActions(dashboard,tab);
renderTabIntro(dashboard,config,tab);
renderQa(dashboard,dashboardState(dashboard).result,tab);

const stamp=document.createElement("div");
stamp.className="ucc-print-stamp";
stamp.innerHTML="<strong>"+esc("Criterion "+config.number+" · "+config.title)+"</strong>"
+"<span>"+esc(tab==="overview"?"Overview":tab)+" · as at "
+esc(new Date().toLocaleString(undefined,{day:"numeric",month:"long",year:"numeric",
hour:"numeric",minute:"2-digit"}))+"</span>";

const platformRoot=dashboard.closest(".ucc-platform")||document.body;
platformRoot.classList.add("ucc-printing");
dashboard.classList.add("ucc-print-target");
dashboard.insertBefore(stamp,dashboard.firstChild);

function cleanup(){
platformRoot.classList.remove("ucc-printing");
dashboard.classList.remove("ucc-print-target");
if(stamp.parentNode)stamp.parentNode.removeChild(stamp);
window.removeEventListener("afterprint",cleanup);
}
window.addEventListener("afterprint",cleanup);
// A browser that never fires afterprint would leave the page stamped.
window.setTimeout(cleanup,60000);
// The renders above are synchronous but the charts they repaint are not; one
// beat lets the layout settle before the dialog opens.
window.setTimeout(function(){window.print();},250);
}

// --- Explore auto-population (#7) -------------------------------------------
// Explore already reads window.UCCLiveVisualDefinitions and already exposes
// UCCExplore.rebuild(). Publishing the added charts into that global is the
// whole feature: Explore becomes a live catalogue of what people have
// embedded, with no separate list to maintain and no change to the ported
// Explore code at all.
function syncExploreCatalogue(){
const catalogue={};
Object.keys(tabChartState).forEach(function(key){
const parts=key.split("::");
const state=tabChartState[key];
if(!state||!state.charts||!state.charts.length)return;
catalogue[parts[0]]=catalogue[parts[0]]||{};
catalogue[parts[0]][parts[1]]=state.charts.map(function(chart){
return{id:chart.chart,title:chart.title,type:"insights",
description:"Embedded Frappe Insights chart"};
});
});
window.UCCLiveVisualDefinitions=catalogue;
if(window.UCCExplore&&window.UCCExplore.rebuild)window.UCCExplore.rebuild();
}

// The picker. A search box over Insights queries THIS user can read, and one
// click to embed. No preview step: the chart appears on the tab immediately,
// which is a faster way to find out it was the wrong one than a preview pane.
function openChartPicker(dashboard,config,tab){
// Three buttons, not a dropdown: there are three choices and they fit on one
// line, so a dropdown would hide two of them behind a click for no gain.
const PICKER_KINDS=[["all","All"],["charts","Charts only"],["tables","Table only"]];
// STEP 1 is a workbook, STEP 2 is its contents. Insights organises everything
// by workbook, so a flat cross-workbook list makes you scan past things you
// know are somewhere else. "All workbooks" stays as the first entry: the
// charts already on the tabs were picked from a flat list, so someone
// re-adding one has no workbook to remember, and that case still has to work.
// STEP 1 IS WORKBOOKS AND NOTHING ELSE.
//
// It previously carried an "All workbooks" row at the top, offering the whole
// flat list in one click. Felix saw it on the bench and had it removed: a
// step-one entry that skips step one is not a two-step flow, it is a one-step
// flow with a detour, and its total sat next to a workbook's own count with
// nothing to tell the two numbers apart.
//
// The server still accepts an unscoped search -- settings/status.py uses it --
// so nothing was deleted, only stopped being offered here.
openModal("Add a chart to this tab",
'<div class="ucc-chart-picker">'
+'<div data-picker-step1>'
+'<p class="ucc-chart-picker-note">Charts and queries live in workbooks in '
+'Frappe Insights. Choose the workbook first.</p>'
+'<div class="ucc-chart-picker-results" data-workbook-list>'+tabChartNotice("Loading…")+"</div></div>"
+'<div data-picker-step2 hidden>'
+'<button type="button" class="ucc-chart-picker-back" data-picker-back>&#8592; Choose a different workbook</button>'
+'<h4 class="ucc-chart-picker-where" data-picker-where></h4>'
+'<p class="ucc-chart-picker-note" data-picker-summary></p>'
+'<div class="ucc-chart-picker-kinds" role="group" aria-label="Filter the list">'
+PICKER_KINDS.map(function(entry){
return'<button type="button" class="ucc-chart-picker-kind'+(entry[0]==="all"?" is-on":"")
+'" data-picker-kind="'+esc(entry[0])+'" aria-pressed="'+(entry[0]==="all")+'">'
+esc(entry[1])+'<span class="ucc-chart-picker-count" data-kind-count="'+esc(entry[0])+'"></span>'
+"</button>";
}).join("")+"</div>"
+'<input type="search" class="ucc-chart-picker-search" data-chart-picker-search '
+'placeholder="Search Frappe Insights charts…" autocomplete="off" aria-label="Search Insights charts">'
+'<p class="ucc-chart-picker-note">Only things you can already open in Frappe Insights are listed.</p>'
+'<div class="ucc-chart-picker-results" data-chart-picker-results>'+tabChartNotice("Loading…")+"</div>"
+"</div></div>");
const modal=ensureModal();
const step1=modal.querySelector("[data-picker-step1]");
const step2=modal.querySelector("[data-picker-step2]");
const bookList=modal.querySelector("[data-workbook-list]");
const where=modal.querySelector("[data-picker-where]");
const summary=modal.querySelector("[data-picker-summary]");
const input=modal.querySelector("[data-chart-picker-search]");
const results=modal.querySelector("[data-chart-picker-results]");
if(!input||!results||!step1||!step2||!bookList)return;
let timer=null;
let kind="all";
// No workbook chosen yet. Step 2 never renders until this is set, so the
// picker cannot open onto a list of charts.
let workbook="";

// EVERY NUMBER SAYS WHAT IT COUNTS.
//
// A bare "11" beside an "All 2" reads as a contradiction, because neither says
// what it is counting. These spell it out in words, and the workbook's name
// sits above its own numbers so a count is never orphaned from its subject.
function countPhrase(counts){
const parts=[];
if(counts.charts)parts.push(counts.charts+(counts.charts===1?" chart":" charts"));
if(counts.tables)parts.push(counts.tables
+(counts.tables===1?" query with no chart":" queries with no chart"));
return parts.join(" · ")||"nothing you can read";
}

function listWorkbooks(){
if(!(window.frappe&&frappe.call)){bookList.innerHTML=tabChartNotice("Frappe API client unavailable.");return;}
frappe.call({
method:"ucc_intelligence.api.list_insights_workbooks",
callback(response){
const data=(response&&response.message)||{};
const books=data.workbooks||[];
if(!books.length){
bookList.innerHTML=tabChartNotice(data.message
||"No Insights workbook holds anything you can read.");return;}
// Workbooks and nothing else. The name on its own line, what is inside it
// underneath in words -- so no number on this screen is a bare figure a
// reader has to attribute to something.
bookList.innerHTML=books.map(function(book){
return'<button type="button" class="ucc-chart-picker-result ucc-chart-picker-book" '
+'data-pick-workbook="'+esc(book.workbook)+'" data-workbook-title="'+esc(book.title)+'" '
+'data-workbook-counts="'+esc(JSON.stringify(book.counts))+'">'
+'<span class="ucc-chart-picker-book-name">'+esc(book.title)+"</span>"
+'<span class="ucc-chart-picker-book-what">'+esc(countPhrase(book.counts))+"</span>"
+"</button>";
}).join("");
},
error(error){bookList.innerHTML=tabChartNotice(apiErrorMessage(error));},
});
}

function showStep(which,title){
step1.hidden=which!==1;
step2.hidden=which!==2;
if(which===2){
// The workbook's name is a HEADING above its own numbers, so "All 2" can
// only be read as "2 in this workbook" -- there is no other subject on
// screen for it to belong to.
where.textContent="In " + (title||"this workbook");
input.focus();
}
}

function search(term){
// No workbook, no list. Enforced here rather than trusted to the call sites,
// so the picker cannot be made to open onto a flat cross-workbook list by
// some future caller reaching search() before a workbook is chosen.
if(!workbook)return;
if(!(window.frappe&&frappe.call)){results.innerHTML=tabChartNotice("Frappe API client unavailable.");return;}
frappe.call({
method:"ucc_intelligence.api.search_insights_charts",
args:{term:term||"",limit:20,kind:kind,workbook:workbook},
callback(response){
const data=(response&&response.message)||{};
const charts=data.charts||[];
// The counts describe the whole search, not this page, so a button never
// promises rows the filter will not produce.
const counts=data.counts||{};
PICKER_KINDS.forEach(function(entry){
const badge=modal.querySelector('[data-kind-count="'+entry[0]+'"]');
if(badge)badge.textContent=counts[entry[0]]==null?"":" "+counts[entry[0]];
});
// Says what the pills are counting, in words, once. Without it the three
// figures are the only numbers on screen and nothing states their subject.
if(summary)summary.textContent=counts.all==null?""
:("This workbook holds "+countPhrase(counts)+". Ones marked Table only have no "
+"Insights chart built yet and will show their rows as a table.");
if(!charts.length){
results.innerHTML=tabChartNotice(data.message
||(kind==="charts"?"No Insights chart is built on anything here."
:kind==="tables"?"Everything here already has a chart built on it."
:"Nothing here matched that search."));return;}
// BOTH kinds are listed, each marked. The probe found 52 queries and only
// 7 charts -- offering charts only would have hidden 45 things that work,
// since a chart-less query still shows its real rows as a table, exports,
// and drills down to records. Marked so nothing is a surprise after adding.
results.innerHTML=charts.map(chart=>
`<button type="button" class="ucc-chart-picker-result" data-pick-chart="${esc(chart.chart)}">`
+`${esc(chart.title)}`
+(chart.has_chart
?`<span class="ucc-chart-picker-type">${esc(chart.chart_type||"chart")}</span>`
:`<span class="ucc-chart-picker-type is-table" title="No Insights chart has been built for this query yet, so it shows as a table">Table only</span>`)
+`</button>`).join("");
},
error(error){results.innerHTML=tabChartNotice(apiErrorMessage(error));},
});
}
input.addEventListener("input",function(){
clearTimeout(timer);
timer=setTimeout(function(){search(input.value);},250);
});
const kinds=modal.querySelector(".ucc-chart-picker-kinds");
if(kinds)kinds.addEventListener("click",function(event){
const button=event.target.closest("[data-picker-kind]");
if(!button||button.dataset.pickerKind===kind)return;
kind=button.dataset.pickerKind;
kinds.querySelectorAll("[data-picker-kind]").forEach(function(other){
const on=other.dataset.pickerKind===kind;
other.classList.toggle("is-on",on);
other.setAttribute("aria-pressed",String(on));
});
// The search term is kept. Narrowing the kind is not a reason to lose what
// someone already typed.
search(input.value);
});
bookList.addEventListener("click",function(event){
const pick=event.target.closest("[data-pick-workbook]");
if(!pick)return;
workbook=pick.dataset.pickWorkbook;
// A new workbook is a new scope, so the kind resets to All. Carrying
// "Charts only" across would land someone in an empty list and leave them
// to work out that the filter, not the workbook, was the reason.
kind="all";
modal.querySelectorAll("[data-picker-kind]").forEach(function(other){
const on=other.dataset.pickerKind==="all";
other.classList.toggle("is-on",on);
other.setAttribute("aria-pressed",String(on));
});
input.value="";
results.innerHTML=tabChartNotice("Loading…");
if(summary)summary.textContent="";
showStep(2,pick.dataset.workbookTitle);
search("");
});
// Back to step 1 clears the chosen workbook, so the picker cannot be left
// holding a scope that is no longer on screen.
const back=modal.querySelector("[data-picker-back]");
if(back)back.addEventListener("click",function(){workbook="";showStep(1);});
results.addEventListener("click",function(event){
const pick=event.target.closest("[data-pick-chart]");
if(!pick)return;
event.preventDefault();
pick.disabled=true;
frappe.call({
method:"ucc_intelligence.api.add_tab_chart",
args:{criterion:dashboard.dataset.demoDashboard,tab:tab,chart:pick.dataset.pickChart},
callback(response){
applyTabConfig(dashboard,config,tab,(response&&response.message)||{});
modal.hidden=true;
},
error(error){pick.disabled=false;results.innerHTML=tabChartNotice(apiErrorMessage(error));},
});
});
// Opens on step 1, the workbook list. Step 2's own empty search lists the
// most recently modified, so it is useful before anyone types anything.
listWorkbooks();
}

function removeTabChart(dashboard,config,tab,chart){
if(!(window.frappe&&frappe.call))return;
frappe.call({
method:"ucc_intelligence.api.remove_tab_chart",
args:{criterion:dashboard.dataset.demoDashboard,tab:tab,chart:chart},
callback(response){applyTabConfig(dashboard,config,tab,(response&&response.message)||{});},
error(error){logEvent(dashboard,"ERROR","tab_chart_remove_failed",apiErrorMessage(error));},
});
}

const TAB_CHART_STYLE_ID="ucc-tab-chart-style";
function injectTabChartStyles(){
if(document.getElementById(TAB_CHART_STYLE_ID))return;
const style=document.createElement("style");
style.id=TAB_CHART_STYLE_ID;
style.textContent=`
.ucc-tab-charts{margin:0 0 18px}
.ucc-tab-charts-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 0 10px}
.ucc-tab-charts-head h2{margin:0;font-size:15px}
.ucc-add-chart{border:1px solid #D8E0EC;background:#fff;border-radius:8px;min-height:36px;padding:0 12px;font-size:12px;font-weight:600;cursor:pointer}
.ucc-add-chart:hover{background:#F1F5F9}
.ucc-tab-charts-notice{padding:14px 2px;font-size:12px;color:#64748B}
/* Twelve columns, so a card can be a quarter, a half, three quarters or the
   full width. The legacy .ucc-live-expanded-grid is a hard 2-column
   !important rule and .ucc-live-generated-card forces min-height:500px, which
   is why neither is reused here -- a "Small" card that is still half the row
   and 500px tall is not a size. */
.ucc-tab-charts-grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:14px;align-items:start}
.ucc-embedded-chart{grid-column:span 6;min-width:0;background:#fff;border:1px solid #D8E0EC;border-radius:10px;padding:12px 14px}
.ucc-embedded-chart-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;flex-wrap:wrap}
.ucc-embedded-chart-head h3{margin:0;font-size:13px;font-weight:600;color:#1E293B;min-width:0;word-break:break-word}
.ucc-embedded-chart-tools{display:flex;align-items:center;gap:6px;flex:none}
.ucc-embedded-views{display:inline-flex;border:1px solid #D8E0EC;border-radius:8px;overflow:hidden}
.ucc-embedded-views>button{border:0;background:#fff;min-height:30px;padding:0 10px;font-size:11px;font-weight:600;color:#64748B;cursor:pointer}
.ucc-embedded-views>button.is-active{background:#172554;color:#fff}
.ucc-tab-charts-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.ucc-tab-action{border:1px solid #D8E0EC;background:#fff;border-radius:8px;min-height:36px;padding:0 12px;font-size:12px;cursor:pointer;color:#334155}
.ucc-tab-action:hover{background:#F1F5F9}
.ucc-tab-mode.is-editing{background:#172554;border-color:#172554;color:#fff;font-weight:600}
/* #5: only an editable card advertises that it is editable. In View mode there
   is no grip, no handle and no x, so a finished tab reads as finished. */
.ucc-embedded-chart.is-editable{border-color:#C7D9F5;position:relative}
.ucc-embedded-chart.is-dragging{opacity:.45}
.ucc-drag-grip{cursor:grab;color:#94A3B8;font-size:13px;letter-spacing:-3px;user-select:none;padding:0 2px}
.ucc-embedded-chart.is-editable:active .ucc-drag-grip{cursor:grabbing}
.ucc-resize-handle{position:absolute;top:0;right:-5px;width:10px;height:100%;border:0;padding:0;
 background:transparent;cursor:col-resize;border-radius:0}
.ucc-resize-handle::after{content:"";position:absolute;top:50%;right:4px;width:2px;height:28px;
 margin-top:-14px;border-radius:2px;background:#C7D9F5}
.ucc-resize-handle:hover::after,.ucc-resize-handle:focus-visible::after{background:#2563EB;height:44px;margin-top:-22px}
.ucc-resize-handle:focus-visible{outline:2px solid #2563EB;outline-offset:1px}
.ucc-tab-charts-grid.is-resizing{cursor:col-resize;user-select:none}
.ucc-history-table{width:100%;border-collapse:collapse;font-size:12px}
.ucc-history-table th,.ucc-history-table td{border:1px solid #E6EBF3;padding:5px 8px;text-align:left;vertical-align:top}
.ucc-history-table th{font-weight:600;color:#64748B}
.ucc-open-records{border:1px solid #2563EB;background:#2563EB;color:#fff;border-radius:6px;
 min-height:26px;padding:0 10px;font-size:11px;font-weight:600;cursor:pointer;margin-left:8px}
.ucc-open-records:hover{background:#1D4ED8}
.ucc-drilldown-paging{display:flex;align-items:center;justify-content:flex-end;gap:10px;
 margin-top:10px;font-size:12px;color:#64748B}
.ucc-drilldown-paging button{border:1px solid #D8E0EC;background:#fff;border-radius:6px;
 min-height:28px;padding:0 10px;font-size:12px;cursor:pointer;color:#334155}
.ucc-drilldown-paging button:hover{background:#F1F5F9}
/* --- chart shapes driven by the Insights Chart record ---------------------
   Every one of these is CSS on real DOM nodes. No SVG is generated anywhere:
   the deleted hand-rolled renderers are not coming back, and a segment that
   stays a <button> is what keeps drill-down clickable and keyboard-reachable. */
.ucc-insights-plot{display:flex;align-items:stretch;gap:6px;height:200px;padding:4px 0}
.ucc-insights-point{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;
 gap:4px;border:0;background:transparent;cursor:pointer;padding:0;min-width:0;height:100%}
.ucc-insights-point:hover .ucc-insights-plot-fill{filter:brightness(1.15)}
.ucc-insights-point:focus-visible{outline:2px solid #2563EB;outline-offset:2px;border-radius:4px}
.ucc-insights-plot-track{flex:1;width:100%;display:flex;align-items:flex-end;justify-content:center;min-height:0}
.ucc-insights-plot-fill{width:100%;max-width:34px;border-radius:4px 4px 0 0;min-height:2px}
.ucc-insights-plot-value{font-size:11px;color:#334155;font-variant-numeric:tabular-nums}
.ucc-insights-plot-label{font-size:10px;color:#64748B;max-width:100%;overflow:hidden;
 text-overflow:ellipsis;white-space:nowrap}
.ucc-insights-donut-wrap{display:flex;align-items:center;gap:18px;flex-wrap:wrap}
/* legend_position, honoured. Insights' own setting, drawn rather than parsed
   and ignored -- see chart_presentation.py. */
.ucc-insights-donut-wrap[data-legend="left"]{flex-direction:row-reverse}
.ucc-insights-donut-wrap[data-legend="top"]{flex-direction:column-reverse;align-items:flex-start}
.ucc-insights-donut-wrap[data-legend="bottom"]{flex-direction:column;align-items:flex-start}
.ucc-insights-donut-wrap[data-legend="top"] .ucc-insights-donut-legend,
.ucc-insights-donut-wrap[data-legend="bottom"] .ucc-insights-donut-legend{width:100%}
/* The ring and its on-ring labels share one positioned box, so a label's
   angle is measured from the same centre the gradient sweeps around. */
.ucc-insights-donut-plot{position:relative;width:132px;height:132px;flex:none}
.ucc-insights-donut-marks{position:absolute;inset:0;pointer-events:none}
/* A pill, not bare white text. The palette runs from mid-blue to yellow, and
   white on #EAB308 is unreadable however heavy the shadow -- found by
   screenshot, on the light-green and yellow slices. The pill reads on every
   colour the palette can produce, including one someone pastes in later. */
.ucc-insights-donut-mark{position:absolute;left:50%;top:50%;font-size:10px;font-weight:700;
 color:#fff;background:rgba(15,23,42,.62);border-radius:999px;padding:1px 5px;
 line-height:1.3;white-space:nowrap}
.ucc-insights-donut{width:132px;height:132px;border-radius:50%;flex:none;
 -webkit-mask:radial-gradient(circle,transparent 54%,#000 55%);
 mask:radial-gradient(circle,transparent 54%,#000 55%)}
.ucc-insights-donut-legend{display:flex;flex-direction:column;gap:2px;min-width:180px;flex:1}
.ucc-insights-legend-item{display:flex;align-items:center;gap:8px;border:0;background:transparent;
 cursor:pointer;padding:3px 4px;border-radius:6px;text-align:left;font-size:12px;color:#334155}
.ucc-insights-legend-item:hover{background:#F1F5F9}
.ucc-insights-legend-item:focus-visible{outline:2px solid #2563EB;outline-offset:1px}
.ucc-insights-swatch{width:10px;height:10px;border-radius:3px;flex:none}
.ucc-insights-legend-label{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ucc-insights-legend-value{color:#64748B;font-variant-numeric:tabular-nums}
.ucc-insights-funnel{display:flex;flex-direction:column;gap:6px}
.ucc-insights-funnel-stage{display:flex;align-items:center;gap:8px;border:0;background:transparent;
 cursor:pointer;padding:2px 0;width:100%;text-align:left}
.ucc-insights-funnel-stage:hover .ucc-insights-funnel-bar{filter:brightness(1.1)}
.ucc-insights-funnel-stage:focus-visible{outline:2px solid #2563EB;outline-offset:2px;border-radius:4px}
.ucc-insights-funnel-label{width:120px;flex:none;font-size:11px;color:#334155;overflow:hidden;
 text-overflow:ellipsis;white-space:nowrap}
.ucc-insights-funnel-bar{height:24px;border-radius:4px;display:flex;align-items:center;
 justify-content:flex-end;padding:0 8px;min-width:34px}
.ucc-insights-funnel-bar span{font-size:11px;color:#fff;font-weight:600;font-variant-numeric:tabular-nums}
.ucc-insights-funnel-drop{font-size:10px;color:#94A3B8;font-variant-numeric:tabular-nums}
.ucc-insights-number{display:flex;flex-direction:column;gap:2px;padding:18px 4px}
.ucc-insights-number strong{font-size:34px;color:#172554;font-variant-numeric:tabular-nums;line-height:1}
.ucc-insights-number span{font-size:12px;color:#64748B}
.ucc-insights-axis-label{margin:8px 0 0;font-size:11px;color:#64748B;text-align:center}
/* The labelled fallback. Never blank, never a broken chart -- it says why. */
.ucc-insights-table-only{padding:10px 0}
.ucc-insights-table-note{margin:0;font-size:12px;color:#64748B}
.ucc-chart-picker-type{display:inline-block;margin-left:8px;font-size:10px;font-weight:600;
 padding:1px 6px;border-radius:999px;background:#EFF6FF;color:#1D4ED8;text-transform:uppercase;
 letter-spacing:.03em}
.ucc-chart-picker-type.is-table{background:#F1F5F9;color:#64748B}
.ucc-palette-control{display:flex;align-items:center;gap:6px;margin-left:auto}
.ucc-palette-control input{width:34px;height:26px;padding:0;border:1px solid #D8E0EC;border-radius:6px;
 background:#fff;cursor:pointer}
/* --- Operations workspace ------------------------------------------------- */
/* #1: the tables were flush against the workspace edge. */
.ucc-ops{padding:4px 18px 24px}
.ucc-ops-head{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;
 flex-wrap:wrap;margin-bottom:14px}
.ucc-ops-head h2{margin:0;font-size:17px;color:#172554}
.ucc-ops-head p{margin:2px 0 0;font-size:12px;color:#64748B}
.ucc-ops-tabs{display:inline-flex;border:1px solid #D8E0EC;border-radius:8px;overflow:hidden}
.ucc-ops-tabs button{border:0;background:#fff;min-height:32px;padding:0 14px;font-size:12px;
 font-weight:600;color:#64748B;cursor:pointer}
.ucc-ops-tabs button.is-active{background:#172554;color:#fff}
.ucc-ops-banner{background:#FEF9C3;border:1px solid #FDE68A;color:#713F12;border-radius:8px;
 padding:8px 12px;font-size:12px;margin-bottom:14px}
.ucc-ops-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;
 margin-bottom:18px}
.ucc-ops-stat{background:#fff;border:1px solid #E6EBF3;border-radius:10px;padding:12px 14px}
.ucc-ops-stat strong{display:block;font-size:26px;color:#172554;font-variant-numeric:tabular-nums;line-height:1.1}
.ucc-ops-stat span{font-size:11px;color:#64748B}
.ucc-ops-stat.is-high{border-left:3px solid #EF4444}
.ucc-ops-stat.is-medium{border-left:3px solid #F97316}
.ucc-ops-stat.is-low{border-left:3px solid #64748B}
.ucc-ops-section{background:#fff;border:1px solid #E6EBF3;border-radius:10px;padding:14px;margin-bottom:14px}
.ucc-ops-section h3{margin:0 0 10px;font-size:13px;color:#172554}
.ucc-ops-section-head{display:flex;align-items:center;justify-content:space-between;gap:12px;
 flex-wrap:wrap;margin-bottom:10px}
.ucc-ops-section-head h3{margin:0}
.ucc-ops-filters{display:flex;gap:10px;flex-wrap:wrap}
.ucc-ops-filters label{font-size:11px;color:#64748B;display:flex;align-items:center;gap:5px}
.ucc-ops-filters select{min-height:28px;border:1px solid #D8E0EC;border-radius:6px;font-size:12px;
 padding:0 6px;background:#fff;color:#334155}
.ucc-ops-empty{margin:0;font-size:12px;color:#64748B;padding:6px 0}
.ucc-ops-pill{display:inline-block;font-size:10px;font-weight:600;padding:2px 8px;border-radius:999px;
 text-transform:uppercase;letter-spacing:.03em}
.ucc-ops-pill.is-high{background:#FEE2E2;color:#B91C1C}
.ucc-ops-pill.is-medium{background:#FFEDD5;color:#C2410C}
.ucc-ops-pill.is-low{background:#F1F5F9;color:#475569}
.ucc-ops-actions{white-space:nowrap}
.ucc-ops-actions button{border:1px solid #D8E0EC;background:#fff;border-radius:6px;min-height:26px;
 padding:0 8px;font-size:11px;cursor:pointer;color:#334155;margin-right:4px}
.ucc-ops-actions button:hover{background:#F1F5F9}
.ucc-ops-form{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;align-items:end}
.ucc-ops-form label{display:flex;flex-direction:column;gap:4px;font-size:11px;color:#64748B}
.ucc-ops-form-wide{grid-column:1/-1}
.ucc-ops-form input,.ucc-ops-form select,.ucc-ops-form textarea{border:1px solid #D8E0EC;
 border-radius:6px;padding:6px 8px;font:inherit;font-size:12px;color:#334155;box-sizing:border-box}
.ucc-ops-primary{border:1px solid #172554;background:#172554;color:#fff;border-radius:8px;
 min-height:34px;padding:0 14px;font-size:12px;font-weight:600;cursor:pointer}
.ucc-ops-primary:hover{background:#1E3A8A}
.ucc-ops-hint{margin:8px 0 0;font-size:11px;color:#64748B}
.ucc-field-error{display:block;margin-top:4px;font-size:11px;color:#B91C1C}
.ucc-ops-form [aria-invalid="true"]{border-color:#EF4444}
.ucc-ops-fix{color:#2563EB}
/* #2: the rule names and their CLAUDE.md references were wrapping badly while
   a one-digit count had a wide column to itself. */
.ucc-col-rule{width:38%}
.ucc-col-open{width:56px;text-align:right}
.ucc-history-table td.ucc-col-open{text-align:right}
.ucc-ops-help{margin:0 0 12px;font-size:12px;color:#475569;background:#F8FAFC;
 border:1px solid #E6EBF3;border-left:3px solid #2563EB;border-radius:6px;padding:9px 12px;line-height:1.55}
.ucc-ops-help strong{color:#172554}
.ucc-settings-heading{margin:18px 0 8px;font-size:14px;color:#172554}
.ucc-settings-heading:first-of-type{margin-top:8px}
.ucc-settings-nav{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 14px}
.ucc-settings-nav a{font-size:11px;font-weight:600;color:#334155;background:#F1F5F9;
 border:1px solid #E2E8F0;border-radius:999px;padding:4px 10px;text-decoration:none}
.ucc-settings-nav a:hover{background:#E2E8F0}
.ucc-set-field{display:flex;flex-direction:column;gap:4px;font-size:11px;color:#64748B}
.ucc-set-field input,.ucc-set-field textarea,.ucc-set-field select{border:1px solid #D8E0EC;border-radius:6px;
 padding:6px 8px;font:inherit;font-size:12px;color:#334155;box-sizing:border-box}
/* .ucc-ops-form label sets column direction and outranks a bare .ucc-set-check,
   which stacked every checkbox above its own label. */
.ucc-ops-form label.ucc-set-check,.ucc-set-check{display:flex;flex-direction:row;
 align-items:center;gap:7px;font-size:12px;color:#334155;align-self:end;padding-bottom:6px}
.ucc-set-check input{margin:0;flex:0 0 auto}
.ucc-settings-save{display:flex;align-items:center;gap:10px;margin:14px 0 4px}
/* Same colour language as the severity pills and the findings table. */
.ucc-ops-state{display:inline-block;font-size:10px;font-weight:600;padding:2px 8px;
 border-radius:999px;text-transform:uppercase;letter-spacing:.03em}
.ucc-ops-state.is-on{background:#DCFCE7;color:#15803D}
.ucc-ops-state.is-off{background:#F1F5F9;color:#475569}
.ucc-ops-state.is-unset{background:#FEF3C7;color:#92400E}
@media(max-width:760px){.ucc-ops-head{flex-direction:column;align-items:flex-start}}

/* #4: the intro renders Markdown, so it needs the elements Markdown makes. */
/* #6: the intro headings were barely larger than body text, so a "#"
   heading read as bold body copy. Scaled to the shell's own type ramp
   (the workspace h2 is 17px), stepping down rather than flattening. */
.ucc-tab-intro-text h3{margin:14px 0 6px;font-size:19px;font-weight:600;color:#172554;line-height:1.3}
.ucc-tab-intro-text h4{margin:12px 0 5px;font-size:16px;font-weight:600;color:#172554}
.ucc-tab-intro-text h5{margin:10px 0 4px;font-size:14px;font-weight:600;color:#334155}
.ucc-tab-intro-text h6{margin:10px 0 4px;font-size:13px;font-weight:600;color:#334155;text-transform:uppercase;letter-spacing:.04em}
.ucc-tab-intro-text ol{margin:0 0 8px;padding-left:20px}
.ucc-tab-intro-text blockquote{margin:0 0 8px;padding:2px 0 2px 12px;border-left:3px solid #D8E0EC;color:#64748B}
.ucc-tab-intro-text hr{border:0;border-top:1px solid #D8E0EC;margin:10px 0}
.ucc-tab-intro-text a{color:#2563EB}
.ucc-remove-chart{border:0;background:transparent;font-size:18px;line-height:1;cursor:pointer;color:#64748B;padding:0 4px;min-height:30px}
.ucc-remove-chart:hover{color:#B91C1C}
.ucc-embedded-chart-body{padding:6px 0 2px}
.ucc-embedded-chart-table{padding:6px 0 2px;font-size:12px}
.ucc-embedded-chart-table table{width:100%;border-collapse:collapse}
.ucc-embedded-chart-table th,.ucc-embedded-chart-table td{border:1px solid #E6EBF3;padding:5px 8px;text-align:left}
.ucc-embedded-chart-table th{font-weight:600;color:#64748B}
.ucc-embedded-chart-filter{display:flex;align-items:center;gap:8px;margin:0 0 8px;font-size:12px;color:#334155}
.ucc-embedded-chart-filter button{border:1px solid #D8E0EC;background:#fff;border-radius:6px;min-height:28px;padding:0 8px;font-size:11px;cursor:pointer}
.ucc-tab-charts .hidden{display:none}
/* The tab intro (#4): editable, empty by default. */
.ucc-tab-intro{margin:0 0 14px;font-size:13px;line-height:1.6;color:#334155}
.ucc-tab-intro-text p{margin:0 0 8px}
.ucc-tab-intro-text ul{margin:0 0 8px;padding-left:20px}
.ucc-tab-intro-text code{background:#F1F5F9;padding:1px 4px;border-radius:4px;font-size:12px}
.ucc-tab-intro-empty{margin:0;color:#94A3B8;font-style:italic}
.ucc-tab-intro-edit,.ucc-intro-save,.ucc-intro-cancel{border:1px solid #D8E0EC;background:#fff;border-radius:8px;min-height:34px;padding:0 12px;font-size:12px;cursor:pointer;margin-top:6px}
.ucc-intro-save{background:#172554;color:#fff;border-color:#172554;font-weight:600}
.ucc-tab-intro-editor textarea{box-sizing:border-box;width:100%;padding:9px 10px;border:1px solid #D8E0EC;border-radius:8px;font:inherit;font-size:13px;line-height:1.5;resize:vertical}
.ucc-tab-intro-actions{display:flex;gap:8px}
/* The management-question controls (#6). */
.ucc-qa-tools{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin:10px 0 0}
.ucc-qa-add{border:1px solid #D8E0EC;background:#fff;border-radius:8px;min-height:34px;padding:0 12px;font-size:12px;font-weight:600;cursor:pointer}
.ucc-qa-add:hover{background:#F1F5F9}
.ucc-qa-hide{border:0;background:transparent;color:#64748B;font-size:16px;line-height:1;cursor:pointer;padding:0 4px;min-height:30px}
.ucc-qa-hide:hover{color:#B91C1C}
.ucc-qa-hidden-list{display:flex;flex-direction:column;gap:4px;max-height:320px;overflow-y:auto}
.ucc-qa-hidden-item{text-align:left;border:1px solid #D8E0EC;background:#fff;border-radius:8px;min-height:38px;padding:8px 10px;font-size:13px;cursor:pointer}
.ucc-qa-hidden-item:hover{background:#F1F5F9}
.ucc-chart-picker-back{border:0;background:none;color:#2563EB;font-size:12px;font-weight:600;
 cursor:pointer;padding:0;margin:0 0 8px}
.ucc-chart-picker-back:hover{text-decoration:underline}
.ucc-chart-picker-where{margin:0 0 10px;font-size:14px;color:#172554}
.ucc-chart-picker-book{display:flex;flex-direction:column;gap:2px;padding:10px 12px}
.ucc-chart-picker-book-name{font-weight:600;color:#172554}
.ucc-chart-picker-book-what{font-size:11px;color:#64748B}
/* PHASE 1 PILOT: the embedded Insights dashboard. A fixed height, because an
   iframe does not size to its content and there is no same-origin-safe way to
   ask it how tall it is without coupling to Insights' internals. */
.ucc-embed-dashboard{grid-column:1/-1}
.ucc-embed-frame{display:block;width:100%;height:620px;border:1px solid #E6EBF3;
 border-radius:12px;background:#fff}
.ucc-embed-note{margin:6px 0 0;font-size:11px;color:#64748B}
.ucc-chart-picker-kinds{display:flex;gap:6px;margin:0 0 10px;flex-wrap:wrap}
.ucc-chart-picker-kind{border:1px solid #D8E0EC;background:#fff;color:#475569;border-radius:999px;
 min-height:30px;padding:0 12px;font-size:12px;font-weight:600;cursor:pointer}
.ucc-chart-picker-kind:hover{background:#F1F5F9}
.ucc-chart-picker-kind.is-on{background:#172554;border-color:#172554;color:#fff}
.ucc-chart-picker-count{opacity:.65;font-weight:600}
.ucc-chart-picker-search{box-sizing:border-box;width:100%;padding:8px 10px;border:1px solid #D8E0EC;border-radius:8px;font-size:13px}
.ucc-chart-picker-note{margin:8px 0 4px;font-size:11px;color:#64748B}
.ucc-chart-picker-results{display:flex;flex-direction:column;gap:4px;max-height:340px;overflow-y:auto}
.ucc-chart-picker-result{text-align:left;border:1px solid #D8E0EC;background:#fff;border-radius:8px;padding:8px 10px;font-size:13px;cursor:pointer}
.ucc-chart-picker-result:hover{background:#F1F5F9}
.ucc-chart-picker-result[disabled]{opacity:.5;cursor:default}
.ucc-insights-series{display:flex;flex-direction:column;gap:6px;padding:8px 0}
/* Each bar is a button: clicking it is the drill-down. */
.ucc-insights-bar{display:grid;width:100%;grid-template-columns:minmax(90px,32%) 1fr auto;gap:8px;align-items:center;
 font:inherit;font-size:12px;text-align:left;border:0;background:transparent;padding:2px 0;cursor:pointer;color:inherit}
.ucc-insights-bar:hover .ucc-insights-bar-fill{background:#172554}
.ucc-insights-bar:focus-visible{outline:2px solid #2563EB;outline-offset:2px}
.ucc-insights-bar-label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ucc-insights-bar-track{background:#F1F5F9;border-radius:3px;height:14px;overflow:hidden}
.ucc-insights-bar-fill{display:block;height:100%;background:#2c5aa0;border-radius:3px}
.ucc-insights-bar-value{font-variant-numeric:tabular-nums;font-weight:600}
@media(max-width:1000px){.ucc-embedded-chart{grid-column:span 12!important}}

/* --- #6: what a printed / PDF-exported tab looks like ---------------------
   Everything except the criterion being exported is hidden, so the output is
   the tab and nothing else -- no workspace nav, no other criteria, and no
   edit controls, because exportTabPdf() forces View mode before it prints. */
@media print{
 .ucc-printing .ucc-platform-shell,
 .ucc-printing .sticky-navigation,
 .ucc-printing .hero-action-card,
 .ucc-printing .ucc-platform-workspace:not([data-ucc-workspace-panel="analytics"]),
 .ucc-printing .ucc-criterion-dashboard:not(.ucc-print-target),
 .ucc-printing .ucc-tab-charts-actions,
 .ucc-printing .ucc-tab-intro-edit,
 .ucc-printing .ucc-qa-tools,
 .ucc-printing .ucc-qa-hide,
 .ucc-printing .ucc-remove-chart,
 .ucc-printing .ucc-drag-grip,
 .ucc-printing .ucc-resize-handle,
 .ucc-printing .ucc-add-chart,
 .ucc-printing .ucc-embedded-views,
 .ucc-printing .loading-overlay{display:none!important}
 .ucc-printing .ucc-criterion-dashboard.ucc-hidden{display:block!important}
 .ucc-print-stamp{display:block;margin:0 0 14px;padding:0 0 10px;border-bottom:2px solid #172554}
 .ucc-print-stamp strong{display:block;font-size:16px;color:#172554}
 .ucc-print-stamp span{font-size:11px;color:#64748B}
 /* A chart split across a page break is not evidence of anything. */
 .ucc-embedded-chart,.ucc-management-panel,.ucc-tab-charts{break-inside:avoid;page-break-inside:avoid}
 .ucc-embedded-chart{border:1px solid #D8E0EC}
 .ucc-tab-charts-grid{gap:10px}
}
.ucc-print-stamp{display:none}
`;
document.head.appendChild(style);
}
// --- MANAGEMENT QUESTIONS AND DATA-BASED ANSWERS (#6) ----------------------
// The table itself is unchanged: every answer is computed live by the
// criterion engine, permission-checked, with its real status and its real
// record links. What is new is WHICH of them a tab shows.
//
// One stored list, of what is HIDDEN. The default therefore stays "everything
// this criterion can answer" -- storing what to SHOW instead would have
// emptied this table on all six criteria that already work, the moment this
// shipped. The x on a row hides it; "+ Add question" offers exactly the rows
// currently hidden. Never free text: the catalogue is the criterion engine's
// own answerable set, the same allowlist-not-free-text rule Ask UCC follows.
//
// CRITERION 4 IS EMPTY FOR A DIFFERENT REASON, and this table cannot fix it:
// analytics/criterion_4.py returns no metrics and no questions at all -- only
// admission_intelligence. That was the agreed scope when it was written, and
// its own docstring says so. Nothing deleted it. Until Criterion 4's ~40
// metrics are ported like the other six criteria, there is nothing to ask, so
// the table says that instead of pretending otherwise.
function qaQuestionId(row,index){
return String(row.metric_id||row.id||row.question||("row-"+index));
}

function renderQa(dashboard,result,tab){
const target=dashboard.querySelector(`[data-demo-qa="${CSS.escape(dashboard.dataset.demoDashboard+":"+((dashboardState(dashboard).lastPanel)||tab))}"]`)||dashboard.querySelector("[data-demo-panel]:not(.hidden) [data-demo-qa]");
if(!target)return;
const state=tabConfig(dashboard,tab);
const hidden=(state&&state.hiddenQuestions)||[];
const canEdit=isEditing(dashboard,tab);
const all=extendedQuestionRows(result,tab);
const rows=all.filter(function(row,index){return hidden.indexOf(qaQuestionId(row,index))===-1;});
target.innerHTML=rows.length?rows.map((row,index)=>{
const metric=metricById(result,row.metric_id);
const available=(metric?.status||row.status)==="available";
const count=Number(metric?.record_count??metric?.total??row.record_count??0);
const doctype=metric?.doctype||row.doctype||"";
const answerAction=available&&row.metric_id
?`<button type="button" class="record-link ucc-qa-action" data-live-qa-records="${esc(row.metric_id)}" data-live-qa-title="${esc(row.question||metric?.label||"Matching records")}">View ${count.toLocaleString()} matching record${count===1?"":"s"} ↗</button>`
:"";
const sourceAction=doctype
?`<button type="button" class="source-doctype-link ucc-qa-action" data-live-source-doctype="${esc(doctype)}">Open ${esc(displayDoctypeName(doctype))} list ↗</button>`
:'<span class="source-unavailable">No readable source list</span>';
const hideAction=canEdit?`<button type="button" class="ucc-qa-hide" data-hide-question="${esc(qaQuestionId(row,all.indexOf(row)))}" title="Hide this question on this tab" aria-label="Hide: ${esc(row.question||"")}">&times;</button>`:"";
return`<tr><td>${esc(row.criterion||result?.meta?.subcriterion||result?.policy?.policy||tab)}</td><td>${esc(row.question)}</td><td><div>${esc(row.answer)}</div>${answerAction}</td><td><div>${esc(sourceCalculation(row,metric))}</div>${sourceAction}</td><td>${statusBadge(metric?.status||row.status)}${hideAction}</td></tr>`;
}).join(""):`<tr><td colspan="5">${esc(all.length
?"Every management question for this section is hidden. Use “+ Add question” to bring one back."
:"This criterion does not answer any management questions yet. Its metric catalogue has not been built, so there is nothing to ask.")}</td></tr>`;
renderQaTools(dashboard,target,all.length,hidden.length,canEdit);
}

// The controls live directly under the table, in the same panel, so adding and
// removing a question happens where the questions are.
function renderQaTools(dashboard,tbody,total,hiddenCount,canEdit){
const panel=tbody.closest(".ucc-management-panel");
if(!panel)return;
let tools=panel.querySelector("[data-qa-tools]");
if(!tools){
tools=document.createElement("div");
tools.className="ucc-qa-tools";
tools.dataset.qaTools="1";
panel.appendChild(tools);
}
tools.innerHTML=(canEdit?`<button type="button" class="ucc-qa-add" data-add-question>+ Add question</button>`:"")
+`<span class="ucc-tab-charts-notice">${esc(hiddenCount
?hiddenCount+" of "+total+" hidden on this tab"
:total+" question"+(total===1?"":"s")+" available")}</span>`;
}

function setTabQuestion(dashboard,config,tab,question,visible){
if(!(window.frappe&&frappe.call))return;
frappe.call({
method:"ucc_intelligence.api.set_tab_question",
args:{criterion:dashboard.dataset.demoDashboard,tab:tab,question:question,visible:visible?1:0},
callback(response){applyTabConfig(dashboard,config,tab,(response&&response.message)||{});},
error(error){logEvent(dashboard,"ERROR","tab_question_failed",apiErrorMessage(error));},
});
}

// The picker lists exactly what this tab is currently hiding -- which is the
// whole catalogue minus what is on screen. Nothing here can invent a question
// the criterion engine cannot answer.
function openQuestionPicker(dashboard,config,tab){
const state=tabConfig(dashboard,tab);
const hidden=(state&&state.hiddenQuestions)||[];
const all=extendedQuestionRows(dashboardState(dashboard).result,tab);
const choices=all.filter(function(row,index){return hidden.indexOf(qaQuestionId(row,index))!==-1;});
openModal("Add a management question",
choices.length
?'<p class="ucc-chart-picker-note">Questions this criterion can answer that are hidden on this tab.</p>'
+'<div class="ucc-qa-hidden-list">'+choices.map(function(row){
return'<button type="button" class="ucc-qa-hidden-item" data-restore-question="'
+esc(qaQuestionId(row,all.indexOf(row)))+'">'+esc(row.question)+"</button>";
}).join("")+"</div>"
:'<p class="ucc-chart-picker-note">'+esc(all.length
?"Every question this criterion can answer is already on this tab."
:"This criterion does not answer any management questions yet, so there is nothing to add. Its metric catalogue has not been built.")
+"</p>");
const modal=ensureModal();
const list=modal.querySelector(".ucc-qa-hidden-list");
if(!list)return;
list.addEventListener("click",function(event){
const choice=event.target.closest("[data-restore-question]");
if(!choice)return;
event.preventDefault();
setTabQuestion(dashboard,config,tab,choice.dataset.restoreQuestion,true);
modal.hidden=true;
});
}

function renderSources(dashboard,result){
const target=dashboard.querySelector(`[data-demo-sources="${CSS.escape(dashboard.dataset.demoDashboard)}"]`);
if(!target)return;
const rows=result?.sources||[];
target.innerHTML=rows.length?rows.map(row=>{
const doctype=row.doctype||"";
const sourceName=doctype||row.candidates?.join(" / ")||row.key;
const action=doctype?`<button type="button" class="source-doctype-link ucc-qa-action" data-live-source-doctype="${esc(doctype)}">Open ${esc(displayDoctypeName(doctype))} list ↗</button>`:"";
return`<tr><td><div>${esc(sourceName)}</div>${action}</td><td>${esc(row.key||"Source")}</td><td>${statusBadge(row.status)} ${esc(row.message||"")}</td><td>${Number(row.count||0).toLocaleString()}</td></tr>`;
}).join(""):'<tr><td colspan="4">No source definitions returned.</td></tr>';
}
function renderQuality(dashboard,result){const target=dashboard.querySelector(`[data-demo-quality="${CSS.escape(dashboard.dataset.demoDashboard)}"]`);if(!target)return;const rows=result?.data_quality||[];target.innerHTML=rows.length?rows.map(row=>`<tr><td>${esc(row.check)}</td><td>${esc(row.source)}</td><td>${statusBadge(row.status)}</td><td>${esc(row.detail)}</td></tr>`).join(""):'<tr><td>Live source and metric checks</td><td>0</td><td>'+statusBadge("available")+'</td><td>No readiness issue returned.</td></tr>';}
function renderError(dashboard,config,error){
const notice=dashboard.querySelector("[data-demo-readiness]"),title=dashboard.querySelector("[data-demo-readiness-title]"),copy=dashboard.querySelector("[data-demo-readiness-copy]");
const detail=error&&error.message?error.message:String(error);
const viewName=`Criterion ${config.number} ${config.title||""}`.trim();
// A permission block is not an outage: name the view and the blocked source in
// plain language and keep the raw Frappe text out of the user-facing copy.
if(UCCShared.isPermissionError(detail)){
const source=UCCShared.permissionSource(detail);
if(notice)notice.dataset.status="blocked";
if(title)title.textContent=`${viewName} is not available to your account.`;
if(copy)copy.textContent=`Blocked data source: ${source}. Your account doesn't have read access to this. Ask an administrator to grant access if you need to see this.`;
if(notice)notice.hidden=false;
return;
}
if(notice)notice.dataset.status="error";
if(title)title.textContent=`Criterion ${config.number} live API unavailable.`;
if(copy)copy.textContent=detail;
if(notice)notice.hidden=false;
}
function updateDashboardIdentity(dashboard,config,tab){
const isAdmission=dashboard.dataset.demoDashboard==="criterion_4"&&tab==="4.1.1";
dashboard.classList.toggle("ucc-admission-intelligence",isAdmission);
const kicker=dashboard.querySelector(".ucc-criterion-kicker"),heading=dashboard.querySelector(".hero-copy h1"),description=dashboard.querySelector(".hero-copy p");
if(isAdmission){if(kicker)kicker.textContent="EDUTRUST CRITERION 4.1.1";if(heading)heading.textContent="Admission Intelligence";if(description)description.textContent="Live admission analytics for applicants, approvals, enrolment conversion, programmes, countries, agents and counselling duration.";}
else{if(kicker)kicker.textContent=`EDUTRUST CRITERION ${config.number}`;if(heading)heading.textContent=`Criterion ${config.number} · ${config.title}`;if(description)description.textContent=config.description;}
const panelHeading=dashboard.querySelector(`[data-demo-panel="${CSS.escape((config.panelMap&&config.panelMap[tab])||tab)}"] .ucc-management-panel .panel-head h2`);
if(panelHeading)panelHeading.textContent=isAdmission?"Admissions Insights and Data-Based Answers":"Management Questions and Data-Based Answers";
}
function renderDashboard(dashboard){const config=CONFIG[dashboard.dataset.demoDashboard],state=dashboardState(dashboard),result=state.result;if(!config)return;const tab=activeSection(dashboard);updateDashboardIdentity(dashboard,config,tab);if(state.error&&!result){renderError(dashboard,config,state.error);return;}renderTabCharts(dashboard,config,tab);renderQa(dashboard,result,tab);renderSources(dashboard,result);renderQuality(dashboard,result);}
// Option B: admission_intelligence's 6 chart series + 4 KPIs are served live
// from Frappe Insights (real Query v3 execute(), permission-checked per
// request -- see ucc_intelligence/ucc_intelligence/analytics/
// admission_intelligence_embed.py) instead of the legacy Server Script's own
// computation. Criterion 4's other ~40 metrics still come from
// ucc_analytics_criterion_4 untouched -- this only overwrites the
// admission_intelligence sub-object callApi() already returned.
function loadAdmissionIntelligenceEmbed(){
return new Promise((resolve,reject)=>{
if(!(window.frappe&&frappe.call)){reject(new Error("Frappe API client is unavailable."));return;}
frappe.call({
method:"ucc_intelligence.api.get_admission_intelligence",
callback(response){resolve((response&&response.message)||null);},
error(error){reject(new Error(apiErrorMessage(error)));}
});
});
}
async function loadLive(dashboard,force=false){const config=CONFIG[dashboard.dataset.demoDashboard],state=dashboardState(dashboard),section=apiSection(config,dashboard,activeSection(dashboard));ensureTabChartArea(dashboard,config,activeSection(dashboard));if(state.loading)return;if(!force&&state.result&&state.result.meta?.subcriterion===section){renderDashboard(dashboard);return;}state.loading=true;state.error=null;setLoading(dashboard,true,15,`Loading ${section}`);try{const result=await callApi(config,dashboard,"summary");if(dashboard.dataset.demoDashboard==="criterion_4"&&section==="4.1.1"){setLoading(dashboard,true,60,"Loading Insights-embedded admission analytics");try{const embed=await loadAdmissionIntelligenceEmbed();if(embed){result.admission_intelligence=embed;result.sources=(result.sources||[]).concat(embed.sources||[]);}}catch(embedError){logEvent(dashboard,"ERROR","admission_intelligence_embed_failed",embedError.message||embedError);}}setLoading(dashboard,true,80,"Rendering live analytics");state.result=result;state.error=null;renderDashboard(dashboard);setLoading(dashboard,true,100,"Live analytics ready");setTimeout(()=>setLoading(dashboard,false),150);}catch(error){state.error=error;logEvent(dashboard,"ERROR","api_failure",error.message||error);renderDashboard(dashboard);setLoading(dashboard,false);}finally{state.loading=false;}}
function showTab(dashboard,tab){const config=CONFIG[dashboard.dataset.demoDashboard];dashboard.dataset.demoActiveTab=tab;dashboard.querySelectorAll("[data-demo-tab]").forEach(button=>button.classList.toggle("active",button.dataset.demoTab===tab));const panelKey=(config.panelMap&&config.panelMap[tab])||tab;dashboardState(dashboard).lastPanel=panelKey;dashboard.querySelectorAll("[data-demo-panel]").forEach(panel=>panel.classList.toggle("hidden",panel.dataset.demoPanel!==panelKey));ensureTabChartArea(dashboard,config,tab);syncTabChartVisibility(dashboard,tab);if(tab!=="quality"&&tab!=="sources")loadLive(dashboard);else renderDashboard(dashboard);}
function allQaRows(result){return extendedQuestionRows(result,result?.meta?.subcriterion||"section").map(row=>[row.criterion,row.question,row.answer,sourceCalculation(row,metricById(result,row.metric_id)),row.status]);}
function allExceptionRows(result){return(result?.exceptions||[]).map(row=>[row.id,row.label,metricValue(row),row.status,row.doctype||row.source]);}
function ensureModal(){let modal=platform.querySelector("[data-demo-modal]");if(modal)return modal;modal=document.createElement("div");modal.className="ucc-demo-modal";modal.dataset.demoModal="1";modal.hidden=true;modal.innerHTML=`<div class="ucc-demo-modal-card"><header><div><strong data-demo-modal-title>Analytics details</strong><span>Permission-aware live data</span></div><button type="button" data-demo-modal-close aria-label="Close">×</button></header><div class="ucc-demo-modal-body" data-demo-modal-body></div></div>`;platform.appendChild(modal);modal.querySelector("[data-demo-modal-close]").addEventListener("click",()=>modal.hidden=true);modal.addEventListener("click",event=>{if(event.target===modal)modal.hidden=true;});return modal;}
function openModal(title,body){const modal=ensureModal();modal.querySelector("[data-demo-modal-title]").textContent=title;modal.querySelector("[data-demo-modal-body]").innerHTML=body;modal.hidden=false;}
function tableFromRows(rows){if(!rows||!rows.length)return'<div class="ucc-live-empty"><strong>No matching records</strong><span>The source is readable but no records matched the current filter.</span></div>';const columns=Array.from(new Set(rows.flatMap(row=>Object.keys(row))));return`<div class="table-wrap"><table><thead><tr>${columns.map(col=>`<th>${esc(col)}</th>`).join("")}</tr></thead><tbody>${rows.map(row=>`<tr>${columns.map(col=>`<td>${esc(row[col])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;}
async function openMetricRecords(config,dashboard,metric,title){
if(!metric){openModal("Live records","No available metric is mapped to this result.");return;}
openModal("Loading live records",`<div class="ucc-demo-modal-note">${esc(title||metric.label)}</div>`);
try{
const response=await callApi(config,dashboard,"drilldown",{metric_id:metric.id,page:1,page_size:100});
openModal(title||metric.label,`<div class="ucc-demo-modal-note"><strong>${esc(response.drilldown?.total||0)} matching record(s)</strong><br>${esc(response.drilldown?.doctype||metric.doctype||"")}</div>${tableFromRows(response.drilldown?.rows||[])}`);
}catch(error){openModal("Drill-down unavailable",esc(error.message||error));}
}
function showDiagnostics(config,dashboard){const state=dashboardState(dashboard),result=state.result,logs=state.logs;openModal(`Criterion ${config.number} diagnostics`,`<div class="table-wrap"><table><thead><tr><th>Time</th><th>Level</th><th>Event</th><th>Detail</th></tr></thead><tbody>${logs.map(row=>`<tr><td>${esc(row.time)}</td><td>${statusBadge(row.level)}</td><td>${esc(row.event)}</td><td>${esc(row.detail)}</td></tr>`).join("")||'<tr><td colspan="4">No diagnostic events.</td></tr>'}</tbody></table></div><div class="ucc-demo-modal-note">API: ${esc(config.apiMethod)} · Section: ${esc(result?.meta?.subcriterion||apiSection(config,dashboard,activeSection(dashboard)))}</div>`);}
async function handleAction(dashboard,action){const config=CONFIG[dashboard.dataset.demoDashboard],state=dashboardState(dashboard),result=state.result;if(action==="refresh")await loadLive(dashboard,true);if(action==="export-qa"){const rows=[["Section","Question","Answer","Source","Status"],...allQaRows(result)];download(`criterion_${config.number}_live_qa.csv`,rows.map(row=>row.map(csvCell).join(",")).join("\n"));}if(action==="export-exceptions"){const rows=[["Metric","Label","Value","Status","Source"],...allExceptionRows(result)];download(`criterion_${config.number}_live_exceptions.csv`,rows.map(row=>row.map(csvCell).join(",")).join("\n"));}if(action==="export-table"){const rows=[["Metric","Value","Unit","Status","Source"],...(result?.metrics||[]).map(item=>[item.label,item.value,item.unit,item.status,item.doctype||item.source])];download(`criterion_${config.number}_${result?.meta?.subcriterion||"section"}_live_metrics.csv`,rows.map(row=>row.map(csvCell).join(",")).join("\n"));}if(action==="copy-link"){const url=new URL(location.href);url.searchParams.set("dashboard",dashboard.dataset.demoDashboard);url.searchParams.set("live_tab",activeSection(dashboard));navigator.clipboard?.writeText(url.toString()).catch(()=>{});}if(action==="diagnostics")showDiagnostics(config,dashboard);}
// ---- Dashboard visibility (interface composition only) ---------------------
// Decides which workspaces and criteria are BUILT. It never changes what data
// a user may read: every data call keeps its own Frappe permission check, and a
// hidden tab neither grants nor removes access to anything.
const ACCESS_WORKSPACE_PANELS={analytics:"analytics",explore:"explore",ask:"ask"};
function fetchDashboardAccess(){
return new Promise(function(resolve){
if(!(window.frappe&&frappe.call)){resolve(null);return;}
let settled=false;
const done=function(value){if(!settled){settled=true;resolve(value);}};
// Fail open on anything at all - a slow or broken lookup must never lock a
// user out of a dashboard they are entitled to use.
window.setTimeout(function(){done(null);},8000);
try{
frappe.call({
method:"ucc_intelligence.api.get_dashboard_access",
args:{},
callback:function(response){
const message=response&&response.message;
done(message&&message.criteria?message:null);
},
error:function(){done(null);}
});
}catch(error){done(null);}
});
}
function applyDashboardAccess(access){
if(!access||!access.criteria)return{applied:"fail_open",hiddenCriteria:[],hiddenWorkspaces:[]};
const hiddenCriteria=[],hiddenWorkspaces=[];
// Criteria: drop the mount point and the CONFIG entry BEFORE mounting, so the
// tab bar and panels for a hidden criterion are never constructed at all.
Object.keys(CONFIG).forEach(function(criterionId){
if(access.criteria[criterionId]===false){
hiddenCriteria.push(criterionId);
const node=platform.querySelector('[data-dashboard-panel="'+CSS.escape(criterionId)+'"]');
if(node&&node.parentNode)node.parentNode.removeChild(node);
delete CONFIG[criterionId];
}
});
// The dashboard picker options are static markup, so prune them separately and
// re-point the selection if the current choice has just been removed.
const select=platform.querySelector("#uccDashboardSelect");
if(select){
Array.from(select.options).forEach(function(option){
if(option.value&&access.criteria[option.value]===false)option.remove();
});
if(select.options.length&&!CONFIG[select.value])select.value=select.options[0].value;
}
// Workspaces: remove the switcher button and its panel together.
const workspaces=(access&&access.workspaces)||{};
Object.keys(ACCESS_WORKSPACE_PANELS).forEach(function(key){
if(workspaces[key]===false){
hiddenWorkspaces.push(key);
const button=platform.querySelector('[data-ucc-workspace="'+CSS.escape(key)+'"]');
if(button&&button.parentNode)button.parentNode.removeChild(button);
const panel=platform.querySelector('[data-ucc-workspace-panel="'+CSS.escape(key)+'"]');
if(panel&&panel.parentNode)panel.parentNode.removeChild(panel);
}
});
return{applied:access.applied||"role_configuration",hiddenCriteria:hiddenCriteria,hiddenWorkspaces:hiddenWorkspaces};
}
function bootstrapDashboards(){
mountUnifiedDashboards();
// No chart manifest to load: charts are not declared by this app any more,
// they are picked per tab from Insights and fetched when the tab renders.
injectTabChartStyles();

platform.querySelectorAll("[data-demo-dashboard]").forEach(function(dashboard){const config=CONFIG[dashboard.dataset.demoDashboard];if(!config)return;ensureTabChartArea(dashboard,config,"overview");syncTabChartVisibility(dashboard,"overview");dashboard.dataset.liveApi="1";dashboard.querySelectorAll("[data-demo-tab]").forEach(button=>button.addEventListener("click",()=>showTab(dashboard,button.dataset.demoTab)));dashboard.addEventListener("ucc:live-tool-action",function(event){const action=event.detail&&event.detail.action;const mapped=action==="export-current"?"export-table":action;if(mapped)handleAction(dashboard,mapped);});dashboard.addEventListener("click",function(event){
const sourceButton=event.target.closest("[data-live-source-doctype]");
if(sourceButton){
event.preventDefault();
event.stopPropagation();
const doctype=sourceButton.dataset.liveSourceDoctype;
if(doctype)window.open(doctypeListRoute(doctype),"_blank","noopener");
return;
}
const questionButton=event.target.closest("[data-live-qa-records]");
if(questionButton){
event.preventDefault();
event.stopPropagation();
const metric=metricById(dashboardState(dashboard).result,questionButton.dataset.liveQaRecords);
openMetricRecords(config,dashboard,metric,questionButton.dataset.liveQaTitle||metric?.label||"Matching records");
return;
}
const modeToggle=event.target.closest("[data-toggle-edit]");
if(modeToggle){
event.preventDefault();event.stopPropagation();
const key=dashboard.dataset.demoDashboard;
tabEditModes[key]=!tabEditModes[key];
const tab=modeToggle.dataset.toggleEdit;
renderTabCharts(dashboard,config,tab);
renderTabActions(dashboard,tab);
renderTabIntro(dashboard,config,tab);
renderQa(dashboard,dashboardState(dashboard).result,tab);
return;
}
const historyButton=event.target.closest("[data-tab-history]");
if(historyButton){
event.preventDefault();event.stopPropagation();
openTabHistory(dashboard,historyButton.dataset.tabHistory);return;
}
const exportButton=event.target.closest("[data-export-pdf]");
if(exportButton){
event.preventDefault();event.stopPropagation();
exportTabPdf(dashboard,config,exportButton.dataset.exportPdf);return;
}
const addChart=event.target.closest("[data-add-chart]");
if(addChart){event.preventDefault();event.stopPropagation();openChartPicker(dashboard,config,addChart.dataset.addChart);return;}
const removeChart=event.target.closest("[data-remove-chart]");
if(removeChart){event.preventDefault();event.stopPropagation();removeTabChart(dashboard,config,activeSection(dashboard),removeChart.dataset.removeChart);return;}
// --- Diagram/Table toggle and drill-down (#8) --------------------------
const viewButton=event.target.closest("[data-demo-view]");
if(viewButton){
event.preventDefault();event.stopPropagation();
const card=viewButton.closest("[data-embedded-chart]");
if(card){setChartView(card,viewButton.dataset.demoView);if(viewButton.dataset.demoView==="table")renderChartTable(card,null);}
return;
}
const segment=event.target.closest("[data-chart-segment]");
if(segment){
event.preventDefault();event.stopPropagation();
const card=segment.closest("[data-embedded-chart]");
if(card)selectChartSegment(card,segment.dataset.chartSegment);
return;
}
const clearSegment=event.target.closest("[data-clear-segment]");
if(clearSegment){
event.preventDefault();event.stopPropagation();
const card=clearSegment.closest("[data-embedded-chart]");
if(card)renderChartTable(card,null);
return;
}
// #4: a card's own title. Insights names a query for whoever built it; a
// criterion tab is read by an auditor, and "Chart 1" tells them nothing.
const retitle=event.target.closest("[data-retitle-chart]");
if(retitle){
event.preventDefault();event.stopPropagation();
const card=retitle.closest("[data-embedded-chart]");
const heading=card&&card.querySelector(".ucc-embedded-chart-head h3");
const next=window.prompt(
"Title for this card. Leave blank to use the chart's own title from Insights.",
heading?heading.textContent:"");
if(next===null)return;
const tab=activeSection(dashboard);
if(!(window.frappe&&frappe.call))return;
frappe.call({method:"ucc_intelligence.api.set_tab_chart_title",
args:{criterion:dashboard.dataset.demoDashboard,tab:tab,
chart:retitle.dataset.retitleChart,title:next},
callback(response){applyTabConfig(dashboard,config,tab,(response&&response.message)||{});},
error(error){openModal("Could not rename the card",tabChartNotice(apiErrorMessage(error)));}});
return;
}

const drillRecords=event.target.closest("[data-drill-records]");
if(drillRecords){
event.preventDefault();event.stopPropagation();
const card=drillRecords.closest("[data-embedded-chart]");
if(card)openDrilldown(card,drillRecords.dataset.drillRecords,1);
return;
}
// The paging buttons live in the modal, outside the card, so the card and
// segment that opened it are remembered rather than looked up from the DOM.
const drillPage=event.target.closest("[data-drill-page]");
if(drillPage&&activeDrill){
event.preventDefault();event.stopPropagation();
openDrilldown(activeDrill.card,activeDrill.segment,Number(drillPage.dataset.drillPage)||1);
return;
}
// --- the tab intro (#4) ------------------------------------------------
const editIntro=event.target.closest("[data-edit-intro]");
if(editIntro){event.preventDefault();event.stopPropagation();openIntroEditor(dashboard,config,editIntro.dataset.editIntro);return;}
const saveIntro=event.target.closest("[data-save-intro]");
if(saveIntro){event.preventDefault();event.stopPropagation();saveTabIntro(dashboard,config,saveIntro.dataset.saveIntro);return;}
const cancelIntro=event.target.closest("[data-cancel-intro]");
if(cancelIntro){
event.preventDefault();event.stopPropagation();
const panelKey=(config.panelMap&&config.panelMap[cancelIntro.dataset.cancelIntro])||cancelIntro.dataset.cancelIntro;
const mount=dashboard.querySelector(`[data-tab-intro="${CSS.escape(panelKey)}"]`);
if(mount)mount.dataset.editing="";
renderTabIntro(dashboard,config,cancelIntro.dataset.cancelIntro);
return;
}
// --- management questions (#6) -----------------------------------------
const hideQuestion=event.target.closest("[data-hide-question]");
if(hideQuestion){
event.preventDefault();event.stopPropagation();
setTabQuestion(dashboard,config,activeSection(dashboard),hideQuestion.dataset.hideQuestion,false);
return;
}
const addQuestion=event.target.closest("[data-add-question]");
if(addQuestion){event.preventDefault();event.stopPropagation();openQuestionPicker(dashboard,config,activeSection(dashboard));return;}
const actionButton=event.target.closest("[data-demo-action]");
if(actionButton){event.preventDefault();event.stopPropagation();handleAction(dashboard,actionButton.dataset.demoAction);return;}
});dashboard.dataset.demoActiveTab="overview";dashboard.querySelectorAll("[data-demo-panel]").forEach(panel=>panel.classList.toggle("hidden",panel.dataset.demoPanel!=="overview"));if(!dashboard.classList.contains("ucc-hidden"))loadLive(dashboard);});platform.addEventListener("ucc:dashboard-change",event=>{const id=event.detail&&event.detail.dashboard;if(!id)return;const dashboard=platform.querySelector(`[data-demo-dashboard="${CSS.escape(id)}"]`);if(dashboard)loadLive(dashboard);});
}
fetchDashboardAccess().then(function(access){
const outcome=applyDashboardAccess(access);
platform.dataset.uccAccessApplied=outcome.applied;
if(outcome.hiddenCriteria.length)platform.dataset.uccHiddenCriteria=outcome.hiddenCriteria.join(",");
if(outcome.hiddenWorkspaces.length)platform.dataset.uccHiddenWorkspaces=outcome.hiddenWorkspaces.join(",");
bootstrapDashboards();
});

platform.addEventListener("click",function(event){
const sourceButton=event.target.closest("[data-live-source-doctype]");
if(!sourceButton||sourceButton.closest("[data-demo-dashboard]"))return;
event.preventDefault();
const doctype=sourceButton.dataset.liveSourceDoctype;
if(doctype)window.open(doctypeListRoute(doctype),"_blank","noopener");
});
window.UCCLiveAnalytics=Object.freeze({config:CONFIG,registerResponseAdapter:registerResponseAdapter,refresh:function(criterion){const dashboard=platform.querySelector(`[data-demo-dashboard="${CSS.escape(criterion)}"]`);if(dashboard)return loadLive(dashboard,true);},showTab:function(criterion,tab){const dashboard=platform.querySelector(`[data-demo-dashboard="${CSS.escape(criterion)}"]`);if(dashboard)showTab(dashboard,tab);}});
}

function initDiagramExplorer(platformRoot) {
	if (!platformRoot || platformRoot.dataset.exploreReady === "1") return;
	platformRoot.dataset.exploreReady = "1";

	const exploreRoot = platformRoot.querySelector("[data-ucc-explore]");
	if (!exploreRoot) return;

	const listNode = exploreRoot.querySelector("[data-ucc-explore-list]");
	const searchNode = exploreRoot.querySelector("[data-ucc-explore-search]");
	const sectionNode = exploreRoot.querySelector("[data-ucc-explore-section]");
	const typeNode = exploreRoot.querySelector("[data-ucc-explore-type]");
	const resultNode = exploreRoot.querySelector("[data-ucc-explore-result-count]");
	const clearButton = exploreRoot.querySelector("[data-ucc-explore-clear]");
	const dashboardSelect = platformRoot.querySelector("#uccDashboardSelect");
	const workspaceButtons = Array.from(platformRoot.querySelectorAll("[data-ucc-workspace]"));

	const parentTabMap = Object.freeze({});

	let entries = [];
	let lastExploreScroll = 0;
	let highlightedCard = null;

	const returnButton = document.createElement("button");
	returnButton.type = "button";
	returnButton.className = "ucc-explore-return";
	returnButton.textContent = "← Back to Explore";
	returnButton.hidden = true;
	platformRoot.appendChild(returnButton);

	function text(value) {
	return String(value == null ? "" : value).replace(/\s+/g, " ").trim();
	}

	function titleFrom(node) {
	const card = node.closest("article, .panel");
	const heading = card ? card.querySelector("h2,h3") : null;
	return text(heading ? heading.textContent : node.dataset.chart || node.dataset.c4Visual || "Untitled visual");
	}

	function sectionLabel(entry) {
	if (entry.kind === "demo") {
	const button = platformRoot.querySelector(`[data-dashboard-panel="${CSS.escape(entry.dashboard)}"] [data-demo-tab="${CSS.escape(entry.panel || "overview")}"]`);
	return text(button ? button.textContent : entry.panel || "Live foundation");
	}
	const button = platformRoot.querySelector(`[data-tab="${CSS.escape(parentTabMap[entry.panel] || entry.panel || "overview")}"]`);
	const local = entry.panel && entry.panel !== (parentTabMap[entry.panel] || entry.panel)
	? platformRoot.querySelector(`[data-section="${CSS.escape(entry.panel)}"]`)
	: null;
	return text(local ? local.textContent : button ? button.textContent : entry.panel || "Criterion 5");
	}

	function inferType(id, title) {
	const value = `${id} ${title}`.toLowerCase();
	const rules = [
	["network", ["network"]],
	["timeline", ["timeline", "trend", "aging", "recency"]],
	["funnel", ["funnel", "flow", "lifecycle", "cycle"]],
	["donut", ["donut", "ring", "orbit"]],
	["heatmap", ["heatmap", "matrix"]],
	["bubble", ["bubble", "constellation"]],
	["radial", ["radial", "radar"]],
	["decision", ["decision"]],
	["ladder", ["ladder"]],
	["reconciliation", ["reconciliation"]]
	];
	for (const [type, terms] of rules) {
	if (terms.some(term => value.includes(term))) return type;
	}
	return "chart";
	}

	function sourceHint(node) {
	const card = node.closest("article, .panel");
	if (!card) return "Configured live source";
	const sourceLink = card.querySelector(".source-doctype-link,.source-link,[data-source]");
	return text(sourceLink ? sourceLink.textContent : "Configured live source");
	}

	function createEntry(node, dashboard, kind) {
	const id = kind === "c4" ? node.dataset.c4Visual : kind === "demo" ? node.dataset.demoChart : node.dataset.chart;
	if (!id) return null;
	const panelNode = kind === "demo" ? node.closest("[data-demo-panel]") : node.closest("[data-panel]");
	const title = kind === "demo" ? text(node.dataset.demoChartTitle || titleFrom(node)) : titleFrom(node);
	const entry = {
	key: `${dashboard}:${kind}:${id}`,id,kind,dashboard,node,title,
	panel: kind === "demo" ? panelNode?.dataset.demoPanel || "overview" : panelNode?.dataset.panel || "overview",
	c511Panel: "",
	localPanel: node.closest("[data-local-panel]")?.dataset.localPanel || "",
	type: kind === "demo" ? node.dataset.demoChartType || "live-foundation" : inferType(id, title),
	source: kind === "demo" ? "Permission-aware live API foundation" : sourceHint(node),
	description: ""
	};
	entry.section = sectionLabel(entry);
	return entry;
	}

	function buildRegistry() {
	const registry = new Map();

	Object.entries(window.UCCLiveVisualDefinitions || {}).forEach(([dashboard, sections]) => {
	Object.entries(sections || {}).forEach(([panel, definitions]) => {
	(definitions || []).forEach(definition => {
	if (definition.enabled === false) return;
	const entry = {
	key: `${dashboard}:demo:${definition.id}`,
	id: definition.id,
	kind: "demo",
	dashboard,
	node: platformRoot.querySelector(`[data-demo-chart="${CSS.escape(definition.id)}"]`),
	title: text(definition.title),
	panel,
	c511Panel: "",
	localPanel: "",
	type: definition.type || inferType(definition.id, definition.title),
	source: "Permission-aware live API metrics",
	description: text(definition.description || "")
	};
	entry.section = sectionLabel(entry);
	if (!registry.has(entry.key)) registry.set(entry.key, entry);
	});
	});
	});

	entries = Array.from(registry.values()).sort((a, b) =>
	a.section.localeCompare(b.section) || a.title.localeCompare(b.title)
	);

	["criterion_1", "criterion_2", "criterion_3", "criterion_4", "criterion_5", "criterion_6", "criterion_7"].forEach(dashboard => {
	const count = exploreRoot.querySelector(`[data-ucc-explore-count="${dashboard}"]`);
	if (count) count.textContent = String(entries.filter(entry => entry.dashboard === dashboard).length);
	});
	}

	function currentDashboard() {
	return dashboardSelect ? dashboardSelect.value : "criterion_5";
	}

	function fillFilters() {
	const dashboard = currentDashboard();
	const dashboardEntries = entries.filter(entry => entry.dashboard === dashboard);
	const previousSection = sectionNode.value;
	const previousType = typeNode.value;
	const sections = Array.from(new Set(dashboardEntries.map(entry => entry.section))).sort();
	const types = Array.from(new Set(dashboardEntries.map(entry => entry.type))).sort();

	sectionNode.innerHTML = '<option value="">All sections</option>' +
	sections.map(value => `<option value="${value.replace(/"/g, "&quot;")}">${value}</option>`).join("");
	typeNode.innerHTML = '<option value="">All visual types</option>' +
	types.map(value => `<option value="${value.replace(/"/g, "&quot;")}">${value}</option>`).join("");

	if (sections.includes(previousSection)) sectionNode.value = previousSection;
	if (types.includes(previousType)) typeNode.value = previousType;
	}

	function filteredEntries() {
	const dashboard = currentDashboard();
	const query = text(searchNode.value).toLowerCase();
	return entries.filter(entry =>
	entry.dashboard === dashboard &&
	(!query || `${entry.title} ${entry.section} ${entry.type} ${entry.source}`.toLowerCase().includes(query)) &&
	(!sectionNode.value || entry.section === sectionNode.value) &&
	(!typeNode.value || entry.type === typeNode.value)
	);
	}

	function renderList() {
	const dashboard = currentDashboard();
	const liveDashboard = dashboard === "criterion_4" || dashboard === "criterion_5";
	const rows = filteredEntries();
	resultNode.textContent = `${rows.length} live diagram${rows.length === 1 ? "" : "s"}`;

	const grouped = rows.reduce((result, entry) => {
	(result[entry.section] ||= []).push(entry);
	return result;
	}, {});

	listNode.innerHTML = Object.entries(grouped).map(([section, sectionEntries]) => `
	<section class="ucc-explore-group">
	<h2>${section}</h2>
	${sectionEntries.map(entry => `
	<button type="button" class="ucc-explore-item" data-ucc-explore-entry="${entry.key}">
	<span>
	<strong>${entry.title}</strong>
	${entry.description ? `<small>${entry.description}</small>` : ""}
	<small>${entry.source}</small>
	</span>
	<em>${entry.type}</em>
	</button>
	`).join("")}
	</section>
	`).join("") || '<div class="ucc-explore-empty">No diagrams match the current search and filters.</div>';
	}

	function chooseDashboard(dashboard) {
	if (!dashboardSelect) return;
	dashboardSelect.value = dashboard;
	dashboardSelect.dispatchEvent(new Event("change", { bubbles: true }));
	}

	function resolveEntryNode(entry) {
	if (entry.node && entry.node.isConnected) return entry.node;
	if (entry.kind === "demo") {
	entry.node = platformRoot.querySelector(`[data-demo-chart="${CSS.escape(entry.id)}"]`);
	}
	return entry.node || null;
	}

	function revealNestedViews(entry) {
	const node = resolveEntryNode(entry);
	if (entry.kind === "demo") {
	window.UCCLiveAnalytics?.showTab(entry.dashboard, entry.panel || "overview");
	node?.closest("[data-demo-card]")?.querySelector('[data-demo-view="diagram"]')?.click();
	return;
	}
	if (entry.localPanel) {
	const panel = node?.closest("[data-panel]");
	const button = panel ? panel.querySelector(
	`[data-local-tab="${CSS.escape(entry.localPanel)}"]`
	) : null;
	if (button) button.click();
	}
	const card = node?.closest("article, .panel");
	if (card) {
	const diagramButton = card.querySelector('[data-card-view="diagram"]');
	if (diagramButton) diagramButton.click();
	}
	}

	function highlightEntry(entry, attempt = 0) {
	const node = resolveEntryNode(entry);
	if (!node) {
	if (attempt < 24) setTimeout(() => highlightEntry(entry, attempt + 1), 250);
	else if (window.frappe && frappe.show_alert) frappe.show_alert({ message: "The selected visual could not be mounted. Open Source Mapping Report for details.", indicator: "orange" });
	return;
	}
	if (highlightedCard) highlightedCard.classList.remove("ucc-explore-highlight");
	highlightedCard = node.closest("article, .panel") || node;
	highlightedCard.classList.add("ucc-explore-highlight");
	highlightedCard.scrollIntoView({ behavior: "smooth", block: "center" });
	setTimeout(() => highlightedCard?.classList.remove("ucc-explore-highlight"), 4200);
	returnButton.hidden = false;
	}

	function openLiveEntry(entry) {
	lastExploreScroll = Math.max(
	Number(window.scrollY || 0),
	Number(document.documentElement?.scrollTop || 0)
	);
	platformRoot.querySelector('[data-ucc-workspace="analytics"]')?.click();
	chooseDashboard(entry.dashboard);

	const finish = () => {
	revealNestedViews(entry);
	setTimeout(() => {
	revealNestedViews(entry);
	highlightEntry(entry);
	window.dispatchEvent(new Event("resize"));
	}, 220);
	};

	if (entry.kind === "demo") {
	window.UCCLiveAnalytics?.showTab(entry.dashboard, entry.panel || "overview");
	setTimeout(finish, 120);
	} else {
	setTimeout(finish, 120);
	}
	}

	listNode.addEventListener("click", event => {
	const switchButton = event.target.closest("[data-ucc-explore-switch]");
	if (switchButton) {
	chooseDashboard(switchButton.dataset.uccExploreSwitch);
	fillFilters();
	renderList();
	return;
	}
	const button = event.target.closest("[data-ucc-explore-entry]");
	if (!button) return;
	const entry = entries.find(item => item.key === button.dataset.uccExploreEntry);
	if (entry) openLiveEntry(entry);
	});

	function resetFilters() {
	searchNode.value = "";
	sectionNode.value = "";
	typeNode.value = "";
	renderList();
	}

	searchNode.addEventListener("input", renderList);
	sectionNode.addEventListener("change", renderList);
	typeNode.addEventListener("change", renderList);
	["pointerdown", "mousedown", "click", "keydown", "keyup", "keypress", "focus", "focusin"].forEach(function (eventName) {
	searchNode.addEventListener(eventName, function (event) {
	event.stopPropagation();
	if (typeof event.stopImmediatePropagation === "function") event.stopImmediatePropagation();
	});
	});
	searchNode.addEventListener("keydown", function (event) {
	if (event.key === "Escape") {
	event.preventDefault();
	resetFilters();
	searchNode.focus();
	}
	});
	clearButton.addEventListener("pointerdown", function (event) {
	event.stopPropagation();
	});
	clearButton.addEventListener("click", function (event) {
	event.preventDefault();
	event.stopPropagation();
	resetFilters();
	searchNode.focus();
	});

	dashboardSelect?.addEventListener("change", () => {
	fillFilters();
	renderList();
	});

	workspaceButtons.forEach(button => {
	button.addEventListener("click", () => {
	if (button.dataset.uccWorkspace === "explore") {
	returnButton.hidden = true;
	setTimeout(() => window.scrollTo({ top: lastExploreScroll, behavior: "smooth" }), 0);
	}
	});
	});

	returnButton.addEventListener("click", () => {
	platformRoot.querySelector('[data-ucc-workspace="explore"]')?.click();
	});

	buildRegistry();
	fillFilters();
	renderList();

	window.UCCExplore = Object.freeze({
	entries: () => entries.slice(),
	openEntry: keyOrEntry => {
	const entry = typeof keyOrEntry === "string" ? entries.find(item => item.key === keyOrEntry) : keyOrEntry;
	if (entry) openLiveEntry(entry);
	},
	openNavigator: dashboard => {
	if (dashboard) chooseDashboard(dashboard);
	platformRoot.querySelector('[data-ucc-workspace="explore"]')?.click();
	setTimeout(() => searchNode?.focus(), 80);
	},
	rebuild: () => {
	buildRegistry();
	fillFilters();
	renderList();
	}
	});
}

// ---------------------------------------------------------------------------
// ASK UCC -- the decision-support surface for ucc_intelligence.api.ask_ucc.
//
// Lives here, inside the platform shell's `ask` workspace panel, NOT as a
// separate Frappe Page. The original design (custom-html-block's
// data-ucc-workspace pattern) is one page with Analytics / Explore / Ask UCC
// tabs; a standalone /app/ask-ucc route was an architecture mistake and was
// removed rather than left alongside this.
//
// The markup is in SHELL_HTML above. Deliberately NOT the legacy `aja-app`
// Ask panel from custom-html-block/HTML.html line 57 -- that carries the
// browser-held OpenAI API key modal CLAUDE.md §1.1.9 forbids. This surface
// talks to the server-side ai/ layer, which never exposes a key to the browser.
//
// THE ONE RULE THIS LAYOUT EXISTS TO SERVE
// A reader must never have to work out whether what they are looking at came
// out of a record or out of a language model. So the card TYPE is decided
// server-side (`answer_kind` in ask_ucc/contracts.py) and rendered as two
// visibly different things:
//
//   VERIFIED RECORD ANSWER -- green, a value read from the record. No model
//       was called at all; ai/orchestration.py returns before the AI layer for
//       any question with a known route that is not listed as interpretive.
//   AI ANALYSIS -- blue, a model's reading of those same records, with the
//       number of record checks behind it stated in the header.
//
// A third band, amber, is neither: a deterministic field-vs-field check
// (ask_ucc/data_checks.py). It is never phrased as an answer.
//
// Evidence, source records and technical metadata are all present and all
// collapsed. The answer must be understandable without opening any of them --
// which is also why the model name is in "Technical details" and not the
// header, where it used to be.
// ---------------------------------------------------------------------------
const ASK_STYLE_ID = "ucc-ask-style";

// Line icons, inline. No emoji: an emoji renders differently on every OS and
// carries a tone this interface should not have. `aria-hidden` on all of them
// -- every icon here sits beside a text label that carries the meaning, per
// the "colour and icons are never the only indicator" rule.
const ASK_ICON = (function () {
	function svg(body, size) {
		return '<svg class="ucc-ask-icon" aria-hidden="true" focusable="false" width="' + (size || 14)
			+ '" height="' + (size || 14) + '" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
			+ ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + body + "</svg>";
	}
	return {
		shield: svg('<path d="M12 3l7 3v5c0 4.6-3 8.3-7 10-4-1.7-7-5.4-7-10V6z"/><path d="M9 12l2 2 4-4"/>'),
		verified: svg('<circle cx="12" cy="12" r="9"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>'),
		ai: svg('<path d="M12 3l1.9 4.6L18.5 9.5 13.9 11.4 12 16l-1.9-4.6L5.5 9.5l4.6-1.9z"/><path d="M18 15l.9 2.1L21 18l-2.1.9L18 21l-.9-2.1L15 18l2.1-.9z"/>'),
		warning: svg('<path d="M12 4l9 16H3z"/><path d="M12 10v4"/><path d="M12 17.5v.01"/>'),
		send: svg('<path d="M4 20l17-8L4 4l3 8z"/><path d="M7 12h14"/>'),
		trash: svg('<path d="M4 7h16"/><path d="M9 7V5h6v2"/><path d="M6 7l1 13h10l1-13"/>'),
		external: svg('<path d="M14 5h5v5"/><path d="M19 5l-8 8"/><path d="M18 14v5H5V6h5"/>', 13),
		person: svg('<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>', 13),
		route: svg('<path d="M5 5h9a4 4 0 010 8H8a4 4 0 000 8h11"/>', 13),
		chart: svg('<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M22 20H2"/>', 13),
		arrow: svg('<path d="M5 12h13"/><path d="M13 6l6 6-6 6"/>', 13),
		clock: svg('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', 13),
	};
}());

// Institutional palette, stated once. Colour never carries meaning alone here
// -- every state below pairs it with a text label and an icon.
const ASK_STYLE_TEXT = `
.ucc-ask{--ask-navy:#172554;--ask-blue:#2563EB;--ask-green:#15803D;--ask-green-bg:#F0FDF4;
 --ask-ai-bg:#F3F7FF;--ask-amber:#B45309;--ask-amber-bg:#FFFBEB;--ask-red:#B91C1C;
 --ask-page:#F6F8FC;--ask-text:#1E293B;--ask-muted:#64748B;--ask-border:#D8E0EC;
 font-size:14px;color:var(--ask-text)}
.ucc-ask-layout{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:16px;align-items:start;padding:16px}
.ucc-ask-main{display:flex;flex-direction:column;gap:16px;min-width:0}

/* header ------------------------------------------------------------------ */
.ucc-ask-head{display:flex;gap:16px;align-items:flex-start;justify-content:space-between;flex-wrap:wrap}
.ucc-ask-head h2{margin:0;font-size:19px;font-weight:600;color:var(--ask-navy)}
.ucc-ask-head p{margin:4px 0 0;font-size:13px;color:var(--ask-muted)}
.ucc-ask-assurance{display:flex;gap:8px;align-items:flex-start;max-width:360px;padding:8px 12px;
 background:#F3F7FF;border:1px solid var(--ask-border);border-radius:8px;font-size:11px;line-height:1.5;color:#334155}
.ucc-ask-assurance .ucc-ask-icon{flex:none;margin-top:1px;color:var(--ask-blue)}

/* controls ---------------------------------------------------------------- */
.ucc-ask-controls{display:flex;flex-direction:column;gap:12px;padding:16px;background:#fff;
 border:1px solid var(--ask-border);border-radius:12px}
.ucc-ask-row{display:grid;grid-template-columns:minmax(150px,200px) minmax(0,1fr) auto;gap:12px;align-items:end}
.ucc-ask-field{display:flex;flex-direction:column;gap:4px;position:relative;min-width:0}
.ucc-ask-field-grow{flex:1}
.ucc-ask-field>span{font-size:11px;font-weight:600;color:var(--ask-muted)}
/* box-sizing is stated because width:100% plus 10px padding was pushing the
   record input 10px into the status badge beside it -- the host stylesheet
   does not set it for these elements. */
.ucc-ask-field select,.ucc-ask-field input,.ucc-ask-field textarea{box-sizing:border-box;padding:9px 10px;
 background:#fff;border:1px solid var(--ask-border);border-radius:8px;font:inherit;font-size:13px;
 width:100%;color:var(--ask-text)}
.ucc-ask-field textarea{resize:vertical;min-height:60px;line-height:1.5}
.ucc-ask select:focus-visible,.ucc-ask input:focus-visible,.ucc-ask textarea:focus-visible,
.ucc-ask button:focus-visible,.ucc-ask a:focus-visible,.ucc-ask summary:focus-visible{
 outline:2px solid var(--ask-blue);outline-offset:2px}
.ucc-ask-record-status{display:inline-flex;align-items:center;gap:6px;margin:0;padding:8px 10px;
 border-radius:8px;font-size:12px;font-weight:600;border:1px solid var(--ask-border);
 background:#F8FAFC;color:var(--ask-muted);min-height:38px}
.ucc-ask-record-status::before{content:"";width:7px;height:7px;border-radius:50%;background:#94A3B8;flex:none}
.ucc-ask-record-status[data-state="active"]{background:var(--ask-green-bg);border-color:#BBF7D0;color:var(--ask-green)}
.ucc-ask-record-status[data-state="active"]::before{background:var(--ask-green)}
.ucc-ask-actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.ucc-ask-submit{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 20px;
 background:var(--ask-navy);color:#fff;border:1px solid var(--ask-navy);border-radius:8px;
 font-size:14px;font-weight:600;cursor:pointer}
.ucc-ask-submit:hover{background:#1E3A8A}
.ucc-ask-submit[disabled]{opacity:.55;cursor:default}
.ucc-ask-clear{display:inline-flex;align-items:center;gap:6px;min-height:40px;padding:0 14px;
 background:#fff;color:var(--ask-red);border:1px solid var(--ask-border);border-radius:8px;
 font-size:13px;font-weight:500;cursor:pointer}
.ucc-ask-clear:hover{background:#FEF2F2;border-color:#FECACA}
.ucc-ask-suggestions{position:absolute;top:100%;left:0;right:0;z-index:20;margin-top:4px;background:#fff;
 border:1px solid var(--ask-border);border-radius:8px;max-height:240px;overflow:auto;box-shadow:0 4px 12px rgba(15,23,42,.08)}
.ucc-ask-suggestion{padding:8px 10px;cursor:pointer;font-size:13px;display:flex;flex-direction:column;gap:1px}
.ucc-ask-suggestion-id{font-size:11px;color:var(--ask-muted)}
.ucc-ask-suggestion:hover,.ucc-ask-suggestion.is-active{background:#F1F5F9}

/* category tabs vs FAQ chips: two rows, two jobs, two visual weights ------- */
.ucc-ask-categories{display:flex;flex-wrap:wrap;gap:4px;border-bottom:1px solid var(--ask-border)}
.ucc-ask-category{min-height:40px;padding:0 12px;border:0;border-bottom:2px solid transparent;
 background:transparent;font-size:13px;font-weight:500;color:var(--ask-muted);cursor:pointer}
.ucc-ask-category:hover{color:var(--ask-navy)}
.ucc-ask-category.is-active{color:var(--ask-navy);font-weight:600;border-bottom-color:var(--ask-navy)}
.ucc-ask-faq-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:12px 0 8px}
.ucc-ask-faq-head h3{margin:0;font-size:13px;font-weight:600;color:var(--ask-text)}
.ucc-ask-faq-head p{margin:0;font-size:11px;color:var(--ask-muted)}
.ucc-ask-questions{display:flex;flex-wrap:wrap;gap:8px}
.ucc-ask-question{display:inline-flex;align-items:center;gap:8px;min-height:40px;padding:0 12px;
 border:1px solid var(--ask-border);border-radius:8px;background:#fff;font-size:13px;
 color:#334155;cursor:pointer;text-align:left}
.ucc-ask-question:hover{background:#F8FAFC;border-color:#94A3B8}
.ucc-ask-question::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--ask-green);flex:none}
/* The settings gear is a SHELL control, but its rules have always lived in
   this stylesheet because injectAskStyles() is the only style injection that
   runs on boot. Left where they are deliberately: moving them would mean
   touching the shell, which this round must not do. */
.ucc-shell-settings-link{margin-left:18px;padding:5px 9px;font-size:19px;line-height:1;background:transparent;border:1px solid var(--ask-border);border-radius:6px;opacity:.7;cursor:pointer}
.ucc-shell-settings-link:hover{opacity:1;background:#F1F5F9}
.ucc-ask-status{font-size:13px;color:var(--ask-muted)}
.ucc-ask-status[data-tone="error"]{color:var(--ask-red)}

/* conversation ------------------------------------------------------------ */
.ucc-ask-thread{display:flex;flex-direction:column;gap:24px}
.ucc-ask-turn{display:flex;flex-direction:column;gap:12px}
.ucc-ask-user{display:flex;justify-content:flex-end}
.ucc-ask-user-bubble{max-width:70%;padding:10px 14px;border-radius:12px 12px 4px 12px;
 background:var(--ask-navy);color:#fff;font-size:14px;line-height:1.5}
.ucc-ask-card{border:1px solid var(--ask-border);border-radius:12px;background:#fff;overflow:hidden}
.ucc-ask-card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;
 padding:8px 14px;border-bottom:1px solid var(--ask-border);font-size:11px}
.ucc-ask-card-label{display:inline-flex;align-items:center;gap:7px;font-weight:700;letter-spacing:.05em;text-transform:uppercase}
.ucc-ask-card-meta{color:var(--ask-muted);font-size:11px;text-align:right}
.ucc-ask-card.is-verified .ucc-ask-card-head{background:var(--ask-green-bg);border-bottom-color:#BBF7D0;color:var(--ask-green)}
.ucc-ask-card.is-ai .ucc-ask-card-head{background:var(--ask-ai-bg);border-bottom-color:#C7D9F5;color:var(--ask-blue)}
.ucc-ask-card.is-unavailable .ucc-ask-card-head{background:#F8FAFC;color:var(--ask-muted)}
.ucc-ask-card-body{padding:14px;display:flex;flex-direction:column;gap:12px}
.ucc-ask-answer{margin:0;font-size:15px;line-height:1.55}
.ucc-ask-answer strong{font-weight:600}
.ucc-ask-answer-detail{display:block;margin-top:4px;font-size:13px;color:var(--ask-muted)}
.ucc-ask-answer-text{white-space:pre-wrap;font-size:14px;line-height:1.6;margin:0}

/* fact tiles -------------------------------------------------------------- */
.ucc-ask-tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px}
.ucc-ask-tile{padding:8px 10px;background:#F8FAFC;border:1px solid var(--ask-border);border-radius:6px}
.ucc-ask-tile dt{margin:0;font-size:11px;color:var(--ask-muted)}
.ucc-ask-tile dd{margin:2px 0 0;font-size:14px;font-weight:600;color:var(--ask-text);word-break:break-word}

/* warning ----------------------------------------------------------------- */
.ucc-ask-warning{display:flex;gap:8px;align-items:flex-start;padding:10px 12px;
 background:var(--ask-amber-bg);border:1px solid #FDE68A;border-radius:8px;font-size:13px;
 line-height:1.5;color:var(--ask-amber)}
.ucc-ask-warning .ucc-ask-icon{flex:none;margin-top:2px}
.ucc-ask-warning strong{display:block;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase}

/* card footer: everything collapsed ---------------------------------------- */
.ucc-ask-card-foot{display:flex;flex-wrap:wrap;gap:8px;align-items:flex-start;
 padding:10px 14px;border-top:1px solid var(--ask-border);background:#FCFDFF}
.ucc-ask-collapse{flex:1 1 100%;border:1px solid var(--ask-border);border-radius:8px;background:#fff}
.ucc-ask-collapse>summary{list-style:none;cursor:pointer;padding:8px 12px;min-height:40px;display:flex;
 align-items:center;gap:8px;font-size:12px;font-weight:600;color:#334155}
.ucc-ask-collapse>summary::-webkit-details-marker{display:none}
.ucc-ask-collapse>summary::after{content:"+";margin-left:auto;font-weight:600;color:var(--ask-muted)}
.ucc-ask-collapse[open]>summary::after{content:"\\2212"}
.ucc-ask-collapse-body{padding:0 12px 12px}
.ucc-ask-fact-group{margin-bottom:12px}
.ucc-ask-fact-group:last-child{margin-bottom:0}
.ucc-ask-fact-group>h4{font-size:12px;margin:0 0 6px;color:var(--ask-muted)}
.ucc-ask-fact-table{width:100%;border-collapse:collapse;font-size:12px}
.ucc-ask-fact-table th,.ucc-ask-fact-table td{border:1px solid #E6EBF3;padding:5px 8px;text-align:left;vertical-align:top}
.ucc-ask-fact-table th{width:34%;font-weight:600;color:var(--ask-muted)}
.ucc-ask-source{display:inline-flex;gap:6px;align-items:center;min-height:36px;font-size:12px;padding:0 10px;
 border:1px solid var(--ask-border);border-radius:8px;text-decoration:none;color:var(--ask-blue);background:#fff}
.ucc-ask-source:hover{background:var(--ask-ai-bg);text-decoration:none}

/* suggested next questions ------------------------------------------------- */
.ucc-ask-suggested{padding:12px;border:1px dashed var(--ask-border);border-radius:10px;background:transparent}
.ucc-ask-suggested>h4{margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:.05em;
 text-transform:uppercase;color:var(--ask-muted)}
.ucc-ask-suggested-list{display:flex;flex-wrap:wrap;gap:8px}
.ucc-ask-suggested-item{display:inline-flex;align-items:center;gap:8px;min-height:40px;padding:0 12px;
 border:1px solid var(--ask-border);border-radius:8px;background:#fff;font-size:13px;color:#334155;
 cursor:pointer;text-align:left}
.ucc-ask-suggested-item:hover{background:#F8FAFC;border-color:#94A3B8}

/* record context panel ----------------------------------------------------- */
.ucc-ask-context{position:sticky;top:12px;display:flex;flex-direction:column;gap:12px;min-width:0}
.ucc-ask-context-card{border:1px solid var(--ask-border);border-radius:12px;background:#fff;padding:14px}
.ucc-ask-context-head h3{margin:0;font-size:13px;font-weight:600;color:var(--ask-navy)}
.ucc-ask-context-head p{margin:2px 0 0;font-size:11px;color:var(--ask-muted)}
.ucc-ask-context-identity{display:flex;gap:10px;align-items:center;margin-bottom:10px}
.ucc-ask-avatar{flex:none;width:38px;height:38px;border-radius:50%;background:var(--ask-navy);color:#fff;
 display:grid;place-content:center;font-size:13px;font-weight:600;letter-spacing:.04em}
.ucc-ask-context-name{font-size:13px;font-weight:600;line-height:1.35;word-break:break-word}
.ucc-ask-context-id{font-size:11px;color:var(--ask-muted);word-break:break-all}
.ucc-ask-context-fields{margin:0;font-size:12px}
.ucc-ask-context-field{display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-top:1px solid #EEF2F7}
.ucc-ask-context-field dt{margin:0;color:var(--ask-muted)}
.ucc-ask-context-field dd{margin:0;font-weight:600;text-align:right;word-break:break-word}
.ucc-ask-context-actions{display:flex;flex-direction:column;gap:6px}
.ucc-ask-context-action{display:inline-flex;align-items:center;gap:8px;min-height:40px;padding:0 12px;
 border:1px solid var(--ask-border);border-radius:8px;background:#fff;font-size:12px;color:#334155;
 cursor:pointer;text-align:left;text-decoration:none}
.ucc-ask-context-action:hover{background:#F8FAFC;text-decoration:none;color:#334155}
.ucc-ask-freshness{display:flex;gap:8px;align-items:flex-start;font-size:11px;line-height:1.5;color:var(--ask-muted)}
.ucc-ask-freshness .ucc-ask-icon{flex:none;margin-top:1px}
.ucc-ask-context-empty{font-size:12px;color:var(--ask-muted);line-height:1.5}

/* tablet and mobile -------------------------------------------------------- */
@media(max-width:1100px){
 .ucc-ask-layout{grid-template-columns:minmax(0,1fr) 250px}
}
@media(max-width:860px){
 .ucc-ask-layout{grid-template-columns:minmax(0,1fr);padding:12px}
 .ucc-ask-row{grid-template-columns:minmax(0,1fr)}
 /* The context panel moves under the controls rather than to the bottom of
    the page: on a phone it is the thing you check before you ask. */
 .ucc-ask-context{position:static;order:2}
 .ucc-ask-main{order:1}
 .ucc-ask-assurance{max-width:none}
 .ucc-ask-question,.ucc-ask-suggested-item,.ucc-ask-submit,.ucc-ask-clear{width:100%;justify-content:center}
 .ucc-ask-user-bubble{max-width:88%}
}
`;

function injectAskStyles() {
	if (document.getElementById(ASK_STYLE_ID)) return;
	const style = document.createElement("style");
	style.id = ASK_STYLE_ID;
	style.textContent = ASK_STYLE_TEXT;
	document.head.appendChild(style);
}

function askEsc(value) {
	return window.UCCShared.escapeHtml(value == null ? "" : String(value));
}

function initAskUcc(platformRoot) {
	const root = platformRoot.querySelector("[data-ucc-ask]");
	if (!root || root.dataset.askReady === "1") return;
	root.dataset.askReady = "1";
	injectAskStyles();

	const moduleSelect = root.querySelector("[data-ask-module]");
	const recordInput = root.querySelector("[data-ask-record]");
	const recordStatus = root.querySelector("[data-ask-record-status]");
	const suggestionBox = root.querySelector("[data-ask-suggestions]");
	const questionInput = root.querySelector("[data-ask-question]");
	const submitButton = root.querySelector("[data-ask-submit]");
	const clearButton = root.querySelector("[data-ask-clear]");
	const statusNode = root.querySelector("[data-ask-status]");
	const thread = root.querySelector("[data-ask-thread]");
	const contextPanel = root.querySelector("[data-ask-context]");
	const guidedPanel = root.querySelector("[data-ask-guided]");
	const categoryRow = root.querySelector("[data-ask-categories]");
	const questionRow = root.querySelector("[data-ask-questions]");

	const state = {
		modules: [], busy: false, category: "", selectedLabel: "",
		asked: [], context: null, checkedAt: "",
	};

	// Icon-bearing labels are filled here rather than in SHELL_HTML: the shell
	// is a single escaped string, and inline SVG in it would be unreadable and
	// unreviewable. Text first in every one of them -- the icon decorates.
	const assurance = root.querySelector("[data-ask-assurance]");
	if (assurance) {
		assurance.innerHTML = ASK_ICON.shield
			+ "<span>Answers use records you already have permission to view. "
			+ "Verified facts and AI analysis are labelled separately.</span>";
	}
	submitButton.innerHTML = ASK_ICON.send + "Ask";
	clearButton.innerHTML = ASK_ICON.trash + "Clear chat";

	function setStatus(text, tone) {
		if (!text) {
			statusNode.hidden = true;
			statusNode.textContent = "";
			return;
		}
		statusNode.hidden = false;
		statusNode.textContent = text;
		statusNode.dataset.tone = tone || "info";
	}

	function currentModule() {
		return state.modules.find((m) => m.key === moduleSelect.value) || null;
	}

	// Which modules this user may see comes from the server
	// (get_dashboard_access's ask_ucc_modules), never from a hardcoded list
	// here -- the same interface-composition rule Analytics follows.
	frappe.call({
		method: "ucc_intelligence.api.get_ask_ucc_modules",
		callback(response) {
			const modules = (response && response.message && response.message.modules) || [];
			state.modules = modules;
			if (!modules.length) {
				moduleSelect.innerHTML = "";
				submitButton.disabled = true;
				recordInput.disabled = true;
				questionInput.disabled = true;
				setStatus("No Ask UCC modules are enabled for your account. Ask an administrator if you need access.", "error");
				renderContext();
				return;
			}
			moduleSelect.innerHTML = modules
				.map((m) => `<option value="${askEsc(m.key)}">${askEsc(m.label)}</option>`)
				.join("");
			applyModule();
		},
		error() {
			setStatus("Could not load the available modules.", "error");
		},
	});

	function applyModule() {
		const module = currentModule();
		questionInput.placeholder = module
			? "Ask a question about this " + module.label.toLowerCase()
				+ ", for example, Is this record ready to close?"
			: "Ask a question about the selected record";
		renderGuided();
		renderContext();
	}

	// --- record picker: a search against the module's own DocType, run
	// server-side so the searchable fields come from the module registry
	// and never from the caller.
	let searchTimer = null;
	function hideSuggestions() {
		suggestionBox.hidden = true;
		suggestionBox.innerHTML = "";
	}

	// The legacy picker matched the HUMAN NAME as well as the record id
	// (uniqueStudentsFromRoll in custom-html-block/JAVASCRIPT.js) -- typing
	// "Mei" had to find EDU-APP-2025-00001. An earlier version of this tab
	// searched only `name`, which is the id, so a name search silently
	// matched nothing. This calls a server endpoint that searches the
	// module's own configured fields; the browser never receives a bulk
	// record dump just to power a search box, unlike the legacy version.
	function searchRecords(term) {
		const module = currentModule();
		if (!module || !term) {
			hideSuggestions();
			return;
		}
		frappe.call({
			method: "ucc_intelligence.api.search_ask_ucc_records",
			args: { module: module.key, term: term },
			callback(response) {
				const rows = (response && response.message && response.message.records) || [];
				if (!rows.length) {
					hideSuggestions();
					return;
				}
				suggestionBox.innerHTML = rows
					.map((r) => (
						'<div class="ucc-ask-suggestion" role="option" data-value="' + askEsc(r.id) + '">'
						+ "<strong>" + askEsc(r.label) + "</strong>"
						+ '<span class="ucc-ask-suggestion-id">' + askEsc(r.id) + "</span>"
						+ "</div>"
					))
					.join("");
				suggestionBox.hidden = false;
			},
			error: hideSuggestions,
		});
	}

	// The status badge states plainly whether a record is in scope. Colour is
	// never the signal on its own -- the words change too.
	function setRecordStatus() {
		const record = recordInput.value.trim();
		if (!record) {
			recordStatus.dataset.state = "none";
			recordStatus.textContent = "No record selected";
			return;
		}
		recordStatus.dataset.state = "active";
		recordStatus.textContent = state.context ? "Active record" : "Record selected";
	}

	recordInput.addEventListener("input", () => {
		window.clearTimeout(searchTimer);
		window.setTimeout(setRecordStatus, 0);
		searchTimer = window.setTimeout(() => searchRecords(recordInput.value.trim()), 250);
	});
	suggestionBox.addEventListener("click", (event) => {
		const option = event.target.closest("[data-value]");
		if (!option) return;
		recordInput.value = option.dataset.value;
		state.selectedLabel = (option.querySelector("strong") || {}).textContent || "";
		// A newly chosen record has no answer behind it yet, so the panel shows
		// what we genuinely know -- the name and id -- and says the rest loads
		// with the first answer. Inventing a second lookup endpoint to fill it
		// early would duplicate what ask_ucc already returns.
		state.context = null;
		state.checkedAt = "";
		state.asked = [];
		hideSuggestions();
		setRecordStatus();
		renderContext();
		questionInput.focus();
	});
	document.addEventListener("click", (event) => {
		if (!suggestionBox.contains(event.target) && event.target !== recordInput) hideSuggestions();
	});
	moduleSelect.addEventListener("change", () => {
		recordInput.value = "";
		state.category = "";
		state.selectedLabel = "";
		state.context = null;
		state.checkedAt = "";
		state.asked = [];
		hideSuggestions();
		setRecordStatus();
		applyModule();
	});

	// --- verified FAQ buttons -------------------------------------------
	// Categories and questions come from the server, ported verbatim from
	// the legacy UI's own question maps (ask_ucc/guided_questions.py). The
	// legacy version sent a guided question IMMEDIATELY on click rather
	// than filling the box, and that is preserved -- it is what makes them
	// one-click.
	function renderGuided() {
		const module = currentModule();
		const categories = (module && module.categories) || [];
		if (!categories.length) {
			guidedPanel.hidden = true;
			return;
		}
		guidedPanel.hidden = false;
		if (!categories.some((c) => c.key === state.category)) {
			state.category = categories[0].key;
		}
		categoryRow.innerHTML = categories
			.map((c) => (
				'<button type="button" role="tab" aria-selected="' + (c.key === state.category)
				+ '" class="ucc-ask-category' + (c.key === state.category ? " is-active" : "")
				+ '" data-ask-category="' + askEsc(c.key) + '">' + askEsc(c.label) + "</button>"
			))
			.join("");
		const active = categories.find((c) => c.key === state.category);
		questionRow.innerHTML = ((active && active.questions) || [])
			.map((q) => (
				'<button type="button" class="ucc-ask-question" data-ask-question-text="'
				+ askEsc(q.question) + '">' + askEsc(q.label) + "</button>"
			))
			.join("");
	}

	categoryRow.addEventListener("click", (event) => {
		const button = event.target.closest("[data-ask-category]");
		if (!button) return;
		state.category = button.dataset.askCategory;
		renderGuided();
	});

	root.addEventListener("click", (event) => {
		const button = event.target.closest("[data-ask-question-text]");
		if (!button) return;
		const text = button.dataset.askQuestionText;
		questionInput.value = text;
		// Legacy behaviour: with no record chosen it does NOT send -- it
		// prompts for one instead of firing a request that cannot resolve.
		if (!recordInput.value.trim()) {
			setStatus("Select a record first.", "error");
			recordInput.focus();
			return;
		}
		ask();
	});

	// --- asking
	function ask() {
		if (state.busy) return;
		const module = currentModule();
		const record = recordInput.value.trim();
		const question = questionInput.value.trim();
		if (!module) return;
		if (!record) {
			setStatus("Select a record first.", "error");
			return;
		}
		if (!question) {
			setStatus("Enter a question first.", "error");
			return;
		}

		state.busy = true;
		submitButton.disabled = true;
		setStatus("Checking live records…");

		frappe.call({
			method: "ucc_intelligence.api.ask_ucc",
			args: { module: module.key, question: question, record: record },
			callback(response) {
				const message = response && response.message;
				if (message) {
					state.asked.push(question);
					if (message.record_context) state.context = message.record_context;
					if (message.checked_at) state.checkedAt = message.checked_at;
					thread.insertAdjacentHTML(
						"afterbegin", renderTurn(question, message, module, suggestionsFor(module, question)));
					questionInput.value = "";
					clearButton.hidden = false;
					setStatus("");
					setRecordStatus();
					renderContext();
				} else {
					setStatus("The server returned no answer.", "error");
				}
			},
			error(error) {
				setStatus(window.UCCShared.errorText(error) || "The request failed.", "error");
			},
			always() {
				state.busy = false;
				submitButton.disabled = false;
			},
		});
	}

	// Follow-ups are drawn from the module's own verified question set, minus
	// what has already been asked this session. System-generated, and provably
	// so: nothing here is written by a model.
	function suggestionsFor(module, justAsked) {
		const asked = state.asked.concat([justAsked]).map((q) => q.toLowerCase());
		const pool = [];
		((module && module.categories) || []).forEach((category) => {
			(category.questions || []).forEach((item) => {
				if (asked.indexOf(item.question.toLowerCase()) === -1) pool.push(item);
			});
		});
		return pool.slice(0, 3);
	}

	submitButton.addEventListener("click", ask);
	questionInput.addEventListener("keydown", (event) => {
		if (event.key === "Enter" && !event.shiftKey) {
			event.preventDefault();
			ask();
		}
	});

	// Clear chat wipes the on-screen thread only. Stored conversations (the
	// UCC AI Conversation / Message records, when persistence is enabled) are
	// deliberately untouched -- this is a "the screen is too long to read"
	// control, not a delete-my-audit-trail control. It still confirms first:
	// an answer someone was reading is not something to discard on a stray
	// click.
	clearButton.addEventListener("click", () => {
		if (!window.confirm("Clear the answers shown on screen? Saved conversation records are not affected.")) return;
		thread.innerHTML = "";
		state.asked = [];
		clearButton.hidden = true;
		setStatus("");
		questionInput.focus();
	});

	// The context panel and the answer cards both trigger questions, so one
	// delegated listener on the root covers both.
	contextPanel.addEventListener("click", (event) => {
		const action = event.target.closest("[data-ask-context-question]");
		if (!action) return;
		questionInput.value = action.dataset.askContextQuestion;
		ask();
	});
	thread.addEventListener("click", (event) => {
		const suggestion = event.target.closest("[data-ask-suggested]");
		if (!suggestion) return;
		questionInput.value = suggestion.dataset.askSuggested;
		ask();
	});
	// <details> exposes its own expanded state to assistive tech; mirroring it
	// onto the summary keeps the explicit aria-expanded the brief asks for
	// without hand-rolling a disclosure widget.
	thread.addEventListener("toggle", (event) => {
		const details = event.target;
		if (!details || !details.matches || !details.matches(".ucc-ask-collapse")) return;
		const summary = details.querySelector("summary");
		if (summary) summary.setAttribute("aria-expanded", details.open ? "true" : "false");
	}, true);

	function renderContext() {
		contextPanel.innerHTML = renderContextPanel(
			currentModule(), recordInput.value.trim(), state.selectedLabel, state.context, state.checkedAt);
	}

	setRecordStatus();
	renderContext();
}

// --- rendering -------------------------------------------------------------
// Two card types, decided by the server's answer_kind, plus one amber band
// that is neither. Nothing here infers the type from the text.

function renderTurn(question, message, module, suggested) {
	return (
		'<article class="ucc-ask-turn">'
		+ '<div class="ucc-ask-user"><div class="ucc-ask-user-bubble">' + askEsc(question) + "</div></div>"
		+ renderAnswerCard(question, message, module)
		+ renderSuggested(suggested)
		+ "</article>"
	);
}

function renderAnswerCard(question, message, module) {
	// A blocked record renders the SAME notice Analytics uses for a blocked
	// source -- not a bespoke error box, and never a raw exception string.
	const blocked = (message.sources || []).find((s) => s.status === "permission_denied");
	if (blocked) {
		return window.UCCShared.permissionNoticeHtml({
			view: module ? module.label : "This answer",
			source: blocked.doctype,
			detail: blocked.message,
		});
	}
	if (message.answer_kind === "verified_record") return renderVerifiedCard(question, message);
	if (message.answer_kind === "ai_analysis") return renderAiCard(message);
	return renderUnavailableCard(message);
}

function askTimestamp(value) {
	if (!value) return "";
	const parsed = new Date(String(value).replace(" ", "T"));
	if (isNaN(parsed.getTime())) return String(value);
	return parsed.toLocaleString(undefined, {
		day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit",
	});
}

function humanise(key) {
	return String(key).replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function renderFactValue(value) {
	if (value == null || value === "") return "&mdash;";
	if (Array.isArray(value)) {
		if (!value.length) return "&mdash;";
		if (typeof value[0] !== "object") return askEsc(value.join(", "));
		return askEsc(value.length + " record(s)");
	}
	if (typeof value === "object") return askEsc(JSON.stringify(value));
	if (typeof value === "boolean") return value ? "Yes" : "No";
	return askEsc(value);
}

// Fields that identify the subject rather than answer anything about it. They
// belong in the context panel and the answer sentence, not in a fact tile that
// repeats what the reader already selected.
const ASK_SUBJECT_KEYS = ["student_name", "agent_name", "title", "subject"];
const ASK_SKIP_KEYS = ["status", "note"];

// Every scalar fact on display, flattened, in the order the tools returned
// them. Lists and nested objects are not tiles -- they are the collapsed
// supporting-facts table, which is what the "one answer, evidence underneath"
// hierarchy asks for.
function scalarFacts(message) {
	const facts = message.facts || {};
	// The record's own id is not a fact about it: it is what the reader picked,
	// and it is already on screen twice (the picker and the context panel).
	// Identified by VALUE rather than by a list of per-module field names --
	// the module keys belong on the server, not in a table in here.
	const recordId = (message.record_context || {}).record;
	const out = [];
	Object.keys(facts).forEach((toolName) => {
		const group = facts[toolName];
		if (!group || group.status !== "available") return;
		Object.keys(group).forEach((key) => {
			if (ASK_SKIP_KEYS.indexOf(key) !== -1) return;
			const value = group[key];
			if (value && typeof value === "object") return;
			if (recordId && value === recordId) return;
			out.push({ key: key, label: humanise(key), value: value });
		});
	});
	return out;
}

function subjectName(message) {
	const facts = message.facts || {};
	let found = "";
	Object.keys(facts).forEach((toolName) => {
		const group = facts[toolName];
		if (!group || group.status !== "available" || found) return;
		ASK_SUBJECT_KEYS.forEach((key) => {
			if (!found && group[key] && typeof group[key] === "string") found = group[key];
		});
	});
	if (found) return found;
	const context = message.record_context;
	const nameField = context && (context.fields || [])[0];
	return (nameField && nameField.value) || "this record";
}

// The direct answer, built from the record's own values -- never phrased for
// the reader by a model. A boolean gets the plain Yes/No it deserves; anything
// else leads with the value itself. The second line names the field it came
// from, so "No." is never a claim floating free of its source.
function verifiedAnswerLine(message) {
	const facts = scalarFacts(message).filter((f) => ASK_SUBJECT_KEYS.indexOf(f.key) === -1);
	const subject = subjectName(message);
	if (!facts.length) {
		return '<p class="ucc-ask-answer"><strong>The record was read successfully.</strong>'
			+ '<span class="ucc-ask-answer-detail">No individual field was requested by this question. '
			+ "Open Supporting facts below for everything that was checked.</span></p>";
	}
	const first = facts[0];
	let headline;
	if (typeof first.value === "boolean") headline = first.value ? "Yes." : "No.";
	else if (first.value == null || first.value === "" || first.value === "Not recorded") headline = "Not recorded.";
	else headline = String(first.value);
	return '<p class="ucc-ask-answer"><strong>' + askEsc(headline) + "</strong>"
		+ '<span class="ucc-ask-answer-detail">' + askEsc(first.label) + " for " + askEsc(subject)
		+ ", read from the live record.</span></p>";
}

function renderTiles(facts) {
	if (!facts.length) return "";
	return '<dl class="ucc-ask-tiles">' + facts.slice(0, 6).map((fact) => (
		'<div class="ucc-ask-tile"><dt>' + askEsc(fact.label) + "</dt>"
		+ "<dd>" + renderFactValue(fact.value) + "</dd></div>"
	)).join("") + "</dl>";
}

// A warning is not an answer and not a fact. It says so in its own label, so a
// reader skimming colour alone still cannot mistake it for either.
function renderWarnings(message) {
	return (message.warnings || []).map((warning) => (
		'<div class="ucc-ask-warning" role="note">' + ASK_ICON.warning
		+ "<div><strong>Data check</strong>" + askEsc(warning.message) + "</div></div>"
	)).join("");
}

function renderCollapse(label, body, open) {
	if (!body) return "";
	return '<details class="ucc-ask-collapse"' + (open ? " open" : "") + ">"
		+ '<summary aria-expanded="' + (open ? "true" : "false") + '">' + askEsc(label) + "</summary>"
		+ '<div class="ucc-ask-collapse-body">' + body + "</div></details>";
}

function factsTableHtml(message) {
	const facts = message.facts || {};
	const groups = Object.keys(facts).filter((k) => facts[k] && facts[k].status === "available");
	if (!groups.length) return "";
	return groups.map((toolName) => {
		const group = facts[toolName];
		const rows = Object.keys(group)
			.filter((k) => k !== "status" && k !== "note")
			.map((k) => "<tr><th>" + askEsc(humanise(k)) + "</th><td>" + renderFactValue(group[k]) + "</td></tr>")
			.join("");
		return '<div class="ucc-ask-fact-group"><h4>' + askEsc(humanise(toolName)) + "</h4>"
			+ '<table class="ucc-ask-fact-table">' + rows + "</table>"
			+ (group.note ? "<p>" + askEsc(group.note) + "</p>" : "")
			+ "</div>";
	}).join("");
}

function recordDetailsHtml(message) {
	const context = message.record_context;
	if (!context || !(context.fields || []).length) return "";
	return '<table class="ucc-ask-fact-table">' + context.fields.map((field) => (
		"<tr><th>" + askEsc(field.label) + "</th><td>" + renderFactValue(field.value) + "</td></tr>"
	)).join("") + "</table>";
}

function sourceLinksHtml(message) {
	const sources = (message.sources || []).filter((s) => s.status === "available" && s.record);
	if (!sources.length) return "";
	return sources.map((s) => {
		const route = window.UCCShared.doctypeRoute(s.doctype) + "/" + encodeURIComponent(s.record);
		return '<a class="ucc-ask-source" href="' + askEsc(route) + '" target="_blank" rel="noopener">'
			+ askEsc(s.doctype) + ": " + askEsc(s.record) + ASK_ICON.external + "</a>";
	}).join("");
}

function renderVerifiedCard(question, message) {
	const facts = scalarFacts(message).filter((f) => ASK_SUBJECT_KEYS.indexOf(f.key) === -1);
	return '<section class="ucc-ask-card is-verified" aria-label="Verified record answer">'
		+ '<div class="ucc-ask-card-head"><span class="ucc-ask-card-label">'
		+ ASK_ICON.verified + "Verified record answer</span>"
		+ '<span class="ucc-ask-card-meta">Checked ' + askEsc(askTimestamp(message.checked_at)) + "</span></div>"
		+ '<div class="ucc-ask-card-body">'
		+ verifiedAnswerLine(message)
		+ renderTiles(facts)
		+ renderWarnings(message)
		+ "</div>"
		+ '<div class="ucc-ask-card-foot">'
		+ renderCollapse("View supporting facts", factsTableHtml(message))
		+ renderCollapse("Record details", recordDetailsHtml(message))
		+ sourceLinksHtml(message)
		+ "</div></section>";
}

function renderAiCard(message) {
	const answer = message.answer || {};
	const checks = Object.keys(message.facts || {})
		.filter((k) => message.facts[k] && message.facts[k].status === "available").length;
	// Model, version and timings go here and nowhere else. They matter for an
	// audit trail and not at all to the person reading the answer, and putting
	// them in the header made every answer look like a machine's output before
	// anyone had read a word of it.
	const technical = "<table class=\"ucc-ask-fact-table\">"
		+ (answer.model ? "<tr><th>Model</th><td>" + askEsc(answer.model) + "</td></tr>" : "")
		+ "<tr><th>Retrieved at</th><td>" + askEsc(askTimestamp(message.checked_at)) + "</td></tr>"
		+ "<tr><th>Record checks</th><td>" + checks + "</td></tr>"
		+ (answer.latency_ms ? "<tr><th>Latency</th><td>" + askEsc(answer.latency_ms) + " ms</td></tr>" : "")
		+ (answer.token_usage ? "<tr><th>Token usage</th><td>" + renderFactValue(answer.token_usage) + "</td></tr>" : "")
		+ (message.conversation_id ? "<tr><th>Conversation</th><td>" + askEsc(message.conversation_id) + "</td></tr>" : "")
		+ "<tr><th>Limitation</th><td>Interpretation of the checked records only. "
		+ "It is not an approval and not an official record.</td></tr>"
		+ "</table>";
	return '<section class="ucc-ask-card is-ai" aria-label="AI analysis">'
		+ '<div class="ucc-ask-card-head"><span class="ucc-ask-card-label">'
		+ ASK_ICON.ai + "AI analysis</span>"
		+ '<span class="ucc-ask-card-meta">Based on ' + checks + " live record check"
		+ (checks === 1 ? "" : "s") + "</span></div>"
		+ '<div class="ucc-ask-card-body">'
		+ '<p class="ucc-ask-answer-text">' + askEsc(answer.text || "") + "</p>"
		+ renderWarnings(message)
		+ "</div>"
		+ '<div class="ucc-ask-card-foot">'
		+ renderCollapse("View supporting facts", factsTableHtml(message))
		+ renderCollapse("Technical details", technical)
		+ sourceLinksHtml(message)
		+ "</div></section>";
}

// "AI interpretation is turned off" on a plain data lookup implies
// interpretation was ever expected. It is only shown when something was
// actually lost:
//
//   disabled -> an administrator deliberately turned AI off. A choice, not an
//       event; only worth saying when there are no facts to show either.
//   unavailable -> AI is switched ON but cannot run: no key in site_config,
//       provider/model blank, unimplemented provider. ALWAYS shown. This is a
//       fault, not a setting, and suppressing it is what made "Enable AI is on
//       but nothing happens" impossible to diagnose.
//   error / guardrail_blocked -> AI DID run and its output was lost or
//       withheld. Always shown; silently dropping a withheld answer would hide
//       a guardrail firing.
//   not_found -> a record-level failure, always shown.
//
// `not_required` never reaches here: a verified lookup does not call AI at
// all, so there is nothing to report about it.
function renderUnavailableCard(message) {
	const status = message.ai_status;
	const hasFacts = Object.keys(message.facts || {})
		.some((k) => message.facts[k] && message.facts[k].status === "available");
	if (hasFacts && status === "disabled") return renderVerifiedCard("", message);

	const reasons = {
		disabled: "AI interpretation is turned off, so this question could not be interpreted.",
		unavailable: "AI is enabled but could not run, so this question could not be interpreted.",
		guardrail_blocked: "An AI answer was generated but referenced something not present in the retrieved facts, so it was withheld.",
		error: "AI interpretation could not be produced.",
		not_found: "That record could not be found.",
	};
	const text = reasons[status] || "AI interpretation is unavailable.";
	return '<section class="ucc-ask-card is-unavailable" aria-label="Answer unavailable">'
		+ '<div class="ucc-ask-card-head"><span class="ucc-ask-card-label">'
		+ ASK_ICON.warning + "Answer unavailable</span></div>"
		+ '<div class="ucc-ask-card-body"><p class="ucc-ask-answer-text">' + askEsc(text)
		+ (message.answer_error ? "\n" + askEsc(message.answer_error) : "") + "</p>"
		+ renderWarnings(message) + "</div>"
		+ '<div class="ucc-ask-card-foot">'
		+ renderCollapse("View supporting facts", factsTableHtml(message))
		+ sourceLinksHtml(message)
		+ "</div></section>";
}

function renderSuggested(suggested) {
	if (!suggested || !suggested.length) return "";
	return '<nav class="ucc-ask-suggested" aria-label="Suggested next questions">'
		+ "<h4>Suggested next questions</h4>"
		+ '<div class="ucc-ask-suggested-list">' + suggested.map((item) => (
			'<button type="button" class="ucc-ask-suggested-item" data-ask-suggested="'
			+ askEsc(item.question) + '">' + ASK_ICON.arrow + askEsc(item.label) + "</button>"
		)).join("") + "</div></nav>";
}

// --- record context panel ---------------------------------------------------
// Only ever shows what the answer already returned. There is no second lookup:
// ask_ucc's own record_context is built from the primary tool's result, which
// this user's permissions already allowed. A field the record does not carry
// is absent, not blank.
function askInitials(name) {
	const parts = String(name || "").replace(/,/g, " ").trim().split(/\s+/).filter(Boolean);
	if (!parts.length) return "?";
	if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
	return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// The panel's two shortcut buttons are the first verified question of each of
// the module's first two categories -- taken from what the SERVER offered for
// this module, never from a table of module keys in here. A module the server
// does not offer has no buttons, because it has no categories.
function contextActions(module) {
	const categories = (module && module.categories) || [];
	const icons = [ASK_ICON.route, ASK_ICON.chart];
	return categories.slice(0, 2).map((category, index) => {
		const first = (category.questions || [])[0];
		return first ? { question: first.question, label: first.label, icon: icons[index] } : null;
	}).filter(Boolean);
}

function renderContextPanel(module, record, selectedLabel, context, checkedAt) {
	const head = '<div class="ucc-ask-context-head"><h3>Record context</h3>'
		+ "<p>Selected record and current scope</p></div>";

	if (!record) {
		return '<section class="ucc-ask-context-card">' + head
			+ '<p class="ucc-ask-context-empty">No record is selected. Search for one above to see its '
			+ "summary and the fields every answer is checked against.</p></section>";
	}

	const name = (context && (context.fields || [])[0] && context.fields[0].value) || selectedLabel || record;
	const fields = context
		? (context.fields || []).slice(1).filter((field) => field.value !== context.record)
		: [];
	const identity = '<div class="ucc-ask-context-identity">'
		+ '<span class="ucc-ask-avatar" aria-hidden="true">' + askEsc(askInitials(name)) + "</span>"
		+ "<div><div class=\"ucc-ask-context-name\">" + askEsc(name) + "</div>"
		+ '<div class="ucc-ask-context-id">' + askEsc(record) + "</div></div></div>";

	const rows = fields.length
		? '<dl class="ucc-ask-context-fields">' + fields.map((field) => (
			'<div class="ucc-ask-context-field"><dt>' + askEsc(field.label) + "</dt>"
			+ "<dd>" + renderFactValue(field.value) + "</dd></div>"
		)).join("") + "</dl>"
		: '<p class="ucc-ask-context-empty">Ask a question to load this record’s summary fields.</p>';

	const recordLink = context && context.doctype && context.record
		? '<a class="ucc-ask-context-action" target="_blank" rel="noopener" href="'
			+ askEsc(window.UCCShared.doctypeRoute(context.doctype) + "/" + encodeURIComponent(context.record))
			+ '">' + ASK_ICON.person + "Open " + askEsc(context.doctype) + ASK_ICON.external + "</a>"
		: "";
	const actions = contextActions(module)
		.map((item) => (
			'<button type="button" class="ucc-ask-context-action" data-ask-context-question="'
			+ askEsc(item.question) + '">' + item.icon + askEsc(item.label) + "</button>"
		)).join("");

	const freshness = checkedAt
		? '<section class="ucc-ask-context-card"><div class="ucc-ask-freshness">' + ASK_ICON.clock
			+ "<div>Live record check completed " + askEsc(askTimestamp(checkedAt))
			+ ". Access follows the signed-in user’s existing permissions.</div></div></section>"
		: "";

	return '<section class="ucc-ask-context-card">' + head + identity + rows + "</section>"
		+ (recordLink || actions
			? '<section class="ucc-ask-context-card"><div class="ucc-ask-context-actions">'
				+ recordLink + actions + "</div></section>"
			: "")
		+ freshness;
}


// ---------------------------------------------------------------------------
// SETTINGS LINK -- the UCC Intelligence Settings Single doctype had no entry
// point anywhere in the UI; it could only be reached by typing the URL. This
// puts a gear in the header immediately AFTER the workspace tab row -- outside
// the nav, with its own spacing and box, so it reads as a separate control
// rather than a fourth tab crowding "Ask UCC". Two earlier placements were
// wrong: buried among the header controls (invisible), then inside the nav
// itself (too small and squeezed against the tabs).
//
// Shown only to users who can actually open it. The Settings form is System
// Manager-only (its own DocType permissions, plus get_settings_status()'s
// frappe.only_for), so showing the gear to everyone would just be an
// invitation to a permission error. Hiding a link is not a security control --
// the DocType's own permissions remain the real gate.
//
// The visibility check MUST NOT be frappe.client.get_count. UCC Intelligence
// Settings is a Single (issingle: 1), and Singles have no `tab<DocType>` table
// at all -- their values live in `tabSingles`. get_count issues a real
// SELECT ... FROM `tabUCC Intelligence Settings`, so it threw
// "Table 'ucc_sms_v2.tabUCC Intelligence Settings' doesn't exist" on every
// page load regardless of permissions or migration state -- which also left
// the gear permanently hidden, since only the success path revealed it.
// frappe.model.can_read reads the permissions already in frappe.boot: correct
// for Singles and no server round-trip.
// ---------------------------------------------------------------------------
function initSettingsLink(platformRoot) {
	const button = platformRoot.querySelector("[data-ucc-settings-link]");
	if (!button || button.dataset.settingsReady === "1") return;
	button.dataset.settingsReady = "1";

	// The gear now opens a chooser rather than jumping straight to the form.
	// Agreed split (2026-08-03): the AI provider, chart palette and knowledge
	// policy are plain fields and Frappe's own form renders them fine; access
	// is a MATRIX and monitoring rules are a TABLE, and neither is readable as
	// a stack of form fields. So those two get a Sophia page, behind the same
	// gear, and everything stays in one entry point.
	button.addEventListener("click", () => {
		if (window.UCCSettings) window.UCCSettings.open();
		else frappe.set_route("Form", "UCC Intelligence Settings");
	});

	// Only hide on a positive "no". If the perm API isn't there to ask, show
	// the gear and let the form's own permission check answer -- a control
	// that is merely styled away is not a gate either way.
	const canRead = !(window.frappe && frappe.model && frappe.model.can_read)
		|| frappe.model.can_read("UCC Intelligence Settings");
	button.hidden = !canRead;
}

frappe.pages['sophia-analytics'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Sophia",
		single_column: true,
	});

	// page.body is jQuery-wrapped in this Frappe version, not a raw DOM node --
	// confirmed by direct browser inspection (the same issue Dashboard Studio
	// hit). [0] unwraps to the underlying element; the rest of this port uses
	// plain DOM APIs throughout, so unwrap once here rather than switching the
	// ported engine/shell code to jQuery.
	const bodyEl = page.body[0] || page.body;
	bodyEl.innerHTML = SHELL_HTML;
	const root = bodyEl.querySelector("#uccIntelligencePlatform");

	function boot() {
		initPlatformShell(root);
		initAnalyticsEngine(root);
		initDiagramExplorer(root);
		initAskUcc(root);
		initSettingsLink(root);
	}

	if (window.UCCShared) {
		boot();
	} else {
		frappe.require("/assets/ucc_intelligence/js/shared.js", boot);
	}
};
