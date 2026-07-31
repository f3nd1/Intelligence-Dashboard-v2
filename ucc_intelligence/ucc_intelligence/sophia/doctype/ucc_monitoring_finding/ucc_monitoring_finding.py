# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UCCMonitoringFinding(Document):
	def validate(self):
		self.require_suppression_reason()

	def require_suppression_reason(self):
		"""Suppressing a finding stops it reappearing on every future run
		(monitoring/engine.py never resurrects a suppressed finding). That is
		exactly the decision that must be auditable, so it cannot be made
		silently."""
		if self.status == "Suppressed" and not (self.suppression_reason or "").strip():
			frappe.throw(frappe._(
				"Record why this finding is being suppressed. A suppressed finding "
				"is never raised again, so the reason is the only remaining record "
				"of that decision."
			))
