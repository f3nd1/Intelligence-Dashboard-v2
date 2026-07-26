"""Audit-safe logging for permission and access decisions.

CLAUDE.md §12.4 (audit trail: user, feature, time, outcome, error reference)
and §14.2 (structured logs, INFO for success, WARNING for degraded-but-
recoverable). Frappe's own logger already stamps time; nothing here repeats
that. No full request payloads are logged, per §12.2.
"""

import frappe

from ucc_intelligence.logging.redaction import redact_error_text

logger = frappe.logger("ucc_intelligence", allow_site=True)


def log_access_check(user, applied, matched_roles=None, error=None):
	"""One line per dashboard-access resolution: who, what was applied, why."""
	fields = {
		"feature": "dashboard_access",
		"user": user,
		"applied": applied,
		"matched_roles": matched_roles or [],
	}
	if error is not None:
		fields["error"] = redact_error_text(error)
		logger.warning(fields)
	else:
		logger.info(fields)
