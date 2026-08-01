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

	WHY THE INSERT FLAG (fixed 2026-08-01)
	`on_update` fires after an INSERT as well as after an update, so the guard
	fired against the very insert that creates the record. The row survived --
	tab_audit.record() catches everything -- but `frappe.throw` had already put
	"Audit records cannot be edited." into the message log, and the message log
	reaches the browser whether or not the exception was caught. So a
	successful resize reported a failure that had not happened.

	The discriminator is a flag set in `before_insert`, which runs on inserts
	and only on inserts. Flags live on the document instance and are never
	persisted, so a document loaded later for a genuine edit cannot carry one.
	The guard itself is unchanged in strength: an edit is still refused, and
	an insert was never an edit.
	"""

	def before_insert(self):
		self.flags.ucc_inserting = True

	def on_update(self):
		if self.flags.ucc_inserting:
			return
		frappe.throw(frappe._("Audit records cannot be edited."), frappe.PermissionError)
