"""Propose / approve / execute, on Frappe's own Workflow (CLAUDE.md Phase 12).

WHY FRAPPE WORKFLOW RATHER THAN AN APPROVAL ENGINE
Felix's decision, and the right one. Frappe already has states, transitions,
role-gated actions, self-approval control and an audit trail on every
transition. Hand-rolling that would mean reimplementing -- and getting wrong
-- something the framework does properly. The workflow lives in
fixtures/workflow.json; this module never sets `workflow_state` itself, it
calls frappe.model.workflow.apply_workflow and lets the framework decide
whether the transition is allowed.

THE SAFETY PROPERTIES, AND WHERE EACH IS ENFORCED
  Nothing executes without a human       the workflow. Execute is only
                                         reachable from Approved, and only a
                                         human transition reaches Approved.
  Approver != proposer                   the workflow's allow_self_approval:
                                         0 on the Approve transition.
  Only allowlisted actions               registry.get() here; an unknown
                                         action_type is refused at propose.
  Permissions re-checked at EXECUTE      execute() below. The check made when
                                         it was proposed may be stale by the
                                         time someone approves it -- roles
                                         change, records move.
  No duplicate execution                 idempotency key + a state check.
                                         Clicking Execute twice runs once.
  Audit                                  UCC AI Usage Log, plus Frappe's own
                                         version history on every transition.
"""

import hashlib
import json

import frappe

from ucc_intelligence.actions import registry

DOCTYPE = "UCC AI Action Request"
WORKFLOW_NAME = "UCC AI Action Approval"

STATE_DRAFT = "Draft"
STATE_PENDING = "Pending Approval"
STATE_APPROVED = "Approved"
STATE_EXECUTED = "Executed"


def idempotency_key(action_type, target_doctype, target_record, payload):
	"""Same proposal twice = same key = one record.

	Hashed rather than concatenated because the payload can be long and a
	DocType field has a length limit; a hash also avoids putting proposal
	content into a field that is indexed and unique.
	"""
	blob = json.dumps(
		[action_type, target_doctype or "", target_record or "", payload or {}],
		sort_keys=True, default=str,
	)
	return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def propose(action_type, title, payload=None, target_record=None, reason="", sources=None):
	"""Create a request in Draft. Nothing happens yet, by construction.

	Refuses an action_type that is not in the registry -- that is the one
	place model output could otherwise reach code by name.
	"""
	action = registry.get(action_type)
	if not action:
		frappe.throw(frappe._("Unknown action type."))
	if action["level"] > registry.LEVEL_CONFIRM_BEFORE_EXECUTE:
		# Levels 3 and 4 are not implemented and must not become reachable by
		# someone adding a registry entry without reading the file.
		frappe.throw(frappe._("Action level {0} is not implemented.").format(action["level"]))

	payload = payload or {}
	if isinstance(payload, str):
		payload = frappe.parse_json(payload) or {}

	target_doctype = action.get("target_doctype")
	if target_doctype and target_record:
		# Fail now, not at execution: proposing an action against a record the
		# proposer cannot even read should never reach an approver's queue.
		frappe.get_doc(target_doctype, target_record).check_permission("read")

	key = idempotency_key(action_type, target_doctype, target_record, payload)
	existing = frappe.db.get_value(DOCTYPE, {"idempotency_key": key}, "name")
	if existing:
		return {"ok": True, "action_request": existing, "created": False,
			"message": "An identical request already exists."}

	doc = frappe.get_doc({
		"doctype": DOCTYPE,
		"action_type": action_type,
		"title": title or action["label"],
		"reason": reason,
		"target_doctype": target_doctype,
		"target_record": target_record,
		"payload_json": frappe.as_json(payload),
		"sources_json": frappe.as_json(sources or []),
		"action_level": "%d - %s" % (action["level"],
			"Draft only" if action["level"] == registry.LEVEL_DRAFT_ONLY else "Confirm before execution"),
		"requested_by": frappe.session.user,
		"idempotency_key": key,
		"workflow_state": STATE_DRAFT,
		"execution_status": "Not Executed",
	}).insert()

	return {"ok": True, "action_request": doc.name, "created": True, "state": doc.workflow_state}


def transition(action_request, workflow_action):
	"""Move a request through the workflow.

	Deliberately a thin pass-through to frappe.model.workflow.apply_workflow:
	it is what enforces which roles may take which transition and whether
	self-approval is allowed. Re-implementing that check here would create a
	second, weaker gate that could disagree with the workflow.
	"""
	from frappe.model.workflow import apply_workflow

	doc = frappe.get_doc(DOCTYPE, action_request)
	apply_workflow(doc, workflow_action)
	if workflow_action == "Approve":
		frappe.db.set_value(DOCTYPE, doc.name, "approved_by", frappe.session.user)
	doc.reload()
	return {"ok": True, "action_request": doc.name, "state": doc.workflow_state}


def execute(action_request):
	"""Carry out an APPROVED request. The only place anything is written.

	Four gates, in order, and each one has a reason:
	  1. state must be Approved     -- a human said yes
	  2. not already executed       -- repeated clicks run once
	  3. action still allowlisted   -- the registry may have changed
	  4. permissions RE-checked     -- as the executing user, now, not as the
	                                   proposer, then
	"""
	doc = frappe.get_doc(DOCTYPE, action_request)

	# Already-executed is checked FIRST, before the state check. A successful
	# execution moves the request to Executed, so checking state first would
	# make a second click throw "this is Executed, not Approved" -- alarming,
	# and wrong: nothing went wrong, the work was simply already done. Both
	# orderings are equally safe; only this one gives an honest answer.
	if doc.execution_status == "Succeeded":
		return {"ok": True, "action_request": doc.name, "already_executed": True,
			"result": doc.execution_result, "message": "Already executed; nothing was repeated."}
	if doc.workflow_state != STATE_APPROVED:
		frappe.throw(frappe._("This request is {0}, not Approved. Nothing was executed.").format(doc.workflow_state))

	action = registry.get(doc.action_type)
	if not action:
		frappe.throw(frappe._("This action type is no longer available."))

	if doc.target_doctype and doc.target_record:
		# The gap between approval and execution is where permissions go
		# stale. Checked here, as the user actually pressing Execute.
		frappe.get_doc(doc.target_doctype, doc.target_record).check_permission("write")

	try:
		outcome = action["execute"](doc)
	except Exception as error:
		doc.execution_status = "Failed"
		doc.execution_result = frappe.utils.cstr(error)[:500]
		doc.executed_at = frappe.utils.now()
		doc.save(ignore_permissions=True)
		frappe.log_error(title="UCC AI action failed: %s" % doc.action_type)
		record_audit(doc, "failed")
		return {"ok": False, "action_request": doc.name, "message": doc.execution_result}

	doc.execution_status = "Succeeded" if outcome.get("ok") else "Failed"
	doc.execution_result = frappe.utils.cstr(outcome.get("result"))[:500]
	doc.rollback_hint = frappe.utils.cstr(outcome.get("rollback"))[:500]
	doc.executed_at = frappe.utils.now()
	doc.save(ignore_permissions=True)

	if outcome.get("ok"):
		transition(doc.name, "Execute")
	record_audit(doc, doc.execution_status.lower())
	return {"ok": bool(outcome.get("ok")), "action_request": doc.name, "result": doc.execution_result,
		"rollback": doc.rollback_hint}


def record_audit(doc, outcome):
	"""CLAUDE.md §12.4. Written with ignore_permissions for the same reason
	the Ask UCC usage log is: an audit trail no role can create is an audit
	trail no role can forge."""
	try:
		frappe.get_doc({
			"doctype": "UCC AI Usage Log",
			"user": frappe.session.user,
			"module": "controlled_action",
			"action_proposed": doc.action_type,
			"approval_status": doc.workflow_state,
			"execution_result": outcome,
			"source_ids": doc.sources_json,
		}).insert(ignore_permissions=True)
	except Exception:
		# An audit-write failure must not roll back a completed action -- the
		# action happened, and hiding that would be worse than a missing log.
		frappe.log_error(title="UCC AI action audit log failed")


def list_requests(state=None, limit=50):
	filters = {}
	if state:
		filters["workflow_state"] = state
	return frappe.get_list(
		DOCTYPE, filters=filters,
		fields=["name", "action_type", "title", "workflow_state", "action_level",
			"requested_by", "approved_by", "execution_status", "modified"],
		order_by="modified desc",
		limit_page_length=max(1, min(200, frappe.utils.cint(limit) or 50)),
	)
