# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document


class UCCAnalyticsTab(Document):
	"""How one Sophia Analytics tab is configured -- for everyone.

	WHAT CHANGED AND WHY
	Charts, intro text and hidden questions were first stored in
	`frappe.defaults`, per user. That was wrong for this app and Felix said so:
	Sophia is an institutional dashboard used as EduTrust evidence, not a
	personal workspace. A chart the Quality Manager adds as evidence has to be
	the chart the auditor sees.

	So one record per criterion+tab, shared. `autoname: format:{criterion}::{tab}`
	makes the name the key, so a duplicate cannot exist by construction.

	WHO MAY CHANGE IT
	Write permission on THIS DocType, which follows the same shape as
	`UCC Dashboard Access`: System Manager by default, adjustable in Desk
	without a code change. Everyone else sees the result read-only and is not
	shown the edit controls at all. See analytics/tab_charts.py's can_edit().

	WHY THE LISTS ARE JSON IN A TEXT FIELD
	`charts` and `hidden_questions` are ordered lists this app owns and always
	reads whole. A child table would add two more DocTypes and a controller
	each to express the same thing, and nothing else ever queries an individual
	row. The validation below is what earns that: a field that cannot be
	trusted to parse would be a worse trade.
	"""

	def validate(self):
		self.charts = self.normalised(self.charts, "charts")
		self.hidden_questions = self.normalised(self.hidden_questions, "hidden_questions")

	def normalised(self, value, fieldname):
		"""Store valid JSON or nothing. A hand-edit in Desk that leaves this
		unparseable would silently empty a tab for every user at once, so it is
		refused at save time rather than swallowed at read time."""
		text = (value or "").strip()
		if not text:
			return "[]"
		try:
			parsed = json.loads(text)
		except (TypeError, ValueError):
			frappe.throw(frappe._("{0} must be a JSON list.").format(self.meta.get_label(fieldname)))
		if not isinstance(parsed, list):
			frappe.throw(frappe._("{0} must be a JSON list.").format(self.meta.get_label(fieldname)))
		return json.dumps(parsed)
