"""Read-only status/summary logic for the UCC Intelligence Settings page
(docs/architecture/settings-page-plan.md). Every check here either reuses
an existing mechanism directly or is a trivial, honest presence check --
nothing here claims a feature is "healthy" beyond what's actually
verifiable with no AI client, no memory storage, and no monitoring engine
built yet (see the plan doc's three-tier breakdown).

Access to this data is gated at the whitelisted call site (api.py's
get_settings_status, System Manager only) rather than here, because the
individual reads below are NOT all self-gating the way an ordinary
frappe.get_list call is: load_rows() reads with ignore_permissions=True
by its own existing design (permissions/access.py), and a raw
frappe.db.get_value/get_singles_dict lookup has no row-level permission
concept at all. This module returns more than any one signed-in user
should necessarily see (every configured role's access, not just their
own), so the gate belongs on the endpoint, not assumed from the reads.
"""

import frappe

from ucc_intelligence.analytics.admission_intelligence_embed import CHART_TITLES
from ucc_intelligence.permissions.access import load_rows

AI_API_KEY_SITE_CONFIG_KEY = "ucc_intelligence_ai_api_key"


def get_dashboard_access_summary():
	"""Reshape permissions.access.load_rows() for display -- UCC Dashboard
	Access remains the only source of truth for role access; this does not
	duplicate or reimplement its resolution logic."""
	rows = load_rows()
	roles = []
	for row in rows:
		role = row.get("role")
		if role and role not in roles:
			roles.append(role)
	return {"configured_role_count": len(roles), "roles": roles}


def get_insights_chart_status():
	"""Which of admission_intelligence's Insights Query v3 charts exist --
	the same title-based lookup admission_intelligence_embed.run_chart_query()
	already does at request time, reused here for a build-status summary."""
	charts = []
	built = 0
	for data_key, title in CHART_TITLES.items():
		query_name = frappe.db.get_value("Insights Query v3", {"title": title}, "name")
		if query_name:
			built += 1
		charts.append({"data_key": data_key, "title": title, "built": bool(query_name)})
	return {"built_count": built, "total_count": len(CHART_TITLES), "charts": charts}


def get_insights_permission_setting():
	"""Insights Settings.apply_user_permissions -- the single site-wide
	toggle every embedded chart's permission enforcement depends on
	(admission_intelligence_embed.py's module docstring). Surfaced here
	because a settings page that omits this is missing the signal most
	likely to matter later."""
	value = frappe.db.get_singles_dict("Insights Settings").get("apply_user_permissions")
	return {"apply_user_permissions": bool(value)}


def get_ai_provider_configured():
	"""Presence check only -- whether an AI provider secret exists in site
	config, never its value. Not "the key works": no AI client exists yet
	to test-call it. Deliberately does not read from the Settings DocType
	itself -- per the plan, no secret field lives there."""
	configured = bool(frappe.conf.get(AI_API_KEY_SITE_CONFIG_KEY))
	return {"configured": configured, "site_config_key": AI_API_KEY_SITE_CONFIG_KEY}


def get_db_reachable():
	"""Trivial reachability check -- the same style resolve_source()
	already uses in every criterion module (a cheap get_meta call)."""
	try:
		frappe.get_meta("Student Applicant")
		return True
	except Exception:
		return False



def get_ai_prompt_status():
	"""Whether the AI is running on reviewed wording. A placeholder prompt is
	safe (the factual constraints are not the part awaiting review) but staff
	are reading engineering-authored tone, and that should be visible in the
	product rather than only in ai/prompts.py's docstring."""
	try:
		from ucc_intelligence.ai import prompts
		return prompts.get_prompt_status()
	except Exception:
		return {"placeholder_count": None, "all_reviewed": None, "note": "Prompt status unavailable."}


def get_chart_layer_status():
	"""How much of the chart layer is genuinely on Insights. Reported as a
	count rather than a claim, so migration progress is readable."""
	try:
		from ucc_intelligence.analytics import chart_registry
		return chart_registry.counts()
	except Exception:
		return {"total": None, "real": None, "placeholder": None}

def get_status_summary():
	return {
		"ok": True,
		"generated_at": frappe.utils.now(),
		"dashboard_access": get_dashboard_access_summary(),
		"insights_charts": get_insights_chart_status(),
		"insights_permission_setting": get_insights_permission_setting(),
		"ai_provider_configured": get_ai_provider_configured(),
		"ai_prompts": get_ai_prompt_status(),
		"chart_layer": get_chart_layer_status(),
		"db_reachable": get_db_reachable(),
	}
