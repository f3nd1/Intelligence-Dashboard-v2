// Consolidates a dashboard's separate "Data Quality" and "Sources" tabs into a
// single "Sources & Data Quality" tab: the Data Quality panel's content is moved
// into the Sources panel and the Data Quality tab button is removed. Shared by
// all three dashboard architectures (demo/C4/C5) via their own tab attributes.
window.__uccMergeSourcesQuality=function(dash,tabAttr,panelAttr){
if(!dash||dash.dataset.sqMerged==="1")return;
const sourcesTab=dash.querySelector(`[${tabAttr}="sources"]`),qualityTab=dash.querySelector(`[${tabAttr}="quality"]`);
const sourcesPanel=dash.querySelector(`[${panelAttr}="sources"]`),qualityPanel=dash.querySelector(`[${panelAttr}="quality"]`);
if(!sourcesTab||!sourcesPanel)return;
dash.dataset.sqMerged="1";
sourcesTab.textContent="Sources & Data Quality";
if(qualityPanel){while(qualityPanel.firstChild)sourcesPanel.appendChild(qualityPanel.firstChild);qualityPanel.remove();}
if(qualityTab)qualityTab.remove();
};
(function () {
"use strict";
const root = typeof root_element !== "undefined"
? root_element.querySelector("#uccIntelligencePlatform")
: document.querySelector("#uccIntelligencePlatform");
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
if (shellToggle) shellToggle.addEventListener("click", function (event) {
event.preventDefault();
event.stopPropagation();
shellCollapsed = !shellCollapsed;
applyShellState();
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
})();
(function(){
const BUILD_ID="UCC-PLATFORM-1.9.6-20260719";
const root=typeof root_element!=="undefined"?root_element.querySelector(".ucc-c5-v41"):document.querySelector(".ucc-c5-v41");if(!root)return;
if(root.dataset.uccBuildInitialized===BUILD_ID){console.warn("[UCC C5] Duplicate initialization ignored",BUILD_ID);return}
root.dataset.uccBuildInitialized=BUILD_ID;
const htmlBuild=root.dataset.buildId||"";
const MAX=5000,LOG_MAX=50000;
const state={progressTimer:null,progressValue:0,loaded:false,data:{},sources:{},qa:[],exceptions:[],quality:[],loading:false,scopeCourses:new Set(),scopeStudentGroups:new Set(),logs:[],resolvedDoctypes:{},requestSeq:0,startedAt:new Date().toISOString(),buildId:BUILD_ID};
const safeJson=value=>{try{return JSON.stringify(value,(key,val)=>/password|token|secret|api[_-]?key|authorization/i.test(key)?"[REDACTED]":val)}catch{return String(value)}};
function addLog(level,category,event,details={}){
const row={sequence:state.logs.length+1,timestamp:new Date().toISOString(),elapsed_ms:Math.round(performance.now()),level,category,event,build_id:BUILD_ID,active_tab:root.dataset.activeTab||"",details:safeJson(details)};
state.logs.push(row);if(state.logs.length>LOG_MAX)state.logs.splice(0,state.logs.length-LOG_MAX);
const count=root.querySelector("[data-log-count]");if(count)count.textContent=String(state.logs.length);
if(level==="ERROR")console.error("[UCC C5]",event,details);else if(level==="WARN")console.warn("[UCC C5]",event,details);else console.debug("[UCC C5]",event,details);
return row;
}
window.addEventListener("error",event=>addLog("ERROR","window","uncaught_error",{message:event.message,filename:event.filename,line:event.lineno,column:event.colno,stack:event.error?.stack}));
window.addEventListener("unhandledrejection",event=>addLog("ERROR","window","unhandled_rejection",{reason:event.reason?.message||String(event.reason),stack:event.reason?.stack}));
addLog("INFO","lifecycle","initialization_started",{url:location.href,user:frappe?.session?.user||"unknown",user_agent:navigator.userAgent});
if(htmlBuild&&htmlBuild!==BUILD_ID){addLog("ERROR","deployment","build_mismatch",{html_build:htmlBuild,javascript_build:BUILD_ID});root.insertAdjacentHTML("afterbegin",`<div class="deployment-warning"><strong>Deployment mismatch:</strong> HTML ${esc(htmlBuild)} · JavaScript ${esc(BUILD_ID)}. Replace all three frontend files and clear cache.</div>`)}
const SOURCE_ALIASES={
"Student Admission UCC":["Shortlisted Applicants","Student Admission UCC"],
"Supplier Rating":["Provider Rating","Supplier Rating"]
};
const SOURCE_ROUTES={
"Shortlisted Applicants":"shortlisted-applicants",
"Student Admission UCC":"student-admission-ucc",
"Provider Rating":"provider-rating",
"Supplier Rating":"supplier-rating"
};
const CFG={
"Academic Year":{mode:"core",purpose:"Academic year filter",fields:["name","academic_year_name","year_start_date","year_end_date"]},
"Student Group":{mode:"core",purpose:"Module Class Details filter and class scope",fields:["name","student_group_name","academic_year","program","course","batch","disabled","max_strength"]},
"Course":{mode:"core",purpose:"5.1 course design",fields:["name","course_name","department","modified"],full:false},
"Program":{mode:"core",purpose:"5.1 programme-course mapping",fields:["name","program_name","department","modified"],full:false},
"Assessment Plan":{mode:"core",purpose:"5.1 and 5.5 assessment planning",fields:["name","assessment_name","student_group","course","program","academic_year","schedule_date","room","examiner","supervisor","maximum_assessment_score"]},
"Assessment Result":{mode:"core",purpose:"5.1 and 5.5 result coverage",fields:["name","assessment_plan","program","course","academic_year","student","student_name","student_group","maximum_score","total_score","grade"]},
"Course Schedule":{mode:"core",purpose:"5.2 class delivery",fields:["name","student_group","instructor","instructor_name","course","schedule_date","room","from_time","to_time","program"]},
"Course Enrollment":{mode:"core",purpose:"5.2 enrollment proxy",fields:["name","student","student_name","course","program","enrollment_date"]},
"Student Attendance":{mode:"core",purpose:"5.2 attendance",fields:["name","student","course_schedule","date","student_group","status","duration_attended","expected_duration"]},
"Module Review":{mode:"core",purpose:"5.1.2 module review records",fields:["name","course","module","module_class_details","date_of_review","status","type_of_review","recommendation","modified"],full:true},
"Course Review":{mode:"core",purpose:"5.1.2 course review records",fields:["name","course","review_date","next_review_date","review_type","review_status","modified"],full:true},
"Student Intake No":{mode:"core",purpose:"5.2.1 intake planning",fields:["name","batch_name","program","course_start_date","course_end_date","modified"],cap:500},
"Module Class Details":{mode:"core",purpose:"5.2.1 and 5.2.2 module operations",fields:["name","program","course","custom_module_status","custom_instructor","custom_instructor_full_name","academic_year","modified"],full:true},
"Student Admission UCC":{mode:"core",purpose:"5.2.1 Shortlisted Applicants admissions and contracts",fields:["name","student_name","program","student_batch","application_status","contract_start","contract_end","modified"],full:true},
"Classroom Observation":{mode:"core",purpose:"5.2.2 teaching observation",fields:["name","date_of_observation","type_of_observation","module_class_details","course","module_name","name_of_teacher","platform_delivery","modified"],full:true},
"Partnership Agreement":{mode:"core",purpose:"5.3.1 signed partnership agreements",fields:["name","party_name","posting_date","start_date","end_date","pa_agreement_type","pa_partner_name","requires_nda","nda_acknowledged","signed_date","ucc_signed_date","modified"],full:true},
"Partnerships Agreement Management":{mode:"core",purpose:"5.3.1 partnership identification, monitoring and evaluation",fields:["name","agreement_title","party_name","type","status","agreement_date","expiry_date","average_identification_and_selection_score","modified"],full:true},
"Supplier Rating":{mode:"core",purpose:"5.3.1 Provider Rating evaluation records",fields:["name","posting_date","year","status","type","document","supplier","evaluation_stage","rating","rating_likert","modified"],cap:500},
"Survey Response":{mode:"core",purpose:"5.4 survey scores and open-ended responses",fields:["name","title","email","program","course","posting_date","frequency","modified"],full:true},
};
const UCC_TERMS={
Program:"Course",
Course:"Module",
Courses:"Modules",
Batch:"Intake No",
Instructor:"Teacher"
};
const SECTION_REGISTRY={
c51:{children:[
{id:"c511",label:"5.1.1 Course Design & Development"},
{id:"c512",label:"5.1.2 Course Review"}
]},
c52:{children:[
{id:"c521",label:"5.2.1 Course Planning"},
{id:"c522",label:"5.2.2 Course Delivery"}
]},
c53:{children:[
{id:"c531",label:"5.3.1 Partnerships"}
]}
};
const C511_SOURCES={
"Course Proposal":{fields:["name","creation","modified","owner","docstatus"],purpose:"Proposal and approvals"},
"Course Review":{fields:["name","creation","modified","owner","docstatus"],purpose:"Validation and improvement"}
};
const C511_GROUPS={
overview:["course_title","mode_of_delivery","academic_level","course_language","programme_structure","proposed_date"],
strategy:["overall_achievement","industry_relevance","skills_development","target_headcount","competitors"],
learner:["target_audience_industry","minimum_age","industry_experience","cognitive_level","prior_knowledge","learning_style","cognitive_development_focus","motivation_level","emotional_state","stress_resilience","social_engagement_level","peer_learning_engagement","teamwork_and_collaboration_skills","special_educational_needs","inclusivity_measures","learning_environment_support","learner_profile_characteristic","mer_academic","mer_language"],
pedagogy:["table_teqa","teaching_technique_offline","teacher_student_ratio_offline","teaching_technique_online","teacher_student_ratio_online","total_duration_ft","total_duration_pt","days_per_week_ft","hour_per_day_ft","days_per_week_pt","hour_per_day_pt","ft_contact_hour_total","pt_contact_hour_total"],
curriculum:["learning_outcomes","module_list","sequencing_and_rationale","course_developer","industrial_attachment_needead","industrial_attachment_details","articulation_pathway","pathway_programme_details","accrediation_y_n","accrediation_details","association_y_n","association_details"],
assessment:["assessment_criteria","assessmnet_descriptions"],
risk:["table_ornh","budget_management","total_budget_fee","total_actual_spending","resource_childable","risk_table","risk_mitigation_childtable","table_odgh","stakeholder_note","documentation_table"],
approval:["approval_status","decision_date","quality_meeting","ssg_approval_date","decision_summary"]
};
const $=s=>root.querySelector(s),$$=s=>Array.from(root.querySelectorAll(s));
const esc=v=>String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
const pct=(n,d)=>d?Math.round(n/d*100):0;
const set=(s,v)=>{const e=$(s);if(e)e.textContent=v};

const C5_READINESS = Object.freeze({
overview:{label:"Criterion 5 Overview",sources:["Academic Year","Student Group","Course","Program"],metrics:[["Courses in selected scope",["Course"]],["Module readiness",["Course"]],["Course-to-programme mapping",["Course","Program"]],["Source availability",[]],["Questions answered",[]],["Open exceptions",[]]]},
c511:{label:"Criterion 5.1.1",sources:["Course","Program","Course Proposal","Course Review","Assessment Plan","Assessment Result"],metrics:[["Proposal approval",["Course Proposal"]],["Proposal decision time",["Course Proposal"]],["Module evidence completeness",["Course"]],["Learning outcomes coverage",["Course"]],["Lesson-plan coverage",["Course"]],["Assessment-design coverage",["Assessment Plan"]],["Review status",["Course Review"]],["Result coverage",["Assessment Result"]]]},
c512:{label:"Criterion 5.1.2",sources:["Module Review","Course Review"],metrics:[["Module review coverage",["Module Review"]],["Course review coverage",["Course Review"]],["Review status",["Module Review","Course Review"]],["Overdue reviews",["Course Review"]],["Action-plan availability",["Module Review"]],["Recommendation follow-up",["Course Review"]]]},
c521:{label:"Criterion 5.2.1",sources:["Student Intake No","Module Class Details","Student Admission UCC","Course Schedule"],metrics:[["Intake readiness",["Student Intake No"]],["Module class readiness",["Module Class Details"]],["Admission coverage",["Student Admission UCC"]],["Schedule coverage",["Course Schedule"]],["Teacher assignment",["Module Class Details"]],["Contract date completeness",["Student Admission UCC"]]]},
c522:{label:"Criterion 5.2.2",sources:["Module Class Details","Classroom Observation","Survey Response"],metrics:[["Delivery readiness",["Module Class Details"]],["Observation coverage",["Classroom Observation"]],["Observation ratings",["Classroom Observation"]],["Survey coverage",["Survey Response"]],["Delivery exceptions",["Classroom Observation"]],["Teacher coverage",["Module Class Details"]]]},
c531:{label:"Criterion 5.3.1",sources:["Partnership Agreement","Partnerships Agreement Management","Supplier Rating"],metrics:[["Agreement lifecycle",["Partnership Agreement"]],["Signature completion",["Partnership Agreement"]],["Monitoring frequency",["Partnerships Agreement Management"]],["Evaluation outcome",["Partnerships Agreement Management"]],["Provider rating",["Supplier Rating"]],["Renewal readiness",["Partnership Agreement","Supplier Rating"]]]},
c54:{label:"Criterion 5.4",sources:["Survey Response","Course Schedule","Student Attendance"],metrics:[["Survey response coverage",["Survey Response"]],["Module survey score",["Survey Response"]],["Question-level score",["Survey Response"]],["Learning attendance",["Student Attendance"]],["Scheduled learning sessions",["Course Schedule"]],["At-risk indicators",["Student Attendance"]]]},
c55:{label:"Criterion 5.5",sources:["Assessment Plan","Assessment Result","Course","Student Group"],metrics:[["Assessment-plan coverage",["Assessment Plan"]],["Assessment-result coverage",["Assessment Result"]],["Grade availability",["Assessment Result"]],["Examiner assignment",["Assessment Plan"]],["Room assignment",["Assessment Plan"]],["Course assessment coverage",["Course","Assessment Plan"]]]},
quality:{label:"Criterion 5 Data Quality",sources:["Course","Program","Course Schedule","Assessment Result"],metrics:[["Missing fields",["Course"]],["Invalid date order",["Course Schedule"]],["Result completeness",["Assessment Result"]],["Source availability",[]]]},
sources:{label:"Criterion 5 Sources",sources:Object.keys(CFG),metrics:[["Source registry",[]],["Readable sources",[]],["Permission status",[]],["Record counts",[]]]}
});
function c5ReadinessDefinition(){ return C5_READINESS[root.dataset.activeTab||"overview"]||C5_READINESS.overview; }
function c5ReadinessState(){
const definition=c5ReadinessDefinition();
const sourceRows=definition.sources.map(function(name){const source=state.sources[name]||{status:"Not loaded"};return{name,status:source.status||"Not loaded",available:source.status==="Available"};});
const metricRows=definition.metrics.map(function(metric){const name=metric[0],dependencies=metric[1]||[];return{name,dependencies,available:dependencies.every(function(source){return sourceReady(source);})};});
return{definition,sourceRows,metricRows,availableSources:sourceRows.filter(function(row){return row.available;}).length,availableMetrics:metricRows.filter(function(row){return row.available;}).length};
}
function renderC5Readiness(){
const notice=$("[data-c5-source-notice]");if(!notice)return;
const readiness=c5ReadinessState(),sourceTotal=readiness.sourceRows.length,metricTotal=readiness.metricRows.length;
const issues=(sourceTotal-readiness.availableSources)+(metricTotal-readiness.availableMetrics);
notice.hidden=false;notice.dataset.dismissed="0";notice.dataset.status=issues?"warning":"available";
const title=notice.querySelector("[data-c5-readiness-title]"),copy=notice.querySelector("[data-c5-readiness-copy]");
if(title)title.textContent=issues?"Criterion 5 live analytics active with limitations.":"Criterion 5 live analytics active.";
if(copy)copy.textContent="Live data connected · "+readiness.availableSources+" of "+sourceTotal+" sources available · "+readiness.availableMetrics+" of "+metricTotal+" metrics available"+(issues?" · "+issues+" item"+(issues===1?"":"s")+" need review":"");
}
function openC5ReadinessDetails(){
const readiness=c5ReadinessState();let overlay=root.querySelector("[data-c5-readiness-dialog]");
if(!overlay){overlay=document.createElement("div");overlay.className="ucc-readiness-dialog";overlay.dataset.c5ReadinessDialog="1";root.appendChild(overlay);}
overlay.innerHTML=`<div class="ucc-readiness-dialog-card" role="dialog" aria-modal="true"><header><div><strong>${esc(readiness.definition.label)}</strong><span>Source and metric readiness</span></div><button type="button" data-c5-readiness-close>×</button></header><div class="ucc-readiness-dialog-body"><section><h3>Sources</h3><div class="table-wrap"><table><thead><tr><th>Source</th><th>Status</th></tr></thead><tbody>${readiness.sourceRows.map(function(row){return`<tr><td>${esc(row.name)}</td><td>${badge(row.available?"Good":"Warning")} ${esc(row.status)}</td></tr>`;}).join("")}</tbody></table></div></section><section><h3>Metrics</h3><div class="table-wrap"><table><thead><tr><th>Metric</th><th>Required source</th><th>Status</th></tr></thead><tbody>${readiness.metricRows.map(function(row){return`<tr><td>${esc(row.name)}</td><td>${esc(row.dependencies.join(" / ")||"Calculated in browser")}</td><td>${badge(row.available?"Good":"Warning")}</td></tr>`;}).join("")}</tbody></table></div></section></div></div>`;
overlay.hidden=false;overlay.querySelector("[data-c5-readiness-close]")?.addEventListener("click",function(){overlay.hidden=true;});overlay.addEventListener("click",function(event){if(event.target===overlay)overlay.hidden=true;},{once:true});
}

function setC5Notice(message,noticeStatus="available"){
const notice=$("[data-c5-source-notice]");if(!notice)return;
if(noticeStatus==="available"){renderC5Readiness();return;}
if(noticeStatus!=="available")notice.dataset.dismissed="0";
notice.hidden=false;notice.dataset.status=noticeStatus;
const strong=notice.querySelector("[data-c5-readiness-title]"),copy=notice.querySelector("[data-c5-readiness-copy]");
if(strong)strong.textContent=noticeStatus==="loading"?"Loading Criterion 5 analytics…":"Criterion 5 data notice.";
if(copy)copy.textContent=message;
}
const status=m=>{
const text=String(m||"");
const noticeStatus=/error|failed|unavailable|permission/i.test(text)
?"error"
:/loading|preparing/i.test(text)
?"loading"
:"available";
setC5Notice(text,noticeStatus);
};
// Surface the real Frappe error. A missing DocType raises DoesNotExistError
// (HTTP 404); its detail lives on the xhr's responseJSON (exception / exc_type /
// _server_messages) and status, none of which the old one-liner read, so it fell
// back to a permission-sounding string and got misclassified. Append the HTTP
// status so classifyError can key off 404/403 even when the body is empty.
const errText=e=>UCCShared.errorText(e);
$("[data-c5-readiness-details]")?.addEventListener("click",openC5ReadinessDetails);
function setProgress(value,task){
const overlay=$("[data-loading-overlay]"),fill=$("[data-progress-fill]");
overlay.classList.remove("hidden");fill.style.width=`${Math.max(0,Math.min(100,value))}%`;
set("[data-progress-value]",`${Math.round(value)}%`);set("[data-progress-task]",task);
}
function hideProgress(){setTimeout(()=>$("[data-loading-overlay]").classList.add("hidden"),180)}
function classifyError(message){return UCCShared.classifyError(message)}
function call(method,args,context={}){
const id=++state.requestSeq,start=performance.now();
addLog("INFO","request","request_started",{id,method,context,args});
return new Promise((resolve,reject)=>frappe.call({
method,args,
callback:r=>{addLog("INFO","request","request_succeeded",{id,method,duration_ms:Math.round(performance.now()-start),context,row_count:Array.isArray(r?.message)?r.message.length:undefined});resolve(r?.message??r)},
error:e=>{const message=errText(e);addLog("ERROR","request","request_failed",{id,method,duration_ms:Math.round(performance.now()-start),context,message,http_status:e?.httpStatus||e?.status});reject(new Error(message))}
}))
}
async function list(dt,fields,filters=[]){return call("frappe.client.get_list",{doctype:dt,fields,filters,limit_page_length:MAX,order_by:"modified desc"},{doctype:dt,operation:"list",fields,filters})}
async function doc(dt,name){return call("frappe.client.get",{doctype:dt,name},{doctype:dt,operation:"get",name})}
// Bounded-concurrency map: runs fn over items in batches of `limit` in parallel,
// preserving order. Replaces per-record sequential hydration so a section's
// document loads run concurrently instead of one round-trip at a time.
async function mapLimit(items,limit,fn){const out=new Array(items.length);for(let i=0;i<items.length;i+=limit){const batch=items.slice(i,i+limit),res=await Promise.all(batch.map((it,j)=>fn(it,i+j)));for(let j=0;j<res.length;j++)out[i+j]=res[j];}return out;}
async function resolveDoctype(canonical){
if(state.resolvedDoctypes[canonical])return state.resolvedDoctypes[canonical];
const candidates=SOURCE_ALIASES[canonical]||[canonical];
addLog("INFO","source","resolution_started",{canonical,candidates});
let lastError=null;
for(const candidate of candidates){
try{
await list(candidate,["name"],[]);
state.resolvedDoctypes[canonical]=candidate;
addLog("INFO","source","resolution_succeeded",{canonical,resolved:candidate,candidates});
return candidate;
}catch(error){
lastError=error;
addLog("WARN","source","resolution_candidate_failed",{canonical,candidate,error:error.message});
}
}
addLog("ERROR","source","resolution_failed",{canonical,candidates,error:lastError?.message});
throw lastError||new Error(`No readable DocType candidate for ${canonical}`);
}
async function safeList(canonical,resolved,cfg,filters){
try{return await list(resolved,cfg.fields,filters)}
catch(error){
if(classifyError(error.message)!=="Field mismatch")throw error;
addLog("WARN","source","field_fallback_started",{canonical,resolved,configured_fields:cfg.fields,error:error.message});
const rows=await list(resolved,["name","modified"],filters);
addLog("INFO","source","field_fallback_succeeded",{canonical,resolved,row_count:rows.length});
return rows;
}
}
async function load(dt,filters=[]){
const c=CFG[dt];if(!c){addLog("WARN","source","source_not_configured",{canonical:dt});return[]}
const attempted=SOURCE_ALIASES[dt]||[dt];
try{
const resolved=await resolveDoctype(dt);
let rows=await safeList(dt,resolved,c,filters);
if(c.full){rows=await mapLimit(rows.slice(0,500),8,async r=>{try{return await doc(resolved,r.name)}catch(error){addLog("WARN","source","document_hydration_failed",{canonical:dt,resolved,name:r.name,error:error.message});return r}})}
else if(c.cap){rows=rows.slice(0,c.cap)}
state.sources[dt]={status:"Available",purpose:c.purpose,count:rows.length,resolved,attempted,route:SOURCE_ROUTES[resolved]||resolved.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"")};
addLog("INFO","source","source_loaded",{canonical:dt,resolved,count:rows.length,filters,full:!!c.full});
return rows;
}catch(e){
const sourceStatus=classifyError(e.message);
state.sources[dt]={status:sourceStatus,purpose:c.purpose,error:e.message,count:0,attempted,resolved:null};
addLog("ERROR","source","source_load_failed",{canonical:dt,attempted,status:sourceStatus,error:e.message,filters});
return[]
}
}
async function hydrateViaServer(dts){
if(state.c5ServerHydrateFailed)return false;
try{
const message=await new Promise((resolve,reject)=>frappe.call({
method:"ucc_analytics_criterion_5",
args:{payload:JSON.stringify({action:"c511_hydrate",limit:1000})},
callback:response=>resolve(response?.message),
error:reject
}));
if(!message||message.ok!==true||!message.data)throw new Error(message?.message||"c511_hydrate is unavailable");
let used=false;
dts.forEach(dt=>{const rows=message.data[dt];if(Array.isArray(rows)&&rows.length){state.data[dt]=rows;used=true;}});
if(!used)throw new Error("c511_hydrate returned no documents");
addLog("INFO","source","server_hydration_used",{doctypes:dts,counts:dts.map(dt=>(message.data[dt]||[]).length)});
return true;
}catch(error){
state.c5ServerHydrateFailed=true;
addLog("WARN","source","server_hydration_unavailable",{error:error.message});
return false;
}
}
// Section 5.1.1 model from the server (c511_analytics). Returns the exact
// buildC511() shape (checks/moduleRows re-hydrated to full record objects) so
// renderC511 consumes it unchanged, or null if the action is unavailable so the
// caller falls back to the client buildC511().
async function fetchC511Model(){
try{
const message=await new Promise((resolve,reject)=>frappe.call({
method:"ucc_analytics_criterion_5",
args:{payload:JSON.stringify({action:"c511_analytics",limit:1000})},
callback:response=>resolve(response?.message),
error:reject
}));
if(!message||message.ok!==true||!message.model||!message.records)throw new Error(message?.message||"c511_analytics is unavailable");
const m=message.model,rec=message.records;
const pByName=new Map((rec.proposals||[]).map(p=>[p.name,p]));
const cByName=new Map((rec.courses||[]).map(c=>[c.name,c]));
const adapted={
proposals:rec.proposals||[],reviews:rec.reviews||[],courses:rec.courses||[],programs:rec.programs||[],plans:rec.plans||[],
checks:(m.checks||[]).map(x=>({record:pByName.get(x.record)||{name:x.record},groups:x.groups,rate:x.rate,status:x.status})),
moduleRows:(m.moduleRows||[]).map(x=>({record:cByName.get(x.record)||{name:x.record},lo:x.lo,lessons:x.lessons,teaching:x.teaching,assessment:x.assessment,resources:x.resources,coverage:x.coverage,zero:x.zero,complete:x.complete})),
topics:m.topics,criteria:m.criteria,approved:m.approved,readiness:m.readiness,gaps:m.gaps,
proposalApproved:m.proposalApproved,reviewApproved:m.reviewApproved,ssgCount:m.ssgCount,overdue:m.overdue,avgDecisionDays:m.avgDecisionDays,avgActions:m.avgActions
};
addLog("INFO","source","c511_server_model_used",{proposals:adapted.proposals.length,reviews:adapted.reviews.length,courses:adapted.courses.length});
return adapted;
}catch(error){
addLog("WARN","source","c511_server_model_unavailable",{error:error.message});
return null;
}
}
// Section 5.1.2 model from the server (c512_analytics), re-hydrated into the
// exact buildC512() shape (dataset records mapped back to full objects) so the
// render branch consumes it unchanged; null when the action is unavailable so
// the caller falls back to the client buildC512().
async function fetchC512Model(){
try{
const message=await new Promise((resolve,reject)=>frappe.call({
method:"ucc_analytics_criterion_5",
args:{payload:JSON.stringify({action:"c512_analytics",limit:1000})},
callback:response=>resolve(response?.message),
error:reject
}));
if(!message||message.ok!==true||!message.model||!message.records)throw new Error(message?.message||"c512_analytics is unavailable");
const rec=message.records,mr=rec.mr||[],cr=rec.cr||[],m=message.model;
const byName=new Map([...mr,...cr].map(r=>[r.name,r]));
const hydrate=ds=>(ds||[]).map(e=>{const out={label:e.label,value:e.value,records:(e.records||[]).map(n=>byName.get(n)||{name:n})};if(e.doctype!==undefined)out.doctype=e.doctype;return out;});
addLog("INFO","source","c512_server_model_used",{module_reviews:mr.length,course_reviews:cr.length});
return{mr,cr,kpis:m.kpis,reviewLevel:hydrate(m.reviewLevel),schedule:hydrate(m.schedule),moduleStatus:hydrate(m.moduleStatus),courseStatus:hydrate(m.courseStatus),reviewType:hydrate(m.reviewType),actions:hydrate(m.actions),recommendationStatus:hydrate(m.recommendationStatus),evidence:hydrate(m.evidence),cycle:hydrate(m.cycle),coverage:hydrate(m.coverage),actionsCompletion:hydrate(m.actionsCompletion),actionAging:hydrate(m.actionAging),missingEvidence:hydrate(m.missingEvidence),followup:hydrate(m.followup)};
}catch(error){
addLog("WARN","source","c512_server_model_unavailable",{error:error.message});
return null;
}
}
// Section 5.2.1 model from the server (c521_analytics), re-hydrated into the
// exact buildC521() shape; null when unavailable so the caller falls back to
// the client buildC521().
async function fetchC521Model(){
try{
const message=await new Promise((resolve,reject)=>frappe.call({
method:"ucc_analytics_criterion_5",
args:{payload:JSON.stringify({action:"c521_analytics",filters:currentFilters()})},
callback:response=>resolve(response?.message),
error:reject
}));
if(!message||message.ok!==true||!message.model||!message.records)throw new Error(message?.message||"c521_analytics is unavailable");
const rec=message.records,m=message.model;
const byName=new Map([...(rec.intakes||[]),...(rec.classes||[]),...(rec.schedules||[]),...(rec.apps||[])].map(r=>[r.name,r]));
const hydrate=ds=>(ds||[]).map(e=>{const out={label:e.label,value:e.value,records:(e.records||[]).map(n=>byName.get(n)||{name:n})};if(e.doctype!==undefined)out.doctype=e.doctype;return out;});
addLog("INFO","source","c521_server_model_used",{intakes:(rec.intakes||[]).length,classes:(rec.classes||[]).length,schedules:(rec.schedules||[]).length,apps:(rec.apps||[]).length});
const out={intakes:rec.intakes||[],classes:rec.classes||[],schedules:rec.schedules||[],apps:rec.apps||[],kpis:m.kpis,exceptions:m.exceptions};
["intakesReady","flow","classStatus","schedule","admission","teacher","sessionReadiness","contracts","dateCompleteness","unscheduled","scheduleCompleteness","roomClashes","teacherClashes","contractVsStart","contractExceptions"].forEach(k=>out[k]=hydrate(m[k]));
return out;
}catch(error){
addLog("WARN","source","c521_server_model_unavailable",{error:error.message});
return null;
}
}
// Section 5.2.2 model from the server (c522_analytics), re-hydrated into the
// exact buildC522() shape; null when unavailable so the caller falls back.
async function fetchC522Model(){
try{
const message=await new Promise((resolve,reject)=>frappe.call({
method:"ucc_analytics_criterion_5",
args:{payload:JSON.stringify({action:"c522_analytics",filters:currentFilters()})},
callback:response=>resolve(response?.message),
error:reject
}));
if(!message||message.ok!==true||!message.model||!message.records)throw new Error(message?.message||"c522_analytics is unavailable");
const rec=message.records,m=message.model;
const obs=rec.obs||[],surveys=rec.surveys||[];
const byName=new Map([...obs,...(rec.classes||[]),...surveys].map(r=>[r.name,r]));
const hydrate=ds=>(ds||[]).map(e=>{const out={label:e.label,value:e.value,records:(e.records||[]).map(n=>byName.get(n)||{name:n})};if(e.doctype!==undefined)out.doctype=e.doctype;return out;});
addLog("INFO","source","c522_server_model_used",{observations:obs.length,surveys:surveys.length});
const out={obs,surveys,kpis:m.kpis};
["coverage","observationType","platform","ratings","surveyCategories","notice","signoff","concerns","plannedDelivered","teacherCoverage","moduleCoverage","observationMode","signoffAging","ratingDistribution","strengths","improvements","surveyVolume","deliveryExceptions"].forEach(k=>out[k]=hydrate(m[k]));
return out;
}catch(error){
addLog("WARN","source","c522_server_model_unavailable",{error:error.message});
return null;
}
}
// Section 5.3.1 model from the server (c531_analytics), re-hydrated into the
// exact buildC531() shape; null when unavailable so the caller falls back.
async function fetchC531Model(){
try{
const message=await new Promise((resolve,reject)=>frappe.call({
method:"ucc_analytics_criterion_5",
args:{payload:JSON.stringify({action:"c531_analytics"})},
callback:response=>resolve(response?.message),
error:reject
}));
if(!message||message.ok!==true||!message.model||!message.records)throw new Error(message?.message||"c531_analytics is unavailable");
const rec=message.records,m=message.model;
const signed=rec.signed||[],managed=rec.managed||[],ratings=rec.ratings||[];
const byName=new Map();
[...signed,...managed,...ratings].forEach(r=>{if(!byName.has(r.name))byName.set(r.name,r);});
const hydrate=ds=>(ds||[]).map(e=>{const out={label:e.label,value:e.value,records:(e.records||[]).map(n=>byName.get(n)||{name:n})};if(e.doctype!==undefined)out.doctype=e.doctype;return out;});
const signedByName=new Map(signed.map(r=>[r.name,r]));
addLog("INFO","source","c531_server_model_used",{signed:signed.length,managed:managed.length,ratings:ratings.length});
const out={signed,managed,ratings,kpis:m.kpis,signedStatus:(m.signedStatus||[]).map(x=>({...(signedByName.get(x.name)||{name:x.name}),derived_status:x.derived_status}))};
["status","type","expiry","nda","monitoring","monitoringType","evaluation","scores","ratingStage","threshold","lifecycle","signature","risk","monitoringRecency","decisions","missingControls","qualityCompleteness"].forEach(k=>out[k]=hydrate(m[k]));
return out;
}catch(error){
addLog("WARN","source","c531_server_model_unavailable",{error:error.message});
return null;
}
}
async function fetchC5QAModel(){
try{
const srcMap={};Object.keys(state.sources||{}).forEach(k=>{srcMap[k]=state.sources[k].status;});
const message=await new Promise((resolve,reject)=>frappe.call({
method:"ucc_analytics_criterion_5",
args:{payload:JSON.stringify({action:"c5_qa",filters:currentFilters(),survey_filter:surveyFilters(),sources:srcMap})},
callback:response=>resolve(response?.message),
error:reject
}));
if(!message||message.ok!==true||!message.model||!message.records)throw new Error(message?.message||"c5_qa is unavailable");
const pool=new Map();
Object.values(message.records).forEach(list=>(list||[]).forEach(r=>{if(r&&r.name&&!pool.has(r.name))pool.set(r.name,r);}));
const rows=(message.model.rows||[]).map(row=>{
const out={...row};
if(Array.isArray(row.records))out.records=row.records.map(n=>pool.get(n)||{name:n});
return out;
});
addLog("INFO","source","c5_qa_server_model_used",{rows:rows.length,pool:pool.size});
return{rows,exceptions:message.model.exceptions||[]};
}catch(error){
addLog("WARN","source","c5_qa_server_model_unavailable",{error:error.message});
return null;
}
}
async function hydrateDocuments(dt){
const rows=state.data[dt]||[];
setProgress(Math.min(90,8),`Loading ${(UCC_TERMS[dt]||dt).toLowerCase()} design details…`);
state.data[dt]=await mapLimit(rows,8,async row=>{
if(row.topics||row.courses||Object.keys(row).length>8)return row;
try{return await doc(state.resolvedDoctypes[dt]||dt,row.name)}catch(error){addLog("WARN","source","document_hydration_failed",{canonical:dt,name:row.name,error:error.message});return row}
});
}
async function loadC511Source(dt){
const cfg=C511_SOURCES[dt];
try{
const rows=await list(dt,cfg.fields);
setProgress(Math.min(94,20),`Loading ${dt} (${Math.min(rows.length,300)})`);
const full=await mapLimit(rows.slice(0,300),8,async row=>{try{return await doc(dt,row.name)}catch{return row}});
state.sources[dt]={status:"Available",count:full.length,purpose:cfg.purpose};return full;
}catch(e){state.sources[dt]={status:/not found|does ?not ?exist|doesnotexist|no such|404/i.test(e.message)?"Not installed":/permission|forbidden|not permitted|403/i.test(e.message)?"Permission denied":"Unavailable",count:0,error:e.message,purpose:cfg.purpose};return[]}
}
function hasEvidence(v){if(Array.isArray(v))return v.length>0;if(v&&typeof v==="object")return Object.keys(v).length>0;return v!==null&&v!==undefined&&String(v).trim()!==""&&v!==0}
function findEvidenceField(record,candidates){
const normal=s=>String(s).replace(/[^a-z0-9]/gi,"").toLowerCase();
for(const field of candidates){if(Object.prototype.hasOwnProperty.call(record,field)&&hasEvidence(record[field]))return{field,value:record[field]}}
const keys=Object.keys(record||{});
for(const candidate of candidates){const n=normal(candidate),hit=keys.find(k=>normal(k)===n||normal(k).includes(n)||n.includes(normal(k)));if(hit&&hasEvidence(record[hit]))return{field:hit,value:record[hit]}}
return null;
}
function c511Group(record,group){const hits=C511_GROUPS[group].map(field=>findEvidenceField(record,[field])).filter(Boolean);return{ok:hits.length>0,fields:[...new Set(hits.map(x=>x.field))]}}
function c511Status(record){return record.approval_status||"Not set"}
function formatDate(value){
if(!value)return"—";
const d=/^\d{4}-\d{2}-\d{2}$/.test(String(value))?new Date(`${value}T00:00:00`):new Date(value);
if(Number.isNaN(d.getTime()))return String(value);
return `${String(d.getDate()).padStart(2,"0")} ${["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][d.getMonth()]} ${d.getFullYear()}`;
}
function buildC511(){
const proposals=state.data["Course Proposal"]||[],reviews=state.data["Course Review"]||[],courses=state.data.Course||[],programs=state.data.Program||[],plans=state.data["Assessment Plan"]||[];
const checks=proposals.map(record=>{const groups={};Object.keys(C511_GROUPS).forEach(group=>groups[group]=c511Group(record,group));const complete=Object.values(groups).filter(x=>x.ok).length;return{record,groups,rate:pct(complete,Object.keys(groups).length),status:c511Status(record)}});
const topics=courses.filter(x=>x.topics?.length).length,criteria=courses.filter(x=>x.assessment_criteria?.length).length,approved=checks.filter(x=>/approved|accepted|endorsed|submitted/i.test(x.status)||x.record.docstatus===1).length;
const readiness=Object.keys(C511_GROUPS).map(group=>({label:group.charAt(0).toUpperCase()+group.slice(1),value:pct(checks.filter(x=>x.groups[group].ok).length,checks.length)}));
const gaps=[];
checks.forEach(x=>Object.entries(x.groups).forEach(([group,result])=>{
if(!result.ok)gaps.push({
doctype:"Course Proposal",
record:x.record.name,
area:group,
issue:`No populated ${group} evidence detected`,
severity:"Risk"
});
}));
const moduleRows=courses.map(record=>{
const lo=(record.custom_list_of_learning_objective||record.topics||[]).length||0;
const lessons=(record.custom_lesson_plans||[]).length||0;
const teaching=(record.custom_teaching_approach||[]).length||0;
const assessment=(record.assessment_criteria||[]).length||0;
const resources=(record.custom_resource||[]).length||0;
const areas=[lo,lessons,teaching,assessment,resources],coverage=pct(areas.filter(v=>v>0).length,5);
return{record,lo,lessons,teaching,assessment,resources,coverage,zero:areas.every(v=>v===0),complete:areas.every(v=>v>0)};
});
moduleRows.forEach(x=>{
[
["learning outcomes",x.lo],
["lesson plans",x.lessons],
["teaching approach",x.teaching],
["assessment criteria",x.assessment],
["resources",x.resources]
].forEach(([area,value])=>{
if(!value)gaps.push({
doctype:"Course",
record:x.record.name,
area,
issue:`Missing ${area}`,
severity:"Risk"
});
});
});
if(!reviews.length){
gaps.push({doctype:"Course Review",record:"—",area:"validation",issue:"No readable Course Review records",severity:"Risk"});
}else{
reviews.forEach(review=>{
if(!hasEvidence(review.recommendations||review.module_recommendation_summary)){
gaps.push({doctype:"Course Review",record:review.name,area:"recommendations",issue:"Missing recommendations",severity:"Warning"});
}
if(!(review.actionplan_progress||[]).length){
gaps.push({doctype:"Course Review",record:review.name,area:"action plan",issue:"No action plan rows",severity:"Risk"});
}
if(review.next_review_date&&new Date(`${review.next_review_date}T00:00:00`)<new Date()){
gaps.push({doctype:"Course Review",record:review.name,area:"review cycle",issue:"Next review date is overdue",severity:"Risk"});
}
});
}
const proposalApproved=proposals.filter(x=>x.approval_status==="Approved").length;
const reviewApproved=reviews.filter(x=>x.review_status==="Approved").length;
const ssgCount=proposals.filter(x=>x.ssg_approval_date).length;
const overdue=reviews.filter(x=>x.next_review_date&&new Date(`${x.next_review_date}T00:00:00`)<new Date()).length;
const avgDecisionDays=(()=>{const vals=proposals.map(x=>x.proposed_date&&x.decision_date?(new Date(`${x.decision_date}T00:00:00`)-new Date(`${x.proposed_date}T00:00:00`))/86400000:null).filter(v=>Number.isFinite(v)&&v>=0);return vals.length?Math.round(vals.reduce((a,b)=>a+b,0)/vals.length):null})();
const actionCounts=reviews.map(x=>(x.actionplan_progress||[]).length||0);
const avgActions=actionCounts.length?Math.round(actionCounts.reduce((a,b)=>a+b,0)/actionCounts.length*10)/10:0;
return{proposals,reviews,courses,programs,plans,checks,topics,criteria,approved,readiness,gaps,moduleRows,proposalApproved,reviewApproved,ssgCount,overdue,avgDecisionDays,avgActions};
}
function renderC511(){
const a=state.c511Server||buildC511();
const setk=(key,value,note)=>{set(`[data-c511-kpi="${key}"]`,value);if(note)set(`[data-c511-note="${key}"]`,note)};
const moduleComplete=a.moduleRows.filter(x=>x.complete).length,zeroModules=a.moduleRows.filter(x=>x.zero).length;
setk("proposal-approval",`${pct(a.proposalApproved,a.proposals.length)}%`,`${a.proposalApproved} of ${a.proposals.length}`);
setk("module-completeness",`${pct(moduleComplete,a.moduleRows.length)}%`,`${moduleComplete} of ${a.moduleRows.length}`);
setk("review-approval",`${pct(a.reviewApproved,a.reviews.length)}%`,`${a.reviewApproved} of ${a.reviews.length}`);
setk("ssg-coverage",`${pct(a.ssgCount,a.proposals.length)}%`,`${a.ssgCount} of ${a.proposals.length}`);
setk("zero-modules",zeroModules,"All five evidence areas empty");
setk("overdue-reviews",a.overdue,"Next review date passed");
setk("proposal-total",a.proposals.length);setk("proposal-approved",a.proposalApproved);setk("proposal-pending",a.proposals.length-a.proposalApproved);setk("decision-time",a.avgDecisionDays===null?"—":`${a.avgDecisionDays}d`);setk("proposal-ssg",`${pct(a.ssgCount,a.proposals.length)}%`);
setk("module-total",a.moduleRows.length);setk("module-complete",moduleComplete);setk("module-zero",zeroModules);setk("module-lo",`${pct(a.moduleRows.filter(x=>x.lo>0).length,a.moduleRows.length)}%`);setk("module-lessons",`${pct(a.moduleRows.filter(x=>x.lessons>0).length,a.moduleRows.length)}%`);setk("module-assessment",`${pct(a.moduleRows.filter(x=>x.assessment>0).length,a.moduleRows.length)}%`);
const pendingReviews=a.reviews.length-a.reviewApproved,noActions=a.reviews.filter(x=>(x.actionplan_progress||[]).length===0).length;
setk("review-total",a.reviews.length);setk("review-approved",a.reviewApproved);setk("review-pending",pendingReviews);setk("review-overdue",a.overdue);setk("review-actions",a.avgActions);setk("review-no-actions",noActions);
const attention=[
{label:"Modules with zero evidence",value:zeroModules,doctype:"Course",records:a.moduleRows.filter(x=>x.zero).map(x=>x.record)},
{label:"Modules missing assessment criteria",value:a.moduleRows.filter(x=>x.assessment===0).length,doctype:"Course",records:a.moduleRows.filter(x=>x.assessment===0).map(x=>x.record)},
{label:"Reviews without action plans",value:noActions,doctype:"Course Review",records:a.reviews.filter(x=>(x.actionplan_progress||[]).length===0)},
{label:"Proposals without SSG date",value:a.proposals.length-a.ssgCount,doctype:"Course Proposal",records:a.proposals.filter(x=>!x.ssg_approval_date)},
{label:"Overdue course reviews",value:a.overdue,doctype:"Course Review",records:a.reviews.filter(x=>x.next_review_date&&new Date(`${x.next_review_date}T00:00:00`)<new Date())}
].sort((x,y)=>y.value-x.value);
const attentionBox=$("[data-c511-attention]");
if(attentionBox){
attentionBox.innerHTML=attention.map((x,i)=>`<div class="attention-item" tabindex="0" data-attention="${i}"><span class="attention-rank">${i+1}</span><span>${esc(x.label)}<br><small>Click to view affected records</small></span><strong class="attention-value">${x.value}</strong></div>`).join("");
attentionBox.querySelectorAll("[data-attention]").forEach(item=>{
const open=()=>{const row=attention[Number(item.dataset.attention)];openAffected(row.label,row.doctype,row.records)};
item.addEventListener("click",open);
item.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();open()}});
});
}
const proposalBody=$('[data-table="c511-proposals"]');if(proposalBody)proposalBody.innerHTML=a.checks.map(x=>`<tr><td><a class="open-record-link" href="${doctypeRoute("Course Proposal",x.record.name)}" target="_blank" rel="noopener">${esc(x.record.name)}</a></td>${Object.keys(C511_GROUPS).map(group=>`<td>${badge(x.groups[group].ok?"Good":"Risk")}</td>`).join("")}</tr>`).join("");
const designBody=$('[data-table="c511-design"]');if(designBody)designBody.innerHTML=a.moduleRows.map(x=>`<tr><td><a class="open-record-link" href="${doctypeRoute("Course",x.record.name)}" target="_blank" rel="noopener">${esc(x.record.course_name||x.record.name)}</a></td><td>${x.lo}</td><td>${x.lessons}</td><td>${x.teaching}</td><td>${x.assessment}</td><td>${x.resources}</td></tr>`).join("");
const reviewBody=$('[data-table="c511-reviews"]');if(reviewBody)reviewBody.innerHTML=a.reviews.map(x=>`<tr><td><a class="open-record-link" href="${doctypeRoute("Course Review",x.name)}" target="_blank" rel="noopener">${esc(x.name)}</a></td><td>${esc(x.course||"—")}</td><td>${esc(formatDate(x.review_date))}</td><td>${esc(x.review_status||"—")}</td><td>${hasEvidence(x.recommendations||x.module_recommendation_summary)?"Available":"Missing"}</td><td>${(x.actionplan_progress||[]).length}</td></tr>`).join("");
const proposalStatusBody=$('[data-table="c511-proposal-status"]');
if(proposalStatusBody)proposalStatusBody.innerHTML=a.proposals.map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(x.approval_status||"Pending / Other")}</td><td>${esc(formatDate(x.decision_date))}</td><td><a class="open-record-link" href="${doctypeRoute("Course Proposal",x.name)}" target="_blank" rel="noopener">Open ↗</a></td></tr>`).join("");
const reviewStatusBody=$('[data-table="c511-review-status"]');
if(reviewStatusBody)reviewStatusBody.innerHTML=a.reviews.map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(x.review_status||"Unknown")}</td><td>${esc(formatDate(x.review_date))}</td><td><a class="open-record-link" href="${doctypeRoute("Course Review",x.name)}" target="_blank" rel="noopener">Open ↗</a></td></tr>`).join("");
const reviewTimelineBody=$('[data-table="c511-review-timeline"]');
if(reviewTimelineBody)reviewTimelineBody.innerHTML=a.reviews.map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(x.course||"—")}</td><td>${esc(formatDate(x.review_date))}</td><td>${esc(x.review_status||"Unknown")}</td><td>${esc(formatDate(x.next_review_date))}</td><td><a class="open-record-link" href="${doctypeRoute("Course Review",x.name)}" target="_blank" rel="noopener">Open ↗</a></td></tr>`).join("")||'<tr><td colspan="6">No Course Review records available.</td></tr>';
const gapBody=$('[data-table="c511-gaps"]');if(gapBody)gapBody.innerHTML=a.gaps.map(x=>`<tr><td>${x.record&&x.record!=="—"?`<a class="open-record-link" href="${doctypeRoute(x.doctype,x.record)}" target="_blank" rel="noopener">${esc(x.record)}</a>`:esc(x.record)}</td><td>${esc(x.doctype==="Course"?"Module":x.doctype)}</td><td>${esc(x.area)}</td><td>${esc(x.issue)}</td><td>${badge(x.severity||(/zero|missing|no readable/i.test(x.issue)?"Risk":"Warning"))}</td></tr>`).join("");
fillC511SupplementaryTables(a);
const avg=a.checks.length?Math.round(a.checks.reduce((sum,x)=>sum+x.rate,0)/a.checks.length):0;
const questions=[
["1","Are course development needs documented through a Course Proposal?",`${a.proposals.length} readable Course Proposal record(s).`,"Course Proposal.name",a.proposals.length?"Good":"Risk"],
["2","Do proposals contain complete overview information?",`${a.readiness.find(x=>x.label==="Overview")?.value||0}% contain all required overview evidence fields.`,"Course Proposal overview fields",(a.readiness.find(x=>x.label==="Overview")?.value||0)===100?"Good":"Warning"],
["3","Do proposals document strategic rationale and market need?",`${a.readiness.find(x=>x.label==="Strategy")?.value||0}% contain strategic evidence.`,"overall_achievement, industry_relevance, skills_development, target_headcount, competitors",(a.readiness.find(x=>x.label==="Strategy")?.value||0)===100?"Good":"Warning"],
["4","Do proposals define learner profile and entry requirements?",`${a.readiness.find(x=>x.label==="Learner")?.value||0}% contain learner-profile evidence.`,"target_audience_industry, learner_profile_characteristic, mer_academic, mer_language",(a.readiness.find(x=>x.label==="Learner")?.value||0)===100?"Good":"Warning"],
["5","Do proposals define pedagogy and delivery arrangements?",`${a.readiness.find(x=>x.label==="Pedagogy")?.value||0}% contain pedagogy/delivery evidence.`,"table_teqa, teaching_technique_offline, teaching_technique_online",(a.readiness.find(x=>x.label==="Pedagogy")?.value||0)===100?"Good":"Warning"],
["6","Is curriculum structure defined?",`${a.readiness.find(x=>x.label==="Curriculum")?.value||0}% of proposals contain curriculum evidence; ${a.moduleRows.length} Module record(s) are available.`,"learning_outcomes, module_list, sequencing_and_rationale; Course records",(a.readiness.find(x=>x.label==="Curriculum")?.value||0)===100?"Good":"Warning"],
["7","Is the assessment framework defined?",`${a.readiness.find(x=>x.label==="Assessment")?.value||0}% of proposals contain assessment evidence; ${a.moduleRows.filter(x=>x.assessment>0).length}/${a.moduleRows.length} Modules have assessment criteria.`,"Course Proposal.assessment_criteria; Course.assessment_criteria",(a.readiness.find(x=>x.label==="Assessment")?.value||0)===100?"Good":"Warning"],
["8","Are resources, risk and stakeholder inputs documented?",`${a.readiness.find(x=>x.label==="Risk")?.value||0}% contain resource/risk/stakeholder evidence.`,"resource_childable, risk_table, risk_mitigation_childtable, table_odgh",(a.readiness.find(x=>x.label==="Risk")?.value||0)===100?"Good":"Warning"],
["9","Is approval and governance evidence recorded?",`${a.readiness.find(x=>x.label==="Approval")?.value||0}% contain proposal decision evidence; ${a.proposalApproved}/${a.proposals.length} are Approved.`,"approval_status, decision_date, quality_meeting, ssg_approval_date, decision_summary",(a.readiness.find(x=>x.label==="Approval")?.value||0)===100?"Good":"Warning"],
["10","Is SSG approval recorded?",`${a.ssgCount} proposal(s) have SSG approval dates.`,"Course Proposal.ssg_approval_date",a.ssgCount===a.proposals.length?"Good":"Warning"],
["11","Are detailed Module materials available?",`${a.moduleRows.filter(x=>x.lessons>0).length}/${a.moduleRows.length} Modules have lesson-plan rows.`,"Course.custom_list_of_learning_objective, custom_lesson_plans, custom_teaching_approach, assessment_criteria, custom_resource",moduleComplete===a.moduleRows.length?"Good":"Risk"],
["12","Is Course Review completed?",`${a.reviews.length} Course Review record(s); ${a.reviewApproved} Approved.`,"Course Review.review_date, review_status, module_review, recommendations, actionplan_progress",a.reviewApproved===a.reviews.length?"Good":"Warning"],
["13","What is overall proposal evidence completeness?",`${avg}% average across eight evidence areas.`,"Exact Course Proposal fields supplied by UCC",avg===100?"Good":avg>=70?"Warning":"Risk"]
];
const qaBody=$('[data-table="c511-qa"]');if(qaBody)qaBody.innerHTML=questions.map(row=>{const doctype=sourceDoctypes(row[3])[0]||"";const action=doctype?`<a class="record-link ucc-qa-action" href="${doctypeListRoute(doctype)}" target="_blank" rel="noopener">View matching records ↗</a>`:"";return`<tr><td>5.1.1</td><td>${esc(row[1])}</td><td><div>${esc(row[2])}</div>${action}</td><td>${sourceCell(row[3])}</td><td>${badge(row[4])}</td></tr>`;}).join("");
state.c511Gaps=a.gaps;
requestAnimationFrame(()=>setTimeout(renderVisibleC511Charts,40));
} function currentFilters(){
const mi=$('[data-filter="month"]'),now=new Date();if(mi&&!mi.value)mi.value=`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}`;
const [y,m]=(mi.value||"").split("-").map(Number),last=new Date(y,m,0).getDate();
return{year:$('[data-filter="academic_year"]').value||"",student_group:$('[data-filter="student_group"]').value||"",program:$('[data-filter="program"]').value||"",start:`${y}-${String(m).padStart(2,"0")}-01`,end:`${y}-${String(m).padStart(2,"0")}-${String(last).padStart(2,"0")}`,month:mi.value};
}
function setOptions(sel,vals,label,labelMap={}){
const e=$(sel),cur=e.value,arr=[...new Set(vals.filter(Boolean))].sort();
e.innerHTML=`<option value="">${label}</option>`+arr.map(v=>`<option value="${esc(v)}">${esc(labelMap[v]||v)}</option>`).join("");
if(arr.includes(cur))e.value=cur;
}
function group(rows,key){
const m=new Map;
(rows||[]).forEach(r=>{const k=r?.[key]||"Not Set";m.set(k,(m.get(k)||0)+1)});
return [...m].map(([label,value])=>({label,value})).sort((a,b)=>b.value-a.value);
}
function groupRecords(rows,key,doctype){
const m=new Map;
(rows||[]).forEach(record=>{
const label=record?.[key]||"Not Set";
if(!m.has(label))m.set(label,[]);
m.get(label).push(record);
});
return [...m].map(([label,records])=>({label,value:records.length,records,doctype})).sort((a,b)=>b.value-a.value);
}
function badge(s){const c=s==="Good"?"good":s==="Warning"?"warn":"risk";return`<span class="badge ${c}">${esc(s)}</span>`}
const C5_VISUAL_DESCRIPTIONS={"target-gaps":"Compares each academic system area against its target readiness level.","c511-radar":"Compares evidence strength across every course design and development control area.","c511-heatmap":"Grids evidence coverage against each course design control area.","c511-proposal-donut":"Shows the current status mix of course proposals, from drafted to approved.","c511-review-donut":"Shows the current status mix of course reviews, from due to complete.","c511-gap-funnel":"Compares identified evidence gaps by how severe each one is.","c512-review-level":"Compares review coverage across the different review levels applied.","c512-module-status":"Shows the current status mix of module reviews, from due to complete.","c512-course-status":"Shows the current status mix of course reviews, from due to complete.","c512-recommendation-status":"Gauges what share of previous recommendations have been implemented.","c521-intakes":"Gauges how ready each intake is ahead of its scheduled start.","c521-class-status":"Shows the current status mix of module classes, from planned to active.","c521-schedule":"Gauges what share of module classes have a completed schedule.","c521-teacher":"Gauges what share of module classes have a teacher assigned.","c522-coverage":"Gauges how much of scheduled delivery has a completed observation.","c522-observation-type":"Compares delivery observations across the different types conducted.","c522-ratings":"Compares observation ratings across each area being assessed.","c522-signoff":"Gauges what share of delivery observations have completed sign-off.","c531-status":"Shows the current status mix of partnership agreements.","c531-nda":"Gauges what share of partnerships have a completed NDA on file.","c531-monitoring":"Compares partnerships across the monitoring methods applied.","c531-evaluation":"Shows the outcome mix of completed partnership evaluations.","survey-module-score":"Compares survey scores achieved across each module.","survey-type-count":"Shows how student surveys are distributed across each survey type.","learning-risk":"Highlights students currently flagged as at academic risk.","assessment-trend":"Tracks the number of assessment plans created across recent months.","grade":"Shows how student grades are distributed across the grading scale.","assessment-controls":"Gauges how many assessment controls are documented and in place."};
window.UCCC5VisualDescriptions=C5_VISUAL_DESCRIPTIONS;
const C5_DISABLED_VISUALS=new Set(["assessment-quality","c511-decision-time","c511-gap-sunburst","c511-module-bubbles","c511-module-radial","c511-module-stream","c511-network","c511-proposal-bars","c511-review-actions","c511-review-timeline","c512-action-aging-v110","c512-actions","c512-actions-completion-v110","c512-coverage-v110","c512-cycle-v110","c512-evidence","c512-followup-v110","c512-missing-evidence-v110","c512-review-type","c512-schedule","c521-admission","c521-contract-exceptions-v110","c521-contract-vs-start-v110","c521-contracts","c521-date-completeness-v110","c521-flow","c521-room-clashes-v110","c521-schedule-completeness-v110","c521-session-readiness","c521-teacher-clashes-v110","c521-unscheduled-v110","c522-concerns","c522-delivery-exceptions-v110","c522-improvements-v110","c522-module-coverage-v110","c522-notice","c522-observation-mode-v110","c522-planned-delivered-v110","c522-platform","c522-rating-distribution-v110","c522-signoff-aging-v110","c522-strengths-v110","c522-survey-categories","c522-survey-volume-v110","c522-teacher-coverage-v110","c531-decisions-v110","c531-expiry","c531-lifecycle-v110","c531-missing-controls-v110","c531-monitoring-recency-v110","c531-monitoring-type","c531-quality-completeness-v110","c531-rating-stage","c531-risk-v110","c531-scores","c531-signature-v110","c531-threshold","c531-type","delivery-controls","learning-support","schedule","survey-question-score"]);
window.UCCC5DisabledVisuals=C5_DISABLED_VISUALS;
function chartNode(n){return $(`[data-chart="${n}"]`)}
function openChartDrill(key,index){
const row=(state.chartDrills?.[key]||[])[Number(index)];
if(!row||!Array.isArray(row.records)||!row.records.length)return;
openAffected(`${row.label}: ${row.value}`,row.doctype,row.records);
}
function drillValue(key,index,row){
if(Array.isArray(row.records)&&row.records.length&&(row.doctype||row.records.some(record=>record?._doctype))){
return `<button type="button" class="count-drill" data-chart-drill="${esc(key)}" data-chart-row="${index}" title="Open matching records">${esc(row.value)} <span aria-hidden="true">↗</span></button>`;
}
return esc(row.value??row.count??"—");
}
function bindChartDrills(scope=root){
scope.querySelectorAll("[data-chart-drill]").forEach(button=>{
if(button.dataset.boundChartDrill)return;
button.dataset.boundChartDrill="1";
button.addEventListener("click",()=>openChartDrill(button.dataset.chartDrill,button.dataset.chartRow));
});
}
function ensureChartCompanion(name,rows){
const chart=chartNode(name);if(!chart)return;
const panel=chart.closest(".panel");if(!panel)return;
state.chartDrills=state.chartDrills||{};
state.chartDrills[name]=Array.isArray(rows)?rows:[];
if(panel.querySelector(`[data-card-toggle]`)&&!panel.querySelector(`[data-card-toggle="${name}-auto-card"]`))return;
let toggle=panel.querySelector(`[data-card-toggle="${name}-auto-card"]`),diagram,table;
if(!toggle){
let head=panel.querySelector(".panel-head");
if(!head){
const h=panel.querySelector("h2");
head=document.createElement("div");head.className="panel-head";
if(h){h.parentNode.insertBefore(head,h);head.appendChild(h)}else panel.insertBefore(head,panel.firstChild);
}
toggle=document.createElement("div");toggle.className="mini-toggle";toggle.dataset.cardToggle=`${name}-auto-card`;
toggle.innerHTML='<button type="button" class="active" data-card-view="diagram">Diagram</button><button type="button" data-card-view="table">Table</button>';
head.appendChild(toggle);
diagram=document.createElement("div");diagram.dataset.cardPanel=`${name}-auto-card-diagram`;
chart.parentNode.insertBefore(diagram,chart);diagram.appendChild(chart);
table=document.createElement("div");table.dataset.cardPanel=`${name}-auto-card-table`;table.className="hidden";
table.innerHTML='<div class="table-wrap"><table><thead><tr><th>Label</th><th>Value</th></tr></thead><tbody></tbody></table></div>';
diagram.parentNode.insertBefore(table,diagram.nextSibling);
toggle.querySelectorAll("[data-card-view]").forEach(btn=>btn.addEventListener("click",()=>{
toggle.querySelectorAll("[data-card-view]").forEach(x=>x.classList.toggle("active",x===btn));
diagram.classList.toggle("hidden",btn.dataset.cardView!=="diagram");
table.classList.toggle("hidden",btn.dataset.cardView!=="table");
}));
}else{
diagram=chart.parentNode;
table=diagram.nextElementSibling;
}
if(!table)return;
const body=table.querySelector("tbody");
const safeRows=Array.isArray(rows)?rows:[];
body.innerHTML=safeRows.length?safeRows.map((x,index)=>`<tr><td>${esc(x.label??x.name??"—")}</td><td>${drillValue(name,index,x)}</td></tr>`).join(""):'<tr><td colspan="2">No records found in the selected scope.</td></tr>';
bindChartDrills(table);
}
function empty(n,msg){const e=chartNode(n);if(e)e.innerHTML=`<div class="empty">${esc(msg)}</div>`}
// Shared ucc-demo-* component renderers so Criterion 5 charts match the
// appearance of Criteria 1-4/6/7 (which use these same CSS components).
function c5Fin(v){const n=Number(v);return Number.isFinite(n)?n:0;}
function c5Bars(el,rows){const pairs=(rows||[]).map(r=>[r.label,c5Fin(r.value)]),max=Math.max(...pairs.map(p=>p[1]),1);el.innerHTML=`<div class="ucc-demo-bars">${pairs.map(p=>`<div class="ucc-demo-bar"><label>${esc(p[0])}</label><div><i style="width:${Math.max(4,p[1]/max*100)}%"></i></div><strong>${esc(p[1])}</strong></div>`).join("")}</div>`;}
function c5DonutView(el,rows){const pairs=(rows||[]).map(r=>[r.label,c5Fin(r.value)]).filter(p=>p[1]>0),total=pairs.reduce((s,p)=>s+p[1],0)||1;let cur=0;const stops=pairs.map((p,i)=>{const a=cur/total*360;cur+=p[1];const b=cur/total*360;return`var(--ucc-chart-${i%6}) ${a}deg ${b}deg`;}).join(",");el.innerHTML=`<div class="ucc-demo-donut-layout"><div class="ucc-demo-donut" style="background:conic-gradient(${stops})"><span>${esc(total)}</span><small>Total</small></div><div class="ucc-demo-legend">${pairs.map((p,i)=>`<div><i style="background:var(--ucc-chart-${i%6})"></i><span>${esc(p[0])}</span><strong>${esc(p[1])}</strong></div>`).join("")}</div></div>`;}
function c5FunnelView(el,rows){const pairs=(rows||[]).map(r=>[r.label,c5Fin(r.value)]),max=Math.max(...pairs.map(p=>p[1]),1);el.innerHTML=`<div class="ucc-demo-funnel">${pairs.map(p=>`<div class="ucc-demo-funnel-stage" style="width:${Math.max(38,p[1]/max*100)}%"><span>${esc(p[0])}</span><strong>${esc(p[1])}</strong></div>`).join("")}</div>`;}
function c5TrendView(el,rows){const data=rows||[],width=560,height=250,pad=38,max=Math.max(...data.map(r=>c5Fin(r.value)),1),step=(width-pad*2)/Math.max(1,data.length-1);const pts=data.map((r,i)=>[pad+i*step,height-pad-(c5Fin(r.value)/max)*(height-pad*2)]);el.innerHTML=`<div class="ucc-demo-trend"><svg viewBox="0 0 ${width} ${height}"><line class="axis" x1="${pad}" y1="${height-pad}" x2="${width-pad}" y2="${height-pad}"></line><polyline points="${pts.map(p=>p.join(",")).join(" ")}"></polyline>${pts.map((p,i)=>`<circle cx="${p[0]}" cy="${p[1]}" r="5"></circle><text x="${p[0]}" y="${height-10}" text-anchor="middle">${esc(data[i].label)}</text>`).join("")}</svg></div>`;}
function c5RadarView(el,rows){const data=(rows||[]).filter(r=>r.label);if(!data.length){el.innerHTML='<div class="empty">No records found in the selected scope.</div>';return;}const size=320,cx=160,cy=160,radius=105,count=Math.max(data.length,3),max=Math.max(...data.map(r=>c5Fin(r.value)),1);const points=data.map((r,i)=>{const a=-Math.PI/2+i*2*Math.PI/count,rr=radius*(c5Fin(r.value)/max);return[cx+Math.cos(a)*rr,cy+Math.sin(a)*rr];});const axes=data.map((r,i)=>{const a=-Math.PI/2+i*2*Math.PI/count,x=cx+Math.cos(a)*radius,y=cy+Math.sin(a)*radius,lx=cx+Math.cos(a)*(radius+28),ly=cy+Math.sin(a)*(radius+28);return`<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}"></line><text x="${lx}" y="${ly}" text-anchor="middle">${esc(r.label)}</text>`;}).join("");el.innerHTML=`<div class="ucc-demo-radar"><svg viewBox="0 0 ${size} ${size}"><circle cx="${cx}" cy="${cy}" r="${radius}"></circle><circle cx="${cx}" cy="${cy}" r="${radius*.66}"></circle><circle cx="${cx}" cy="${cy}" r="${radius*.33}"></circle>${axes}<polygon points="${points.map(p=>p.join(",")).join(" ")}"></polygon></svg></div>`;}
function c5MatrixView(el,rows){const data=rows||[],max=Math.max(...data.map(r=>c5Fin(r.total||r.value)),1);el.innerHTML=`<div class="ucc-demo-matrix">${data.map(r=>`<div style="--ucc-intensity:${Math.max(.18,c5Fin(r.value)/(c5Fin(r.total)||max))}"><span>${esc(r.label)}</span><strong>${esc(r.display!=null?r.display:r.value)}</strong></div>`).join("")}</div>`;}
function bar(n,rows){
rows=(rows||[]).map(row=>({...row,value:Number.isFinite(Number(row.value))?Number(row.value):0}));
ensureChartCompanion(n,rows);
const el=chartNode(n);if(!el)return;if(!rows.length)return empty(n,"No records found in the selected scope.");
c5Bars(el,rows);
}
function line(n,rows){
rows=(rows||[]).map(row=>({...row,value:Number.isFinite(Number(row.value))?Number(row.value):0}));
ensureChartCompanion(n,rows);
const el=chartNode(n);if(!el)return;if(!rows.length)return empty(n,"No trend data");
c5TrendView(el,rows);
}
function csv(name,rows){if(!rows.length)return;const keys=Object.keys(rows[0]),q=v=>`"${String(v??"").replaceAll('"','""')}"`,text=[keys.join(","),...rows.map(r=>keys.map(k=>q(r[k])).join(","))].join("\n"),a=document.createElement("a");a.href=URL.createObjectURL(new Blob([text],{type:"text/csv"}));a.download=name;a.click();URL.revokeObjectURL(a.href)}
function deriveScope(){
const f=currentFilters(),groups=state.data["Student Group"]||[],programs=state.data.Program||[];
const scopedGroups=groups.filter(g=>(!f.year||g.academic_year===f.year)&&(!f.program||g.program===f.program)&&(!f.student_group||g.name===f.student_group));
state.scopeStudentGroups=new Set(scopedGroups.map(g=>g.name));
const courses=new Set(scopedGroups.map(g=>g.course).filter(Boolean));
if(!f.student_group&&f.program){
const p=programs.find(x=>x.name===f.program);
(p?.courses||[]).forEach(c=>courses.add(c.course));
}
if(!f.student_group&&!f.program) (state.data.Course||[]).forEach(c=>courses.add(c.name));
state.scopeCourses=courses;
}
function scopedRows(){
const f=currentFilters(),d=state.data,groupNames=state.scopeStudentGroups;
const schedules=(d["Course Schedule"]||[]).filter(x=>(!f.student_group&&!f.year||groupNames.has(x.student_group))&&(!f.program||x.program===f.program));
const scheduleNames=new Set(schedules.map(x=>x.name));
const attendance=(d["Student Attendance"]||[]).filter(x=>scheduleNames.has(x.course_schedule));
const plans=(d["Assessment Plan"]||[]).filter(x=>(!f.year||x.academic_year===f.year)&&(!f.program||x.program===f.program)&&(!f.student_group||x.student_group===f.student_group));
const planNames=new Set(plans.map(x=>x.name));
const results=(d["Assessment Result"]||[]).filter(x=>(!f.year||x.academic_year===f.year)&&(!f.program||x.program===f.program)&&(!f.student_group||x.student_group===f.student_group)&&(!planNames.size||planNames.has(x.assessment_plan)));
const courses=(d.Course||[]).filter(x=>state.scopeCourses.has(x.name));
const enroll=(d["Course Enrollment"]||[]).filter(x=>(!f.program||x.program===f.program)&&(!state.scopeCourses.size||state.scopeCourses.has(x.course)));
return{courses,schedules,attendance,plans,results,enroll};
}
function compute(){
deriveScope();const s=scopedRows(),topics=s.courses.filter(x=>x.topics?.length).length,criteria=s.courses.filter(x=>x.assessment_criteria?.length).length;
const schedNames=new Set(s.schedules.map(x=>x.name)),attNames=new Set(s.attendance.map(x=>x.course_schedule).filter(x=>schedNames.has(x)));
const planNames=new Set(s.plans.map(x=>x.name)),resultPlanNames=new Set(s.results.map(x=>x.assessment_plan).filter(x=>planNames.has(x)));
const metrics=[
{criterion:"5.1",question:"What proportion of courses in scope have curriculum topics configured?",current:pct(topics,s.courses.length),target:100,source:"Course.topics on scoped Course documents"},
{criterion:"5.1",question:"What proportion of courses in scope have assessment criteria configured?",current:pct(criteria,s.courses.length),target:100,source:"Course.assessment_criteria on scoped Course documents"},
{criterion:"5.2",question:"What proportion of scheduled classes have an instructor assigned?",current:pct(s.schedules.filter(x=>x.instructor).length,s.schedules.length),target:100,source:"Course Schedule.instructor"},
{criterion:"5.2",question:"What proportion of scheduled classes have a room assigned?",current:pct(s.schedules.filter(x=>x.room).length,s.schedules.length),target:100,source:"Course Schedule.room"},
{criterion:"5.2",question:"What proportion of scheduled classes have at least one attendance record?",current:pct(attNames.size,schedNames.size),target:100,source:"Distinct Student Attendance.course_schedule ÷ distinct Course Schedule.name"},
{criterion:"5.5",question:"What proportion of assessment plans have at least one linked assessment result?",current:pct(resultPlanNames.size,planNames.size),target:95,source:"Distinct Assessment Result.assessment_plan ÷ Assessment Plan.name"}
].map(x=>({...x,gap:x.current-x.target,status:x.current>=x.target?"Good":x.current>=x.target-10?"Warning":"Risk"}));
return{s,metrics,topics,criteria,attNames,resultPlanNames};
}
function buildQuality(c){
const {s}=c,resultKeys=new Map;s.results.forEach(r=>{const k=`${r.assessment_plan}|${r.student}`;resultKeys.set(k,(resultKeys.get(k)||0)+1)});
state.quality=[
{check:"Schedule missing programme",count:s.schedules.filter(x=>!x.program).length,source:"Course Schedule.program"},
{check:"Schedule missing course",count:s.schedules.filter(x=>!x.course).length,source:"Course Schedule.course"},
{check:"Schedule missing instructor",count:s.schedules.filter(x=>!x.instructor).length,source:"Course Schedule.instructor"},
{check:"Attendance missing status",count:s.attendance.filter(x=>!x.status).length,source:"Student Attendance.status"},
{check:"Enrollment missing course",count:s.enroll.filter(x=>!x.course).length,source:"Course Enrollment.course"},
{check:"Result score above maximum",count:s.results.filter(x=>Number(x.total_score)>Number(x.maximum_score)).length,source:"Assessment Result total_score / maximum_score"},
{check:"Result missing grade",count:s.results.filter(x=>!x.grade).length,source:"Assessment Result.grade"},
{check:"Duplicate result key",count:[...resultKeys.values()].filter(v=>v>1).length,source:"assessment_plan + student"}
].map(x=>({...x,status:x.count?"Risk":"Good"}));
const b=$('[data-table="quality"]');if(b)b.innerHTML=state.quality.map(x=>`<tr><td>${esc(x.check)}</td><td>${x.count}</td><td>${esc(x.source)}</td><td>${badge(x.status)}</td></tr>`).join("");
}
const DOCTYPE_DISPLAY={
"Student Admission UCC":"Shortlisted Applicants",
"Supplier Rating":"Provider Rating",
"Course Schedule":"Module Schedule",
"Student Group":"Module Class Details",
"Program":"Course",
"Course":"Module"
};
function displayDoctype(doctype){return DOCTYPE_DISPLAY[doctype]||doctype}
function resolvedDoctype(doctype){return state.resolvedDoctypes[doctype]||doctype}
function routeSlug(doctype){
const resolved=resolvedDoctype(doctype);
return SOURCE_ROUTES[resolved]||String(resolved||"").trim().toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
}
function doctypeRoute(doctype,name){return `/app/${routeSlug(doctype)}/${encodeURIComponent(name)}`}
function doctypeListRoute(doctype){return `/app/${routeSlug(doctype)}`}
const SOURCE_DOCTYPES=[
"Course Proposal","Module Review","Course Review","Assessment Plan","Assessment Result",
"Course Schedule","Student Attendance","Student Group","Student Intake No","Student Admission UCC",
"Classroom Observation","Partnership Agreement","Partnerships Agreement Management","Supplier Rating",
"Program","Course","Survey Response","Academic Year"
];
function sourceDoctypes(source,explicit=[]){
const text=String(source||"");
const detected=SOURCE_DOCTYPES.filter(doctype=>new RegExp(`\\b${doctype.replace(/[.*+?^${}()|[\\]\\]/g,"\\$&")}\\b`,"i").test(text));
return [...new Set([...(explicit||[]),...detected].filter(Boolean))];
}
function sourceCell(source,explicit=[]){
const doctypes=sourceDoctypes(source,explicit);
const links=doctypes.length
?`<div class="source-links">${doctypes.map(doctype=>`<a class="source-doctype-link" href="${doctypeListRoute(doctype)}" target="_blank" rel="noopener">Open ${esc(displayDoctype(doctype))} list ↗</a>`).join("")}</div>`
:'<div class="source-unavailable">No confirmed DocType link</div>';
return `<div>${esc(source)}</div>${links}`;
}
function fillC511SupplementaryTables(a){
const networkBody=$('[data-table="c511-network"]');
if(networkBody){
const rows=a.programs.flatMap(program=>(program.courses||[]).map(item=>({
courseName:program.program_name||program.name,
courseKey:program.name,
moduleName:item.course_name||item.course,
moduleKey:item.course
})));
networkBody.innerHTML=rows.length
? rows.map(row=>[
"<tr>",
`<td>${esc(row.courseName)}</td>`,
`<td>${esc(row.moduleName)}</td>`,
`<td><a class="open-record-link" href="${doctypeRoute("Program",row.courseKey)}" target="_blank" rel="noopener">Open Course ↗</a></td>`,
`<td><a class="open-record-link" href="${doctypeRoute("Course",row.moduleKey)}" target="_blank" rel="noopener">Open Module ↗</a></td>`,
"</tr>"
].join("")).join("")
: '<tr><td colspan="4">No Course → Module mapping records found.</td></tr>';
}
const decisionBody=$('[data-table="c511-decision-time"]');
if(decisionBody){
const byYear=new Map();
a.proposals.forEach(x=>{
if(!x.proposed_date||!x.decision_date)return;
const days=(new Date(`${x.decision_date}T00:00:00`)-new Date(`${x.proposed_date}T00:00:00`))/86400000;
if(!Number.isFinite(days)||days<0)return;
const year=String(x.proposed_date).slice(0,4);
const entry=byYear.get(year)||{count:0,total:0};
entry.count+=1;
entry.total+=days;
byYear.set(year,entry);
});
const rows=Array.from(byYear.entries())
.sort((a,b)=>a[0].localeCompare(b[0]))
.map(([year,entry])=>({year,count:entry.count,avg:Math.round(entry.total/entry.count)}));
decisionBody.innerHTML=rows.length
? rows.map(row=>`<tr><td>${esc(row.year)}</td><td>${row.count}</td><td>${row.avg}d</td></tr>`).join("")
: '<tr><td colspan="3">No proposal decision-date pairs available.</td></tr>';
}
const constellationBody=$('[data-table="c511-module-constellation"]');
if(constellationBody){
constellationBody.innerHTML=a.moduleRows.length
? a.moduleRows.map(x=>`<tr><td>${esc(x.record.course_name||x.record.name)}</td><td>${x.lo}</td><td>${x.lessons}</td><td>${x.teaching}</td><td>${x.assessment}</td><td>${x.resources}</td><td>${x.coverage}%</td><td><a class="open-record-link" href="${doctypeRoute("Course",x.record.name)}" target="_blank" rel="noopener">Open ↗</a></td></tr>`).join("")
: '<tr><td colspan="8">No Module evidence records found.</td></tr>';
}
const coverageBody=$('[data-table="c511-module-coverage"]');
if(coverageBody){
const total=a.moduleRows.length||0;
const counts=[
{label:"Outcomes",value:a.moduleRows.filter(x=>x.lo>0).length},
{label:"Lesson plans",value:a.moduleRows.filter(x=>x.lessons>0).length},
{label:"Teaching",value:a.moduleRows.filter(x=>x.teaching>0).length},
{label:"Assessment",value:a.moduleRows.filter(x=>x.assessment>0).length},
{label:"Resources",value:a.moduleRows.filter(x=>x.resources>0).length}
];
coverageBody.innerHTML=counts.length
? counts.map(row=>`<tr><td>${esc(row.label)}</td><td>${row.value}</td><td>${total}</td><td>${pct(row.value,total)}%</td></tr>`).join("")
: '<tr><td colspan="4">No Module evidence coverage data available.</td></tr>';
}
}
function openAffected(title,doctype,records){
const dialog=$("[data-dialog]"),head=$("[data-dialog-head]"),body=$("[data-dialog-body]"),heading=$("[data-dialog-title]");
if(!dialog||!head||!body)return;
if(heading)heading.textContent=title;
head.innerHTML="<tr><th>Record</th><th>Source</th><th>Open</th></tr>";
body.innerHTML=(records||[]).map(record=>{
const name=typeof record==="string"?record:record.name;
const recordDoctype=typeof record==="string"?doctype:(record._doctype||doctype);
const label=typeof record==="string"?record:(record.course_name||record.program_name||record.assessment_name||record.agreement_title||record.party_name||record.student_name||record.name);
return `<tr><td>${esc(label)}</td><td>${esc(displayDoctype(recordDoctype||"—"))}</td><td>${recordDoctype&&name?`<a href="${doctypeRoute(recordDoctype,name)}" target="_blank" rel="noopener">Open in new tab ↗</a>`:"—"}</td></tr>`;
}).join("")||'<tr><td colspan="3">No affected records.</td></tr>';
if(typeof dialog.showModal==="function")dialog.showModal();
}
function renderFallbackBars(name,rows,suffix="%"){
const el=$(`[data-chart="${name}"]`);if(!el)return;
const safe=(rows||[]).slice(0,12);
el.innerHTML=safe.length?safe.map(row=>`<div style="display:grid;grid-template-columns:minmax(110px,1fr) 3fr auto;gap:8px;align-items:center;margin:8px 0">
    <span style="font-size:11px">${esc(row.label)}</span>
    <span style="height:10px;background:#f2f4f7;border-radius:999px;overflow:hidden"><i style="display:block;height:100%;width:${Math.max(0,Math.min(100,Number(row.value)||0))}%;background:linear-gradient(90deg,#26345b,#ce9e5d)"></i></span>
    <strong style="font-size:11px">${esc(row.value)}${suffix}</strong>
  </div>`).join(""):'<div class="chart-empty">No chart data available.</div>';
}
function radarChart(name,rows){
const el=chartNode(name);if(!el)return;
const data=(rows||[]).filter(x=>x.label);
ensureChartCompanion(name,data.map(d=>({label:d.label,value:`${c5Fin(d.value)}%`})));
c5RadarView(el,data);
}
function heatmapChart(name,rows){
const el=chartNode(name);if(!el)return;
const data=(rows||[]).slice(0,18).map(row=>{const values=row.values||[];const done=values.filter(Boolean).length,total=values.length;return{label:String(row.label).slice(0,28),value:done,total:total,display:`${done}/${total}`};});
if(!data.length){el.innerHTML='<div class="empty">No records found in the selected scope.</div>';return}
ensureChartCompanion(name,data.map(d=>({label:d.label,value:d.display})));
c5MatrixView(el,data);
}
function networkChart(name,programs){
const el=$(`[data-chart="${name}"]`);if(!el)return;
const source=(programs||[]).filter(p=>Array.isArray(p.courses)&&p.courses.length).slice(0,12);
if(!window.d3){
renderFallbackBars(name,source.map(p=>({label:p.program_name||p.name,value:(p.courses||[]).length})),"");
return;
}
d3.select(el).selectAll("*").remove();
el.classList.add("network-chart-host");
const tooltip=document.createElement("div");
tooltip.className="network-tooltip hidden";
el.appendChild(tooltip);
const nodes=[],links=[],neighborMap=new Map();
const index=new Map();
const addNeighbor=(a,b)=>{if(!neighborMap.has(a))neighborMap.set(a,new Set());neighborMap.get(a).add(b);};
source.forEach(program=>{
const courseNode={id:`P:${program.name}`,name:program.name,label:program.program_name||program.name,type:"course"};
nodes.push(courseNode);index.set(courseNode.id,courseNode);
(program.courses||[]).slice(0,14).forEach(item=>{
const moduleId=`M:${item.course}`;
if(!index.has(moduleId)){
const moduleNode={id:moduleId,name:item.course,label:item.course_name||item.course,type:"module"};
nodes.push(moduleNode);index.set(moduleId,moduleNode);
}
links.push({source:courseNode.id,target:moduleId});
addNeighbor(courseNode.id,moduleId);addNeighbor(moduleId,courseNode.id);
});
});
if(!nodes.length){el.innerHTML='<div class="chart-empty">No Course → Module mapping data available.</div>';return}
const w=Math.max(el.clientWidth||620,480),h=420;
const svg=d3.select(el).append("svg").attr("width",w).attr("height",h);
const rootG=svg.append("g");
svg.call(d3.zoom().scaleExtent([0.7,2.5]).on("zoom",event=>rootG.attr("transform",event.transform)));
const link=rootG.append("g").attr("stroke","#cbd5e1").attr("stroke-width",1.2).selectAll("line")
.data(links).enter().append("line");
const node=rootG.append("g").selectAll("circle").data(nodes).enter().append("circle")
.attr("class",d=>`network-node ${d.type}`)
.attr("r",d=>d.type==="course"?8:4.5)
.attr("fill",d=>d.type==="course"?"#26345b":"#d9bf98")
.on("mouseenter",(event,d)=>{
tooltip.innerHTML=`<strong>${esc(d.label)}</strong><div>${d.type==="course"?"Course (ERPNext Program)":"Module (ERPNext Course)"}</div>`;
tooltip.classList.remove("hidden");
tooltip.style.left=`${event.offsetX+14}px`;
tooltip.style.top=`${event.offsetY+10}px`;
})
.on("mousemove",(event)=>{
tooltip.style.left=`${event.offsetX+14}px`;
tooltip.style.top=`${event.offsetY+10}px`;
})
.on("mouseleave",()=>tooltip.classList.add("hidden"));
const labels=rootG.append("g").selectAll("text").data(nodes).enter().append("text")
.attr("class",d=>`network-label network-label-${d.type}`)
.attr("font-size",d=>d.type==="course"?11:10)
.attr("font-weight",d=>d.type==="course"?800:500)
.attr("fill","#344054")
.text(d=>String(d.label).length>24?`${String(d.label).slice(0,23)}…`:d.label);
const simulation=d3.forceSimulation(nodes)
.force("link",d3.forceLink(links).id(d=>d.id).distance(d=>String(d.source.id||d.source).startsWith("P:")?62:42))
.force("charge",d3.forceManyBody().strength(-100))
.force("collide",d3.forceCollide().radius(d=>d.type==="course"?30:15))
.force("center",d3.forceCenter(w/2,h/2));
const drag=d3.drag()
.on("start",(event,d)=>{if(!event.active)simulation.alphaTarget(.3).restart();d.fx=d.x;d.fy=d.y;})
.on("drag",(event,d)=>{d.fx=event.x;d.fy=event.y;})
.on("end",(event,d)=>{if(!event.active)simulation.alphaTarget(0);d.fx=null;d.fy=null;});
node.call(drag);
let focusId=null;
function connectedToFocus(d){
if(!focusId)return d.type==="course";
if(d.id===focusId)return true;
return !!neighborMap.get(focusId)?.has(d.id);
}
function updateFocus(){
link.attr("opacity",d=>{
if(!focusId)return .85;
const sid=d.source.id||d.source, tid=d.target.id||d.target;
return sid===focusId || tid===focusId ? 1 : .08;
})
.attr("stroke",d=>{
const sid=d.source.id||d.source, tid=d.target.id||d.target;
return focusId && (sid===focusId || tid===focusId) ? "#26345b" : "#cbd5e1";
})
.attr("stroke-width",d=>{
const sid=d.source.id||d.source, tid=d.target.id||d.target;
return focusId && (sid===focusId || tid===focusId) ? 1.8 : 1.1;
});
node.attr("opacity",d=>connectedToFocus(d)?1:.18)
.attr("r",d=>{
if(d.type==="course")return focusId===d.id?10:8;
return focusId && connectedToFocus(d)?5.6:4.5;
});
labels.attr("opacity",d=>{
if(d.type==="course")return !focusId || d.id===focusId ? 1 : .22;
return focusId && connectedToFocus(d) ? 1 : 0;
});
}
node.on("click",(event,d)=>{
if(d.type!=="course")return;
focusId = focusId===d.id ? null : d.id;
updateFocus();
});
simulation.on("tick",()=>{
nodes.forEach(d=>{d.x=Math.max(18,Math.min(w-18,d.x));d.y=Math.max(28,Math.min(h-18,d.y))});
link.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);
node.attr("cx",d=>d.x).attr("cy",d=>d.y);
labels.attr("x",d=>d.x+(d.type==="course"?12:7)).attr("y",d=>d.y-6);
});
const hint=document.createElement("div");
hint.className="network-hint";
hint.textContent="Tip: click a Course node to focus connected Modules. Click again to reset.";
el.appendChild(hint);
updateFocus();
}
function donutChart(name,rows,centerLabel){
ensureChartCompanion(name,rows);
const el=chartNode(name);if(!el)return;
const data=(rows||[]).filter(x=>Number(x.value)>0);
if(!data.length){el.innerHTML='<div class="empty">No records found in the selected scope.</div>';return}
c5DonutView(el,data);
}
function bubbleChart(name,rows){
ensureChartCompanion(name,rows);
const el=$(`[data-chart="${name}"]`);if(!el)return;
if(!window.d3){renderFallbackBars(name,(rows||[]).slice(0,12).map(x=>({label:x.label,value:x.coverage||0})));return}
d3.select(el).selectAll("*").remove();
const data=(rows||[]).filter(x=>x.label);
if(!data.length){el.innerHTML='<div class="chart-empty">No chart data available.</div>';return}
const w=Math.max(el.clientWidth||620,360),h=380;
const rootNode=d3.hierarchy({children:data}).sum(d=>Math.max(1,Number(d.value)||1));
const packed=d3.pack().size([w,h]).padding(4)(rootNode);
const svg=d3.select(el).append("svg").attr("width",w).attr("height",h);
const color=d3.scaleLinear().domain([0,100]).range(["#d9bf98","#26345b"]);
const node=svg.selectAll("g").data(packed.leaves()).enter().append("g")
.attr("transform",d=>`translate(${d.x},${d.y})`);
node.append("circle").attr("r",d=>d.r)
.attr("fill",d=>color(Number(d.data.coverage)||0))
.attr("fill-opacity",.86).attr("stroke","#fff").attr("stroke-width",1.5);
node.filter(d=>d.r>16).append("text")
.attr("text-anchor","middle").attr("font-size",d=>d.r>28?9:8).attr("fill","#111827")
.text(d=>String(d.data.label).slice(0,d.r>28?14:8));
node.append("title").text(d=>`${d.data.label}: ${d.data.coverage||0}% evidence coverage; ${d.data.value||0} populated evidence entries`);
const legend=svg.append("g").attr("transform","translate(12,18)");
const defs=svg.append("defs");
const gradient=defs.append("linearGradient").attr("id",`${name}-coverage-gradient`);
gradient.append("stop").attr("offset","0%").attr("stop-color","#d9bf98");
gradient.append("stop").attr("offset","100%").attr("stop-color","#26345b");
legend.append("rect").attr("width",100).attr("height",10).attr("rx",5).attr("fill",`url(#${name}-coverage-gradient)`);
legend.append("text").attr("x",0).attr("y",24).attr("font-size",9).text("Lower coverage");
legend.append("text").attr("x",100).attr("y",24).attr("text-anchor","end").attr("font-size",9).text("Higher coverage");
}
function funnelChart(name,rows){
ensureChartCompanion(name,rows);
const el=chartNode(name);if(!el)return;
const data=(rows||[]).filter(x=>Number(x.value)>=0);
if(!data.length){el.innerHTML='<div class="empty">No records found in the selected scope.</div>';return}
c5FunnelView(el,data);
}
function radialBars(name,rows){
ensureChartCompanion(name,rows);
const el=$(`[data-chart="${name}"]`);if(!el)return;
if(!window.d3){renderFallbackBars(name,rows);return}
d3.select(el).selectAll("*").remove();
const data=(rows||[]).filter(x=>x.label);
if(!data.length){el.innerHTML='<div class="chart-empty">No chart data available.</div>';return}
const w=Math.max(el.clientWidth||440,340),h=360,cx=w/2,cy=h/2,r0=55,r1=Math.min(w,h)/2-30;
const svg=d3.select(el).append("svg").attr("width",w).attr("height",h);
const g=svg.append("g").attr("transform",`translate(${cx},${cy})`);
const angle=d3.scaleBand().domain(data.map(d=>d.label)).range([0,Math.PI*2]).padding(.12);
const radius=d3.scaleLinear().domain([0,100]).range([r0,r1]);
const colors=["#26345b","#ce9e5d","#d9bf98","#52658f","#ce9e5d"];
g.selectAll("path").data(data).enter().append("path")
.attr("d",d3.arc()
.innerRadius(r0)
.outerRadius(d=>radius(Number(d.value)||0))
.startAngle(d=>angle(d.label))
.endAngle(d=>angle(d.label)+angle.bandwidth())
.padAngle(.02).padRadius(r0))
.attr("fill",(d,i)=>colors[i%colors.length])
.append("title").text(d=>`${d.label}: ${d.value}%`);
g.selectAll(".value-label").data(data).enter().append("text")
.attr("class","chart-label")
.attr("transform",d=>{
const a=angle(d.label)+angle.bandwidth()/2-Math.PI/2;
const rr=Math.max(r0+18,radius(Number(d.value)||0)-12);
return `translate(${Math.cos(a)*rr},${Math.sin(a)*rr})`;
})
.attr("text-anchor","middle").text(d=>`${d.value}%`);
g.selectAll(".name-label").data(data).enter().append("text")
.attr("transform",d=>{
const a=angle(d.label)+angle.bandwidth()/2-Math.PI/2;
return `translate(${Math.cos(a)*(r1+22)},${Math.sin(a)*(r1+22)})`;
})
.attr("text-anchor","middle").attr("font-size",10).text(d=>d.label);
}
function timelineChart(name,rows){
ensureChartCompanion(name,rows);
const el=$(`[data-chart="${name}"]`);if(!el)return;
if(!window.d3){
const grouped={};
(rows||[]).forEach(x=>{if(x.date instanceof Date&&!Number.isNaN(x.date)){const y=x.date.getFullYear();grouped[y]=(grouped[y]||0)+1}});
renderFallbackBars(name,Object.entries(grouped).map(([label,value])=>({label,value})),"");
return;
}
d3.select(el).selectAll("*").remove();
const data=(rows||[]).filter(d=>d.date instanceof Date&&!Number.isNaN(d.date));
if(!data.length){el.innerHTML='<div class="chart-empty">No dated review records available.</div>';return}
const w=Math.max(el.clientWidth||560,360),h=300,m={t:24,r:20,b:48,l:70};
const svg=d3.select(el).append("svg").attr("width",w).attr("height",h);
const statuses=[...new Set(data.map(d=>d.status||"Unknown"))];
const x=d3.scaleTime().domain(d3.extent(data,d=>d.date)).nice().range([m.l,w-m.r]);
const y=d3.scaleBand().domain(statuses).range([m.t,h-m.b]).padding(.35);
svg.append("g").attr("transform",`translate(0,${h-m.b})`).call(d3.axisBottom(x).ticks(5).tickFormat(d3.timeFormat("%d %b %Y")));
svg.append("g").attr("transform",`translate(${m.l},0)`).call(d3.axisLeft(y));
svg.selectAll("circle").data(data).enter().append("circle")
.attr("cx",d=>x(d.date)).attr("cy",d=>y(d.status)+y.bandwidth()/2)
.attr("r",6).attr("fill",d=>/approved/i.test(d.status)?"#26345b":"#ce9e5d")
.append("title").text(d=>`${d.label} · ${d.status} · ${formatDate(d.date)}`);
}
function labelledBar(name,rows,suffix="%"){
const el=$(`[data-chart="${name}"]`);if(!el)return;
if(!window.d3){renderFallbackBars(name,rows,suffix);return}
d3.select(el).selectAll("*").remove();
const data=(rows||[]).filter(x=>x.label);
if(!data.length){el.innerHTML='<div class="chart-empty">No chart data available.</div>';return}
const w=Math.max(el.clientWidth||540,360),h=300,m={t:20,r:30,b:70,l:45};
const max=Math.max(1,d3.max(data,d=>Number(d.value)||0));
const svg=d3.select(el).append("svg").attr("width",w).attr("height",h);
const x=d3.scaleBand().domain(data.map(d=>d.label)).range([m.l,w-m.r]).padding(.25);
const y=d3.scaleLinear().domain([0,max]).nice().range([h-m.b,m.t]);
svg.append("g").attr("transform",`translate(0,${h-m.b})`).call(d3.axisBottom(x))
.selectAll("text").attr("transform","rotate(-35)").style("text-anchor","end").style("font-size","10px");
svg.append("g").attr("transform",`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5));
svg.selectAll("rect").data(data).enter().append("rect")
.attr("x",d=>x(d.label)).attr("y",d=>y(Number(d.value)||0))
.attr("width",x.bandwidth()).attr("height",d=>y(0)-y(Number(d.value)||0))
.attr("rx",5).attr("fill","#26345b");
svg.selectAll(".bar-value").data(data).enter().append("text")
.attr("class","chart-label")
.attr("x",d=>x(d.label)+x.bandwidth()/2).attr("y",d=>Math.max(m.t+12,y(Number(d.value)||0)-6))
.attr("text-anchor","middle").text(d=>`${d.value}${suffix}`);
}
function renderVisibleC511Charts(){
const panel=$('[data-c511-panel]:not(.hidden)');
if(!panel)return;
const tab=panel.dataset.c511Panel,a=state.c511Server||buildC511();
const safe=(label,fn)=>{try{fn()}catch(error){console.error(`5.1.1 ${label} chart error`,error)}};
if(tab==="summary"){
safe("radar",()=>radarChart("c511-radar",a.readiness));
safe("matrix",()=>heatmapChart("c511-heatmap",a.checks.map(x=>({label:x.record.name,values:Object.keys(C511_GROUPS).map(g=>x.groups[g].ok?1:0)}))));
safe("network",()=>networkChart("c511-network",a.programs));
}else if(tab==="proposal"){
safe("proposal status",()=>donutChart("c511-proposal-donut",[
{label:"Approved",value:a.proposalApproved},
{label:"Pending / Other",value:a.proposals.length-a.proposalApproved}
],a.proposals.length));
const byYear=new Map();
a.proposals.forEach(x=>{
if(!x.proposed_date||!x.decision_date)return;
const days=(new Date(`${x.decision_date}T00:00:00`)-new Date(`${x.proposed_date}T00:00:00`))/86400000;
if(!Number.isFinite(days)||days<0)return;
const year=String(x.proposed_date).slice(0,4),values=byYear.get(year)||[];
values.push(days);byYear.set(year,values);
});
safe("decision time",()=>labelledBar("c511-decision-time",[...byYear].map(([label,values])=>({label,value:Math.round(values.reduce((a,b)=>a+b,0)/values.length)})),"d"));
safe("proposal evidence",()=>labelledBar("c511-proposal-bars",a.readiness));
}else if(tab==="module"){
safe("module constellation",()=>bubbleChart("c511-module-bubbles",a.moduleRows.map(x=>({label:x.record.course_name||x.record.name,value:x.lo+x.lessons+x.teaching+x.assessment+x.resources,coverage:x.coverage}))));
safe("module coverage",()=>radialBars("c511-module-radial",[
{label:"Outcomes",value:pct(a.moduleRows.filter(x=>x.lo>0).length,a.moduleRows.length)},
{label:"Lesson plans",value:pct(a.moduleRows.filter(x=>x.lessons>0).length,a.moduleRows.length)},
{label:"Teaching",value:pct(a.moduleRows.filter(x=>x.teaching>0).length,a.moduleRows.length)},
{label:"Assessment",value:pct(a.moduleRows.filter(x=>x.assessment>0).length,a.moduleRows.length)},
{label:"Resources",value:pct(a.moduleRows.filter(x=>x.resources>0).length,a.moduleRows.length)}
]));
safe("module design",()=>labelledBar("c511-module-stream",[
{label:"Complete",value:pct(a.moduleRows.filter(x=>x.complete).length,a.moduleRows.length)},
{label:"Partial",value:pct(a.moduleRows.filter(x=>!x.complete&&!x.zero).length,a.moduleRows.length)},
{label:"Zero evidence",value:pct(a.moduleRows.filter(x=>x.zero).length,a.moduleRows.length)}
]));
}else if(tab==="review"){
safe("review status",()=>donutChart("c511-review-donut",[
{label:"Approved",value:a.reviewApproved},
{label:"Pending / Other",value:a.reviews.length-a.reviewApproved}
],a.reviews.length));
safe("review timeline",()=>timelineChart("c511-review-timeline",a.reviews.map(x=>({label:x.name,status:x.review_status||"Unknown",date:x.review_date?new Date(`${x.review_date}T00:00:00`):null}))));
safe("review actions",()=>labelledBar("c511-review-actions",a.reviews.slice().sort((x,y)=>(y.actionplan_progress||[]).length-(x.actionplan_progress||[]).length).slice(0,15).map(x=>({label:x.name,value:(x.actionplan_progress||[]).length})),""));
}else if(tab==="gaps"){
renderGapView(state.c511GapFilter||"all");
}
}
function renderGapView(filter="all"){
state.c511GapFilter=filter;
$$("[data-gap-filter]").forEach(button=>button.classList.toggle("active",button.dataset.gapFilter===filter));
const rows=(state.c511Gaps||[]).filter(x=>filter==="all"||(filter==="proposal"&&x.doctype==="Course Proposal")||(filter==="module"&&x.doctype==="Course")||(filter==="review"&&x.doctype==="Course Review"));
const body=$('[data-table="c511-gaps"]');
if(body)body.innerHTML=rows.length?rows.map(x=>`<tr><td>${x.record&&x.record!=="—"?`<a class="open-record-link" href="${doctypeRoute(x.doctype,x.record)}" target="_blank" rel="noopener">${esc(x.record)}</a>`:esc(x.record)}</td><td>${esc(x.doctype==="Course"?"Module":x.doctype)}</td><td>${esc(x.area)}</td><td>${esc(x.issue)}</td><td>${badge(x.severity||(/zero|missing|no readable/i.test(x.issue)?"Risk":"Warning"))}</td></tr>`).join(""):'<tr><td colspan="5">No evidence gaps for this filter.</td></tr>';
const severitySummary=[
{label:"Risk",value:rows.filter(x=>(x.severity||"Risk")==="Risk").length},
{label:"Warning",value:rows.filter(x=>x.severity==="Warning").length}
].filter(x=>x.value>0);
const typeSummary=[
{label:"Module",value:rows.filter(x=>x.doctype==="Course").length},
{label:"Proposal",value:rows.filter(x=>x.doctype==="Course Proposal").length},
{label:"Review",value:rows.filter(x=>x.doctype==="Course Review").length}
].filter(x=>x.value>0);
funnelChart("c511-gap-funnel",severitySummary);
donutChart("c511-gap-sunburst",typeSummary,rows.length);
const severityBody=$('[data-table="c511-gap-severity"]');
if(severityBody)severityBody.innerHTML=severitySummary.length?severitySummary.map(x=>`<tr><td>${esc(x.label)}</td><td>${x.value}</td></tr>`).join(""):'<tr><td colspan="2">No gaps.</td></tr>';
const typeBody=$('[data-table="c511-gap-types"]');
if(typeBody)typeBody.innerHTML=typeSummary.length?typeSummary.map(x=>`<tr><td>${esc(x.label)}</td><td>${x.value}</td></tr>`).join(""):'<tr><td colspan="2">No gaps.</td></tr>';
}
function renderOverviewQA(){
const body=$('[data-table="overview-qa"]');if(!body)return;
const filter=$("[data-qa-filter]")?.value||"";
const parentFilter=/^5\.\d$/.test(filter);
const rows=(state.qa||[]).filter(row=>!filter||row.criterion===filter||(parentFilter&&row.criterion.startsWith(`${filter}.`)));
body.innerHTML=rows.length?rows.map((row,index)=>{
const count=Array.isArray(row.records)?row.records.length:0;
const actionDoctype=row.doctype||(row.doctypes||[])[0]||"";
const action=actionDoctype?`<button type="button" class="record-link ucc-qa-action" data-overview-qa="${index}">View ${count} matching record${count===1?"":"s"} ↗</button>`:"";
return`<tr>
    <td>${esc(row.criterion)}</td>
    <td>${esc(row.question)}</td>
    <td><div>${esc(row.answer)}</div>${action}</td>
    <td>${sourceCell(row.source,row.doctypes)}</td>
    <td>${badge(row.status)}</td>
  </tr>`;
}).join(""):'<tr><td colspan="5">No questions for the selected criterion.</td></tr>';
body.querySelectorAll("[data-overview-qa]").forEach(button=>button.addEventListener("click",()=>{
const row=rows[Number(button.dataset.overviewQa)];
const actionDoctype=row.doctype||(row.doctypes||[])[0]||"";
if(Array.isArray(row.records))openAffected(row.question,actionDoctype,row.records);
else if(actionDoctype)window.open(doctypeListRoute(actionDoctype),"_blank","noopener");
}));
}
function renderQATable(key,rows){
const body=$(`[data-table="${key}"]`);if(!body)return;
body.innerHTML=rows.length?rows.map((row,index)=>{
const count=Array.isArray(row.records)?row.records.length:0;
const actionDoctype=row.doctype||(row.doctypes||[])[0]||"";
const action=actionDoctype?`<button type="button" class="record-link ucc-qa-action" data-qa-index="${index}">View ${count} matching record${count===1?"":"s"} ↗</button>`:"";
return`<tr>
    <td>${esc(row.criterion)}</td>
    <td>${esc(row.question)}</td>
    <td><div>${esc(row.answer)}</div>${action}</td>
    <td>${sourceCell(row.source,row.doctypes)}</td>
    <td>${badge(row.status)}</td>
  </tr>`;
}).join(""):'<tr><td colspan="5">No questions available for this criterion.</td></tr>';
body.querySelectorAll("[data-qa-index]").forEach(button=>button.addEventListener("click",()=>{
const row=rows[Number(button.dataset.qaIndex)];
const actionDoctype=row.doctype||(row.doctypes||[])[0]||"";
if(Array.isArray(row.records))openAffected(row.question,actionDoctype,row.records);
else if(actionDoctype)window.open(doctypeListRoute(actionDoctype),"_blank","noopener");
}));
}
function sourceReady(dt){return state.sources?.[dt]?.status==="Available"}
function makeQA(c){
const srv=state.c5qaServer;
const rows=srv&&Array.isArray(srv.rows)?srv.rows:buildQARows(c);
state.qa=rows;
renderOverviewQA();
renderQATable("qa-c54",rows.filter(x=>x.criterion==="5.4"));
renderQATable("qa-c55",rows.filter(x=>x.criterion==="5.5"));
renderQATable("qa-c512",rows.filter(x=>x.criterion==="5.1.2"));
renderQATable("qa-c521",rows.filter(x=>x.criterion==="5.2.1"));
renderQATable("qa-c522",rows.filter(x=>x.criterion==="5.2.2"));
renderQATable("qa-c531",rows.filter(x=>x.criterion==="5.3.1"));
state.exceptions=srv&&Array.isArray(srv.exceptions)?srv.exceptions:[
...c.metrics.filter(x=>x.status!=="Good").map(x=>({criterion:x.criterion,issue:x.question,value:`${x.current}%`,target:`${x.target}%`,status:x.status})),
...state.quality.filter(x=>x.count).map(x=>({criterion:"Data Quality",issue:x.check,value:x.count,target:0,status:"Risk"})),
...rows.filter(x=>x.status==="Risk").map(x=>({criterion:x.criterion,issue:x.question,value:x.answer,target:"Follow-up required",status:"Risk"}))
];
}
function buildQARows(c){
const {s,metrics,topics,criteria}=c,f=currentFilters(),d=state.data;
const missingTopics=s.courses.filter(x=>!(x.topics?.length));
const missingCriteria=s.courses.filter(x=>!(x.assessment_criteria?.length));
const mappedCourseNames=new Set((d.Program||[]).flatMap(p=>(p.courses||[]).map(x=>x.course).filter(Boolean)));
const unmappedCourses=s.courses.filter(x=>!mappedCourseNames.has(x.name));
const coursesWithPlans=new Set(s.plans.map(x=>x.course).filter(Boolean));
const coursesWithoutPlans=s.courses.filter(x=>!coursesWithPlans.has(x.name));
const schedules=s.schedules||[];
const missingInstructor=schedules.filter(x=>!x.instructor);
const missingRoom=schedules.filter(x=>!x.room);
const schedNames=new Set(schedules.map(x=>x.name));
const attendedScheduleNames=new Set(s.attendance.map(x=>x.course_schedule).filter(x=>schedNames.has(x)));
const schedulesNoAttendance=schedules.filter(x=>!attendedScheduleNames.has(x.name));
const attendanceByStatus=group(s.attendance,"status");
const attendanceText=attendanceByStatus.length?attendanceByStatus.map(x=>`${x.label}: ${x.value}`).join(", "):"No attendance records in the selected scope.";
const absent=s.attendance.filter(x=>x.status==="Absent").length;
const late=s.attendance.filter(x=>x.status==="Late").length;
const plansMissingExaminer=s.plans.filter(x=>!x.examiner);
const plansMissingSupervisor=s.plans.filter(x=>!x.supervisor);
const plansMissingRoom=s.plans.filter(x=>!x.room);
const plansMissingDate=s.plans.filter(x=>!x.schedule_date);
const planNames=new Set(s.plans.map(x=>x.name));
const resultPlanNames=new Set(s.results.map(x=>x.assessment_plan).filter(x=>planNames.has(x)));
const plansWithoutResults=s.plans.filter(x=>!resultPlanNames.has(x.name));
const gradeDistribution=group(s.results,"grade");
const resultErrors=state.quality.filter(x=>/Result|score|grade|Duplicate/i.test(x.check)).reduce((sum,x)=>sum+x.count,0);
const mr=d["Module Review"]||[],cr=d["Course Review"]||[];
const overdueReviews=cr.filter(x=>x.next_review_date&&new Date(x.next_review_date)<new Date());
const pendingRecommendations=[...mr,...cr].filter(x=>x.recommendation_implementation_status==="Not Implemented");
const actionRows=cr.flatMap(parent=>(parent.actionplan_progress||[]).map(action=>({...action,parent_name:parent.name})));
const incompleteModuleReviews=mr.filter(x=>{
const fields=["rating_duration","rating_pedagogy","rating_assessment","rating_learning_outcomes","rating_lesson_plan","rating_resource","recommendation"];
return fields.some(field=>!x[field]);
});
const intakes=d["Student Intake No"]||[],classes=d["Module Class Details"]||[];
const admissions=d["Student Admission UCC"]||[];
const intakeGaps=intakes.filter(x=>!x.program||!x.course_start_date||!x.course_end_date);
const classesNoTeacher=classes.filter(x=>!x.custom_instructor);
const classesNoSchedule=classes.filter(x=>!(x.schedules||[]).length);
const incompleteContracts=admissions.filter(x=>!x.contract_start||!x.contract_end);
const admissionsNoIntake=admissions.filter(x=>!x.student_batch);
const observations=d["Classroom Observation"]||[],surveys=d["Survey Response"]||[];
const observedClassNames=new Set(observations.map(x=>x.module_class_details).filter(Boolean));
const classesNoObservation=classes.filter(x=>!observedClassNames.has(x.name));
const unsignedObservations=observations.filter(x=>!x.observers_signature||!x.teachers_signature);
const concernObservations=observations.filter(x=>String(x.areas_text||"").replace(/<[^>]*>/g,"").trim());
const observationTypes=group(observations,"type_of_observation");
const noticeTypes=group(observations,"prior_notice");
const agreements=d["Partnership Agreement"]||[],managed=d["Partnerships Agreement Management"]||[];
const supplierRatings=d["Supplier Rating"]||[];
const now=new Date(),in90=new Date(now.getTime()+90*86400000);
const expiredAgreements=agreements.filter(x=>x.end_date&&new Date(x.end_date)<now);
const expiringAgreements=agreements.filter(x=>x.end_date&&new Date(x.end_date)>=now&&new Date(x.end_date)<=in90);
const ndaIncomplete=agreements.filter(x=>x.requires_nda&&!x.nda_acknowledged);
const monitoring=managed.flatMap(parent=>(parent.monitoring_childtable||[]).map(row=>({...row,parent_name:parent.name})));
const evaluations=managed.flatMap(parent=>(parent.table_luoo||[]).map(row=>({...row,parent_name:parent.name})));
const belowThreshold=managed.filter(x=>Number(x.average_identification_and_selection_score)>0&&Number(x.average_identification_and_selection_score)<70);
const rows=[
{criterion:"5.1.1",question:"Which Modules are missing curriculum topics?",answer:missingTopics.length?`${missingTopics.length} Module(s): ${missingTopics.slice(0,8).map(x=>x.course_name||x.name).join(", ")}${missingTopics.length>8?"…":""}`:"No scoped Modules are missing curriculum topics.",source:"Course.topics child table on scoped Module records.",doctypes:["Course"],doctype:"Course",records:missingTopics,status:missingTopics.length?"Risk":"Good"},
{criterion:"5.1.1",question:"Which Modules are missing assessment criteria?",answer:missingCriteria.length?`${missingCriteria.length} Module(s) are missing assessment criteria.`:"No scoped Modules are missing assessment criteria.",source:"Course.assessment_criteria child table.",doctypes:["Course"],doctype:"Course",records:missingCriteria,status:missingCriteria.length?"Risk":"Good"},
{criterion:"5.1.1",question:"How complete is the Course-to-Module mapping?",answer:`${mappedCourseNames.size} unique Module(s) are mapped; ${unmappedCourses.length} scoped Module(s) are not found in a readable Course mapping.`,source:"Program.courses compared with scoped Course.name.",doctypes:["Program","Course"],doctype:"Course",records:unmappedCourses,status:unmappedCourses.length?"Warning":"Good"},
{criterion:"5.1.1",question:"Which Modules do not have an Assessment Plan?",answer:coursesWithoutPlans.length?`${coursesWithoutPlans.length} Module(s) have no Assessment Plan.`:"Every scoped Module has at least one Assessment Plan.",source:"Course.name compared with Assessment Plan.course.",doctypes:["Course","Assessment Plan"],doctype:"Course",records:coursesWithoutPlans,status:coursesWithoutPlans.length?"Risk":"Good"},
{criterion:"5.1.1",question:"What is the overall Module-design readiness?",answer:`${pct(topics+criteria,s.courses.length*2)}% across curriculum topics and assessment criteria for ${s.courses.length} scoped Module(s).`,source:"(Modules with topics + Modules with criteria) ÷ (Module count × 2).",doctypes:["Course"],doctype:"Course",records:[...new Map([...missingTopics,...missingCriteria].map(x=>[x.name,x])).values()],status:pct(topics+criteria,s.courses.length*2)>=100?"Good":pct(topics+criteria,s.courses.length*2)>=90?"Warning":"Risk"},
{criterion:"5.1.2",question:"What is the Module Review approval status?",answer:sourceReady("Module Review")?(group(mr,"status").map(x=>`${x.label}: ${x.value}`).join(", ")||"No Module Review records."):"Open 5.1.2 to load Module Review data.",source:"Module Review.status.",doctypes:["Module Review"],doctype:"Module Review",records:mr,status:!sourceReady("Module Review")?"Warning":mr.some(x=>x.status!=="Approved")?"Warning":"Good"},
{criterion:"5.1.2",question:"Which Course Reviews are overdue?",answer:sourceReady("Course Review")?`${overdueReviews.length} Course Review(s) have a next review date before today.`:"Open 5.1.2 to load Course Review data.",source:"Course Review.next_review_date compared with today.",doctypes:["Course Review"],doctype:"Course Review",records:overdueReviews,status:overdueReviews.length?"Risk":"Good"},
{criterion:"5.1.2",question:"Are scheduled and ad-hoc reviews identifiable?",answer:sourceReady("Module Review")||sourceReady("Course Review")?group([...mr.map(x=>({kind:x.type_of_review||"Not Set"})),...cr.map(x=>({kind:x.review_type||"Not Set"}))],"kind").map(x=>`${x.label}: ${x.value}`).join(", "):"Open 5.1.2 to load review data.",source:"Module Review.type_of_review and Course Review.review_type.",doctypes:["Module Review","Course Review"],status:(mr.length||cr.length)?"Good":"Warning"},
{criterion:"5.1.2",question:"Which previous recommendations remain unimplemented?",answer:sourceReady("Module Review")||sourceReady("Course Review")?`${pendingRecommendations.length} review record(s) are marked Not Implemented.`:"Open 5.1.2 to load review data.",source:"recommendation_implementation_status.",doctypes:["Module Review","Course Review"],doctype:"Module Review",records:pendingRecommendations.map(x=>({...x,_doctype:mr.includes(x)?"Module Review":"Course Review"})),status:pendingRecommendations.length?"Risk":"Good"},
{criterion:"5.1.2",question:"What is the Course Review action-plan status?",answer:sourceReady("Course Review")?(group(actionRows,"status").map(x=>`${x.label}: ${x.value}`).join(", ")||"No action-plan rows."):"Open 5.1.2 to load Course Review data.",source:"Course Review.actionplan_progress.status.",doctypes:["Course Review"],status:actionRows.some(x=>!["Completed","In Effect"].includes(x.status))?"Warning":"Good"},
{criterion:"5.1.2",question:"Which Module Reviews have incomplete core evidence?",answer:sourceReady("Module Review")?`${incompleteModuleReviews.length} Module Review(s) have one or more core evidence fields empty.`:"Open 5.1.2 to load Module Review data.",source:"Core rating and recommendation fields in Module Review.",doctypes:["Module Review"],doctype:"Module Review",records:incompleteModuleReviews,status:incompleteModuleReviews.length?"Warning":"Good"},
{criterion:"5.2.1",question:"How many scheduled Module sessions are in the selected period?",answer:`${schedules.length} Module Schedule record(s) for ${f.month}.`,source:"Course Schedule.schedule_date filtered by selected period and scope.",doctypes:["Course Schedule"],doctype:"Course Schedule",records:schedules,status:schedules.length?"Good":"Warning"},
{criterion:"5.2.1",question:"Which scheduled sessions have no Teacher?",answer:missingInstructor.length?`${missingInstructor.length} session(s) lack a Teacher.`:"All selected sessions have a Teacher.",source:"Course Schedule.instructor.",doctypes:["Course Schedule"],doctype:"Course Schedule",records:missingInstructor,status:missingInstructor.length?"Risk":"Good"},
{criterion:"5.2.1",question:"Which scheduled sessions have no room or venue?",answer:missingRoom.length?`${missingRoom.length} session(s) lack a room.`:"All selected sessions have a room.",source:"Course Schedule.room.",doctypes:["Course Schedule"],doctype:"Course Schedule",records:missingRoom,status:missingRoom.length?"Warning":"Good"},
{criterion:"5.2.1",question:"Which Intakes are missing core planning dates or Course?",answer:sourceReady("Student Intake No")?`${intakeGaps.length} Intake(s) have missing Course/start/end information.`:"Open 5.2.1 to load Intake data.",source:"Student Intake No.program, course_start_date and course_end_date.",doctypes:["Student Intake No"],doctype:"Student Intake No",records:intakeGaps,status:intakeGaps.length?"Risk":"Good"},
{criterion:"5.2.1",question:"Which Module Classes have no assigned Teacher or schedule?",answer:sourceReady("Module Class Details")?`${classesNoTeacher.length} lack a Teacher; ${classesNoSchedule.length} have no schedule rows.`:"Open 5.2.1 to load Module Class Details.",source:"Module Class Details.custom_instructor and schedules.",doctypes:["Module Class Details"],doctype:"Module Class Details",records:[...new Map([...classesNoTeacher,...classesNoSchedule].map(x=>[x.name,x])).values()],status:(classesNoTeacher.length||classesNoSchedule.length)?"Risk":"Good"},
{criterion:"5.2.1",question:"Which Shortlisted Applicants have incomplete Intake or contract dates?",answer:sourceReady("Student Admission UCC")?`${admissionsNoIntake.length} lack Intake No; ${incompleteContracts.length} have incomplete contract dates.`:"Open 5.2.1 to load Shortlisted Applicants.",source:"Student Admission UCC.student_batch, contract_start and contract_end.",doctypes:["Student Admission UCC"],doctype:"Student Admission UCC",records:[...new Map([...admissionsNoIntake,...incompleteContracts].map(x=>[x.name,x])).values()],status:(admissionsNoIntake.length||incompleteContracts.length)?"Warning":"Good"},
{criterion:"5.2.2",question:"What percentage of scheduled lessons have attendance captured?",answer:`${pct(attendedScheduleNames.size,schedNames.size)}% (${attendedScheduleNames.size} of ${schedNames.size} distinct schedules).`,source:"Distinct Student Attendance.course_schedule ÷ Course Schedule.name.",doctypes:["Student Attendance","Course Schedule"],doctype:"Course Schedule",records:schedulesNoAttendance,status:pct(attendedScheduleNames.size,schedNames.size)>=100?"Good":pct(attendedScheduleNames.size,schedNames.size)>=90?"Warning":"Risk"},
{criterion:"5.2.2",question:"What is the attendance status distribution?",answer:attendanceText,source:"Student Attendance.status.",doctypes:["Student Attendance"],status:s.attendance.length?"Good":"Warning"},
{criterion:"5.2.2",question:"Which Module Classes have no Classroom Observation?",answer:sourceReady("Classroom Observation")?`${classesNoObservation.length} Module Class(es) have no linked observation.`:"Open 5.2.2 to load observation data.",source:"Module Class Details.name compared with Classroom Observation.module_class_details.",doctypes:["Module Class Details","Classroom Observation"],doctype:"Module Class Details",records:classesNoObservation,status:classesNoObservation.length?"Warning":"Good"},
{criterion:"5.2.2",question:"What observation types were conducted?",answer:sourceReady("Classroom Observation")?(observationTypes.map(x=>`${x.label}: ${x.value}`).join(", ")||"No observations."):"Open 5.2.2 to load observation data.",source:"Classroom Observation.type_of_observation.",doctypes:["Classroom Observation"],doctype:"Classroom Observation",records:observations,status:observations.length?"Good":"Warning"},
{criterion:"5.2.2",question:"Which observations are missing Observer or Teacher sign-off?",answer:sourceReady("Classroom Observation")?`${unsignedObservations.length} observation(s) have incomplete signatures.`:"Open 5.2.2 to load observation data.",source:"Classroom Observation.observers_signature and teachers_signature.",doctypes:["Classroom Observation"],doctype:"Classroom Observation",records:unsignedObservations,status:unsignedObservations.length?"Warning":"Good"},
{criterion:"5.2.2",question:"Which observations record areas for improvement?",answer:sourceReady("Classroom Observation")?`${concernObservations.length} observation(s) contain areas for improvement.`:"Open 5.2.2 to load observation data.",source:"Classroom Observation.areas_text.",doctypes:["Classroom Observation"],doctype:"Classroom Observation",records:concernObservations,status:concernObservations.length?"Warning":"Good"},
{criterion:"5.2.2",question:"Were observations conducted with or without prior notice?",answer:sourceReady("Classroom Observation")?(noticeTypes.map(x=>`${x.label}: ${x.value}`).join(", ")||"No observations."):"Open 5.2.2 to load observation data.",source:"Classroom Observation.prior_notice.",doctypes:["Classroom Observation"],status:observations.length?"Good":"Warning"},
{criterion:"5.3.1",question:"How many signed partnership agreements are active, upcoming or expired?",answer:sourceReady("Partnership Agreement")?`${agreements.length} agreement(s); expired: ${expiredAgreements.length}; expiring within 90 days: ${expiringAgreements.length}.`:"Open 5.3.1 to load Partnership Agreement data.",source:"Partnership Agreement.start_date and end_date.",doctypes:["Partnership Agreement"],doctype:"Partnership Agreement",records:agreements,status:expiredAgreements.length?"Warning":"Good"},
{criterion:"5.3.1",question:"Which agreements require an NDA that is not acknowledged?",answer:sourceReady("Partnership Agreement")?`${ndaIncomplete.length} agreement(s) require NDA follow-up.`:"Open 5.3.1 to load Partnership Agreement data.",source:"Partnership Agreement.requires_nda and nda_acknowledged.",doctypes:["Partnership Agreement","Non Disclosure Agreement"],doctype:"Partnership Agreement",records:ndaIncomplete,status:ndaIncomplete.length?"Risk":"Good"},
{criterion:"5.3.1",question:"How many partnership monitoring activities are recorded?",answer:sourceReady("Partnerships Agreement Management")?`${monitoring.length} monitoring row(s) across ${managed.length} managed partnership record(s).`:"Open 5.3.1 to load management data.",source:"Partnerships Agreement Management.monitoring_childtable.",doctypes:["Partnerships Agreement Management"],doctype:"Partnerships Agreement Management",records:managed.filter(x=>(x.monitoring_childtable||[]).length),status:monitoring.length?"Good":"Warning"},
{criterion:"5.3.1",question:"What monitoring methods are being used?",answer:sourceReady("Partnerships Agreement Management")?(group(monitoring,"monitoring_details").map(x=>`${x.label}: ${x.value}`).join(", ")||"No monitoring entries."):"Open 5.3.1 to load management data.",source:"Partnerships Monitoring Childtable.monitoring_details.",doctypes:["Partnerships Agreement Management"],status:monitoring.length?"Good":"Warning"},
{criterion:"5.3.1",question:"What decisions resulted from partnership evaluations?",answer:sourceReady("Partnerships Agreement Management")?(group(evaluations,"evaluation_outcome").map(x=>`${x.label}: ${x.value}`).join(", ")||"No evaluation entries."):"Open 5.3.1 to load management data.",source:"Partnerships Evaluation Childtable.evaluation_outcome.",doctypes:["Partnerships Agreement Management"],status:evaluations.length?"Good":"Warning"},
{criterion:"5.3.1",question:"Which managed partnerships are below the 70/100 selection threshold?",answer:sourceReady("Partnerships Agreement Management")?`${belowThreshold.length} managed partnership(s) are below threshold.`:"Open 5.3.1 to load management data.",source:"average_identification_and_selection_score compared with 70/100.",doctypes:["Partnerships Agreement Management"],doctype:"Partnerships Agreement Management",records:belowThreshold,status:belowThreshold.length?"Risk":"Good"},
{criterion:"5.3.1",question:"What Provider Rating stages are recorded?",answer:sourceReady("Supplier Rating")?(group(supplierRatings,"evaluation_stage").map(x=>`${x.label}: ${x.value}`).join(", ")||"No Provider Rating records."):"Open 5.3.1 to load Provider Rating data.",source:"Supplier Rating.evaluation_stage. Display term: Provider Rating.",doctypes:["Supplier Rating"],doctype:"Supplier Rating",records:supplierRatings,status:supplierRatings.length?"Good":"Warning"},
{criterion:"5.4",question:"What is the average End of Module Survey score for each Module?",answer:(()=>{const a=buildSurveyAnalytics(),list=a.moduleScores.filter(x=>a.scored.some(item=>item.module===x.label&&item.survey_type==="End of Module"));return list.length?list.slice(0,8).map(x=>`${x.label}: ${x.value}`).join(", "):"No scored End of Module Survey responses were classified in the selected scope.";})(),source:"Survey Response.course plus scored child response rows.",doctypes:["Survey Response"],status:buildSurveyAnalytics().moduleScores.length?"Good":"Warning"},
{criterion:"5.4",question:"How many survey responses exist by survey type?",answer:(()=>{const a=buildSurveyAnalytics();return ["End of Module","End of Course","Graduate Survey"].map(t=>`${t}: ${a.scored.filter(x=>x.survey_type===t).length+a.comments.filter(x=>x.survey_type===t).length}`).join(", ");})(),source:"Survey type classified from title, category and question text.",doctypes:["Survey Response"],status:(d["Survey Response"]||[]).length?"Good":"Warning"},
{criterion:"5.4",question:"Which survey questions have the lowest scores?",answer:(()=>{const list=buildSurveyAnalytics().questionScores.slice().sort((a,b)=>a.value-b.value).slice(0,5);return list.length?list.map(x=>`${x.label}: ${x.value}`).join(", "):"No scored survey questions were available.";})(),source:"Average parsed score grouped by child question.",doctypes:["Survey Response"],status:buildSurveyAnalytics().questionScores.length?"Warning":"Warning"},
{criterion:"5.4",question:"What open-ended responses were submitted?",answer:`${buildSurveyAnalytics().comments.length} open-ended/non-numeric response(s) are available.`,source:"Survey Response child rows not parsed as numeric/Likert scores.",doctypes:["Survey Response"],status:buildSurveyAnalytics().comments.length?"Good":"Warning"},
{criterion:"5.4",question:"What attendance-risk indicators are visible alongside survey feedback?",answer:`${absent} Absent record(s) and ${late} Late record(s) in the selected schedule scope.`,source:"Student Attendance.status linked to selected Module Schedule records.",doctypes:["Student Attendance"],status:(absent||late)?"Warning":"Good"},
{criterion:"5.5",question:"Which Assessment Plans are missing examiner or supervisor?",answer:`${plansMissingExaminer.length} plan(s) lack examiner and ${plansMissingSupervisor.length} lack supervisor.`,source:"Assessment Plan.examiner and supervisor.",doctypes:["Assessment Plan"],doctype:"Assessment Plan",records:[...new Map([...plansMissingExaminer,...plansMissingSupervisor].map(x=>[x.name,x])).values()],status:(plansMissingExaminer.length||plansMissingSupervisor.length)?"Warning":"Good"},
{criterion:"5.5",question:"Which Assessment Plans have no linked results?",answer:plansWithoutResults.length?`${plansWithoutResults.length} plan(s) have no linked Assessment Result.`:"Every selected Assessment Plan has at least one linked result.",source:"Assessment Plan.name compared with Assessment Result.assessment_plan.",doctypes:["Assessment Plan","Assessment Result"],doctype:"Assessment Plan",records:plansWithoutResults,status:plansWithoutResults.length?"Risk":"Good"},
{criterion:"5.5",question:"What is the grade distribution?",answer:gradeDistribution.length?gradeDistribution.map(x=>`${x.label}: ${x.value}`).join(", "):"No graded Assessment Result records in the selected scope.",source:"Assessment Result.grade.",doctypes:["Assessment Result"],status:gradeDistribution.length?"Good":"Warning"},
{criterion:"5.5",question:"How complete are assessment control fields?",answer:`Missing room: ${plansMissingRoom.length}; missing schedule date: ${plansMissingDate.length}; missing examiner: ${plansMissingExaminer.length}; missing supervisor: ${plansMissingSupervisor.length}.`,source:"Assessment Plan control fields.",doctypes:["Assessment Plan"],status:(plansMissingRoom.length||plansMissingDate.length||plansMissingExaminer.length||plansMissingSupervisor.length)?"Warning":"Good"},
{criterion:"5.5",question:"Are there assessment-result data errors requiring correction?",answer:`${resultErrors} result-quality exception(s) across score-above-maximum, missing grade and duplicate-result checks.`,source:"Assessment Result data-quality rules.",doctypes:["Assessment Result"],status:resultErrors?"Risk":"Good"}
];
return rows;
}
function setKpi(slot,label,value,note){set(`[data-kpi-label="${slot}"]`,label);set(`[data-kpi="${slot}"]`,value);set(`[data-kpi-note="${slot}"]`,note)}
function avg(values){const v=values.filter(Number.isFinite);return v.length?Math.round(v.reduce((a,b)=>a+b,0)/v.length*100)/100:null}
function renderKpis(tab,c){
const {s,topics,criteria}=c,d=state.data,survey=buildSurveyAnalytics();
const sched=new Set(s.schedules.map(x=>x.name)),att=new Set(s.attendance.map(x=>x.course_schedule).filter(x=>sched.has(x)));
const plans=new Set(s.plans.map(x=>x.name)),resPlans=new Set(s.results.map(x=>x.assessment_plan).filter(x=>plans.has(x)));
const ready=pct(topics+criteria,s.courses.length*2),surveyAvg=avg(survey.scored.map(x=>x.score));
const cfg={
overview:[["Courses in scope",s.courses.length,"Programme/module class"],["Course readiness",`${ready}%`,"Topics + criteria"],["Loaded records",Object.values(d).reduce((a,r)=>a+(Array.isArray(r)?r.length:0),0),"Loaded tabs only"],["Available sources",Object.values(state.sources).filter(x=>x.status==="Available").length,"Readable now"],["Questions answered",state.qa.length||25,"Criterion 5"],["Open exceptions",state.exceptions.length,"Risk/data quality"]],
c51:[["Courses in scope",s.courses.length,"Selected scope"],["Readiness",`${ready}%`,"Topics + criteria"],["Missing topics",s.courses.length-topics,"Course.topics"],["Missing criteria",s.courses.length-criteria,"Course criteria"],["Without plans",s.courses.filter(x=>!new Set(s.plans.map(p=>p.course)).has(x.name)).length,"Assessment Plan"],["Programmes",(d.Program||[]).length,"Readable records"]],
c52:[["Scheduled lessons",s.schedules.length,"Selected month"],["Instructor complete",`${pct(s.schedules.filter(x=>x.instructor).length,s.schedules.length)}%`,"Schedule instructor"],["Room complete",`${pct(s.schedules.filter(x=>x.room).length,s.schedules.length)}%`,"Schedule room"],["Attendance capture",`${pct(att.size,sched.size)}%`,"Distinct schedules"],["Attendance rows",s.attendance.length,"Selected scope"],["Enrollment rows",s.enroll.length,"Programme/course proxy"]],
c53:[["Signed agreements",(d["Partnership Agreement"]||[]).length,"Partnership Agreement"],["Managed partnerships",(d["Partnerships Agreement Management"]||[]).length,"Partnerships Agreement Management"],["Partner ratings",(d["Supplier Rating"]||[]).length,"Supplier Rating"],["Expiring / expired",(d["Partnership Agreement"]||[]).filter(x=>x.end_date&&new Date(x.end_date)<=new Date()).length,"Agreement end date"],["Monitoring rows",(d["Partnerships Agreement Management"]||[]).flatMap(x=>x.monitoring_childtable||[]).length,"Monitoring child table"],["Evaluation rows",(d["Partnerships Agreement Management"]||[]).flatMap(x=>x.table_luoo||[]).length,"Evaluation child table"]],
c54:[["Survey documents",survey.docs.length,"Filtered Survey Response"],["Scored responses",survey.scored.length,"Numeric/Likert"],["Open comments",survey.comments.length,"Non-scored"],["Average score",surveyAvg===null?"—":surveyAvg,"Survey subfilters"],["Absent records",s.attendance.filter(x=>x.status==="Absent").length,"Attendance"],["Survey modules",new Set(survey.scored.map(x=>x.module)).size,"Filtered survey modules"]],
c55:[["Assessment plans",s.plans.length,"Selected scope"],["Result coverage",`${pct(resPlans.size,plans.size)}%`,"Plans with results"],["Missing examiner",s.plans.filter(x=>!x.examiner).length,"Assessment Plan"],["Missing supervisor",s.plans.filter(x=>!x.supervisor).length,"Assessment Plan"],["Result rows",s.results.length,"Assessment Result"],["Result errors",state.quality.filter(x=>/Result|score|grade|Duplicate/i.test(x.check)).reduce((a,x)=>a+x.count,0),"Quality rules"]],
quality:[["Quality checks",state.quality.length,"Rules"],["Failed checks",state.quality.filter(x=>x.count>0).length,"With exceptions"],["Total exceptions",state.quality.reduce((a,x)=>a+x.count,0),"All issues"],["Schedule issues",state.quality.filter(x=>/Schedule/i.test(x.check)).reduce((a,x)=>a+x.count,0),"Course Schedule"],["Attendance issues",state.quality.filter(x=>/Attendance/i.test(x.check)).reduce((a,x)=>a+x.count,0),"Attendance"],["Result issues",state.quality.filter(x=>/Result|score|grade|Duplicate/i.test(x.check)).reduce((a,x)=>a+x.count,0),"Results"]],
sources:[["Configured sources",Object.keys(CFG).length,"Confirmed sources"],["Available",Object.values(state.sources).filter(x=>x.status==="Available").length,"Readable"],["Permission denied",Object.values(state.sources).filter(x=>x.status==="Permission denied").length,"Restricted"],["Unavailable",Object.values(state.sources).filter(x=>x.status==="Unavailable").length,"Missing/failed"],["Survey source",state.sources["Survey Response"]?.status||"Not loaded","Criterion 5.4"],["Loaded records",Object.values(d).reduce((a,r)=>a+(Array.isArray(r)?r.length:0),0),"Cache"]]
};
(cfg[tab]||cfg.overview).forEach((r,i)=>setKpi(["one","two","three","four","five","six"][i],r[0],r[1],r[2]));
}
function renderSources(){
const label=dt=>displayDoctype(dt)===dt?esc(dt):`${esc(displayDoctype(dt))}<br><small>Technical: ${esc(dt)}</small>`;
const b=$('[data-table="sources"]');if(b)b.innerHTML=Object.entries(CFG).map(([dt,c])=>{const s=state.sources[dt]||{status:"Not loaded"};return`<tr><td>${label(dt)}</td><td>${badge(s.status==="Available"?"Good":s.status==="Not loaded"?"Warning":"Risk")}</td><td>${esc(c.purpose)}${s.error?`<br><small>${esc(s.error)}</small>`:""}</td></tr>`}).join("");
const box=$("[data-source-status]");if(box)box.innerHTML=Object.entries(CFG).map(([dt,c])=>{const s=state.sources[dt]||{status:"Not loaded"};return`<div class="source-row"><span>${label(dt)}</span><strong>${esc(s.status)}</strong></div>`}).join("");
}
function surveyType(row,child){
const text=`${row.title||""} ${child?.category||""} ${child?.question||""}`.toLowerCase();
if(/graduate|graduation|alumni/.test(text))return "Graduate Survey";
if(/end\s*of\s*course|course survey|programme survey|program survey/.test(text))return "End of Course";
if(/end\s*of\s*module|module survey|module feedback/.test(text))return "End of Module";
return "Other / Unclassified";
}
function parseSurveyScore(value){
const raw=String(value??"").trim();
if(!raw)return null;
const numeric=Number(raw.replace("%",""));
if(Number.isFinite(numeric)){
if(raw.includes("%"))return numeric/20;
return numeric;
}
const key=raw.toLowerCase();
const likert={
"strongly disagree":1,"disagree":2,"neutral":3,"neither agree nor disagree":3,
"agree":4,"strongly agree":5,
"very dissatisfied":1,"dissatisfied":2,"satisfied":4,"very satisfied":5,
"poor":1,"fair":2,"average":3,"good":4,"excellent":5,
"never":1,"rarely":2,"sometimes":3,"often":4,"always":5
};
return Object.prototype.hasOwnProperty.call(likert,key)?likert[key]:null;
}
function surveyFilters(){
return{type:$('[data-survey-filter="type"]')?.value||"",module:$('[data-survey-filter="module"]')?.value||""};
}
function populateSurveyModuleFilter(){
const select=$('[data-survey-filter="module"]');if(!select)return;
const current=select.value;
const modules=[...new Set((state.data["Survey Response"]||[]).map(x=>x.course).filter(Boolean))].sort();
select.innerHTML='<option value="">All Survey Modules</option>'+modules.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join("");
if(modules.includes(current))select.value=current;
}
function buildSurveyAnalytics(){
const docs=state.data["Survey Response"]||[],filter=surveyFilters(),scored=[],comments=[],typeCounts=new Map();
docs.forEach(doc=>{
if(filter.module&&doc.course!==filter.module)return;
(Array.isArray(doc.response)?doc.response:[]).forEach(child=>{
const type=surveyType(doc,child);if(filter.type&&type!==filter.type)return;
typeCounts.set(type,(typeCounts.get(type)||0)+1);
const score=parseSurveyScore(child.response);
const base={survey_type:type,module:doc.course||"Not Set",course:doc.program||"Not Set",category:child.category||"",question:child.question||"",response:child.response||"",posting_date:doc.posting_date||"",survey:doc.name};
if(score!==null)scored.push({...base,score});else if(String(child.response||"").trim())comments.push(base);
});
});
const avgBy=(rows,key)=>{const map=new Map();rows.forEach(r=>{const k=r[key]||"Not Set",v=map.get(k)||{sum:0,count:0};v.sum+=r.score;v.count++;map.set(k,v)});return[...map].map(([label,v])=>({label,value:Math.round((v.sum/v.count)*100)/100,count:v.count})).sort((a,b)=>b.value-a.value)};
return{docs:docs.filter(d=>!filter.module||d.course===filter.module),scored,comments,typeCounts:[...typeCounts].map(([label,value])=>({label,value})),moduleScores:avgBy(scored,"module"),questionScores:avgBy(scored,"question")};
}
function renderSurvey(){
const a=buildSurveyAnalytics();
bar("survey-module-score",a.moduleScores.slice(0,20));
bar("survey-type-count",a.typeCounts);
bar("survey-question-score",a.questionScores.slice(0,20));
const body=$('[data-table="survey-comments"]');
if(body)body.innerHTML=a.comments.slice(0,500).map(x=>`<tr><td>${esc(x.survey_type)}</td><td>${esc(x.module)}</td><td>${esc(x.category)}</td><td>${esc(x.question)}</td><td>${esc(x.response)}</td><td>${esc(x.posting_date)}</td></tr>`).join("");
return a;
}
function renderCharts(tab,c){
const {s,metrics}=c;
const d=state.data;
if(tab==="overview"){
bar("target-gaps",metrics.map(x=>({
label:x.question.replace("What proportion of ","").replace("?",""),
value:Math.max(0,x.target-x.current)
})));
return;
}
if(tab==="c54"){
renderSurvey();
empty("learning-support","No confirmed learning-intervention source is available in the current Criterion 5 data scope.");ensureCardDescription("learning-support");
bar("learning-risk",[
{label:"Absent",value:s.attendance.filter(x=>x.status==="Absent").length},
{label:"Late",value:s.attendance.filter(x=>x.status==="Late").length}
]);
}
if(tab==="c55"){
const mm=new Map();
s.plans.forEach(x=>{
const k=(x.schedule_date||"").slice(0,7)||"No Date";
mm.set(k,(mm.get(k)||0)+1);
});
line("assessment-trend",[...mm].map(([label,value])=>({label,value})).sort((a,b)=>a.label.localeCompare(b.label)));
bar("grade",group(s.results,"grade"));
bar("assessment-controls",[
{label:"Examiner %",value:pct(s.plans.filter(x=>x.examiner).length,s.plans.length)},
{label:"Supervisor %",value:pct(s.plans.filter(x=>x.supervisor).length,s.plans.length)},
{label:"Room %",value:pct(s.plans.filter(x=>x.room).length,s.plans.length)},
{label:"Maximum score %",value:pct(s.plans.filter(x=>x.maximum_assessment_score).length,s.plans.length)}
]);
bar("assessment-quality",state.quality.filter(x=>/Result|score|grade/i.test(x.check)).map(x=>({
label:x.check,
value:x.count
})));
}
}
function setNewKpi(key,value){set(`[data-new-kpi="${key}"]`,value)}
function tbody(key,rows,colspan=2){
const el=$(`[data-table="${key}"]`);if(!el)return;
el.innerHTML=rows.length?rows.join(""):`<tr><td colspan="${colspan}">No records found in the selected scope.</td></tr>`;
}
function recordLink(dt,name){return name?`<a class="open-record-link" href="${doctypeRoute(dt,name)}" target="_blank" rel="noopener">Open ↗</a>`:"—"}
function chartAndTable(key,rows){
const safeRows=Array.isArray(rows)?rows:[];
state.chartDrills=state.chartDrills||{};
state.chartDrills[key]=safeRows;
bar(key,safeRows);
tbody(key,safeRows.map((x,index)=>`<tr><td>${esc(x.label)}</td><td>${drillValue(key,index,x)}</td></tr>`),2);
bindChartDrills(root);
}
function ensureCardDescription(chartId){
const chart=chartNode(chartId);if(!chart)return;
const panel=chart.closest(".panel");if(!panel)return;
const h2=panel.querySelector("h2");if(!h2||h2.querySelector(".ucc-card-desc-inline"))return;
const description=C5_VISUAL_DESCRIPTIONS[chartId];if(!description)return;
const span=document.createElement("span");
span.className="ucc-card-desc-inline";
span.textContent=" — "+description;
h2.appendChild(span);
}
state.c5RequestedCharts=state.c5RequestedCharts||new Set();
state.c5PendingCharts=state.c5PendingCharts||new Map();
function deferredChartCall(realFn,name,args){
if(C5_DISABLED_VISUALS.has(name)){const n=chartNode(name),p=n&&n.closest(".panel");if(p)p.classList.add("ucc-visual-archived");return;}
if(state.c5RequestedCharts.has(name)){realFn(name,...args);return;}
state.c5PendingCharts.set(name,{realFn,args});
ensureChartCompanion(name,[]);
ensureCardDescription(name);
const chart=chartNode(name);
if(chart)chart.dataset.c5Deferred="1";
const panel=chart&&chart.closest(".panel");
const toggle=panel&&panel.querySelector("[data-card-toggle]");
if(toggle&&!toggle.dataset.deferBound){
toggle.dataset.deferBound="1";
toggle.querySelectorAll("[data-card-view]").forEach(btn=>btn.addEventListener("click",()=>{
if(state.c5RequestedCharts.has(name))return;
state.c5RequestedCharts.add(name);
if(chart)delete chart.dataset.c5Deferred;
const pending=state.c5PendingCharts.get(name);
if(pending)pending.realFn(name,...pending.args);
}));
}
}
const __c5Bar=bar;bar=function(n,rows){deferredChartCall(__c5Bar,n,[rows]);};
const __c5Line=line;line=function(n,rows){deferredChartCall(__c5Line,n,[rows]);};
const __c5RadarChart=radarChart;radarChart=function(n,rows){deferredChartCall(__c5RadarChart,n,[rows]);};
const __c5HeatmapChart=heatmapChart;heatmapChart=function(n,rows){deferredChartCall(__c5HeatmapChart,n,[rows]);};
const __c5NetworkChart=networkChart;networkChart=function(n,programs){deferredChartCall(__c5NetworkChart,n,[programs]);};
const __c5DonutChart=donutChart;donutChart=function(n,rows,centerLabel){deferredChartCall(__c5DonutChart,n,[rows,centerLabel]);};
const __c5BubbleChart=bubbleChart;bubbleChart=function(n,rows){deferredChartCall(__c5BubbleChart,n,[rows]);};
const __c5FunnelChart=funnelChart;funnelChart=function(n,rows){deferredChartCall(__c5FunnelChart,n,[rows]);};
const __c5RadialBars=radialBars;radialBars=function(n,rows){deferredChartCall(__c5RadialBars,n,[rows]);};
const __c5TimelineChart=timelineChart;timelineChart=function(n,rows){deferredChartCall(__c5TimelineChart,n,[rows]);};
const __c5LabelledBar=labelledBar;labelledBar=function(n,rows,suffix){deferredChartCall(__c5LabelledBar,n,[rows,suffix]);};
const __c5ChartAndTable=chartAndTable;chartAndTable=function(key,rows){deferredChartCall(__c5ChartAndTable,key,[rows]);};
function numericRating(v){
const n=Number(v);if(!Number.isFinite(n))return null;
return n<=1?n*5:n;
}
// Section 5.1.2 compute, extracted from the render branch unchanged so it can be
// ported to the server (c512_analytics) and wired with this as the fallback.
// Returns the exact datasets the render branch consumed inline; behaviour identical.
function buildC512(d,today){
const attachType=(rows,doctype)=>(rows||[]).map(row=>({...row,_doctype:doctype}));
const mr=d["Module Review"]||[],cr=d["Course Review"]||[];
const reviewRecords=[...attachType(mr,"Module Review"),...attachType(cr,"Course Review")];
const overdue=cr.filter(x=>x.next_review_date&&new Date(x.next_review_date)<today);
const upcoming=cr.filter(x=>x.next_review_date&&new Date(x.next_review_date)>=today);
const noNext=cr.filter(x=>!x.next_review_date);
const reviewTypeGroups=new Map;
reviewRecords.forEach(record=>{
const label=record._doctype==="Module Review"?(record.type_of_review||"Not Set"):(record.review_type||"Not Set");
if(!reviewTypeGroups.has(label))reviewTypeGroups.set(label,[]);
reviewTypeGroups.get(label).push(record);
});
const actionGroups=new Map;
cr.forEach(parent=>(parent.actionplan_progress||[]).forEach(action=>{
const label=action.status||"Not Set";
if(!actionGroups.has(label))actionGroups.set(label,new Map);
actionGroups.get(label).set(parent.name,parent);
}));
const recGroups=new Map;
reviewRecords.forEach(record=>{
const label=record.recommendation_implementation_status||"Not Set";
if(!recGroups.has(label))recGroups.set(label,[]);
recGroups.get(label).push(record);
});
const evidenceFields=["rating_duration","rating_pedagogy","rating_assessment","rating_learning_outcomes","rating_lesson_plan","rating_resource","risk_question","existing_attendance","existing_assessment_result","existing_classroom_observation","student_intervention_plan","admission_requirement_effectiveness","survey_results","rating_value_quality","recommendation"];
const complete=mr.filter(record=>evidenceFields.every(field=>record[field]!==undefined&&record[field]!==null&&record[field]!==""));
const incomplete=mr.filter(record=>!complete.includes(record));
const completedReviews=cr.filter(x=>String(x.review_status||"").toLowerCase().includes("complet"));
const dueReviews=cr.filter(x=>{
if(!x.next_review_date)return false;
const date=new Date(x.next_review_date);
return date>=today&&date<=new Date(today.getTime()+30*86400000);
});
const futureReviews=cr.filter(x=>x.next_review_date&&new Date(x.next_review_date)>new Date(today.getTime()+30*86400000));
const reviewedModules=new Set(mr.map(x=>x.course||x.module).filter(Boolean));
const reviewedCourses=new Set(cr.map(x=>x.course).filter(Boolean));
const coveredModuleReviews=mr.filter(x=>reviewedCourses.has(x.course));
const uncoveredModuleReviews=mr.filter(x=>!reviewedCourses.has(x.course));
const allActions=cr.flatMap(parent=>(parent.actionplan_progress||[]).map(action=>({...action,_parent:parent})));
const actionRecordSet=items=>[...new Map(items.map(x=>[x._parent.name,x._parent])).values()];
const completedActions=allActions.filter(x=>/complete|closed|done|implemented/i.test(String(x.status||"")));
const pendingActions=allActions.filter(x=>!completedActions.includes(x));
const actionDate=x=>x.due_date||x.target_date||x.completion_date||x.date||x.modified;
const aged=pendingActions.map(x=>({...x,_age:actionDate(x)?Math.max(0,Math.floor((today-new Date(actionDate(x)))/86400000)):null}));
const agingGroups=[
{label:"0–30 days",items:aged.filter(x=>x._age!==null&&x._age<=30)},
{label:"31–60 days",items:aged.filter(x=>x._age>30&&x._age<=60)},
{label:"61–90 days",items:aged.filter(x=>x._age>60&&x._age<=90)},
{label:"More than 90 days",items:aged.filter(x=>x._age>90)},
{label:"No action date",items:aged.filter(x=>x._age===null)}
];
const hasAnyField=(record,names)=>names.some(name=>Object.prototype.hasOwnProperty.call(record,name));
const hasValue=(record,names)=>names.some(name=>record[name]!==undefined&&record[name]!==null&&String(record[name]).replace(/<[^>]+>/g,"").trim()!=="");
const stakeholderFields=["stakeholder_feedback","feedback_from_stakeholders","stakeholder_comments","stakeholder_input"];
const benchmarkFields=["benchmarking_evidence","benchmarking","benchmark_data","industry_benchmark"];
const stakeholderSupported=cr.some(x=>hasAnyField(x,stakeholderFields));
const benchmarkSupported=cr.some(x=>hasAnyField(x,benchmarkFields));
const missingStakeholder=stakeholderSupported?cr.filter(x=>!hasValue(x,stakeholderFields)):[];
const missingBenchmark=benchmarkSupported?cr.filter(x=>!hasValue(x,benchmarkFields)):[];
const followupGroups=new Map;
reviewRecords.forEach(record=>{
const raw=record.review_date||record.date_of_review||record.modified;
const month=raw?String(raw).slice(0,7):"No date";
if(!followupGroups.has(month))followupGroups.set(month,[]);
followupGroups.get(month).push(record);
});
return{
mr,cr,
kpis:{mrTotal:mr.length,mrApproved:mr.filter(x=>x.status==="Approved").length,crTotal:cr.length,crOverdue:overdue.length},
reviewLevel:[
{label:"Module Review",value:mr.length,records:mr,doctype:"Module Review"},
{label:"Course Review",value:cr.length,records:cr,doctype:"Course Review"}
],
schedule:[
{label:"Overdue",value:overdue.length,records:overdue,doctype:"Course Review"},
{label:"Upcoming / current",value:upcoming.length,records:upcoming,doctype:"Course Review"},
{label:"No next review date",value:noNext.length,records:noNext,doctype:"Course Review"}
],
moduleStatus:groupRecords(mr,"status","Module Review"),
courseStatus:groupRecords(cr,"review_status","Course Review"),
reviewType:[...reviewTypeGroups].map(([label,records])=>({label,value:records.length,records})).sort((a,b)=>b.value-a.value),
actions:[...actionGroups].map(([label,map])=>({label,value:[...map.values()].reduce((sum,parent)=>sum+(parent.actionplan_progress||[]).filter(x=>(x.status||"Not Set")===label).length,0),records:[...map.values()],doctype:"Course Review"})).sort((a,b)=>b.value-a.value),
recommendationStatus:[...recGroups].map(([label,records])=>({label,value:records.length,records})).sort((a,b)=>b.value-a.value),
evidence:[
{label:"Core evidence complete",value:complete.length,records:complete,doctype:"Module Review"},
{label:"Core evidence incomplete",value:incomplete.length,records:incomplete,doctype:"Module Review"}
],
cycle:[
{label:"Completed",value:completedReviews.length,records:completedReviews,doctype:"Course Review"},
{label:"Due within 30 days",value:dueReviews.length,records:dueReviews,doctype:"Course Review"},
{label:"Upcoming",value:futureReviews.length,records:futureReviews,doctype:"Course Review"},
{label:"Overdue",value:overdue.length,records:overdue,doctype:"Course Review"},
{label:"No next review date",value:noNext.length,records:noNext,doctype:"Course Review"}
],
coverage:[
{label:"Module Reviews linked to a Course Review",value:coveredModuleReviews.length,records:coveredModuleReviews,doctype:"Module Review"},
{label:"Module Reviews without matching Course Review",value:uncoveredModuleReviews.length,records:uncoveredModuleReviews,doctype:"Module Review"},
{label:"Distinct reviewed modules",value:reviewedModules.size,records:mr,doctype:"Module Review"}
],
actionsCompletion:[
{label:"Completed actions",value:completedActions.length,records:actionRecordSet(completedActions),doctype:"Course Review"},
{label:"Pending actions",value:pendingActions.length,records:actionRecordSet(pendingActions),doctype:"Course Review"}
],
actionAging:agingGroups.map(x=>({label:x.label,value:x.items.length,records:actionRecordSet(x.items),doctype:"Course Review"})),
missingEvidence:[
{label:"Missing next review date",value:noNext.length,records:noNext,doctype:"Course Review"},
{label:stakeholderSupported?"Missing stakeholder feedback":"Stakeholder feedback field unsupported",value:stakeholderSupported?missingStakeholder.length:0,records:missingStakeholder,doctype:"Course Review"},
{label:benchmarkSupported?"Missing benchmarking evidence":"Benchmarking field unsupported",value:benchmarkSupported?missingBenchmark.length:0,records:missingBenchmark,doctype:"Course Review"}
],
followup:[...followupGroups].sort((a,b)=>a[0].localeCompare(b[0])).map(([label,records])=>({label,value:records.filter(x=>/complete|implemented|closed/i.test(String(x.recommendation_implementation_status||x.review_status||x.status||""))).length,records}))
};
}
// Section 5.2.1 compute, extracted from the render branch unchanged so it can be
// ported to the server (c521_analytics) and wired with this as the fallback.
function buildC521(d){
const intakes=d["Student Intake No"]||[],classes=d["Module Class Details"]||[],schedules=d["Course Schedule"]||[],apps=d["Student Admission UCC"]||[];
const ready=intakes.filter(x=>x.program&&x.course_start_date&&x.course_end_date),notReady=intakes.filter(x=>!ready.includes(x));
const assigned=classes.filter(x=>x.custom_instructor),unassigned=classes.filter(x=>!x.custom_instructor);
const sessionReady=schedules.filter(x=>x.instructor&&x.room&&x.from_time&&x.to_time);
const missingTeacher=schedules.filter(x=>!x.instructor),missingRoom=schedules.filter(x=>!x.room),missingTiming=schedules.filter(x=>!x.from_time||!x.to_time);
const completeContracts=apps.filter(x=>x.contract_start&&x.contract_end),incompleteContracts=apps.filter(x=>!x.contract_start||!x.contract_end);
const scheduleClassNames=new Set(schedules.map(x=>x.student_group||x.module_class_details).filter(Boolean));
const unscheduledClasses=classes.filter(x=>!scheduleClassNames.has(x.name));
const scheduledClasses=classes.filter(x=>scheduleClassNames.has(x.name));
const overlap=(a,b)=>{
if(String(a.schedule_date||"")!==String(b.schedule_date||""))return false;
const toMinutes=value=>{
if(value===null||value===undefined||value==="")return null;
const parts=String(value).split(":").map(Number);
return Number.isFinite(parts[0])?parts[0]*60+(parts[1]||0):null;
};
const af=toMinutes(a.from_time),at=toMinutes(a.to_time),bf=toMinutes(b.from_time),bt=toMinutes(b.to_time);
return af!==null&&at!==null&&bf!==null&&bt!==null&&af<bt&&bf<at;
};
const clashRecords=(field)=>{
const found=new Map;
schedules.forEach((a,index)=>schedules.slice(index+1).forEach(b=>{
if(a[field]&&a[field]===b[field]&&overlap(a,b)){found.set(a.name,a);found.set(b.name,b)}
}));
return [...found.values()];
};
const roomClashes=clashRecords("room"),teacherClashes=clashRecords("instructor");
const intakeByName=new Map(intakes.map(x=>[x.name,x]));
const contractBeforeStart=[],contractAfterStart=[],contractUnknown=[];
apps.forEach(app=>{
const intake=intakeByName.get(app.student_batch);
const commencement=app.actual_commencement_date||app.course_commencement_date||(intake&&intake.course_start_date);
if(!commencement||!app.contract_start){contractUnknown.push(app);return}
if(new Date(app.contract_start)<=new Date(commencement))contractBeforeStart.push(app);else contractAfterStart.push(app);
});
const signatureFields=["contract_signed","is_contract_signed","signed_contract","student_signature"];
const sentFields=["contract_sent","is_contract_sent","sent_to_student","contract_email_sent"];
const signatureSupported=apps.some(x=>signatureFields.some(f=>Object.prototype.hasOwnProperty.call(x,f)));
const sentSupported=apps.some(x=>sentFields.some(f=>Object.prototype.hasOwnProperty.call(x,f)));
const truthyField=(x,fields)=>fields.some(f=>x[f]===1||x[f]===true||String(x[f]).toLowerCase()==="yes");
const unsigned=signatureSupported?apps.filter(x=>!truthyField(x,signatureFields)):[];
const unsent=sentSupported?apps.filter(x=>!truthyField(x,sentFields)):[];
const exceptions=[];
intakes.forEach(x=>{if(!x.program||!x.course_start_date||!x.course_end_date)exceptions.push([x.name,"Student Intake No","Missing Course or start/end date"])});
classes.forEach(x=>{if(!x.custom_instructor)exceptions.push([x.name,"Module Class Details","Teacher not assigned"]);if(!(x.schedules||[]).length)exceptions.push([x.name,"Module Class Details","No schedule rows"])});
apps.forEach(x=>{if(!x.student_batch)exceptions.push([x.name,"Student Admission UCC","No Intake No"]);if(!x.contract_start||!x.contract_end)exceptions.push([x.name,"Student Admission UCC","Contract dates incomplete"])});
return{
intakes,classes,schedules,apps,
kpis:{intakes:intakes.length,classes:classes.length,sessions:schedules.length,applicants:apps.length},
intakesReady:[
{label:"Ready",value:ready.length,records:ready,doctype:"Student Intake No"},
{label:"Missing Course or dates",value:notReady.length,records:notReady,doctype:"Student Intake No"}
],
flow:[
{label:"Intakes",value:intakes.length,records:intakes,doctype:"Student Intake No"},
{label:"Module classes",value:classes.length,records:classes,doctype:"Module Class Details"},
{label:"Scheduled sessions",value:schedules.length,records:schedules,doctype:"Course Schedule"},
{label:"Shortlisted applicants",value:apps.length,records:apps,doctype:"Student Admission UCC"}
],
classStatus:groupRecords(classes,"custom_module_status","Module Class Details"),
schedule:[
{label:"All sessions",value:schedules.length,records:schedules,doctype:"Course Schedule"},
{label:"With Teacher",value:schedules.filter(x=>x.instructor).length,records:schedules.filter(x=>x.instructor),doctype:"Course Schedule"},
{label:"With room",value:schedules.filter(x=>x.room).length,records:schedules.filter(x=>x.room),doctype:"Course Schedule"},
{label:"With start and end time",value:schedules.filter(x=>x.from_time&&x.to_time).length,records:schedules.filter(x=>x.from_time&&x.to_time),doctype:"Course Schedule"}
],
admission:groupRecords(apps,"application_status","Student Admission UCC"),
teacher:[
{label:"Teacher assigned",value:assigned.length,records:assigned,doctype:"Module Class Details"},
{label:"Teacher missing",value:unassigned.length,records:unassigned,doctype:"Module Class Details"}
],
sessionReadiness:[
{label:"Ready",value:sessionReady.length,records:sessionReady,doctype:"Course Schedule"},
{label:"Missing Teacher",value:missingTeacher.length,records:missingTeacher,doctype:"Course Schedule"},
{label:"Missing room",value:missingRoom.length,records:missingRoom,doctype:"Course Schedule"},
{label:"Missing timing",value:missingTiming.length,records:missingTiming,doctype:"Course Schedule"}
],
contracts:[
{label:"Contract dates complete",value:completeContracts.length,records:completeContracts,doctype:"Student Admission UCC"},
{label:"Contract dates incomplete",value:incompleteContracts.length,records:incompleteContracts,doctype:"Student Admission UCC"}
],
dateCompleteness:[
{label:"Start and end dates complete",value:ready.length,records:ready,doctype:"Student Intake No"},
{label:"Missing start or end date",value:notReady.length,records:notReady,doctype:"Student Intake No"}
],
unscheduled:[
{label:"With schedules",value:scheduledClasses.length,records:scheduledClasses,doctype:"Module Class Details"},
{label:"Without schedules",value:unscheduledClasses.length,records:unscheduledClasses,doctype:"Module Class Details"}
],
scheduleCompleteness:[
{label:"Complete",value:sessionReady.length,records:sessionReady,doctype:"Course Schedule"},
{label:"Missing Teacher",value:missingTeacher.length,records:missingTeacher,doctype:"Course Schedule"},
{label:"Missing room",value:missingRoom.length,records:missingRoom,doctype:"Course Schedule"},
{label:"Missing time",value:missingTiming.length,records:missingTiming,doctype:"Course Schedule"}
],
roomClashes:[
{label:"Sessions with room clash",value:roomClashes.length,records:roomClashes,doctype:"Course Schedule"},
{label:"No detected room clash",value:Math.max(0,schedules.length-roomClashes.length),records:schedules.filter(x=>!roomClashes.includes(x)),doctype:"Course Schedule"}
],
teacherClashes:[
{label:"Sessions with Teacher clash",value:teacherClashes.length,records:teacherClashes,doctype:"Course Schedule"},
{label:"No detected Teacher clash",value:Math.max(0,schedules.length-teacherClashes.length),records:schedules.filter(x=>!teacherClashes.includes(x)),doctype:"Course Schedule"}
],
contractVsStart:[
{label:"Contract on/before commencement",value:contractBeforeStart.length,records:contractBeforeStart,doctype:"Student Admission UCC"},
{label:"Contract after commencement",value:contractAfterStart.length,records:contractAfterStart,doctype:"Student Admission UCC"},
{label:"Comparison unavailable",value:contractUnknown.length,records:contractUnknown,doctype:"Student Admission UCC"}
],
contractExceptions:[
{label:signatureSupported?"Unsigned contracts":"Signature field unsupported",value:unsigned.length,records:unsigned,doctype:"Student Admission UCC"},
{label:sentSupported?"Unsent contracts":"Sent-status field unsupported",value:unsent.length,records:unsent,doctype:"Student Admission UCC"},
{label:"Contract dates incomplete",value:incompleteContracts.length,records:incompleteContracts,doctype:"Student Admission UCC"}
],
exceptions
};
}
// Section 5.2.2 compute, extracted from the render branch so it can be ported to
// the server (c522_analytics) and wired with this as the fallback. Rating averages
// are returned RAW; the render branch applies toFixed so both the server and
// fallback paths format identically in the browser.
function buildC522(d,today){
const obs=d["Classroom Observation"]||[],classes=d["Module Class Details"]||[],surveys=d["Survey Response"]||[],schedules=d["Course Schedule"]||[];
const ratingFields={
"Preparation":["availability_of_learning_materials_likert","lesson_aligned_likert","lesson_plan_alignment_likert","lesson_objective_likert"],
"Delivery":["relevance_likert","mastery_likert","transition_likert","pacing_likert","educational_tools_likert","teaching_style_likert"],
"Class dynamics":["able_to_maintain_order_in_class_likert","good_rapport_with_students_likert","teacher_attentive_likert","timely_likert"],
"Communication":["simple_language_likert","teacher_confident_likert","good_balance_likert","vocal_likert","teacher_encourage_likert","non_verbal_likert"]
};
const flatRatingFields=Object.values(ratingFields).flat();
const allRatings=obs.flatMap(o=>flatRatingFields.map(f=>numericRating(o[f])).filter(v=>v!==null));
const observedClassNames=new Set(obs.map(x=>x.module_class_details).filter(Boolean));
const observedClasses=classes.filter(x=>observedClassNames.has(x.name)),unobservedClasses=classes.filter(x=>!observedClassNames.has(x.name));
const areaRows=Object.entries(ratingFields).map(([label,fields])=>{
const vals=obs.flatMap(o=>fields.map(f=>numericRating(o[f])).filter(v=>v!==null));
return{label,value:vals.length?vals.reduce((a,b)=>a+b,0)/vals.length:0,records:obs,doctype:"Classroom Observation"};
});
const categoryMap=new Map;
surveys.forEach(survey=>(survey.response||[]).forEach(response=>{
const label=response.category||"Uncategorised";
if(!categoryMap.has(label))categoryMap.set(label,new Map);
categoryMap.get(label).set(survey.name,survey);
}));
const bothSigned=obs.filter(x=>x.observers_signature&&x.teachers_signature),observerOnly=obs.filter(x=>x.observers_signature&&!x.teachers_signature),teacherOnly=obs.filter(x=>!x.observers_signature&&x.teachers_signature),unsigned=obs.filter(x=>!x.observers_signature&&!x.teachers_signature);
const concerns=obs.filter(x=>String(x.areas_text||"").replace(/<[^>]*>/g,"").trim()),noConcerns=obs.filter(x=>!concerns.includes(x));
const attendance=d["Student Attendance"]||[];
const deliveredScheduleNames=new Set(attendance.map(x=>x.course_schedule).filter(Boolean));
const deliveredSchedules=schedules.filter(x=>deliveredScheduleNames.has(x.name));
const undeliveredSchedules=schedules.filter(x=>!deliveredScheduleNames.has(x.name));
const teachers=[...new Set(classes.map(x=>x.custom_instructor_full_name||x.custom_instructor).filter(Boolean))];
const observedTeachers=new Set(obs.map(x=>x.name_of_teacher).filter(Boolean));
const scheduledObs=obs.filter(x=>/scheduled|formal/i.test(String(x.type_of_observation||""))||x.course_schedule);
const adhocObs=obs.filter(x=>!scheduledObs.includes(x));
const unsignedObs=obs.filter(x=>!(x.observers_signature&&x.teachers_signature));
const signoffAgeGroups=[
{label:"0–7 days",records:unsignedObs.filter(x=>{const dd=x.date_of_observation?Math.floor((today-new Date(x.date_of_observation))/86400000):null;return dd!==null&&dd<=7})},
{label:"8–30 days",records:unsignedObs.filter(x=>{const dd=x.date_of_observation?Math.floor((today-new Date(x.date_of_observation))/86400000):null;return dd>7&&dd<=30})},
{label:"31+ days",records:unsignedObs.filter(x=>{const dd=x.date_of_observation?Math.floor((today-new Date(x.date_of_observation))/86400000):null;return dd>30})},
{label:"No observation date",records:unsignedObs.filter(x=>!x.date_of_observation)}
];
const observationAverages=obs.map(record=>{
const vals=flatRatingFields.map(f=>numericRating(record[f])).filter(v=>v!==null);
return {...record,_average:vals.length?vals.reduce((a,b)=>a+b,0)/vals.length:null};
});
const ratingBands=[
{label:"4.0–5.0",records:observationAverages.filter(x=>x._average>=4)},
{label:"3.0–3.9",records:observationAverages.filter(x=>x._average>=3&&x._average<4)},
{label:"Below 3.0",records:observationAverages.filter(x=>x._average!==null&&x._average<3)},
{label:"Not rated",records:observationAverages.filter(x=>x._average===null)}
];
const belowThreshold=observationAverages.filter(x=>x._average!==null&&x._average<3);
const textPresent=(x,fields)=>fields.some(f=>String(x[f]||"").replace(/<[^>]+>/g,"").trim());
const strengthFields=["strengths","strengths_text","positive_observations","good_practices"];
const improvementFields=["areas_text","areas_for_improvement","improvement_areas","recommendations"];
const strengthRows=obs.filter(x=>textPresent(x,strengthFields));
const improvementRows=obs.filter(x=>textPresent(x,improvementFields));
const surveyMonths=new Map;
surveys.forEach(x=>{const month=String(x.posting_date||x.modified||"No date").slice(0,7);if(!surveyMonths.has(month))surveyMonths.set(month,[]);surveyMonths.get(month).push(x)});
return{
obs,classes,schedules,surveys,
kpis:{observations:obs.length,observationScoreAvg:allRatings.length?allRatings.reduce((a,b)=>a+b,0)/allRatings.length:null,surveys:surveys.length,unobserved:unobservedClasses.length},
coverage:[
{label:"Observed Module classes",value:observedClasses.length,records:observedClasses,doctype:"Module Class Details"},
{label:"Without observation",value:unobservedClasses.length,records:unobservedClasses,doctype:"Module Class Details"}
],
observationType:groupRecords(obs,"type_of_observation","Classroom Observation"),
platform:groupRecords(obs,"platform_delivery","Classroom Observation"),
ratings:areaRows,
surveyCategories:[...categoryMap].map(([label,map])=>({label,value:[...map.values()].reduce((sum,survey)=>sum+(survey.response||[]).filter(row=>(row.category||"Uncategorised")===label).length,0),records:[...map.values()],doctype:"Survey Response"})).sort((a,b)=>b.value-a.value),
notice:groupRecords(obs,"prior_notice","Classroom Observation"),
signoff:[
{label:"Both signed",value:bothSigned.length,records:bothSigned,doctype:"Classroom Observation"},
{label:"Observer only",value:observerOnly.length,records:observerOnly,doctype:"Classroom Observation"},
{label:"Teacher only",value:teacherOnly.length,records:teacherOnly,doctype:"Classroom Observation"},
{label:"Unsigned",value:unsigned.length,records:unsigned,doctype:"Classroom Observation"}
],
concerns:[
{label:"Areas for improvement recorded",value:concerns.length,records:concerns,doctype:"Classroom Observation"},
{label:"No areas recorded",value:noConcerns.length,records:noConcerns,doctype:"Classroom Observation"}
],
plannedDelivered:[
{label:"Planned sessions",value:schedules.length,records:schedules,doctype:"Course Schedule"},
{label:"Delivered / attendance captured",value:deliveredSchedules.length,records:deliveredSchedules,doctype:"Course Schedule"},
{label:"No delivery evidence",value:undeliveredSchedules.length,records:undeliveredSchedules,doctype:"Course Schedule"}
],
teacherCoverage:[
{label:"Teachers observed",value:teachers.filter(x=>observedTeachers.has(x)).length,records:obs.filter(x=>observedTeachers.has(x.name_of_teacher)),doctype:"Classroom Observation"},
{label:"Teachers not observed",value:teachers.filter(x=>!observedTeachers.has(x)).length,records:classes.filter(x=>!observedTeachers.has(x.custom_instructor_full_name||x.custom_instructor)),doctype:"Module Class Details"}
],
moduleCoverage:groupRecords(obs,"module_name","Classroom Observation"),
observationMode:[
{label:"Scheduled / formal",value:scheduledObs.length,records:scheduledObs,doctype:"Classroom Observation"},
{label:"Ad-hoc / other",value:adhocObs.length,records:adhocObs,doctype:"Classroom Observation"}
],
signoffAging:signoffAgeGroups.map(x=>({label:x.label,value:x.records.length,records:x.records,doctype:"Classroom Observation"})),
ratingDistribution:ratingBands.map(x=>({label:x.label,value:x.records.length,records:x.records,doctype:"Classroom Observation"})),
strengths:[
{label:"Strengths recorded",value:strengthRows.length,records:strengthRows,doctype:"Classroom Observation"},
{label:"No strengths recorded",value:obs.length-strengthRows.length,records:obs.filter(x=>!strengthRows.includes(x)),doctype:"Classroom Observation"}
],
improvements:[
{label:"Improvement areas recorded",value:improvementRows.length,records:improvementRows,doctype:"Classroom Observation"},
{label:"No improvement area recorded",value:obs.length-improvementRows.length,records:obs.filter(x=>!improvementRows.includes(x)),doctype:"Classroom Observation"}
],
surveyVolume:[...surveyMonths].sort((a,b)=>a[0].localeCompare(b[0])).map(([label,records])=>({label,value:records.reduce((sum,x)=>sum+Math.max(1,(x.response||[]).length),0),records,doctype:"Survey Response"})),
deliveryExceptions:[
{label:"Module classes without observation",value:unobservedClasses.length,records:unobservedClasses,doctype:"Module Class Details"},
{label:"Observations awaiting full sign-off",value:unsignedObs.length,records:unsignedObs,doctype:"Classroom Observation"},
{label:"Observations below rating threshold",value:belowThreshold.length,records:belowThreshold,doctype:"Classroom Observation"},
{label:"No delivery evidence",value:undeliveredSchedules.length,records:undeliveredSchedules,doctype:"Course Schedule"}
]
};
}
// Section 5.3.1 compute, extracted from the render branch so it can be ported to
// the server (c531_analytics) and wired with this as the fallback.
function buildC531(d,today,in90){
const signed=d["Partnership Agreement"]||[],managed=d["Partnerships Agreement Management"]||[],ratings=d["Supplier Rating"]||[];
const monitoring=managed.flatMap(parent=>(parent.monitoring_childtable||[]).map(row=>({...row,name:parent.name,_doctype:"Partnerships Agreement Management"})));
const evaluations=managed.flatMap(parent=>(parent.table_luoo||[]).map(row=>({...row,name:parent.name,_doctype:"Partnerships Agreement Management"})));
const signedStatus=signed.map(x=>{
const end=x.end_date?new Date(x.end_date):null,start=x.start_date?new Date(x.start_date):null;
return {...x,derived_status:end&&end<today?"Expired":start&&start>today?"Upcoming":"Active"};
});
const expired=signed.filter(x=>x.end_date&&new Date(x.end_date)<today),expiring=signed.filter(x=>x.end_date&&new Date(x.end_date)>=today&&new Date(x.end_date)<=in90),later=signed.filter(x=>x.end_date&&new Date(x.end_date)>in90),noEnd=signed.filter(x=>!x.end_date);
const ndaNotRequired=signed.filter(x=>!x.requires_nda),ndaComplete=signed.filter(x=>x.requires_nda&&x.nda_acknowledged),ndaIncomplete=signed.filter(x=>x.requires_nda&&!x.nda_acknowledged);
const scoreRows=managed.filter(x=>Number(x.average_identification_and_selection_score)>0).map(x=>({label:x.agreement_title||x.name,value:Number(x.average_identification_and_selection_score),records:[x],doctype:"Partnerships Agreement Management"})).sort((a,b)=>b.value-a.value);
const pass=managed.filter(x=>Number(x.average_identification_and_selection_score)>=70),below=managed.filter(x=>Number(x.average_identification_and_selection_score)>0&&Number(x.average_identification_and_selection_score)<70),notScored=managed.filter(x=>!Number(x.average_identification_and_selection_score));
const statusField=x=>String(x.status||x.agreement_status||x.workflow_state||"");
const lifecycle=signed.map(x=>{
const explicit=statusField(x);
const end=x.end_date?new Date(x.end_date):null,start=x.start_date?new Date(x.start_date):null;
const derived=/terminat/i.test(explicit)?"Terminated":end&&end<today?"Expired":end&&end<=in90?"Expiring":start&&start>today?"Upcoming":"Active";
return {...x,derived_status_v110:derived};
});
const partySignatureFields=["party_signature","partner_signature","signed_by_partner","partner_signed"];
const uccSignatureFields=["ucc_signature","company_signature","signed_by_ucc","ucc_signed"];
const hasField=(x,fields)=>fields.some(f=>Object.prototype.hasOwnProperty.call(x,f));
const hasValue=(x,fields)=>fields.some(f=>x[f]===1||x[f]===true||String(x[f]||"").trim()!=="");
const signatureSupported=signed.some(x=>hasField(x,[...partySignatureFields,...uccSignatureFields]));
const bothSigned=signatureSupported?signed.filter(x=>hasValue(x,partySignatureFields)&&hasValue(x,uccSignatureFields)):[];
const signatureIncomplete=signatureSupported?signed.filter(x=>!bothSigned.includes(x)):[];
const riskFields=["risk_level","partnership_risk","risk_rating","average_identification_and_selection_score"];
const riskSupported=managed.some(x=>hasField(x,riskFields));
const riskRows=riskSupported?managed.map(x=>{
let label=x.risk_level||x.partnership_risk||x.risk_rating;
if(!label&&Number(x.average_identification_and_selection_score))label=Number(x.average_identification_and_selection_score)>=70?"Low":"High";
return {...x,_risk:label||"Not Set"};
}):[];
const latestMonitoring=new Map;
monitoring.forEach(row=>{
const key=row.name,date=new Date(row.monitoring_date||row.date||row.modified||0);
if(!latestMonitoring.has(key)||date>latestMonitoring.get(key).date)latestMonitoring.set(key,{date,row});
});
const recentManaged=[],staleManaged=[],noMonitoring=[];
managed.forEach(parent=>{
const item=latestMonitoring.get(parent.name);
if(!item){noMonitoring.push(parent);return}
const age=Math.floor((today-item.date)/86400000);
if(age<=180)recentManaged.push(parent);else staleManaged.push(parent);
});
const decisionFields=["decision","continuation_decision","evaluation_decision","recommended_action"];
const decisionRows=evaluations.map(x=>({...x,_decision:decisionFields.map(f=>x[f]).find(Boolean)||x.evaluation_outcome||"Not Set"}));
const parentsWithMonitoring=new Set(monitoring.map(x=>x.name)),parentsWithEvaluation=new Set(evaluations.map(x=>x.name));
const withoutMonitoring=managed.filter(x=>!parentsWithMonitoring.has(x.name));
const withoutEvaluation=managed.filter(x=>!parentsWithEvaluation.has(x.name));
const qualityComplete=managed.filter(x=>parentsWithMonitoring.has(x.name)&&parentsWithEvaluation.has(x.name)&&Number(x.average_identification_and_selection_score)>0);
const qualityIncomplete=managed.filter(x=>!qualityComplete.includes(x));
return{
signed,managed,ratings,signedStatus,
kpis:{partners:signed.length,partnersActive:signedStatus.filter(x=>x.derived_status==="Active").length,monitoring:monitoring.length,evaluations:evaluations.length},
status:groupRecords(signedStatus,"derived_status","Partnership Agreement"),
type:groupRecords(signed,"pa_agreement_type","Partnership Agreement"),
expiry:[
{label:"Expired",value:expired.length,records:expired,doctype:"Partnership Agreement"},
{label:"Due within 90 days",value:expiring.length,records:expiring,doctype:"Partnership Agreement"},
{label:"More than 90 days",value:later.length,records:later,doctype:"Partnership Agreement"},
{label:"No end date",value:noEnd.length,records:noEnd,doctype:"Partnership Agreement"}
],
nda:[
{label:"Not required",value:ndaNotRequired.length,records:ndaNotRequired,doctype:"Partnership Agreement"},
{label:"Required and acknowledged",value:ndaComplete.length,records:ndaComplete,doctype:"Partnership Agreement"},
{label:"Required but incomplete",value:ndaIncomplete.length,records:ndaIncomplete,doctype:"Partnership Agreement"}
],
monitoring:groupRecords(monitoring,"monitoring_details"),
monitoringType:groupRecords(monitoring,"type_of_monitoring"),
evaluation:groupRecords(evaluations,"evaluation_outcome"),
scores:scoreRows,
ratingStage:groupRecords(ratings,"evaluation_stage","Supplier Rating"),
threshold:[
{label:"Meets threshold",value:pass.length,records:pass,doctype:"Partnerships Agreement Management"},
{label:"Below threshold",value:below.length,records:below,doctype:"Partnerships Agreement Management"},
{label:"Not scored",value:notScored.length,records:notScored,doctype:"Partnerships Agreement Management"}
],
lifecycle:groupRecords(lifecycle,"derived_status_v110","Partnership Agreement"),
signature:[
{label:signatureSupported?"Both parties signed":"Signature fields unsupported",value:bothSigned.length,records:bothSigned,doctype:"Partnership Agreement"},
{label:"Signature incomplete",value:signatureIncomplete.length,records:signatureIncomplete,doctype:"Partnership Agreement"}
],
risk:riskSupported?groupRecords(riskRows,"_risk","Partnerships Agreement Management"):[
{label:"Risk field unsupported",value:0,records:[],doctype:"Partnerships Agreement Management"}
],
monitoringRecency:[
{label:"Monitored within 180 days",value:recentManaged.length,records:recentManaged,doctype:"Partnerships Agreement Management"},
{label:"Monitoring older than 180 days",value:staleManaged.length,records:staleManaged,doctype:"Partnerships Agreement Management"},
{label:"No monitoring record",value:noMonitoring.length,records:noMonitoring,doctype:"Partnerships Agreement Management"}
],
decisions:groupRecords(decisionRows,"_decision","Partnerships Agreement Management"),
missingControls:[
{label:"Without recent monitoring",value:withoutMonitoring.length,records:withoutMonitoring,doctype:"Partnerships Agreement Management"},
{label:"Without evaluation",value:withoutEvaluation.length,records:withoutEvaluation,doctype:"Partnerships Agreement Management"}
],
qualityCompleteness:[
{label:"Core quality record complete",value:qualityComplete.length,records:qualityComplete,doctype:"Partnerships Agreement Management"},
{label:"Core quality record incomplete",value:qualityIncomplete.length,records:qualityIncomplete,doctype:"Partnerships Agreement Management"}
]
};
}
function renderNewSection(tab){
const d=state.data||{},today=new Date();today.setHours(0,0,0,0);
const in90=new Date(today.getTime()+90*86400000);
const attachType=(rows,doctype)=>(rows||[]).map(row=>({...row,_doctype:doctype}));
if(tab==="c512"){
const b=state.c512Server||buildC512(d,today);
setNewKpi("mr-total",b.kpis.mrTotal);setNewKpi("mr-approved",b.kpis.mrApproved);
setNewKpi("cr-total",b.kpis.crTotal);setNewKpi("cr-overdue",b.kpis.crOverdue);
chartAndTable("c512-review-level",b.reviewLevel);
chartAndTable("c512-schedule",b.schedule);
chartAndTable("c512-module-status",b.moduleStatus);
chartAndTable("c512-course-status",b.courseStatus);
chartAndTable("c512-review-type",b.reviewType);
chartAndTable("c512-actions",b.actions);
chartAndTable("c512-recommendation-status",b.recommendationStatus);
chartAndTable("c512-evidence",b.evidence);
chartAndTable("c512-cycle-v110",b.cycle);
chartAndTable("c512-coverage-v110",b.coverage);
chartAndTable("c512-actions-completion-v110",b.actionsCompletion);
chartAndTable("c512-action-aging-v110",b.actionAging);
chartAndTable("c512-missing-evidence-v110",b.missingEvidence);
chartAndTable("c512-followup-v110",b.followup);
const recordRows=[
...b.mr.map(x=>`<tr><td>${esc(x.name)}</td><td>Module Review</td><td>${esc(x.course||"—")}</td><td>${esc(x.module||"—")}</td><td>${esc(formatDate(x.date_of_review))}</td><td>${esc(x.status||"Not Set")}</td><td>${recordLink("Module Review",x.name)}</td></tr>`),
...b.cr.map(x=>`<tr><td>${esc(x.name)}</td><td>Course Review</td><td>${esc(x.course||"—")}</td><td>—</td><td>${esc(formatDate(x.review_date))}</td><td>${esc(x.review_status||"Not Set")}</td><td>${recordLink("Course Review",x.name)}</td></tr>`)
];
tbody("c512-records",recordRows,7);
}
if(tab==="c521"){
const b=state.c521Server||buildC521(d);
setNewKpi("intakes",b.kpis.intakes);setNewKpi("classes",b.kpis.classes);setNewKpi("sessions",b.kpis.sessions);setNewKpi("applicants",b.kpis.applicants);
chartAndTable("c521-intakes",b.intakesReady);
chartAndTable("c521-flow",b.flow);
chartAndTable("c521-class-status",b.classStatus);
chartAndTable("c521-schedule",b.schedule);
chartAndTable("c521-admission",b.admission);
chartAndTable("c521-teacher",b.teacher);
chartAndTable("c521-session-readiness",b.sessionReadiness);
chartAndTable("c521-contracts",b.contracts);
chartAndTable("c521-date-completeness-v110",b.dateCompleteness);
chartAndTable("c521-unscheduled-v110",b.unscheduled);
chartAndTable("c521-schedule-completeness-v110",b.scheduleCompleteness);
chartAndTable("c521-room-clashes-v110",b.roomClashes);
chartAndTable("c521-teacher-clashes-v110",b.teacherClashes);
chartAndTable("c521-contract-vs-start-v110",b.contractVsStart);
chartAndTable("c521-contract-exceptions-v110",b.contractExceptions);
tbody("c521-exceptions",b.exceptions.map(x=>`<tr><td>${esc(x[0])}</td><td>${esc(displayDoctype(x[1]))}</td><td>${esc(x[2])}</td><td>${recordLink(x[1],x[0])}</td></tr>`),4);
}
if(tab==="c522"){
const b=state.c522Server||buildC522(d,today);
setNewKpi("observations",b.kpis.observations);setNewKpi("observation-score",b.kpis.observationScoreAvg!==null?b.kpis.observationScoreAvg.toFixed(1)+"/5":"—");
setNewKpi("surveys",b.kpis.surveys);setNewKpi("unobserved",b.kpis.unobserved);
chartAndTable("c522-coverage",b.coverage);
chartAndTable("c522-observation-type",b.observationType);
chartAndTable("c522-platform",b.platform);
chartAndTable("c522-ratings",b.ratings.map(x=>({...x,value:Number(Number(x.value).toFixed(2))})));
chartAndTable("c522-survey-categories",b.surveyCategories);
chartAndTable("c522-notice",b.notice);
chartAndTable("c522-signoff",b.signoff);
chartAndTable("c522-concerns",b.concerns);
chartAndTable("c522-planned-delivered-v110",b.plannedDelivered);
chartAndTable("c522-teacher-coverage-v110",b.teacherCoverage);
chartAndTable("c522-module-coverage-v110",b.moduleCoverage);
chartAndTable("c522-observation-mode-v110",b.observationMode);
chartAndTable("c522-signoff-aging-v110",b.signoffAging);
chartAndTable("c522-rating-distribution-v110",b.ratingDistribution);
chartAndTable("c522-strengths-v110",b.strengths);
chartAndTable("c522-improvements-v110",b.improvements);
chartAndTable("c522-survey-volume-v110",b.surveyVolume);
chartAndTable("c522-delivery-exceptions-v110",b.deliveryExceptions);
const recordRows=[
...b.obs.map(x=>`<tr><td>${esc(x.name)}</td><td>Classroom Observation</td><td>${esc(x.course||"—")}</td><td>${esc(x.module_name||"—")}</td><td>${esc(formatDate(x.date_of_observation))}</td><td>${recordLink("Classroom Observation",x.name)}</td></tr>`),
...b.surveys.map(x=>`<tr><td>${esc(x.name)}</td><td>Survey Response</td><td>${esc(x.program||"—")}</td><td>${esc(x.course||"—")}</td><td>${esc(formatDate(x.posting_date))}</td><td>${recordLink("Survey Response",x.name)}</td></tr>`)
];
tbody("c522-records",recordRows,6);
}
if(tab==="c531"){
const b=state.c531Server||buildC531(d,today,in90);
setNewKpi("partners",b.kpis.partners);setNewKpi("partners-active",b.kpis.partnersActive);
setNewKpi("monitoring",b.kpis.monitoring);setNewKpi("evaluations",b.kpis.evaluations);
chartAndTable("c531-status",b.status);
chartAndTable("c531-type",b.type);
chartAndTable("c531-expiry",b.expiry);
chartAndTable("c531-nda",b.nda);
chartAndTable("c531-monitoring",b.monitoring);
chartAndTable("c531-monitoring-type",b.monitoringType);
chartAndTable("c531-evaluation",b.evaluation);
chartAndTable("c531-scores",b.scores);
chartAndTable("c531-rating-stage",b.ratingStage);
chartAndTable("c531-threshold",b.threshold);
chartAndTable("c531-lifecycle-v110",b.lifecycle);
chartAndTable("c531-signature-v110",b.signature);
chartAndTable("c531-risk-v110",b.risk);
chartAndTable("c531-monitoring-recency-v110",b.monitoringRecency);
chartAndTable("c531-decisions-v110",b.decisions);
chartAndTable("c531-missing-controls-v110",b.missingControls);
chartAndTable("c531-quality-completeness-v110",b.qualityCompleteness);
tbody("c531-records",b.signedStatus.map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(x.pa_partner_name||x.party_name||"—")}</td><td>${esc(x.pa_agreement_type||"—")}</td><td>${esc(x.derived_status)}</td><td>${esc(formatDate(x.start_date||x.posting_date))}</td><td>${esc(formatDate(x.end_date))}</td><td>${recordLink("Partnership Agreement",x.name)}</td></tr>`),7);
}
}
async function loadBase(){
if(state.loading)return;
state.loading=true;
setProgress(2,"Loading dashboard filters");
status("Loading base data…");
try{
const tasks=["Academic Year","Student Group","Course","Program"];
state.data=state.data||{};
for(let i=0;i<tasks.length;i++){
const dt=tasks[i];
setProgress(8+(i/tasks.length)*70,`Loading ${dt}`);
state.data[dt]=await load(dt);
}
const f=currentFilters();
const years=state.data["Academic Year"]||[],yearLabels={};
years.forEach(x=>yearLabels[x.name]=x.academic_year_name||x.name);
setOptions('[data-filter="academic_year"]',years.map(x=>x.name),"All Academic Years",yearLabels);
const groups=(state.data["Student Group"]||[]).filter(x=>!x.disabled&&(!f.year||x.academic_year===f.year)&&(!f.program||x.program===f.program));
const groupLabels={};groups.forEach(x=>groupLabels[x.name]=x.student_group_name||x.name);
setOptions('[data-filter="student_group"]',groups.map(x=>x.name),"All Module Classes",groupLabels);
const programs=state.data.Program||[],programLabels={};
programs.forEach(x=>programLabels[x.name]=x.program_name||x.name);
setOptions('[data-filter="program"]',programs.map(x=>x.name),"All Programmes",programLabels);
setProgress(90,"Preparing overview");
state.loadedSections=state.loadedSections||{};
state.loadedSections.base=true;
const baseCalc=compute();buildQuality(baseCalc);state.c5qaServer=await fetchC5QAModel();makeQA(baseCalc);renderKpis("overview",baseCalc);
renderSources();
updateAudit();
setProgress(100,"Complete");
status("Criterion 5 overview loaded for the current user and filters. Open a section to load its detailed evidence.");
}catch(e){
status(`Load error: ${errText(e)}`);
}finally{
state.loading=false;
hideProgress();
}
}
async function loadSection(tab, force=false){
state.loadedSections=state.loadedSections||{};
if(state.loadedSections[tab]&&!force){
const c=compute();buildQuality(c);state.c5qaServer=await fetchC5QAModel();makeQA(c);renderCharts(tab,c);if(tab==="c511")renderC511();renderNewSection(tab);renderKpis(tab==="c511"?"c51":tab,c);renderSources();updateAudit();
return;
}
if(state.loading)return;
state.loading=true;
const f=currentFilters();
setProgress(2,`Preparing ${tab}`);
status(`Loading ${tab} data…`);
try{
const tasks=[];
const add=(dt,filters=[])=>tasks.push({dt,filters});
if(tab==="overview"){
}
if(tab==="c511"||tab==="c55"){
if(tab==="c511"){setProgress(5,"Loading detailed course and programme design");if(!await hydrateViaServer(["Course","Program"])){await hydrateDocuments("Course");await hydrateDocuments("Program");}}
const ap=[];if(f.year)ap.push(["Assessment Plan","academic_year","=",f.year]);if(f.program)ap.push(["Assessment Plan","program","=",f.program]);if(f.student_group)ap.push(["Assessment Plan","student_group","=",f.student_group]);
const ar=[];if(f.year)ar.push(["Assessment Result","academic_year","=",f.year]);if(f.program)ar.push(["Assessment Result","program","=",f.program]);if(f.student_group)ar.push(["Assessment Result","student_group","=",f.student_group]);
add("Assessment Plan",ap);add("Assessment Result",ar);
}
if(tab==="c511"){
for(const dt of Object.keys(C511_SOURCES)){setProgress(22,`Loading ${dt}`);state.data[dt]=await loadC511Source(dt);}
setProgress(30,"Computing 5.1.1 analytics");state.c511Server=await fetchC511Model();
}
if(tab==="c54"){
const sf=[];
if(f.program)sf.push(["Survey Response","program","=",f.program]);
if(f.student_group){
const selectedGroup=(state.data["Student Group"]||[]).find(x=>x.name===f.student_group);
if(selectedGroup?.course)sf.push(["Survey Response","course","=",selectedGroup.course]);
}
if(f.start&&f.end){
sf.push(["Survey Response","posting_date",">=",f.start]);
sf.push(["Survey Response","posting_date","<=",f.end]);
}
add("Survey Response",sf);
const cs=[["Course Schedule","schedule_date",">=",f.start],["Course Schedule","schedule_date","<=",f.end]];
if(f.program)cs.push(["Course Schedule","program","=",f.program]);
if(f.student_group)cs.push(["Course Schedule","student_group","=",f.student_group]);
add("Course Schedule",cs);
}
if(tab==="c512"){
add("Module Review");add("Course Review");
}
if(tab==="c521"){
add("Student Intake No");add("Module Class Details");add("Student Admission UCC");
const cs=[];if(f.program)cs.push(["Course Schedule","program","=",f.program]);if(f.student_group)cs.push(["Course Schedule","student_group","=",f.student_group]);add("Course Schedule",cs);
}
if(tab==="c522"){
add("Module Class Details");add("Classroom Observation");
const sf=[];if(f.program)sf.push(["Survey Response","program","=",f.program]);add("Survey Response",sf);
}
if(tab==="c531"){
add("Partnership Agreement");add("Partnerships Agreement Management");add("Supplier Rating");
}
if(tab==="quality"){
const cs=[["Course Schedule","schedule_date",">=",f.start],["Course Schedule","schedule_date","<=",f.end]];
if(f.program)cs.push(["Course Schedule","program","=",f.program]);
if(f.student_group)cs.push(["Course Schedule","student_group","=",f.student_group]);
add("Course Schedule",cs);add("Course Enrollment");
const ar=[];if(f.year)ar.push(["Assessment Result","academic_year","=",f.year]);if(f.program)ar.push(["Assessment Result","program","=",f.program]);if(f.student_group)ar.push(["Assessment Result","student_group","=",f.student_group]);
add("Assessment Result",ar);
}
for(let i=0;i<tasks.length;i++){
const t=tasks[i];
setProgress(8+(i/Math.max(tasks.length,1))*68,`Loading ${t.dt}`);
state.data[t.dt]=await load(t.dt,t.filters);
if(t.dt==="Survey Response")populateSurveyModuleFilter();
}
if(tab==="c512"){setProgress(78,"Computing 5.1.2 analytics");state.c512Server=await fetchC512Model();}
if(tab==="c521"){setProgress(78,"Computing 5.2.1 analytics");state.c521Server=await fetchC521Model();}
if(tab==="c522"){setProgress(78,"Computing 5.2.2 analytics");state.c522Server=await fetchC522Model();}
if(tab==="c531"){setProgress(78,"Computing 5.3.1 analytics");state.c531Server=await fetchC531Model();}
if(["c54","quality"].includes(tab)){
const schedules=state.data["Course Schedule"]||[];
const names=schedules.map(x=>x.name).filter(Boolean);
let att=[];const chunks=[];
for(let i=0;i<names.length;i+=200)chunks.push(names.slice(i,i+200));
for(let i=0;i<chunks.length;i++){
setProgress(78+(i/Math.max(chunks.length,1))*14,`Loading attendance ${i+1}/${chunks.length}`);
att.push(...await load("Student Attendance",[["Student Attendance","course_schedule","in",chunks[i]]]));
}
state.data["Student Attendance"]=att;
}
setProgress(94,"Calculating answers and charts");
state.loadedSections[tab]=true;
const c=compute();
buildQuality(c);
setProgress(96,"Computing Criterion 5 answers");
state.c5qaServer=await fetchC5QAModel();
makeQA(c);
renderCharts(tab,c);
if(tab==="c511")renderC511();
renderNewSection(tab);
renderKpis(tab==="c511"?"c51":tab,c);
renderSources();
updateAudit();
setProgress(100,"Complete");
status("Criterion 5 section loaded for the current user and filters.");
}catch(e){
status(`Load error: ${errText(e)}`);
}finally{
state.loading=false;
hideProgress();
}
}
async function loadAll(){
state.loadedSections={};
state.data={};
state.sources={};
await loadBase();
await loadSection(root.dataset.activeTab||"overview", true);
}
function updateAudit(){const f=currentFilters();set('[data-audit="refreshed"]',formatDate(new Date()));set('[data-audit="filters"]',`${f.year||"All years"} · ${f.student_group||"All module classes"} · ${f.program||"All programmes"} · ${f.month}`)}
function parentTab(tab){if(/^c51[12]$/.test(tab))return"c51";if(/^c52[12]$/.test(tab))return"c52";if(tab==="c531")return"c53";return tab}
function renderSubnav(parent,active){
const groups=$$("[data-c5-menu-group]");
groups.forEach(group=>{
const groupId=group.dataset.c5MenuGroup;
const isParent=groupId===parent;
group.classList.toggle("is-active",isParent);
const parentButton=group.querySelector(":scope > [data-tab]");
if(parentButton){
parentButton.classList.toggle("active",isParent);
parentButton.setAttribute("aria-expanded","false");
}
group.querySelectorAll(".ucc-c5-child-menu [data-tab]").forEach(button=>{
button.classList.toggle("active",button.dataset.tab===active);
});
});
}
function showTab(tab){
tab=({c51:"c511",c52:"c521",c53:"c531"})[tab]||tab;
const parent=parentTab(tab);root.dataset.activeTab=tab;
$$(".ucc-shared-tabs > [data-tab]").forEach(button=>{
button.classList.toggle("active",button.dataset.tab===parent);
});
$$("[data-panel]").forEach(panel=>panel.classList.toggle("hidden",panel.dataset.panel!==tab));
renderSubnav(parent,tab);
loadSection(tab);
}
function sortableValue(cell){
const raw=(cell?.dataset.sortValue||cell?.textContent||"").trim();
const normalized=raw.replace(/,/g,"").replace(/%$/,"");
if(/^[-+]?\d+(\.\d+)?$/.test(normalized))return{type:"number",value:Number(normalized)};
const parsed=Date.parse(raw);
if(/\d{1,4}[-/ ]\w*[-/ ]\d{1,4}/.test(raw)&&!Number.isNaN(parsed))return{type:"date",value:parsed};
return{type:"text",value:raw.toLowerCase()};
}
function enableSortableTables(){
$$("table").forEach(table=>{
const body=table.tBodies?.[0];
if(!body)return;
table.classList.add("sortable-table");
[...(table.tHead?.rows?.[0]?.cells||[])].forEach((header,index)=>{
if(header.dataset.sortBound==="1"||header.dataset.noSort==="1")return;
header.dataset.sortBound="1";
header.tabIndex=0;
header.setAttribute("role","button");
header.setAttribute("aria-label",`${header.textContent.trim()}: sort column`);
const sort=()=>{
const direction=header.dataset.sortDirection==="asc"?"desc":"asc";
[...table.querySelectorAll("thead th")].forEach(th=>{delete th.dataset.sortDirection;th.classList.remove("sort-asc","sort-desc")});
header.dataset.sortDirection=direction;
header.classList.add(direction==="asc"?"sort-asc":"sort-desc");
const rows=[...body.rows];
rows.sort((a,b)=>{
const av=sortableValue(a.cells[index]),bv=sortableValue(b.cells[index]);
let result=0;
if(av.type===bv.type&&av.type!=="text")result=av.value-bv.value;
else result=String(av.value).localeCompare(String(bv.value),undefined,{numeric:true,sensitivity:"base"});
return direction==="asc"?result:-result;
});
rows.forEach(row=>body.appendChild(row));
};
header.addEventListener("click",sort);
header.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();sort()}});
});
});
}
function exportLog(format="csv"){
addLog("INFO","diagnostics","log_export_requested",{format,rows:state.logs.length});
if(format==="json"){
const blob=new Blob([JSON.stringify({metadata:{build_id:BUILD_ID,started_at:state.startedAt,exported_at:new Date().toISOString(),url:location.href,resolved_doctypes:state.resolvedDoctypes,sources:state.sources},logs:state.logs},null,2)],{type:"application/json"});
const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=`ucc_c5_frontend_log_${new Date().toISOString().replace(/[:.]/g,"-")}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);return;
}
const metadata=[
{sequence:0,timestamp:new Date().toISOString(),elapsed_ms:0,level:"INFO",category:"metadata",event:"diagnostic_metadata",build_id:BUILD_ID,active_tab:root.dataset.activeTab||"",details:safeJson({started_at:state.startedAt,url:location.href,resolved_doctypes:state.resolvedDoctypes,sources:state.sources})},
...state.logs
];
csv(`ucc_c5_frontend_log_${new Date().toISOString().replace(/[:.]/g,"-")}.csv`,metadata);
}
function renderDiagnosticLog(){
const body=$('[data-table="diagnostic-log"]');if(!body)return;
const level=$("[data-log-filter-level]")?.value||"",category=$("[data-log-filter-category]")?.value||"",search=($("[data-log-search]")?.value||"").toLowerCase();
const rows=state.logs.filter(row=>(!level||row.level===level)&&(!category||row.category===category)&&(!search||safeJson(row).toLowerCase().includes(search))).slice(-1000).reverse();
body.innerHTML=rows.map(row=>`<tr><td>${row.sequence}</td><td>${esc(row.timestamp)}</td><td><span class="log-level log-${row.level.toLowerCase()}">${esc(row.level)}</span></td><td>${esc(row.category)}</td><td>${esc(row.event)}</td><td><code>${esc(row.details)}</code></td></tr>`).join("")||`<tr><td colspan="6">No matching log entries.</td></tr>`;
}
function showDiagnostics(){
renderDiagnosticLog();
const dialog=$("[data-diagnostics-dialog]");if(dialog)dialog.showModal();
addLog("INFO","interaction","diagnostics_opened",{});
}
function bind(){
addLog("INFO","lifecycle","event_binding_started",{});
enableSortableTables();
$$("[data-tab]").forEach(button=>{
button.addEventListener("click",event=>{
event.stopPropagation();
showTab(button.dataset.tab);
});
});
$$("[data-c5-menu-group]").forEach(group=>{
const parentButton=group.querySelector(":scope > .ucc-c5-parent-tab");
const menu=group.querySelector(":scope > .ucc-c5-child-menu");
if(!parentButton||!menu)return;
const open=()=>{
group.classList.add("is-open");
parentButton.setAttribute("aria-expanded","true");
};
const close=()=>{
group.classList.remove("is-open");
parentButton.setAttribute("aria-expanded","false");
};
group.addEventListener("mouseenter",open);
group.addEventListener("mouseleave",close);
group.addEventListener("focusin",open);
group.addEventListener("focusout",event=>{
if(!group.contains(event.relatedTarget))close();
});
parentButton.addEventListener("keydown",event=>{
if(event.key==="ArrowDown"){
event.preventDefault();
open();
menu.querySelector("[data-tab]")?.focus();
}
if(event.key==="Escape"){
event.preventDefault();
close();
parentButton.focus();
}
});
menu.addEventListener("keydown",event=>{
const items=Array.from(menu.querySelectorAll("[data-tab]"));
const current=items.indexOf(document.activeElement);
if(event.key==="ArrowDown"){
event.preventDefault();
items[(current+1+items.length)%items.length]?.focus();
}
if(event.key==="ArrowUp"){
event.preventDefault();
items[(current-1+items.length)%items.length]?.focus();
}
if(event.key==="Escape"){
event.preventDefault();
close();
parentButton.focus();
}
});
});
$$("[data-local-tabs]").forEach(nav=>{
const section=nav.closest("[data-panel]");
const buttons=Array.from(nav.querySelectorAll("[data-local-tab]"));
const panels=section?Array.from(section.querySelectorAll(":scope > [data-local-panel]")):[];
buttons.forEach(button=>button.addEventListener("click",()=>{
buttons.forEach(item=>item.classList.toggle("active",item===button));
panels.forEach(panel=>panel.classList.toggle("hidden",panel.dataset.localPanel!==button.dataset.localTab));
if(section?.dataset.panel&&["c512","c521","c522","c531"].includes(section.dataset.panel)){
requestAnimationFrame(()=>setTimeout(()=>renderNewSection(section.dataset.panel),30));
}else{
requestAnimationFrame(()=>setTimeout(renderVisibleC511Charts,30));
}
}));
});
const refresh=$('[data-action="refresh"]');
if(refresh)refresh.addEventListener("click",loadAll);
const exportAnswers=$('[data-action="export-answers"]');
if(exportAnswers)exportAnswers.addEventListener("click",()=>{
csv("criterion5_questions_answers.csv",state.qa);
});
const exportExceptions=$('[data-action="export-exceptions"]');
if(exportExceptions)exportExceptions.addEventListener("click",()=>{
csv("criterion5_exceptions.csv",state.exceptions);
});
$$("[data-filter]").forEach(field=>{
field.addEventListener("change",loadAll);
});
const qaFilter=$("[data-qa-filter]");
if(qaFilter)qaFilter.addEventListener("change",renderOverviewQA);
const dialogClose=$("[data-dialog-close]");
if(dialogClose)dialogClose.addEventListener("click",()=>{
const dialog=$("[data-dialog]");
if(dialog)dialog.close();
});
$$("[data-survey-filter]").forEach(field=>field.addEventListener("change",async()=>{const c=compute();buildQuality(c);state.c5qaServer=await fetchC5QAModel();makeQA(c);renderSurvey();renderKpis("c54",c)}));
const clearSurvey=$('[data-action="clear-survey-filters"]');
if(clearSurvey)clearSurvey.addEventListener("click",async()=>{const t=$('[data-survey-filter="type"]'),m=$('[data-survey-filter="module"]');if(t)t.value="";if(m)m.value="";const c=compute();buildQuality(c);state.c5qaServer=await fetchC5QAModel();makeQA(c);renderSurvey();renderKpis("c54",c)});
$$("[data-visual-card]").forEach(card=>{
card.querySelectorAll("[data-card-view]").forEach(button=>button.addEventListener("click",()=>{
const view=button.dataset.cardView;
card.querySelectorAll("[data-card-view]").forEach(x=>x.classList.toggle("active",x===button));
card.querySelectorAll("[data-card-panel]").forEach(panel=>panel.classList.toggle("hidden",panel.dataset.cardPanel!==view));
if(view==="diagram")requestAnimationFrame(()=>setTimeout(renderVisibleC511Charts,30));
}));
});
$$("[data-card-toggle] [data-card-view]").forEach(button=>{
button.addEventListener("click",()=>{
const group=button.closest("[data-card-toggle]")?.dataset.cardToggle;
const view=button.dataset.cardView;
if(!group)return;
$$(`[data-card-toggle="${group}"] [data-card-view]`).forEach(b=>b.classList.toggle("active",b===button));
const tablePanel=$(`[data-card-panel="${group}-table"]`);
const diagramPanel=$(`[data-card-panel="${group}-diagram"]`);
if(tablePanel)tablePanel.classList.toggle("hidden",view!=="table");
if(diagramPanel)diagramPanel.classList.toggle("hidden",view!=="diagram");
if(view==="diagram")requestAnimationFrame(()=>setTimeout(renderVisibleC511Charts,30));
});
});
$$("[data-c511-tab]").forEach(button=>button.addEventListener("click",()=>{
$$("[data-c511-tab]").forEach(b=>b.classList.toggle("active",b===button));
$$("[data-c511-panel]").forEach(panel=>panel.classList.toggle("hidden",panel.dataset.c511Panel!==button.dataset.c511Tab));
requestAnimationFrame(()=>setTimeout(()=>{try{renderVisibleC511Charts()}catch(error){console.error("5.1.1 chart render error",error)}},40));
}));
$$("[data-gap-filter]").forEach(button=>button.addEventListener("click",()=>renderGapView(button.dataset.gapFilter)));
const export511=$('[data-action="export-511"]');
if(export511)export511.addEventListener("click",()=>csv("criterion_5_1_1_evidence_gaps.csv",state.c511Gaps||[]));
const showLog=$('[data-action="show-diagnostics"]');if(showLog)showLog.addEventListener("click",showDiagnostics);
const closeLog=$("[data-diagnostics-close]");if(closeLog)closeLog.addEventListener("click",()=>{const dialog=$("[data-diagnostics-dialog]");if(dialog)dialog.close()});
const exportLogCsv=$('[data-action="export-log-csv"]');if(exportLogCsv)exportLogCsv.addEventListener("click",()=>exportLog("csv"));
const exportLogJson=$('[data-action="export-log-json"]');if(exportLogJson)exportLogJson.addEventListener("click",()=>exportLog("json"));
const clearLog=$('[data-action="clear-log"]');if(clearLog)clearLog.addEventListener("click",()=>{state.logs=[];addLog("INFO","diagnostics","log_cleared",{});renderDiagnosticLog()});
$$("[data-log-filter-level],[data-log-filter-category],[data-log-search]").forEach(field=>field.addEventListener(field.tagName==="INPUT"?"input":"change",renderDiagnosticLog));
root.addEventListener("click",event=>{const target=event.target.closest("button,a,[data-tab],[data-local-tab],[data-card-view]");if(target)addLog("INFO","interaction","ui_click",{text:(target.textContent||"").trim().slice(0,120),action:target.dataset.action||"",tab:target.dataset.tab||target.dataset.localTab||"",href:target.getAttribute("href")||""})});
root.addEventListener("change",event=>{const target=event.target;if(target.matches("select,input"))addLog("INFO","interaction","control_changed",{name:target.dataset.filter||target.dataset.qaFilter||target.name||target.id||"",value:target.value})});
addLog("INFO","lifecycle","event_binding_completed",{});
}
function ensureD3(cb){if(window.d3)return cb();const s=document.createElement("script");s.src="https://d3js.org/d3.v7.min.js";s.onload=cb;s.onerror=()=>status("D3 could not load");document.head.appendChild(s)}
function sortChartCardsAlphabetically(){
const groups=new Map();
$$("article.panel").forEach(article=>{
if(article.querySelector("article.panel"))return;
if(!article.querySelector("[data-chart]"))return;
const parent=article.parentElement;
if(!parent)return;
if(!groups.has(parent))groups.set(parent,[]);
groups.get(parent).push(article);
});
groups.forEach(articles=>{
articles
.map(article=>({article,title:(article.querySelector("h2")?.textContent||"").trim()}))
.sort((a,b)=>a.title.localeCompare(b.title,undefined,{sensitivity:"base"}))
.forEach(({article})=>article.parentElement.appendChild(article));
});
}
function hideDisabledC5Visuals(){
C5_DISABLED_VISUALS.forEach(function(name){const n=chartNode(name),p=n&&n.closest(".panel");if(p)p.classList.add("ucc-visual-archived");});
}
hideDisabledC5Visuals();
window.__uccMergeSourcesQuality(root,"data-tab","data-panel");
(function(){const status=root.querySelector("[data-source-status]"),sp=root.querySelector('[data-panel="sources"]');const art=status&&status.closest("article");if(art&&sp)sp.insertBefore(art,sp.firstChild);})();
sortChartCardsAlphabetically();
bind();addLog("INFO","lifecycle","d3_initialization_started",{present:!!window.d3});ensureD3(async()=>{addLog("INFO","lifecycle","d3_ready",{version:window.d3?.version});await loadBase();await loadSection("overview",true);addLog("INFO","lifecycle","initialization_completed",{sources:state.sources,resolved_doctypes:state.resolvedDoctypes})});
})();
(function () {
"use strict";
const root = typeof root_element !== "undefined" ? root_element : document;
const app = root ? root.querySelector("#ajaApp") : null;
if (!app || app.dataset.admissionJourneyReady === "1") {
return;
}
app.dataset.admissionJourneyReady = "1";
const MODULE_CONFIG = {
student_journey: {
label: "Student Journey",
apiMethod: "ucc_ask_student_journey",
entityLabel: "student",
entityLabelTitle: "Student",
pinnedLabel: "Pinned student",
findLabel: "Find student",
recentLabel: "Recent students",
searchPlaceholder: "Type name or Applicant ID",
headerTitle: "Ask UCC · Student Journey",
headerSubtitle: "Ask about students, courses, modules, assessments, classes, leave and graduation.",
comingSoon: false
},
recruitment_agent: {
label: "Recruitment Agent",
apiMethod: "ucc_ask_recruitment_agent",
entityLabel: "agent",
entityLabelTitle: "Recruitment Agent",
pinnedLabel: "Pinned agent",
findLabel: "Find recruitment agent",
recentLabel: "Recent agents",
searchPlaceholder: "Type agent, company or contract ID",
headerTitle: "Ask UCC · Recruitment Agent",
headerSubtitle: "Ask about agent profiles, contracts, expiry, recruitment performance, ratings and renewal.",
comingSoon: false
},
quality_action: {
label: "Quality Action",
apiMethod: "ucc_ask_quality_action",
entityLabel: "quality action",
entityLabelTitle: "Quality Action",
pinnedLabel: "Pinned Quality Action",
findLabel: "Find Quality Action",
recentLabel: "Recent Quality Actions",
searchPlaceholder: "Type Quality Action ID or subject",
headerTitle: "Ask UCC · Quality Action",
headerSubtitle: "Ask about findings, root causes, actions, assignments, due dates, closure readiness and quality review.",
comingSoon: false
},
hr_assistant: {
label: "HR",
entityLabel: "employee",
entityLabelTitle: "Employee",
comingSoon: true
}
};
function activeModuleConfig() {
return MODULE_CONFIG[state.activeModule] || MODULE_CONFIG.student_journey;
}
const moduleSelect = root.querySelector("#ajaModuleSelect");
const moduleStatus = root.querySelector("#ajaModuleStatus");
const pinnedLabel = root.querySelector("#ajaPinnedLabel");
const findLabel = root.querySelector("#ajaFindLabel");
const recentLabel = root.querySelector("#ajaRecentLabel");
const headerTitle = root.querySelector("#ajaHeaderTitle");
const headerSubtitle = root.querySelector("#ajaHeaderSubtitle");
const comingSoon = root.querySelector("#ajaComingSoon");
const chat = root.querySelector("#ajaChat");
const questionInput = root.querySelector("#ajaQuestion");
const sendButton = root.querySelector("#ajaSend");
const printButton = root.querySelector("#ajaPrint");
const statusElement = root.querySelector("#ajaStatus");
const currentStudentElement = root.querySelector("#ajaCurrentStudent .aja-current-value");
const suggestionsContainer = root.querySelector("#ajaSuggestions");
const categorySelect = root.querySelector("#ajaQuestionCategory");
const categoryButtons = root.querySelector("#ajaQuestionCategoryButtons");
const clearChatButton = root.querySelector("#ajaClearChat");
const controlledQuestions = root.querySelector("#ajaControlledQuestions");
const studentSearch = root.querySelector("#ajaStudentSearch");
const studentMatches = root.querySelector("#ajaStudentMatches");
const sourceNotice = root.querySelector("#ajaSourceNotice");
const studentPager = root.querySelector("#ajaStudentPager");
const courseFilter = root.querySelector("#ajaCourseFilter");
const recentStudents = root.querySelector("#ajaRecentStudents");
const changeStudentButton = root.querySelector("#ajaChangeStudent");
const resetContextButton = root.querySelector("#ajaResetContext");
const exportCsvButton = root.querySelector("#ajaExportCsv");
const diagnosticsButton = root.querySelector("#ajaDiagnostics");
const apiButton = root.querySelector("#ajaApiButton");
const apiModal = root.querySelector("#ajaApiModal");
const apiKeyInput = root.querySelector("#ajaApiKeyInput");
const apiCancel = root.querySelector("#ajaApiCancel");
const apiSkip = root.querySelector("#ajaApiSkip");
const apiConnect = root.querySelector("#ajaApiConnect");
let pendingFreeQuestion = "";
const state = {
activeModule: "student_journey",
moduleRecords: null,
loading: false,
studentApplicant: "",
studentName: "",
history: [],
studentRollRows: null,
// Permission-aware fallback directory (Student Applicant) used for the record
// picker when the Student Roll report is blocked. Kept separate from
// studentRollRows so partial data is never posted back as roll evidence.
studentDirectory: null,
rollNotice: null,
lastQuestion: "",
recentStudents: [],
lastResult: null,
lastVisualRows: [],
lastExportSections: [],
searchPage: 1,
searchPageSize: 8
};
function safeArray(value) {
return Array.isArray(value) ? value : [];
}
function cleanText(value) {
return String(value === null || value === undefined ? "" : value)
.replace(/\s+/g, " ")
.trim();
}
function formatDate(value) {
if (!value) return "";
const text = String(value).trim();
let match = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T].*)?$/);
if (!match) {
match = text.match(/^(\d{1,2})[-\/]([0-9]{1,2})[-\/](\d{4})$/);
if (!match) return text;
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
return String(Number(match[1])).padStart(2, "0") + " " + months[Number(match[2]) - 1] + " " + match[3];
}
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
return String(Number(match[3])).padStart(2, "0") + " " + months[Number(match[2]) - 1] + " " + match[1];
}
function formatDatesInText(value) {
return String(value === null || value === undefined ? "" : value).replace(
/\b(\d{4}-\d{2}-\d{2})(?:[T ][0-9:.+-Z]+)?\b/g,
function (matched) {
return formatDate(matched.slice(0, 10));
}
);
}
function displayValue(value) {
if (value === null || value === undefined || value === "") {
return "Not recorded";
}
if (value && typeof value === "object" && !Array.isArray(value)) {
return formatDatesInText(
value.text || value.label || value.name || "Not recorded"
);
}
if (typeof value === "string") {
return formatDatesInText(value);
}
return String(value);
}
function setStatus(text, loading) {
if (statusElement) {
statusElement.textContent = text || "Ready";
}
const catStatus = root.querySelector("#ajaCatStatus");
if (catStatus) {
catStatus.classList.toggle("is-working", Boolean(loading));
}
}
function updateSuggestionState() {
if (!suggestionsContainer) {
return;
}
suggestionsContainer
.querySelectorAll(".aja-suggestion")
.forEach(function (button) {
button.disabled = false;
button.title = state.studentApplicant
? "Ask about " + (state.studentName || state.studentApplicant)
: "Select a student first";
});
}
function updateCurrentStudent() {
if (!currentStudentElement) return;
if (!state.studentApplicant) {
currentStudentElement.textContent = "Not selected";
return;
}
currentStudentElement.textContent =
(state.studentName || state.studentApplicant) +
" (" + state.studentApplicant + ")";
}
// Rows behind the record picker: the Student Roll report when readable,
// otherwise the permission-aware Student Applicant directory.
function studentSourceRows() {
const rows = safeArray(state.studentRollRows);
return rows.length ? rows : safeArray(state.studentDirectory);
}
function uniqueStudentsFromRoll() {
if (state.activeModule === "recruitment_agent") {
return safeArray(state.moduleRecords).map(function (row) {
return {
id: cleanText(row.name),
name: cleanText(row.party_name) || cleanText(row.name),
course: cleanText(row.personal_id) || "Agent Contract"
};
}).filter(function (item) {
return Boolean(item.id);
}).sort(function (a, b) {
return a.name.localeCompare(b.name);
});
}
if (state.activeModule === "quality_action") {
return safeArray(state.moduleRecords).map(function (row) {
return {
id: cleanText(row.name),
name: cleanText(row.custom_subject) || cleanText(row.name),
course: "Quality Action"
};
}).filter(function (item) {
return Boolean(item.id);
}).sort(function (a, b) {
return a.name.localeCompare(b.name);
});
}
const map = new Map();
studentSourceRows().forEach(function (row) {
const id = cleanText(row.student_applicant_id);
const name = cleanText(row.student_name);
if (!id || map.has(id)) return;
map.set(id, {
id: id,
name: name || id,
course: cleanText(row.course)
});
});
return Array.from(map.values()).sort(function (a, b) {
return a.name.localeCompare(b.name);
});
}
function availableCourses() {
const courses = new Set();
if (state.activeModule !== "student_journey") {
return [];
}
studentSourceRows().forEach(function (row) {
const course = cleanText(row.course);
if (course) courses.add(course);
});
return Array.from(courses).sort(function (a, b) {
return a.localeCompare(b);
});
}
function renderCourseFilter() {
if (!courseFilter) return;
const selected = courseFilter.value || "";
courseFilter.innerHTML = '<option value="">All courses</option>';
availableCourses().forEach(function (course) {
const option = document.createElement("option");
option.value = course;
option.textContent = course;
courseFilter.appendChild(option);
});
if (selected && availableCourses().includes(selected)) {
courseFilter.value = selected;
}
}
function rememberStudent(id, name) {
if (!id) return;
state.recentStudents = state.recentStudents.filter(function (item) {
return item.id !== id;
});
state.recentStudents.unshift({ id: id, name: name || id });
state.recentStudents = state.recentStudents.slice(0, 5);
saveRecentStudents();
renderRecentStudents();
}
function loadRecentStudents() {
try {
const value = JSON.parse(
window.localStorage.getItem("uccAiRecent_" + state.activeModule) || "[]"
);
state.recentStudents = Array.isArray(value) ? value : [];
} catch (error) {
state.recentStudents = [];
}
}
function saveRecentStudents() {
try {
window.localStorage.setItem(
"uccAiRecent_" + state.activeModule,
JSON.stringify(state.recentStudents)
);
} catch (error) {
console.warn("Could not save recent students", error);
}
}
function removeRecentStudent(id) {
state.recentStudents = state.recentStudents.filter(function (item) {
return item.id !== id;
});
saveRecentStudents();
renderRecentStudents();
}
function renderRecentStudents() {
if (!recentStudents) return;
recentStudents.innerHTML = "";
state.recentStudents.forEach(function (item) {
const row = document.createElement("div");
row.className = "aja-recent-row";
const button = document.createElement("button");
button.type = "button";
button.className = "aja-recent-button";
button.textContent = item.name;
button.dataset.studentApplicant = item.id;
button.dataset.studentName = item.name;
const remove = document.createElement("button");
remove.type = "button";
remove.className = "aja-recent-remove";
remove.textContent = "×";
remove.title = "Remove from recent students";
remove.setAttribute("aria-label", "Remove " + item.name);
remove.dataset.removeStudent = item.id;
row.appendChild(button);
row.appendChild(remove);
recentStudents.appendChild(row);
});
}
function selectStudent(id, name) {
state.studentApplicant = id || "";
state.studentName = name || id || "";
updateCurrentStudent();
updateSuggestionState();
rememberStudent(state.studentApplicant, state.studentName);
}
function renderStudentMatches(query) {
if (!studentMatches) return;
studentMatches.innerHTML = "";
if (studentPager) {
studentPager.innerHTML = "";
}
const value = cleanText(query).toLowerCase();
const selectedCourse = courseFilter
? cleanText(courseFilter.value)
: "";
if (!value && !selectedCourse) return;
if (state.activeModule === "student_journey" && !state.studentRollRows) {
const loading = document.createElement("div");
loading.className = "aja-search-loading";
loading.textContent = "Loading students...";
studentMatches.appendChild(loading);
return;
}
const filtered = uniqueStudentsFromRoll()
.filter(function (item) {
const matchesText = (
!value
|| item.name.toLowerCase().includes(value)
|| item.id.toLowerCase().includes(value)
);
const matchesCourse = (
state.activeModule !== "student_journey"
|| !selectedCourse
|| cleanText(item.course) === selectedCourse
);
return matchesText && matchesCourse;
});
const total = filtered.length;
const pageSize = state.searchPageSize;
const totalPages = Math.max(1, Math.ceil(total / pageSize));
if (state.searchPage > totalPages) {
state.searchPage = totalPages;
}
const startIndex = (state.searchPage - 1) * pageSize;
const pageItems = filtered.slice(startIndex, startIndex + pageSize);
if (!pageItems.length) {
const empty = document.createElement("div");
empty.className = "aja-search-empty";
empty.textContent = (state.activeModule === "student_journey" && state.rollNotice)
? state.rollNotice.text
: "No matching " + activeModuleConfig().entityLabel + " records.";
studentMatches.appendChild(empty);
}
pageItems.forEach(function (item) {
const button = document.createElement("button");
button.type = "button";
button.className = "aja-student-match";
button.dataset.studentApplicant = item.id;
button.dataset.studentName = item.name;
const strong = document.createElement("strong");
strong.textContent = item.name;
const meta = document.createElement("span");
meta.textContent = item.id + " | " + item.course;
button.appendChild(strong);
button.appendChild(meta);
studentMatches.appendChild(button);
});
if (studentPager && total) {
const count = document.createElement("span");
count.className = "aja-pager-count";
count.textContent =
String(startIndex + 1)
+ "-"
+ String(Math.min(startIndex + pageSize, total))
+ " of "
+ String(total);
const controls = document.createElement("div");
controls.className = "aja-pager-controls";
const prev = document.createElement("button");
prev.type = "button";
prev.className = "aja-pager-button";
prev.textContent = "‹";
prev.disabled = state.searchPage <= 1;
prev.dataset.pageAction = "prev";
const next = document.createElement("button");
next.type = "button";
next.className = "aja-pager-button";
next.textContent = "›";
next.disabled = state.searchPage >= totalPages;
next.dataset.pageAction = "next";
controls.appendChild(prev);
controls.appendChild(next);
studentPager.appendChild(count);
studentPager.appendChild(controls);
}
}
function csvEscape(value) {
const text = String(value === null || value === undefined ? "" : value);
return '"' + text.replace(/"/g, '""') + '"';
}
function exportLastResultCsv() {
const sections = safeArray(state.lastExportSections);
if (!sections.length) {
frappe.show_alert({
message: "Run a question with a table or summary before exporting.",
indicator: "orange"
});
return;
}
const lines = [];
sections.forEach(function (section, sectionIndex) {
if (sectionIndex) lines.push("");
lines.push(csvEscape(section.title || "Admission Journey Export"));
safeArray(section.rows).forEach(function (row) {
lines.push(safeArray(row).map(csvEscape).join(","));
});
});
const csv = "\uFEFF" + lines.join("\r\n");
const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
const url = window.URL.createObjectURL(blob);
const link = document.createElement("a");
const studentPart = cleanText(state.studentName || "cohort")
.replace(/[^a-z0-9]+/gi, "-")
.replace(/^-+|-+$/g, "")
.toLowerCase();
link.style.display = "none";
link.href = url;
link.download = "admission-journey-" + (studentPart || "export") + ".csv";
document.body.appendChild(link);
link.click();
window.setTimeout(function () {
document.body.removeChild(link);
window.URL.revokeObjectURL(url);
}, 1000);
frappe.show_alert({
message: "CSV export prepared.",
indicator: "green"
});
}
function scrollBottom() {
window.requestAnimationFrame(function () {
chat.scrollTop = chat.scrollHeight;
});
}
function addUserMessage(text) {
const wrapper = document.createElement("div");
wrapper.className = "aja-message aja-message-user";
const bubble = document.createElement("div");
bubble.className = "aja-user-bubble";
bubble.textContent = text;
wrapper.appendChild(bubble);
chat.appendChild(wrapper);
scrollBottom();
}
function createAssistantBubble() {
const wrapper = document.createElement("div");
wrapper.className = "aja-message aja-message-assistant";
const bubble = document.createElement("div");
bubble.className = "aja-assistant-bubble";
const header = document.createElement("div");
header.className = "aja-assistant-header";
const avatar = document.createElement("div");
avatar.className = "aja-avatar";
avatar.textContent = "AI";
const title = document.createElement("span");
title.textContent =
activeModuleConfig().headerTitle
|| activeModuleConfig().label
|| "UCC AI Assistant";
const content = document.createElement("div");
content.className = "aja-assistant-content";
header.appendChild(avatar);
header.appendChild(title);
bubble.appendChild(header);
bubble.appendChild(content);
wrapper.appendChild(bubble);
chat.appendChild(wrapper);
scrollBottom();
return wrapper;
}
function addLoadingMessage() {
const wrapper = createAssistantBubble();
const content = wrapper.querySelector(".aja-assistant-content");
content.innerHTML = '<div class="aja-loading">Checking ERPNext records...</div>';
return wrapper;
}
function buildUrl(source) {
if (!source || !source.doctype || !source.name) return "";
const slug =
frappe.router && typeof frappe.router.slug === "function"
? frappe.router.slug(source.doctype)
: String(source.doctype)
.toLowerCase()
.replace(/[^a-z0-9]+/g, "-")
.replace(/^-+|-+$/g, "");
return window.location.origin + "/app/" + slug + "/" + encodeURIComponent(source.name);
}
function renderSummary(container, visual) {
const grid = document.createElement("div");
grid.className = "aja-summary-grid";
safeArray(visual.items).forEach(function (item) {
const card = document.createElement("div");
card.className = "aja-summary-card";
const label = document.createElement("div");
label.className = "aja-summary-label";
label.textContent = item.label || "";
const value = document.createElement("div");
value.className = "aja-summary-value";
value.textContent = displayValue(item.value);
card.appendChild(label);
card.appendChild(value);
grid.appendChild(card);
});
container.appendChild(grid);
}
function renderTable(container, visual) {
const wrap = document.createElement("div");
wrap.className = "aja-table-wrap";
const table = document.createElement("table");
table.className = "aja-table";
const thead = document.createElement("thead");
const headRow = document.createElement("tr");
safeArray(visual.columns).forEach(function (column) {
const th = document.createElement("th");
th.textContent = column;
headRow.appendChild(th);
});
thead.appendChild(headRow);
table.appendChild(thead);
const tbody = document.createElement("tbody");
safeArray(visual.rows).forEach(function (row) {
const tr = document.createElement("tr");
safeArray(row).forEach(function (value) {
const td = document.createElement("td");
if (
value
&& typeof value === "object"
&& !Array.isArray(value)
&& value.doctype
&& value.name
) {
const link = document.createElement("a");
link.className = "aja-record-link";
link.href = "/app/"
+ frappe.router.slug(value.doctype)
+ "/"
+ encodeURIComponent(value.name);
link.target = "_blank";
link.rel = "noopener noreferrer";
link.textContent = displayValue(value);
link.title = "Open " + value.doctype + " " + value.name;
td.appendChild(link);
} else {
td.textContent = displayValue(value);
}
tr.appendChild(td);
});
tbody.appendChild(tr);
});
table.appendChild(tbody);
wrap.appendChild(table);
container.appendChild(wrap);
}
function renderSources(container, sources) {
const seen = new Set();
const wrapper = document.createElement("div");
wrapper.className = "aja-source-links";
safeArray(sources).forEach(function (source) {
if (!source || !source.doctype || !source.name) return;
const key = source.doctype + "::" + source.name;
if (seen.has(key)) return;
seen.add(key);
const url = buildUrl(source);
if (!url) return;
const link = document.createElement("a");
link.className = "aja-source-link";
link.href = url;
link.target = "_blank";
link.rel = "noopener noreferrer";
link.title = source.label || source.name;
link.textContent = "Source: " + (source.short_label || source.label || source.name);
wrapper.appendChild(link);
});
if (wrapper.children.length) {
container.appendChild(wrapper);
}
}
function renderTimeline(container, visual) {
const timeline = document.createElement("div");
timeline.className = "aja-timeline";
safeArray(visual.items).forEach(function (item) {
const row = document.createElement("div");
row.className = "aja-timeline-item";
const marker = document.createElement("div");
marker.className = "aja-timeline-marker";
const body = document.createElement("div");
body.className = "aja-timeline-body";
const date = document.createElement("div");
date.className = "aja-timeline-date";
date.textContent = item.date || "Not recorded";
const title = document.createElement("div");
title.className = "aja-timeline-title";
title.textContent = item.title || "";
const description = document.createElement("div");
description.className = "aja-timeline-description";
description.textContent = item.description || "";
body.appendChild(date);
body.appendChild(title);
body.appendChild(description);
row.appendChild(marker);
row.appendChild(body);
timeline.appendChild(row);
});
container.appendChild(timeline);
}
function renderResponse(result) {
state.lastResult = result || null;
state.lastVisualRows = [];
state.lastExportSections = [];
const wrapper = createAssistantBubble();
const content = wrapper.querySelector(".aja-assistant-content");
const answer = document.createElement("div");
answer.className = "aja-answer";
answer.textContent = formatDatesInText(result.answer || "No answer was returned.");
const outOfScope = (
result.confidence === "Not applicable"
|| cleanText(result.answer).toLowerCase().includes("outside the admission journey scope")
|| cleanText(result.answer).toLowerCase().includes("not an admission journey question")
);
if (outOfScope) {
wrapper.classList.add("aja-message-out-of-scope");
answer.innerHTML =
'<span class="aja-out-scope-icon">!</span>'
+ '<span>'
+ frappe.utils.escape_html(
formatDatesInText(result.answer || "This question is outside the Admission Journey scope.")
)
+ '</span>';
}
content.appendChild(answer);
safeArray(result.warnings).forEach(function (warning) {
const box = document.createElement("div");
box.className = "aja-warning";
box.textContent = "Warning: " + formatDatesInText(warning);
content.appendChild(box);
});
safeArray(result.visuals).forEach(function (visual) {
const section = document.createElement("section");
section.className = "aja-visual";
const title = document.createElement("div");
title.className = "aja-visual-title";
title.textContent = visual.title || "Student information";
section.appendChild(title);
if (visual.type === "table" || visual.type === "timeline_table") {
const tableRows = [safeArray(visual.columns)].concat(safeArray(visual.rows));
state.lastVisualRows = tableRows;
state.lastExportSections.push({
title: visual.title || "Table",
rows: tableRows
});
} else if (visual.type === "summary") {
state.lastExportSections.push({
title: visual.title || "Summary",
rows: [["Field", "Value"]].concat(
safeArray(visual.items).map(function (item) {
return [item.label || "", displayValue(item.value)];
})
)
});
}
if (visual.type === "summary") {
renderSummary(section, visual);
} else if (visual.type === "table" || visual.type === "timeline_table") {
renderTable(section, visual);
} else if (visual.type === "timeline") {
renderTimeline(section, visual);
}
content.appendChild(section);
});
renderSources(content, result.sources || result.source_links);
if (result.confidence) {
const confidence = document.createElement("div");
confidence.className = "aja-confidence";
confidence.textContent = "Confidence: " + result.confidence;
content.appendChild(confidence);
}
if (result.diagnostics && Object.keys(result.diagnostics).length) {
const details = document.createElement("details");
details.className = "aja-diagnostic-details";
const summary = document.createElement("summary");
summary.textContent = "Diagnostic details";
const pre = document.createElement("pre");
pre.textContent = JSON.stringify(result.diagnostics, null, 2);
details.appendChild(summary);
details.appendChild(pre);
content.appendChild(details);
}
if (result.ai_used) {
const note = document.createElement("div");
note.className = "aja-ai-note";
note.textContent = "OpenAI interpreted the question. ERPNext supplied the facts.";
content.appendChild(note);
}
if (result.student_applicant || result.agent_contract) {
state.studentApplicant =
result.student_applicant || result.agent_contract;
state.studentName =
result.student_name || result.agent_name || state.studentApplicant;
updateCurrentStudent();
}
scrollBottom();
}
function renderCandidateSelection(result, originalQuestion) {
const wrapper = createAssistantBubble();
const content = wrapper.querySelector(".aja-assistant-content");
const answer = document.createElement("div");
answer.className = "aja-answer";
answer.textContent = result.answer || "More than one student matches. Select the correct student below.";
content.appendChild(answer);
const list = document.createElement("div");
list.className = "aja-candidate-list";
safeArray(result.candidates).forEach(function (candidate) {
const button = document.createElement("button");
button.type = "button";
button.className = "aja-candidate";
button.dataset.studentApplicant = candidate.student_applicant || "";
button.dataset.studentName = candidate.student_name || "";
button.dataset.question = originalQuestion;
const strong = document.createElement("strong");
strong.textContent = candidate.student_name || candidate.student_applicant;
const detail = document.createElement("span");
detail.textContent = [
candidate.student_applicant,
candidate.program,
candidate.student_type
].filter(Boolean).join(" | ");
button.appendChild(strong);
button.appendChild(detail);
list.appendChild(button);
});
content.appendChild(list);
scrollBottom();
}
async function loadRecruitmentAgents() {
if (state.moduleRecords) {
return state.moduleRecords;
}
try {
const response = await frappe.call({
method: "frappe.client.get_list",
args: {
doctype: "Agent Contract",
fields: ["name", "party_name", "personal_id"],
filters: [],
order_by: "modified desc",
limit_page_length: 500
},
freeze: false
});
state.moduleRecords = response && Array.isArray(response.message)
? response.message
: [];
} catch (error) {
console.warn("Recruitment agents could not be loaded", error);
state.moduleRecords = [];
setModuleLoadNotice(error, "Recruitment agents", "Agent Contract");
}
return state.moduleRecords;
}
async function loadQualityActions() {
if (state.moduleRecords) {
return state.moduleRecords;
}
try {
const response = await frappe.call({
method: "frappe.client.get_list",
args: {
doctype: "Quality Action",
fields: ["name", "custom_subject", "modified"],
filters: [],
order_by: "modified desc",
limit_page_length: 1000
},
freeze: false
});
state.moduleRecords = response && Array.isArray(response.message)
? response.message
: [];
} catch (error) {
console.warn("Quality Actions could not be loaded", error);
state.moduleRecords = [];
setModuleLoadNotice(error, "Quality Actions", "Quality Action");
}
return state.moduleRecords;
}
async function loadActiveModuleData() {
if (state.activeModule === "recruitment_agent") {
return loadRecruitmentAgents();
}
if (state.activeModule === "student_journey") {
return loadStudentRollReport();
}
if (state.activeModule === "quality_action") {
return loadQualityActions();
}
return [];
}
async function loadStudentRollReport() {
if (state.studentRollRows) {
return state.studentRollRows;
}
try {
const response = await frappe.call({
method: "frappe.desk.query_report.run",
args: {
report_name: "Student Roll",
filters: {
from_date: "2000-01-01",
to_date: "2100-12-31"
},
ignore_prepared_report: true,
are_default_filters: false
},
freeze: false
});
const message = response ? response.message : null;
state.studentRollRows =
message && Array.isArray(message.result)
? message.result
: [];
state.rollNotice = null;
} catch (error) {
console.warn("Student Roll report could not be loaded", error);
state.studentRollRows = [];
await handleRollFailure(error);
}
renderCourseFilter();
renderSourceNotice();
return state.studentRollRows;
}
// The Student Roll report joins sources such as Assessment Result, so a user
// without read access to every one of them gets a 403 for the whole report.
// Classify the failure, then try the permission-aware directory so the picker
// shows whatever that user IS allowed to read instead of nothing at all.
async function handleRollFailure(error) {
const detail = UCCShared.errorText(error);
const kind = UCCShared.classifyError(detail);
const directory = await loadStudentDirectoryFallback();
const recovered = safeArray(directory).length;
if (kind === "Permission denied") {
state.rollNotice = {
tone: recovered ? "partial" : "blocked",
permission: !recovered, view: "The student list", source: UCCShared.permissionSource(detail, "Assessment Result"),
text: recovered
? "Showing the records your account can read. The full student list needs read access to every source used by the Student Roll report (including Assessment Result), so some students may be missing."
: "Student list unavailable: your account lacks read access to a required source (including Assessment Result). Ask an administrator for read permission on the Student Roll report sources.",
detail: detail
};
return;
}
state.rollNotice = {
tone: recovered ? "partial" : "blocked",
text: recovered
? "The full student list could not be loaded, so a reduced list is shown. Some students may be missing."
: (kind === "Not installed"
? "Student list unavailable: the Student Roll report is not available on this site."
: "Student list unavailable: the Student Roll report could not be loaded."),
detail: detail
};
}
// Minimal permission-aware source for the record picker: Student Applicant
// carries the same identifier the assistant sends back (student_applicant),
// plus the name parts and programme. get_list enforces the caller's read
// permission, so this never exposes anything the user could not already read.
async function loadStudentDirectoryFallback() {
if (state.studentDirectory) {
return state.studentDirectory;
}
try {
const response = await frappe.call({
method: "frappe.client.get_list",
args: {
doctype: "Student Applicant",
fields: ["name", "first_name", "middle_name", "last_name", "program"],
filters: [["Student Applicant", "docstatus", "<", 2]],
order_by: "modified desc",
limit_page_length: 5000
},
freeze: false
});
const rows = response && Array.isArray(response.message) ? response.message : [];
state.studentDirectory = rows.map(function (row) {
const parts = [];
["first_name", "middle_name", "last_name"].forEach(function (field) {
const value = cleanText(row[field]);
if (value && parts.indexOf(value) === -1) parts.push(value);
});
return {
student_applicant_id: cleanText(row.name),
student_name: parts.join(" ") || cleanText(row.name),
course: cleanText(row.program)
};
});
} catch (error) {
console.warn("Student Applicant directory could not be loaded", error);
state.studentDirectory = [];
}
return state.studentDirectory;
}
// Any Ask UCC module whose record list fails to load explains why, instead of
// leaving an empty picker. Permission blocks get the shared wording.
function setModuleLoadNotice(error, label, sourceName) {
const detail = UCCShared.errorText(error);
state.rollNotice = UCCShared.isPermissionError(detail)
? { tone: "blocked", permission: true, view: label,
    source: UCCShared.permissionSource(detail, sourceName),
    text: label + " unavailable: your account doesn't have read access to " + UCCShared.permissionSource(detail, sourceName) + ". Ask an administrator to grant access if you need to see this.",
    detail: detail }
: { tone: "blocked", view: label, source: sourceName,
    text: label + " could not be loaded.", detail: detail };
}
function renderSourceNotice() {
if (!sourceNotice) return;
const notice = state.rollNotice;
sourceNotice.hidden = !notice;
if (!notice) { sourceNotice.innerHTML = ""; sourceNotice.removeAttribute("title"); return; }
// Permission blocks use the shared platform-wide notice so Ask UCC reads the
// same as every dashboard; other failures keep the plain sentence.
if (notice.permission) {
sourceNotice.classList.remove("aja-warning");
sourceNotice.innerHTML = UCCShared.permissionNoticeHtml({view: notice.view || "This list", source: notice.source, detail: notice.detail, compact: true});
sourceNotice.removeAttribute("title");
} else {
sourceNotice.classList.add("aja-warning");
sourceNotice.textContent = notice.text;
if (notice.detail) sourceNotice.title = notice.detail;
}
}
async function sendQuestion(question, selectedApplicant, showUserMessage) {
const text = cleanText(question);
if (!text || state.loading) return;
state.loading = true;
state.lastQuestion = text;
sendButton.disabled = true;
setStatus("Checking records", true);
if (showUserMessage !== false) {
addUserMessage(text);
state.history.push({ role: "user", content: text });
}
const loadingMessage = addLoadingMessage();
try {
await loadActiveModuleData();
const moduleConfig = activeModuleConfig();
const selectedRecord = (
selectedApplicant === "__GLOBAL__"
? ""
: (selectedApplicant || state.studentApplicant || "")
);
const requestArgs = {
question: text,
conversation: JSON.stringify(state.history.slice(-20))
};
try {
const sessionKey = window.sessionStorage.getItem("uccAiOpenAIKey") || "";
if (sessionKey) requestArgs.openai_api_key = sessionKey;
} catch (error) {
}
if (state.activeModule === "student_journey") {
requestArgs.student_applicant = selectedRecord;
requestArgs.student_roll_rows = JSON.stringify(state.studentRollRows || []);
} else if (state.activeModule === "recruitment_agent") {
requestArgs.agent_contract = selectedRecord;
} else if (state.activeModule === "quality_action") {
requestArgs.quality_action = selectedRecord;
}
const response = await frappe.call({
method: moduleConfig.apiMethod,
args: requestArgs,
freeze: false
});
loadingMessage.remove();
const result = response && response.message ? response.message : response;
if (result && result.status === "choose_student") {
renderCandidateSelection(result, text);
return;
}
renderResponse(result || {
status: "error",
answer: "No response was returned.",
warnings: [],
visuals: [],
sources: []
});
state.history.push({
role: "assistant",
content: result && result.answer ? result.answer : ""
});
} catch (error) {
loadingMessage.remove();
console.error("Admission Journey Assistant error", error);
renderResponse({
status: "error",
answer: "Unable to retrieve the information.",
warnings: ["Open the browser console for the exact ERPNext error."],
visuals: [],
sources: []
});
} finally {
state.loading = false;
sendButton.disabled = false;
setStatus("Ready", false);
questionInput.focus();
}
}
function resetChatPanel() {
if (!chat) return;
chat.innerHTML = "";
if (comingSoon) {
comingSoon.hidden = true;
comingSoon.innerHTML = "";
chat.appendChild(comingSoon);
}
const welcome = document.createElement("div");
welcome.className = "aja-welcome";
const avatar = document.createElement("div");
avatar.className = "aja-avatar";
avatar.textContent = "AI";
const content = document.createElement("div");
const title = document.createElement("strong");
title.textContent = "Ready to review";
const paragraph = document.createElement("p");
paragraph.textContent = "Select a record, then choose a guided question.";
const example = document.createElement("div");
example.className = "aja-example";
example.textContent = "ERPNext evidence, tables, warnings and AI interpretation will appear here.";
content.appendChild(title);
content.appendChild(paragraph);
content.appendChild(example);
welcome.appendChild(avatar);
welcome.appendChild(content);
chat.appendChild(welcome);
state.history = [];
state.lastQuestion = "";
state.lastResult = null;
state.lastVisualRows = [];
state.lastExportSections = [];
}
function closeApiModal() {
if (apiModal) apiModal.hidden = true;
}
function proceedFreeQuestion(useStoredKey) {
const question = cleanText(pendingFreeQuestion || (questionInput ? questionInput.value : ""));
pendingFreeQuestion = "";
closeApiModal();
if (!question) return;
if (questionInput) questionInput.value = "";
sendQuestion(question, "", true);
}
sendButton.addEventListener("click", function () {
const question = questionInput.value.trim();
if (!question) return;
let hasSessionKey = false;
try {
hasSessionKey = Boolean(window.sessionStorage.getItem("uccAiOpenAIKey"));
} catch (error) {}
if (hasSessionKey || !apiModal) {
questionInput.value = "";
sendQuestion(question, "", true);
return;
}
pendingFreeQuestion = question;
apiModal.hidden = false;
if (apiKeyInput) apiKeyInput.focus();
});
if (apiButton) {
apiButton.addEventListener("click", function () {
pendingFreeQuestion = "";
if (apiModal) apiModal.hidden = false;
if (apiKeyInput) apiKeyInput.focus();
});
}
if (clearChatButton) {
clearChatButton.addEventListener("click", function () {
resetChatPanel();
setStatus("Ready", false);
});
}
if (apiCancel) apiCancel.addEventListener("click", function () {
pendingFreeQuestion = "";
closeApiModal();
});
if (apiSkip) apiSkip.addEventListener("click", function () {
proceedFreeQuestion(false);
});
if (apiConnect) apiConnect.addEventListener("click", function () {
const key = cleanText(apiKeyInput ? apiKeyInput.value : "");
if (!key) {
if (apiKeyInput) apiKeyInput.focus();
return;
}
try {
window.sessionStorage.setItem("uccAiOpenAIKey", key);
} catch (error) {}
if (apiKeyInput) apiKeyInput.value = "";
proceedFreeQuestion(true);
});
function blockGlobalSearch(event) {
const path = event.composedPath ? event.composedPath() : [];
if (!path.includes(questionInput)) return;
event.stopPropagation();
if (event.key === "Enter" && !event.shiftKey) {
event.preventDefault();
sendButton.click();
}
}
["keydown", "keypress", "keyup"].forEach(function (eventName) {
app.addEventListener(eventName, blockGlobalSearch, true);
});
if (studentSearch) {
["click", "mousedown", "keydown", "keyup", "input"].forEach(function (eventName) {
studentSearch.addEventListener(eventName, function (event) {
event.stopPropagation();
});
});
studentSearch.addEventListener("input", function () {
state.searchPage = 1;
renderStudentMatches(studentSearch.value);
});
}
if (courseFilter) {
courseFilter.addEventListener("change", function (event) {
event.stopPropagation();
state.searchPage = 1;
renderStudentMatches(studentSearch ? studentSearch.value : "");
});
}
if (studentPager) {
studentPager.addEventListener("click", function (event) {
const button = event.target.closest(".aja-pager-button");
if (!button) return;
event.preventDefault();
event.stopPropagation();
if (button.dataset.pageAction === "prev" && state.searchPage > 1) {
state.searchPage = state.searchPage - 1;
}
if (button.dataset.pageAction === "next") {
state.searchPage = state.searchPage + 1;
}
renderStudentMatches(studentSearch ? studentSearch.value : "");
});
}
if (studentMatches) {
studentMatches.addEventListener("pointerdown", function (event) {
const button = event.target.closest(".aja-student-match");
if (!button) return;
event.preventDefault();
event.stopPropagation();
selectStudent(
button.dataset.studentApplicant,
button.dataset.studentName
);
studentMatches.innerHTML = "";
studentSearch.value = "";
questionInput.focus();
});
}
if (recentStudents) {
recentStudents.addEventListener("click", function (event) {
const removeButton = event.target.closest(".aja-recent-remove");
if (removeButton) {
event.preventDefault();
event.stopPropagation();
removeRecentStudent(removeButton.dataset.removeStudent || "");
return;
}
const button = event.target.closest(".aja-recent-button");
if (!button) return;
selectStudent(
button.dataset.studentApplicant,
button.dataset.studentName
);
});
}
if (changeStudentButton) {
changeStudentButton.addEventListener("click", function () {
studentSearch.focus();
});
}
if (resetContextButton) {
resetContextButton.addEventListener("click", function () {
state.studentApplicant = "";
state.studentName = "";
state.history = [];
updateCurrentStudent();
setStatus("Context reset", false);
});
}
if (exportCsvButton) {
exportCsvButton.addEventListener("click", exportLastResultCsv);
}
if (diagnosticsButton) {
diagnosticsButton.addEventListener("click", function () {
if (!state.studentApplicant) {
setStatus("Select a student first", false);
return;
}
sendQuestion(
"Show admin diagnostics for this student",
state.studentApplicant,
true
);
});
}
loadRecentStudents();
renderRecentStudents();
printButton.addEventListener("click", function () {
window.print();
});
const studentQuestionMap = {
profile: [
["Student profile", "Show this student's profile"],
["Course", "What course is this student in?"],
["Nationality", "What is this student's nationality?"],
["Commencement", "When did this student start?"],
["Completion", "When is this student completing the course?"]
],
journey: [
["Full timeline", "Show this student's journey"],
["Current module", "Which module is this student in right now?"],
["Class and group", "Show this student's class and student group"],
["Current leave", "Is this student on leave now?"]
],
academic: [
["All results", "Show all this student's results and grades"],
["Module completion", "Has this student finished all modules?"],
["Graduation status", "Has this student graduated?"],
["Results and grades", "Show all this student\'s results and grades"]
],
attendance: [
["Attendance summary", "Show this student's attendance"],
["Current leave", "Is this student on leave now?"],
["Leave history", "Show this student's leave records"]
],
finance: [
["Payment status", "Show this student's fee and payment status"],
["Outstanding fees", "Does this student have outstanding fees?"],
["Invoices", "Show this student's invoices"],
["FPS status", "What is this student's FPS status?"]
],
graduation: [
["Readiness", "Is this student ready to graduate?"],
["Risk summary", "Show this student's risk summary"],
["Follow-up actions", "What follow-up actions are needed for this student?"],
["Admission documents", "Show this student's attached admission documents"]
],
cohort: [
["Cohort dashboard", "Show the cohort dashboard"],
["Class today", "Who are the students in class today?"],
["Graduating this month", "Who is graduating this month?"],
["Graduated months ago", "Who graduated 6 months ago?"],
["Leave count", "How many students are on leave from 15 to 30 August 2026?"]
]
};
const recruitmentQuestionMap = {
profile: [
["Agent profile", "Show this agent's profile"],
["Contract status", "Is this agent's contract active?"],
["Contract dates", "Show this agent's contract dates"]
],
journey: [
["Agent journey", "Show this agent's complete journey"],
["Latest contract", "Show this agent's latest contract"],
["Expiry", "When does this agent's contract expire?"]
],
academic: [
["Students recruited", "How many students did this agent recruit?"],
["Recruitment list", "Show students recruited by this agent"]
],
attendance: [
["Latest rating", "What is this agent's latest rating?"],
["Rating threshold", "Does this agent meet the minimum rating?"]
],
finance: [
["Revenue contribution", "What revenue came from this agent?"],
["Commission status", "Show this agent's commission status"]
],
graduation: [
["Renewal readiness", "Should this agent's contract be renewed?"],
["Compliance issues", "Show this agent's compliance issues"],
["Risk summary", "Show this agent's risk summary"]
],
cohort: [
["Active agents", "How many recruitment agents have active contracts?"],
["Expiring contracts", "Which agent contracts are expiring soon?"]
]
};
const qualityActionQuestionMap = {
profile: [
["Quality Action overview", "Show this Quality Action"],
["Problem", "What is the problem?"],
["Current status", "What is the current status?"]
],
journey: [
["Root cause and resolution", "Show the root cause and resolution"],
["Action taken", "What action has been taken?"],
["Assigned person", "Who is assigned?"]
],
academic: [
["Due date", "When is it due?"],
["Overdue check", "Is it overdue?"],
["Completion status", "What is the current status?"]
],
attendance: [
["Closure readiness", "Is this Quality Action ready for closure?"],
["Quality review", "Run a quality review of the root cause and action taken"],
["Root-cause review", "Assess the root cause and resolution"]
],
finance: [
["Open Quality Actions", "Show all open Quality Actions"],
["Overdue Quality Actions", "Show overdue Quality Actions"]
],
graduation: [
["NC findings", "Show NC findings"],
["OFI findings", "Show OFI findings"]
],
cohort: [
["All open actions", "Show all open Quality Actions"],
["All overdue actions", "Show overdue Quality Actions"],
["All NC findings", "Show NC findings"],
["All OFI findings", "Show OFI findings"]
]
};
function renderCategoryButtons() {
if (!categoryButtons || !categorySelect) return;
categoryButtons.innerHTML = "";
Array.from(categorySelect.options).forEach(function (option) {
const button = document.createElement("button");
button.type = "button";
button.className = "aja-category-button";
button.dataset.value = option.value;
button.textContent = option.textContent;
if (option.value === categorySelect.value) {
button.classList.add("active");
}
button.addEventListener("click", function () {
categorySelect.value = option.value;
categorySelect.dispatchEvent(new Event("change", { bubbles: true }));
});
categoryButtons.appendChild(button);
});
}
function renderControlledQuestions() {
if (!controlledQuestions || !categorySelect) {
return;
}
renderCategoryButtons();
controlledQuestions.innerHTML = "";
const category = categorySelect.value || "profile";
const questionMap = state.activeModule === "recruitment_agent"
? recruitmentQuestionMap
: (
state.activeModule === "quality_action"
? qualityActionQuestionMap
: studentQuestionMap
);
const questions = questionMap[category] || [];
questions.forEach(function (item) {
const button = document.createElement("button");
button.type = "button";
button.className = "aja-suggestion";
button.dataset.question = item[1];
button.textContent = item[0];
controlledQuestions.appendChild(button);
});
}
if (categorySelect) {
categorySelect.addEventListener("change", renderControlledQuestions);
}
suggestionsContainer.addEventListener("click", function (event) {
const button = event.target.closest(".aja-suggestion");
if (!button) return;
const question = button.dataset.question || button.textContent.trim();
const isCohortQuestion = (
categorySelect
&& categorySelect.value === "cohort"
);
if (isCohortQuestion) {
sendQuestion(question, "__GLOBAL__", true);
return;
}
if (state.studentApplicant) {
sendQuestion(question, state.studentApplicant, true);
return;
}
const moduleConfig = activeModuleConfig();
questionInput.value = "";
questionInput.placeholder =
"Enter or select a " + moduleConfig.entityLabel + " first";
questionInput.focus();
setStatus("Select a " + moduleConfig.entityLabel + " first", false);
});
function resetModuleContext() {
state.studentApplicant = "";
state.studentName = "";
state.history = [];
state.lastResult = null;
state.lastVisualRows = [];
state.lastExportSections = [];
state.searchPage = 1;
state.moduleRecords = null;
if (studentSearch) studentSearch.value = "";
if (studentMatches) studentMatches.innerHTML = "";
if (studentPager) studentPager.innerHTML = "";
updateCurrentStudent();
}
function renderCategoryOptions() {
if (!categorySelect) return;
const options = state.activeModule === "recruitment_agent"
? [
["profile", "Profile and Contract"],
["journey", "Agent Journey"],
["academic", "Recruitment Performance"],
["attendance", "Ratings"],
["finance", "Revenue and Commission"],
["graduation", "Compliance and Renewal"],
["cohort", "Agent Portfolio"]
]
: (
state.activeModule === "quality_action"
? [
["profile", "Overview"],
["journey", "Root Cause and Action"],
["academic", "Status and Due Dates"],
["attendance", "Review and Closure"],
["finance", "Open and Overdue"],
["graduation", "Finding Types"],
["cohort", "Quality Action Portfolio"]
]
: [
["profile", "Profile"],
["journey", "Student Journey"],
["academic", "Academic and Results"],
["attendance", "Attendance and Leave"],
["finance", "Fees and Payments"],
["graduation", "Graduation and Risk"],
["cohort", "Cohort Questions"]
]
);
categorySelect.innerHTML = "";
options.forEach(function (item) {
const option = document.createElement("option");
option.value = item[0];
option.textContent = item[1];
categorySelect.appendChild(option);
});
}
async function applyModule(moduleId) {
state.activeModule = moduleId || "student_journey";
resetModuleContext();
const config = activeModuleConfig();
if (pinnedLabel) pinnedLabel.textContent = config.pinnedLabel || "Pinned record";
if (findLabel) findLabel.textContent = config.findLabel || "Find record";
if (recentLabel) recentLabel.textContent = config.recentLabel || "Recent records";
if (studentSearch) studentSearch.placeholder = config.searchPlaceholder || "Type to search";
if (headerTitle) headerTitle.textContent = config.headerTitle || config.label;
if (headerSubtitle) headerSubtitle.textContent = config.headerSubtitle || "";
if (moduleStatus) {
moduleStatus.textContent = config.comingSoon
? config.label + " is coming soon."
: config.label + " is active.";
}
if (courseFilter) {
courseFilter.hidden = state.activeModule !== "student_journey";
}
if (comingSoon) {
comingSoon.hidden = !config.comingSoon;
comingSoon.textContent = config.comingSoon
? config.label + " is planned for a future version."
: "";
}
if (questionInput) questionInput.disabled = Boolean(config.comingSoon);
if (sendButton) sendButton.disabled = Boolean(config.comingSoon);
if (suggestionsContainer) suggestionsContainer.hidden = Boolean(config.comingSoon);
renderCategoryOptions();
renderControlledQuestions();
renderSourceNotice();
if (!config.comingSoon) {
setStatus("Loading " + config.entityLabel + " records", true);
await loadActiveModuleData();
renderCourseFilter();
renderSourceNotice();
setStatus(state.rollNotice ? "Limited record access" : "Ready", false);
} else {
setStatus("Coming soon", false);
}
}
if (moduleSelect) {
moduleSelect.addEventListener("change", function () {
applyModule(moduleSelect.value);
});
}
renderControlledQuestions();
applyModule("student_journey");
updateCurrentStudent();
updateSuggestionState();
})();
(function(){
"use strict";
const root=typeof root_element!=="undefined"
?root_element.querySelector("#uccIntelligencePlatform")
:document.querySelector("#uccIntelligencePlatform");
if(!root||root.dataset.v110Ready==="1")return;
root.dataset.v110Ready="1";
const STORAGE_KEY="ucc-intelligence-platform-v1.2.0-view";
const $=(selector,scope=root)=>scope.querySelector(selector);
const $$=(selector,scope=root)=>Array.from(scope.querySelectorAll(selector));
function notify(message,indicator="blue"){
if(window.frappe&&frappe.show_alert)frappe.show_alert({message,indicator},5);
else console.info("[UCC]",message);
}
function visiblePanel(){
return $$(".panel-view").find(panel=>!panel.classList.contains("hidden")&&panel.offsetParent!==null)
|| $$(".panel-view").find(panel=>!panel.classList.contains("hidden"));
}
function activeTable(){
const panel=visiblePanel()||root;
return $$("table",panel).find(table=>table.offsetParent!==null)||$("table",panel);
}
const csvCell=UCCShared.csvCell;
function tableToCsv(table){return UCCShared.tableToCsv(table);}
function download(name,content,type="text/csv;charset=utf-8"){return UCCShared.download(name,content,type);}
function exportCurrentTable(){
const table=activeTable();
if(!table){notify("No visible table to export.","orange");return}
download("ucc-current-table.csv",tableToCsv(table));
}
function exportExceptions(){
const panel=visiblePanel()||root;
const candidate=$$("table",panel).find(table=>/exception|gap|risk|attention/i.test(table.closest(".panel")?.innerText||""));
if(!candidate){notify("No visible exception table in this view.","orange");return}
download("ucc-current-exceptions.csv",tableToCsv(candidate));
}
function selectedState(){
const selected={};
const activeMain=$(".tabs [data-tab].active");
const activeLocal=$(".section-local-tabs [data-local-tab].active");
const activeWorkspace=$("[data-ucc-workspace].is-active");
if(activeMain)selected.tab=activeMain.dataset.tab;
if(activeLocal)selected.localTab=activeLocal.dataset.localTab;
if(activeWorkspace)selected.workspace=activeWorkspace.dataset.uccWorkspace;
selected.filters={};
$$("[data-filter]").forEach(el=>selected.filters[el.dataset.filter]=el.value);
return selected;
}
function saveState(){
try{localStorage.setItem(STORAGE_KEY,JSON.stringify(selectedState()))}catch(e){console.warn("[UCC] state persistence unavailable",e)}
}
function copyFilteredLink(){
const state=selectedState(),url=new URL(location.href);
if(state.tab)url.searchParams.set("ucc_tab",state.tab);
if(state.localTab)url.searchParams.set("ucc_subpage",state.localTab);
Object.entries(state.filters).forEach(([key,value])=>{if(value)url.searchParams.set("ucc_"+key,value);else url.searchParams.delete("ucc_"+key)});
const value=url.toString();
const copy=navigator.clipboard?.writeText?navigator.clipboard.writeText(value):Promise.reject();
copy.then(()=>notify("Filtered link copied.","green")).catch(()=>{
const input=document.createElement("textarea");input.value=value;document.body.appendChild(input);input.select();document.execCommand("copy");input.remove();notify("Filtered link copied.","green")
});
}
root.addEventListener("click",event=>{
const action=event.target.closest("[data-universal-action]")?.dataset.universalAction;
if(action==="export-table")exportCurrentTable();
if(action==="export-exceptions")exportExceptions();
if(action==="copy-link")copyFilteredLink();
if(event.target.closest("[data-tab],[data-local-tab],[data-ucc-workspace]"))setTimeout(saveState,20);
});
root.addEventListener("change",event=>{if(event.target.matches("[data-filter],select,input"))saveState()});
function restoreState(){
let stored={};
try{stored=JSON.parse(localStorage.getItem(STORAGE_KEY)||"{}")}catch{}
const url=new URL(location.href);
const tab=url.searchParams.get("ucc_tab")||stored.tab;
const localTab=url.searchParams.get("ucc_subpage")||stored.localTab;
const workspace=stored.workspace;
if(workspace)$(`[data-ucc-workspace="${CSS.escape(workspace)}"]`)?.click();
if(tab)$(`[data-tab="${CSS.escape(tab)}"]`)?.click();
setTimeout(()=>{if(localTab)$(`[data-local-tab="${CSS.escape(localTab)}"]`)?.click()},80);
$$("[data-filter]").forEach(el=>{
const value=url.searchParams.get("ucc_"+el.dataset.filter)??stored.filters?.[el.dataset.filter];
if(value!==undefined&&value!==null&&Array.from(el.options||[]).some(o=>o.value===value))el.value=value;
});
}
function ensureChartToggles(){
$$("[data-chart]").forEach(chart=>{
const panel=chart.closest(".panel");if(!panel)return;
chart.classList.add("ucc-clickable-result");
const key=chart.dataset.chart;
if(panel.querySelector("[data-card-toggle]"))return;
const table=$(`[data-table="${CSS.escape(key)}"]`)?.closest(".table-wrap");
if(!table)return;
const head=$(".panel-head",panel)||$("h2",panel)?.parentElement;
if(!head||$(`[data-auto-toggle="${CSS.escape(key)}"]`,panel))return;
const wrap=document.createElement("div");
wrap.className="mini-toggle";wrap.dataset.autoToggle=key;
wrap.innerHTML='<button type="button" class="active" data-auto-view="diagram">Diagram</button><button type="button" data-auto-view="table">Table</button>';
head.appendChild(wrap);
table.classList.add("ucc-hidden");
wrap.addEventListener("click",event=>{
const button=event.target.closest("[data-auto-view]");if(!button)return;
$$("button",wrap).forEach(x=>x.classList.toggle("active",x===button));
chart.classList.toggle("ucc-hidden",button.dataset.autoView==="table");
table.classList.toggle("ucc-hidden",button.dataset.autoView==="diagram");
});
});
}
function classifyEmptyStates(){
$$("[data-table] tr td:only-child,.empty-state,.source-empty").forEach(node=>{
const text=node.textContent.toLowerCase();
let type="no-data",title="No matching data";
if(/permission|not permitted|403/.test(text)){type="permission";title="Permission denied"}
else if(/unavailable|missing doctype|source not/.test(text)){type="unavailable";title="Source unavailable"}
else if(/unsupported|missing field|unknown column/.test(text)){type="unsupported";title="Unsupported or missing fields"}
if(node.closest(".ucc-empty-state"))return;
node.classList.add("ucc-empty-state");node.dataset.state=type;
if(!node.querySelector("strong"))node.innerHTML="<strong>"+title+"</strong>"+node.innerHTML;
});
}
function makeCountsClickable(){
$$("[data-kpi],[data-new-kpi],[data-c511-kpi],.kpis strong,.c511-kpis strong").forEach(node=>{
node.classList.add("ucc-clickable-result");node.tabIndex=0;
const activate=()=>{
const card=node.closest("article"),label=card?.querySelector("span")?.textContent||"Result";
const panel=visiblePanel(),table=panel&&$("table",panel);
if(table){table.scrollIntoView({behavior:"smooth",block:"center"});notify(label+": review the visible drill-down table.","blue")}
};
node.addEventListener("click",activate);
node.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" ")activate()});
});
}
function makeTableRowsDrillable(){
$$("tbody tr").forEach(row=>{
if(row.dataset.v110Drill==="1")return;row.dataset.v110Drill="1";
row.classList.add("ucc-clickable-result");
row.addEventListener("dblclick",()=>row.querySelector("a.open-record-link")?.click());
});
}
const observer=new MutationObserver(()=>{ensureChartToggles();classifyEmptyStates();makeCountsClickable();makeTableRowsDrillable()});
observer.observe(root,{childList:true,subtree:true});
setTimeout(()=>{restoreState();ensureChartToggles();classifyEmptyStates();makeCountsClickable();makeTableRowsDrillable()},250);
})();
(function(){
"use strict";
const platform=typeof root_element!=="undefined"
? root_element.querySelector("#uccIntelligencePlatform")
: document.querySelector("#uccIntelligencePlatform");
if(!platform)return;
const root=platform.querySelector('[data-dashboard-panel="criterion_4"]');
if(!root||root.dataset.ready==="1")return;
root.dataset.ready="1";
window.__uccMergeSourcesQuality(root,"data-c4-tab","data-c4-panel");
const $$=(selector,scope=root)=>Array.from(scope.querySelectorAll(selector));
const $=(selector,scope=root)=>scope.querySelector(selector);
const TAB_MAP={
c411:"4.1.1",c421:"4.2.1",c422:"4.2.2",c431:"4.3.1",
c441:"4.4.1",c451:"4.5.1",c461:"4.6.1"
};
const CODE_TO_TAB=Object.fromEntries(Object.entries(TAB_MAP).map(entry=>[entry[1],entry[0]]));
const API_TABS=Object.keys(TAB_MAP);
const STORAGE_KEY="ucc.c4.v130";
const EXCEPTION_IDS=new Set([
"c411-conditional","c411-late","c421-pending","c422-late",
"c431-overdue","c441-open","c441-overdue","c451-followup",
"c461-risk","c461-intervention"
]);
const state={
tab:"overview",
results:new Map(),
metrics:new Map(),
qa:[],
exceptions:[],
quality:[],
drillRows:[],
loading:false,
logs:[],
requestId:0
};
const C4_VISUALS={
c411:{
type:"funnel",
title:"Admissions control funnel",
stages:[
{label:"Counselling declarations",metric:"c411-counselling",source:"Pre Course Counselling Declaration"},
{label:"Applicant acknowledgement",metric:"c411-acknowledged",source:"Pre Course Counselling Declaration"},
{label:"PDPA consent",metric:"c411-pdpa",source:"Pre Course Counselling Declaration"},
{label:"Staff declaration complete",metric:"c411-staff-complete",source:"Pre Course Counselling Declaration"},
{label:"Approved applications",metric:"c411-complete",source:"Student Applicant"}
]
},
c421:{
type:"lifecycle",
title:"Student contract lifecycle",
stages:[
{label:"Admission approved",metric:"c421-approved",source:"Student Admission UCC"},
{label:"Contract generated",metric:"c421-generated",source:"Student Admission UCC"},
{label:"Sent, awaiting signature",metric:"c421-pending",source:"Student Admission UCC",exception:true},
{label:"Student signed",metric:"c421-signed",source:"Student Admission UCC"}
]
},
c422:{
type:"reconciliation",
title:"Fee and FPS reconciliation",
stages:[
{label:"Sales invoice linked",metric:"c422-invoiced",source:"Student Admission UCC"},
{label:"Payment received",metric:"c422-paid",source:"Payment Entry"},
{label:"FPS processed / approved",metric:"c422-fps",source:"FPS Record"},
{label:"Overdue invoice",metric:"c422-late",source:"Sales Invoice",exception:true}
]
},
c431:{
type:"decision",
title:"Course adjustment decision tree",
stages:[
{label:"All movement requests",aggregate:["c431-transfer","c431-defer","c431-withdraw"],source:"Student Log"},
{label:"Course transfer",metric:"c431-transfer",source:"Student Log"},
{label:"Course deferment",metric:"c431-defer",source:"Student Log"},
{label:"Course withdrawal",metric:"c431-withdraw",source:"Student Log"},
{label:"Beyond processing period",metric:"c431-overdue",source:"Student Log",exception:true}
]
},
c441:{
type:"radial",
title:"Refund decision and payment status",
stages:[
{label:"Open requests",metric:"c441-open",source:"Student Log",exception:true},
{label:"Approved requests",metric:"c441-eligible",source:"Student Log"},
{label:"Refund payments",metric:"c441-paid",source:"Payment Entry"},
{label:"Overdue requests",metric:"c441-overdue",source:"Student Log",exception:true}
]
},
c451:{
type:"network",
title:"Student support pathway",
stages:[
{label:"Student logs",metric:"c451-services",source:"Student Log"},
{label:"Academic support",metric:"c451-cases",source:"Intervention Issue Academic Support"},
{label:"Wellness support",metric:"c451-followup",source:"Intervention Issue Wellness Services"},
{label:"Academic integrity",metric:"c451-outcomes",source:"Intervention Issue Academic Integrity"}
]
},
c461:{
type:"ladder",
title:"Attendance intervention ladder",
stages:[
{label:"Attendance records",metric:"c461-attendance",source:"Student Attendance"},
{label:"Attendance risk",metric:"c461-risk",source:"Student Attendance",exception:true},
{label:"Warning records",metric:"c461-warning",source:"Dismissal Letters due to Attendance Requirements"},
{label:"Open interventions",metric:"c461-intervention",source:"Student Log",exception:true}
]
},
"c4-overview-flow":{"panel":"overview","type":"network","title":"Student protection control flow","stages":[{"label":"Approved applications","metric":"c411-complete","source":"Student Applicant"},{"label":"Signed contracts","metric":"c421-signed","source":"Student Admission UCC"},{"label":"Payments received","metric":"c422-paid","source":"Payment Entry"},{"label":"Support cases","metric":"c451-services","source":"Student Log"},{"label":"Attendance records","metric":"c461-attendance","source":"Student Attendance"}]},
"c4-overview-exceptions":{"panel":"overview","type":"radial","title":"Open exception profile","stages":[{"label":"Late admissions","metric":"c411-late","source":"Student Applicant","exception":true},{"label":"Unsigned contracts","metric":"c421-pending","source":"Student Admission UCC","exception":true},{"label":"Overdue invoices","metric":"c422-late","source":"Sales Invoice","exception":true},{"label":"Movement overdue","metric":"c431-overdue","source":"Student Log","exception":true},{"label":"Refund overdue","metric":"c441-overdue","source":"Student Log","exception":true},{"label":"Attendance risk","metric":"c461-risk","source":"Student Attendance","exception":true}]},
"c4-overview-readiness":{"panel":"overview","type":"ladder","title":"Student control readiness","stages":[{"label":"Counselling complete","metric":"c411-counselling","source":"Pre Course Counselling Declaration"},{"label":"Contract generated","metric":"c421-generated","source":"Student Admission UCC"},{"label":"Fee invoiced","metric":"c422-invoiced","source":"Sales Invoice"},{"label":"Refund requests","metric":"c441-open","source":"Student Log"},{"label":"Support pathways","metric":"c451-cases","source":"Student Log"},{"label":"Interventions","metric":"c461-intervention","source":"Student Log"}]},
"c411-coverage":{"panel":"c411","type":"radial","title":"Counselling and admission control coverage","stages":[{"label":"Counselling","metric":"c411-counselling","source":"Pre Course Counselling Declaration"},{"label":"Acknowledged","metric":"c411-acknowledged","source":"Pre Course Counselling Declaration"},{"label":"PDPA consent","metric":"c411-pdpa","source":"Pre Course Counselling Declaration"},{"label":"Staff complete","metric":"c411-staff-complete","source":"Pre Course Counselling Declaration"},{"label":"Approved","metric":"c411-complete","source":"Student Applicant"}]},
"c411-exceptions":{"panel":"c411","type":"ladder","title":"Admissions exception escalation","stages":[{"label":"Acknowledgement missing","metric":"c411-unacknowledged","source":"Pre Course Counselling Declaration","exception":true},{"label":"PDPA missing","metric":"c411-pdpa-missing","source":"Pre Course Counselling Declaration","exception":true},{"label":"Conditional open","metric":"c411-conditional","source":"Student Admission UCC","exception":true},{"label":"Late admission","metric":"c411-late","source":"Student Applicant","exception":true}]},
"c421-readiness":{"panel":"c421","type":"radial","title":"Student contract readiness","stages":[{"label":"Admission approved","metric":"c421-approved","source":"Student Admission UCC"},{"label":"Contract generated","metric":"c421-generated","source":"Student Admission UCC"},{"label":"Contract sent","metric":"c421-pending","source":"Student Admission UCC"},{"label":"Contract signed","metric":"c421-signed","source":"Student Admission UCC"}]},
"c421-aging":{"panel":"c421","type":"ladder","title":"Contract follow-up ladder","stages":[{"label":"Generated","metric":"c421-generated","source":"Student Admission UCC"},{"label":"Approved","metric":"c421-approved","source":"Student Admission UCC"},{"label":"Awaiting signature","metric":"c421-pending","source":"Student Admission UCC","exception":true},{"label":"Signed","metric":"c421-signed","source":"Student Admission UCC"}]},
"c422-flow":{"panel":"c422","type":"lifecycle","title":"Fee and FPS processing flow","stages":[{"label":"Invoice linked","metric":"c422-invoiced","source":"Sales Invoice"},{"label":"Payment received","metric":"c422-paid","source":"Payment Entry"},{"label":"FPS processed","metric":"c422-fps","source":"FPS Record"},{"label":"Overdue","metric":"c422-late","source":"Sales Invoice","exception":true}]},
"c422-exceptions":{"panel":"c422","type":"radial","title":"Fee-control exception profile","stages":[{"label":"Not invoiced","metric":"c422-invoiced","source":"Sales Invoice","exception":true},{"label":"Payment pending","metric":"c422-paid","source":"Payment Entry","exception":true},{"label":"FPS pending","metric":"c422-fps","source":"FPS Record","exception":true},{"label":"Invoice overdue","metric":"c422-late","source":"Sales Invoice","exception":true}]},
"c431-mix":{"panel":"c431","type":"radial","title":"Course movement request mix","stages":[{"label":"Transfer","metric":"c431-transfer","source":"Student Log"},{"label":"Deferment","metric":"c431-defer","source":"Student Log"},{"label":"Withdrawal","metric":"c431-withdraw","source":"Student Log"}]},
"c431-timing":{"panel":"c431","type":"ladder","title":"Movement processing timeliness","stages":[{"label":"Transfer","metric":"c431-transfer","source":"Student Log"},{"label":"Deferment","metric":"c431-defer","source":"Student Log"},{"label":"Withdrawal","metric":"c431-withdraw","source":"Student Log"},{"label":"Beyond period","metric":"c431-overdue","source":"Student Log","exception":true}]},
"c441-outcomes":{"panel":"c441","type":"reconciliation","title":"Refund request outcomes","stages":[{"label":"Open requests","metric":"c441-open","source":"Student Log","exception":true},{"label":"Eligible / approved","metric":"c441-eligible","source":"Student Log"},{"label":"Payments completed","metric":"c441-paid","source":"Payment Entry"},{"label":"Overdue","metric":"c441-overdue","source":"Student Log","exception":true}]},
"c441-aging":{"panel":"c441","type":"ladder","title":"Refund follow-up ladder","stages":[{"label":"Request logged","metric":"c441-open","source":"Student Log"},{"label":"Eligibility confirmed","metric":"c441-eligible","source":"Student Log"},{"label":"Payment issued","metric":"c441-paid","source":"Payment Entry"},{"label":"Overdue follow-up","metric":"c441-overdue","source":"Student Log","exception":true}]},
"c451-channels":{"panel":"c451","type":"radial","title":"Student support channel mix","stages":[{"label":"Student logs","metric":"c451-services","source":"Student Log"},{"label":"Academic support","metric":"c451-cases","source":"Intervention Issue Academic Support"},{"label":"Wellness","metric":"c451-followup","source":"Intervention Issue Wellness Services"},{"label":"Academic integrity","metric":"c451-outcomes","source":"Intervention Issue Academic Integrity"}]},
"c451-followup":{"panel":"c451","type":"lifecycle","title":"Student support follow-up flow","stages":[{"label":"Service request","metric":"c451-services","source":"Student Log"},{"label":"Case opened","metric":"c451-cases","source":"Intervention Issue Academic Support"},{"label":"Follow-up required","metric":"c451-followup","source":"Intervention Issue Wellness Services","exception":true},{"label":"Outcome recorded","metric":"c451-outcomes","source":"Student Log"}]},
"c461-risk":{"panel":"c461","type":"radial","title":"Attendance risk profile","stages":[{"label":"Attendance records","metric":"c461-attendance","source":"Student Attendance"},{"label":"At risk","metric":"c461-risk","source":"Student Attendance","exception":true},{"label":"Warning issued","metric":"c461-warning","source":"Dismissal Letters due to Attendance Requirements"},{"label":"Intervention open","metric":"c461-intervention","source":"Student Log","exception":true}]},
"c461-response":{"panel":"c461","type":"lifecycle","title":"Attendance intervention response","stages":[{"label":"Attendance captured","metric":"c461-attendance","source":"Student Attendance"},{"label":"Risk identified","metric":"c461-risk","source":"Student Attendance","exception":true},{"label":"Warning issued","metric":"c461-warning","source":"Dismissal Letters due to Attendance Requirements"},{"label":"Intervention opened","metric":"c461-intervention","source":"Student Log"}]}
};
let c4D3Promise=null;
function ensureC4D3(){
if(window.d3)return Promise.resolve(window.d3);
if(c4D3Promise)return c4D3Promise;
c4D3Promise=new Promise((resolve,reject)=>{
let script=document.querySelector('script[data-ucc-d3],script[src*="d3.v7.min.js"]');
const loaded=()=>{
if(window.d3)resolve(window.d3);
else reject(new Error("D3 loaded without exposing window.d3."));
};
const failed=()=>reject(new Error("D3 could not be loaded."));
if(script){
script.addEventListener("load",loaded,{once:true});
script.addEventListener("error",failed,{once:true});
window.setTimeout(()=>{
if(window.d3)resolve(window.d3);
},50);
return;
}
script=document.createElement("script");
script.src="https://d3js.org/d3.v7.min.js";
script.async=true;
script.dataset.uccD3="1";
script.addEventListener("load",loaded,{once:true});
script.addEventListener("error",failed,{once:true});
document.head.appendChild(script);
});
return c4D3Promise;
}
function c4DoctypeRoute(doctype){return UCCShared.doctypeRoute(doctype);}
function openC4Source(doctype){return UCCShared.openDoctype(doctype);}
function c4QaSourceCell(question){
const doctype=question?.doctype||"";
const link=doctype?`<a class="source-doctype-link ucc-qa-action" href="${escapeHtml(c4DoctypeRoute(doctype))}" target="_blank" rel="noopener noreferrer">Open ${escapeHtml(doctype)} list ↗</a>`:'<span class="source-unavailable">No readable source list</span>';
return`<div>${escapeHtml(question?.source_logic||"Live API calculation")}</div>${link}`;
}
function c4ExtendedQuestions(result,tab){
const rows=(result?.questions||[]).map(question=>({...question}));
const used=new Set(rows.map(question=>question.metric_id).filter(Boolean));
(result?.metrics||[]).forEach(metric=>{
if(!metric?.id||used.has(metric.id))return;
const available=metric.status==="available";
const count=Number(metric.record_count??metric.value??0);
rows.push({
id:"extended-"+metric.id,
criterion:metric.criterion||result?.policy?.criterion||TAB_MAP[tab]||tab,
question:`What is the current ${String(metric.label||"metric").toLowerCase()}?`,
answer:available?`${Number(metric.value||0).toLocaleString()} ${metric.unit||"record(s)"} match the current filters.`:`Unavailable: ${metric.message||metric.status||"required source or field is unavailable"}`,
source_logic:[metric.doctype,metric.field].filter(Boolean).join(" · ")||"Live API calculation",
confidence:available?"Live":"Unavailable",
status:metric.status||"unavailable",
metric_id:metric.id,
record_count:count,
doctype:metric.doctype||"",
field:metric.field||""
});
});
return rows;
}
function c4FiniteNumber(value,fallback=0){
const number=Number(value);
return Number.isFinite(number)?number:fallback;
}
function c4VisualStage(raw){
let metric=null;
let value=null;
let status="unavailable";
let doctype=raw.source||null;
let field=null;
if(raw.metric){
metric=state.metrics.get(raw.metric)||null;
if(metric){
value=metric.status==="available"?c4FiniteNumber(metric.value,0):metric.value;
status=metric.status||"unavailable";
doctype=metric.doctype||doctype;
field=metric.field||null;
}
}
if(Array.isArray(raw.aggregate)){
let total=0;
let found=false;
let available=true;
raw.aggregate.forEach(metricId=>{
const item=state.metrics.get(metricId);
if(!item)return;
found=true;
if(item.status!=="available")available=false;
if(item.value!==null&&item.value!==undefined){
total=total+c4FiniteNumber(item.value,0);
}
});
value=found?total:null;
status=found&&available?"available":found?"unsupported_field":"unavailable";
}
return {
label:raw.label,
metricId:raw.metric||null,
value,
status,
doctype,
field,
exception:raw.exception===true
};
}
function c4VisualData(tab){
const config=C4_VISUALS[tab];
if(!config)return null;
return {
type:config.type,
title:config.title,
stages:config.stages.map(c4VisualStage)
};
}
function c4VisualCount(stage){
return stage.value===null||stage.value===undefined?"—":String(stage.value);
}
function c4VisualFill(stage){
if(stage.status!=="available")return "#aeb7c8";
if(stage.exception&&c4FiniteNumber(stage.value,0)>0)return "#ce9e5d";
return "#26345b";
}
function c4VisualStroke(stage){
if(stage.status!=="available")return "#818ba0";
if(stage.exception&&c4FiniteNumber(stage.value,0)>0)return "#a9783b";
return "#1f2a49";
}
function bindC4Stage(selection,container){
selection
.attr("role","button")
.attr("tabindex",0)
.style("cursor",stage=>stage.metricId?"pointer":"default")
.on("click",function(event,stage){
if(stage.metricId)openDrilldown(stage.metricId);
})
.on("keydown",function(event,stage){
if((event.key==="Enter"||event.key===" ")&&stage.metricId){
event.preventDefault();
openDrilldown(stage.metricId);
}
})
.on("mouseenter",function(event,stage){
const tooltip=container.querySelector(".ucc-c4-chart-tooltip");
if(!tooltip)return;
tooltip.hidden=false;
tooltip.innerHTML=
`<strong>${escapeHtml(stage.label)}</strong>`
+`<span>Count: ${escapeHtml(c4VisualCount(stage))}</span>`
+`<span>Status: ${escapeHtml(statusText(stage.status))}</span>`
+`<span>Source: ${escapeHtml(stage.doctype||"Not resolved")}</span>`
+(stage.metricId?`<em>Click to view matching records</em>`:"");
})
.on("mousemove",function(event){
const tooltip=container.querySelector(".ucc-c4-chart-tooltip");
if(!tooltip)return;
const rect=container.getBoundingClientRect();
tooltip.style.left=Math.min(rect.width-230,event.clientX-rect.left+14)+"px";
tooltip.style.top=Math.max(8,event.clientY-rect.top-22)+"px";
})
.on("mouseleave",function(){
const tooltip=container.querySelector(".ucc-c4-chart-tooltip");
if(tooltip)tooltip.hidden=true;
});
}
function addC4SourceText(group,stage,x,y,anchor="middle"){
const text=group.append("text")
.attr("class","ucc-c4-d3-source")
.attr("x",x)
.attr("y",y)
.attr("text-anchor",anchor)
.text(stage.doctype||"Source not resolved");
if(stage.doctype){
text
.attr("role","link")
.attr("tabindex",0)
.on("click",function(event){
event.stopPropagation();
openC4Source(stage.doctype);
})
.on("keydown",function(event){
if(event.key==="Enter"||event.key===" "){
event.preventDefault();
event.stopPropagation();
openC4Source(stage.doctype);
}
});
}
}
function prepareC4Svg(container,height){
container.innerHTML='<div class="ucc-c4-chart-tooltip" hidden></div>';
const width=Math.max(container.clientWidth||720,360);
return {
width,
height,
svg:d3.select(container)
.append("svg")
.attr("class","ucc-c4-d3-svg")
.attr("viewBox",`0 0 ${width} ${height}`)
.attr("preserveAspectRatio","xMidYMid meet")
};
}
function renderC4Funnel(container,stages){
const rowHeight=70;
const height=stages.length*rowHeight+36;
const chart=prepareC4Svg(container,height);
const width=chart.width;
const maxValue=d3.max(stages,stage=>c4FiniteNumber(stage.value,0))||1;
const minWidth=Math.min(250,width*.42);
const maxWidth=Math.min(610,width-64);
const center=width/2;
const groups=chart.svg.selectAll("g.ucc-c4-funnel-stage")
.data(stages)
.join("g")
.attr("class","ucc-c4-funnel-stage");
bindC4Stage(groups,container);
groups.each(function(stage,index){
const group=d3.select(this);
const ratio=stage.status==="available"
?Math.max(.28,c4FiniteNumber(stage.value,0)/maxValue)
:.42;
const topWidth=minWidth+(maxWidth-minWidth)*ratio;
const next=stages[index+1];
const nextRatio=next&&next.status==="available"
?Math.max(.28,c4FiniteNumber(next.value,0)/maxValue)
:Math.max(.24,ratio-.08);
const bottomWidth=minWidth+(maxWidth-minWidth)*nextRatio;
const y=18+index*rowHeight;
const points=[
[center-topWidth/2,y],
[center+topWidth/2,y],
[center+bottomWidth/2,y+54],
[center-bottomWidth/2,y+54]
];
group.append("path")
.attr("d","M"+points.map(point=>point.join(",")).join("L")+"Z")
.attr("fill",c4VisualFill(stage))
.attr("stroke",c4VisualStroke(stage))
.attr("stroke-width",1.5);
group.append("text")
.attr("class","ucc-c4-d3-label is-inverse")
.attr("x",center)
.attr("y",y+24)
.attr("text-anchor","middle")
.text(stage.label);
group.append("text")
.attr("class","ucc-c4-d3-value is-inverse")
.attr("x",center)
.attr("y",y+43)
.attr("text-anchor","middle")
.text(c4VisualCount(stage));
addC4SourceText(group,stage,center+topWidth/2+10,y+31,"start");
});
}
function renderC4Lifecycle(container,stages){
const chart=prepareC4Svg(container,300);
const width=chart.width;
const x=d3.scalePoint()
.domain(d3.range(stages.length))
.range([72,width-72])
.padding(.25);
const y=126;
chart.svg.append("path")
.attr("class","ucc-c4-d3-connector")
.attr("d",d3.line().curve(d3.curveMonotoneX)(
stages.map((stage,index)=>[x(index),y])
));
const groups=chart.svg.selectAll("g.ucc-c4-life-node")
.data(stages)
.join("g")
.attr("class","ucc-c4-life-node")
.attr("transform",(stage,index)=>`translate(${x(index)},${y})`);
bindC4Stage(groups,container);
groups.append("circle")
.attr("r",stage=>26+Math.min(12,Math.sqrt(c4FiniteNumber(stage.value,0))*1.4))
.attr("fill",c4VisualFill)
.attr("stroke",c4VisualStroke)
.attr("stroke-width",3);
groups.append("text")
.attr("class","ucc-c4-d3-value is-inverse")
.attr("text-anchor","middle")
.attr("dy","0.35em")
.text(c4VisualCount);
groups.append("text")
.attr("class","ucc-c4-d3-label")
.attr("text-anchor","middle")
.attr("y",(stage,index)=>index%2===0?-60:66)
.each(function(stage){
const words=stage.label.split(/\s+/);
const text=d3.select(this);
const midpoint=Math.ceil(words.length/2);
text.append("tspan").attr("x",0).text(words.slice(0,midpoint).join(" "));
if(words.length>midpoint){
text.append("tspan").attr("x",0).attr("dy",15)
.text(words.slice(midpoint).join(" "));
}
});
groups.each(function(stage,index){
addC4SourceText(
d3.select(this),
stage,
0,
index%2===0?-91:96,
"middle"
);
});
}
function renderC4Reconciliation(container,stages){
const chart=prepareC4Svg(container,350);
const width=chart.width;
const positions=[
{x:width*.18,y:95},
{x:width*.50,y:95},
{x:width*.82,y:95},
{x:width*.50,y:265}
];
const links=[[0,1],[1,2],[0,3]];
chart.svg.selectAll("path.ucc-c4-reconcile-link")
.data(links)
.join("path")
.attr("class","ucc-c4-reconcile-link")
.attr("d",link=>{
const source=positions[link[0]];
const target=positions[link[1]];
const mid=(source.x+target.x)/2;
return `M${source.x},${source.y} C${mid},${source.y} ${mid},${target.y} ${target.x},${target.y}`;
});
const groups=chart.svg.selectAll("g.ucc-c4-reconcile-node")
.data(stages)
.join("g")
.attr("class","ucc-c4-reconcile-node")
.attr("transform",(stage,index)=>`translate(${positions[index].x},${positions[index].y})`);
bindC4Stage(groups,container);
groups.append("rect")
.attr("x",-92)
.attr("y",-42)
.attr("width",184)
.attr("height",84)
.attr("rx",18)
.attr("fill",c4VisualFill)
.attr("stroke",c4VisualStroke)
.attr("stroke-width",2);
groups.append("text")
.attr("class","ucc-c4-d3-label is-inverse")
.attr("text-anchor","middle")
.attr("y",-8)
.text(stage=>stage.label);
groups.append("text")
.attr("class","ucc-c4-d3-value is-inverse")
.attr("text-anchor","middle")
.attr("y",20)
.text(c4VisualCount);
groups.each(function(stage){
addC4SourceText(d3.select(this),stage,0,65,"middle");
});
}
function renderC4Decision(container,stages){
const chart=prepareC4Svg(container,410);
const width=chart.width;
const rootData={
stage:stages[0],
children:[
{stage:stages[1]},
{stage:stages[2],children:[{stage:stages[4]}]},
{stage:stages[3]}
]
};
const hierarchy=d3.hierarchy(rootData);
d3.tree().size([width-130,285])(hierarchy);
chart.svg.selectAll("path.ucc-c4-tree-link")
.data(hierarchy.links())
.join("path")
.attr("class","ucc-c4-tree-link")
.attr("d",d3.linkVertical()
.x(link=>link.x+65)
.y(link=>link.y+42));
const groups=chart.svg.selectAll("g.ucc-c4-tree-node")
.data(hierarchy.descendants())
.join("g")
.attr("class","ucc-c4-tree-node")
.attr("transform",node=>`translate(${node.x+65},${node.y+42})`);
groups.each(function(node){
const stage=node.data.stage;
const group=d3.select(this);
bindC4Stage(group,container);
group.append("rect")
.attr("x",-75)
.attr("y",-28)
.attr("width",150)
.attr("height",56)
.attr("rx",15)
.attr("fill",c4VisualFill(stage))
.attr("stroke",c4VisualStroke(stage))
.attr("stroke-width",2);
group.append("text")
.attr("class","ucc-c4-d3-label is-inverse")
.attr("text-anchor","middle")
.attr("y",-3)
.text(stage.label);
group.append("text")
.attr("class","ucc-c4-d3-value is-inverse")
.attr("text-anchor","middle")
.attr("y",18)
.text(c4VisualCount(stage));
addC4SourceText(group,stage,0,48,"middle");
});
}
function renderC4Radial(container,stages){
const chart=prepareC4Svg(container,380);
const width=chart.width;
const centerX=Math.min(width*.38,300);
const centerY=185;
const radius=Math.min(130,width*.23);
const values=stages.map(stage=>Math.max(1,c4FiniteNumber(stage.value,0)));
const pie=d3.pie().sort(null).value((stage,index)=>values[index])(stages);
const arc=d3.arc().innerRadius(radius*.47).outerRadius(radius);
const groups=chart.svg.append("g")
.attr("transform",`translate(${centerX},${centerY})`)
.selectAll("g.ucc-c4-radial-stage")
.data(pie)
.join("g")
.attr("class","ucc-c4-radial-stage");
bindC4Stage(groups.datum(segment=>segment.data),container);
groups.append("path")
.attr("d",segment=>arc(segment))
.attr("fill",segment=>c4VisualFill(segment.data))
.attr("stroke","#fff")
.attr("stroke-width",3);
groups.append("text")
.attr("class","ucc-c4-d3-value is-inverse")
.attr("transform",segment=>`translate(${arc.centroid(segment)})`)
.attr("text-anchor","middle")
.text(segment=>c4VisualCount(segment.data));
const total=d3.sum(stages,stage=>c4FiniteNumber(stage.value,0));
chart.svg.append("text")
.attr("class","ucc-c4-radial-total")
.attr("x",centerX)
.attr("y",centerY-6)
.attr("text-anchor","middle")
.text(total);
chart.svg.append("text")
.attr("class","ucc-c4-d3-source")
.attr("x",centerX)
.attr("y",centerY+16)
.attr("text-anchor","middle")
.text("tracked events");
const legend=chart.svg.selectAll("g.ucc-c4-radial-legend")
.data(stages)
.join("g")
.attr("class","ucc-c4-radial-legend")
.attr("transform",(stage,index)=>`translate(${Math.max(centerX+radius+45,width*.62)},${78+index*66})`);
bindC4Stage(legend,container);
legend.append("rect")
.attr("x",0)
.attr("y",-17)
.attr("width",15)
.attr("height",15)
.attr("rx",4)
.attr("fill",c4VisualFill);
legend.append("text")
.attr("class","ucc-c4-d3-label")
.attr("x",25)
.attr("y",-4)
.text(stage=>`${stage.label}: ${c4VisualCount(stage)}`);
legend.each(function(stage){
addC4SourceText(d3.select(this),stage,25,17,"start");
});
}
function renderC4Network(container,stages){
const chart=prepareC4Svg(container,370);
const width=chart.width;
const rootStage=stages[0];
const childStages=stages.slice(1);
const rootPosition={x:width*.24,y:185};
const childPositions=childStages.map((stage,index)=>({
x:width*.74,
y:80+index*105
}));
const maxValue=d3.max(childStages,stage=>c4FiniteNumber(stage.value,0))||1;
chart.svg.selectAll("path.ucc-c4-network-link")
.data(childStages)
.join("path")
.attr("class","ucc-c4-network-link")
.attr("stroke-width",stage=>4+18*(c4FiniteNumber(stage.value,0)/maxValue))
.attr("d",(stage,index)=>{
const target=childPositions[index];
const mid=(rootPosition.x+target.x)/2;
return `M${rootPosition.x+80},${rootPosition.y} C${mid},${rootPosition.y} ${mid},${target.y} ${target.x-80},${target.y}`;
});
const allStages=[rootStage].concat(childStages);
const allPositions=[rootPosition].concat(childPositions);
const groups=chart.svg.selectAll("g.ucc-c4-network-node")
.data(allStages)
.join("g")
.attr("class","ucc-c4-network-node")
.attr("transform",(stage,index)=>`translate(${allPositions[index].x},${allPositions[index].y})`);
bindC4Stage(groups,container);
groups.append("rect")
.attr("x",-88)
.attr("y",-35)
.attr("width",176)
.attr("height",70)
.attr("rx",18)
.attr("fill",c4VisualFill)
.attr("stroke",c4VisualStroke)
.attr("stroke-width",2);
groups.append("text")
.attr("class","ucc-c4-d3-label is-inverse")
.attr("text-anchor","middle")
.attr("y",-5)
.text(stage=>stage.label);
groups.append("text")
.attr("class","ucc-c4-d3-value is-inverse")
.attr("text-anchor","middle")
.attr("y",19)
.text(c4VisualCount);
groups.each(function(stage){
addC4SourceText(d3.select(this),stage,0,55,"middle");
});
}
function renderC4Ladder(container,stages){
const chart=prepareC4Svg(container,370);
const width=chart.width;
const margin=55;
const available=width-margin*2;
const stepWidth=available/stages.length;
chart.svg.append("path")
.attr("class","ucc-c4-ladder-line")
.attr("d",d3.line().curve(d3.curveStepAfter)(
stages.map((stage,index)=>[
margin+index*stepWidth+stepWidth*.5,
285-index*58
])
));
const groups=chart.svg.selectAll("g.ucc-c4-ladder-stage")
.data(stages)
.join("g")
.attr("class","ucc-c4-ladder-stage")
.attr("transform",(stage,index)=>`translate(${margin+index*stepWidth},${270-index*58})`);
bindC4Stage(groups,container);
groups.append("rect")
.attr("x",3)
.attr("y",-35)
.attr("width",Math.max(100,stepWidth-10))
.attr("height",70)
.attr("rx",14)
.attr("fill",c4VisualFill)
.attr("stroke",c4VisualStroke)
.attr("stroke-width",2);
groups.append("text")
.attr("class","ucc-c4-d3-label is-inverse")
.attr("x",stepWidth*.5)
.attr("y",-5)
.attr("text-anchor","middle")
.text(stage=>stage.label);
groups.append("text")
.attr("class","ucc-c4-d3-value is-inverse")
.attr("x",stepWidth*.5)
.attr("y",20)
.attr("text-anchor","middle")
.text(c4VisualCount);
groups.each(function(stage){
addC4SourceText(
d3.select(this),
stage,
stepWidth*.5,
56,
"middle"
);
});
}
function renderC4VisualTable(tab,data){
const tbody=$(`[data-c4-visual-table="${CSS.escape(tab)}"]`);
if(!tbody)return;
tbody.innerHTML=data.stages.map(stage=>{
const drill=stage.metricId&&stage.status==="available"
?`<button type="button" class="record-link" data-c4-visual-drill="${escapeHtml(stage.metricId)}">View ${escapeHtml(c4VisualCount(stage))} record(s) ↗</button>`
:'<span class="ucc-c4-visual-muted">No record drill-down</span>';
const source=stage.doctype
?`<a class="source-doctype-link" href="${escapeHtml(c4DoctypeRoute(stage.doctype))}" target="_blank" rel="noopener noreferrer">Open ${escapeHtml(stage.doctype)} list ↗</a>`
:'<span class="ucc-c4-visual-muted">Source not resolved</span>';
return `<tr>
        <td><strong>${escapeHtml(stage.label)}</strong></td>
        <td>${escapeHtml(c4VisualCount(stage))}</td>
        <td><span class="ucc-c4-status-pill" data-status="${escapeHtml(stage.status)}">${escapeHtml(statusText(stage.status))}</span></td>
        <td>${source}</td>
        <td>${drill}</td>
      </tr>`;
}).join("");
$$("[data-c4-visual-drill]",tbody).forEach(button=>{
button.addEventListener("click",()=>{
openDrilldown(button.dataset.c4VisualDrill);
});
});
}
function drawC4Visual(tab,data){
const container=$(`[data-c4-visual="${CSS.escape(tab)}"]`);
if(!container)return;
const renderers={
funnel:renderC4Funnel,
lifecycle:renderC4Lifecycle,
reconciliation:renderC4Reconciliation,
decision:renderC4Decision,
radial:renderC4Radial,
network:renderC4Network,
ladder:renderC4Ladder
};
const renderer=renderers[data.type];
if(!renderer){
container.innerHTML='<div class="empty-state">No diagram renderer is configured.</div>';
return;
}
renderer(container,data.stages);
container.dataset.visualType=data.type;
}
function renderC4Visual(keyOrPanel){
const direct=C4_VISUALS[keyOrPanel];
const keys=direct&&direct.panel&&direct.panel!==keyOrPanel?[keyOrPanel]:Object.keys(C4_VISUALS).filter(key=>(C4_VISUALS[key].panel||key)===keyOrPanel);
if(!keys.length&&direct)keys.push(keyOrPanel);
keys.forEach(key=>{
const data=c4VisualData(key);
if(!data)return;
renderC4VisualTable(key,data);
const container=$(`[data-c4-visual="${CSS.escape(key)}"]`);
if(!container)return;
container.innerHTML='<div class="ucc-c4-visual-loading">Preparing live diagram…</div>';
ensureC4D3().then(()=>drawC4Visual(key,data)).catch(error=>{container.innerHTML=`<div class="empty-state">Diagram unavailable: ${escapeHtml(error.message||String(error))}. Use the Table view for the same data.</div>`;});
});
}
function escapeHtml(value){
return String(value??"").replace(/[&<>"']/g,char=>({
"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
}[char]));
}
function notify(message,indicator="blue"){
if(window.frappe&&frappe.show_alert)frappe.show_alert({message,indicator});
}
function addLog(level,event,detail){
const row={
time:new Date().toISOString(),
level:String(level||"INFO"),
event:String(event||"event"),
detail:typeof detail==="string"?detail:JSON.stringify(detail||{})
};
state.logs.push(row);
if(state.logs.length>5000)state.logs.splice(0,state.logs.length-5000);
const count=$("[data-c4-log-count]");
if(count)count.textContent=String(state.logs.length);
renderDiagnostics();
return row;
}
function statusText(status){
return {
available:"Available",
unavailable:"Source unavailable",
permission_denied:"Permission denied",
unsupported_field:"Unsupported or missing field",
error:"Runtime error",
loading:"Loading"
}[status]||status||"Unknown";
}
function filters(){
const output={};
$$("[data-c4-filter]").forEach(element=>{
output[element.dataset.c4Filter]=element.value||"";
});
return output;
}
function callApi(subcriterion,action="summary",extra={}){
return new Promise((resolve,reject)=>{
if(!(window.frappe&&frappe.call)){
reject(new Error("Frappe API client is unavailable."));
return;
}
const payload={
action,
subcriterion,
filters:filters(),
page_size:100
};
Object.keys(extra||{}).forEach(key=>payload[key]=extra[key]);
addLog("INFO","api_request",{subcriterion,action});
frappe.call({
method:"ucc_analytics_criterion_4",
args:{payload:JSON.stringify(payload)},
callback(response){
const message=response&&response.message;
if(message&&message.ok){
addLog("INFO","api_success",{
subcriterion,
action,
sources:(message.sources||[]).length,
metrics:(message.metrics||[]).length
});
resolve(message);
}else{
const errorMessage=message&&message.message||"Criterion 4 request failed.";
addLog("ERROR","api_failure",{subcriterion,action,message:errorMessage});
reject(new Error(errorMessage));
}
},
error(error){
const errorMessage=error&&error.message||"Criterion 4 request failed.";
addLog("ERROR","api_error",{subcriterion,action,message:errorMessage});
reject(error instanceof Error?error:new Error(errorMessage));
}
});
});
}
function setLoading(active,progress=0,task="Preparing…"){
const overlay=$("[data-c4-loading-overlay]");
if(overlay)overlay.classList.toggle("hidden",!active);
const fill=$("[data-c4-progress-fill]");
const value=$("[data-c4-progress-value]");
const taskNode=$("[data-c4-progress-task]");
if(fill)fill.style.width=Math.max(0,Math.min(100,progress))+"%";
if(value)value.textContent=Math.round(progress)+"%";
if(taskNode)taskNode.textContent=task;
}
function setNotice(message,status="available"){
const notice=$("[data-c4-source-notice]");
if(!notice)return;
if(notice.dataset.dismissed==="1"&&status==="available")return;
if(status!=="available")notice.dataset.dismissed="0";
notice.hidden=false;
notice.dataset.status=status;
const strong=$("strong",notice);
const span=$("span",notice);
if(strong){
strong.textContent=status==="available"
?"Criterion 4 live analytics active."
:"Criterion 4 live analytics active with limitations.";
}
if(span)span.textContent=message;
}
function sourceDetail(item){
if(item.message)return item.message;
if(Array.isArray(item.errors)&&item.errors.length){
return item.errors.map(error=>error&&error.message).filter(Boolean).join(" | ");
}
return statusText(item.status);
}
function renderMetricCards(result,tab){
(result.metrics||[]).forEach(metric=>{
const contextualMetric=Object.assign({},metric,{criterion:TAB_MAP[tab]});
state.metrics.set(metric.id,contextualMetric);
const card=root.querySelector(`[data-c4-drill="${CSS.escape(metric.id)}"]`);
if(!card)return;
const value=$("strong",card);
const detail=$("small",card);
card.dataset.mappingStatus=metric.status||"unknown";
if(value)value.textContent=metric.value===null||metric.value===undefined?"—":String(metric.value);
if(detail){
detail.textContent=metric.status==="available"
? [metric.doctype,metric.field].filter(Boolean).join(" · ")
: statusText(metric.status);
}
card.title=metric.status==="available"
? `Click to view ${metric.value||0} matching records`
: statusText(metric.status);
});
}
function renderQuestionRows(tab,result){
const tbody=$(`[data-c4-qa-table="${CSS.escape(tab)}"]`);
if(!tbody)return;
const questions=c4ExtendedQuestions(result,tab);
tbody.innerHTML=questions.map(question=>{
const count=Number(question.record_count||0);
const drill=question.metric_id&&question.status==="available"
?`<button type="button" class="record-link ucc-qa-action" data-c4-question-drill="${escapeHtml(question.metric_id)}">View ${count} matching record${count===1?"":"s"} ↗</button>`
:"";
return `
      <tr>
        <td>${escapeHtml(question.criterion||result.policy?.criterion||tab)}</td>
        <td>${escapeHtml(question.question)}</td>
        <td><div>${escapeHtml(question.answer)}</div>${drill}</td>
        <td>${c4QaSourceCell(question)}</td>
        <td><span class="ucc-c4-status-pill" data-status="${escapeHtml(question.status)}">${escapeHtml(question.confidence)}</span></td>
      </tr>`;
}).join("")||'<tr><td colspan="5">No management questions are configured.</td></tr>';
$$("[data-c4-question-drill]",tbody).forEach(button=>{
button.addEventListener("click",()=>openDrilldown(button.dataset.c4QuestionDrill));
});
}
function renderSourceRows(tab,result){
const tbody=$(`[data-c4-source-table="${CSS.escape(tab)}"]`);
if(!tbody)return;
tbody.innerHTML=(result.sources||[]).map(source=>`
      <tr>
        <td>${escapeHtml(source.key)}</td>
        <td>${source.doctype
          ?`<a class="source-doctype-link" href="${escapeHtml(c4DoctypeRoute(source.doctype))}" target="_blank" rel="noopener noreferrer">Open ${escapeHtml(source.doctype)} list ↗</a>`
          :escapeHtml((source.candidates||[]).join(" / "))}</td>
        <td><span class="ucc-c4-status-pill" data-status="${escapeHtml(source.status)}">${escapeHtml(statusText(source.status))}</span></td>
        <td>${escapeHtml(sourceDetail(source))}</td>
      </tr>
    `).join("")||'<tr><td colspan="4">No source registry rows were returned.</td></tr>';
}
function renderExceptionRows(tab,result){
const panel=$(`[data-c4-panel="${CSS.escape(tab)}"]`);
if(!panel)return;
$$("[data-c4-exception-row]",panel).forEach(row=>{
const metric=state.metrics.get(row.dataset.c4ExceptionRow);
const value=$("[data-c4-exception-value]",row);
const status=$("[data-c4-exception-status]",row);
if(!metric){
if(value)value.textContent="—";
if(status)status.textContent="No mapping";
return;
}
if(value)value.textContent=metric.value===null||metric.value===undefined?"—":String(metric.value);
if(status)status.textContent=statusText(metric.status);
row.dataset.status=metric.status||"unknown";
});
}

const C4_VISUAL_EXPANSION={"c411":[{"id":"v190-c4-c411-01","title":"Admission and Counselling Funnel","type":"bar","description":"Tracks applicants from counselling through to a completed admission decision.","i":0},{"id":"v190-c4-c411-02","title":"Counselling Evidence Coverage","type":"donut","description":"Shows what share of counselling sessions have documented supporting evidence.","i":1},{"id":"v190-c4-c411-03","title":"Application Status Distribution","type":"funnel","description":"Compares how applications are distributed across each status stage.","i":2},{"id":"v190-c4-c411-07","title":"PDPA and Consent Coverage","type":"gauge","description":"Gauges what share of admissions have completed PDPA and consent capture.","i":6},{"id":"v190-c4-c411-10","title":"Counselling Source Readiness","type":"donut","description":"Tracks how readable the underlying counselling data sources currently are.","i":9}],"c421":[{"id":"v190-c4-c421-01","title":"Student Contract Lifecycle","type":"bar","description":"Maps a student contract from drafted through signature to activation.","i":0},{"id":"v190-c4-c421-02","title":"Contract Signature Coverage","type":"donut","description":"Gauges what share of student contracts have a completed signature.","i":1},{"id":"v190-c4-c421-05","title":"Contract Evidence Completeness","type":"radar","description":"Compares how complete supporting contract evidence is across students.","i":4},{"id":"v190-c4-c421-10","title":"Contract Source Readiness","type":"donut","description":"Tracks how readable the underlying student contract data sources are.","i":9}],"c422":[{"id":"v190-c4-c422-01","title":"Fee Collection Profile","type":"bar","description":"Compares fee collection results across the areas measured.","i":0},{"id":"v190-c4-c422-02","title":"Fee Protection Coverage","type":"donut","description":"Shows what share of student fees have fee protection scheme coverage.","i":1},{"id":"v190-c4-c422-03","title":"Invoice and Payment Status","type":"funnel","description":"Compares how invoices and payments are distributed across status.","i":2},{"id":"v190-c4-c422-07","title":"FPS Status Distribution","type":"gauge","description":"Shows how FPS coverage is distributed across enrolled students.","i":6},{"id":"v190-c4-c422-10","title":"Fee Source Readiness","type":"donut","description":"Tracks how readable the underlying fee data sources currently are.","i":9}],"c431":[{"id":"v190-c4-c431-01","title":"Movement Request Lifecycle","type":"bar","description":"Maps a student movement request from submitted through to actioned.","i":0},{"id":"v190-c4-c431-02","title":"Transfer Request Status","type":"donut","description":"Compares transfer requests across the different status stages.","i":1},{"id":"v190-c4-c431-07","title":"Approval Coverage","type":"gauge","description":"Gauges what share of movement requests have completed approval.","i":6},{"id":"v190-c4-c431-10","title":"Movement Source Readiness","type":"donut","description":"Tracks how readable the underlying movement request data sources are.","i":9}],"c441":[{"id":"v190-c4-c441-01","title":"Refund Request Lifecycle","type":"bar","description":"Maps a refund request from submitted through to disbursed.","i":0},{"id":"v190-c4-c441-02","title":"Refund Status Distribution","type":"donut","description":"Compares refund requests across their current status.","i":1},{"id":"v190-c4-c441-05","title":"Refund Completion Coverage","type":"radar","description":"Gauges what share of eligible refunds have been completed.","i":4},{"id":"v190-c4-c441-10","title":"Refund Source Readiness","type":"donut","description":"Tracks how readable the underlying refund data sources currently are.","i":9}],"c451":[{"id":"v190-c4-c451-01","title":"Support Service Demand","type":"bar","description":"Compares demand for student support services across categories.","i":0},{"id":"v190-c4-c451-02","title":"Support Case Status","type":"donut","description":"Shows the current status mix of student support cases.","i":1},{"id":"v190-c4-c451-07","title":"Support Outcome Coverage","type":"gauge","description":"Gauges what share of support cases reached a positive outcome.","i":6},{"id":"v190-c4-c451-10","title":"Support Source Readiness","type":"donut","description":"Tracks how readable the underlying student support data sources are.","i":9}],"c461":[{"id":"v190-c4-c461-01","title":"Attendance Status Distribution","type":"bar","description":"Compares student attendance records across each status category.","i":0},{"id":"v190-c4-c461-03","title":"Warning and Intervention Funnel","type":"funnel","description":"Tracks students from a warning issued through to intervention taken.","i":2},{"id":"v190-c4-c461-07","title":"Intervention Completion","type":"gauge","description":"Gauges what share of required interventions have been completed.","i":6},{"id":"v190-c4-c461-10","title":"Conduct Source Readiness","type":"donut","description":"Tracks how readable the underlying conduct data sources currently are.","i":9}]};
window.UCCC4VisualDefinitions=C4_VISUAL_EXPANSION
function c4ExpandedRows(result,index){
const available=(result.metrics||[]).filter(metric=>metric.status==="available");
if(!available.length){
const sourceSummary=result.source_summary||{};
const metricSummary=result.metric_summary||{};
return[
{label:"Available sources",value:Number(sourceSummary.available||0),metric:null},
{label:"Source issues",value:Number(sourceSummary.issues||0),metric:null},
{label:"Available metrics",value:Number(metricSummary.available||0),metric:null},
{label:"Metric issues",value:Number(metricSummary.issues||0),metric:null}
];
}
const size=Math.min(5,available.length);
const start=(index*size)%available.length;
const rows=[];
for(let offset=0;offset<size;offset+=1){
const metric=available[(start+offset)%available.length];
rows.push({label:metric.label,value:c4FiniteNumber(metric.value,0),metric});
}
return rows;
}
function c4ExpandedChartMarkup(chart){
return`<article class="panel ucc-c4-expanded-card" data-c4-expanded-card="${escapeHtml(chart.id)}">
<div class="panel-head">
<h2>${escapeHtml(chart.title)}<span class="ucc-card-desc-inline"> — ${escapeHtml(chart.description||"Live Criterion 4 API metrics.")}</span></h2>
<div class="mini-toggle">
<button type="button" class="active" data-c4-expanded-view="diagram">Diagram</button>
<button type="button" data-c4-expanded-view="table">Table</button>
</div>
</div>
<div class="chart ucc-c4-expanded-chart" data-c4-expanded-chart="${escapeHtml(chart.id)}"></div>
<div class="table-wrap hidden" data-c4-expanded-table="${escapeHtml(chart.id)}">
<table><thead><tr><th>Measure</th><th>Live value</th><th>Source / Calculation</th><th>Records</th></tr></thead><tbody></tbody></table>
</div>
</article>`;
}
function c4ExpandedPairs(rows){return rows.map(row=>[row.label,Number.isFinite(row.value)?row.value:0]);}
function c4ExpandedRenderBars(node,rows){
const pairs=c4ExpandedPairs(rows),max=Math.max(...pairs.map(row=>row[1]),1);
node.innerHTML=`<div class="ucc-demo-bars">${pairs.map(row=>`<div class="ucc-demo-bar"><label>${escapeHtml(row[0])}</label><div><i style="width:${Math.max(4,row[1]/max*100)}%"></i></div><strong>${escapeHtml(row[1])}</strong></div>`).join("")}</div>`;
}
function c4ExpandedRenderDonut(node,rows){
const pairs=c4ExpandedPairs(rows),total=pairs.reduce((sum,row)=>sum+row[1],0)||1;
let cursor=0;
const stops=pairs.map((row,index)=>{const start=cursor/total*360;cursor+=row[1];const end=cursor/total*360;return`var(--ucc-chart-${index%6}) ${start}deg ${end}deg`;}).join(",");
node.innerHTML=`<div class="ucc-demo-donut-layout"><div class="ucc-demo-donut" style="background:conic-gradient(${stops})"><span>${escapeHtml(total)}</span><small>Total</small></div><div class="ucc-demo-legend">${pairs.map((row,index)=>`<div><i style="background:var(--ucc-chart-${index%6})"></i><span>${escapeHtml(row[0])}</span><strong>${escapeHtml(row[1])}</strong></div>`).join("")}</div></div>`;
}
function c4ExpandedRenderFunnel(node,rows){
const pairs=c4ExpandedPairs(rows),max=Math.max(...pairs.map(row=>row[1]),1);
node.innerHTML=`<div class="ucc-demo-funnel">${pairs.map(row=>`<div class="ucc-demo-funnel-stage" style="width:${Math.max(38,row[1]/max*100)}%"><span>${escapeHtml(row[0])}</span><strong>${escapeHtml(row[1])}</strong></div>`).join("")}</div>`;
}
function c4ExpandedRenderLifecycle(node,rows){
node.innerHTML=`<div class="ucc-demo-lifecycle">${rows.map((row,index)=>`<div class="ucc-demo-life-step"><i>${index+1}</i><span>${escapeHtml(row.label)}</span><strong>${escapeHtml(row.value)}</strong></div>${index<rows.length-1?'<b aria-hidden="true">→</b>':""}`).join("")}</div>`;
}
function c4ExpandedRenderMatrix(node,rows){
const max=Math.max(...rows.map(row=>c4FiniteNumber(row.value,0)),1);
node.innerHTML=`<div class="ucc-demo-matrix">${rows.map(row=>`<div style="--ucc-intensity:${Math.max(.18,c4FiniteNumber(row.value,0)/max)}"><span>${escapeHtml(row.label)}</span><strong>${escapeHtml(row.value)}</strong></div>`).join("")}</div>`;
}
function c4ExpandedRenderGauge(node,rows){
const total=rows.reduce((sum,row)=>sum+c4FiniteNumber(row.value,0),0),value=rows.length?c4FiniteNumber(rows[0].value,0):0,pct=Math.max(0,Math.min(100,total?value/total*100:0));
node.innerHTML=`<div class="ucc-demo-gauge"><div style="--ucc-gauge:${pct}deg"><strong>${escapeHtml(value)}</strong><span>${escapeHtml(rows[0]?.label||"Live value")}</span></div></div>`;
}
function c4ExpandedRenderRadar(node,rows){
const size=320,cx=160,cy=160,radius=105,count=Math.max(rows.length,3),max=Math.max(...rows.map(row=>Number(row.value||0)),1);
const points=rows.map((row,index)=>{const angle=-Math.PI/2+index*2*Math.PI/count,r=radius*(c4FiniteNumber(row.value,0)/max);return[cx+Math.cos(angle)*r,cy+Math.sin(angle)*r];});
const axes=rows.map((row,index)=>{const angle=-Math.PI/2+index*2*Math.PI/count,x=cx+Math.cos(angle)*radius,y=cy+Math.sin(angle)*radius,lx=cx+Math.cos(angle)*(radius+28),ly=cy+Math.sin(angle)*(radius+28);return`<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}"></line><text x="${lx}" y="${ly}" text-anchor="middle">${escapeHtml(row.label)}</text>`;}).join("");
node.innerHTML=`<div class="ucc-demo-radar"><svg viewBox="0 0 ${size} ${size}"><circle cx="${cx}" cy="${cy}" r="${radius}"></circle><circle cx="${cx}" cy="${cy}" r="${radius*.66}"></circle><circle cx="${cx}" cy="${cy}" r="${radius*.33}"></circle>${axes}<polygon points="${points.map(point=>point.join(",")).join(" ")}"></polygon></svg></div>`;
}
function c4ExpandedRenderTrend(node,rows){
const width=560,height=250,pad=38,max=Math.max(...rows.map(row=>Number(row.value||0)),1),step=(width-pad*2)/Math.max(1,rows.length-1);
const points=rows.map((row,index)=>[pad+index*step,height-pad-(c4FiniteNumber(row.value,0)/max)*(height-pad*2)]);
node.innerHTML=`<div class="ucc-demo-trend"><svg viewBox="0 0 ${width} ${height}"><line class="axis" x1="${pad}" y1="${height-pad}" x2="${width-pad}" y2="${height-pad}"></line><polyline points="${points.map(point=>point.join(",")).join(" ")}"></polyline>${points.map((point,index)=>`<circle cx="${point[0]}" cy="${point[1]}" r="5"></circle><text x="${point[0]}" y="${height-10}" text-anchor="middle">${escapeHtml(rows[index].label)}</text>`).join("")}</svg></div>`;
}
function c4ExpandedRenderChart(node,type,rows){
if(!rows.length){node.innerHTML='<div class="empty-state">No readable live metric for this visual.</div>';return;}
if(type==="donut")return c4ExpandedRenderDonut(node,rows);
if(type==="funnel")return c4ExpandedRenderFunnel(node,rows);
if(type==="lifecycle")return c4ExpandedRenderLifecycle(node,rows);
if(type==="matrix")return c4ExpandedRenderMatrix(node,rows);
if(type==="gauge")return c4ExpandedRenderGauge(node,rows);
if(type==="radar")return c4ExpandedRenderRadar(node,rows);
if(type==="trend")return c4ExpandedRenderTrend(node,rows);
return c4ExpandedRenderBars(node,rows);
}
function ensureC4ExpandedVisuals(tab,result){
const definitions=C4_VISUAL_EXPANSION[tab]||[];
const panel=root.querySelector(`[data-c4-panel="${CSS.escape(tab)}"]`);
if(!panel||!definitions.length)return;
let grid=panel.querySelector(":scope > .ucc-c4-expanded-grid");
if(!grid){
grid=document.createElement("div");
grid.className="grid2 ucc-c4-expanded-grid";
const qa=Array.from(panel.children).find(child=>/Management Questions and Data-Based Answers/i.test(child.textContent||""));
panel.insertBefore(grid,qa||null);
}
definitions.map((chart,index)=>({chart,index:chart.i??index})).filter(o=>o.chart.enabled!==false).sort((a,b)=>(a.chart.title||"").localeCompare(b.chart.title||"",undefined,{sensitivity:"base"})).forEach(({chart,index})=>{
if(!grid.querySelector(`[data-c4-expanded-card="${CSS.escape(chart.id)}"]`)){
grid.insertAdjacentHTML("beforeend",c4ExpandedChartMarkup(chart));
}
const card=grid.querySelector(`[data-c4-expanded-card="${CSS.escape(chart.id)}"]`);
card._c4CardPending={chart,index,result};
card.dataset.c4CardRendered="";
card.querySelectorAll("[data-c4-expanded-view]").forEach(button=>button.onclick=()=>{
renderC4ExpandedCardNow(card);
card.querySelectorAll("[data-c4-expanded-view]").forEach(item=>item.classList.toggle("active",item===button));
card.querySelector("[data-c4-expanded-chart]").classList.toggle("hidden",button.dataset.c4ExpandedView!=="diagram");
card.querySelector("[data-c4-expanded-table]").classList.toggle("hidden",button.dataset.c4ExpandedView!=="table");
});
});
}
function renderC4ExpandedCardNow(card){
if(!card||!card._c4CardPending||card.dataset.c4CardRendered==="1")return;
const{chart,index,result}=card._c4CardPending;
const rows=c4ExpandedRows(result,index);
c4ExpandedRenderChart(card.querySelector("[data-c4-expanded-chart]"),chart.type,rows);
const tbody=card.querySelector("tbody");
tbody.innerHTML=rows.map(row=>{
const metric=row.metric;
const source=metric?.doctype?`<a class="source-doctype-link" href="${escapeHtml(c4DoctypeRoute(metric.doctype))}" target="_blank" rel="noopener noreferrer">Open ${escapeHtml(metric.doctype)} list ↗</a>`:"Live readiness calculation";
const drill=metric?.id?`<button type="button" class="record-link" data-c4-expanded-drill="${escapeHtml(metric.id)}">View ${escapeHtml(metric.record_count||metric.value||0)} matching records ↗</button>`:"—";
return`<tr><td>${escapeHtml(row.label)}</td><td>${escapeHtml(row.value)}</td><td>${source}</td><td>${drill}</td></tr>`;
}).join("");
card.querySelectorAll("[data-c4-expanded-drill]").forEach(button=>button.onclick=()=>openDrilldown(button.dataset.c4ExpandedDrill));
card.dataset.c4CardRendered="1";
}

function renderDetailed(tab,result){
renderMetricCards(result,tab);
ensureC4ExpandedVisuals(tab,result);
renderQuestionRows(tab,result);
renderSourceRows(tab,result);
renderExceptionRows(tab,result);
renderC4Visual(tab);
const sourceSummary=result.source_summary||{};
const metricSummary=result.metric_summary||{};
const policy=result.policy||{};
const issueCount=(sourceSummary.issues||0)+(metricSummary.issues||0);
setNotice(
`Live data connected · `
+`${sourceSummary.available||0} of ${sourceSummary.total||0} sources available · `
+`${metricSummary.available||0} of ${metricSummary.total||0} metrics available`
+(issueCount?` · ${issueCount} item${issueCount===1?"":"s"} need review`:""),
issueCount?"warning":"available"
);
}
async function loadTab(tab,{force=false}={}){
const code=TAB_MAP[tab];
if(!code)return null;
if(!force&&state.results.has(tab)){
const cached=state.results.get(tab);
renderDetailed(tab,cached);
return cached;
}
const result=await callApi(code,"summary");
state.results.set(tab,result);
renderDetailed(tab,result);
rebuildAggregates();
return result;
}
async function loadAll({force=false}={}){
if(state.loading)return;
state.loading=true;
const requestId=++state.requestId;
setLoading(true,2,"Preparing Criterion 4 sources");
setNotice("Loading all Criterion 4 source mappings and management answers…","loading");
try{
for(let index=0;index<API_TABS.length;index+=1){
const tab=API_TABS[index];
const code=TAB_MAP[tab];
setLoading(true,5+(index/API_TABS.length)*88,`Loading ${code}`);
if(force||!state.results.has(tab)){
const result=await callApi(code,"summary");
if(requestId!==state.requestId)return;
state.results.set(tab,result);
renderDetailed(tab,result);
}
}
rebuildAggregates();
setLoading(true,98,"Rendering management answers");
setNotice("All Criterion 4 sections loaded for the current user and filters.","available");
}catch(error){
setNotice(error.message||"Unable to load Criterion 4 analytics.","error");
notify(error.message||"Criterion 4 request failed.","red");
addLog("ERROR","load_all_failed",error.message||String(error));
}finally{
state.loading=false;
setTimeout(()=>setLoading(false,100,"Complete"),120);
}
}
function rebuildAggregates(){
state.qa=[];
state.exceptions=[];
state.quality=[];
let availableSources=0;
let totalSources=0;
let availableMetrics=0;
let totalMetrics=0;
let answeredQuestions=0;
let openExceptions=0;
const gapRows=[];
const sourceRows=[];
const qualityRows=[];
API_TABS.forEach(tab=>{
const result=state.results.get(tab);
if(!result)return;
const code=TAB_MAP[tab];
const sourceSummary=result.source_summary||{};
const metricSummary=result.metric_summary||{};
availableSources+=Number(sourceSummary.available||0);
totalSources+=Number(sourceSummary.total||0);
availableMetrics+=Number(metricSummary.available||0);
totalMetrics+=Number(metricSummary.total||0);
c4ExtendedQuestions(result,tab).forEach(question=>{
state.qa.push(question);
if(question.status==="available")answeredQuestions+=1;
});
(result.exceptions||[]).forEach(metric=>{
state.exceptions.push({...metric,criterion:code});
if(metric.status==="available")openExceptions+=Number(metric.value||0);
});
(result.data_quality||[]).forEach(item=>{
state.quality.push(item);
qualityRows.push(`
          <tr>
            <td>${escapeHtml(code)}</td>
            <td>${escapeHtml(item.check)}</td>
            <td>${escapeHtml(item.source)}</td>
            <td><span class="ucc-c4-status-pill" data-status="${escapeHtml(item.status)}">${escapeHtml(statusText(item.status))}</span></td>
            <td>${escapeHtml(item.detail)}</td>
          </tr>
        `);
});
(result.sources||[]).forEach(source=>{
sourceRows.push(`
          <tr>
            <td>${escapeHtml(code)}</td>
            <td>${escapeHtml(source.key)}</td>
            <td>${escapeHtml((source.candidates||[]).join(" / "))}</td>
            <td>${source.doctype
              ?`<a class="source-doctype-link" href="${escapeHtml(c4DoctypeRoute(source.doctype))}" target="_blank" rel="noopener noreferrer">Open ${escapeHtml(source.doctype)} list ↗</a>`
              :"—"}</td>
            <td><span class="ucc-c4-status-pill" data-status="${escapeHtml(source.status)}">${escapeHtml(statusText(source.status))}</span></td>
            <td>${escapeHtml(sourceDetail(source))}</td>
          </tr>
        `);
});
const sourcePct=sourceSummary.total?Math.round((sourceSummary.available/sourceSummary.total)*100):0;
const metricPct=metricSummary.total?Math.round((metricSummary.available/metricSummary.total)*100):0;
gapRows.push(`
        <article>
          <div><strong>${escapeHtml(code)}</strong><span>${sourceSummary.available||0}/${sourceSummary.total||0} sources · ${metricSummary.available||0}/${metricSummary.total||0} metrics</span></div>
          <div class="ucc-c4-gap-track"><i style="width:${Math.round((sourcePct+metricPct)/2)}%"></i></div>
        </article>
      `);
});
const setKpi=(name,value)=>{
const node=$(`[data-c4-overall-kpi="${name}"]`);
if(node)node.textContent=String(value);
};
setKpi("sources",`${availableSources}/${totalSources}`);
setKpi("metrics",`${availableMetrics}/${totalMetrics}`);
setKpi("questions",answeredQuestions);
setKpi("exceptions",openExceptions);
setKpi("quality",state.quality.length);
const gap=$("[data-c4-gap-summary]");
if(gap)gap.innerHTML=gapRows.join("")||'<div class="empty-state">Load Criterion 4 data to see target gaps.</div>';
const sourceSummaryBox=$("[data-c4-source-summary]");
if(sourceSummaryBox){
const unavailable=Math.max(0,totalSources-availableSources);
sourceSummaryBox.innerHTML=`
        <article><strong>${availableSources}</strong><span>Available</span></article>
        <article><strong>${unavailable}</strong><span>Unavailable or restricted</span></article>
        <article><strong>${totalSources}</strong><span>Total checks</span></article>
      `;
}
const sourceTotal=$("[data-c4-source-total]");
if(sourceTotal)sourceTotal.textContent=`${totalSources} source checks`;
const qualityTable=$("[data-c4-quality-table]");
if(qualityTable){
qualityTable.innerHTML=qualityRows.join("")
||'<tr><td colspan="5">No source or field issues were reported.</td></tr>';
}
const registryTable=$("[data-c4-registry-table]");
if(registryTable){
registryTable.innerHTML=sourceRows.join("")
||'<tr><td colspan="6">Load Criterion 4 data to populate the source registry.</td></tr>';
}
renderOverviewQa();
renderC4Visual("overview");
const updated=$("[data-c4-overview-updated]");
if(updated)updated.textContent=`Updated ${new Date().toLocaleTimeString()}`;
}
function renderOverviewQa(){
const tbody=$("[data-c4-overview-qa]");
if(!tbody)return;
const selected=$("[data-c4-qa-filter]")?.value||"";
const rows=state.qa.filter(question=>!selected||question.criterion===selected);
tbody.innerHTML=rows.map(question=>{
const count=Number(question.record_count||0);
const drill=question.metric_id&&question.status==="available"
?`<button type="button" class="record-link ucc-qa-action" data-c4-overview-drill="${escapeHtml(question.metric_id)}">View ${count} matching record${count===1?"":"s"} ↗</button>`
:"";
return `
      <tr>
        <td>${escapeHtml(question.criterion)}</td>
        <td>${escapeHtml(question.question)}</td>
        <td><div>${escapeHtml(question.answer)}</div>${drill}</td>
        <td>${c4QaSourceCell(question)}</td>
        <td><span class="ucc-c4-status-pill" data-status="${escapeHtml(question.status)}">${escapeHtml(question.confidence)}</span></td>
      </tr>`;
}).join("")||'<tr><td colspan="5">No management questions match the current filter.</td></tr>';
$$("[data-c4-overview-drill]",tbody).forEach(button=>{
button.addEventListener("click",()=>openDrilldown(button.dataset.c4OverviewDrill));
});
}
function selectTab(tab,{load=true}={}){
$$("[data-c4-tab]").forEach(button=>{
button.classList.toggle("active",button.dataset.c4Tab===tab);
});
$$("[data-c4-panel]").forEach(panel=>{
panel.classList.toggle("hidden",panel.dataset.c4Panel!==tab);
});
state.tab=tab;
root.dataset.activeC4Tab=tab;
try{
const stored={tab,filters:filters()};
localStorage.setItem(STORAGE_KEY,JSON.stringify(stored));
}catch(error){}
const url=new URL(window.location.href);
url.searchParams.set("dashboard","criterion_4");
url.searchParams.set("c4tab",tab);
history.replaceState(null,"",url.toString());
if(!load)return;
if(TAB_MAP[tab]){
loadTab(tab).catch(error=>{
setNotice(error.message||"Unable to load Criterion 4 section.","error");
notify(error.message||"Criterion 4 request failed.","red");
});
}else{
loadAll().catch(()=>{});
}
}
function currentVisiblePanel(){
return $(`[data-c4-panel="${CSS.escape(state.tab)}"]`)||root;
}
function currentTable(){
const panel=currentVisiblePanel();
return $$("table",panel).find(table=>table.offsetParent!==null)||$("table",panel);
}
const csvCell=UCCShared.csvCell;
function rowsToCsv(rows){
if(!rows||!rows.length)return "";
const columns=[];
rows.forEach(row=>{
Object.keys(row||{}).forEach(key=>{
if(!columns.includes(key))columns.push(key);
});
});
const output=[columns.map(csvCell).join(",")];
rows.forEach(row=>{
output.push(columns.map(column=>csvCell(row[column])).join(","));
});
return output.join("\n");
}
function tableToCsv(table){return UCCShared.tableToCsv(table);}
function download(name,content,type="text/csv;charset=utf-8"){return UCCShared.download(name,content,type);}
function exportCurrent(){
const table=currentTable();
if(!table){
notify("No visible table to export.","orange");
return;
}
download(`criterion-4-${state.tab}.csv`,tableToCsv(table));
}
function exportAnswers(){
if(!state.qa.length){
notify("Load Criterion 4 data before exporting answers.","orange");
return;
}
download("criterion-4-management-answers.csv",rowsToCsv(state.qa));
}
function exportExceptions(){
if(!state.exceptions.length){
notify("No Criterion 4 exception data is loaded.","orange");
return;
}
download("criterion-4-exceptions.csv",rowsToCsv(state.exceptions));
}
async function copyFilteredLink(){
const url=new URL(window.location.href);
url.searchParams.set("dashboard","criterion_4");
url.searchParams.set("c4tab",state.tab);
Object.entries(filters()).forEach(entry=>{
const key="c4_"+entry[0];
const value=entry[1];
if(value)url.searchParams.set(key,value);
else url.searchParams.delete(key);
});
try{
await navigator.clipboard.writeText(url.toString());
notify("Filtered link copied.","green");
}catch(error){
window.prompt("Copy this link",url.toString());
}
}
function renderDrilldown(metric){
const dialog=$("[data-c4-drill-dialog]");
const title=$("[data-c4-drill-title]");
const stateBox=$("[data-c4-drill-state]");
const wrap=$("[data-c4-drill-table-wrap]");
const head=$("[data-c4-drill-head-row]");
const body=$("[data-c4-drill-body]");
if(title)title.textContent=metric.label||"Criterion 4 drill-down";
if(!dialog)return;
if(typeof dialog.showModal==="function"&&!dialog.open)dialog.showModal();
else dialog.setAttribute("open","");
if(metric.status!=="available"){
if(stateBox){
stateBox.classList.remove("hidden");
stateBox.textContent=statusText(metric.status);
}
if(wrap)wrap.classList.add("hidden");
return;
}
const rows=metric.rows||[];
state.drillRows=rows;
if(!rows.length){
if(stateBox){
stateBox.classList.remove("hidden");
stateBox.textContent="No matching records for the active filters.";
}
if(wrap)wrap.classList.add("hidden");
return;
}
const columns=[];
rows.forEach(row=>{
Object.keys(row||{}).forEach(key=>{
if(!columns.includes(key))columns.push(key);
});
});
if(head)head.innerHTML="<tr>"+columns.map(column=>`<th>${escapeHtml(column)}</th>`).join("")+"</tr>";
if(body)body.innerHTML=rows.map(row=>
"<tr>"+columns.map(column=>`<td>${escapeHtml(row[column])}</td>`).join("")+"</tr>"
).join("");
if(stateBox)stateBox.classList.add("hidden");
if(wrap)wrap.classList.remove("hidden");
}
async function openDrilldown(metricId){
const metric=state.metrics.get(metricId);
if(!metric){
notify("Metric mapping has not loaded yet.","orange");
return;
}
if(metric.status!=="available"){
renderDrilldown(metric);
return;
}
try{
const code=TAB_MAP[state.tab]||metric.criterion;
const result=await callApi(code,"drilldown",{metric_id:metric.id});
renderDrilldown(result.drilldown||metric);
}catch(error){
renderDrilldown({...metric,status:"error",message:error.message});
notify(error.message||"Unable to load drill-down.","red");
}
}
function renderDiagnostics(){
const body=$("[data-c4-diagnostics-body]");
if(!body)return;
body.innerHTML=state.logs.slice().reverse().map(row=>`
      <tr>
        <td>${escapeHtml(row.time)}</td>
        <td>${escapeHtml(row.level)}</td>
        <td>${escapeHtml(row.event)}</td>
        <td>${escapeHtml(row.detail)}</td>
      </tr>
    `).join("")||'<tr><td colspan="4">No diagnostics recorded.</td></tr>';
}
function openDiagnostics(){
const dialog=$("[data-c4-diagnostics-dialog]");
if(!dialog)return;
renderDiagnostics();
if(typeof dialog.showModal==="function"&&!dialog.open)dialog.showModal();
else dialog.setAttribute("open","");
}
function closeDialog(dialog){
if(!dialog)return;
if(typeof dialog.close==="function"&&dialog.open)dialog.close();
else dialog.removeAttribute("open");
}
function bindActions(){
$$("[data-c4-tab]").forEach(button=>{
button.addEventListener("click",()=>selectTab(button.dataset.c4Tab));
});
$$("[data-c4-filter]").forEach(input=>{
input.addEventListener("change",()=>{
state.results.clear();
state.metrics.clear();
try{
localStorage.setItem(STORAGE_KEY,JSON.stringify({tab:state.tab,filters:filters()}));
}catch(error){}
if(TAB_MAP[state.tab])loadTab(state.tab,{force:true}).catch(()=>{});
else loadAll({force:true}).catch(()=>{});
});
});
$$("[data-c4-card-toggle]").forEach(toggle=>{
const card=toggle.closest(".panel");
const visual=card?card.querySelector("[data-c4-visual]"):null;
const visualTab=visual?visual.dataset.c4Visual:"";
const storageKey=visualTab?`ucc.c4.visual.${visualTab}`:"";
let initialView="diagram";
if(storageKey){
try{
initialView=localStorage.getItem(storageKey)||"diagram";
}catch(error){}
}
$$("[data-c4-card-view]",toggle).forEach(item=>{
item.classList.toggle("active",item.dataset.c4CardView===initialView);
});
if(card){
$$("[data-c4-card-panel]",card).forEach(panel=>{
panel.classList.toggle("hidden",panel.dataset.c4CardPanel!==initialView);
});
}
$$("[data-c4-card-view]",toggle).forEach(button=>{
button.addEventListener("click",()=>{
const owner=button.closest(".panel");
if(!owner)return;
const view=button.dataset.c4CardView;
$$("[data-c4-card-view]",toggle).forEach(item=>item.classList.toggle("active",item===button));
$$("[data-c4-card-panel]",owner).forEach(panel=>{
panel.classList.toggle("hidden",panel.dataset.c4CardPanel!==view);
});
if(storageKey){
try{
localStorage.setItem(storageKey,view);
}catch(error){}
}
if(view==="diagram"&&visualTab){
renderC4Visual(visualTab);
}
});
});
});
$$("[data-c4-drill]").forEach(card=>{
card.addEventListener("click",()=>openDrilldown(card.dataset.c4Drill));
});
$("[data-c4-qa-filter]")?.addEventListener("change",renderOverviewQa);
root.addEventListener("click",event=>{
const button=event.target.closest("[data-c4-action]");
if(!button)return;
const action=button.dataset.c4Action;
if(action==="refresh"){
state.results.clear();
state.metrics.clear();
loadAll({force:true}).catch(()=>{});
}
if(action==="export-current")exportCurrent();
if(action==="export-answers")exportAnswers();
if(action==="export-exceptions")exportExceptions();
if(action==="copy-link")copyFilteredLink();
if(action==="show-diagnostics")openDiagnostics();
});
$("[data-c4-drill-close]")?.addEventListener("click",()=>closeDialog($("[data-c4-drill-dialog]")));
$("[data-c4-drill-export]")?.addEventListener("click",()=>{
if(!state.drillRows.length){
notify("No drill-down rows to export.","orange");
return;
}
download(`criterion-4-${state.tab}-drilldown.csv`,rowsToCsv(state.drillRows));
});
$("[data-c4-diagnostics-close]")?.addEventListener("click",()=>closeDialog($("[data-c4-diagnostics-dialog]")));
$("[data-c4-diagnostics-clear]")?.addEventListener("click",()=>{
state.logs=[];
renderDiagnostics();
const count=$("[data-c4-log-count]");
if(count)count.textContent="0";
});
$("[data-c4-diagnostics-export]")?.addEventListener("click",()=>{
if(!state.logs.length){
notify("No diagnostics to export.","orange");
return;
}
download("criterion-4-diagnostics.csv",rowsToCsv(state.logs));
});
}
function restoreState(){
let tab="overview";
let stored={};
try{
stored=JSON.parse(localStorage.getItem(STORAGE_KEY)||"{}");
}catch(error){}
const url=new URL(window.location.href);
tab=url.searchParams.get("c4tab")||stored.tab||tab;
if(!root.querySelector(`[data-c4-tab="${CSS.escape(tab)}"]`))tab="overview";
$$("[data-c4-filter]").forEach(input=>{
const urlValue=url.searchParams.get("c4_"+input.dataset.c4Filter);
const storedValue=stored.filters&&stored.filters[input.dataset.c4Filter];
const value=urlValue!==null?urlValue:storedValue;
if(value!==undefined&&value!==null)input.value=value;
});
selectTab(tab);
}
let c4ResizeFrame=0;
window.addEventListener("resize",()=>{
if(c4ResizeFrame)return;
c4ResizeFrame=window.requestAnimationFrame(()=>{
c4ResizeFrame=0;
if(TAB_MAP[state.tab])renderC4Visual(state.tab);
});
},{passive:true});
bindActions();
addLog("INFO","criterion_4_initialized",{version:"1.9.6"});
if(!root.classList.contains("ucc-hidden")){
restoreState();
}else{
platform.addEventListener("ucc:dashboard-change",function onFirstShow(event){
if(event.detail&&event.detail.dashboard==="criterion_4"){
platform.removeEventListener("ucc:dashboard-change",onFirstShow);
restoreState();
}
});
}
})();
(function(){
"use strict";
const platform=typeof root_element!=="undefined"?root_element.querySelector("#uccIntelligencePlatform"):document.querySelector("#uccIntelligencePlatform");
if(!platform||platform.dataset.sharedHeroToolsReady==="1")return;
platform.dataset.sharedHeroToolsReady="1";
const csvCell=UCCShared.csvCell;
function dashboardOwner(toolbar){return toolbar.closest("[data-dashboard-panel]")||platform;}
function activePanel(owner){return Array.from(owner.querySelectorAll(".panel-view")).find(panel=>!panel.classList.contains("hidden")&&!panel.classList.contains("ucc-hidden"))||owner;}
function tableCandidates(owner,exceptionsOnly){const panel=activePanel(owner);let tables=Array.from(panel.querySelectorAll("table"));if(exceptionsOnly){const filtered=tables.filter(table=>/exception|gap|risk|overdue|attention|quality/i.test((table.closest(".panel")?.innerText||"")+" "+(table.className||"")));if(filtered.length)tables=filtered;}tables.sort((a,b)=>(b.offsetParent!==null?1:0)-(a.offsetParent!==null?1:0));return tables;}
function notify(message,indicator){if(window.frappe&&frappe.show_alert)frappe.show_alert({message,indicator:indicator||"blue"});}
function exportTable(owner,exceptionsOnly){const table=tableCandidates(owner,exceptionsOnly)[0];if(!table){notify("No table is available in the current section.","orange");return;}const rows=Array.from(table.rows).map(row=>Array.from(row.cells).map(cell=>csvCell(cell.innerText.trim())).join(","));UCCShared.download(exceptionsOnly?"ucc-current-exceptions.csv":"ucc-current-table.csv",rows.join("\n"),"text/csv;charset=utf-8");}
function copyLink(owner){const url=new URL(window.location.href),dashboard=owner.dataset.dashboardPanel;if(dashboard)url.searchParams.set("dashboard",dashboard);if(owner.dataset.demoActiveTab)url.searchParams.set("demo_tab",owner.dataset.demoActiveTab);if(owner.dataset.activeTab)url.searchParams.set("ucc_tab",owner.dataset.activeTab);const value=url.toString(),task=navigator.clipboard?.writeText?navigator.clipboard.writeText(value):Promise.reject(new Error("Clipboard unavailable"));task.then(()=>notify("Filtered link copied.","green")).catch(()=>window.prompt("Copy this link",value));}
function handleAction(action,owner){
if(action==="visual-navigator"){window.UCCExplore?.openNavigator(owner?.dataset?.dashboardPanel);return;}
if(action==="source-mapping"){platform.dispatchEvent(new CustomEvent("ucc:open-source-mapping",{detail:{dashboard:owner?.dataset?.dashboardPanel||""}}));return;}
if(owner&&owner.matches&&owner.matches("[data-demo-dashboard]")){owner.dispatchEvent(new CustomEvent("ucc:live-tool-action",{detail:{action}}));return;}
if(action==="export-current")exportTable(owner,false);
if(action==="export-exceptions")exportTable(owner,true);
if(action==="copy-link")copyLink(owner);
}
function close(toolbar){const trigger=toolbar.querySelector("[data-ucc-tools-trigger]"),menu=toolbar.querySelector("[data-ucc-tools-menu]");toolbar.removeAttribute("open");if(menu)menu.hidden=true;if(trigger)trigger.setAttribute("aria-expanded","false");}
function closeAll(except){platform.querySelectorAll("[data-ucc-tools][open]").forEach(toolbar=>{if(toolbar!==except)close(toolbar);});}
platform.querySelectorAll("[data-ucc-tools]").forEach(toolbar=>{
if(toolbar.dataset.toolsReady==="1")return;
toolbar.dataset.toolsReady="1";
const trigger=toolbar.querySelector("[data-ucc-tools-trigger]"),menu=toolbar.querySelector("[data-ucc-tools-menu]");
if(!trigger||!menu)return;
trigger.addEventListener("click",event=>{event.preventDefault();event.stopPropagation();const opening=!toolbar.hasAttribute("open");closeAll(toolbar);toolbar.toggleAttribute("open",opening);menu.hidden=!opening;trigger.setAttribute("aria-expanded",opening?"true":"false");});
menu.addEventListener("click",event=>{const button=event.target.closest("[data-ucc-tool-action]");if(!button)return;event.preventDefault();event.stopPropagation();handleAction(button.dataset.uccToolAction,dashboardOwner(toolbar));close(toolbar);});
});
document.addEventListener("click",event=>{if(!event.target.closest("[data-ucc-tools]"))closeAll();});
document.addEventListener("keydown",event=>{if(event.key==="Escape")closeAll();});
})();
(function(){
"use strict";
const platform=typeof root_element!=="undefined"
?root_element.querySelector("#uccIntelligencePlatform")
:document.querySelector("#uccIntelligencePlatform");
if(!platform||platform.dataset.criterionNoticesReady==="1")return;
platform.dataset.criterionNoticesReady="1";
platform.querySelectorAll("[data-notice-dismiss]").forEach(button=>{
button.addEventListener("click",()=>{
const notice=button.closest(".ucc-criterion-notice");
if(!notice)return;
notice.dataset.dismissed="1";
notice.hidden=true;
});
});
})();

/* UCC Intelligence Platform v1.8.2 integrated interaction controls */
(function () {
"use strict";

const root = typeof root_element !== "undefined"
? root_element.querySelector("#uccIntelligencePlatform")
: document.querySelector("#uccIntelligencePlatform");

if (!root || root.dataset.v182ControlsReady === "1") return;
root.dataset.v182ControlsReady = "1";

function closeToolMenus(except) {
root.querySelectorAll(".ucc-hero-tools[open]").forEach(function (details) {
if (details !== except) {
details.removeAttribute("open");
const summary = details.querySelector("summary");
if (summary) summary.setAttribute("aria-expanded", "false");
}
});
}

root.querySelectorAll(".ucc-hero-tools").forEach(function (details) {
const summary = details.querySelector(":scope > summary");
if (!summary) return;
summary.setAttribute("role", "button");
summary.setAttribute("aria-expanded", details.hasAttribute("open") ? "true" : "false");
summary.addEventListener("click", function (event) {
event.preventDefault();
event.stopPropagation();
const willOpen = !details.hasAttribute("open");
closeToolMenus(details);
details.toggleAttribute("open", willOpen);
summary.setAttribute("aria-expanded", willOpen ? "true" : "false");
});
details.querySelectorAll("button").forEach(function (button) {
button.addEventListener("click", function () {
details.removeAttribute("open");
summary.setAttribute("aria-expanded", "false");
});
});
});

document.addEventListener("click", function (event) {
if (!event.target.closest(".ucc-hero-tools")) closeToolMenus();
});
document.addEventListener("keydown", function (event) {
if (event.key === "Escape") closeToolMenus();
});

root.addEventListener("click", function (event) {
const tab = event.target.closest("[data-ucc-placeholder-tab]");
if (!tab) return;
const dashboard = tab.closest("[data-dashboard-panel]");
if (!dashboard) return;
const key = tab.dataset.uccPlaceholderTab;
dashboard.querySelectorAll("[data-ucc-placeholder-tab]").forEach(function (button) {
button.classList.toggle("is-active", button === tab);
});
dashboard.querySelectorAll("[data-ucc-placeholder-panel]").forEach(function (panel) {
const active = panel.dataset.uccPlaceholderPanel === key;
panel.hidden = !active;
panel.classList.toggle("is-active", active);
});
});

})();




