"""Shared Ask UCC response contract
(docs/architecture/ask-ucc-phase-plan.md §2.4) -- the shape every module's
whitelisted method returns, not reinvented per module. Deliberately not
the Analytics contract (analytics/contracts.py) -- a chat turn's facts
(answer/facts/sources/ai_status) don't fit the criterion catalogue shape
(metrics/questions/requirements), so this is a new, smaller contract
rather than a forced reuse of one that doesn't match.
"""


def build_response(conversation, result):
	facts = result.get("facts") or {}
	summary = facts.get("summary") or {}

	sources = []
	if summary.get("status") == "available":
		sources.append({
			"doctype": "Quality Action",
			"record": summary.get("quality_action"),
			"status": "available",
		})
	elif summary.get("status") in ("permission_denied", "not_found", "unavailable"):
		sources.append({
			"doctype": "Quality Action",
			"record": None,
			"status": summary.get("status"),
			"message": summary.get("message"),
		})

	return {
		"ok": True,
		"conversation_id": conversation.name if conversation else None,
		"ai_status": result.get("ai_status"),
		"answer": result.get("answer"),
		"answer_error": result.get("answer_error"),
		"facts": facts,
		"sources": sources,
		"warnings": [],
	}
