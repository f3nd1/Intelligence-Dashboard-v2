# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import add_days, today


class UCCAIConversation(Document):
	def before_insert(self):
		if not self.expires_on:
			self.expires_on = add_days(today(), 30)
