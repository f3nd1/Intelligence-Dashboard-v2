"""The fixed allowlist of things the platform may ever propose to do
(CLAUDE.md Phase 12).

WHY AN ALLOWLIST, NOT A CAPABILITY
CLAUDE.md §8.6 is explicit: the AI must not "accept a user-provided method
path" or "execute arbitrary SQL". So an action is not a function the model
names -- it is an entry in this dict, chosen by id. A proposal naming an
action_type that is not a key here cannot be created at all; there is no
path from model output to code except through this table.

ACTION LEVELS -- CLAUDE.md §12
  0  Read only               explain, summarise. No record ever changes.
  1  Draft only              produce text a human will copy, edit and send.
  2  Confirm before execute  the system performs it, but only after a named
                             human approves the exact payload.
  3  Policy-approved auto    NOT IMPLEMENTED.
  4  Prohibited              NOT IMPLEMENTED.

Every action below is level 1 or 2. Nothing in this file can run without a
human moving the request through the approval workflow first, and the
execute step re-checks permissions at that moment rather than trusting the
check made when it was proposed.

PLACEHOLDER ACTIONS
Most entries are marked PLACEHOLDER: the shape, level, permission and audit
trail are real and tested, but the body either produces draft text for a
human or is deliberately not wired to an external system. Jira and email
sending need credentials and are explicitly out of scope. A placeholder
executor NEVER pretends to have done something -- it returns a result
saying plainly what it did and did not do.
"""

import json

import frappe

LEVEL_DRAFT_ONLY = 1
LEVEL_CONFIRM_BEFORE_EXECUTE = 2


def _draft_reminder(request):
	"""PLACEHOLDER EXECUTOR -- level 1, produces text only.

	Writes nothing anywhere. The 'execution' of a draft action is producing
	the draft; a human then decides what to do with it. That is the whole
	point of level 1 and why it is the safe default.
	"""
	payload = json.loads(request.payload_json or "{}")
	return {
		"ok": True,
		"result": (
			"DRAFT ONLY -- nothing was sent. Suggested reminder text:\n\n"
			+ (payload.get("draft_text") or "(no draft text supplied)")
		),
		"rollback": "Nothing to roll back: this action only produced text.",
	}


def _create_internal_task(request):
	"""PLACEHOLDER EXECUTOR -- level 2, creates a Frappe ToDo.

	A real internal task, deliberately using Frappe's own ToDo rather than
	Jira: Jira needs credentials and is out of scope. Written as the
	approving user, so ordinary permissions apply -- no ignore_permissions.
	"""
	payload = json.loads(request.payload_json or "{}")
	todo = frappe.get_doc({
		"doctype": "ToDo",
		"description": payload.get("description") or request.title,
		"reference_type": request.target_doctype or None,
		"reference_name": request.target_record or None,
		"allocated_to": payload.get("assign_to") or frappe.session.user,
		"priority": payload.get("priority") or "Medium",
	}).insert()
	return {
		"ok": True,
		"result": "Created ToDo %s" % todo.name,
		"rollback": "Delete ToDo %s" % todo.name,
	}


def _flag_monitoring_finding(request):
	"""Level 2. Suppresses a monitoring finding WITH a recorded reason.

	Included because it is the one write the platform genuinely needs today
	and it is safely reversible: suppression never deletes a finding, and
	monitoring/engine.py refuses to resurrect a suppressed one.
	"""
	payload = json.loads(request.payload_json or "{}")
	reason = payload.get("suppression_reason")
	if not reason:
		return {"ok": False, "result": "A suppression reason is required.", "rollback": ""}
	finding = frappe.get_doc("UCC Monitoring Finding", request.target_record)
	previous = finding.status
	finding.status = "Suppressed"
	finding.suppression_reason = reason
	finding.save()
	return {
		"ok": True,
		"result": "Finding %s suppressed." % finding.name,
		"rollback": "Set UCC Monitoring Finding %s back to %r." % (finding.name, previous),
	}


ACTIONS = {
	"draft_reminder": {
		"label": "Draft a reminder",
		"level": LEVEL_DRAFT_ONLY,
		"placeholder": True,
		"description": "PLACEHOLDER: produces reminder text for a human to send. Sends nothing.",
		"target_doctype": None,
		"execute": _draft_reminder,
	},
	"draft_quality_action": {
		"label": "Draft a Quality Action",
		"level": LEVEL_DRAFT_ONLY,
		"placeholder": True,
		"description": "PLACEHOLDER: drafts the wording of a Quality Action. Creates no record.",
		"target_doctype": "Quality Action",
		"execute": _draft_reminder,
	},
	"draft_audit_evidence_list": {
		"label": "Draft an audit evidence list",
		"level": LEVEL_DRAFT_ONLY,
		"placeholder": True,
		"description": "PLACEHOLDER: lists the evidence an auditor would ask for. Gathers nothing.",
		"target_doctype": None,
		"execute": _draft_reminder,
	},
	"create_internal_task": {
		"label": "Create an internal task",
		"level": LEVEL_CONFIRM_BEFORE_EXECUTE,
		"placeholder": False,
		"description": "Creates a Frappe ToDo after approval. Jira is out of scope (needs credentials).",
		"target_doctype": None,
		"execute": _create_internal_task,
	},
	"suppress_monitoring_finding": {
		"label": "Suppress a monitoring finding",
		"level": LEVEL_CONFIRM_BEFORE_EXECUTE,
		"placeholder": False,
		"description": "Marks a finding suppressed with a recorded reason. Never deletes it.",
		"target_doctype": "UCC Monitoring Finding",
		"execute": _flag_monitoring_finding,
	},
}


def get(action_type):
	return ACTIONS.get(action_type)


def summary():
	return {
		"total": len(ACTIONS),
		"placeholder": sum(1 for a in ACTIONS.values() if a["placeholder"]),
		"max_level": max(a["level"] for a in ACTIONS.values()),
		"levels": sorted({a["level"] for a in ACTIONS.values()}),
	}
