"""Assembles retrieved facts + the user's question into an AI explanation
call, then validates the result before it's ever returned
(docs/architecture/ask-ucc-phase-plan.md §2.1 steps 6-7).

v1 scope: Quality Action only, and deterministically calls BOTH of that
module's tools every time rather than having the model select from an
allowlist via function-calling -- with only two tools, both cheap
DB-backed lookups, there's nothing to gain from model-driven selection
yet, and one less moving part to get wrong for a first build. Revisit
once a module has enough tools that calling all of them unconditionally
stops being the practical choice.

Permission gating is the caller's job (api.py), not this module's --
by the time ask_quality_action() runs, quality_action_tools.
get_quality_action_summary() has already applied ordinary Frappe
permissions via frappe.get_doc(); this module only decides what to do
with the result.
"""

import json

from ucc_intelligence.ai import client as ai_client
from ucc_intelligence.ai import guardrails
from ucc_intelligence.ask_ucc import quality_action as quality_action_tools

SYSTEM_PROMPT = (
	"You are Ask UCC, an assistant for United Ceres College staff. Answer the "
	"question using ONLY the facts supplied below, in the 'FACTS' section. "
	"Never state anything not present in those facts. Never invent a record "
	"name, status, date, or person that is not in the facts. If the facts do "
	"not answer the question, say so plainly rather than guessing. Be concise "
	"and refer to the Quality Action by its title."
)


def ask_quality_action(question, quality_action_name):
	"""Returns {ai_status, answer, answer_error, facts, tools_called,
	known_record_names}. ai_status is one of: "available" (answer is
	populated and guardrail-checked), "disabled"/"unavailable" (AI not
	configured -- facts are still populated, progressive enhancement),
	"guardrail_blocked"/"error" (AI ran but its output was rejected or the
	call failed), or the tool's own status ("not_found"/"permission_denied"/
	"unavailable") when the record itself couldn't be resolved."""
	summary = quality_action_tools.get_quality_action_summary(quality_action_name)
	tools_called = ["get_quality_action_summary"]

	if summary.get("status") != "available":
		return {
			"ai_status": summary.get("status"),
			"answer": None,
			"answer_error": summary.get("message"),
			"facts": {"summary": summary},
			"tools_called": tools_called,
			"known_record_names": [],
		}

	closure = quality_action_tools.assess_quality_action_closure(quality_action_name)
	tools_called.append("assess_quality_action_closure")

	facts = {"summary": summary, "closure_assessment": closure}
	known_record_names = [quality_action_name, summary.get("title")]

	if not ai_client.is_enabled():
		return {
			"ai_status": "disabled",
			"answer": None,
			"answer_error": None,
			"facts": facts,
			"tools_called": tools_called,
			"known_record_names": known_record_names,
		}

	user_prompt = "QUESTION: " + question + "\n\nFACTS (JSON):\n" + json.dumps(facts, default=str)
	completion = ai_client.complete(SYSTEM_PROMPT, user_prompt)

	if not completion.get("ok"):
		return {
			"ai_status": completion.get("status") or "error",
			"answer": None,
			"answer_error": completion.get("message"),
			"facts": facts,
			"tools_called": tools_called,
			"known_record_names": known_record_names,
		}

	valid, reason = guardrails.validate(completion["text"], known_record_names)
	if not valid:
		return {
			"ai_status": "guardrail_blocked",
			"answer": None,
			"answer_error": reason,
			"facts": facts,
			"tools_called": tools_called,
			"known_record_names": known_record_names,
		}

	return {
		"ai_status": "available",
		"answer": {
			"text": completion["text"],
			"model": completion.get("model"),
			"latency_ms": completion.get("latency_ms"),
			"token_usage": completion.get("token_usage"),
		},
		"answer_error": None,
		"facts": facts,
		"tools_called": tools_called,
		"known_record_names": known_record_names,
	}
