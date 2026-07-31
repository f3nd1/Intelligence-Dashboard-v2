# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

from frappe.model.document import Document


class UCCMonitoringRun(Document):
	"""One execution of one monitoring rule.

	No validation: a run is a historical record written by the engine, never
	edited. Its permissions grant no write to any role for the same reason --
	an operational history someone can revise is not a history.
	"""
	pass
