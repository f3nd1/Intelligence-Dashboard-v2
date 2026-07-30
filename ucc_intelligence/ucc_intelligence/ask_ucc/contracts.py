"""Shared Ask UCC response contract
(docs/architecture/ask-ucc-phase-plan.md §2.4) -- the shape every module's
whitelisted method returns, not reinvented per module. Deliberately not
the Analytics contract (analytics/contracts.py) -- a chat turn's shape
(answer/facts/sources/ai_status) doesn't fit the criterion catalogue shape
(metrics/questions/requirements), so this is a new, smaller contract
rather than a forced reuse of one that doesn't match.
"""

from ucc_intelligence.ai.orchestration import MODULES

BLOCKED_STATUSES = ("permission_denied", "not_found", "unavailable")


def build_response(module_key, conversation, result):
	module = MODULES[module_key]
	facts = result.get("facts") or {}
	primary = facts.get(module["primary_tool"]) or {}

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
		"answer": result.get("answer"),
		"answer_error": result.get("answer_error"),
		"facts": facts,
		"sources": sources,
		"warnings": [],
	}
