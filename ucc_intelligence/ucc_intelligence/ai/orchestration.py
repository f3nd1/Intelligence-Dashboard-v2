"""Assembles retrieved facts + the user's question into an AI explanation
call, then validates the result before it's ever returned
(docs/architecture/ask-ucc-phase-plan.md §2.1 steps 6-7).

Parametrised by module rather than hardcoded per module: all three Ask UCC
modules (Quality Action, Recruitment Agent, Student Journey) run the exact
same pipeline, differing only in which tool functions they may call and
which record identifiers the guardrail should accept. That's a real,
three-caller generalisation, not a speculative one.

Tool selection is deterministic, never model-driven. A guided question
routes to the specific tool(s) and field(s) it needs
(ask_ucc/guided_questions.QUESTION_ROUTES), mirroring the legacy
assistant's detect_intent -> one focused handler design; a free-typed
question, whose intent we can't infer, falls back to calling every tool.
With 2-4 cheap DB-backed tools per module there's nothing to gain from
model-driven selection and one less moving part to get wrong.

Permission gating is the caller's job (api.py), not this module's -- by
the time a tool runs it has already applied ordinary Frappe permissions
via frappe.get_doc(); this module only decides what to do with the result.
"""

import json

from ucc_intelligence.ai import client as ai_client
from ucc_intelligence.ai import guardrails
from ucc_intelligence.ask_ucc import guided_questions
from ucc_intelligence.ask_ucc import quality_action as quality_action_tools
from ucc_intelligence.ask_ucc import recruitment_agent as recruitment_agent_tools
from ucc_intelligence.ask_ucc import student_journey as student_journey_tools

SYSTEM_PROMPT = (
	"You are Ask UCC, an assistant for United Ceres College staff. Answer the "
	"question using ONLY the facts supplied below, in the 'FACTS' section. "
	"Never state anything not present in those facts. Never invent a record "
	"name, status, date, or person that is not in the facts. If the facts do "
	"not answer the question, say so plainly rather than guessing. Be concise."
)

# module key -> how to run it. `primary_tool` must be the tool that resolves
# the record itself: if it can't (not found / permission denied), the
# remaining tools are skipped, since they'd all fail the same way.
# `record_key` is the field each module's primary tool echoes the record
# name back under -- it differs per module, so it's declared, not guessed.
#
# `search_fields`/`label_field(s)` drive the record picker. Taken from the
# legacy loaders' own field lists (uniqueStudentsFromRoll and the three
# loadX functions in custom-html-block/JAVASCRIPT.js), because the legacy
# picker matched the HUMAN NAME as well as the record id -- typing "Mei"
# had to find EDU-APP-2025-00001. Declared here rather than accepted from
# the caller so a request can never search or return an arbitrary field.
MODULES = {
	"quality_action": {
		"label": "Quality Action",
		"doctype": "Quality Action",
		"tools": quality_action_tools.TOOLS,
		"primary_tool": "get_quality_action_summary",
		"record_key": "quality_action",
		"search_fields": ["name", "custom_subject"],
		"label_field": "custom_subject",
	},
	"recruitment_agent": {
		"label": "Recruitment Agent",
		"doctype": "Agent Contract",
		"tools": recruitment_agent_tools.TOOLS,
		"primary_tool": "get_agent_contract_summary",
		"record_key": "agent_contract",
		"search_fields": ["name", "party_name", "personal_id"],
		"label_field": "party_name",
	},
	"student_journey": {
		"label": "Student Journey",
		"doctype": "Student Applicant",
		"tools": student_journey_tools.TOOLS,
		"primary_tool": "get_student_profile",
		"record_key": "student_applicant",
		"search_fields": ["name", "first_name", "middle_name", "last_name"],
		"label_fields": ["first_name", "middle_name", "last_name"],
	},
}


def known_names_from(primary_result, record_name):
	"""Every identifier the AI is allowed to reference. Includes the human
	name/title as well as the record id -- an answer legitimately says
	"Jane Tan" or the Quality Action's subject, not just "QA-0001"."""
	names = [record_name]
	for key in ("title", "name", "agent_name", "student_name"):
		value = primary_result.get(key)
		if value and value not in names:
			names.append(value)
	return names


def narrow(result, fields):
	"""One tool's output reduced to the fields a question actually asked for.
	`status` is always kept (the renderer and the contract both key off it),
	and so is `note` -- a tool's note is its own caveat about what the numbers
	do and don't prove, so dropping it would strip a caveat from a fact that
	still carries it. A falsy `fields`, or a non-available result, is returned
	untouched."""
	if not fields or result.get("status") != "available":
		return result
	keep = set(fields) | {"status"}
	if "note" in result:
		keep.add("note")
	return {k: v for k, v in result.items() if k in keep}


def ask(module_key, question, record_name):
	"""Returns {ai_status, answer, answer_error, facts, tools_called,
	known_record_names}. ai_status is one of: "available" (answer populated
	and guardrail-checked), "disabled"/"unavailable" (AI not configured --
	facts still populated, progressive enhancement), "guardrail_blocked"/
	"error" (AI ran but its output was rejected or the call failed), or the
	primary tool's own status ("not_found"/"permission_denied"/
	"unavailable") when the record itself couldn't be resolved."""
	module = MODULES[module_key]
	tools = module["tools"]
	primary_tool_name = module["primary_tool"]

	# The primary tool always runs, whatever the route asks for: it is what
	# proves the record exists and that this user may read it, and it supplies
	# the source link and the guardrail's allowed names. Whether it is SHOWN
	# is a separate decision, made by the route below.
	primary_result = tools[primary_tool_name](record_name)
	tools_called = [primary_tool_name]

	if primary_result.get("status") != "available":
		return {
			"ai_status": primary_result.get("status"),
			"answer": None,
			"answer_error": primary_result.get("message"),
			"facts": {primary_tool_name: primary_result},
			"primary": primary_result,
			"tools_called": tools_called,
			"known_record_names": [],
		}

	# A guided question asks for a specific thing; answering it with the whole
	# record is a worse answer, not a more thorough one.
	route = guided_questions.route_for(module_key, question)
	wanted = list(route) if route else list(tools)

	facts = {}
	if primary_tool_name in wanted:
		facts[primary_tool_name] = narrow(primary_result, route and route.get(primary_tool_name))
	for tool_name, tool_function in tools.items():
		if tool_name == primary_tool_name or tool_name not in wanted:
			continue
		result = tool_function(record_name)
		facts[tool_name] = narrow(result, route and route.get(tool_name))
		tools_called.append(tool_name)

	known_record_names = known_names_from(primary_result, record_name)

	if not ai_client.is_enabled():
		return {
			"ai_status": "disabled",
			"answer": None,
			"answer_error": None,
			"facts": facts,
			"primary": primary_result,
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
			"primary": primary_result,
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
			"primary": primary_result,
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
		"primary": primary_result,
		"tools_called": tools_called,
		"known_record_names": known_record_names,
	}


def ask_quality_action(question, quality_action_name):
	"""Kept as a named wrapper: api.py's existing method and its tests call
	this directly, and a one-line alias is cheaper than churning them."""
	return ask("quality_action", question, quality_action_name)
