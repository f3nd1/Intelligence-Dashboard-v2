# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UCCAIActionRequest(Document):
	def validate(self):
		self.reject_unknown_action_type()
		self.freeze_proposal_after_draft()

	def reject_unknown_action_type(self):
		"""Actions are an allowlist (actions/registry.py), not a capability.
		Checked here as well as in the service so a record created directly --
		through the Desk UI, a fixture, an import -- cannot introduce an
		action type the executor would then be asked to run."""
		from ucc_intelligence.actions import registry

		action = registry.get(self.action_type)
		if not action:
			frappe.throw(frappe._("{0} is not an allowlisted action type.").format(self.action_type))
		if action["level"] > registry.LEVEL_CONFIRM_BEFORE_EXECUTE:
			frappe.throw(frappe._("Action level {0} is not implemented.").format(action["level"]))

	def freeze_proposal_after_draft(self):
		"""An approver approves a specific payload against a specific record.
		If either could change after approval, the approval would be
		meaningless -- someone could approve a harmless draft and execute
		something else. Editable only while still in Draft."""
		if self.is_new() or self.workflow_state == "Draft":
			return
		before = self.get_doc_before_save()
		if not before:
			return
		for fieldname, label in (
			("action_type", "action type"),
			("payload_json", "proposed payload"),
			("target_doctype", "target DocType"),
			("target_record", "target record"),
		):
			if (before.get(fieldname) or "") != (self.get(fieldname) or ""):
				frappe.throw(frappe._(
					"The {0} cannot change once a request has left Draft -- an approval "
					"applies to exactly what was proposed."
				).format(label))
