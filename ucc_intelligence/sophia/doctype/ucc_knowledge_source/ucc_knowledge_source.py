# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UCCKnowledgeSource(Document):
	def validate(self):
		self.reject_self_supersession()
		self.reject_supersession_cycle()

	def reject_self_supersession(self):
		"""A document superseded by itself would be excluded from retrieval
		permanently and silently -- current_source_names() drops anything with
		superseded_by set, so this would quietly remove a live policy."""
		if self.superseded_by and self.superseded_by == self.name:
			frappe.throw(frappe._("A document cannot supersede itself."))

	def reject_supersession_cycle(self):
		"""A -> B -> A makes both unquotable and neither obviously wrong.
		Walked rather than checked one level deep, because a three-document
		cycle is just as silent as a two-document one."""
		seen = {self.name}
		current = self.superseded_by
		while current:
			if current in seen:
				frappe.throw(frappe._("That supersession would create a loop, leaving these documents unquotable."))
			seen.add(current)
			current = frappe.db.get_value("UCC Knowledge Source", current, "superseded_by")
