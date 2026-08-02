import frappe

from ucc_intelligence.ai import client as _ai_client
from ucc_intelligence.ai import orchestration as _ask_ucc_orchestration
from ucc_intelligence.analytics import admission_intelligence_embed, criterion_1, criterion_2, criterion_3, criterion_4, criterion_5, criterion_6, criterion_7
from ucc_intelligence.analytics import drilldown as _drilldown
from ucc_intelligence.analytics import tab_charts as _tab_charts
from ucc_intelligence.analytics.contracts import is_permission_error as _is_permission_error
from ucc_intelligence.analytics.request import parse_payload
from ucc_intelligence.ask_ucc import contracts as _ask_ucc_contracts
from ucc_intelligence.ask_ucc import conversations as _ask_ucc_conversations
from ucc_intelligence.ask_ucc import guided_questions as _ask_ucc_guided
from ucc_intelligence.actions import registry as _action_registry
from ucc_intelligence.actions import service as _action_service
from ucc_intelligence.knowledge import ingestion as _knowledge_ingestion
from ucc_intelligence.knowledge import retrieval as _knowledge_retrieval
from ucc_intelligence.monitoring import engine as _monitoring_engine
from ucc_intelligence.operations import service as _operations
from ucc_intelligence.monitoring import rule_registry as _monitoring_rules
from ucc_intelligence.permissions.access import get_dashboard_access as _get_dashboard_access
from ucc_intelligence.settings import status as _settings_status

CRITERION_1_ALLOWED_ACTIONS = [
	"summary", "source_status", "policy_registry", "requirement_registry",
	"question_registry", "drilldown",
]

CRITERION_2_ALLOWED_ACTIONS = [
	"summary", "source_status", "policy_registry", "requirement_registry",
	"question_registry", "drilldown",
]

# Criterion 4 was "summary" only while the module held admission_intelligence
# and nothing else. The verbatim port on 2026-08-02 brought the other six
# actions with it -- the registries and the drilldown now have real data
# behind them -- so it takes the same list as every other ported criterion.
CRITERION_4_ALLOWED_ACTIONS = [
	"summary", "source_status", "policy_registry", "requirement_registry",
	"question_registry", "drilldown",
]

CRITERION_3_ALLOWED_ACTIONS = [
	"summary", "source_status", "policy_registry", "requirement_registry",
	"question_registry", "question_catalogue", "drilldown",
]

CRITERION_5_ALLOWED_ACTIONS = [
	"summary", "source_status", "policy_registry", "requirement_registry",
	"question_registry", "drilldown",
]

# Criterion 5's legacy script defaults `limit` to 500 and clamps to 2000; the
# shared parse_payload() (extracted from Criterion 1) uses 2000/5000. Routing
# this criterion through the shared parser unchanged would silently quadruple
# both, so get_criterion_5() re-clamps rather than forking the parser for one
# caller. See analytics/criterion_5.py's module docstring, special case 5.
CRITERION_5_DEFAULT_ROW_LIMIT = 500
CRITERION_5_MAX_ROW_LIMIT = 2000

CRITERION_6_ALLOWED_ACTIONS = [
	"summary", "source_status", "policy_registry", "requirement_registry",
	"question_registry", "drilldown",
]

CRITERION_7_ALLOWED_ACTIONS = [
	"summary", "source_status", "policy_registry", "requirement_registry",
	"question_registry", "drilldown",
]


def _relabel_api_method(result, criterion_number):
	"""Stamp the response with the method that ACTUALLY served it.

	Each criterion module's run() is a verbatim port of the legacy Server
	Script, right down to the `api_method` string it puts in meta -- so a
	response served by this app still announced itself as
	`ucc_analytics_criterion_N`. That was harmless while the frontend really
	did call the Server Script; after the Phase 13 cutover it is simply
	untrue, and meta.api_method is exactly what someone reads when
	diagnosing which layer answered.

	Corrected HERE rather than in the criterion modules because those are
	byte-identical ports and their own tests re-extract the legacy source to
	prove it. Relabelling inside them would break that guarantee to fix a
	label; this is app-authored code, so it costs nothing.
	"""
	if isinstance(result, dict) and isinstance(result.get("meta"), dict):
		result["meta"]["api_method"] = "ucc_intelligence.api.get_criterion_%s" % criterion_number
		result["meta"]["served_by"] = "ucc_intelligence app"
	return result


@frappe.whitelist()
def health_check():
	"""Confirm the app is installed and reachable. No business data, no auth bypass."""
	return {
		"ok": True,
		"app": "ucc_intelligence",
		"user": frappe.session.user,
	}


@frappe.whitelist()
def get_settings_status():
	"""Read-only status summary for the UCC Intelligence Settings form
	(docs/architecture/settings-page-plan.md). System Manager only -- the
	underlying reads (settings/status.py) are not all self-gating the way
	an ordinary frappe.get_list call is (load_rows() reads with
	ignore_permissions=True by its own existing design), and this returns
	more than any one user should necessarily see (every configured role's
	access, not just their own), so the gate belongs here explicitly."""
	frappe.only_for("System Manager")
	return _settings_status.get_status_summary()


@frappe.whitelist()
def fetch_ai_models():
	"""The provider's model list, for the AI Model field's dropdown.

	System Manager only -- this spends a real API call against UCC's provider
	account, so it is not something any logged-in user should be able to
	trigger. The API key stays server-side: this returns model ids and a
	status, never the key or the raw provider response.
	"""
	frappe.only_for("System Manager")
	return _ai_client.list_models()


@frappe.whitelist()
def run_monitoring(rule=None):
	"""Run one monitoring rule, or every enabled rule.

	System Manager only. A run reads every record in the target DocType
	(monitoring/engine.py explains why), so triggering one is an
	administrative act, not something an ordinary user should be able to
	fire on demand. The FINDINGS it produces are permission-gated normally.

	`rule` is validated against the fixed registry before use -- an unknown
	value is rejected, never used to reach code by name.
	"""
	frappe.only_for("System Manager")
	if rule:
		rule = frappe.utils.cstr(rule).strip()
		if rule not in _monitoring_rules.RULES:
			frappe.throw(frappe._("Unknown monitoring rule."))
		return {"ok": True, "runs": [_monitoring_engine.run_rule(rule)]}
	return {"ok": True, "runs": _monitoring_engine.run_all_rules()}


@frappe.whitelist()
def search_knowledge(question, limit=5):
	"""Permission-aware document search over registered knowledge sources.

	No only_for: retrieval filters per-user itself (knowledge/retrieval.py's
	current_source_names applies the source's restricted-to-role, and
	frappe.get_list applies ordinary DocType permissions on top), so this is
	safe for any authenticated user -- they get exactly the documents their
	roles allow.

	Gated on the document-knowledge toggle so an unfinished index is not
	quietly queryable.
	"""
	question = frappe.utils.cstr(question).strip()
	if not question:
		frappe.throw(frappe._("Please enter a question."))
	try:
		enabled = bool(frappe.get_single("UCC Intelligence Settings").enable_document_knowledge)
	except Exception:
		enabled = False
	if not enabled:
		return {"ok": True, "results": [], "note": "Document knowledge is not enabled."}
	return _knowledge_retrieval.search(question, limit=limit)


@frappe.whitelist()
def get_monitoring_findings(status="Open", limit=100):
	"""Open findings, newest first.

	No ignore_permissions and no only_for: frappe.get_list applies the
	Finding DocType's own permissions, so a user sees exactly the findings
	their roles allow. Page size is clamped rather than caller-controlled
	(CLAUDE.md §11.4).
	"""
	status = frappe.utils.cstr(status).strip() or "Open"
	if status not in ("Open", "Resolved", "Suppressed"):
		frappe.throw(frappe._("Unknown finding status."))
	limit = max(1, min(500, frappe.utils.cint(limit) or 100))
	return {
		"ok": True,
		"findings": frappe.get_list(
			"UCC Monitoring Finding",
			filters={"status": status},
			fields=["name", "rule", "target_doctype", "target_record", "detail",
				"severity", "occurrence_count", "modified"],
			order_by="modified desc",
			limit_page_length=limit,
		),
	}



@frappe.whitelist()
def search_insights_charts(term=None, limit=20):
	"""The "+ Add chart" picker: Insights queries this user can read.

	No only_for -- what comes back is exactly what frappe.get_list allows this
	user to see, so the endpoint cannot show anyone a chart they could not
	already open in Insights itself.
	"""
	return _tab_charts.search(term, limit)


@frappe.whitelist()
def get_tab_charts(criterion, tab):
	"""Everything one criterion tab holds for this user: its charts and their
	sizes, its intro text, and which management questions it hides."""
	return _tab_charts.get_tab(criterion, tab)


@frappe.whitelist()
def set_tab_chart_size(criterion, tab, chart, span):
	"""Resize one card to a whole number of the tab's 12 grid columns. The drag
	snaps to the grid in the browser; this refuses anything off it."""
	return _tab_charts.set_size(criterion, tab, chart, span)


@frappe.whitelist()
def set_tab_chart_order(criterion, tab, order):
	"""Reorder the cards on a tab, after a drag."""
	return _tab_charts.set_order(criterion, tab, order)


@frappe.whitelist()
def get_tab_history(criterion, tab, limit=50):
	"""Who changed this tab's configuration, what changed, and when.

	No only_for: everyone who can see a tab can see how it came to look that
	way, and the records hold configuration rather than institutional data.
	Nobody can write one -- see analytics/tab_audit.py."""
	return _tab_charts.history(criterion, tab, limit)


@frappe.whitelist()
def set_tab_intro(criterion, tab, intro):
	"""The tab's own intro text. Stored as written; the page renders a small
	escaped Markdown subset, so it can never become an injection point."""
	return _tab_charts.set_intro(criterion, tab, intro)


@frappe.whitelist()
def set_tab_question(criterion, tab, question, visible):
	"""Show or hide one management question on this tab. Stores WHICH question,
	never an answer -- every answer is still computed live and
	permission-checked on each request."""
	return _tab_charts.set_question(criterion, tab, question, visible)


@frappe.whitelist()
def add_tab_chart(criterion, tab, chart):
	"""Add one Insights chart to one tab, for this user."""
	return _tab_charts.add(criterion, tab, chart)


@frappe.whitelist()
def remove_tab_chart(criterion, tab, chart):
	"""Remove one chart from one tab, for this user."""
	return _tab_charts.remove(criterion, tab, chart)


@frappe.whitelist()
def get_tab_chart_data(chart, criterion=None, tab=None):
	"""Execute one embedded chart.

	The id is checked against what this user may read at THIS moment, not
	against what was true when they added it: chart_data() calls
	check_permission("read") before execute(), so a revoked permission takes
	effect on the next refresh. The public-dashboard mechanism is never used --
	it applies no permissions at all.
	"""
	return _tab_charts.chart_data(chart, criterion=criterion, tab=tab)


@frappe.whitelist()
def set_tab_chart_title(criterion, tab, chart, title=None):
	"""Give one card its own display title.

	An Insights record is named for whoever built the query; a criterion tab is
	read by an auditor. Blank clears it and the record's own title returns.
	"""
	return _tab_charts.set_display_title(criterion, tab, chart, title)


@frappe.whitelist()
def set_tab_chart_palette(criterion, tab, chart, palette=None):
	"""Override one chart's series colours on one tab.

	Colour is Sophia's, not Insights': the live probe on 2026-08-02 dumped all
	seven Insights Chart v3 records in full and there is no colour field on any
	of them. See analytics/chart_presentation.py and ADR-015. Blank clears the
	override and the chart returns to the institution's default.
	"""
	return _tab_charts.set_palette(criterion, tab, chart, palette)


# ---------------------------------------------------------------------------
# OPERATIONS -- monitoring findings and document knowledge, made visible
#
# Both engines existed and neither was reachable outside a bench console. These
# read and act; no detection or retrieval logic lives here. See
# operations/service.py for who may see and do what, and why the two differ.
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_monitoring_overview():
	"""Rules, open findings by severity, and recent runs.

	No only_for: every read inside goes through frappe.get_list, so a user sees
	exactly the findings whose target records they may already read. Someone
	with no access to Student Log sees no Student Log findings.
	"""
	return _operations.monitoring_overview()


@frappe.whitelist()
def get_monitoring_findings_list(status="Open", rule=None, severity=None, limit=100):
	"""Findings, filtered. Permission-applied per row by get_list."""
	return _operations.findings(status=status, rule=rule, severity=severity, limit=limit)


@frappe.whitelist()
def set_monitoring_finding_status(finding, status, note=None):
	"""Resolve, suppress or reopen one finding.

	Gated on write permission for UCC Monitoring Finding -- seeing a finding
	and being the person who may declare it dealt with are different things.
	Suppression requires a note, because a suppressed finding never returns on
	a later run and an unexplained permanent silence is not auditable.
	"""
	return _operations.set_finding_status(finding, status, note)


@frappe.whitelist()
def get_knowledge_overview():
	"""Registered document sources and their indexing state.

	Returns an empty list when nothing is registered, which is the honest
	answer -- the panel says so rather than implying an index exists.
	"""
	return _operations.knowledge_overview()


@frappe.whitelist()
def add_knowledge_source(title, source_type="Policy", text=None, attached_file=None):
	"""Register a document and index it. Write permission on the DocType."""
	return _operations.add_source(title, source_type, text=text, attached_file=attached_file)


@frappe.whitelist()
def reindex_knowledge(source=None):
	"""Re-index one source, or every stale one."""
	return _operations.reindex(source)


@frappe.whitelist()
def get_access_overview():
	"""Who can see what, for the settings page. Existing permissions only."""
	return _operations.access_overview()


@frappe.whitelist()
def set_monitoring_rule(rule_id, enabled=None, severity=None):
	"""Turn a monitoring rule on/off, or change its severity.

	The rule's definition stays in code; only its on/off state and severity are
	editable. Gated on write permission for UCC Monitoring Rule.
	"""
	return _operations.set_rule_config(rule_id, enabled, severity)


@frappe.whitelist()
def get_chart_drilldown(chart):
	"""Whether a chart's segments can be opened, and on which columns.

	Asked once when a chart renders, so the page only offers the drill-down on
	charts that actually have one -- rather than offering it everywhere and
	explaining the refusal after the click.
	"""
	return _drilldown.resolve(chart)


@frappe.whitelist()
def get_chart_records(chart, column, value, page=1, page_size=20):
	"""The records behind one chart segment.

	The permission story is deliberately different from get_tab_chart_data().
	That one checks read permission on the Insights Query, which is right for a
	count. This returns records, so it additionally requires read permission on
	the underlying DocType and fetches through frappe.get_list, which applies
	user permissions and the DocType's own query conditions. A reader who may
	see the bar but not the rows gets an empty list, never a leak.

	Paged, and capped -- see drilldown.MAX_PAGE_SIZE. A segment with 4,000
	records behind it is not sent to a browser in one response.
	"""
	return _drilldown.records(chart, column, value, page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# CONTROLLED ACTIONS (CLAUDE.md Phase 12)
#
# Nothing here executes anything. propose() creates a Draft; approval runs
# through Frappe's own Workflow; execute() only works from Approved and
# re-checks permissions at that moment. See actions/service.py.
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_action_types():
	"""The allowlist, so a UI can offer only what exists. Metadata only."""
	return {"ok": True, "summary": _action_registry.summary(), "actions": [
		{"action_type": key, "label": spec["label"], "level": spec["level"],
			"placeholder": spec["placeholder"], "description": spec["description"]}
		for key, spec in sorted(_action_registry.ACTIONS.items())
	]}


@frappe.whitelist()
def propose_action(action_type, title=None, payload=None, target_record=None, reason="", sources=None):
	"""Propose an action. Creates a Draft and nothing else.

	No only_for: proposing is harmless by construction -- a Draft executes
	nothing, and propose() already checks the proposer can READ the target.
	Approval and execution are where the gates belong, and they are gated.
	"""
	return _action_service.propose(
		frappe.utils.cstr(action_type).strip(),
		frappe.utils.cstr(title).strip() or None,
		payload=payload, target_record=frappe.utils.cstr(target_record).strip() or None,
		reason=frappe.utils.cstr(reason).strip(), sources=sources,
	)


@frappe.whitelist()
def transition_action(action_request, workflow_action):
	"""Move a request through the approval workflow.

	Deliberately NOT gated with only_for here -- Frappe's Workflow decides
	which roles may take which transition, including whether the proposer may
	approve their own request. A second check here could disagree with it.
	"""
	return _action_service.transition(
		frappe.utils.cstr(action_request).strip(),
		frappe.utils.cstr(workflow_action).strip(),
	)


@frappe.whitelist()
def execute_action(action_request):
	"""Carry out an APPROVED request. System Manager only, on top of the
	workflow's own gate -- this is the one call in the platform that writes
	to another system, so it carries a belt as well as braces."""
	frappe.only_for("System Manager")
	return _action_service.execute(frappe.utils.cstr(action_request).strip())


@frappe.whitelist()
def get_action_requests(state=None, limit=50):
	"""Requests visible to this user. frappe.get_list applies the DocType's
	own permissions, which grant if_owner read to All -- so a proposer sees
	their own requests and an approver sees everything."""
	return {"ok": True, "requests": _action_service.list_requests(
		frappe.utils.cstr(state).strip() or None, limit)}


# ---------------------------------------------------------------------------
# KNOWLEDGE INGESTION (CLAUDE.md Phase 9)
# ---------------------------------------------------------------------------
@frappe.whitelist()
def register_knowledge_source(title, source_type, text=None, attached_file=None,
		document_version=None, effective_date=None, classification=None, permission_role=None):
	"""Register and index a document in one step. System Manager only:
	registering a source decides what the assistant will quote as policy."""
	frappe.only_for("System Manager")
	return _knowledge_ingestion.register_source(
		frappe.utils.cstr(title).strip(),
		frappe.utils.cstr(source_type).strip(),
		text=text,
		attached_file=frappe.utils.cstr(attached_file).strip() or None,
		document_version=frappe.utils.cstr(document_version).strip() or None,
		effective_date=effective_date or None,
		classification=frappe.utils.cstr(classification).strip() or None,
		permission_role=frappe.utils.cstr(permission_role).strip() or None,
	)


@frappe.whitelist()
def reindex_knowledge_source(source):
	"""Re-index one source after its file changed."""
	frappe.only_for("System Manager")
	return _knowledge_ingestion.index_source(frappe.utils.cstr(source).strip())


@frappe.whitelist()
def supersede_knowledge_source(old_source, new_source):
	"""Retire a document in favour of its replacement, so the old one can
	never again be quoted as current."""
	frappe.only_for("System Manager")
	return _knowledge_ingestion.supersede(
		frappe.utils.cstr(old_source).strip(), frappe.utils.cstr(new_source).strip())


@frappe.whitelist()
def get_dashboard_access():
	"""Which dashboard workspaces and criteria the signed-in user's roles allow
	the interface to build. Interface composition only -- see
	ucc_intelligence/ucc_intelligence/permissions/access.py."""
	return _get_dashboard_access()


@frappe.whitelist()
def get_criterion_1():
	"""Phase 4 port of `ucc_analytics_criterion_1`
	(server-scripts/UCC Analytics - Criterion 1.py). Not yet called by the
	frontend -- sophia_analytics.js still calls the legacy Server Script
	directly (Phase 4 plan Decision B: ship dark, cut over once parity is
	confirmed on a real bench). See
	ucc_intelligence/ucc_intelligence/analytics/criterion_1.py."""
	parsed = parse_payload(
		frappe.form_dict.get("payload"),
		default_subcriterion="1.1.1",
		allowed_actions=CRITERION_1_ALLOWED_ACTIONS,
		criterion_label="Criterion 1",
	)
	return _relabel_api_method(criterion_1.run(**parsed), "1")


@frappe.whitelist()
def get_criterion_2():
	"""Phase 4 port of `ucc_analytics_criterion_2`
	(server-scripts/UCC Analytics - Criterion 2.py). Not yet called by the
	frontend -- sophia_analytics.js still calls the legacy Server Script
	directly (Decision B: ship dark, cut over once parity is confirmed on a
	real bench). See ucc_intelligence/ucc_intelligence/analytics/criterion_2.py."""
	parsed = parse_payload(
		frappe.form_dict.get("payload"),
		default_subcriterion="2.1.1",
		allowed_actions=CRITERION_2_ALLOWED_ACTIONS,
		criterion_label="Criterion 2",
	)
	return _relabel_api_method(criterion_2.run(**parsed), "2")


@frappe.whitelist()
def get_admission_intelligence():
	"""Option B live embed for Criterion 4's admission_intelligence (4 KPIs
	+ 6 chart series) -- executes real Insights Query v3 records server-side,
	permission-checked per request. See
	ucc_intelligence/ucc_intelligence/analytics/admission_intelligence_embed.py's
	module docstring for the full architecture and the
	Insights Settings.apply_user_permissions dependency. This IS wired into
	sophia_analytics.js. Criterion 4's other metrics and its 40 management
	questions are no longer the legacy Server Script's -- they are ported in
	analytics/criterion_4.py and served by get_criterion_4()."""
	return admission_intelligence_embed.run()


@frappe.whitelist()
def get_criterion_4():
	"""Criterion 4 -- the full verbatim port of
	server-scripts/UCC Analytics - Criterion 4.py: 40 management questions
	across 8 sections, 81 metrics, the requirement registry and the 33 engine
	functions.

	One declared divergence: admission_intelligence comes from
	analytics/criterion_4_admission.py, the Insights-informed implementation
	that was already live, rather than from the legacy
	build_admission_intelligence(). See criterion_4.py's module docstring."""
	parsed = parse_payload(
		frappe.form_dict.get("payload"),
		default_subcriterion="4.1.1",
		allowed_actions=CRITERION_4_ALLOWED_ACTIONS,
		criterion_label="Criterion 4",
	)
	return _relabel_api_method(criterion_4.run(**parsed), "4")


@frappe.whitelist()
def get_criterion_3():
	"""Phase 4 port of `ucc_analytics_criterion_3`
	(server-scripts/UCC Analytics - Criterion 3.py). Not yet called by the
	frontend -- sophia_analytics.js still calls the legacy Server Script
	directly (Decision B: ship dark, cut over once parity is confirmed on a
	real bench). See ucc_intelligence/ucc_intelligence/analytics/criterion_3.py."""
	parsed = parse_payload(
		frappe.form_dict.get("payload"),
		default_subcriterion="3.1.1",
		allowed_actions=CRITERION_3_ALLOWED_ACTIONS,
		criterion_label="Criterion 3",
	)
	return _relabel_api_method(criterion_3.run(**parsed), "3")


@frappe.whitelist()
def get_criterion_5():
	"""Phase 4 port of `ucc_analytics_criterion_5`
	(server-scripts/UCC Analytics - Criterion 5.py). Option A, a verbatim
	port like Criteria 1/2/3/6/7 -- Criterion 5 has no
	admission_intelligence-equivalent block, so Criterion 4's Insights-embed
	approach doesn't apply. Not yet called by the frontend (Decision B: ship
	dark). See ucc_intelligence/ucc_intelligence/analytics/criterion_5.py.

	Two criterion-specific deviations from the shared shape, both documented
	in that module: `question_id` (a drilldown fallback no other criterion
	has, so it's read here rather than widening the shared parser) and the
	tighter legacy row limit, re-clamped below."""
	raw_payload = frappe.form_dict.get("payload")
	parsed = parse_payload(
		raw_payload,
		default_subcriterion="5.1.1",
		allowed_actions=CRITERION_5_ALLOWED_ACTIONS,
		criterion_label="Criterion 5",
	)

	payload = raw_payload or {}
	if isinstance(payload, str):
		try:
			payload = frappe.parse_json(payload) or {}
		except Exception:
			payload = {}
	if not isinstance(payload, dict):
		payload = {}

	requested_limit = payload.get("limit") or CRITERION_5_DEFAULT_ROW_LIMIT
	try:
		parsed["row_limit"] = max(1, min(int(requested_limit), CRITERION_5_MAX_ROW_LIMIT))
	except Exception:
		parsed["row_limit"] = CRITERION_5_DEFAULT_ROW_LIMIT

	return _relabel_api_method(criterion_5.run(question_id=payload.get("question_id"), **parsed), "5")


@frappe.whitelist()
def get_criterion_6():
	"""Phase 4 port of `ucc_analytics_criterion_6`
	(server-scripts/UCC Analytics - Criterion 6.py). Not yet called by the
	frontend -- sophia_analytics.js still calls the legacy Server Script
	directly (Decision B: ship dark, cut over once parity is confirmed on a
	real bench). See ucc_intelligence/ucc_intelligence/analytics/criterion_6.py."""
	parsed = parse_payload(
		frappe.form_dict.get("payload"),
		default_subcriterion="6.1.1",
		allowed_actions=CRITERION_6_ALLOWED_ACTIONS,
		criterion_label="Criterion 6",
	)
	return _relabel_api_method(criterion_6.run(**parsed), "6")


@frappe.whitelist()
def get_criterion_7():
	"""Phase 4 port of `ucc_analytics_criterion_7`
	(server-scripts/UCC Analytics - Criterion 7.py). Not yet called by the
	frontend -- sophia_analytics.js still calls the legacy Server Script
	directly (Decision B: ship dark, cut over once parity is confirmed on a
	real bench). See ucc_intelligence/ucc_intelligence/analytics/criterion_7.py."""
	parsed = parse_payload(
		frappe.form_dict.get("payload"),
		default_subcriterion="7.1.1",
		allowed_actions=CRITERION_7_ALLOWED_ACTIONS,
		criterion_label="Criterion 7",
	)
	return _relabel_api_method(criterion_7.run(**parsed), "7")


@frappe.whitelist()
def ask_ucc(module, question, record):
	"""Ask UCC -- all three modules (quality_action, recruitment_agent,
	student_journey) through one endpoint, since the pipeline is identical
	and only the tool set differs
	(docs/architecture/ask-ucc-phase-plan.md §6).

	No role check at this layer, by design -- whether this user's role may
	see a given module in the UI at all is interface composition
	(get_dashboard_access()'s ask_ucc_modules, same as hidden Analytics
	criteria), and the real data gate is the ordinary Frappe DocType
	permission each tool already applies via frappe.get_doc(). Exactly the
	same split CLAUDE.md §3.3 establishes for Analytics, not a new
	exception.

	`module` is validated against the fixed MODULES registry before
	anything else runs -- an unknown value is rejected, never used to
	reach code by name."""
	module = frappe.utils.cstr(module).strip()
	question = frappe.utils.cstr(question).strip()
	record = frappe.utils.cstr(record).strip()

	if module not in _ask_ucc_orchestration.MODULES:
		frappe.throw("Unsupported Ask UCC module.")
	if not question:
		frappe.throw("Please enter a question.")
	if not record:
		frappe.throw("Please select a record.")

	module_config = _ask_ucc_orchestration.MODULES[module]
	result = _ask_ucc_orchestration.ask(module, question, record)
	conversation = _ask_ucc_conversations.persist_turn(
		module_config["label"], module_config["doctype"], record, question, result,
	)
	return _ask_ucc_contracts.build_response(module, conversation, result)


@frappe.whitelist()
def search_ask_ucc_records(module, term=None):
	"""Record-picker search for the Ask UCC tab.

	The legacy picker bulk-loaded up to 5000 records into the browser and
	filtered them client-side (custom-html-block/JAVASCRIPT.js's
	uniqueStudentsFromRoll). Same *behaviour* here -- match the human name
	as well as the record id, so typing "Mei" finds EDU-APP-2025-00001 --
	but done server-side, so no bulk personal data crosses to the browser
	just to power a search box.

	Which fields are searched and returned comes from the fixed MODULES
	registry, never from the caller: a request cannot ask this to search or
	disclose an arbitrary field. frappe.get_list applies ordinary
	permissions, so a user only ever sees records they could already read.
	"""
	module = frappe.utils.cstr(module).strip()
	term = frappe.utils.cstr(term).strip()
	if module not in _ask_ucc_orchestration.MODULES:
		frappe.throw("Unsupported Ask UCC module.")
	if not term:
		return {"ok": True, "records": []}

	config = _ask_ucc_orchestration.MODULES[module]
	search_fields = config["search_fields"]
	label_fields = config.get("label_fields") or [config.get("label_field")]
	label_fields = [f for f in label_fields if f]

	fields = ["name"]
	for fieldname in search_fields + label_fields:
		if fieldname not in fields:
			fields.append(fieldname)

	meta = frappe.get_meta(config["doctype"])
	fields = [f for f in fields if f == "name" or meta.has_field(f)]
	or_filters = [[f, "like", "%" + term + "%"] for f in search_fields if f == "name" or meta.has_field(f)]

	try:
		rows = frappe.get_list(
			config["doctype"], fields=fields, or_filters=or_filters,
			order_by="modified desc", limit_page_length=10,
		) or []
	except Exception as error:
		if _is_permission_error(error):
			return {"ok": True, "records": [], "status": "permission_denied"}
		return {"ok": True, "records": [], "status": "unavailable"}

	records = []
	for row in rows:
		parts = []
		for fieldname in label_fields:
			value = frappe.utils.cstr(row.get(fieldname)).strip()
			if value and value not in parts:
				parts.append(value)
		records.append({"id": row.get("name"), "label": " ".join(parts) or row.get("name")})
	return {"ok": True, "records": records}


@frappe.whitelist()
def get_ask_ucc_modules():
	"""Which Ask UCC modules this user's roles allow the interface to build,
	plus each one's record DocType and its guided-question categories (the
	legacy "FAQ" buttons, see ask_ucc/guided_questions.py). Interface composition only -- same contract as
	get_dashboard_access(), which is where the gating actually comes from."""
	access = _get_dashboard_access()
	allowed = access.get("ask_ucc_modules") or {}
	return {
		"ok": True,
		"modules": [
			{
				"key": key,
				"label": config["label"],
				"doctype": config["doctype"],
				"categories": _ask_ucc_guided.supported_questions(key),
			}
			for key, config in _ask_ucc_orchestration.MODULES.items()
			if allowed.get(key)
		],
	}
