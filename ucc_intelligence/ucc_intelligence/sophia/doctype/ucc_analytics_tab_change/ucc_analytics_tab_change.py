# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UCCAnalyticsTabChange(Document):
	"""One recorded change to a Sophia Analytics tab's configuration.

	WHY IT EXISTS
	The tabs feed EduTrust evidence. "Who put this chart here, and when" is an
	audit question, and the answer has to survive the person who did it
	changing their mind.

	WRITE-ONCE, BY DESIGN
	The DocType grants no `write` and no `create` to anyone -- records are
	created by analytics/tab_audit.py with ignore_permissions, and nothing in
	the platform edits one afterwards. That is a deliberate use of the bypass
	CLAUDE.md §1.1.10 otherwise forbids, for the one case where it is the
	point: an audit entry the actor could decline to write, or could rewrite
	later, is not an audit entry. `delete` is left with System Manager so a
	retention policy remains possible.

	on_update refuses an edit outright rather than trusting the missing
	permission, because permissions can be granted in Desk by someone who has
	not read this docstring.
	"""

	def on_update(self):
		if not self.is_new():
			frappe.throw(frappe._("Audit records cannot be edited."), frappe.PermissionError)
