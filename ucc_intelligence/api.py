import frappe

from ucc_intelligence.analytics import criterion_1, criterion_2, criterion_3, criterion_4, criterion_6, criterion_7
from ucc_intelligence.analytics.request import parse_payload
from ucc_intelligence.permissions.access import get_dashboard_access as _get_dashboard_access

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
