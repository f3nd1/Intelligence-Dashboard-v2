# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt
"""Deterministic data-consistency checks on a retrieved record.

WHAT THIS IS NOT
Not an AI answer, and not a monitoring rule. A warning from here is produced by
reading two fields and comparing them -- no model, no judgement, no scoring. It
renders in its own amber band in Ask UCC precisely so nobody reads it as either
a fact from the record or a conclusion drawn by a model.

WHY IT SITS IN THE ANSWER
The case that motivated it: a student's planned completion date has passed and
the record still says Graduated: No. Both fields are correct as facts, and a
verified answer that reports either one alone is misleading. The person asking
"has this student graduated?" needs to see the tension in the same breath as
the answer, not on a monitoring report next quarter.

SCOPE
One rule, for the one case named. `monitoring/` is where scheduled, tracked,
deduplicated rules belong -- this is a read-time observation attached to an
answer, and should stay small. If this file starts growing rule versions,
severities or suppression, that is the signal it has become monitoring and
should move there.
"""

import frappe

# The record's own words for "this is finished", so a completion date in the
# past is not flagged on a student who has in fact graduated.
COMPLETE_STATUSES = {"graduated", "completed", "withdrawn", "terminated", "cancelled"}


def _as_date(value):
	if not value or value in ("Not recorded", "-"):
		return None
	try:
		return frappe.utils.getdate(value)
	except Exception:
		return None


def for_student_journey(profile):
	"""Completion date reached, graduation still not recorded."""
	if not profile or profile.get("status") != "available":
		return []
	if profile.get("graduated"):
		return []
	if str(profile.get("academic_status") or "").strip().lower() in COMPLETE_STATUSES:
		return []
	completion = _as_date(profile.get("completion_date"))
	if not completion or completion > frappe.utils.getdate(frappe.utils.nowdate()):
		return []
	return [{
		"code": "completion_date_reached_not_graduated",
		"severity": "warning",
		"message": (
			"The completion date has been reached. Confirm whether the graduation "
			"status needs updating."
		),
		"fields": ["completion_date", "graduated", "academic_status"],
	}]


CHECKS = {"student_journey": for_student_journey}


def run(module_key, primary_result):
	"""Every check for this module. Never raises: a broken check must not cost
	the user their answer."""
	check = CHECKS.get(module_key)
	if not check:
		return []
	try:
		return check(primary_result or {})
	except Exception:
		frappe.log_error(title="UCC Ask UCC data check failed", message=frappe.get_traceback())
		return []
