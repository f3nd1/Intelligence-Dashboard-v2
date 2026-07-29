"""Shared request-payload parsing for the per-criterion analytics APIs.

Extracted from `server-scripts/UCC Analytics - Criterion 1.py:24-61`,
diffed against Criterion 3's equivalent block during the Phase 4 plan: the
*only* difference between them was the default `subcriterion` string
(`"1.1.1"` vs `"3.1.1"`), and `ALLOWED_ACTIONS` is identical across six of
seven criteria (Criterion 3 alone adds `"question_catalogue"`). Parameterised
by exactly those two things -- everything else (JSON parsing, clamping,
error message shape) is unchanged from the legacy source, not redesigned.
"""

import json

import frappe


def parse_payload(payload_input, default_subcriterion, allowed_actions, criterion_label):
	"""Parse and validate a criterion API's request payload.

	:param payload_input: the raw value of `frappe.form_dict.get("payload")`
		-- a JSON string, a dict, or falsy. Callers pass this straight
		through rather than pre-parsing it, so this function can be
		exercised directly in tests without stubbing `frappe.form_dict`.
	:param default_subcriterion: e.g. `"1.1.1"` -- used when the payload
		doesn't specify one.
	:param allowed_actions: the criterion's own `ALLOWED_ACTIONS` list.
	:param criterion_label: e.g. `"Criterion 1"` -- used only to build the
		same "Unsupported {label} action." message the legacy script threw.
	"""
	payload_input = payload_input or {}
	try:
		payload = json.loads(payload_input) if isinstance(payload_input, str) else payload_input
	except Exception:
		payload = {}
	if not isinstance(payload, dict):
		payload = {}
	action = payload.get("action") or "summary"
	subcriterion = payload.get("subcriterion") or default_subcriterion
	filters = payload.get("filters") or {}
	if not isinstance(filters, dict):
		filters = {}
	metric_id = payload.get("metric_id")
	page = payload.get("page") or 1
	page_size = payload.get("page_size") or 50
	row_limit = payload.get("limit") or 2000

	try:
		page = max(1, int(page))
	except Exception:
		page = 1

	try:
		page_size = max(1, min(int(page_size), 200))
	except Exception:
		page_size = 50

	try:
		row_limit = max(1, min(int(row_limit), 5000))
	except Exception:
		row_limit = 2000

	if action not in allowed_actions:
		frappe.throw("Unsupported " + criterion_label + " action.")

	return {
		"action": action,
		"subcriterion": subcriterion,
		"filters": filters,
		"metric_id": metric_id,
		"page": page,
		"page_size": page_size,
		"row_limit": row_limit,
	}
