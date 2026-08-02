# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt
"""Who changed a Sophia tab's configuration, what changed, and when.

WHY
The tabs feed EduTrust evidence. A chart on Criterion 3 is part of what an
auditor is shown, so "who put it there and when" is an audit question, not a
debugging one. That is why this writes DocType records rather than log lines --
a log file is not somewhere Felix can read, and CLAUDE.md §12.4 asks for an
audit trail that names the user, the time and the record context.

WHAT IS RECORDED
One record per change, with a human-readable summary and the before/after
value. The summary is the thing anyone will actually read; the before/after is
what settles an argument about it.

WHAT IS NOT RECORDED
No institutional data. A chart id, a chart title, a question id and the intro
text are configuration -- they say what the tab is set up to show, not what it
showed. Nobody's grades end up in the audit trail.

FAILURE POLICY
`record()` never raises. An audit write that fails must not cost someone the
change they were making: the change is the user's intent, and losing it to a
bookkeeping error would be the worse outcome. A failure goes to the Error Log,
which is where an unwritten audit entry becomes visible.
"""

import json

import frappe

AUDIT_DOCTYPE = "UCC Analytics Tab Change"

# Every action this module knows how to describe. A caller passing anything
# else is a bug, and is recorded as-is rather than dropped -- an unlabelled
# audit entry beats a missing one.
ACTIONS = (
	"chart_added",
	"chart_removed",
	"chart_resized",
	"chart_recoloured",
	"chart_retitled",
	"charts_reordered",
	"intro_edited",
	"question_hidden",
	"question_shown",
	"dashboard_embedded",
	"dashboard_unembedded",
)

MAX_VALUE_LENGTH = 4000


def _text(value):
	if value is None:
		return ""
	if isinstance(value, str):
		return value[:MAX_VALUE_LENGTH]
	try:
		return json.dumps(value, default=str)[:MAX_VALUE_LENGTH]
	except Exception:
		return str(value)[:MAX_VALUE_LENGTH]


def record(criterion, tab, action, summary, before=None, after=None):
	"""Write one audit entry. Never raises."""
	try:
		document = frappe.new_doc(AUDIT_DOCTYPE)
		document.update({
			"criterion": criterion,
			"tab": tab,
			"action": action,
			"summary": (summary or "")[:300],
			"changed_by": frappe.session.user,
			"changed_at": frappe.utils.now(),
			"before_value": _text(before),
			"after_value": _text(after),
		})
		# ignore_permissions deliberately, and this is the one place in the
		# platform where that is the POINT: the DocType grants create to
		# nobody, so an actor cannot decline to be recorded. See the DocType's
		# own docstring.
		document.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(
			title="UCC Analytics tab audit write failed",
			message="%s/%s %s\n\n%s" % (criterion, tab, action, frappe.get_traceback()))


def history(criterion, tab, limit=50):
	"""The recent changes to one tab, newest first.

	Read with ignore_permissions for the same reason the configuration itself
	is: everyone who can see a tab should be able to see who set it up, and the
	records hold no institutional data. Writing is impossible for everyone;
	this is the read.
	"""
	limit = max(1, min(int(limit or 50), 200))
	try:
		return frappe.get_all(
			AUDIT_DOCTYPE,
			filters={"criterion": criterion, "tab": tab},
			fields=["name", "action", "summary", "changed_by", "changed_at"],
			order_by="changed_at desc",
			limit_page_length=limit,
			ignore_permissions=True,
		) or []
	except Exception:
		return []


# --- summary builders -------------------------------------------------------
# One place that turns a change into the sentence someone will read, so the
# wording cannot drift between endpoints.

def chart_label(title, chart):
	return title or chart


def added(title, chart):
	return "Added the chart %r" % chart_label(title, chart)


def removed(title, chart):
	return "Removed the chart %r" % chart_label(title, chart)


def resized(title, chart, before_span, after_span):
	return "Resized %r from %s to %s of 12 columns" % (
		chart_label(title, chart), before_span, after_span)


def reordered(count):
	return "Reordered the %d charts on this tab" % count


def intro_edited(before, after):
	if not (before or "").strip():
		return "Added the tab introduction"
	if not (after or "").strip():
		return "Removed the tab introduction"
	return "Edited the tab introduction"


def question_visibility(question, visible):
	return "%s the management question %r" % ("Showed" if visible else "Hid", question)


def dashboard_embedded(title, dashboard):
	"""Which Insights dashboard this tab now embeds, or that it stopped."""
	if not dashboard:
		return "Stopped embedding an Insights dashboard on this tab"
	return "Embedded the Insights dashboard %s" % chart_label(title, dashboard)
