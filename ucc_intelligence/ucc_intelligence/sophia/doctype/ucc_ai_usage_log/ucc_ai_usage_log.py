# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

# Read-only in the Desk permissions (no role has write/create) -- audit log
# integrity, not editable even by System Manager through the UI. Rows are
# only ever inserted server-side, with ignore_permissions=True, by the Ask
# UCC orchestration layer on behalf of the requesting user's own action
# (CLAUDE.md §1.1.10's "explicit documented reason" for a permission
# bypass: this is audit logging of what the system itself just did in
# response to a permission-checked user request, not a new way for a user
# to reach data they couldn't otherwise read).

from frappe.model.document import Document


class UCCAIUsageLog(Document):
	pass
