"""Dashboard access resolution.

Ported from server-scripts/UCC Dashboard Access.py (Phase 2). Returns which
dashboard workspaces and criteria the signed-in user's roles allow the
interface to BUILD. This controls user-interface composition only.

It does not read, filter or expose any business data, and it neither
consults nor modifies Frappe's permission system. Every data read elsewhere
in the platform remains subject to the user's own DocType permissions
exactly as before. Hiding a tab does not grant or remove access to anything;
a user who reaches a hidden area by other means is still stopped by Frappe.

Configuration DocType: UCC Dashboard Access (see
ucc_intelligence/ucc_intelligence/sophia/doctype/ucc_dashboard_access/).
Newly created, app-managed -- verified 2026-07-26 that no such DocType
previously existed on ucc.local.
"""

import frappe

from ucc_intelligence.logging.audit import log_access_check

CRITERION_KEYS = [
	"criterion_1", "criterion_2", "criterion_3", "criterion_4",
	"criterion_5", "criterion_6", "criterion_7",
]
WORKSPACE_FIELDS = {
	"analytics": "show_analytics",
	"explore": "show_explore",
	"ask": "show_ask_ucc",
}
SHOW_EVERYTHING = "Show everything"
SHOW_NOTHING = "Show nothing"

ACCESS_FIELDS = [
	"name", "role", "enabled", "default_when_unconfigured",
	"show_analytics", "show_explore", "show_ask_ucc",
	"show_criterion_1", "show_criterion_2", "show_criterion_3",
	"show_criterion_4", "show_criterion_5", "show_criterion_6",
	"show_criterion_7", "notes",
]


def clean_text(value):
	if value is None:
		return ""
	return str(value).strip()


def is_checked(value):
	if value in [None, "", 0, "0", False]:
		return False
	if clean_text(value).lower() in ["false", "no", "0", "none", "null", "unchecked"]:
		return False
	return True


def everything_visible():
	payload = {"workspaces": {}, "criteria": {}}
	for workspace_key in WORKSPACE_FIELDS:
		payload["workspaces"][workspace_key] = True
	for criterion_key in CRITERION_KEYS:
		payload["criteria"][criterion_key] = True
	return payload


def nothing_visible():
	payload = {"workspaces": {}, "criteria": {}}
	for workspace_key in WORKSPACE_FIELDS:
		payload["workspaces"][workspace_key] = False
	for criterion_key in CRITERION_KEYS:
		payload["criteria"][criterion_key] = False
	return payload


def load_rows():
	# This DocType holds interface configuration only - checkboxes describing
	# which tabs to build. It contains no business data, so it is read with
	# ignore_permissions to keep the configuration readable by the very users it
	# configures. No other read in the platform does this, and this call cannot
	# be used to reach any other DocType.
	#
	# Inherited from the legacy Server Script as-is for migration parity
	# (Felix, 2026-07-26). Review before Phase 13 cutover rather than
	# carrying it forward unexamined -- see CLAUDE.md §1.1.10.
	try:
		return frappe.get_all(
			"UCC Dashboard Access",
			filters={"enabled": 1},
			fields=ACCESS_FIELDS,
			limit_page_length=500,
			ignore_permissions=True,
		) or []
	except Exception:
		return frappe.get_all(
			"UCC Dashboard Access",
			filters={"enabled": 1},
			fields=ACCESS_FIELDS,
			limit_page_length=500,
		) or []


def resolve_default(rows):
	# default_when_unconfigured is intended as one global setting but lives on
	# every row. Only agree to it when every row that sets it agrees. Anything
	# else (nothing set, or rows disagreeing) resolves to the safer
	# "Show everything" rather than guessing which row was meant to win.
	values = []
	for row in rows or []:
		value = clean_text(row.get("default_when_unconfigured"))
		if value and value not in values:
			values.append(value)
	if len(values) == 1 and values[0] == SHOW_NOTHING:
		return [SHOW_NOTHING, False]
	if len(values) > 1:
		return [SHOW_EVERYTHING, True]
	return [SHOW_EVERYTHING, False]


def union_of(rows):
	# A user holding several roles sees the combination of what those roles
	# allow, never the intersection: any role granting a tab is enough.
	payload = nothing_visible()
	for row in rows or []:
		for workspace_key in WORKSPACE_FIELDS:
			if is_checked(row.get(WORKSPACE_FIELDS.get(workspace_key))):
				payload["workspaces"][workspace_key] = True
		for criterion_key in CRITERION_KEYS:
			if is_checked(row.get("show_" + criterion_key)):
				payload["criteria"][criterion_key] = True
	return payload


def assigned_roles(user):
	# frappe.get_roles() returns the EFFECTIVE role set, not the roles listed on
	# the User record. For Administrator it expands to every enabled Role on the
	# site, so ANY configured row would match an administrator and silently
	# apply another role's restriction - the reported bug (see server-scripts
	# commit 49361a8). Match against the Has Role rows instead, which are
	# exactly what the User form shows and what an admin edits. Fall back to
	# get_roles() only if that read fails, so a lookup fault never changes who
	# matches.
	try:
		rows = frappe.get_all(
			"Has Role",
			filters={"parent": user, "parenttype": "User"},
			fields=["role"],
			limit_page_length=500,
			ignore_permissions=True,
		)
	except Exception:
		try:
			rows = frappe.get_all(
				"Has Role",
				filters={"parent": user, "parenttype": "User"},
				fields=["role"],
				limit_page_length=500,
			)
		except Exception:
			return [frappe.get_roles() or [], "effective_roles_fallback"]
	output = []
	for row in rows or []:
		name = clean_text(row.get("role"))
		if name and name not in output:
			output.append(name)
	return [output, "assigned_roles"]


def role_key(value):
	# Role names are matched exactly by Frappe, but a configuration row typed
	# with different casing or a stray space should still match rather than
	# silently never applying.
	return clean_text(value).lower()


def build_response():
	user = frappe.session.user
	roles_result = assigned_roles(user)
	roles = roles_result[0]
	roles_source = roles_result[1]
	role_lookup = []
	for role_name in roles:
		key = role_key(role_name)
		if key and key not in role_lookup:
			role_lookup.append(key)
	rows = load_rows()

	default_result = resolve_default(rows)
	default_value = default_result[0]
	default_ambiguous = default_result[1]

	matched = []
	matched_roles = []
	for row in rows:
		row_role = clean_text(row.get("role"))
		if row_role and role_key(row_role) in role_lookup:
			matched.append(row)
			if row_role not in matched_roles:
				matched_roles.append(row_role)

	if matched:
		payload = union_of(matched)
		applied = "role_configuration"
	elif default_value == SHOW_NOTHING:
		payload = nothing_visible()
		applied = "default_show_nothing"
	else:
		payload = everything_visible()
		applied = "default_show_everything"

	return {
		"ok": True,
		"meta": {
			"api_method": "ucc_intelligence.api.get_dashboard_access",
			"generated_at": frappe.utils.now(),
			"note": "Interface composition only. Data permissions are unchanged.",
		},
		"user": user,
		"roles": roles,
		"roles_source": roles_source,
		"matched_roles": matched_roles,
		"configured_rows": len(rows),
		"applied": applied,
		"default_when_unconfigured": default_value,
		"default_ambiguous": default_ambiguous,
		"workspaces": payload["workspaces"],
		"criteria": payload["criteria"],
	}


def get_dashboard_access():
	"""Business logic entry point. The whitelisted HTTP shim lives in api.py."""
	try:
		result = build_response()
		log_access_check(
			user=result["user"],
			applied=result["applied"],
			matched_roles=result["matched_roles"],
		)
		return result
	except Exception as error:
		# Fail open, always, and deliberately not configurable. This feature only
		# tidies the interface; a lookup fault must never lock anyone out of a
		# dashboard they are otherwise entitled to use. Data remains protected by
		# Frappe's own permissions regardless of what is returned here.
		fallback = everything_visible()
		log_access_check(user=frappe.session.user, applied="error_fail_open", error=error)
		return {
			"ok": True,
			"meta": {
				"api_method": "ucc_intelligence.api.get_dashboard_access",
				"note": "Interface composition only. Data permissions are unchanged.",
			},
			"applied": "error_fail_open",
			"error": str(error),
			"workspaces": fallback["workspaces"],
			"criteria": fallback["criteria"],
		}
