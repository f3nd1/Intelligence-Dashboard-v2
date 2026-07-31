# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UCCKnowledgeChunk(Document):
	"""One indexed section of a knowledge document.

	WHAT THIS IS
	Knowledge ingestion (knowledge/ingestion.py) takes a registered
	`UCC Knowledge Source` -- a policy, procedure, course document or
	compliance requirement -- extracts its text and splits it on headings
	(knowledge/retrieval.py's split_sections). Each resulting section becomes
	one of these records: the text, the heading it came from, and its section
	index. Retrieval scores these and cites them as
	"document · version · section", which is why the heading is stored and
	not just the body -- an answer a reader cannot trace back to an exact
	section is not sourced (CLAUDE.md §9).

	WHO WRITES THESE
	Only `retrieval.index_source()`, which deletes and rebuilds every chunk
	for a source on each (re)index. A document is republished, not edited in
	place, and a partial reindex leaving orphans would let retired wording
	keep surfacing. Nothing typed into this form survives the next indexing
	run, which is why it is read-only to everyone but System Manager.

	WHY THERE IS VALIDATION HERE AT ALL
	Two fields are COPIES of the parent source, kept so a citation can be
	rendered without a second read. A copy that can drift is worse than a
	join -- see sync_denormalised_fields() for the one that matters.
	"""

	def validate(self):
		self.require_source()
		self.sync_denormalised_fields()

	def require_source(self):
		"""A chunk with no source cannot be cited and cannot be permission
		checked -- retrieval resolves eligibility from the SOURCE, so an
		orphan chunk would be unreachable at best."""
		if not self.source:
			frappe.throw(frappe._("A knowledge chunk must belong to a knowledge source."))

	def sync_denormalised_fields(self):
		"""Re-read `source_title` and `permission_role` from the parent.

		`permission_role` is the one that matters. It is NOT the permission
		gate: retrieval.current_source_names() filters on the SOURCE's role,
		per request, against the live document. This copy exists only so a
		citation can be rendered without a second read.

		That distinction is easy to lose -- the field looks like a permission
		field, and someone optimising retrieval later could reasonably filter
		on it instead. If they did, and an administrator had since tightened
		a document's restriction, this stale copy would still hold the older,
		LOOSER role, and a restricted document would be retrievable by people
		who should no longer see it. Re-syncing on every save means the copy
		can never be more permissive than its source, so that change would be
		safe rather than silently wrong.

		The field's description in the JSON now says display-only, which is
		the real fix. This is the belt to that's braces.
		"""
		if not self.source:
			return
		parent = frappe.db.get_value(
			"UCC Knowledge Source", self.source, ["title", "permission_role"], as_dict=True)
		if not parent:
			frappe.throw(frappe._("Knowledge source {0} no longer exists.").format(self.source))
		self.source_title = parent.get("title")
		self.permission_role = parent.get("permission_role")
