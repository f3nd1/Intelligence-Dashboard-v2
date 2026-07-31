# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

from frappe.model.document import Document


class UCCKnowledgeChunk(Document):
	"""One indexed section of a knowledge document.

	No validation of its own: chunks are derived data, written only by
	knowledge/retrieval.py's index_source() and replaced wholesale on
	re-index. Nothing a user edits here would survive the next indexing run,
	which is why the DocType is read-only to everyone but System Manager.
	"""
	pass
