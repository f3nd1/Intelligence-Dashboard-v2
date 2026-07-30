import frappe

from ucc_intelligence.ai import orchestration as _ask_ucc_orchestration
from ucc_intelligence.analytics import admission_intelligence_embed, criterion_1, criterion_2, criterion_3, criterion_4, criterion_5, criterion_6, criterion_7
from ucc_intelligence.analytics.request import parse_payload
from ucc_intelligence.ask_ucc import contracts as _ask_ucc_contracts
from ucc_intelligence.ask_ucc import conversations as _ask_ucc_conversations
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

# Criterion 4 is a partial, Insights-informed implementation (admission_intelligence
# only, see analytics/criterion_4.py's module docstring) -- only "summary" does
# anything meaningful right now, so that's all that's allowed rather than
# claiming support for actions with no real data behind them yet.
CRITERION_4_ALLOWED_ACTIONS = ["summary"]

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
	return criterion_1.run(**parsed)


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
	return criterion_2.run(**parsed)


@frappe.whitelist()
def get_admission_intelligence():
	"""Option B live embed for Criterion 4's admission_intelligence (4 KPIs
	+ 6 chart series) -- executes real Insights Query v3 records server-side,
	permission-checked per request. See
	ucc_intelligence/ucc_intelligence/analytics/admission_intelligence_embed.py's
	module docstring for the full architecture and the
	Insights Settings.apply_user_permissions dependency. This IS wired into
	sophia_analytics.js (unlike every other method in this file) -- Criterion
	4's other ~40 metrics still come from the legacy Server Script via
	ucc_analytics_criterion_4, untouched."""
	return admission_intelligence_embed.run()


@frappe.whitelist()
def get_criterion_4():
	"""Partial, Insights-informed Criterion 4 implementation --
	admission_intelligence only (4 KPIs + 6 chart series). Not a port of
	server-scripts/UCC Analytics - Criterion 4.py -- see
	ucc_intelligence/ucc_intelligence/analytics/criterion_4.py's module
	docstring for the architecture and what's still open. Not yet called by
	the frontend -- sophia_analytics.js still calls the legacy Server Script
	directly."""
	parsed = parse_payload(
		frappe.form_dict.get("payload"),
		default_subcriterion="4.1.1",
		allowed_actions=CRITERION_4_ALLOWED_ACTIONS,
		criterion_label="Criterion 4",
	)
	return criterion_4.run(**parsed)


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
	return criterion_3.run(**parsed)


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

	return criterion_5.run(question_id=payload.get("question_id"), **parsed)


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
	return criterion_6.run(**parsed)


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
	return criterion_7.run(**parsed)


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
def get_ask_ucc_modules():
	"""Which Ask UCC modules this user's roles allow the interface to build,
	plus each one's record DocType so the frontend's record picker knows what
	to search. Interface composition only -- same contract as
	get_dashboard_access(), which is where the gating actually comes from."""
	access = _get_dashboard_access()
	allowed = access.get("ask_ucc_modules") or {}
	return {
		"ok": True,
		"modules": [
			{"key": key, "label": config["label"], "doctype": config["doctype"]}
			for key, config in _ask_ucc_orchestration.MODULES.items()
			if allowed.get(key)
		],
	}
