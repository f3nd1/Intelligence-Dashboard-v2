"""Shared Ask UCC response contract
(docs/architecture/ask-ucc-phase-plan.md §2.4) -- the shape every module's
whitelisted method returns, not reinvented per module. Deliberately not
the Analytics contract (analytics/contracts.py) -- a chat turn's shape
(answer/facts/sources/ai_status) doesn't fit the criterion catalogue shape
(metrics/questions/requirements), so this is a new, smaller contract
rather than a forced reuse of one that doesn't match.
"""

import frappe

from ucc_intelligence.ai.orchestration import MODULES
from ucc_intelligence.ask_ucc import data_checks

BLOCKED_STATUSES = ("permission_denied", "not_found", "unavailable")

# The record summary the Ask UCC context panel shows beside the conversation:
# who/what is currently selected, and the handful of fields that frame every
# answer about it. Taken from the primary tool's FULL result, never from the
# narrowed `facts` -- a question routed to one field must not empty the panel.
#
# A fixed list per module, not "whatever the tool returned": the panel is a
# summary, and a tool gaining a field should not silently push more of a
# person's record onto the screen. Ordinary Frappe permissions already decided
# whether the primary tool could read the record at all.
CONTEXT_FIELDS = {
	"student_journey": [
		("student_name", "Name"), ("student_applicant", "Record"),
		("academic_status", "Status"), ("nationality", "Nationality"),
		("programme", "Course"), ("commencement_date", "Commencement"),
		("completion_date", "Completion"), ("graduated", "Graduated"),
	],
	"recruitment_agent": [
		("agent_name", "Name"), ("agent_contract", "Record"),
		("contract_status", "Status"), ("identifier", "Identifier"),
		("commencement_date", "Commencement"), ("expiry_date", "Expiry"),
	],
	"quality_action": [
		("title", "Subject"), ("quality_action", "Record"),
		("open_count", "Open actions"), ("completed_count", "Completed"),
		("overdue_count", "Overdue"),
	],
}


def build_record_context(module_key, primary):
	"""Name/label pairs for the context panel, skipping anything the record
	does not carry. Returns None when the record was not readable -- the panel
	then shows nothing rather than a shell of empty rows."""
	if not primary or primary.get("status") != "available":
		return None
	fields = []
	for key, label in CONTEXT_FIELDS.get(module_key, []):
		if key not in primary:
			continue
		value = primary.get(key)
		if isinstance(value, bool):
			value = "Yes" if value else "No"
		fields.append({"key": key, "label": label, "value": value})
	return {
		"doctype": MODULES[module_key]["doctype"],
		"record": primary.get(MODULES[module_key]["record_key"]),
		"fields": fields,
	}


def build_response(module_key, conversation, result):
	module = MODULES[module_key]
	facts = result.get("facts") or {}
	# The source link comes from the primary tool's FULL result, not from
	# `facts`. A narrowly-routed question ("what is this student's
	# nationality?") may not display the primary tool at all, or may display
	# only two of its fields -- neither of which should cost the answer its
	# link back to the record it came from (CLAUDE.md §8.4).
	primary = result.get("primary") or facts.get(module["primary_tool"]) or {}

	if primary.get("status") == "available":
		sources = [{
			"doctype": module["doctype"],
			"record": primary.get(module["record_key"]),
			"status": "available",
		}]
	elif primary.get("status") in BLOCKED_STATUSES:
		sources = [{
			"doctype": module["doctype"],
			"record": None,
			"status": primary.get("status"),
			"message": primary.get("message"),
		}]
	else:
		sources = []

	return {
		"ok": True,
		"module": module_key,
		"conversation_id": conversation.name if conversation else None,
		"ai_status": result.get("ai_status"),
		# Which KIND of answer this is, decided server-side and never inferred
		# from the text: "verified_record" (fields read from the record, no
		# model involved), "ai_analysis" (a model interpreted those fields), or
		# "unavailable". The interface labels the card from this and nothing
		# else, so the label can never drift from what actually happened.
		"answer_kind": result.get("answer_kind") or "unavailable",
		"answer": result.get("answer"),
		"answer_error": result.get("answer_error"),
		"facts": facts,
		"sources": sources,
		"record_context": build_record_context(module_key, primary),
		# Deterministic field-vs-field checks, not a model and not a fact --
		# see ask_ucc/data_checks.py.
		"warnings": data_checks.run(module_key, primary),
		"checked_at": frappe.utils.now(),
	}
