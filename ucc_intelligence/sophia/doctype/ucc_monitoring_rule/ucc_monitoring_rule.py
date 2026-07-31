# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UCCMonitoringRule(Document):
	def validate(self):
		self.reject_unknown_rule_id()

	def reject_unknown_rule_id(self):
		"""The evaluation logic lives in monitoring/rule_registry.py, not here.
		A record whose rule_id has no registry entry can never run -- it would
		sit in the list looking enabled and never produce a finding, which is
		the most misleading possible state for a monitoring rule."""
		from ucc_intelligence.monitoring import rule_registry

		if self.rule_id and self.rule_id not in rule_registry.RULES:
			frappe.throw(frappe._(
				"No monitoring rule named {0} exists in the rule registry, so this "
				"record could never run. Rules are defined in code, not created here."
			).format(self.rule_id))
