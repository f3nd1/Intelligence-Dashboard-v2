"""Quality Action tool functions for Ask UCC -- the fixed, named allowlist
this module is permitted to call (CLAUDE.md Phase 8: "AI must not query
arbitrary DocTypes... must not accept a user-provided method path"). The
AI orchestration layer only ever calls these two named functions with a
validated record name; it never constructs a query itself.

Faithfully ported from server-scripts/UCC Ask - Quality Action.py's own
deterministic logic (find_resolution_field, resolution_rows,
root_cause_review, action_review, closure_assessment) -- confirmed by a
full read of the legacy script, not the earlier per-module summary, that
it has zero AI code of its own. There is no AI-generation behaviour to
preserve, only the deterministic fact-gathering and the deterministic
readiness heuristics, both ported as-is.

Global/cross-record search (the legacy script's "all open quality
actions" / "all overdue" style queries, driven by detect_intent()) is
deliberately NOT ported this round -- see
docs/architecture/ask-ucc-phase-plan.md §6: this round proves the
pipeline on a single record in context; searching across every Quality
Action is a distinct capability, deferred, not silently dropped.

Permission model: frappe.get_doc("Quality Action", name) below runs with
no ignore_permissions -- ordinary Frappe DocType permissions apply exactly
as they did in the legacy script (confirmed: it never used
ignore_permissions either), and exactly as every criterion module tonight.
"""

import frappe

from ucc_intelligence.analytics.contracts import is_permission_error
from ucc_intelligence.analytics.engine import clean_text, lower_text

RESOLUTION_CHILD_DOCTYPE = "Quality Action Resolution"
RESOLUTION_FIELD_CANDIDATES = [
	"resolutions", "resolution", "quality_action_resolution",
	"quality_action_resolutions", "action_resolution",
]
TITLE_FIELD_CANDIDATES = [
	"custom_subject", "subject", "title", "action_name", "quality_action_name",
]


def strip_html(value):
	text = clean_text(value)
	for token in [
		"<p>", "</p>", "<div>", "</div>", "<br>", "<br/>", "<br />",
		"<ul>", "</ul>", "<ol>", "</ol>", "<li>", "</li>",
		"<strong>", "</strong>", "<b>", "</b>", "<em>", "</em>",
		"<i>", "</i>", "&nbsp;",
	]:
		text = text.replace(token, " ")
	while "<" in text and ">" in text:
		start = text.find("<")
		end = text.find(">", start)
		if start < 0 or end < 0:
			break
		text = text[:start] + " " + text[end + 1:]
	return " ".join(text.split())


def find_resolution_field(doctype="Quality Action"):
	"""Discovered live via meta inspection, not hardcoded -- the legacy
	script's own defensive pattern (a Table field with options == "Quality
	Action Resolution", falling back to a candidate-name list), preserved
	rather than assuming a specific fieldname this session has never
	verified against the real site schema."""
	try:
		meta = frappe.get_meta(doctype)
	except Exception:
		return ""
	for field in meta.fields or []:
		if clean_text(field.fieldtype) == "Table" and clean_text(field.options) == RESOLUTION_CHILD_DOCTYPE:
			return clean_text(field.fieldname)
	for candidate in RESOLUTION_FIELD_CANDIDATES:
		if meta.has_field(candidate):
			return candidate
	return ""


def resolution_rows(doc, fieldname):
	if not fieldname:
		return []
	try:
		return doc.get(fieldname) or []
	except Exception:
		return []


def quality_action_title(doc):
	for fieldname in TITLE_FIELD_CANDIDATES:
		value = clean_text(doc.get(fieldname))
		if value:
			return value
	return clean_text(doc.get("name"))


def row_status(row):
	return clean_text(row.get("status")) or "Not recorded"


def row_is_completed(row):
	return lower_text(row_status(row)) == "completed" or bool(row.get("completion_by"))


def row_is_overdue(row):
	target = clean_text(row.get("target_date"))
	if not target or row_is_completed(row):
		return False
	today = clean_text(frappe.utils.today())
	return bool(today and target < today)


def row_owner(row):
	return clean_text(row.get("full_name") or row.get("responsible")) or "Not assigned"


def load_quality_action(quality_action_name):
	"""Shared doc-resolution + error classification for both tools below."""
	try:
		return {"status": "available", "doc": frappe.get_doc("Quality Action", quality_action_name)}
	except frappe.DoesNotExistError:
		return {"status": "not_found", "message": "No Quality Action named %r." % quality_action_name}
	except Exception as error:
		status = "permission_denied" if is_permission_error(error) else "unavailable"
		return {"status": status, "message": clean_text(error)}


def get_quality_action_summary(quality_action_name):
	"""Tool: full profile of one Quality Action -- subject, resolution rows
	(finding type, status, owner, dates, problem/resolution/action text),
	and open/completed/overdue counts. Mirrors the legacy script's
	handle_profile()."""
	loaded = load_quality_action(quality_action_name)
	if loaded["status"] != "available":
		return loaded
	doc = loaded["doc"]

	fieldname = find_resolution_field()
	rows = resolution_rows(doc, fieldname)

	row_summaries = []
	open_count = 0
	completed_count = 0
	overdue_count = 0
	for index, row in enumerate(rows, 1):
		completed = row_is_completed(row)
		overdue = row_is_overdue(row)
		if completed:
			completed_count += 1
		else:
			open_count += 1
		if overdue:
			overdue_count += 1
		row_summaries.append({
			"row": index,
			"finding_type": clean_text(row.get("finding_type")) or "Not recorded",
			"status": row_status(row),
			"assigned_to": row_owner(row),
			"target_date": clean_text(row.get("target_date")) or "Not recorded",
			"completed_on": clean_text(row.get("completion_by")) or "Not recorded",
			"overdue": overdue,
			"problem": strip_html(row.get("problem")) or "Not recorded",
			"resolution": strip_html(row.get("resolution")) or "Not recorded",
			"action_taken": strip_html(row.get("action_taken")) or "Not recorded",
		})

	return {
		"status": "available",
		"quality_action": quality_action_name,
		"title": quality_action_title(doc),
		"resolution_rows": row_summaries,
		"open_count": open_count,
		"completed_count": completed_count,
		"overdue_count": overdue_count,
	}


def root_cause_review(text):
	value = strip_html(text)
	q = lower_text(value)
	issues = []
	if not value:
		issues.append("Root cause and resolution are missing.")
		return issues
	if len(value) < 80:
		issues.append("Root cause and resolution are very brief.")
	causal_terms = ["because", "due to", "caused by", "root cause", "lack of", "failure to", "insufficient", "inadequate"]
	if not any(term in q for term in causal_terms):
		issues.append("The text does not clearly distinguish the underlying cause from the symptom.")
	action_terms = ["implement", "update", "revise", "train", "monitor", "review", "create", "configure", "approve", "verify"]
	if not any(term in q for term in action_terms):
		issues.append("The resolution plan does not contain a clear corrective step.")
	recurrence_terms = ["prevent recurrence", "recurrence", "ongoing monitoring", "periodic review", "control", "verification"]
	if not any(term in q for term in recurrence_terms):
		issues.append("Recurrence-prevention or ongoing control is not explicit.")
	return issues


def action_review(text):
	value = strip_html(text)
	q = lower_text(value)
	issues = []
	if not value:
		issues.append("Action taken is missing.")
		return issues
	if len(value) < 50:
		issues.append("Action taken is too brief to demonstrate implementation.")
	evidence_terms = ["attached", "evidence", "record", "screenshot", "approved", "completed", "updated", "implemented", "verified"]
	if not any(term in q for term in evidence_terms):
		issues.append("Implementation evidence or an identifiable record is not mentioned.")
	return issues


def assess_quality_action_closure(quality_action_name):
	"""Tool: deterministic closure-readiness assessment, per resolution row.
	The ready/not-ready decision is a fixed rule -- CLAUDE.md: "the
	pass/fail decision should remain deterministic where possible" -- the
	AI explains these results, it does not compute or override them.
	Mirrors the legacy script's closure_assessment()/root_cause_review()/
	action_review() exactly."""
	loaded = load_quality_action(quality_action_name)
	if loaded["status"] != "available":
		return loaded
	doc = loaded["doc"]

	fieldname = find_resolution_field()
	rows = resolution_rows(doc, fieldname)

	assessments = []
	ready_count = 0
	for index, row in enumerate(rows, 1):
		reasons = []
		if not row_is_completed(row):
			reasons.append("Status is not completed.")
		if not row.get("completion_by"):
			reasons.append("Completed On is missing.")
		reasons.extend(root_cause_review(row.get("resolution")))
		reasons.extend(action_review(row.get("action_taken")))
		ready = len(reasons) == 0
		if ready:
			ready_count += 1
		assessments.append({
			"row": index,
			"finding_type": clean_text(row.get("finding_type")) or "Not recorded",
			"status": row_status(row),
			"ready": ready,
			"reasons": reasons,
		})

	return {
		"status": "available",
		"quality_action": quality_action_name,
		"title": quality_action_title(doc),
		"ready_count": ready_count,
		"total_count": len(assessments),
		"assessments": assessments,
		"note": "This is a rule-based readiness check. Formal closure still requires authorised verification and supporting evidence.",
	}


# The fixed allowlist ai/orchestration.py dispatches against -- adding a
# tool means adding it here explicitly, not exposing every function in
# this module automatically.
TOOLS = {
	"get_quality_action_summary": get_quality_action_summary,
	"assess_quality_action_closure": assess_quality_action_closure,
}
