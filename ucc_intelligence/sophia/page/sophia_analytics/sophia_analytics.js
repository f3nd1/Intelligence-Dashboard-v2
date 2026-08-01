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

const SHELL_HTML = "<div class=\"ucc-platform ucc-embed-safe\" data-build-id=\"SOPHIA-ANALYTICS-PAGE\" data-platform-version=\"phase-3\" id=\"uccIntelligencePlatform\"><header class=\"ucc-platform-shell\"><div class=\"ucc-platform-brand\"><div aria-hidden=\"true\" class=\"ucc-platform-mark\">UCC</div><div class=\"ucc-platform-brand-copy\"><div class=\"ucc-platform-brand-title\"><strong>UCC Intelligence Platform</strong></div><small>Analytics, evidence and guided answers</small></div></div><nav aria-label=\"Platform workspaces\" class=\"ucc-platform-workspaces\"><button aria-pressed=\"true\" class=\"is-active\" data-ucc-workspace=\"analytics\" type=\"button\">Analytics</button><button aria-pressed=\"false\" data-ucc-workspace=\"explore\" type=\"button\">Explore</button><button aria-pressed=\"false\" data-ucc-workspace=\"ask\" type=\"button\">Ask UCC</button></nav><button aria-label=\"UCC Intelligence Settings\" class=\"ucc-shell-settings-link\" data-ucc-settings-link=\"\" hidden=\"\" title=\"UCC Intelligence Settings\" type=\"button\"><span aria-hidden=\"true\">&#9881;</span><span class=\"ucc-visually-hidden\">UCC Intelligence Settings</span></button><div class=\"ucc-platform-dashboard-control\" data-ucc-dashboard-control=\"\"><label for=\"uccDashboardSelect\">Dashboard</label><select id=\"uccDashboardSelect\"><option value=\"criterion_1\">Criterion 1 \u00b7 Leadership and Strategic Planning</option><option value=\"criterion_2\">Criterion 2 \u00b7 Corporate Administration</option><option value=\"criterion_3\">Criterion 3 \u00b7 External Recruitment Agents</option><option value=\"criterion_4\">Criterion 4 \u00b7 Student Protection and Support Services</option><option selected=\"\" value=\"criterion_5\">Criterion 5 \u00b7 Academic Systems and Processes</option><option value=\"criterion_6\">Criterion 6 \u00b7 Quality Assurance, Innovation and Continual Improvement</option><option value=\"criterion_7\">Criterion 7 \u00b7 Performance Outcomes</option></select></div><button aria-expanded=\"true\" aria-label=\"Minimise UCC navigation\" class=\"ucc-shell-collapse-toggle\" data-shell-toggle=\"\" title=\"Minimise navigation\" type=\"button\"><span aria-hidden=\"true\" class=\"ucc-shell-toggle-icon\" data-shell-toggle-icon=\"\">\u2039</span><span class=\"ucc-visually-hidden\" data-shell-toggle-label=\"\">Minimise navigation</span></button></header><main class=\"ucc-platform-main\"><section class=\"ucc-platform-workspace\" data-ucc-workspace-panel=\"analytics\"><div class=\"ucc-criterion-dashboard\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_5\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_5\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_4\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_4\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_1\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_1\" data-live-api=\"1\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_2\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_2\" data-live-api=\"1\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_3\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_3\" data-live-api=\"1\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_6\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_6\" data-live-api=\"1\"></div><div class=\"ucc-criterion-dashboard ucc-hidden\" data-dashboard-architecture=\"shared-v2\" data-dashboard-panel=\"criterion_7\" data-demo-active-tab=\"overview\" data-demo-dashboard=\"criterion_7\" data-live-api=\"1\"></div></section><section class=\"ucc-platform-workspace\" data-ucc-workspace-panel=\"explore\" hidden=\"\">\n<div class=\"ucc-explore-hub\" data-ucc-explore=\"\">\n<header class=\"ucc-explore-hero\">\n<div>\n<span class=\"ucc-explore-kicker\">DIAGRAM EXPLORER</span>\n<h1>Find live diagrams without opening another dashboard page</h1>\n<p>Search all Criterion 1\u20137 visual catalogues. Criteria 1, 2, 3, 6 and 7 use permission-aware live API foundations; Criteria 4 and 5 retain their established live implementations.</p>\n</div>\n<div class=\"ucc-explore-summary\">\n<article><span>Criterion 4</span><strong data-ucc-explore-count=\"criterion_4\">0</strong><small>live visuals</small></article>\n<article><span>Criterion 5</span><strong data-ucc-explore-count=\"criterion_5\">0</strong><small>live visuals</small></article>\n<article><span>Live foundations</span><strong>5</strong><small>permission-aware APIs</small></article>\n</div>\n</header>\n<div class=\"ucc-explore-controls\">\n<label><span>Search</span><input autocomplete=\"off\" data-ucc-explore-search=\"\" placeholder=\"Search diagram, section, type or source\" role=\"searchbox\" spellcheck=\"false\" type=\"text\"/></label>\n<label><span>Section</span><select data-ucc-explore-section=\"\"><option value=\"\">All sections</option></select></label>\n<label><span>Visual type</span><select data-ucc-explore-type=\"\"><option value=\"\">All visual types</option></select></label>\n<button data-ucc-explore-clear=\"\" type=\"button\">Clear</button>\n</div>\n<div class=\"ucc-explore-layout\">\n<aside class=\"ucc-explore-catalogue\">\n<div class=\"ucc-explore-catalogue-head\">\n<div><strong>Available diagrams</strong><small data-ucc-explore-result-count=\"\">Scanning platform\u2026</small></div>\n<span class=\"ucc-explore-live-pill\">Live</span>\n</div>\n<div class=\"ucc-explore-list\" data-ucc-explore-list=\"\"></div>\n</aside>\n<section class=\"ucc-explore-guide\">\n<div class=\"ucc-explore-guide-card\">\n<span class=\"ucc-explore-step\">1</span>\n<div><strong>Choose the dashboard</strong><p>Use the existing Criterion selector in the top bar.</p></div>\n</div>\n<div class=\"ucc-explore-guide-card\">\n<span class=\"ucc-explore-step\">2</span>\n<div><strong>Search or filter</strong><p>The catalogue is generated from the real chart elements, so future diagrams appear automatically.</p></div>\n</div>\n<div class=\"ucc-explore-guide-card\">\n<span class=\"ucc-explore-step\">3</span>\n<div><strong>Open the live card</strong><p>One click takes you to the original analytics card. No duplicate rendering logic or copied data.</p></div>\n</div>\n<div class=\"ucc-explore-note\">\n<strong>Why this approach scales</strong>\n<p>Explore is a fast index over the existing dashboards\u2014not a second dashboard system. Criterion-specific calculations, D3 renderers, tables, exports and record links remain in their original tested components.</p>\n</div>\n</section>\n</div>\n</div>\n</section><section class=\"ucc-platform-workspace\" data-ucc-workspace-panel=\"ask\" hidden=\"\"><div class=\"ucc-ask\" data-ucc-ask=\"\"><div class=\"ucc-ask-layout\"><div class=\"ucc-ask-main\"><header class=\"ucc-ask-head\"><div class=\"ucc-ask-head-copy\"><h2 id=\"uccAskTitle\">Ask UCC</h2><p>Ask about a selected record, or use a verified FAQ for a direct answer.</p></div><aside class=\"ucc-ask-assurance\" data-ask-assurance=\"\"></aside></header><section class=\"ucc-ask-controls\" aria-labelledby=\"uccAskTitle\"><div class=\"ucc-ask-row\"><label class=\"ucc-ask-field\"><span>Module</span><select data-ask-module=\"\"></select></label><label class=\"ucc-ask-field ucc-ask-field-grow\"><span>Record</span><input autocomplete=\"off\" data-ask-record=\"\" placeholder=\"Search by name or ID\u2026\" type=\"text\"/><div class=\"ucc-ask-suggestions\" data-ask-suggestions=\"\" hidden=\"\" role=\"listbox\"></div></label><div class=\"ucc-ask-field\"><span id=\"uccAskStatusLabel\">Status</span><p aria-labelledby=\"uccAskStatusLabel\" class=\"ucc-ask-record-status\" data-ask-record-status=\"\" data-state=\"none\">No record selected</p></div></div><label class=\"ucc-ask-field\"><span>Question</span><textarea data-ask-question=\"\" rows=\"2\" placeholder=\"Ask a question about the selected record\"></textarea></label><div class=\"ucc-ask-actions\"><button class=\"ucc-ask-submit\" data-ask-submit=\"\" type=\"button\"></button><button class=\"ucc-ask-clear\" data-ask-clear=\"\" hidden=\"\" type=\"button\"></button></div></section><div class=\"ucc-ask-guided\" data-ask-guided=\"\" hidden=\"\"><div aria-label=\"Question categories\" class=\"ucc-ask-categories\" data-ask-categories=\"\" role=\"tablist\"></div><div class=\"ucc-ask-faq-head\"><h3>Verified FAQs</h3><p>Direct answers from live records, no AI interpretation</p></div><div class=\"ucc-ask-questions\" data-ask-questions=\"\"></div></div><div class=\"ucc-ask-status\" data-ask-status=\"\" hidden=\"\" role=\"status\"></div><section aria-label=\"Answers\" aria-live=\"polite\" class=\"ucc-ask-thread\" data-ask-thread=\"\"></section></div><aside aria-label=\"Record context\" class=\"ucc-ask-context\" data-ask-context=\"\"></aside></div></div></section></main></div>";

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
const CONFIG={"criterion_1":{"number":"1","title":"Leadership and Strategic Planning","description":"Live, permission-aware analytics foundation for leadership, governance and strategic planning. Source and metric availability is resolved from ERPNext permissions.","subcriteria":[["1.1.1","Leadership and Corporate Governance"],["1.2.1","Strategic Planning"]],"sections":{"overview":{"title":"Overview","charts":[]},"1.1":{"title":"Leadership and Corporate Governance","charts":[]},"1.2":{"title":"Strategic Planning","charts":[]},"1.1.1":{"title":"Leadership and Corporate Governance","charts":[]},"1.2.1":{"title":"Strategic Planning","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_1","defaultSection":"1.1.1","apiSections":{"overview":"1.1.1","1.1.1":"1.1.1","1.2.1":"1.2.1","quality":"1.1.1","sources":"1.1.1"},"panelMap":{"overview":"overview","1.1.1":"1.1.1","1.2.1":"1.2.1","sources":"sources","quality":"sources"},"filters":[["academic_year","Academic Year",["All Academic Years","2026","2025"]],["student_group","Module Class Details",["All Module Classes"]],["program","Course",["All Courses"]],{"key":"month","label":"Month","type":"month"}]},"criterion_2":{"number":"2","title":"Corporate Administration","description":"Live, permission-aware analytics foundation for human resources, communication, knowledge management and feedback. Unsupported fields are shown explicitly.","subcriteria":[["2.1.1","Staff Selection and Management"],["2.1.2","Staff Training and Development"],["2.2.1","Internal and External Communication"],["2.3.1","Data and Information Management"],["2.3.2","Knowledge Management"],["2.4.1","Feedback Management"],["2.4.2","Student Satisfaction Survey"],["2.4.3","Staff Satisfaction Survey"]],"sections":{"overview":{"title":"Overview","charts":[]},"2.1":{"title":"Human Resource","charts":[]},"2.2":{"title":"Communication","charts":[]},"2.3":{"title":"Data, Information and Knowledge Management","charts":[]},"2.4":{"title":"Feedback Management","charts":[]},"2.1.1":{"title":"Human Resource","charts":[]},"2.1.2":{"title":"Staff Training and Development","charts":[]},"2.2.1":{"title":"Communication","charts":[]},"2.3.1":{"title":"Data, Information and Knowledge Management","charts":[]},"2.3.2":{"title":"Knowledge Management","charts":[]},"2.4.1":{"title":"Feedback Management","charts":[]},"2.4.2":{"title":"Student Satisfaction Survey","charts":[]},"2.4.3":{"title":"Staff Satisfaction Survey","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_2","defaultSection":"2.1.1","apiSections":{"overview":"2.1.1","2.1.1":"2.1.1","2.1.2":"2.1.2","2.2.1":"2.2.1","2.3.1":"2.3.1","2.3.2":"2.3.2","2.4.1":"2.4.1","2.4.2":"2.4.2","2.4.3":"2.4.3","quality":"2.1.1","sources":"2.1.1"},"panelMap":{"overview":"overview","2.1.1":"2.1.1","2.1.2":"2.1.2","2.2.1":"2.2.1","2.3.1":"2.3.1","2.3.2":"2.3.2","2.4.1":"2.4.1","2.4.2":"2.4.2","2.4.3":"2.4.3","sources":"sources","quality":"sources"},"filters":[["academic_year","Academic Year",["All Academic Years","2026","2025"]],["student_group","Module Class Details",["All Module Classes"]],["program","Course",["All Courses"]],{"key":"month","label":"Month","type":"month"}]},"criterion_3":{"number":"3","title":"External Recruitment Agents","description":"Policy-aligned live analytics foundation for agent selection, appointment, onboarding, performance evaluation, renewal and offboarding. Unsupported fields are shown explicitly.","policy_set":[{"code":"PPD-SES-SL-3.1.1","version":"1.2","title":"Selection and Appointment of External Recruitment Agents","updated":"15 January 2026"},{"code":"PPD-SES-SL-3.2.1","version":"1.2","title":"Management and Evaluation of Recruitment Agents","updated":"15 January 2026"}],"subcriteria":[["3.1.1","Selection and Appointment"],["3.2.1","Management and Evaluation"]],"filters":[["review_year","Review Year",["All Review Years","2026","2025"]],["agent_status","Agent Status",["All Agent Statuses","Active","Pending","Inactive"]],["market","Market / Region",["All Markets","Southeast Asia","South Asia","Greater China","Other"]],["renewal_cycle","Renewal Cycle",["All Renewal Cycles","June","December"]]],"sections":{"overview":{"title":"Criterion 3 Overview","charts":[]},"3.1.1":{"title":"Selection and Appointment of External Recruitment Agents","charts":[]},"3.2.1":{"title":"Management and Evaluation of Recruitment Agents","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_3","defaultSection":"3.1.1","apiSections":{"overview":"3.1.1","3.1.1":"3.1.1","3.2.1":"3.2.1","quality":"3.1.1","sources":"3.1.1"},"panelMap":{"overview":"overview","3.1.1":"3.1.1","3.2.1":"3.2.1","sources":"sources","quality":"sources"}},"criterion_4":{"number":"4","title":"Student Protection and Support Services","description":"Live, permission-aware analytics for admissions, contracts, fees, student movement, refunds, student support, conduct and attendance.","subcriteria":[["4.1.1","Pre-Course Counselling, Selection and Admissions"],["4.2.1","Student Contract"],["4.2.2","Fee Collection and Fee Protection Scheme"],["4.3.1","Course Transfer, Deferment and Withdrawal"],["4.4.1","Refund"],["4.5.1","Student Support Services"],["4.6.1","Student Conduct and Attendance"]],"filters":[["academic_year","Academic Year",["All Academic Years"]],["program","Programme",["All Programmes"]],["intake","Intake",["All Intakes"]],["status","Status",["All Statuses"]],["nationality","Country / Nationality",["All Countries"]],["agent","Recruitment Agent",["All Agents"]]],"sections":{"overview":{"title":"Overview","charts":[]},"4.1.1":{"title":"Pre-Course Counselling, Selection and Admissions","charts":[]},"4.2.1":{"title":"Student Contract","charts":[]},"4.2.2":{"title":"Fee Collection and Fee Protection Scheme","charts":[]},"4.3.1":{"title":"Course Transfer, Deferment and Withdrawal","charts":[]},"4.4.1":{"title":"Refund","charts":[]},"4.5.1":{"title":"Student Support Services","charts":[]},"4.6.1":{"title":"Student Conduct and Attendance","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_4","defaultSection":"4.1.1","apiSections":{"overview":"4.1.1","4.1.1":"4.1.1","4.2.1":"4.2.1","4.2.2":"4.2.2","4.3.1":"4.3.1","4.4.1":"4.4.1","4.5.1":"4.5.1","4.6.1":"4.6.1","quality":"4.1.1","sources":"4.1.1"},"panelMap":{"overview":"overview","4.1.1":"4.1.1","4.2.1":"4.2.1","4.2.2":"4.2.2","4.3.1":"4.3.1","4.4.1":"4.4.1","4.5.1":"4.5.1","4.6.1":"4.6.1","sources":"sources","quality":"sources"}},"criterion_5":{"number":"5","title":"Academic Systems and Processes","description":"Live, permission-aware analytics for course design, review, planning, delivery, partnerships, student feedback, learning support and assessment.","subcriteria":[["5.1.1","Course Design and Development"],["5.1.2","Course Review"],["5.2.1","Course Planning"],["5.2.2","Course Delivery"],["5.3.1","Partnership Management"],["5.4","Student Feedback and Learning Support"],["5.5","Assessment"]],"sections":{"overview":{"title":"Overview","charts":[]},"5.1.1":{"title":"Course Design and Development","charts":[]},"5.1.2":{"title":"Course Review","charts":[]},"5.2.1":{"title":"Course Planning","charts":[]},"5.2.2":{"title":"Course Delivery","charts":[]},"5.3.1":{"title":"Partnerships","charts":[]},"5.4":{"title":"Student Feedback and Learning Support","charts":[]},"5.5":{"title":"Assessment","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_5","defaultSection":"5.1.1","apiSections":{"overview":"5.1.1","5.1.1":"5.1.1","5.1.2":"5.1.2","5.2.1":"5.2.1","5.2.2":"5.2.2","5.3.1":"5.3.1","5.4":"5.4","5.5":"5.5","quality":"5.1.1","sources":"5.1.1"},"panelMap":{"overview":"overview","5.1.1":"5.1.1","5.1.2":"5.1.2","5.2.1":"5.2.1","5.2.2":"5.2.2","5.3.1":"5.3.1","5.4":"5.4","5.5":"5.5","sources":"sources","quality":"sources"},"filters":[["year","Academic Year",["All Academic Years"]],["student_group","Module Class Details",["All Module Classes"]],["program","Course",["All Courses"]],["status","Status",["All Statuses"]]]},"criterion_6":{"number":"6","title":"Quality Assurance, Innovation and Continual Improvement","description":"Policy-aligned live analytics foundation for audits, management review, innovation, providers, risk and business continuity. Unsupported fields are shown explicitly.","policy_set":[{"code":"PPD-SGL-SQ-6.1.1","version":"1.2","title":"Internal Assessment and Quality Audits","updated":"15 January 2026"},{"code":"PPD-SGL-SQ-6.2.1","version":"1.3","title":"Management Review","updated":"10 April 2026"},{"code":"PPD-SGL-SQ-6.3.1","version":"1.2","title":"Innovation and Continual Improvement","updated":"15 January 2026"},{"code":"PPD-OE-FN-6.4.1","version":"1.2","title":"Provider's Accreditation and Evaluation","updated":"15 January 2026"},{"code":"PPD-SGL-SQ-6.5.3","version":"1.2","title":"Hazard Identification and Risk Assessment","updated":"15 January 2026"}],"subcriteria":[["6.1.1","Internal Assessment and Quality Audits"],["6.2.1","Management Review"],["6.3.1","Innovation and Continual Improvement"],["6.4.1","Provider Accreditation and Evaluation"],["6.5.3","Hazard Identification and Risk Assessment"]],"filters":[["review_year","Review Year",["All Review Years","2026","2025"]],["department","Department",["All Departments","SGL / SQ","Academic","Student Services","Finance"]],["quality_area","Quality Area",["All Quality Areas","Audit","Management Review","Innovation","Providers","Risk"]],["month","Month",["All Months","January 2026","April 2026","July 2026","December 2026"]]],"sections":{"overview":{"title":"Criterion 6 Overview","charts":[]},"6.1.1":{"title":"Internal Assessment and Quality Audits","charts":[]},"6.2.1":{"title":"Management Review","charts":[]},"6.3.1":{"title":"Innovation and Continual Improvement","charts":[]},"6.4.1":{"title":"Provider's Accreditation and Evaluation","charts":[]},"6.5.3":{"title":"Hazard Identification and Risk Assessment","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_6","defaultSection":"6.1.1","apiSections":{"overview":"6.1.1","6.1.1":"6.1.1","6.2.1":"6.2.1","6.3.1":"6.3.1","6.4.1":"6.4.1","6.5.3":"6.5.3","quality":"6.1.1","sources":"6.1.1"},"panelMap":{"overview":"overview","6.1.1":"6.1.1","6.2.1":"6.2.1","6.3.1":"6.3.1","6.4.1":"6.4.1","6.5.3":"6.5.3","sources":"sources","quality":"sources"}},"criterion_7":{"number":"7","title":"Performance Outcomes","description":"Live, permission-aware analytics foundation for outcome measurement, target achievement and stakeholder performance. Unsupported fields are shown explicitly.","subcriteria":[["7.1.1","Measurement of Outcomes"]],"sections":{"overview":{"title":"Overview","charts":[]},"7.1":{"title":"Measurement of Outcomes","charts":[]},"7.1.1":{"title":"Measurement of Outcomes","charts":[]},"sources":{"title":"Sources and Data Quality","charts":[]},"quality":{"title":"Sources and Data Quality","charts":[]}},"apiMethod":"ucc_intelligence.api.get_criterion_7","defaultSection":"7.1.1","apiSections":{"overview":"7.1.1","7.1.1":"7.1.1","quality":"7.1.1","sources":"7.1.1"},"panelMap":{"overview":"overview","7.1.1":"7.1.1","sources":"sources","quality":"sources"},"filters":[["academic_year","Academic Year",["All Academic Years","2026","2025"]],["student_group","Module Class Details",["All Module Classes"]],["program","Course",["All Courses"]],{"key":"month","label":"Month","type":"month"}]}};
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
// ---------------------------------------------------------------------------
// PER-TAB INSIGHTS CHARTS -- the area, and where it goes
//
// A tab starts with NO charts and one "+ Add chart" button. Whatever a person
// adds is theirs, on that tab, and is stored server-side (see
// analytics/tab_charts.py -- frappe.defaults, per user).
//
// This replaced 222 fixed chart boxes declared in this file: 16 had a real
// Insights query behind them, 206 were blank. Boxes nobody chose, mostly
// showing nothing. Nothing is declared here now, so nothing can be declared
// and then not exist.
// ---------------------------------------------------------------------------
const tabChartState={};

function tabChartKey(criterionId,tab){return criterionId+"::"+tab;}

function tabChartAreaMarkup(tab){
return`<section class="ucc-tab-charts" data-tab-charts="${esc(tab)}">`
+`<div class="ucc-tab-charts-head"><h2>Charts</h2>`
+`<button type="button" class="ucc-add-chart" data-add-chart="${esc(tab)}">+ Add chart</button></div>`
+`<div class="ucc-live-expanded-grid ucc-tab-charts-grid" data-tab-charts-grid="${esc(tab)}"></div></section>`;
}

// analyticsPanelMarkup() already emits an empty [data-live-anchor] between the
// section heading and the Management Questions panel. Mounting there puts the
// charts above the tables without this function needing to know anything about
// the tables -- which is also why the Q&A markup is untouched by any of this.
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
return area;
}

// panelMap can point two tabs at one panel, so an anchor can hold more than
// one area. Only the active tab's is shown.
function syncTabChartVisibility(dashboard,tab){
dashboard.querySelectorAll("[data-tab-charts]").forEach(function(area){
area.hidden=area.dataset.tabCharts!==tab;
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
// ---------------------------------------------------------------------------
// PER-TAB INSIGHTS CHARTS -- loading, rendering, picking, removing
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

function embeddedChartMarkup(chart){
return`<article class="panel ucc-shared-panel ucc-live-generated-card ucc-embedded-chart" data-embedded-chart="${esc(chart.chart)}">`
+`<div class="panel-head ucc-card-header"><div class="ucc-card-heading-copy"><h2>${esc(chart.title)}</h2>`
+`<p class="ucc-card-description">Live from Frappe Insights.</p></div>`
+`<button type="button" class="ucc-remove-chart" data-remove-chart="${esc(chart.chart)}" `
+`title="Remove this chart from the tab" aria-label="Remove ${esc(chart.title)} from this tab">&times;</button></div>`
+`<div class="ucc-embedded-chart-body" data-embedded-chart-body>${tabChartNotice("Loading…")}</div></article>`;
}

function renderTabCharts(dashboard,config,tab){
const area=ensureTabChartArea(dashboard,config,tab);
if(!area)return;
const grid=area.querySelector("[data-tab-charts-grid]");
const state=tabChartState[tabChartKey(dashboard.dataset.demoDashboard,tab)];
if(!state){grid.innerHTML=tabChartNotice("Loading your charts…");loadTabCharts(dashboard,config,tab);return;}
if(state.loading){grid.innerHTML=tabChartNotice("Loading your charts…");return;}
if(state.error){grid.innerHTML=tabChartNotice(state.error);return;}
if(!state.charts.length){
grid.innerHTML=tabChartNotice("No charts on this tab yet. Use “+ Add chart” to embed one from Frappe Insights.");
return;
}
grid.innerHTML=state.charts.map(embeddedChartMarkup).join("");
state.charts.forEach(function(chart){paintEmbeddedChart(grid,chart);});
}

function setTabCharts(dashboard,config,tab,response){
tabChartState[tabChartKey(dashboard.dataset.demoDashboard,tab)]={
charts:(response&&response.charts)||[],loading:false,error:null};
renderTabCharts(dashboard,config,tab);
}

function loadTabCharts(dashboard,config,tab){
const key=tabChartKey(dashboard.dataset.demoDashboard,tab);
if(tabChartState[key])return;
if(!(window.frappe&&frappe.call)){
tabChartState[key]={charts:[],loading:false,error:"Frappe API client unavailable."};return;}
tabChartState[key]={charts:[],loading:true,error:null};
frappe.call({
method:"ucc_intelligence.api.get_tab_charts",
args:{criterion:dashboard.dataset.demoDashboard,tab:tab},
callback(response){setTabCharts(dashboard,config,tab,(response&&response.message)||{});},
error(error){
tabChartState[key]={charts:[],loading:false,error:apiErrorMessage(error)};
renderTabCharts(dashboard,config,tab);
},
});
}

// One embedded chart. A failure is SHOWN as a failure -- there is no second
// data source to quietly fall back to, and pretending otherwise is what made
// the old chart boxes unreadable.
function paintEmbeddedChart(grid,chart){
const card=grid.querySelector(`[data-embedded-chart="${CSS.escape(chart.chart)}"]`);
const body=card&&card.querySelector("[data-embedded-chart-body]");
if(!body)return;
if(!(window.frappe&&frappe.call)){body.innerHTML=tabChartNotice("Frappe API client unavailable.");return;}
frappe.call({
method:"ucc_intelligence.api.get_tab_chart_data",
args:{chart:chart.chart},
callback(response){
const data=(response&&response.message)||{};
if(data.status==="available"&&(data.series||[]).length){paintChartSeries(body,data.series);return;}
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
// or a funnel from two columns is decoration, not information. A chart that
// genuinely needs a different shape should say so in its Insights definition.
function paintChartSeries(node,series){
const max=Math.max.apply(null,series.map(row=>Number(row.value)||0).concat([1]));
node.innerHTML='<div class="ucc-insights-series">'+series.map(row=>{
const value=Number(row.value)||0;
const width=Math.max(1,Math.round((value/max)*100));
return'<div class="ucc-insights-bar"><span class="ucc-insights-bar-label">'+esc(row.label)+"</span>"
+'<span class="ucc-insights-bar-track"><span class="ucc-insights-bar-fill" style="width:'+width+'%"></span></span>'
+'<span class="ucc-insights-bar-value">'+esc(value.toLocaleString())+"</span></div>";
}).join("")+"</div>";
}

// The picker. A search box over Insights queries THIS user can read, and one
// click to embed. No preview step: the chart appears on the tab immediately,
// which is a faster way to find out it was the wrong one than a preview pane.
function openChartPicker(dashboard,config,tab){
openModal("Add a chart to this tab",
'<div class="ucc-chart-picker">'
+'<input type="search" class="ucc-chart-picker-search" data-chart-picker-search '
+'placeholder="Search Frappe Insights charts…" autocomplete="off" aria-label="Search Insights charts">'
+'<p class="ucc-chart-picker-note">Only charts you can already open in Frappe Insights are listed.</p>'
+'<div class="ucc-chart-picker-results" data-chart-picker-results>'+tabChartNotice("Loading…")+"</div></div>");
const modal=ensureModal();
const input=modal.querySelector("[data-chart-picker-search]");
const results=modal.querySelector("[data-chart-picker-results]");
if(!input||!results)return;
let timer=null;
function search(term){
if(!(window.frappe&&frappe.call)){results.innerHTML=tabChartNotice("Frappe API client unavailable.");return;}
frappe.call({
method:"ucc_intelligence.api.search_insights_charts",
args:{term:term||"",limit:20},
callback(response){
const data=(response&&response.message)||{};
const charts=data.charts||[];
if(!charts.length){
results.innerHTML=tabChartNotice(data.message||"No Insights chart matched that search.");return;}
results.innerHTML=charts.map(chart=>
`<button type="button" class="ucc-chart-picker-result" data-pick-chart="${esc(chart.chart)}">`
+`${esc(chart.title)}</button>`).join("");
},
error(error){results.innerHTML=tabChartNotice(apiErrorMessage(error));},
});
}
input.addEventListener("input",function(){
clearTimeout(timer);
timer=setTimeout(function(){search(input.value);},250);
});
results.addEventListener("click",function(event){
const pick=event.target.closest("[data-pick-chart]");
if(!pick)return;
event.preventDefault();
pick.disabled=true;
frappe.call({
method:"ucc_intelligence.api.add_tab_chart",
args:{criterion:dashboard.dataset.demoDashboard,tab:tab,chart:pick.dataset.pickChart},
callback(response){
setTabCharts(dashboard,config,tab,(response&&response.message)||{});
modal.hidden=true;
},
error(error){pick.disabled=false;results.innerHTML=tabChartNotice(apiErrorMessage(error));},
});
});
// An empty search lists the most recently modified, so the picker is useful
// before anyone types anything.
search("");
input.focus();
}

function removeTabChart(dashboard,config,tab,chart){
if(!(window.frappe&&frappe.call))return;
frappe.call({
method:"ucc_intelligence.api.remove_tab_chart",
args:{criterion:dashboard.dataset.demoDashboard,tab:tab,chart:chart},
callback(response){setTabCharts(dashboard,config,tab,(response&&response.message)||{});},
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
.ucc-add-chart{border:1px solid var(--border-color,#d1d8dd);background:var(--fg-color,#fff);border-radius:6px;padding:5px 12px;font-size:12px;font-weight:600;cursor:pointer}
.ucc-add-chart:hover{background:var(--bg-light-gray,#f4f5f6)}
.ucc-tab-charts-notice{padding:14px 2px;font-size:12px;color:var(--text-muted,#8d99a6)}
.ucc-embedded-chart .panel-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.ucc-remove-chart{border:0;background:transparent;font-size:18px;line-height:1;cursor:pointer;color:var(--text-muted,#8d99a6);padding:0 2px}
.ucc-remove-chart:hover{color:var(--text-color,#1f272e)}
.ucc-embedded-chart-body{padding:6px 0 2px}
.ucc-chart-picker-search{width:100%;padding:8px 10px;border:1px solid var(--border-color,#d1d8dd);border-radius:6px;font-size:13px}
.ucc-chart-picker-note{margin:8px 0 4px;font-size:11px;color:var(--text-muted,#8d99a6)}
.ucc-chart-picker-results{display:flex;flex-direction:column;gap:4px;max-height:340px;overflow-y:auto}
.ucc-chart-picker-result{text-align:left;border:1px solid var(--border-color,#d1d8dd);background:var(--fg-color,#fff);border-radius:6px;padding:8px 10px;font-size:13px;cursor:pointer}
.ucc-chart-picker-result:hover{background:var(--bg-light-gray,#f4f5f6)}
.ucc-chart-picker-result[disabled]{opacity:.5;cursor:default}
.ucc-insights-series{display:flex;flex-direction:column;gap:6px;padding:8px 0}
.ucc-insights-bar{display:grid;grid-template-columns:minmax(90px,32%) 1fr auto;gap:8px;align-items:center;font-size:12px}
.ucc-insights-bar-label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ucc-insights-bar-track{background:var(--bg-light-gray,#f4f5f6);border-radius:3px;height:14px;overflow:hidden}
.ucc-insights-bar-fill{display:block;height:100%;background:#2c5aa0;border-radius:3px}
.ucc-insights-bar-value{font-variant-numeric:tabular-nums;font-weight:600}
`;
document.head.appendChild(style);
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
function renderDashboard(dashboard){const config=CONFIG[dashboard.dataset.demoDashboard],state=dashboardState(dashboard),result=state.result;if(!config)return;const tab=activeSection(dashboard);updateDashboardIdentity(dashboard,config,tab);if(state.error&&!result){renderError(dashboard,config,state.error);return;}renderKpis(dashboard,config,result);renderTabCharts(dashboard,config,tab);renderQa(dashboard,result,tab);renderSources(dashboard,result);renderQuality(dashboard,result);renderReadiness(dashboard,config,result);}
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
// No chart manifest to load: charts are not declared by this app any more,
// they are picked per tab from Insights and fetched when the tab renders.
injectTabChartStyles();

platform.querySelectorAll("[data-demo-dashboard]").forEach(function(dashboard){const config=CONFIG[dashboard.dataset.demoDashboard];if(!config)return;ensureTabChartArea(dashboard,config,"overview");syncTabChartVisibility(dashboard,"overview");dashboard.dataset.liveApi="1";dashboard.querySelectorAll("[data-demo-tab]").forEach(button=>button.addEventListener("click",()=>showTab(dashboard,button.dataset.demoTab)));dashboard.querySelectorAll("[data-demo-filter]").forEach(input=>input.addEventListener("change",()=>loadLive(dashboard,true)));dashboard.addEventListener("ucc:live-tool-action",function(event){const action=event.detail&&event.detail.action;const mapped=action==="export-current"?"export-table":action;if(mapped)handleAction(dashboard,mapped);});dashboard.addEventListener("click",function(event){
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
const addChart=event.target.closest("[data-add-chart]");
if(addChart){event.preventDefault();event.stopPropagation();openChartPicker(dashboard,config,addChart.dataset.addChart);return;}
const removeChart=event.target.closest("[data-remove-chart]");
if(removeChart){event.preventDefault();event.stopPropagation();removeTabChart(dashboard,config,activeSection(dashboard),removeChart.dataset.removeChart);return;}
const actionButton=event.target.closest("[data-demo-action]");
if(actionButton){event.preventDefault();event.stopPropagation();handleAction(dashboard,actionButton.dataset.demoAction);return;}
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
