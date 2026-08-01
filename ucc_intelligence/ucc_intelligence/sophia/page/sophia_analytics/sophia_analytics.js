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

const SHELL_HTML = "<div class=\"ucc-platform ucc-embed-safe\" data-build-id=\"SOPHIA-ANALYTICS-PAGE\" data-platform-version=\"phase-3\" id=\"uccIntelligencePlatform\"><header class=\"ucc-platform-shell\"><div class=\"ucc-platform-brand\"><div aria-hidden=\"true\" class=\"ucc-platform-mark\">UCC</div><div class=\"ucc-platform-brand-copy\"><div class=\"ucc-platform-brand-title\"><strong>UCC Intelligence Platform</strong></div><small>Analytics, evidence and guided answers</small></div></div><nav aria-label=\"Platform workspaces\" class=\"ucc-platform-workspaces\"><button aria-pressed=\"true\" class=\"is-active\" data-ucc-workspace=\"analytics\" type=\"button\">Analytics</button><button aria-pressed=\"false\" data-ucc-workspace=\"explore\" type=\"button\">Explore</button><button aria-pressed=\"false\" data-ucc-workspace=\"ask\" type=\"button\">Ask UCC</button></nav><button aria-label=\"UCC Intelligence Settings\" class=\"ucc-shell-settings-link\" data-ucc-settings-link=\"\" hidden=\"\" title=\"UCC Intelligence Settings\" type=\"button\"><span aria-hidden=\"true\">&#9881;</span><span class=\"ucc-visually-hidden\">UCC Intelligence Settings</span></button><div class=\"ucc-platform-dashboard-control\" data-ucc-dashboard-control=\"\"><label for=\"uccDashboardSelect\">Dashboard</label><select id=\"uccDashboardSelect\"><option value=\"criterion_1\">Criterion 1 \u00b7 Leadership and Strategic Planning</option><option value=\"criterion_2\">Criterion 2 \u00b7 Corporate Administration</option><option value=\"criterion_3\">Criterion 3 \u00b7 External Recruitment Agents</option><option value=\"criterion_4\">Criterion 4 \u00b7 Student Protection and Support Services</option><option selected=\"\" value=\"criterion_5\">Criterion 5 \u00b7 Academic Systems and Processes</option><option value=\"criterion_6\">Criterion 6 \u00b7 Quality Assurance, Innovation and Continual Improvement</option><option value=\"criterion_7\">Criterion 7 \u00b7 Performance Outcomes</option></select></div><button aria-expanded=\"true\" aria-label=\"Minimise UCC navigation\" class=\"ucc-shell-collapse-toggle\" data-shell-toggle=\"\" title=\"Minimise navigation\" type=\"button\"><span aria-hidden=\"true\" class=\"ucc-shell-toggle-icon\" data-shell-toggle-icon=\"\">\u2039</span><span class=\"ucc-visually-hidden\" data-shell-toggle-label=\"\">Minimise navigation</span></button></header><main class=\"ucc-platform-main\"><section class=\"ucc-platform-workspace\" data-ucc-workspace-panel=\"analytics\"><div class=\"ucc-criterion-dashboard\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_5\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_5\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_4\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_4\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_1\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_1\" data-live-api=\"1\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_2\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_2\" data-live-api=\"1\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_3\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_3\" data-live-api=\"1\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_6\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_6\" data-live-api=\"1\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_7\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_7\" data-live-api=\"1\"></div></section><section class=\"ucc-platform-workspace\" data-ucc-workspace-panel=\"explore\" hidden=\"\">\n<div class=\"ucc-explore-hub\" data-ucc-explore=\"\">\n<header class=\"ucc-explore-hero\">\n<div>\n<span class=\"ucc-explore-kicker\">DIAGRAM EXPLORER</span>\n<h1>Find live diagrams without opening another dashboard page</h1>\n<p>Search all Criterion 1\u20137 visual catalogues. Criteria 1, 2, 3, 6 and 7 use permission-aware live API foundations; Criteria 4 and 5 retain their established live implementations.</p>\n</div>\n<div class=\"ucc-explore-summary\">\n<article><span>Criterion 4</span><strong data-ucc-explore-count=\"criterion_4\">0</strong><small>live visuals</small></article>\n<article><span>Criterion 5</span><strong data-ucc-explore-count=\"criterion_5\">0</strong><small>live visuals</small></article>\n<article><span>Live foundations</span><strong>5</strong><small>permission-aware APIs</small></article>\n</div>\n</header>\n<div class=\"ucc-explore-controls\">\n<label><span>Search</span><input autocomplete=\"off\" data-ucc-explore-search=\"\" placeholder=\"Search diagram, section, type or source\" role=\"searchbox\" spellcheck=\"false\" type=\"text\"/></label>\n<label><span>Section</span><select data-ucc-explore-section=\"\"><option value=\"\">All sections</option></select></label>\n<label><span>Visual type</span><select data-ucc-explore-type=\"\"><option value=\"\">All visual types</option></select></label>\n<button data-ucc-explore-clear=\"\" type=\"button\">Clear</button>\n</div>\n<div class=\"ucc-explore-layout\">\n<aside class=\"ucc-explore-catalogue\">\n<div class=\"ucc-explore-catalogue-head\">\n<div><strong>Available diagrams</strong><small data-ucc-explore-result-count=\"\">Scanning platform\u2026</small></div>\n<span class=\"ucc-explore-live-pill\">Live</span>\n</div>\n<div class=\"ucc-explore-list\" data-ucc-explore-list=\"\"></div>\n</aside>\n<section class=\"ucc-explore-guide\">\n<div class=\"ucc-explore-guide-card\">\n<span class=\"ucc-explore-step\">1</span>\n<div><strong>Choose the dashboard</strong><p>Use the existing Criterion selector in the top bar.</p></div>\n</div>\n<div class=\"ucc-explore-guide-card\">\n<span class=\"ucc-explore-step\">2</span>\n<div><strong>Search or filter</strong><p>The catalogue is generated from the real chart elements, so future diagrams appear automatically.</p></div>\n</div>\n<div class=\"ucc-explore-guide-card\">\n<span class=\"ucc-explore-step\">3</span>\n<div><strong>Open the live card</strong><p>One click takes you to the original analytics card. No duplicate rendering logic or copied data.</p></div>\n</div>\n<div class=\"ucc-explore-note\">\n<strong>Why this approach scales</strong>\n<p>Explore is a fast index over the existing dashboards\u2014not a second dashboard system. Criterion-specific calculations, D3 renderers, tables, exports and record links remain in their original tested components.</p>\n</div>\n</section>\n</div>\n</div>\n</section><section class=\"ucc-platform-workspace\" data-ucc-workspace-panel=\"ask\" hidden=\"\"><div class=\"ucc-ask\" data-ucc-ask=\"\"><section class=\"panel ucc-shared-panel ucc-ask-controls\"><div class=\"ucc-ask-head\"><h2>Ask UCC</h2><p>Built from live records you already have permission to see. Any AI text is labelled separately.</p></div><div class=\"ucc-ask-row\"><label class=\"ucc-ask-field\"><span>Module</span><select data-ask-module=\"\"></select></label><label class=\"ucc-ask-field ucc-ask-field-grow\"><span>Record</span><input autocomplete=\"off\" data-ask-record=\"\" placeholder=\"Search by name or ID\u2026\" type=\"text\"/><div class=\"ucc-ask-suggestions\" data-ask-suggestions=\"\" hidden=\"\"></div></label><label class=\"ucc-ask-field ucc-ask-field-grow\"><span>Question</span><input autocomplete=\"off\" data-ask-question=\"\" placeholder=\"e.g. Is this ready to close?\" type=\"text\"/></label><button class=\"btn btn-primary ucc-ask-submit\" data-ask-submit=\"\" type=\"button\">Ask</button><button class=\"btn ucc-ask-clear\" data-ask-clear=\"\" hidden=\"\" type=\"button\">Clear chat</button></div><div class=\"ucc-ask-guided\" data-ask-guided=\"\" hidden=\"\"><div class=\"ucc-ask-categories\" data-ask-categories=\"\"></div><div class=\"ucc-ask-questions\" data-ask-questions=\"\"></div></div><div class=\"ucc-ask-status\" data-ask-status=\"\" hidden=\"\"></div></section><section class=\"ucc-ask-thread\" data-ask-thread=\"\"></section></div></section></main></div>";

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
const CONFIG={"criterion_1":{"number":"1","title":"Leadership and Strategic Planning","description":"Live, permission-aware analytics foundation for leadership, governance and strategic planning. Source and metric availability is resolved from ERPNext permissions.","subcriteria":[["1.1.1","Leadership and Corporate Governance"],["1.2.1","Strategic Planning"]],"sections":{"overview":{"title":"Overview","charts":[{"id":"criterion_1-overview-targets","title":"Target Gap Summary","type":"bar"},{"id":"criterion_1-overview-sources","title":"Source Availability","type":"donut"}]},"1.1":{"title":"Leadership and Corporate Governance","charts":[{"id":"criterion_1-11-coverage","title":"Leadership and Corporate Governance Control Coverage","type":"bar"},{"id":"criterion_1-11-status","title":"Leadership and Corporate Governance Status Distribution","type":"donut"}]},"1.2":{"title":"Strategic Planning","charts":[{"id":"criterion_1-12-coverage","title":"Strategic Planning Control Coverage","type":"bar"},{"id":"criterion_1-12-status","title":"Strategic Planning Status Distribution","type":"donut"}]},"1.1.1":{"title":"Leadership and Corporate Governance","charts":[{"id":"criterion_1-11-coverage","title":"Leadership and Corporate Governance Control Coverage","type":"bar"},{"id":"criterion_1-11-status","title":"Leadership and Corporate Governance Status Distribution","type":"donut"}]},"1.2.1":{"title":"Strategic Planning","charts":[{"id":"criterion_1-12-coverage","title":"Strategic Planning Control Coverage","type":"bar"},{"id":"criterion_1-12-status","title":"Strategic Planning Status Distribution","type":"donut"}]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_1","defaultSection":"1.1.1","apiSections":{"overview":"1.1.1","1.1.1":"1.1.1","1.2.1":"1.2.1","quality":"1.1.1","sources":"1.1.1"},"panelMap":{"overview":"overview","1.1.1":"1.1.1","1.2.1":"1.2.1","sources":"sources","quality":"sources"},"filters":[["academic_year","Academic Year",["All Academic Years","2026","2025"]],["student_group","Module Class Details",["All Module Classes"]],["program","Course",["All Courses"]],{"key":"month","label":"Month","type":"month"}]},"criterion_2":{"number":"2","title":"Corporate Administration","description":"Live, permission-aware analytics foundation for human resources, communication, knowledge management and feedback. Unsupported fields are shown explicitly.","subcriteria":[["2.1.1","Staff Selection and Management"],["2.1.2","Staff Training and Development"],["2.2.1","Internal and External Communication"],["2.3.1","Data and Information Management"],["2.3.2","Knowledge Management"],["2.4.1","Feedback Management"],["2.4.2","Student Satisfaction Survey"],["2.4.3","Staff Satisfaction Survey"]],"sections":{"overview":{"title":"Overview","charts":[{"id":"criterion_2-overview-targets","title":"Target Gap Summary","type":"bar"},{"id":"criterion_2-overview-sources","title":"Source Availability","type":"donut"}]},"2.1":{"title":"Human Resource","charts":[{"id":"criterion_2-21-coverage","title":"Human Resource Control Coverage","type":"bar"},{"id":"criterion_2-21-status","title":"Human Resource Status Distribution","type":"donut"}]},"2.2":{"title":"Communication","charts":[{"id":"criterion_2-22-coverage","title":"Communication Control Coverage","type":"bar"},{"id":"criterion_2-22-status","title":"Communication Status Distribution","type":"donut"}]},"2.3":{"title":"Data, Information and Knowledge Management","charts":[{"id":"criterion_2-23-coverage","title":"Data, Information and Knowledge Management Control Coverage","type":"bar"},{"id":"criterion_2-23-status","title":"Data, Information and Knowledge Management Status Distribution","type":"donut"}]},"2.4":{"title":"Feedback Management","charts":[{"id":"criterion_2-24-coverage","title":"Feedback Management Control Coverage","type":"bar"},{"id":"criterion_2-24-status","title":"Feedback Management Status Distribution","type":"donut"}]},"2.1.1":{"title":"Human Resource","charts":[{"id":"criterion_2-21-coverage","title":"Human Resource Control Coverage","type":"bar"},{"id":"criterion_2-21-status","title":"Human Resource Status Distribution","type":"donut"}]},"2.1.2":{"title":"Staff Training and Development","charts":[{"id":"criterion_2-21-coverage","title":"Human Resource Control Coverage","type":"bar"},{"id":"criterion_2-21-status","title":"Human Resource Status Distribution","type":"donut"}]},"2.2.1":{"title":"Communication","charts":[{"id":"criterion_2-22-coverage","title":"Communication Control Coverage","type":"bar"},{"id":"criterion_2-22-status","title":"Communication Status Distribution","type":"donut"}]},"2.3.1":{"title":"Data, Information and Knowledge Management","charts":[{"id":"criterion_2-23-coverage","title":"Data, Information and Knowledge Management Control Coverage","type":"bar"},{"id":"criterion_2-23-status","title":"Data, Information and Knowledge Management Status Distribution","type":"donut"}]},"2.3.2":{"title":"Knowledge Management","charts":[{"id":"criterion_2-23-coverage","title":"Data, Information and Knowledge Management Control Coverage","type":"bar"},{"id":"criterion_2-23-status","title":"Data, Information and Knowledge Management Status Distribution","type":"donut"}]},"2.4.1":{"title":"Feedback Management","charts":[{"id":"criterion_2-24-coverage","title":"Feedback Management Control Coverage","type":"bar"},{"id":"criterion_2-24-status","title":"Feedback Management Status Distribution","type":"donut"}]},"2.4.2":{"title":"Student Satisfaction Survey","charts":[{"id":"criterion_2-24-coverage","title":"Feedback Management Control Coverage","type":"bar"},{"id":"criterion_2-24-status","title":"Feedback Management Status Distribution","type":"donut"}]},"2.4.3":{"title":"Staff Satisfaction Survey","charts":[{"id":"criterion_2-24-coverage","title":"Feedback Management Control Coverage","type":"bar"},{"id":"criterion_2-24-status","title":"Feedback Management Status Distribution","type":"donut"}]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_2","defaultSection":"2.1.1","apiSections":{"overview":"2.1.1","2.1.1":"2.1.1","2.1.2":"2.1.2","2.2.1":"2.2.1","2.3.1":"2.3.1","2.3.2":"2.3.2","2.4.1":"2.4.1","2.4.2":"2.4.2","2.4.3":"2.4.3","quality":"2.1.1","sources":"2.1.1"},"panelMap":{"overview":"overview","2.1.1":"2.1.1","2.1.2":"2.1.2","2.2.1":"2.2.1","2.3.1":"2.3.1","2.3.2":"2.3.2","2.4.1":"2.4.1","2.4.2":"2.4.2","2.4.3":"2.4.3","sources":"sources","quality":"sources"},"filters":[["academic_year","Academic Year",["All Academic Years","2026","2025"]],["student_group","Module Class Details",["All Module Classes"]],["program","Course",["All Courses"]],{"key":"month","label":"Month","type":"month"}]},"criterion_3":{"number":"3","title":"External Recruitment Agents","description":"Policy-aligned live analytics foundation for agent selection, appointment, onboarding, performance evaluation, renewal and offboarding. Unsupported fields are shown explicitly.","policy_set":[{"code":"PPD-SES-SL-3.1.1","version":"1.2","title":"Selection and Appointment of External Recruitment Agents","updated":"15 January 2026"},{"code":"PPD-SES-SL-3.2.1","version":"1.2","title":"Management and Evaluation of Recruitment Agents","updated":"15 January 2026"}],"subcriteria":[["3.1.1","Selection and Appointment"],["3.2.1","Management and Evaluation"]],"filters":[["review_year","Review Year",["All Review Years","2026","2025"]],["agent_status","Agent Status",["All Agent Statuses","Active","Pending","Inactive"]],["market","Market / Region",["All Markets","Southeast Asia","South Asia","Greater China","Other"]],["renewal_cycle","Renewal Cycle",["All Renewal Cycles","June","December"]]],"sections":{"overview":{"title":"Criterion 3 Overview","charts":[{"id":"c3-overview-lifecycle","title":"Agent Lifecycle Coverage","type":"lifecycle"},{"id":"c3-overview-policy","title":"Policy Control Coverage","type":"donut"},{"id":"c3-overview-health","title":"Agent Control Health","type":"radar"},{"id":"c3-overview-renewal","title":"Renewal and Evaluation Trend","type":"trend"},{"id":"c3-overview-exceptions","title":"Open Exception Profile","type":"bar"}]},"3.1.1":{"title":"Selection and Appointment of External Recruitment Agents","charts":[{"id":"c311-identification","title":"Identification Pathways","type":"donut"},{"id":"c311-screening","title":"Selection and Screening Funnel","type":"funnel"},{"id":"c311-weighting","title":"Selection Criteria Weighting","type":"radar"},{"id":"c311-score","title":"Selection Score Distribution","type":"bar"},{"id":"c311-approval","title":"Approval and Background Check","type":"lifecycle"},{"id":"c311-contract","title":"Contract and NDA Readiness","type":"matrix"},{"id":"c311-listing","title":"Agent Listing and Status","type":"donut"}]},"3.2.1":{"title":"Management and Evaluation of Recruitment Agents","charts":[{"id":"c321-onboarding","title":"Agent Onboarding Funnel","type":"funnel"},{"id":"c321-training","title":"Training Coverage","type":"radar"},{"id":"c321-service","title":"Service Delivery Controls","type":"matrix"},{"id":"c321-evaluation","title":"Performance Evaluation Distribution","type":"bar"},{"id":"c321-renewal","title":"Renewal Checkpoint Flow","type":"lifecycle"},{"id":"c321-complaints","title":"Complaints and Breaches","type":"donut"},{"id":"c321-offboarding","title":"Offboarding and Exit Security","type":"flow"}]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_3","defaultSection":"3.1.1","apiSections":{"overview":"3.1.1","3.1.1":"3.1.1","3.2.1":"3.2.1","quality":"3.1.1","sources":"3.1.1"},"panelMap":{"overview":"overview","3.1.1":"3.1.1","3.2.1":"3.2.1","sources":"sources","quality":"sources"}},"criterion_4":{"number":"4","title":"Student Protection and Support Services","description":"Live, permission-aware analytics for admissions, contracts, fees, student movement, refunds, student support, conduct and attendance.","subcriteria":[["4.1.1","Pre-Course Counselling, Selection and Admissions"],["4.2.1","Student Contract"],["4.2.2","Fee Collection and Fee Protection Scheme"],["4.3.1","Course Transfer, Deferment and Withdrawal"],["4.4.1","Refund"],["4.5.1","Student Support Services"],["4.6.1","Student Conduct and Attendance"]],"filters":[["academic_year","Academic Year",["All Academic Years"]],["program","Programme",["All Programmes"]],["intake","Intake",["All Intakes"]],["status","Status",["All Statuses"]],["nationality","Country / Nationality",["All Countries"]],["agent","Recruitment Agent",["All Agents"]]],"sections":{"overview":{"title":"Overview","charts":[]},"4.1.1":{"title":"Pre-Course Counselling, Selection and Admissions","charts":[]},"4.2.1":{"title":"Student Contract","charts":[]},"4.2.2":{"title":"Fee Collection and Fee Protection Scheme","charts":[]},"4.3.1":{"title":"Course Transfer, Deferment and Withdrawal","charts":[]},"4.4.1":{"title":"Refund","charts":[]},"4.5.1":{"title":"Student Support Services","charts":[]},"4.6.1":{"title":"Student Conduct and Attendance","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_4","defaultSection":"4.1.1","apiSections":{"overview":"4.1.1","4.1.1":"4.1.1","4.2.1":"4.2.1","4.2.2":"4.2.2","4.3.1":"4.3.1","4.4.1":"4.4.1","4.5.1":"4.5.1","4.6.1":"4.6.1","quality":"4.1.1","sources":"4.1.1"},"panelMap":{"overview":"overview","4.1.1":"4.1.1","4.2.1":"4.2.1","4.2.2":"4.2.2","4.3.1":"4.3.1","4.4.1":"4.4.1","4.5.1":"4.5.1","4.6.1":"4.6.1","sources":"sources","quality":"sources"}},"criterion_5":{"number":"5","title":"Academic Systems and Processes","description":"Live, permission-aware analytics for course design, review, planning, delivery, partnerships, student feedback, learning support and assessment.","subcriteria":[["5.1.1","Course Design and Development"],["5.1.2","Course Review"],["5.2.1","Course Planning"],["5.2.2","Course Delivery"],["5.3.1","Partnership Management"],["5.4","Student Feedback and Learning Support"],["5.5","Assessment"]],"sections":{"overview":{"title":"Overview","charts":[{"id":"c5-overview-readiness","title":"Academic System Readiness","type":"bar","description":"Compares the live academic-system metrics returned for the selected Criterion 5 area.","i":0},{"id":"c5-overview-availability","title":"Source Availability","type":"donut","description":"Shows readable sources, source issues, readable metrics and metric issues.","i":1},{"id":"c5-overview-health","title":"Criterion 5 System Health","type":"matrix","description":"Summarises available metrics, unavailable metrics, sources and exceptions.","i":2},{"id":"c5-overview-exceptions","title":"Criterion 5 Exception Profile","type":"funnel","description":"Highlights live exceptions that require academic or data-quality follow-up.","i":3}]},"5.1.1":{"title":"Course Design and Development","charts":[{"id":"c5-511-coverage","title":"Course Design Control Coverage","type":"bar","description":"Compares course proposal, module design, programme mapping and assessment-plan evidence.","i":0},{"id":"c5-511-status","title":"Course Design Status Distribution","type":"donut","description":"Shows available design metrics, source readiness and exceptions.","i":1},{"id":"c5-511-readiness","title":"Course Design Evidence Readiness","type":"radar","description":"Compares readiness across the main course design and development controls.","i":2},{"id":"c5-511-gaps","title":"Course Design Gap Profile","type":"funnel","description":"Highlights course design controls that require follow-up.","i":3}]},"5.1.2":{"title":"Course Review","charts":[{"id":"c5-512-coverage","title":"Course Review Control Coverage","type":"bar","description":"Compares module review, course review, approval and recommendation evidence.","i":0},{"id":"c5-512-status","title":"Course Review Status Distribution","type":"donut","description":"Shows review source and metric readiness.","i":1},{"id":"c5-512-cycle","title":"Course Review Lifecycle","type":"lifecycle","description":"Follows review evidence from recorded through approval and recommendation follow-up.","i":2},{"id":"c5-512-gaps","title":"Review Exception Profile","type":"funnel","description":"Highlights overdue or incomplete review controls.","i":3}]},"5.2.1":{"title":"Course Planning","charts":[{"id":"c5-521-coverage","title":"Course Planning Control Coverage","type":"bar","description":"Compares intake, module class, schedule and student-contract planning evidence.","i":0},{"id":"c5-521-status","title":"Course Planning Status Distribution","type":"donut","description":"Shows planning source and metric readiness.","i":1},{"id":"c5-521-flow","title":"Planning Readiness Flow","type":"lifecycle","description":"Follows planning evidence from intake through class, schedule and contract readiness.","i":2},{"id":"c5-521-gaps","title":"Planning Exception Profile","type":"funnel","description":"Highlights incomplete planning controls requiring follow-up.","i":3}]},"5.2.2":{"title":"Course Delivery","charts":[{"id":"c5-522-coverage","title":"Course Delivery Control Coverage","type":"bar","description":"Compares schedules, attendance, observations and sign-off evidence.","i":0},{"id":"c5-522-status","title":"Course Delivery Status Distribution","type":"donut","description":"Shows delivery source and metric readiness.","i":1},{"id":"c5-522-readiness","title":"Delivery Evidence Readiness","type":"radar","description":"Compares attendance, observation and sign-off evidence across delivery controls.","i":2},{"id":"c5-522-gaps","title":"Delivery Exception Profile","type":"funnel","description":"Highlights delivery controls requiring follow-up.","i":3}]},"5.3.1":{"title":"Partnerships","charts":[{"id":"c5-531-coverage","title":"Partnership Control Coverage","type":"bar","description":"Compares agreement, monitoring, evaluation and provider-rating evidence.","i":0},{"id":"c5-531-status","title":"Partnership Status Distribution","type":"donut","description":"Shows partnership source and metric readiness.","i":1},{"id":"c5-531-risk","title":"Partnership Risk Profile","type":"funnel","description":"Highlights expiry, NDA and threshold risks requiring follow-up.","i":2},{"id":"c5-531-readiness","title":"Partnership Evidence Readiness","type":"matrix","description":"Grids readiness across partnership management controls.","i":3}]},"5.4":{"title":"Student Feedback and Learning Support","charts":[{"id":"c5-54-coverage","title":"Student Feedback Control Coverage","type":"bar","description":"Compares survey, score and attendance-risk evidence.","i":0},{"id":"c5-54-status","title":"Student Feedback Status Distribution","type":"donut","description":"Shows feedback source and metric readiness.","i":1},{"id":"c5-54-readiness","title":"Feedback Evidence Readiness","type":"radar","description":"Compares survey and learning-support evidence across key controls.","i":2},{"id":"c5-54-gaps","title":"Feedback Exception Profile","type":"funnel","description":"Highlights feedback controls requiring follow-up.","i":3}]},"5.5":{"title":"Assessment","charts":[{"id":"c5-55-coverage","title":"Assessment Control Coverage","type":"bar","description":"Compares assessment plans, control fields, results, grades and scores.","i":0},{"id":"c5-55-status","title":"Assessment Status Distribution","type":"donut","description":"Shows assessment source and metric readiness.","i":1},{"id":"c5-55-readiness","title":"Assessment Evidence Readiness","type":"radar","description":"Compares readiness across assessment planning and result controls.","i":2},{"id":"c5-55-gaps","title":"Assessment Exception Profile","type":"funnel","description":"Highlights assessment controls requiring correction or follow-up.","i":3}]},"quality":{"title":"Sources and Data Quality","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_5","defaultSection":"5.1.1","apiSections":{"overview":"5.1.1","5.1.1":"5.1.1","5.1.2":"5.1.2","5.2.1":"5.2.1","5.2.2":"5.2.2","5.3.1":"5.3.1","5.4":"5.4","5.5":"5.5","quality":"5.1.1","sources":"5.1.1"},"panelMap":{"overview":"overview","5.1.1":"5.1.1","5.1.2":"5.1.2","5.2.1":"5.2.1","5.2.2":"5.2.2","5.3.1":"5.3.1","5.4":"5.4","5.5":"5.5","sources":"sources","quality":"sources"},"filters":[["year","Academic Year",["All Academic Years"]],["student_group","Module Class Details",["All Module Classes"]],["program","Course",["All Courses"]],["status","Status",["All Statuses"]]]},"criterion_6":{"number":"6","title":"Quality Assurance, Innovation and Continual Improvement","description":"Policy-aligned live analytics foundation for audits, management review, innovation, providers, risk and business continuity. Unsupported fields are shown explicitly.","policy_set":[{"code":"PPD-SGL-SQ-6.1.1","version":"1.2","title":"Internal Assessment and Quality Audits","updated":"15 January 2026"},{"code":"PPD-SGL-SQ-6.2.1","version":"1.3","title":"Management Review","updated":"10 April 2026"},{"code":"PPD-SGL-SQ-6.3.1","version":"1.2","title":"Innovation and Continual Improvement","updated":"15 January 2026"},{"code":"PPD-OE-FN-6.4.1","version":"1.2","title":"Provider's Accreditation and Evaluation","updated":"15 January 2026"},{"code":"PPD-SGL-SQ-6.5.3","version":"1.2","title":"Hazard Identification and Risk Assessment","updated":"15 January 2026"}],"subcriteria":[["6.1.1","Internal Assessment and Quality Audits"],["6.2.1","Management Review"],["6.3.1","Innovation and Continual Improvement"],["6.4.1","Provider Accreditation and Evaluation"],["6.5.3","Hazard Identification and Risk Assessment"]],"filters":[["review_year","Review Year",["All Review Years","2026","2025"]],["department","Department",["All Departments","SGL / SQ","Academic","Student Services","Finance"]],["quality_area","Quality Area",["All Quality Areas","Audit","Management Review","Innovation","Providers","Risk"]],["month","Month",["All Months","January 2026","April 2026","July 2026","December 2026"]]],"sections":{"overview":{"title":"Criterion 6 Overview","charts":[{"id":"c6-overview-cycle","title":"Quality Management Cycle","type":"lifecycle"},{"id":"c6-overview-policy","title":"Policy Evidence Coverage","type":"donut"},{"id":"c6-overview-health","title":"Quality System Health","type":"radar"},{"id":"c6-overview-calendar","title":"Quality Calendar Completion","type":"trend"},{"id":"c6-overview-actions","title":"Action Status","type":"bar"},{"id":"c6-overview-readiness","title":"Source Readiness","type":"matrix"}]},"6.1.1":{"title":"Internal Assessment and Quality Audits","charts":[{"id":"c611-programme","title":"Annual Audit Programme","type":"donut"},{"id":"c611-scope","title":"Audit Scope Coverage","type":"radar"},{"id":"c611-lifecycle","title":"Audit Lifecycle","type":"funnel"},{"id":"c611-auditors","title":"Auditor Qualification and Independence","type":"matrix"},{"id":"c611-findings","title":"Audit Findings by Severity","type":"bar"},{"id":"c611-cap","title":"Corrective Action Closure","type":"trend"}]},"6.2.1":{"title":"Management Review","charts":[{"id":"c621-thesis","title":"THESIS Review Coverage","type":"radar"},{"id":"c621-preparation","title":"Management Review Preparation","type":"funnel"},{"id":"c621-inputs","title":"Review Input Completeness","type":"matrix"},{"id":"c621-outputs","title":"Review Outputs","type":"donut"},{"id":"c621-ageing","title":"Action Ageing","type":"bar"},{"id":"c621-effectiveness","title":"Action Effectiveness","type":"trend"}]},"6.3.1":{"title":"Innovation and Continual Improvement","charts":[{"id":"c631-types","title":"Innovation Type Mix","type":"donut"},{"id":"c631-lifecycle","title":"Improvement Initiative Lifecycle","type":"funnel"},{"id":"c631-investment","title":"Innovation Performance Categories","type":"radar"},{"id":"c631-qipi","title":"QIPI Outcome Trend","type":"trend"},{"id":"c631-impact","title":"Before and After Impact","type":"gauge"},{"id":"c631-status","title":"Improvement Action Status","type":"matrix"}]},"6.4.1":{"title":"Provider's Accreditation and Evaluation","charts":[{"id":"c641-tier","title":"Provider Tier Profile","type":"donut"},{"id":"c641-screening","title":"Provider Accreditation Funnel","type":"funnel"},{"id":"c641-package","title":"Compliance Package","type":"matrix"},{"id":"c641-delivery","title":"Service Delivery and Purchase Controls","type":"lifecycle"},{"id":"c641-rating","title":"Provider Rating Weighting","type":"radar"},{"id":"c641-outcomes","title":"Provider Evaluation Outcomes","type":"donut"}]},"6.5.3":{"title":"Hazard Identification and Risk Assessment","charts":[{"id":"c653-reporting","title":"Hazard Reporting Funnel","type":"funnel"},{"id":"c653-levels","title":"Risk Level Distribution","type":"donut"},{"id":"c653-matrix","title":"5×5 Risk Matrix","type":"risk-matrix"},{"id":"c653-treatment","title":"Risk Treatment Lifecycle","type":"lifecycle"},{"id":"c653-residual","title":"Residual Risk Trend","type":"trend"},{"id":"c653-bcdr","title":"Business Continuity Readiness","type":"radar"}]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_6","defaultSection":"6.1.1","apiSections":{"overview":"6.1.1","6.1.1":"6.1.1","6.2.1":"6.2.1","6.3.1":"6.3.1","6.4.1":"6.4.1","6.5.3":"6.5.3","quality":"6.1.1","sources":"6.1.1"},"panelMap":{"overview":"overview","6.1.1":"6.1.1","6.2.1":"6.2.1","6.3.1":"6.3.1","6.4.1":"6.4.1","6.5.3":"6.5.3","sources":"sources","quality":"sources"}},"criterion_7":{"number":"7","title":"Performance Outcomes","description":"Live, permission-aware analytics foundation for outcome measurement, target achievement and stakeholder performance. Unsupported fields are shown explicitly.","subcriteria":[["7.1.1","Measurement of Outcomes"]],"sections":{"overview":{"title":"Overview","charts":[{"id":"criterion_7-overview-targets","title":"Target Gap Summary","type":"bar"},{"id":"criterion_7-overview-sources","title":"Source Availability","type":"donut"}]},"7.1":{"title":"Measurement of Outcomes","charts":[{"id":"criterion_7-71-coverage","title":"Measurement of Outcomes Control Coverage","type":"bar"},{"id":"criterion_7-71-status","title":"Measurement of Outcomes Status Distribution","type":"donut"}]},"7.1.1":{"title":"Measurement of Outcomes","charts":[{"id":"criterion_7-71-coverage","title":"Measurement of Outcomes Control Coverage","type":"bar"},{"id":"criterion_7-71-status","title":"Measurement of Outcomes Status Distribution","type":"donut"}]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_7","defaultSection":"7.1.1","apiSections":{"overview":"7.1.1","7.1.1":"7.1.1","quality":"7.1.1","sources":"7.1.1"},"panelMap":{"overview":"overview","7.1.1":"7.1.1","sources":"sources","quality":"sources"},"filters":[["academic_year","Academic Year",["All Academic Years","2026","2025"]],["student_group","Module Class Details",["All Module Classes"]],["program","Course",["All Courses"]],{"key":"month","label":"Month","type":"month"}]}};
const LIVE_VISUAL_EXPANSION={"criterion_1":{"overview":[{"id":"v190-c1-overview-01","title":"Governance and Strategy Metric Profile","type":"bar","description":"Compares key governance and strategic planning metrics side by side for this criterion.","i":0},{"id":"v190-c1-overview-02","title":"Live Source Availability","type":"donut","description":"Shows what share of the underlying DocTypes and fields are currently readable.","i":1},{"id":"v190-c1-overview-06","title":"Evidence Readiness Matrix","type":"matrix","description":"Grids evidence completeness against each governance and strategy control area.","i":5},{"id":"v190-c1-overview-08","title":"Leadership Responsibility Coverage","type":"trend","description":"Tracks over time how many leadership roles have clearly assigned responsibilities.","i":7},{"id":"v190-c1-overview-17","title":"Governance Risk Exposure","type":"bar","description":"Compares governance risk exposure across the areas this criterion covers.","i":16},{"id":"v190-c1-overview-20","title":"Evidence Completeness","type":"lifecycle","description":"Follows evidence records from missing through to fully documented and verified.","i":19},{"id":"v190-c1-overview-27","title":"Target Achievement Gauge","type":"funnel","description":"Tracks strategic targets from set through to fully achieved.","i":26},{"id":"v190-c1-overview-28","title":"Overall Criterion Readiness","type":"lifecycle","description":"Summarises how ready Criterion 1 is overall, from raw data through to verified evidence.","i":27}],"1.1.1":[{"id":"v190-c1-111-01","title":"Governance Control Coverage","type":"bar","description":"Compares how many governance controls are in place across different control areas.","i":0},{"id":"v190-c1-111-02","title":"Governance Status Distribution","type":"donut","description":"Shows the current status mix of governance records, from open to resolved.","i":1},{"id":"v190-c1-111-03","title":"Leadership and Role Readiness","type":"funnel","description":"Tracks leadership roles from defined through to fully staffed and ready.","i":2},{"id":"v190-c1-111-04","title":"Policy and Review Lifecycle","type":"lifecycle","description":"Follows a governance policy from drafted through approval to its next review.","i":3},{"id":"v190-c1-111-05","title":"Governance Evidence Matrix","type":"radar","description":"Compares evidence strength across the different governance control areas.","i":4},{"id":"v190-c1-111-06","title":"Governance Action Completion","type":"matrix","description":"Grids governance action completion against each responsible area or owner.","i":5},{"id":"v190-c1-111-15","title":"Policy Approval Status","type":"gauge","description":"Gauges what share of governance policies have completed formal approval.","i":14},{"id":"v190-c1-111-19","title":"Conflict and Independence Controls","type":"funnel","description":"Tracks conflict-of-interest declarations from required through to confirmed and cleared.","i":18},{"id":"v190-c1-111-22","title":"Governance Records Readiness","type":"matrix","description":"Grids how ready governance records are for audit against each control area.","i":21},{"id":"v190-c1-111-27","title":"Governance Source Readiness","type":"funnel","description":"Tracks the underlying governance data sources from unread through to fully readable.","i":26},{"id":"v190-c1-111-28","title":"Governance Metric Readiness","type":"lifecycle","description":"Follows governance metrics from unavailable through to fully calculated and ready.","i":27}],"1.2.1":[{"id":"v190-c1-121-01","title":"Strategic Planning Control Coverage","type":"bar","description":"Compares how many strategic planning controls are documented across each planning area.","i":0},{"id":"v190-c1-121-02","title":"Strategic Objective Status","type":"donut","description":"Shows the current status mix of strategic objectives, from drafted to achieved.","i":1},{"id":"v190-c1-121-03","title":"Strategic Target Readiness","type":"funnel","description":"Tracks strategic targets from set through to having a measurable result recorded.","i":2},{"id":"v190-c1-121-04","title":"Plan-to-Review Lifecycle","type":"lifecycle","description":"Follows a strategic plan from drafted through implementation to its formal review.","i":3},{"id":"v190-c1-121-06","title":"Strategic Action Completion","type":"matrix","description":"Grids strategic action completion against each objective or planning area.","i":5},{"id":"v190-c1-121-09","title":"Target versus Actual Profile","type":"bar","description":"Compares planned targets against actual results across strategic objectives.","i":8},{"id":"v190-c1-121-10","title":"Milestone Completion","type":"donut","description":"Shows what share of strategic plan milestones have been completed on time.","i":9},{"id":"v190-c1-121-16","title":"Planning Evidence Completeness","type":"trend","description":"Tracks how complete the supporting evidence for strategic planning has been over time.","i":15},{"id":"v190-c1-121-22","title":"Objective Ownership Coverage","type":"matrix","description":"Grids strategic objectives against whether each one has a clearly named owner.","i":21},{"id":"v190-c1-121-27","title":"Strategy Source Readiness","type":"funnel","description":"Tracks the underlying strategic planning data sources from unread through to readable.","i":26},{"id":"v190-c1-121-28","title":"Strategy Metric Readiness","type":"lifecycle","description":"Follows strategic planning metrics from unavailable through to fully calculated and ready.","i":27}]},"criterion_2":{"overview":[{"id":"v190-c2-overview-01","title":"Corporate Administration Metric Profile","type":"bar","description":"Compares key corporate administration metrics side by side for this criterion.","i":0},{"id":"v190-c2-overview-02","title":"Live Source Availability","type":"donut","description":"Shows what share of the underlying DocTypes and fields are currently readable.","i":1},{"id":"v190-c2-overview-03","title":"Administration System Health","type":"funnel","description":"Tracks how administration records move from raised to fully resolved across the system.","i":2},{"id":"v190-c2-overview-04","title":"People-to-Feedback Lifecycle","type":"lifecycle","description":"Maps the stages a people record passes through on its way to feedback closure.","i":3},{"id":"v190-c2-overview-05","title":"Corporate Exception Funnel","type":"radar","description":"Highlights where corporate administration exceptions are concentrated across different areas.","i":4},{"id":"v190-c2-overview-06","title":"Evidence Readiness Matrix","type":"matrix","description":"Grids evidence completeness against each corporate administration control area.","i":5}],"2.1.1":[{"id":"v190-c2-211-01","title":"Staff Selection and Management Coverage","type":"bar","description":"Compares how many staff selection and management controls are covered across each area.","i":0},{"id":"v190-c2-211-02","title":"Staff Lifecycle Status","type":"donut","description":"Shows the current status mix of staff records, from onboarding to exit.","i":1},{"id":"v190-c2-211-04","title":"Workforce Control Readiness","type":"lifecycle","description":"Follows workforce controls from unverified through to fully in place and ready.","i":3}],"2.1.2":[{"id":"v190-c2-212-01","title":"Training and Development Coverage","type":"bar","description":"Compares how many staff have documented training and development coverage.","i":0},{"id":"v190-c2-212-02","title":"Training Status Distribution","type":"donut","description":"Shows the current status mix of staff training records, from planned to completed.","i":1},{"id":"v190-c2-212-11","title":"Development Action Completion","type":"funnel","description":"Tracks development actions from identified through to closed out.","i":10}],"2.2.1":[{"id":"v190-c2-221-01","title":"Communication Control Coverage","type":"bar","description":"Compares how many communication controls are documented across internal and external channels.","i":0},{"id":"v190-c2-221-02","title":"Communication Status Distribution","type":"donut","description":"Shows the current status mix of communication records, from draft to published.","i":1},{"id":"v190-c2-221-11","title":"Communication Record Completeness","type":"funnel","description":"Tracks what share of communication records are fully and correctly documented.","i":10}],"2.3.1":[{"id":"v190-c2-231-01","title":"Data Management Control Coverage","type":"bar","description":"Compares how many data management controls are in place across this area.","i":0},{"id":"v190-c2-231-02","title":"Data Control Status","type":"donut","description":"Shows the current status mix of data control records, from open to resolved.","i":1},{"id":"v190-c2-231-04","title":"Data Quality Readiness","type":"lifecycle","description":"Follows data quality checks from unverified through to confirmed clean.","i":3}],"2.3.2":[{"id":"v190-c2-232-01","title":"Knowledge Management Coverage","type":"bar","description":"Compares how many knowledge management controls are covered across this area.","i":0},{"id":"v190-c2-232-02","title":"Knowledge Asset Status","type":"donut","description":"Shows the current status mix of knowledge assets, from draft to published.","i":1},{"id":"v190-c2-232-04","title":"Knowledge Repository Readiness","type":"lifecycle","description":"Follows the knowledge repository from incomplete through to confirmed ready.","i":3}],"2.4.1":[{"id":"v190-c2-241-01","title":"Feedback Management Coverage","type":"bar","description":"Compares how many feedback management controls are covered across this area.","i":0},{"id":"v190-c2-241-02","title":"Feedback Status Distribution","type":"donut","description":"Shows the current status mix of feedback records, from received to closed.","i":1},{"id":"v190-c2-241-11","title":"Improvement Action Linkage","type":"funnel","description":"Tracks improvement actions raised from feedback through to implementation.","i":10}],"2.4.2":[{"id":"v190-c2-242-01","title":"Student Survey Coverage","type":"bar","description":"Compares how many student satisfaction surveys have documented coverage.","i":0},{"id":"v190-c2-242-02","title":"Student Survey Status","type":"donut","description":"Shows the current status mix of student surveys, from open to completed.","i":1},{"id":"v190-c2-242-04","title":"Student Satisfaction Readiness","type":"lifecycle","description":"Follows student satisfaction readiness from unverified through to confirmed complete.","i":3}],"2.4.3":[{"id":"v190-c2-243-01","title":"Staff Survey Coverage","type":"bar","description":"Compares how many staff satisfaction surveys have documented coverage.","i":0},{"id":"v190-c2-243-02","title":"Staff Survey Status","type":"donut","description":"Shows the current status mix of staff surveys, from open to completed.","i":1},{"id":"v190-c2-243-04","title":"Staff Satisfaction Readiness","type":"lifecycle","description":"Follows staff satisfaction readiness from unverified through to confirmed complete.","i":3}]},"criterion_3":{"overview":[{"id":"v190-c3-overview-01","title":"Agent Lifecycle Coverage","type":"bar","description":"Compares agent lifecycle stages side by side across all recruitment agents.","i":0},{"id":"v190-c3-overview-02","title":"Policy Control Coverage","type":"donut","description":"Shows what share of agent-related policy controls are currently in place.","i":1},{"id":"v190-c3-overview-05","title":"Open Exception Profile","type":"radar","description":"Highlights where open exceptions are concentrated across agent management areas.","i":4},{"id":"v190-c3-overview-06","title":"Source Readiness","type":"matrix","description":"Grids source readiness against each area this criterion covers.","i":5},{"id":"v190-c3-overview-07","title":"Agent Portfolio Status","type":"gauge","description":"Gauges how the current agent portfolio is distributed by status.","i":6},{"id":"v190-c3-overview-10","title":"Agent NDA Coverage","type":"donut","description":"Shows the share of agents with a completed NDA on file.","i":9},{"id":"v190-c3-overview-20","title":"Agent Evidence Completeness","type":"lifecycle","description":"Follows agent evidence records from incomplete through to fully documented.","i":19},{"id":"v190-c3-overview-28","title":"Agent Target Achievement","type":"lifecycle","description":"Tracks agents from recruitment target set through to achieved.","i":27}],"3.1.1":[{"id":"v190-c3-311-01","title":"Identification Pathways","type":"bar","description":"Compares how agent candidates were identified across each sourcing pathway.","i":0},{"id":"v190-c3-311-02","title":"Selection and Screening Funnel","type":"donut","description":"Tracks candidate agents from initial screening through to selection.","i":1},{"id":"v190-c3-311-05","title":"Approval and Background Check","type":"radar","description":"Follows candidate agents from approval through to a completed background check.","i":4},{"id":"v190-c3-311-06","title":"Contract and NDA Readiness","type":"matrix","description":"Gauges how ready contract and NDA documentation is for new agents.","i":5},{"id":"v190-c3-311-07","title":"Agent Listing and Status","type":"gauge","description":"Gauges how the current agent listing is distributed by status.","i":6},{"id":"v190-c3-311-12","title":"Due-Diligence Evidence","type":"lifecycle","description":"Follows due-diligence evidence from missing through to fully documented.","i":11},{"id":"v190-c3-311-15","title":"Selection Rating Completeness","type":"gauge","description":"Gauges what share of candidate agents have a completed selection rating.","i":14},{"id":"v190-c3-311-20","title":"Contract Signature Coverage","type":"lifecycle","description":"Gauges what share of agent contracts have a completed signature.","i":19},{"id":"v190-c3-311-22","title":"NDA Completion Status","type":"matrix","description":"Gauges what share of required agent NDAs have been completed.","i":21},{"id":"v190-c3-311-27","title":"Selection Source Readiness","type":"funnel","description":"Tracks the underlying selection data sources from unread through to readable.","i":26},{"id":"v190-c3-311-28","title":"Selection Metric Readiness","type":"lifecycle","description":"Follows selection metrics from unavailable through to fully calculated and ready.","i":27}],"3.2.1":[{"id":"v190-c3-321-01","title":"Agent Onboarding Funnel","type":"bar","description":"Tracks agents from onboarding start through to onboarding completion.","i":0},{"id":"v190-c3-321-02","title":"Training Coverage","type":"donut","description":"Shows what share of active agents have completed required training.","i":1},{"id":"v190-c3-321-03","title":"Service Delivery Controls","type":"funnel","description":"Gauges how many service delivery controls are in place for active agents.","i":2},{"id":"v190-c3-321-04","title":"Performance Evaluation Distribution","type":"lifecycle","description":"Shows how agent performance evaluations are distributed across ratings.","i":3},{"id":"v190-c3-321-06","title":"Complaints and Breaches","type":"matrix","description":"Grids complaints and breaches against each responsible agent.","i":5},{"id":"v190-c3-321-15","title":"Contract Renewal Coverage","type":"gauge","description":"Gauges what share of agent contracts have been renewed on time.","i":14},{"id":"v190-c3-321-17","title":"Provider Rating Outcomes","type":"bar","description":"Compares agent performance against their provider rating outcomes.","i":16},{"id":"v190-c3-321-22","title":"Monitoring Record Coverage","type":"matrix","description":"Grids monitoring record coverage against each active agent.","i":21},{"id":"v190-c3-321-26","title":"Offboarding Completion","type":"donut","description":"Shows what share of agent offboarding processes have been completed.","i":25},{"id":"v190-c3-321-27","title":"Evaluation Source Readiness","type":"funnel","description":"Tracks the underlying evaluation data sources from unread through to readable.","i":26},{"id":"v190-c3-321-28","title":"Evaluation Metric Readiness","type":"lifecycle","description":"Follows evaluation metrics from unavailable through to fully calculated and ready.","i":27}]},"criterion_4":{"overview":[{"id":"c4-overview-flow","title":"Student Protection Control Flow","type":"lifecycle","description":"Follows the principal student-protection controls from admission through attendance and support.","i":0},{"id":"c4-overview-exceptions","title":"Open Exception Profile","type":"ladder","description":"Highlights the live Criterion 4 exceptions requiring follow-up.","i":1},{"id":"c4-overview-readiness","title":"Student Control Readiness","type":"radar","description":"Compares readiness across the main student protection and support controls.","i":2}],"4.1.1":[{"id":"c411-applicants-year","title":"No. of Student Applicants per Year","type":"admission-line","description":"Counts all Student Applicant records grouped by academic year.","dataKey":"applicants_by_year","metricId":"c411-applicants-total"},{"id":"c411-enrolled-year","title":"No. of Enrolled Students per Year","type":"admission-line","description":"Counts Student Applicant records with application status Admitted, grouped by academic year.","dataKey":"enrolled_by_year","metricId":"c411-enrolled-admitted"},{"id":"c411-applicants-country","title":"Applicants per Country","type":"admission-column","description":"Counts Student Applicant records grouped by nationality or country.","dataKey":"applicants_by_country","metricId":"c411-applicants-total"},{"id":"c411-counselling-duration","title":"Duration from Counselling to Admission","type":"admission-line","description":"Average calendar days from pre-course counselling to student signature, grouped by applicant academic year.","dataKey":"counselling_to_admission","metricId":"c411-enrolled-admitted"},{"id":"c411-popular-programmes","title":"Popular Courses of Full Qualification","type":"admission-column","description":"Counts Student Applicant records grouped by programme.","dataKey":"programmes","metricId":"c411-applicants-total"},{"id":"c411-students-agent","title":"Number of Students per Agent","type":"donut","description":"Counts Student Applicant records grouped by recruitment agent, following the supplied Metabase calculation.","dataKey":"agents","metricId":"c411-applicants-total"}],"4.2.1":[{"id":"c4-421-contract","title":"Student Contract Lifecycle","type":"lifecycle","description":"Follows contract preparation, signature, invoicing and full execution.","i":0},{"id":"c4-421-readiness","title":"Student Contract Readiness","type":"radar","description":"Compares the evidence required for an executed student contract.","i":1},{"id":"c4-421-aging","title":"Contract Follow-up Ladder","type":"ladder","description":"Prioritises contract cases requiring follow-up.","i":2}],"4.2.2":[{"id":"c4-422-reconciliation","title":"Fee and FPS Reconciliation","type":"reconciliation","description":"Reconciles invoices, payments, FPS records and fee-protection controls.","i":0},{"id":"c4-422-flow","title":"Fee and FPS Processing Flow","type":"lifecycle","description":"Follows fee processing from invoice through protection and reconciliation.","i":1},{"id":"c4-422-exceptions","title":"Fee-Control Exception Profile","type":"ladder","description":"Shows fee and protection issues requiring review.","i":2}],"4.3.1":[{"id":"c4-431-decision","title":"Course Movement Decision Path","type":"decision","description":"Shows transfer, deferment and withdrawal cases by decision path.","i":0},{"id":"c4-431-mix","title":"Course Movement Request Mix","type":"donut","description":"Compares the current mix of student movement requests.","i":1},{"id":"c4-431-timing","title":"Movement Processing Timeliness","type":"ladder","description":"Prioritises movement cases according to processing status.","i":2}],"4.4.1":[{"id":"c4-441-decision","title":"Refund Decision Path","type":"decision","description":"Shows refund requests from eligibility through approval and payment.","i":0},{"id":"c4-441-outcomes","title":"Refund Request Outcomes","type":"funnel","description":"Tracks refund requests through completion.","i":1},{"id":"c4-441-aging","title":"Refund Follow-up Ladder","type":"ladder","description":"Prioritises open and overdue refund cases.","i":2}],"4.5.1":[{"id":"c4-451-network","title":"Student Support Service Network","type":"network","description":"Maps the live channels and records supporting student interventions.","i":0},{"id":"c4-451-channels","title":"Student Support Channel Mix","type":"donut","description":"Compares support activity across the available channels.","i":1},{"id":"c4-451-followup","title":"Student Support Follow-up Flow","type":"ladder","description":"Shows follow-up controls from service coverage through outcome review.","i":2}],"4.6.1":[{"id":"c4-461-lifecycle","title":"Attendance Intervention Lifecycle","type":"lifecycle","description":"Follows attendance records through risk identification and intervention.","i":0},{"id":"c4-461-risk","title":"Attendance Risk Profile","type":"radar","description":"Compares attendance, leave, warning and intervention evidence.","i":1},{"id":"c4-461-response","title":"Attendance Intervention Response","type":"ladder","description":"Shows intervention controls in follow-up order.","i":2}]},"criterion_5":{"overview":[{"id":"c5-overview-readiness","title":"Academic System Readiness","type":"bar","description":"Compares the live academic-system metrics returned for the selected Criterion 5 area.","i":0},{"id":"c5-overview-availability","title":"Source Availability","type":"donut","description":"Shows readable sources, source issues, readable metrics and metric issues.","i":1},{"id":"c5-overview-health","title":"Criterion 5 System Health","type":"matrix","description":"Summarises available metrics, unavailable metrics, sources and exceptions.","i":2},{"id":"c5-overview-exceptions","title":"Criterion 5 Exception Profile","type":"funnel","description":"Highlights live exceptions that require academic or data-quality follow-up.","i":3}],"5.1.1":[{"id":"c5-511-coverage","title":"Course Design Control Coverage","type":"bar","description":"Compares course proposal, module design, programme mapping and assessment-plan evidence.","i":0},{"id":"c5-511-status","title":"Course Design Status Distribution","type":"donut","description":"Shows available design metrics, source readiness and exceptions.","i":1},{"id":"c5-511-readiness","title":"Course Design Evidence Readiness","type":"radar","description":"Compares readiness across the main course design and development controls.","i":2},{"id":"c5-511-gaps","title":"Course Design Gap Profile","type":"funnel","description":"Highlights course design controls that require follow-up.","i":3}],"5.1.2":[{"id":"c5-512-coverage","title":"Course Review Control Coverage","type":"bar","description":"Compares module review, course review, approval and recommendation evidence.","i":0},{"id":"c5-512-status","title":"Course Review Status Distribution","type":"donut","description":"Shows review source and metric readiness.","i":1},{"id":"c5-512-cycle","title":"Course Review Lifecycle","type":"lifecycle","description":"Follows review evidence from recorded through approval and recommendation follow-up.","i":2},{"id":"c5-512-gaps","title":"Review Exception Profile","type":"funnel","description":"Highlights overdue or incomplete review controls.","i":3}],"5.2.1":[{"id":"c5-521-coverage","title":"Course Planning Control Coverage","type":"bar","description":"Compares intake, module class, schedule and student-contract planning evidence.","i":0},{"id":"c5-521-status","title":"Course Planning Status Distribution","type":"donut","description":"Shows planning source and metric readiness.","i":1},{"id":"c5-521-flow","title":"Planning Readiness Flow","type":"lifecycle","description":"Follows planning evidence from intake through class, schedule and contract readiness.","i":2},{"id":"c5-521-gaps","title":"Planning Exception Profile","type":"funnel","description":"Highlights incomplete planning controls requiring follow-up.","i":3}],"5.2.2":[{"id":"c5-522-coverage","title":"Course Delivery Control Coverage","type":"bar","description":"Compares schedules, attendance, observations and sign-off evidence.","i":0},{"id":"c5-522-status","title":"Course Delivery Status Distribution","type":"donut","description":"Shows delivery source and metric readiness.","i":1},{"id":"c5-522-readiness","title":"Delivery Evidence Readiness","type":"radar","description":"Compares attendance, observation and sign-off evidence across delivery controls.","i":2},{"id":"c5-522-gaps","title":"Delivery Exception Profile","type":"funnel","description":"Highlights delivery controls requiring follow-up.","i":3}],"5.3.1":[{"id":"c5-531-coverage","title":"Partnership Control Coverage","type":"bar","description":"Compares agreement, monitoring, evaluation and provider-rating evidence.","i":0},{"id":"c5-531-status","title":"Partnership Status Distribution","type":"donut","description":"Shows partnership source and metric readiness.","i":1},{"id":"c5-531-risk","title":"Partnership Risk Profile","type":"funnel","description":"Highlights expiry, NDA and threshold risks requiring follow-up.","i":2},{"id":"c5-531-readiness","title":"Partnership Evidence Readiness","type":"matrix","description":"Grids readiness across partnership management controls.","i":3}],"5.4":[{"id":"c5-54-coverage","title":"Student Feedback Control Coverage","type":"bar","description":"Compares survey, score and attendance-risk evidence.","i":0},{"id":"c5-54-status","title":"Student Feedback Status Distribution","type":"donut","description":"Shows feedback source and metric readiness.","i":1},{"id":"c5-54-readiness","title":"Feedback Evidence Readiness","type":"radar","description":"Compares survey and learning-support evidence across key controls.","i":2},{"id":"c5-54-gaps","title":"Feedback Exception Profile","type":"funnel","description":"Highlights feedback controls requiring follow-up.","i":3}],"5.5":[{"id":"c5-55-coverage","title":"Assessment Control Coverage","type":"bar","description":"Compares assessment plans, control fields, results, grades and scores.","i":0},{"id":"c5-55-status","title":"Assessment Status Distribution","type":"donut","description":"Shows assessment source and metric readiness.","i":1},{"id":"c5-55-readiness","title":"Assessment Evidence Readiness","type":"radar","description":"Compares readiness across assessment planning and result controls.","i":2},{"id":"c5-55-gaps","title":"Assessment Exception Profile","type":"funnel","description":"Highlights assessment controls requiring correction or follow-up.","i":3}]},"criterion_6":{"overview":[{"id":"v190-c6-overview-02","title":"Policy Evidence Coverage","type":"donut","description":"Shows what share of quality policies have documented supporting evidence.","i":1},{"id":"v190-c6-overview-04","title":"Quality Calendar Completion","type":"lifecycle","description":"Gauges how much of the planned quality calendar has been completed.","i":3},{"id":"v190-c6-overview-06","title":"Source Readiness","type":"matrix","description":"Grids source readiness against each quality assurance area this criterion covers.","i":5},{"id":"v190-c6-overview-14","title":"Quality Evidence Completeness","type":"matrix","description":"Follows quality evidence records from incomplete through to fully documented.","i":13},{"id":"v190-c6-overview-16","title":"Overall Criterion Readiness","type":"trend","description":"Summarises how ready Criterion 6 is overall, from raw data through to verified evidence.","i":15}],"6.1.1":[{"id":"v190-c6-611-01","title":"Annual Audit Programme","type":"bar","description":"Compares planned audits against the annual audit programme.","i":0},{"id":"v190-c6-611-02","title":"Audit Scope Coverage","type":"donut","description":"Shows how audit scope is distributed across the areas covered.","i":1},{"id":"v190-c6-611-05","title":"Audit Findings by Severity","type":"radar","description":"Compares audit findings by severity across recent audits.","i":4},{"id":"v190-c6-611-06","title":"Corrective Action Closure","type":"matrix","description":"Grids corrective action closure against each audit finding raised.","i":5},{"id":"v190-c6-611-16","title":"Audit Source Readiness","type":"trend","description":"Tracks the underlying audit data sources from unread through to fully readable.","i":15}],"6.2.1":[{"id":"v190-c6-621-01","title":"THESIS Review Coverage","type":"bar","description":"Compares THESIS review inputs covered against the required agenda items.","i":0},{"id":"v190-c6-621-03","title":"Review Input Completeness","type":"funnel","description":"Follows management review input completeness from partial through to full.","i":2},{"id":"v190-c6-621-04","title":"Review Outputs","type":"lifecycle","description":"Follows management review outputs from raised through to implemented.","i":3},{"id":"v190-c6-621-07","title":"Review Status Distribution","type":"gauge","description":"Shows how management review meetings are distributed across their status.","i":6},{"id":"v190-c6-621-16","title":"Management Review Source Readiness","type":"trend","description":"Tracks the underlying management review data sources from unread through to readable.","i":15}],"6.3.1":[{"id":"v190-c6-631-01","title":"Innovation Type Mix","type":"bar","description":"Compares how innovation initiatives are distributed across their type.","i":0},{"id":"v190-c6-631-02","title":"Improvement Initiative Lifecycle","type":"donut","description":"Follows an improvement initiative from proposed through to implemented.","i":1},{"id":"v190-c6-631-06","title":"Improvement Action Status","type":"matrix","description":"Grids improvement action status against each initiative raised.","i":5},{"id":"v190-c6-631-08","title":"Implementation Progress","type":"trend","description":"Tracks how much implementation progress has been made across initiatives.","i":7},{"id":"v190-c6-631-16","title":"Innovation Source Readiness","type":"trend","description":"Tracks the underlying innovation data sources from unread through to readable.","i":15}],"6.4.1":[{"id":"v190-c6-641-01","title":"Provider Tier Profile","type":"bar","description":"Compares how providers are distributed across their accreditation tier.","i":0},{"id":"v190-c6-641-02","title":"Provider Accreditation Funnel","type":"donut","description":"Tracks providers from application through to accreditation approval.","i":1},{"id":"v190-c6-641-06","title":"Provider Evaluation Outcomes","type":"matrix","description":"Shows what share of provider evaluations resulted in a positive outcome.","i":5},{"id":"v190-c6-641-11","title":"Rating Completeness","type":"funnel","description":"Gauges what share of provider ratings have been fully completed.","i":10},{"id":"v190-c6-641-16","title":"Provider Source Readiness","type":"trend","description":"Tracks the underlying provider data sources from unread through to readable.","i":15}],"6.5.3":[{"id":"v190-c6-653-01","title":"Hazard Reporting Funnel","type":"bar","description":"Tracks hazards from reported through to fully assessed.","i":0},{"id":"v190-c6-653-02","title":"Risk Level Distribution","type":"donut","description":"Shows how identified risks are distributed across severity levels.","i":1},{"id":"v190-c6-653-03","title":"5×5 Risk Matrix","type":"funnel","description":"Grids likelihood against impact across the full 5x5 risk matrix.","i":2},{"id":"v190-c6-653-07","title":"Risk Assessment Coverage","type":"gauge","description":"Compares how many risk assessments have been completed across areas.","i":6},{"id":"v190-c6-653-16","title":"Risk Source Readiness","type":"trend","description":"Tracks the underlying risk data sources from unread through to fully readable.","i":15}]},"criterion_7":{"overview":[{"id":"v190-c7-overview-02","title":"Live Source Availability","type":"donut","description":"Shows what share of the underlying DocTypes and fields are currently readable.","i":1},{"id":"v190-c7-overview-06","title":"Outcome Evidence Readiness","type":"matrix","description":"Grids evidence completeness against each outcome area this criterion covers.","i":5},{"id":"v190-c7-overview-08","title":"Target Availability","type":"trend","description":"Tracks how many indicators have a defined target over recent periods.","i":7},{"id":"v190-c7-overview-09","title":"Actual Result Availability","type":"bar","description":"Compares how many indicators have an actual result recorded.","i":8},{"id":"v190-c7-overview-10","title":"Target Achievement","type":"donut","description":"Shows the share of indicators that have achieved their set target.","i":9},{"id":"v190-c7-overview-11","title":"Target Variance","type":"funnel","description":"Tracks the variance between target and actual results across indicators.","i":10},{"id":"v190-c7-overview-14","title":"Outcome Review Status","type":"matrix","description":"Grids outcome review status against each area being measured.","i":13},{"id":"v190-c7-overview-28","title":"Underperforming Indicators","type":"lifecycle","description":"Follows underperforming indicators from flagged through to addressed.","i":27},{"id":"v190-c7-overview-29","title":"Missing Measurements","type":"radar","description":"Compares where measurements are missing across tracked indicators.","i":28},{"id":"v190-c7-overview-34","title":"Outcome Action Status","type":"donut","description":"Shows the status mix of actions raised against underperforming outcomes.","i":33},{"id":"v190-c7-overview-35","title":"Outcome Source Readiness","type":"funnel","description":"Tracks the underlying outcome data sources from unread through to readable.","i":34},{"id":"v190-c7-overview-40","title":"Overall Criterion Readiness","type":"trend","description":"Summarises how ready Criterion 7 is overall, from raw data through to verified evidence.","i":39}],"7.1.1":[{"id":"v190-c7-711-01","title":"Measurement Control Coverage","type":"bar","description":"Compares how many measurement controls are documented across outcome areas.","i":0},{"id":"v190-c7-711-02","title":"Measurement Status Distribution","type":"donut","description":"Shows the current status mix of outcome measurements, from open to resolved.","i":1},{"id":"v190-c7-711-03","title":"Indicator Definition Coverage","type":"funnel","description":"Tracks how many indicators have a complete, documented definition.","i":2},{"id":"v190-c7-711-04","title":"Indicator Ownership Coverage","type":"lifecycle","description":"Compares how many indicators have a clearly assigned owner.","i":3},{"id":"v190-c7-711-05","title":"Target Definition Coverage","type":"radar","description":"Compares how many indicators have a documented target definition.","i":4},{"id":"v190-c7-711-06","title":"Actual Result Coverage","type":"matrix","description":"Grids actual result coverage against each defined indicator.","i":5},{"id":"v190-c7-711-08","title":"Target Achievement Gauge","type":"trend","description":"Gauges what share of indicators have achieved their set target.","i":7},{"id":"v190-c7-711-09","title":"Target Variance Profile","type":"bar","description":"Compares target-versus-actual variance across defined indicators.","i":8},{"id":"v190-c7-711-12","title":"Benchmark Readiness","type":"lifecycle","description":"Gauges how ready indicators are for benchmark comparison.","i":11},{"id":"v190-c7-711-14","title":"Underperformance Profile","type":"matrix","description":"Grids underperformance against each indicator falling short of target.","i":13},{"id":"v190-c7-711-15","title":"Missing Result Profile","type":"gauge","description":"Gauges what share of indicators are missing a recorded result.","i":14},{"id":"v190-c7-711-16","title":"Review Completion","type":"trend","description":"Gauges how many scheduled outcome reviews have been completed.","i":15},{"id":"v190-c7-711-17","title":"Improvement Action Coverage","type":"bar","description":"Compares how many underperforming outcomes have a linked improvement action.","i":16},{"id":"v190-c7-711-31","title":"Measurement Source Readiness","type":"gauge","description":"Gauges how readable the underlying measurement data sources currently are.","i":30},{"id":"v190-c7-711-32","title":"Measurement Metric Readiness","type":"trend","description":"Tracks how ready measurement metrics are, from unavailable to calculated.","i":31},{"id":"v190-c7-711-36","title":"Outcome Action Closure","type":"lifecycle","description":"Follows outcome actions from raised through to formally closed.","i":35},{"id":"v190-c7-711-37","title":"Evidence Completeness","type":"radar","description":"Tracks how complete supporting evidence is across measured outcomes.","i":36},{"id":"v190-c7-711-38","title":"Data Quality Profile","type":"matrix","description":"Grids data quality checks against each outcome measurement area.","i":37}]}};
window.UCCLiveVisualDefinitions=LIVE_VISUAL_EXPANSION;
Object.keys(LIVE_VISUAL_EXPANSION).forEach(function(criterion){const config=CONFIG[criterion];if(!config)return;Object.keys(LIVE_VISUAL_EXPANSION[criterion]).forEach(function(section){config.sections[section]=config.sections[section]||{title:section,charts:[]};config.sections[section].configCharts=config.sections[section].charts;config.sections[section].charts=LIVE_VISUAL_EXPANSION[criterion][section];});});
function esc(value){return String(value==null?"":value).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");}

function normaliseFilterDefinition(raw){
if(Array.isArray(raw))return{key:raw[0],label:raw[1],options:Array.isArray(raw[2])?raw[2]:[],type:raw[0]==="month"?"month":"select"};
return{key:raw?.key||"filter",label:raw?.label||raw?.key||"Filter",options:Array.isArray(raw?.options)?raw.options:[],type:raw?.type||"text",placeholder:raw?.placeholder||""};
}
function filterMarkup(raw,index,criterionId){
const filter=normaliseFilterDefinition(raw),id=`ucc-${criterionId}-${filter.key}-${index}`;
if(filter.type==="month")return`<div><label for="${esc(id)}">${esc(filter.label)}</label><input id="${esc(id)}" data-demo-filter="${esc(filter.key)}" type="month"></div>`;
if(filter.type==="select"&&filter.options.length){
const options=filter.options.map((option,optionIndex)=>{const label=Array.isArray(option)?option[1]:option;const value=Array.isArray(option)?option[0]:(optionIndex===0?"":option);return`<option value="${esc(value)}">${esc(label)}</option>`;}).join("");
return`<div><label for="${esc(id)}">${esc(filter.label)}</label><select id="${esc(id)}" data-demo-filter="${esc(filter.key)}">${options}</select></div>`;
}
return`<div><label for="${esc(id)}">${esc(filter.label)}</label><input id="${esc(id)}" data-demo-filter="${esc(filter.key)}" type="text" placeholder="${esc(filter.placeholder||`All ${filter.label}`)}"></div>`;
}
function analyticsPanelMarkup(criterionId,key,title){
const isOverview=key==="overview",code=isOverview?"OVERVIEW":key;
return`<section class="panel-view${isOverview?"":" hidden"}" data-demo-panel="${esc(key)}"><div class="section-heading"><div><div class="section-code">${esc(code)}</div><h2>${esc(title)}</h2><p>Permission-aware live evidence, visual analysis and management questions.</p></div></div><div class="ucc-section-visual-anchor" data-live-anchor="${esc(key)}"></div><article class="panel ucc-shared-panel ucc-management-panel"><div class="panel-head"><h2>Management Questions and Data-Based Answers</h2></div><div class="table-wrap"><table class="qa-table"><thead><tr><th>Criterion</th><th>Question</th><th>Answer</th><th>Source / Calculation</th><th>Status</th></tr></thead><tbody data-demo-qa="${esc(criterionId+":"+key)}"></tbody></table></div></article></section>`;
}
function sourcesQualityPanelMarkup(criterionId){
return`<section class="panel-view hidden ucc-sources-quality-panel" data-demo-panel="sources"><div class="ucc-sources-quality-grid"><article class="panel ucc-shared-panel"><div class="panel-head"><div><h2>Source Availability</h2><p class="panel-subtitle">Resolved against the signed-in user's permissions.</p></div></div><div class="table-wrap"><table><thead><tr><th>Resolved DocType</th><th>Source key</th><th>Status</th><th>Records</th></tr></thead><tbody data-demo-sources="${esc(criterionId)}"></tbody></table></div></article><article class="panel ucc-shared-panel"><div class="panel-head"><div><h2>Data Quality Checks</h2><p class="panel-subtitle">Unavailable sources, permissions and unsupported fields are shown explicitly.</p></div></div><div class="table-wrap"><table><thead><tr><th>Check</th><th>Source</th><th>Status</th><th>Detail</th></tr></thead><tbody data-demo-quality="${esc(criterionId)}"></tbody></table></div></article></div></section>`;
}
function dashboardShellMarkup(criterionId,config){
const filters=(config.filters||[]).map((filter,index)=>filterMarkup(filter,index,criterionId)).join("");
const tabs=[['overview','Overview']].concat(config.subcriteria||[]).concat([['sources','Sources & Data Quality']]);
const tabMarkup=tabs.map((item,index)=>`<button type="button" class="${index===0?"active":""}" data-demo-tab="${esc(item[0])}">${esc(item[0]==="overview"||item[0]==="sources"?item[1]:item[0]+" "+item[1])}</button>`).join("");
const panels=[analyticsPanelMarkup(criterionId,'overview',config.sections?.overview?.title||'Overview')].concat((config.subcriteria||[]).map(item=>analyticsPanelMarkup(criterionId,item[0],item[1]))).join("")+sourcesQualityPanelMarkup(criterionId);
return`<div class="ucc-unified-dashboard"><div class="loading-overlay hidden" data-demo-loading-overlay><div class="loading-card"><div class="spinner"></div><strong data-demo-loading-title>Loading Criterion ${esc(config.number)}</strong><div class="progress-track"><div class="progress-fill" data-demo-progress-fill></div></div><div class="progress-text"><span data-demo-progress-value>0%</span> · <span>Permission-aware sources</span></div></div></div><header class="hero ucc-shared-hero ucc-standard-criterion-hero"><div class="hero-copy"><span class="ucc-criterion-kicker">EDUTRUST CRITERION ${esc(config.number)}</span><h1>Criterion ${esc(config.number)} · ${esc(config.title)}</h1><p>${esc(config.description)}</p></div><div class="hero-action-card ucc-shared-action-card ucc-standard-hero-actions" aria-label="Criterion ${esc(config.number)} analytics actions"><button type="button" class="primary-btn" data-demo-action="refresh">Refresh</button><button type="button" data-demo-action="export-qa">Export Q&amp;A CSV</button><button type="button" data-demo-action="export-exceptions">Export Exceptions CSV</button><button type="button" data-demo-action="diagnostics">Diagnostics Log (<span data-demo-log-count>0</span>)</button></div></header><div class="sticky-navigation"><section class="controls ucc-shared-controls"><div class="control-grid">${filters}</div></section><nav class="tabs ucc-shared-tabs" data-demo-tabs aria-label="Criterion ${esc(config.number)} sections">${tabMarkup}</nav></div><div class="ucc-criterion-notice ucc-readiness-strip" data-demo-readiness data-status="loading"><div class="ucc-criterion-notice-copy"><strong data-demo-readiness-title>Loading Criterion ${esc(config.number)} analytics…</strong><span data-demo-readiness-copy>Current-user permissions and live sources are being checked.</span></div><div class="ucc-readiness-actions"><button type="button" class="ucc-readiness-detail" data-demo-action="readiness">View readiness</button><button type="button" class="ucc-notice-dismiss" data-demo-action="dismiss-readiness" aria-label="Dismiss Criterion ${esc(config.number)} readiness notification" title="Dismiss">×</button></div></div><section class="kpis ucc-shared-kpis" data-demo-kpis></section><div class="ucc-unified-panel-stack">${panels}</div></div>`;
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
function sectionDefinition(config,tab){const key=(config.panelMap&&config.panelMap[tab])||tab;return config.sections[tab]||config.sections[key]||config.sections.overview;}
function liveChartCardMarkup(chart){
return`<article class="panel ucc-shared-panel ucc-demo-visual-card ucc-live-generated-card ucc-standard-functional-card" data-demo-card="${esc(chart.id)}"><div class="panel-head ucc-card-header"><div class="ucc-card-heading-copy"><h2>${esc(chart.title)}</h2><p class="ucc-card-description">${esc(chart.description||"Permission-aware live metrics.")}</p></div><div class="mini-toggle ucc-card-view-toggle" data-demo-view-toggle="${esc(chart.id)}"><button type="button" class="active" data-demo-view="diagram">Diagram</button><button type="button" data-demo-view="table">Table</button></div></div><div class="chart ucc-demo-chart" data-demo-chart="${esc(chart.id)}" data-demo-chart-title="${esc(chart.title)}" data-demo-chart-type="${esc(chart.type||"bar")}"></div><div class="table-wrap hidden" data-demo-chart-table="${esc(chart.id)}"><table><thead><tr><th>Metric</th><th>Live value</th><th>Status</th></tr></thead><tbody data-demo-chart-table-body="${esc(chart.id)}"></tbody></table></div><button type="button" data-demo-drill="${esc(chart.id)}">View underlying records</button></article>`;
}
function panelInsertPoint(panel){
return Array.from(panel.children).find(function(child){return/Management Questions and Data-Based Answers/i.test(child.textContent||"");})||null;
}
// The chart boxes for one tab, from the ONE place that decides them.
//
// LIVE_VISUAL_EXPANSION REPLACES a section's CONFIG charts rather than adding
// to them, and every visible tab has an expansion entry. That silently hid 9
// of the 16 bench-verified Insights charts: their CONFIG entry sits on the
// same tab, shadowed. So the expansion list is used as-is, then any chart the
// tab's own CONFIG defines that has a VERIFIED Insights query is appended.
//
// Only real charts are appended, never the rest of the CONFIG list -- adding
// ~30 more blank boxes to show nothing would be the opposite of the point.
// It is self-maintaining: verify a chart, promote it in chart_registry, and
// its box appears on the tab that already declared it.
function chartsForTab(criterionId,config,sectionKey){
const section=config?.sections?.[sectionKey];
const expanded=LIVE_VISUAL_EXPANSION[criterionId]?.[sectionKey];
if(!expanded)return section?.charts||[];
const shown=new Set(expanded.map(chart=>chart.id));
const verified=(section?.configCharts||[]).filter(chart=>
!shown.has(chart.id)&&chartDefinitions.byId[chart.id]?.definition_status==="real");
return verified.length?expanded.concat(verified):expanded;
}
function ensureLiveSectionCards(dashboard,config,sectionKey){
const definitions=LIVE_VISUAL_EXPANSION[dashboard.dataset.demoDashboard]||{};
if(!sectionKey||!definitions[sectionKey])return;
const panelKey=(config.panelMap&&config.panelMap[sectionKey])||sectionKey;
if(panelKey==="quality"||panelKey==="sources")return;
const panel=dashboard.querySelector(`[data-demo-panel="${CSS.escape(panelKey)}"]`);
if(!panel)return;
let grid=panel.querySelector(`:scope > .ucc-live-expanded-grid[data-live-section="${CSS.escape(sectionKey)}"]`);
if(!grid){
grid=document.createElement("div");
grid.className="grid2 ucc-live-expanded-grid";
grid.dataset.liveSection=sectionKey;
panel.insertBefore(grid,panelInsertPoint(panel));
}
if(!grid.dataset.liveCardsMounted){
grid.innerHTML=chartsForTab(dashboard.dataset.demoDashboard,config,sectionKey).filter(function(chart){return chart.enabled!==false;}).map(liveChartCardMarkup).join("");
// Cards mount synchronously; the chart manifest arrives over the wire. Stay
// unmounted until it lands, or the verified charts chartsForTab() appends
// would be missing from this grid for the rest of the session.
if(chartDefinitions.loaded)grid.dataset.liveCardsMounted="1";
}
}
function ensureLiveVisualCards(dashboard,config){
const definitions=LIVE_VISUAL_EXPANSION[dashboard.dataset.demoDashboard]||{};
dashboard.querySelectorAll(".ucc-demo-visual-card:not(.ucc-live-generated-card)").forEach(function(card){
card.hidden=true;
card.classList.add("ucc-live-base-card");
});
if(!dashboard.classList.contains("ucc-hidden"))ensureLiveSectionCards(dashboard,config,activeSection(dashboard));
}
function syncLiveSectionVisibility(dashboard,tab){
dashboard.querySelectorAll("[data-live-section]").forEach(function(grid){
grid.hidden=grid.dataset.liveSection!==tab;
});
}
function chartMax(rows){return Math.max.apply(null,rows.map(row=>finiteNumber(row[1],0)).concat([1]));}
function renderBars(node,rows){const max=chartMax(rows);node.innerHTML=`<div class="ucc-demo-bars">${rows.map(function(row){return`<div class="ucc-demo-bar"><label>${esc(row[0])}</label><div><i style="width:${Math.max(4,finiteNumber(row[1],0)/max*100)}%"></i></div><strong>${row[1]}${max<=100?"%":""}</strong></div>`;}).join("")}</div>`;}
function renderDonut(node,rows){const total=rows.reduce((sum,row)=>sum+finiteNumber(row[1],0),0)||1;let cursor=0;const stops=rows.map(function(row,index){const start=cursor/total*360;cursor+=finiteNumber(row[1],0);const end=cursor/total*360;return`var(--ucc-chart-${index%6}) ${start}deg ${end}deg`;}).join(",");node.innerHTML=`<div class="ucc-demo-donut-layout"><div class="ucc-demo-donut" style="background:conic-gradient(${stops})"><span>${total}</span><small>Total</small></div><div class="ucc-demo-legend">${rows.map(function(row,index){return`<div><i style="background:var(--ucc-chart-${index%6})"></i><span>${esc(row[0])}</span><strong>${row[1]}</strong></div>`;}).join("")}</div></div>`;}
function renderFunnel(node,rows){const max=chartMax(rows);node.innerHTML=`<div class="ucc-demo-funnel">${rows.map(function(row,index){const width=Math.max(38,finiteNumber(row[1],0)/max*100);return`<div class="ucc-demo-funnel-stage" style="width:${width}%"><span>${esc(row[0])}</span><strong>${row[1]}</strong></div>`;}).join("")}</div>`;}
function renderLifecycle(node,rows){node.innerHTML=`<div class="ucc-demo-lifecycle">${rows.map(function(row,index){return`<div class="ucc-demo-life-step"><i>${index+1}</i><span>${esc(row[0])}</span><strong>${row[1]}</strong></div>${index<rows.length-1?'<b aria-hidden="true">→</b>':""}`;}).join("")}</div>`;}
function renderMatrix(node,rows){const max=chartMax(rows);node.innerHTML=`<div class="ucc-demo-matrix">${rows.map(function(row){const level=Math.max(.18,finiteNumber(row[1],0)/max);return`<div style="--ucc-intensity:${level}"><span>${esc(row[0])}</span><strong>${row[1]}${max<=100?"%":""}</strong></div>`;}).join("")}</div>`;}
function renderRadar(node,rows){const size=320,cx=160,cy=160,radius=105,count=Math.max(rows.length,3),max=chartMax(rows);const points=rows.map(function(row,index){const angle=-Math.PI/2+index*2*Math.PI/count,r=radius*(finiteNumber(row[1],0)/max);return[cx+Math.cos(angle)*r,cy+Math.sin(angle)*r];});const axes=rows.map(function(row,index){const angle=-Math.PI/2+index*2*Math.PI/count,x=cx+Math.cos(angle)*radius,y=cy+Math.sin(angle)*radius,lx=cx+Math.cos(angle)*(radius+28),ly=cy+Math.sin(angle)*(radius+28);return`<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}"></line><text x="${lx}" y="${ly}" text-anchor="middle">${esc(row[0])}</text>`;}).join("");node.innerHTML=`<div class="ucc-demo-radar"><svg viewBox="0 0 ${size} ${size}" role="img" aria-label="Radar diagram"><circle cx="${cx}" cy="${cy}" r="${radius}"></circle><circle cx="${cx}" cy="${cy}" r="${radius*.66}"></circle><circle cx="${cx}" cy="${cy}" r="${radius*.33}"></circle>${axes}<polygon points="${points.map(point=>point.join(",")).join(" ")}"></polygon></svg><div class="ucc-demo-radar-values">${rows.map(row=>`<span>${esc(row[0])}: <strong>${row[1]}</strong></span>`).join("")}</div></div>`;}
function renderTrend(node,rows){const width=560,height=250,pad=38,max=chartMax(rows),step=(width-pad*2)/Math.max(1,rows.length-1);const points=rows.map(function(row,index){return[pad+index*step,height-pad-(finiteNumber(row[1],0)/max)*(height-pad*2)];});node.innerHTML=`<div class="ucc-demo-trend"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Trend diagram"><line class="axis" x1="${pad}" y1="${height-pad}" x2="${width-pad}" y2="${height-pad}"></line><polyline points="${points.map(p=>p.join(",")).join(" ")}"></polyline>${points.map(function(p,index){return`<circle cx="${p[0]}" cy="${p[1]}" r="5"></circle><text x="${p[0]}" y="${height-12}" text-anchor="middle">${esc(rows[index][0])}</text><text class="value" x="${p[0]}" y="${p[1]-10}" text-anchor="middle">${rows[index][1]}</text>`;}).join("")}</svg></div>`;}
function renderGauge(node,rows){const current=finiteNumber(rows[0]?.[1],0),reference=finiteNumber(rows[1]?.[1],current||1),percentage=reference?Math.max(0,Math.min(100,current/reference*100)):0;node.innerHTML=`<div class="ucc-demo-gauge-layout"><div class="ucc-demo-gauge" style="--ucc-gauge:${percentage*1.8}deg"><div><strong>${current}</strong><span>Current</span></div></div><div class="ucc-demo-gauge-copy"><span>Reference metric</span><strong>${reference}</strong><small>${current>=reference?"At or above reference":"Difference "+Math.max(0,reference-current)}</small></div></div>`;}
function renderAdmissionLine(node,rows){
const width=720,height=300,pad={top:32,right:24,bottom:62,left:52},max=Math.max.apply(null,rows.map(row=>finiteNumber(row[1],0)).concat([1])),plotW=width-pad.left-pad.right,plotH=height-pad.top-pad.bottom,step=rows.length>1?plotW/(rows.length-1):0;
const points=rows.map((row,index)=>[pad.left+index*step,pad.top+plotH-(finiteNumber(row[1],0)/max)*plotH]);
const grid=[];for(let i=0;i<=5;i++){const y=pad.top+(plotH/5)*i,value=Math.round(max-(max/5)*i);grid.push(`<line class="grid" x1="${pad.left}" y1="${y}" x2="${width-pad.right}" y2="${y}"></line><text class="axis-label" x="${pad.left-10}" y="${y+4}" text-anchor="end">${value}</text>`);}
node.innerHTML=`<div class="ucc-admission-svg"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(node.dataset.demoChartTitle||"Admission trend")}">${grid.join("")}<line class="axis" x1="${pad.left}" y1="${height-pad.bottom}" x2="${width-pad.right}" y2="${height-pad.bottom}"></line><polyline class="series" points="${points.map(point=>point.join(",")).join(" ")}"></polyline>${points.map((point,index)=>`<circle class="point" cx="${point[0]}" cy="${point[1]}" r="5"></circle><text class="value" x="${point[0]}" y="${point[1]-12}" text-anchor="middle">${rows[index][1]}</text><text class="x-label" x="${point[0]}" y="${height-25}" text-anchor="middle">${esc(rows[index][0])}</text>`).join("")}</svg></div>`;
}
function renderAdmissionColumns(node,rows){
const width=720,height=320,pad={top:28,right:24,bottom:92,left:52},max=Math.max.apply(null,rows.map(row=>finiteNumber(row[1],0)).concat([1])),plotW=width-pad.left-pad.right,plotH=height-pad.top-pad.bottom,gap=12,barW=Math.max(12,(plotW-gap*Math.max(0,rows.length-1))/Math.max(1,rows.length));
const grid=[];for(let i=0;i<=5;i++){const y=pad.top+(plotH/5)*i,value=Math.round(max-(max/5)*i);grid.push(`<line class="grid" x1="${pad.left}" y1="${y}" x2="${width-pad.right}" y2="${y}"></line><text class="axis-label" x="${pad.left-10}" y="${y+4}" text-anchor="end">${value}</text>`);}
node.innerHTML=`<div class="ucc-admission-svg"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(node.dataset.demoChartTitle||"Admission comparison")}">${grid.join("")}<line class="axis" x1="${pad.left}" y1="${height-pad.bottom}" x2="${width-pad.right}" y2="${height-pad.bottom}"></line>${rows.map((row,index)=>{const value=finiteNumber(row[1],0),x=pad.left+index*(barW+gap),barH=(value/max)*plotH,y=pad.top+plotH-barH;return`<rect class="column" x="${x}" y="${y}" width="${barW}" height="${barH}" rx="4"></rect><text class="value" x="${x+barW/2}" y="${Math.max(16,y-9)}" text-anchor="middle">${value}</text><text class="x-label rotated" transform="translate(${x+barW/2},${height-pad.bottom+18}) rotate(-38)" text-anchor="end">${esc(row[0])}</text>`;}).join("")}</svg></div>`;
}
function renderRiskMatrix(node,chart){const values=chart.values||[],likelihood=["Rare","Remote","Occasional","Frequent","Almost Certain"],severity=["Catastrophic","Major","Moderate","Minor","Negligible"];node.innerHTML=`<div class="ucc-demo-risk-matrix"><div class="corner">Severity × Likelihood</div>${likelihood.map(x=>`<div class="head">${x}</div>`).join("")}${severity.map(function(label,row){return`<div class="side">${label}</div>${likelihood.map(function(_,col){const value=values[row*5+col]||0,level=value>=15?"high":value>=4?"medium":"low";return`<div class="${level}"><strong>${value}</strong></div>`;}).join("")}`;}).join("")}</div>`;}
function renderDecision(node,rows){const root=rows[0]||["Decision",0],branches=rows.slice(1);node.innerHTML=`<div class="ucc-plugin-decision"><div class="ucc-plugin-decision-root"><span>${esc(root[0])}</span><strong>${root[1]}</strong></div><div class="ucc-plugin-decision-branches">${branches.map(row=>`<div><span>${esc(row[0])}</span><strong>${row[1]}</strong></div>`).join("")}</div></div>`;}
function renderNetwork(node,rows){const centre=rows[0]||["Network",0],nodes=rows.slice(1);node.innerHTML=`<div class="ucc-plugin-network"><div class="ucc-plugin-network-centre"><span>${esc(centre[0])}</span><strong>${centre[1]}</strong></div><div class="ucc-plugin-network-nodes">${nodes.map(row=>`<div><span>${esc(row[0])}</span><strong>${row[1]}</strong></div>`).join("")}</div></div>`;}
function renderReconciliation(node,rows){node.innerHTML=`<div class="ucc-plugin-reconciliation">${rows.map((row,index)=>`<div><i>${index+1}</i><span>${esc(row[0])}</span><strong>${row[1]}</strong></div>${index<rows.length-1?'<b aria-hidden="true">⇄</b>':""}`).join("")}</div>`;}
function renderLadder(node,rows){node.innerHTML=`<div class="ucc-plugin-ladder">${rows.map((row,index)=>`<div style="--ucc-step:${index}"><i>${index+1}</i><span>${esc(row[0])}</span><strong>${row[1]}</strong></div>`).join("")}</div>`;}
const CHART_PLUGINS=new Map();
function registerChartPlugin(type,renderer){if(type&&typeof renderer==="function")CHART_PLUGINS.set(String(type),renderer);}
registerChartPlugin("bar",(node,rows)=>renderBars(node,rows));
registerChartPlugin("donut",(node,rows)=>renderDonut(node,rows));
registerChartPlugin("funnel",(node,rows)=>renderFunnel(node,rows));
registerChartPlugin("lifecycle",(node,rows)=>renderLifecycle(node,rows));
registerChartPlugin("flow",(node,rows)=>renderLifecycle(node,rows));
registerChartPlugin("matrix",(node,rows)=>renderMatrix(node,rows));
registerChartPlugin("radar",(node,rows)=>renderRadar(node,rows));
registerChartPlugin("trend",(node,rows)=>renderTrend(node,rows));
registerChartPlugin("gauge",(node,rows)=>renderGauge(node,rows));
registerChartPlugin("admission-line",(node,rows)=>renderAdmissionLine(node,rows));
registerChartPlugin("admission-column",(node,rows)=>renderAdmissionColumns(node,rows));
registerChartPlugin("decision",(node,rows)=>renderDecision(node,rows));
registerChartPlugin("network",(node,rows)=>renderNetwork(node,rows));
registerChartPlugin("reconciliation",(node,rows)=>renderReconciliation(node,rows));
registerChartPlugin("ladder",(node,rows)=>renderLadder(node,rows));
registerChartPlugin("risk-matrix",(node,rows,chart)=>{const seed=rows.map(row=>Math.max(0,Math.round(row[1]))),values=[];for(let i=0;i<25;i++)values.push(seed.length?seed[i%seed.length]:0);renderRiskMatrix(node,{...chart,values});});
function renderChart(node,chart,rows){const type=chart.type||"bar",renderer=CHART_PLUGINS.get(type)||CHART_PLUGINS.get("bar");return renderer(node,rows,chart);}
window.UCCChartPlugins=Object.freeze({register:registerChartPlugin,has:type=>CHART_PLUGINS.has(type),types:()=>Array.from(CHART_PLUGINS.keys())});


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
function selectedFilterObject(dashboard){const output={};dashboard.querySelectorAll("[data-demo-filter]").forEach(input=>{if(input.value)output[input.dataset.demoFilter]=input.value;});return output;}
function apiSection(config,dashboard,tab){const state=dashboardState(dashboard);if(tab==="quality"||tab==="sources")return state.lastSection||config.defaultSection;const mapped=config.apiSections&&config.apiSections[tab];if(mapped&&tab!=="overview")state.lastSection=mapped;return mapped||state.lastSection||config.defaultSection;}
function callApi(config,dashboard,action="summary",extra={}){
return new Promise((resolve,reject)=>{
if(!(window.frappe&&frappe.call)){reject(new Error("Frappe API client is unavailable."));return;}
const payload={action,subcriterion:apiSection(config,dashboard,activeSection(dashboard)),filters:selectedFilterObject(dashboard),page_size:100};
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
function metricRows(result,chartIndex,chart){
if(chart?.dataKey){
const grouped=result?.admission_intelligence?.charts?.[chart.dataKey];
if(Array.isArray(grouped))return grouped.map(item=>[item.label,finiteNumber(item.value,0),null,true]);
}
const metrics=(result?.metrics||[]).filter(item=>item.status==="available");
const title=String(chart?.title||"").toLowerCase();
const first=metrics[0]||null;
if(/source availability|evidence readiness|source readiness/.test(title)){
const ss=result?.source_summary||{},ms=result?.metric_summary||{};
return[
["Available sources",finiteNumber(ss.available,0),first,true],
["Source issues",finiteNumber(ss.issues,0),first,true],
["Available metrics",finiteNumber(ms.available,0),first,true],
["Metric issues",finiteNumber(ms.issues,0),first,true]
];
}
if(/status distribution|system health|control health|readiness/.test(title)&&metrics.length){
const unavailable=(result?.metrics||[]).filter(item=>item.status!=="available").length;
return[
["Available",metrics.length,metrics[0],true],
["Unavailable",unavailable,metrics[0],true],
["Sources",finiteNumber(result?.source_summary?.available,0),metrics[0],true],
["Exceptions",(result?.exceptions||[]).length,metrics[0],true]
];
}
if(/exception|gap|risk profile/.test(title)){
const exceptionMetrics=(result?.exceptions||[]).filter(item=>item.status==="available");
if(exceptionMetrics.length)return exceptionMetrics.slice(0,5).map(item=>[item.label,finiteNumber(item.value,0),item]);
}
if(!metrics.length)return[];
const size=Math.min(5,metrics.length),start=(chartIndex*size)%metrics.length,rows=[];
for(let i=0;i<size;i++){const metric=metrics[(start+i)%metrics.length];rows.push([metric.label,finiteNumber(metric.value,0),metric]);}
return rows;
}
// Sources the API reported as permission-blocked for this user, display-named.
function blockedSourceNames(result){
const rows=(result&&result.sources)||[];
const out=[];
rows.forEach(function(s){
const st=String(s&&(s.status||"")).toLowerCase();
if(st==="permission_denied"||st==="not permitted"||st==="permission denied"){
const n=displayDoctypeName(s.doctype||s.name||s.label);
if(n&&out.indexOf(n)===-1)out.push(n);
}
});
return out;
}
function chartForLive(node,chart,rows){
node.dataset.visualRenderAttempted="1";
if(!rows.length){
const blocked=blockedSourceNames(node._liveResult);
if(blocked.length){node.innerHTML=UCCShared.permissionNoticeHtml({view:chart&&chart.title?chart.title:"This visual",source:blocked.join(", "),compact:true});node.dataset.uccPermissionBlocked="1";return;}
node.innerHTML='<div class="ucc-live-empty"><strong>No live metric is readable for this section</strong><span>Open Source Mapping Report to see the exact DocType, permission or field issue.</span><button type="button" data-ucc-open-mapping>Source mapping report</button></div>';return;}
const pairs=rows.map(row=>[row[0],finiteNumber(row[1],0)]).filter(row=>Number.isFinite(row[1]));
if(!pairs.length){node.innerHTML='<div class="ucc-live-empty"><strong>The returned metrics are not numeric</strong><span>The visual was stopped before an invalid SVG path could be produced.</span><button type="button" data-ucc-open-mapping>Source mapping report</button></div>';return;}
try{
return renderChart(node,chart,pairs);
}catch(error){
node.dataset.visualRenderError=error&&error.message?error.message:String(error);
node.innerHTML='<div class="ucc-visual-diagnostic"><strong>Visual data could not be rendered</strong><span>'+esc(node.dataset.visualRenderError)+' Open Source Mapping Report to check the mapped DocTypes and fields.</span><button type="button" data-ucc-open-mapping>Source mapping report</button></div>';
}
}
// ---------------------------------------------------------------------------
// INSIGHTS CHART LAYER
//
// Frappe Insights is the definition source for every chart in the platform
// (analytics/chart_registry.py). The manifest below is loaded once and says,
// per chart, whether a real Insights query has been authored for it yet.
//
// Charts whose definition is REAL are answered by Insights, executed
// server-side and permission-checked (the mechanism proved on the bench --
// never the public-dashboard mechanism, which applies no permissions).
//
// Charts still marked PLACEHOLDER keep rendering the criterion API's own
// real, permission-checked numbers and carry a visible badge saying their
// Insights definition is outstanding. That is deliberate: replacing 100+
// working charts with empty placeholder cards would destroy working
// functionality to advertise a migration. The badge tells the truth -- the
// figures are real, the Insights definition is what is pending -- and
// flipping one chart to "real" needs no frontend change.
// ---------------------------------------------------------------------------
const chartDefinitions = { loaded: false, byId: {}, counts: null };

function loadChartDefinitions(onReady) {
    if (chartDefinitions.loaded) { if (onReady) onReady(); return; }
    if (!(window.frappe && frappe.call)) return;
    frappe.call({
        method: "ucc_intelligence.api.get_chart_definitions",
        callback(response) {
            const message = (response && response.message) || {};
            (message.charts || []).forEach((c) => { chartDefinitions.byId[c.chart_id] = c; });
            chartDefinitions.counts = message.counts || null;
            chartDefinitions.loaded = true;
            if (onReady) onReady();
        },
        error() {
            // No manifest -> no badges. The dashboard still works; it simply
            // cannot say which charts are on Insights yet.
            chartDefinitions.loaded = true;
            if (onReady) onReady();
        },
    });
}

function applyInsightsBadge(heading, chartId) {
    if (!heading) return;
    const existing = heading.querySelector("[data-insights-badge]");
    if (existing) existing.remove();
    const definition = chartDefinitions.byId[chartId];
    if (!definition) return;

    // Only a real Insights chart is badged. A box with no chart behind it is
    // blank, and a badge on a blank box would be commentary on an absence --
    // "Insights definition pending" and "Computed live" both went this way.
    if (definition.definition_status !== "real") return;

    const badge = document.createElement("span");
    badge.dataset.insightsBadge = "1";
    badge.className = "ucc-insights-badge is-real";
    badge.textContent = "Insights";
    badge.title = "Answered by Frappe Insights query: " + definition.insights_query_title;
    heading.appendChild(badge);
}

const INSIGHTS_BADGE_STYLE_ID = "ucc-insights-badge-style";
function injectInsightsBadgeStyles() {
    if (document.getElementById(INSIGHTS_BADGE_STYLE_ID)) return;
    const style = document.createElement("style");
    style.id = INSIGHTS_BADGE_STYLE_ID;
    style.textContent = `
.ucc-insights-badge{display:inline-block;margin-left:8px;padding:1px 7px;border-radius:999px;font-size:10px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;vertical-align:middle}
.ucc-insights-badge.is-real{background:#eefaf1;color:#1e7a45;border:1px solid #b7e3c6}
.ucc-chart-empty{display:flex;align-items:center;justify-content:center;min-height:120px;font-size:12px;color:var(--text-muted,#8d99a6)}
.ucc-chart-placeholder{display:flex;flex-direction:column;gap:6px;align-items:flex-start;justify-content:center;min-height:120px;padding:16px;border:1px dashed var(--border-color,#d1d8dd);border-radius:8px;background:repeating-linear-gradient(45deg,transparent,transparent 8px,rgba(0,0,0,.02) 8px,rgba(0,0,0,.02) 16px)}
.ucc-chart-placeholder strong{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:#8a5a00}
.ucc-chart-placeholder p{margin:0;font-size:12px;opacity:.75;line-height:1.5}
.ucc-chart-placeholder code{font-size:11px;opacity:.6;word-break:break-all}
.ucc-insights-series{display:flex;flex-direction:column;gap:6px;padding:8px 0}
.ucc-insights-bar{display:grid;grid-template-columns:minmax(90px,32%) 1fr auto;gap:8px;align-items:center;font-size:12px}
.ucc-insights-bar-label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ucc-insights-bar-track{background:var(--bg-light-gray,#f4f5f6);border-radius:3px;height:14px;overflow:hidden}
.ucc-insights-bar-fill{display:block;height:100%;background:#2c5aa0;border-radius:3px}
.ucc-insights-bar-value{font-variant-numeric:tabular-nums;font-weight:600}
`;
    document.head.appendChild(style);
}

function renderLiveChartCard(dashboard, chart, index, result) {
    const chartNode = dashboard.querySelector(
        `[data-demo-chart="${CSS.escape(chart.id)}"]`
    );

    const card = chartNode?.closest("[data-demo-card]");

    if (!card) return;

    const heading = card.querySelector("h2");
    const description = card.querySelector(".ucc-card-description");

    if (heading) {
        heading.textContent = chart.title || "Live visual";
        applyInsightsBadge(heading, chart.id);
    }

    if (description) {
        description.textContent =
            chart.description || "Permission-aware live metrics.";
    }

    card._liveCardPending = {
        chart: chart,
        index: index,
        result: result
    };

    card.dataset.liveCardRendered = "";
}
// DOCUMENTED DIVERGENCE FROM THE PORT -- Frappe Insights is now the single
// source for chart content.
//
// The legacy renderLiveChartCardNow() derived chart rows from the criterion
// API response (metricRows()) and drew them with the hand-written SVG
// renderers (chartForLive() and its per-type variants). That was the second
// rendering path. It is gone from the runtime: nothing below calls
// metricRows() or chartForLive(), and tools/test_end_to_end.py asserts they
// are unreachable.
//
// A chart now shows exactly one of two things:
//   - real Insights data, executed server-side and permission-checked; or
//   - nothing at all, because no verified Insights query stands behind it.
// There is no third case and no fallback. A blank chart means the definition
// is outstanding -- it never means "we quietly used the old path".
function renderLiveChartCardNow(card){
if(!card||!card._liveCardPending||card.dataset.liveCardRendered==="1")return;
const{chart,result}=card._liveCardPending;
const chartNode=card.querySelector("[data-demo-chart]");
const tableBody=card.querySelector("[data-demo-chart-table-body]");
card.dataset.liveCardRendered="1";
if(chartNode){chartNode.dataset.demoChartTitle=chart.title;chartNode.dataset.demoChartType=chart.type||"bar";chartNode._liveResult=result;}
renderInsightsChartInto(chartNode,tableBody,chart,result);
}

// Renders one card. Frappe Insights is the ONLY source of chart content --
// there is no criterion-engine path, no composite path, no fallback. Exactly
// two things qualify as an Insights source, both Insights Query v3 executed
// server-side with ordinary Frappe permissions applied:
//
//   1. chart.dataKey  -> get_admission_intelligence's series (Criterion 4.1.1)
//   2. a registry entry marked "real" -> get_chart_data
//
// Every other box on the dashboard renders BLANK. Not "pending", not
// "computed", not an error -- blank. A box with no verified Insights query
// behind it has nothing to say, and saying it anyway is what made the old
// dashboard read as broken.
function renderInsightsChartInto(chartNode,tableBody,chart,result){
if(chart&&chart.dataKey){
paintAdmissionChart(chartNode,tableBody,chart,result);
return;
}
const definition=chartDefinitions.byId[chart.id];
if(!definition||definition.definition_status!=="real"){paintChartEmpty(chartNode,tableBody);return;}
if(!(window.frappe&&frappe.call)){paintChartEmpty(chartNode,tableBody);return;}
paintChartMessage(chartNode,tableBody,chart,"Loading from Insights…");
frappe.call({
method:"ucc_intelligence.api.get_chart_data",
args:{chart_id:chart.id},
callback(response){
const data=(response&&response.message)||{};
if(data.status==="available"&&(data.series||[]).length){paintChartSeries(chartNode,tableBody,chart,data.series);return;}
// A permission refusal is the one thing worth saying: the chart exists and
// the user may not see it, which is different from the chart not existing.
if(data.status==="permission_denied"){
if(chartNode)chartNode.innerHTML="";
if(tableBody)tableBody.innerHTML='<tr><td colspan="3">'+window.UCCShared.permissionNoticeHtml({view:chart.title||"This visual",source:data.insights_query_title||"this chart",detail:data.message,compact:true})+"</td></tr>";
return;
}
paintChartEmpty(chartNode,tableBody);
},
error(){paintChartEmpty(chartNode,tableBody);},
});
}

// The six Criterion 4.1.1 series. Their data comes from Insights (see
// analytics/admission_intelligence_embed.py -- Query v3 execute(), permission
// checked per request); loadLive() has already put it on the result object, so
// there is nothing further to fetch. They keep their purpose-built line and
// column rendering: these are the charts the Insights pilot was proved on,
// and renderChart() is the dispatcher that already knows those types.
function paintAdmissionChart(chartNode,tableBody,chart,result){
const charts=(result&&result.admission_intelligence&&result.admission_intelligence.charts)||{};
const rows=charts[chart.dataKey];
if(!Array.isArray(rows)||!rows.length){paintChartEmpty(chartNode,tableBody);return;}
// Table via the shared painter (null chartNode = table only), diagram via the
// type dispatcher, so neither is duplicated here.
paintChartSeries(null,tableBody,chart,rows.map(item=>({label:item.label,value:finiteNumber(item.value,0)})));
if(chartNode)renderChart(chartNode,chart,rows.map(item=>[item.label,finiteNumber(item.value,0)]));
}

// The empty state. Deliberately wordless beyond one muted line: ~210 of the
// 223 boxes are in this state today, and an explanation repeated 210 times is
// noise. The migration status page is where "which charts are outstanding"
// gets answered.
function paintChartEmpty(chartNode,tableBody){
if(chartNode)chartNode.innerHTML='<div class="ucc-chart-empty">No chart available</div>';
if(tableBody)tableBody.innerHTML='<tr><td colspan="3" class="ucc-chart-empty">No chart available</td></tr>';
}

function paintChartMessage(chartNode,tableBody,chart,message){
if(chartNode)chartNode.innerHTML='<div class="ucc-chart-placeholder"><p>'+esc(message)+"</p></div>";
if(tableBody)tableBody.innerHTML='<tr><td colspan="3">'+esc(message)+"</td></tr>";
}

// One renderer for every Insights series: a horizontal bar list. Deliberately
// ONE shape rather than reproducing the ten hand-rolled chart types -- an
// Insights query returns label/value rows, and inventing a radar or a funnel
// from two columns would be decoration, not information. When a chart genuinely
// needs a different shape, that belongs in its Insights chart definition.
function paintChartSeries(chartNode,tableBody,chart,series){
const max=Math.max.apply(null,series.map(row=>Number(row.value)||0).concat([1]));
if(chartNode){
chartNode.innerHTML='<div class="ucc-insights-series">'+series.map(row=>{
const value=Number(row.value)||0;
const width=Math.max(1,Math.round((value/max)*100));
return'<div class="ucc-insights-bar"><span class="ucc-insights-bar-label">'+esc(row.label)+"</span>"
+'<span class="ucc-insights-bar-track"><span class="ucc-insights-bar-fill" style="width:'+width+'%"></span></span>'
+'<span class="ucc-insights-bar-value">'+esc(value.toLocaleString())+"</span></div>";
}).join("")+"</div>";
}
if(tableBody){
tableBody.innerHTML=series.map(row=>{
const shown=row.display!=null&&row.display!==""?row.display:(Number(row.value)||0).toLocaleString();
return"<tr><td>"+esc(row.label)+"</td><td>"+esc(shown)+"</td><td>"+statusBadge(row.status||"available")+"</td></tr>";
}).join("");
}
}
function renderKpis(dashboard,config,result){const mount=dashboard.querySelector("[data-demo-kpis]");if(!mount)return;
if(dashboard.dataset.demoDashboard==="criterion_4"&&result?.meta?.subcriterion==="4.1.1"&&Array.isArray(result?.admission_intelligence?.kpis)){
const kpis=result.admission_intelligence.kpis;
mount.innerHTML=kpis.map(item=>{const suffix=item.unit==="percent"?"%":"";return`<article class="ucc-admission-kpi"><span>${esc(item.label)}</span><strong>${Number(item.value||0).toLocaleString(undefined,{maximumFractionDigits:2})}${suffix}</strong><small>Student Applicant · live calculation</small></article>`;}).join("");
return;
}
const metrics=(result?.metrics||[]),rows=metrics.slice(0,6);while(rows.length<6)rows.push(null);mount.innerHTML=rows.map((metric,index)=>{if(metric)return`<article><span>${esc(metric.label)}</span><strong>${esc(metricValue(metric))}</strong><small>${esc(metric.doctype||metric.source||"Live metric")} · ${esc(metric.status.replaceAll("_"," "))}</small></article>`;const summary=index%2===0?result?.source_summary:result?.metric_summary;return`<article><span>${index%2===0?"Sources available":"Metrics available"}</span><strong>${summary?summary.available+"/"+summary.total:"—"}</strong><small>Permission-aware readiness</small></article>`;}).join("");}
function renderQa(dashboard,result,tab){
const target=dashboard.querySelector(`[data-demo-qa="${CSS.escape(dashboard.dataset.demoDashboard+":"+((dashboardState(dashboard).lastPanel)||tab))}"]`)||dashboard.querySelector("[data-demo-panel]:not(.hidden) [data-demo-qa]");
if(!target)return;
const rows=extendedQuestionRows(result,tab);
target.innerHTML=rows.length?rows.map(row=>{
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
return`<tr><td>${esc(row.criterion||result?.meta?.subcriterion||result?.policy?.policy||tab)}</td><td>${esc(row.question)}</td><td><div>${esc(row.answer)}</div>${answerAction}</td><td><div>${esc(sourceCalculation(row,metric))}</div>${sourceAction}</td><td>${statusBadge(row.status)}</td></tr>`;
}).join(""):'<tr><td colspan="5">No management questions are configured for this section.</td></tr>';
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
function renderReadiness(dashboard,config,result){const notice=dashboard.querySelector("[data-demo-readiness]"),title=dashboard.querySelector("[data-demo-readiness-title]"),copy=dashboard.querySelector("[data-demo-readiness-copy]");if(!result){if(notice)notice.dataset.status="loading";if(title)title.textContent=`Loading Criterion ${config.number} analytics…`;if(copy)copy.textContent="Waiting for the live data connection and current-user permission checks.";return;}const ss=result.source_summary||{},ms=result.metric_summary||{},sA=ss.available||0,sT=ss.total||0,mA=ms.available||0,mT=ms.total||0,issues=Math.max(0,sT-sA)+Math.max(0,mT-mA);if(notice)notice.dataset.status=issues?"warning":"available";if(title)title.textContent=`Criterion ${config.number} live analytics active${issues?" with limitations":""}.`;if(copy)copy.textContent=`Live data connected · ${sA} of ${sT} sources available · ${mA} of ${mT} metrics available${issues?` · ${issues} item${issues===1?"":"s"} need review`:""}`;}
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
const pmount=dashboard.querySelector("[data-demo-kpis]");
if(pmount)pmount.innerHTML=UCCShared.permissionNoticeHtml({view:viewName,source:source,detail:detail});
return;
}
if(notice)notice.dataset.status="error";
if(title)title.textContent=`Criterion ${config.number} live API unavailable.`;
if(copy)copy.textContent=detail;
const mount=dashboard.querySelector("[data-demo-kpis]");
if(mount)mount.innerHTML=`<article><span>API status</span><strong>Unavailable</strong><small>${esc(detail)}</small></article>`;
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
function renderDashboard(dashboard){const config=CONFIG[dashboard.dataset.demoDashboard],state=dashboardState(dashboard),result=state.result;if(!config)return;const tab=activeSection(dashboard);updateDashboardIdentity(dashboard,config,tab);if(state.error&&!result){renderError(dashboard,config,state.error);return;}const liveDefinitions=chartsForTab(dashboard.dataset.demoDashboard,config,tab);renderKpis(dashboard,config,result);liveDefinitions.forEach((chart,index)=>renderLiveChartCard(dashboard,chart,chart.i??index,result));dashboard.querySelectorAll(`[data-live-section="${CSS.escape(tab)}"] [data-demo-card]`).forEach(renderLiveChartCardNow);renderQa(dashboard,result,tab);renderSources(dashboard,result);renderQuality(dashboard,result);renderReadiness(dashboard,config,result);}
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
async function loadLive(dashboard,force=false){const config=CONFIG[dashboard.dataset.demoDashboard],state=dashboardState(dashboard),section=apiSection(config,dashboard,activeSection(dashboard));ensureLiveSectionCards(dashboard,config,activeSection(dashboard));if(state.loading)return;if(!force&&state.result&&state.result.meta?.subcriterion===section){renderDashboard(dashboard);return;}state.loading=true;state.error=null;setLoading(dashboard,true,15,`Loading ${section}`);try{const result=await callApi(config,dashboard,"summary");if(dashboard.dataset.demoDashboard==="criterion_4"&&section==="4.1.1"){setLoading(dashboard,true,60,"Loading Insights-embedded admission analytics");try{const embed=await loadAdmissionIntelligenceEmbed();if(embed){result.admission_intelligence=embed;result.sources=(result.sources||[]).concat(embed.sources||[]);}}catch(embedError){logEvent(dashboard,"ERROR","admission_intelligence_embed_failed",embedError.message||embedError);}}setLoading(dashboard,true,80,"Rendering live analytics");state.result=result;state.error=null;renderDashboard(dashboard);setLoading(dashboard,true,100,"Live analytics ready");setTimeout(()=>setLoading(dashboard,false),150);}catch(error){state.error=error;logEvent(dashboard,"ERROR","api_failure",error.message||error);renderDashboard(dashboard);setLoading(dashboard,false);}finally{state.loading=false;}}
function showTab(dashboard,tab){const config=CONFIG[dashboard.dataset.demoDashboard];dashboard.dataset.demoActiveTab=tab;dashboard.querySelectorAll("[data-demo-tab]").forEach(button=>button.classList.toggle("active",button.dataset.demoTab===tab));const panelKey=(config.panelMap&&config.panelMap[tab])||tab;dashboardState(dashboard).lastPanel=panelKey;dashboard.querySelectorAll("[data-demo-panel]").forEach(panel=>panel.classList.toggle("hidden",panel.dataset.demoPanel!==panelKey));ensureLiveSectionCards(dashboard,config,tab);syncLiveSectionVisibility(dashboard,tab);if(tab!=="quality"&&tab!=="sources")loadLive(dashboard);else renderDashboard(dashboard);}
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
async function openRecords(config,chartId,dashboard){
const result=dashboardState(dashboard).result,tab=activeSection(dashboard),definitions=chartsForTab(dashboard.dataset.demoDashboard,config,tab),index=Math.max(0,definitions.findIndex(item=>item.id===chartId)),chart=definitions[index];
if(/readiness|source availability|status distribution|system health|control health/i.test(chart?.title||"")){openReadiness(config,dashboard);return;}
const rows=metricRows(result,index,chart),metric=chart?.metricId?metricById(result,chart.metricId):rows.find(row=>row[2])?.[2];
return openMetricRecords(config,dashboard,metric,metric?.label||chart?.title||"Live records");
}
function openReadiness(config,dashboard){
const result=dashboardState(dashboard).result;
if(!result){openModal("Readiness","The live API has not returned a result.");return;}
const policy=result.policy||{},sources=result.sources||[],metrics=result.metrics||[];
openModal(`Criterion ${config.number} readiness`,`<div class="ucc-demo-modal-note"><strong>Criterion ${config.number} data readiness</strong><br>Source and metric status reflects the current user's permissions.</div><div class="grid2"><section><h3>Sources</h3><div class="table-wrap"><table><thead><tr><th>Source</th><th>Records</th><th>Status</th></tr></thead><tbody>${sources.map(row=>{const doctype=row.doctype||"";const action=doctype?`<button type="button" class="source-doctype-link ucc-qa-action" data-live-source-doctype="${esc(doctype)}">Open ${esc(displayDoctypeName(doctype))} list ↗</button>`:"";return`<tr><td><div>${esc(doctype||row.candidates?.join(" / ")||row.key)}</div>${action}</td><td>${row.count||0}</td><td>${statusBadge(row.status)}</td></tr>`;}).join("")}</tbody></table></div></section><section><h3>Metrics</h3><div class="table-wrap"><table><thead><tr><th>Metric</th><th>Value</th><th>Status</th></tr></thead><tbody>${metrics.map(item=>`<tr><td>${esc(item.label)}</td><td>${esc(metricValue(item))}</td><td>${statusBadge(item.status)}</td></tr>`).join("")}</tbody></table></div></section></div>`);
}
function showDiagnostics(config,dashboard){const state=dashboardState(dashboard),result=state.result,logs=state.logs;openModal(`Criterion ${config.number} diagnostics`,`<div class="table-wrap"><table><thead><tr><th>Time</th><th>Level</th><th>Event</th><th>Detail</th></tr></thead><tbody>${logs.map(row=>`<tr><td>${esc(row.time)}</td><td>${statusBadge(row.level)}</td><td>${esc(row.event)}</td><td>${esc(row.detail)}</td></tr>`).join("")||'<tr><td colspan="4">No diagnostic events.</td></tr>'}</tbody></table></div><div class="ucc-demo-modal-note">API: ${esc(config.apiMethod)} · Section: ${esc(result?.meta?.subcriterion||apiSection(config,dashboard,activeSection(dashboard)))}</div>`);}
async function handleAction(dashboard,action){const config=CONFIG[dashboard.dataset.demoDashboard],state=dashboardState(dashboard),result=state.result;if(action==="dismiss-readiness"){const notice=dashboard.querySelector("[data-demo-readiness]");if(notice){notice.dataset.dismissed="1";notice.hidden=true;}return;}if(action==="refresh")await loadLive(dashboard,true);if(action==="export-qa"){const rows=[["Section","Question","Answer","Source","Status"],...allQaRows(result)];download(`criterion_${config.number}_live_qa.csv`,rows.map(row=>row.map(csvCell).join(",")).join("\n"));}if(action==="export-exceptions"){const rows=[["Metric","Label","Value","Status","Source"],...allExceptionRows(result)];download(`criterion_${config.number}_live_exceptions.csv`,rows.map(row=>row.map(csvCell).join(",")).join("\n"));}if(action==="export-table"){const rows=[["Metric","Value","Unit","Status","Source"],...(result?.metrics||[]).map(item=>[item.label,item.value,item.unit,item.status,item.doctype||item.source])];download(`criterion_${config.number}_${result?.meta?.subcriterion||"section"}_live_metrics.csv`,rows.map(row=>row.map(csvCell).join(",")).join("\n"));}if(action==="copy-link"){const url=new URL(location.href);url.searchParams.set("dashboard",dashboard.dataset.demoDashboard);url.searchParams.set("live_tab",activeSection(dashboard));navigator.clipboard?.writeText(url.toString()).catch(()=>{});}if(action==="diagnostics")showDiagnostics(config,dashboard);if(action==="readiness")openReadiness(config,dashboard);}
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
// Load the Insights chart manifest once, then repaint the headings so the
// badges appear. Deliberately non-blocking: if the manifest never arrives
// the dashboard still renders, just without the migration badges.
injectInsightsBadgeStyles();
loadChartDefinitions(function(){
platform.querySelectorAll("[data-demo-chart]").forEach(function(node){
const card=node.closest("[data-demo-card]");
const heading=card&&card.querySelector("h2");
if(heading)applyInsightsBadge(heading,node.dataset.demoChart);
});
});
platform.querySelectorAll("[data-demo-dashboard]").forEach(function(dashboard){const config=CONFIG[dashboard.dataset.demoDashboard];if(!config)return;ensureLiveVisualCards(dashboard,config);syncLiveSectionVisibility(dashboard,"overview");dashboard.dataset.liveApi="1";dashboard.querySelectorAll("[data-demo-tab]").forEach(button=>button.addEventListener("click",()=>showTab(dashboard,button.dataset.demoTab)));dashboard.querySelectorAll("[data-demo-filter]").forEach(input=>input.addEventListener("change",()=>loadLive(dashboard,true)));dashboard.addEventListener("ucc:live-tool-action",function(event){const action=event.detail&&event.detail.action;const mapped=action==="export-current"?"export-table":action;if(mapped)handleAction(dashboard,mapped);});dashboard.addEventListener("click",function(event){
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
const actionButton=event.target.closest("[data-demo-action]");
if(actionButton){event.preventDefault();event.stopPropagation();handleAction(dashboard,actionButton.dataset.demoAction);return;}
const drill=event.target.closest("[data-demo-drill]");
if(drill){event.preventDefault();openRecords(config,drill.dataset.demoDrill,dashboard);return;}
const viewButton=event.target.closest("[data-demo-view]");
if(viewButton){const card=viewButton.closest("[data-demo-card]");if(!card)return;renderLiveChartCardNow(card);card.querySelectorAll("[data-demo-view]").forEach(button=>button.classList.toggle("active",button===viewButton));const diagram=card.querySelector("[data-demo-chart]"),table=card.querySelector("[data-demo-chart-table]");if(diagram)diagram.classList.toggle("hidden",viewButton.dataset.demoView!=="diagram");if(table)table.classList.toggle("hidden",viewButton.dataset.demoView!=="table");}
});dashboard.dataset.demoActiveTab="overview";dashboard.querySelectorAll("[data-demo-panel]").forEach(panel=>panel.classList.toggle("hidden",panel.dataset.demoPanel!=="overview"));if(!dashboard.classList.contains("ucc-hidden"))loadLive(dashboard);else renderReadiness(dashboard,config,null);});platform.addEventListener("ucc:dashboard-change",event=>{const id=event.detail&&event.detail.dashboard;if(!id)return;const dashboard=platform.querySelector(`[data-demo-dashboard="${CSS.escape(id)}"]`);if(dashboard)loadLive(dashboard);});
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
window.UCCLiveAnalytics=Object.freeze({config:CONFIG,registerResponseAdapter:registerResponseAdapter,registerChartPlugin:registerChartPlugin,refresh:function(criterion){const dashboard=platform.querySelector(`[data-demo-dashboard="${CSS.escape(criterion)}"]`);if(dashboard)return loadLive(dashboard,true);},showTab:function(criterion,tab){const dashboard=platform.querySelector(`[data-demo-dashboard="${CSS.escape(criterion)}"]`);if(dashboard)showTab(dashboard,tab);}});
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
// ASK UCC -- the chat surface for ucc_intelligence.api.ask_ucc.
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
// The plan doc's §2.1 step 8 requirement -- a reader can always tell AI text
// from retrieved facts -- is why the answer renders as three separately
// labelled zones rather than one prose blob.
// ---------------------------------------------------------------------------
const ASK_STYLE_ID = "ucc-ask-style";
const ASK_STYLE_TEXT = `
.ucc-ask{display:flex;flex-direction:column;gap:12px;padding:12px}
.ucc-ask-head{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;padding:10px 16px 8px}
.ucc-ask-head h2{margin:0;font-size:15px}
.ucc-ask-head p{margin:0;font-size:12px;opacity:.7}
.ucc-ask-row{display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap;padding:0 16px 10px}
.ucc-ask-field{display:flex;flex-direction:column;gap:3px;position:relative;min-width:180px}
.ucc-ask-field-grow{flex:1}
.ucc-ask-field>span{font-size:11px;font-weight:600;opacity:.75}
.ucc-ask-field select,.ucc-ask-field input,.ucc-ask-field textarea{padding:6px 8px;border:1px solid var(--border-color,#d1d8dd);border-radius:6px;font:inherit;width:100%}
.ucc-ask-submit{white-space:nowrap}
.ucc-ask-suggestions{position:absolute;top:100%;left:0;right:0;z-index:20;background:var(--card-bg,#fff);border:1px solid var(--border-color,#d1d8dd);border-radius:6px;max-height:240px;overflow:auto;box-shadow:0 4px 12px rgba(0,0,0,.08)}
.ucc-ask-suggestion{padding:6px 10px;cursor:pointer;font-size:13px;display:flex;flex-direction:column;gap:1px}
.ucc-ask-suggestion-id{font-size:11px;opacity:.65}
/* Two rows, two jobs, so two visual weights. Row 1 is navigation: which
   topic am I in -- uppercase, tracked, borderless, the selected one filled
   solid so the current topic is unmistakable. Row 2 is the actions inside
   that topic -- sentence case, outlined cards, larger text. Previously both
   rows were near-identical pills and the hierarchy was invisible. */
.ucc-ask-categories{display:flex;flex-wrap:wrap;gap:2px;padding:2px 16px 0;border-bottom:1px solid var(--border-color,#e6e9ec);margin:0 0 10px}
.ucc-ask-category{padding:6px 12px;border:0;border-bottom:2px solid transparent;background:transparent;font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--text-muted,#8d99a6);cursor:pointer}
.ucc-ask-category:hover{color:var(--text-color,#36414c)}
.ucc-ask-category.is-active{color:var(--text-color,#36414c);border-bottom-color:var(--text-color,#36414c)}
.ucc-ask-questions{display:flex;flex-wrap:wrap;gap:6px;padding:0 16px 12px}
.ucc-ask-question{padding:6px 12px;border:1px solid var(--border-color,#d1d8dd);border-radius:6px;background:var(--card-bg,#fff);font-size:13px;cursor:pointer;text-align:left}
.ucc-ask-question:hover{background:var(--bg-light-gray,#f4f5f6);border-color:var(--text-muted,#8d99a6)}
.ucc-shell-settings-link{margin-left:18px;padding:5px 9px;font-size:19px;line-height:1;background:transparent;border:1px solid var(--border-color,#d1d8dd);border-radius:6px;opacity:.7;cursor:pointer}
.ucc-shell-settings-link:hover{opacity:1;background:var(--bg-light-gray,#f4f5f6)}
.ucc-ask-suggestion:hover,.ucc-ask-suggestion.is-active{background:var(--bg-light-gray,#f4f5f6)}
.ucc-ask-status{padding:0 16px 10px;font-size:13px}
.ucc-ask-status[data-tone="error"]{color:var(--red-600,#c0392b)}
.ucc-ask-thread{display:flex;flex-direction:column;gap:16px}
.ucc-ask-turn{display:flex;flex-direction:column;gap:12px}
.ucc-ask-question-bubble{align-self:flex-end;max-width:70%;background:var(--bg-light-gray,#f4f5f6);padding:10px 14px;border-radius:12px;font-size:14px}
.ucc-ask-zone{border:1px solid var(--border-color,#d1d8dd);border-radius:8px;overflow:hidden}
.ucc-ask-zone-head{padding:8px 12px;font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;background:var(--bg-light-gray,#f4f5f6)}
.ucc-ask-zone-body{padding:12px}
.ucc-ask-zone-ai .ucc-ask-zone-head{background:#eef4ff;color:#2c5aa0}
.ucc-ask-zone-facts .ucc-ask-zone-head{background:#eefaf1;color:#1e7a45}
.ucc-ask-answer-text{white-space:pre-wrap;font-size:14px;line-height:1.55}
.ucc-ask-fact-group{margin-bottom:12px}
.ucc-ask-fact-group:last-child{margin-bottom:0}
.ucc-ask-fact-group>h4{font-size:12px;margin:0 0 6px;opacity:.8}
.ucc-ask-fact-table{width:100%;border-collapse:collapse;font-size:12px}
.ucc-ask-fact-table th,.ucc-ask-fact-table td{border:1px solid var(--border-color,#e6e9ec);padding:4px 8px;text-align:left;vertical-align:top}
.ucc-ask-fact-table th{width:34%;font-weight:600;opacity:.8}
.ucc-ask-source{display:inline-flex;gap:6px;align-items:center;font-size:12px;padding:4px 8px;border:1px solid var(--border-color,#d1d8dd);border-radius:999px;margin:0 6px 6px 0;text-decoration:none}
.ucc-ask-ai-unavailable{font-size:13px;opacity:.8;font-style:italic}
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
	const suggestionBox = root.querySelector("[data-ask-suggestions]");
	const questionInput = root.querySelector("[data-ask-question]");
	const submitButton = root.querySelector("[data-ask-submit]");
	const clearButton = root.querySelector("[data-ask-clear]");
	const statusNode = root.querySelector("[data-ask-status]");
	const thread = root.querySelector("[data-ask-thread]");
	const guidedPanel = root.querySelector("[data-ask-guided]");
	const categoryRow = root.querySelector("[data-ask-categories]");
	const questionRow = root.querySelector("[data-ask-questions]");

	const state = { modules: [], busy: false, category: "", selectedLabel: "" };

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
				return;
			}
			moduleSelect.innerHTML = modules
				.map((m) => `<option value="${askEsc(m.key)}">${askEsc(m.label)}</option>`)
				.join("");
			renderGuided();
		},
		error() {
			setStatus("Could not load the available modules.", "error");
		},
	});

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
						'<div class="ucc-ask-suggestion" data-value="' + askEsc(r.id) + '">'
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

	recordInput.addEventListener("input", () => {
		window.clearTimeout(searchTimer);
		searchTimer = window.setTimeout(() => searchRecords(recordInput.value.trim()), 250);
	});
	suggestionBox.addEventListener("click", (event) => {
		const option = event.target.closest("[data-value]");
		if (!option) return;
		recordInput.value = option.dataset.value;
		state.selectedLabel = (option.querySelector("strong") || {}).textContent || "";
		hideSuggestions();
		renderGuided();
		questionInput.focus();
	});
	document.addEventListener("click", (event) => {
		if (!suggestionBox.contains(event.target) && event.target !== recordInput) hideSuggestions();
	});
	moduleSelect.addEventListener("change", () => {
		recordInput.value = "";
		state.category = "";
		state.selectedLabel = "";
		hideSuggestions();
		renderGuided();
	});

	// --- guided ("FAQ") question buttons -------------------------------
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
				'<button type="button" class="ucc-ask-category' + (c.key === state.category ? " is-active" : "")
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

	questionRow.addEventListener("click", (event) => {
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
		setStatus("Asking...");

		frappe.call({
			method: "ucc_intelligence.api.ask_ucc",
			args: { module: module.key, question: question, record: record },
			callback(response) {
				const message = response && response.message;
				if (message) {
					thread.insertAdjacentHTML("afterbegin", renderTurn(question, message, module));
					questionInput.value = "";
					clearButton.hidden = false;
					setStatus("");
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

	submitButton.addEventListener("click", ask);
	questionInput.addEventListener("keydown", (event) => {
		if (event.key === "Enter") ask();
	});

	// Clear chat wipes the on-screen thread only. Stored conversations (the
	// UCC AI Conversation / Message records, when persistence is enabled) are
	// deliberately untouched -- this is a "the screen is too long to read"
	// control, not a delete-my-audit-trail control.
	clearButton.addEventListener("click", () => {
		thread.innerHTML = "";
		clearButton.hidden = true;
		setStatus("");
		questionInput.focus();
	});
}

// --- rendering -------------------------------------------------------------
// Three visually distinct zones, per the plan doc: what the AI said, the
// facts it was given, and where those came from. A reader must never have to
// guess which is which.

function renderTurn(question, message, module) {
	return (
		'<article class="ucc-ask-turn">'
		+ '<div class="ucc-ask-question-bubble">' + askEsc(question) + "</div>"
		+ renderAnswerZone(message, module)
		+ renderFactsZone(message)
		+ renderSourcesZone(message)
		+ "</article>"
	);
}

function renderAnswerZone(message, module) {
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

	const status = message.ai_status;
	if (status === "available" && message.answer) {
		return (
			'<div class="ucc-ask-zone ucc-ask-zone-ai">'
			+ '<div class="ucc-ask-zone-head">AI interpretation'
			+ (message.answer.model ? " &middot; " + askEsc(message.answer.model) : "")
			+ "</div>"
			+ '<div class="ucc-ask-zone-body"><div class="ucc-ask-answer-text">'
			+ askEsc(message.answer.text)
			+ "</div></div></div>"
		);
	}

	// "AI interpretation is turned off" on a plain data lookup ("what is this
	// student's nationality?") implies interpretation was ever expected, and
	// on every answer it is just noise. So the notice is only shown when
	// something was actually lost:
	//
	//   disabled -> an administrator deliberately turned AI off. That is a
	//       choice, not an event; if the facts rendered, there is nothing to
	//       report. Only worth saying when the facts zone will be empty too,
	//       so the user isn't left with a blank answer.
	//   unavailable -> AI is switched ON but cannot run: no key in
	//       site_config, provider/model blank, unimplemented provider. ALWAYS
	//       shown. This is a fault, not a setting, and suppressing it is what
	//       made "Enable AI is on but nothing happens" impossible to diagnose
	//       -- the message names the exact missing piece, so it must reach
	//       the person who can fix it.
	//   error / guardrail_blocked -> AI DID run and its output was lost or
	//       withheld. Always shown; silently dropping a withheld answer would
	//       hide a guardrail firing.
	//   not_found -> a record-level failure, always shown.
	//
	// ponytail: keyed off "did any facts render", not off classifying the
	// question as lookup-vs-analytical. Classifying would mean hand-tagging
	// ~60 ported legacy questions with metadata the legacy UI never had. If
	// an analytical question with AI off later needs its own "this needed
	// interpretation" hint, that tagging is where it goes.
	const hasFacts = Object.keys(message.facts || {})
		.some((k) => message.facts[k] && message.facts[k].status === "available");
	if (hasFacts && status === "disabled") return "";

	const reasons = {
		disabled: "AI interpretation is turned off. The facts below come straight from live records.",
		unavailable: "AI is enabled but could not run, so this answer is facts only.",
		guardrail_blocked: "An AI answer was generated but referenced something not present in the retrieved facts, so it was withheld. The facts below are unaffected.",
		error: "AI interpretation could not be produced. The facts below come straight from live records.",
		not_found: "That record could not be found.",
	};
	const text = reasons[status] || "AI interpretation is unavailable. The facts below come straight from live records.";
	return (
		'<div class="ucc-ask-zone ucc-ask-zone-ai">'
		+ '<div class="ucc-ask-zone-head">AI interpretation unavailable</div>'
		+ '<div class="ucc-ask-zone-body"><div class="ucc-ask-ai-unavailable">'
		+ askEsc(text)
		+ (message.answer_error ? "<br>" + askEsc(message.answer_error) : "")
		+ "</div></div></div>"
	);
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

function renderFactsZone(message) {
	const facts = message.facts || {};
	const groups = Object.keys(facts).filter((k) => facts[k] && facts[k].status === "available");
	if (!groups.length) return "";

	const body = groups
		.map((toolName) => {
			const group = facts[toolName];
			const rows = Object.keys(group)
				.filter((k) => k !== "status" && k !== "note")
				.map((k) => "<tr><th>" + askEsc(humanise(k)) + "</th><td>" + renderFactValue(group[k]) + "</td></tr>")
				.join("");
			return (
				'<div class="ucc-ask-fact-group"><h4>' + askEsc(humanise(toolName)) + "</h4>"
				+ '<table class="ucc-ask-fact-table">' + rows + "</table>"
				+ (group.note ? '<p class="ucc-card-description">' + askEsc(group.note) + "</p>" : "")
				+ "</div>"
			);
		})
		.join("");

	return (
		'<div class="ucc-ask-zone ucc-ask-zone-facts">'
		+ '<div class="ucc-ask-zone-head">Facts from live records</div>'
		+ '<div class="ucc-ask-zone-body">' + body + "</div></div>"
	);
}

function renderSourcesZone(message) {
	const sources = (message.sources || []).filter((s) => s.status === "available" && s.record);
	if (!sources.length) return "";
	const links = sources
		.map((s) => {
			const route = window.UCCShared.doctypeRoute(s.doctype) + "/" + encodeURIComponent(s.record);
			return '<a class="ucc-ask-source" href="' + askEsc(route) + '" target="_blank" rel="noopener">'
				+ askEsc(s.doctype) + ": " + askEsc(s.record) + " &#8599;</a>";
		})
		.join("");
	return (
		'<div class="ucc-ask-zone">'
		+ '<div class="ucc-ask-zone-head">Sources</div>'
		+ '<div class="ucc-ask-zone-body">' + links + "</div></div>"
	);
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

	button.addEventListener("click", () => {
		frappe.set_route("Form", "UCC Intelligence Settings");
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
