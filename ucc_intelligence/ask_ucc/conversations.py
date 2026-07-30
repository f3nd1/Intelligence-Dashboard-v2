"""Conversation/message/usage-log persistence shared across every Ask UCC
module -- not Quality-Action-specific, so Recruitment Agent and Student
Journey reuse this unchanged when their turn comes (see
docs/architecture/ask-ucc-phase-plan.md §6).

v1: one `UCC AI Conversation` per (user, module, linked record), reused
across a session rather than a new row per question -- avoids a
conversation-per-question explosion while there's no explicit "start a
new conversation" action exposed to the frontend yet. Revisit once there
is one.

No `ignore_permissions` for Conversation/Message reads or writes below --
`UCC AI Conversation`/`UCC AI Message`'s own DocType permissions grant
`if_owner` access to the "All" role, and every read here is scoped to
`frappe.session.user`'s own records, every write is inserted as the
current user (Frappe sets `owner` automatically) -- so ordinary
permissions already allow exactly what this module does, nothing more.
`UCC AI Usage Log` is the one exception (see record_usage_log()) --
that DocType's own permissions grant no create access to any role by
design (audit log, not user-editable), so its insert is the one place
`ignore_permissions=True` is used, with the justification recorded on
the DocType's own .py controller.
"""

import frappe


def get_or_create_conversation(module_label, linked_doctype, linked_name):
	existing = frappe.get_all(
		"UCC AI Conversation",
		filters={
			"user": frappe.session.user,
			"module": module_label,
			"linked_doctype": linked_doctype,
			"linked_name": linked_name,
		},
		order_by="creation desc",
		limit_page_length=1,
	)
	if existing:
		conversation = frappe.get_doc("UCC AI Conversation", existing[0]["name"])
	else:
		conversation = frappe.new_doc("UCC AI Conversation")
		conversation.user = frappe.session.user
		conversation.module = module_label
		conversation.linked_doctype = linked_doctype
		conversation.linked_name = linked_name
		conversation.title = module_label + ": " + linked_name
		conversation.insert()
	conversation.last_activity = frappe.utils.now()
	conversation.save()
	return conversation


def record_message(conversation, role, content, model=None, latency_ms=None, token_usage=None, source_summary=None):
	message = frappe.new_doc("UCC AI Message")
	message.conversation = conversation.name
	message.role = role
	message.content = content
	if source_summary:
		message.source_summary = frappe.as_json(source_summary)
	if model:
		message.model = model
	if latency_ms is not None:
		message.latency_ms = latency_ms
	if token_usage is not None:
		message.token_usage = token_usage
	message.insert()
	return message


def record_usage_log(conversation, module_label, result):
	log = frappe.new_doc("UCC AI Usage Log")
	log.user = frappe.session.user
	log.module = module_label
	log.conversation = conversation.name
	log.tools_called = frappe.as_json(result.get("tools_called") or [])
	log.source_ids = frappe.as_json(result.get("known_record_names") or [])
	answer = result.get("answer") or {}
	log.model = answer.get("model")
	log.latency_ms = answer.get("latency_ms")
	log.token_usage = answer.get("token_usage")
	log.request_diagnostic_id = frappe.generate_hash(length=10)
	log.insert(ignore_permissions=True)
	return log
