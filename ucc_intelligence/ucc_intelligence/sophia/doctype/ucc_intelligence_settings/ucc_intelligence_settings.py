# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

from frappe.model.document import Document


class UCCIntelligenceSettings(Document):
	def validate(self):
		if self.default_temperature is not None:
			self.default_temperature = max(0.0, min(2.0, self.default_temperature))
