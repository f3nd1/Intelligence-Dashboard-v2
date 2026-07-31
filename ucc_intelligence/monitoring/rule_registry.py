"""The monitoring rules themselves (CLAUDE.md Phase 11).

Rules live in version-controlled Python, not in DocType records. CLAUDE.md
§11 requires the pass/fail decision to be deterministic and §5 wants
configuration reviewable; an evaluator stored as a database row is neither
diffable nor testable. The `UCC Monitoring Rule` DocType carries the
operational knobs an administrator legitimately changes without a deploy --
enabled, severity, responsible role, effective date, remediation text --
and nothing that decides whether a record passes.

Each rule declares:
    rule_id        stable identifier, also the DocType record name
    title          what it checks, in the words a process owner would use
    purpose        why it exists
    target_doctype which DocType it evaluates
    fields         the fields it needs loaded (never `*`)
    severity       default severity, overridable on the record
    version        bumped whenever the LOGIC changes, so a finding can be
                   traced to the logic that produced it
    evaluate(row)  -> None if the record passes, or a detail string

`evaluate` is pure: a dict in, a string or None out. No queries, no writes,
no clock. That is what makes these testable without a database and what
keeps a rerun idempotent.

Scope note: the three rules below are CLAUDE.md §11's use cases 1, 2 and 4.
Cases 5-8 (course review evidence, expiring contracts, the QA calendar,
departmental housekeeping) are not implemented -- they need field-level
facts about DocTypes this migration has not yet inspected, and inventing
their field names would produce rules that silently never fire, which is
worse than not shipping them.
"""

import re

# CLAUDE.md §11 use case 2: "Student Log content must not contain guide or
# dummy text." These are the placeholder strings a template leaves behind.
# Matched as whole words on a normalised copy so "lorem" doesn't fire on a
# student named Lorem and "n/a" doesn't fire inside "n/august".
DUMMY_TEXT_MARKERS = (
	"lorem ipsum",
	"dummy",
	"placeholder",
	"tbc",
	"tbd",
	"to be confirmed",
	"to be advised",
	"xxx",
	"test test",
	"sample text",
	"enter text here",
	"type here",
	"your text",
	"n/a n/a",
)

# Text that is technically present but carries no information. A field
# holding only this is not filled in, whatever the database thinks.
EMPTY_EQUIVALENTS = {"", "-", "--", "n/a", "na", "nil", "none", "not applicable", "."}

HTML_TAG = re.compile(r"<[^>]+>")
WHITESPACE = re.compile(r"\s+")


def plain_text(value):
	"""Frappe text-editor fields arrive as HTML. Compare on the words."""
	if value is None:
		return ""
	text = HTML_TAG.sub(" ", str(value))
	text = text.replace("&nbsp;", " ").replace("&amp;", "&")
	return WHITESPACE.sub(" ", text).strip()


def is_blank(value):
	return plain_text(value).lower() in EMPTY_EQUIVALENTS


# Whole-word matching, not substring: "tbc" as a substring fires on a student
# in the "Tbcaster" programme, and a rule that cries wolf gets ignored, which
# is worse than not having it. Longest-first so "n/a n/a" wins over a shorter
# overlapping marker and the reported detail is the specific one.
DUMMY_TEXT_PATTERN = re.compile(
	r"(?<![0-9a-z])(" + "|".join(re.escape(m) for m in sorted(DUMMY_TEXT_MARKERS, key=len, reverse=True))
	+ r")(?![0-9a-z])",
	re.IGNORECASE,
)


def find_dummy_text(value):
	"""The marker found, or None. Returns the marker so the finding can say
	exactly what tripped it rather than "contains dummy text"."""
	match = DUMMY_TEXT_PATTERN.search(WHITESPACE.sub(" ", plain_text(value).lower()))
	return match.group(1) if match else None


# ---------------------------------------------------------------------------
# Rule 1 -- CLAUDE.md §11 use case 1
# ---------------------------------------------------------------------------
def evaluate_student_log_background(row):
	"""A Student Log may only be completed or closed once the student
	background is filled in. Closing with an empty background is the exact
	gap this rule exists to catch, so an open log with a blank background is
	NOT a finding -- it is simply not finished yet."""
	status = plain_text(row.get("status")).lower()
	if status not in ("completed", "closed"):
		return None
	if is_blank(row.get("student_background")):
		return "Status is %r but the student background is empty." % plain_text(row.get("status"))
	return None


# ---------------------------------------------------------------------------
# Rule 2 -- CLAUDE.md §11 use case 2
# ---------------------------------------------------------------------------
DUMMY_TEXT_FIELDS = ("student_background", "details", "action_taken")


def evaluate_student_log_dummy_text(row):
	hits = []
	for fieldname in DUMMY_TEXT_FIELDS:
		marker = find_dummy_text(row.get(fieldname))
		if marker:
			hits.append("%s contains %r" % (fieldname, marker))
	return "; ".join(hits) if hits else None


# ---------------------------------------------------------------------------
# Rule 3 -- CLAUDE.md §11 use case 4
# ---------------------------------------------------------------------------
def evaluate_quality_action_closure(row):
	"""A closed Quality Action must carry the evidence of its closure: an
	owner, a target date, and a recorded resolution and action. Anything
	less is a closure that cannot be audited."""
	status = plain_text(row.get("status")).lower()
	if status not in ("completed", "closed"):
		return None
	missing = []
	for fieldname, label in (
		("assigned_to", "an assigned owner"),
		("target_date", "a target date"),
		("resolution", "a recorded resolution"),
		("action_taken", "a recorded action taken"),
	):
		if is_blank(row.get(fieldname)):
			missing.append(label)
	if missing:
		return "Closed without %s." % ", ".join(missing)
	return None


RULES = {
	"student_log_background_required": {
		"rule_id": "student_log_background_required",
		"title": "Student Log closed without student background",
		"purpose": "CLAUDE.md §11 use case 1 -- a log may only be completed or closed once the student background is filled.",
		"target_doctype": "Student Log",
		"fields": ["name", "status", "student_background", "creation"],
		"severity": "High",
		"version": "1.0",
		"remediation": "Fill in the student background, or reopen the log until it can be completed properly.",
		"evaluate": evaluate_student_log_background,
	},
	"student_log_dummy_text": {
		"rule_id": "student_log_dummy_text",
		"title": "Student Log contains guide or dummy text",
		"purpose": "CLAUDE.md §11 use case 2 -- template placeholder text left in a live record.",
		"target_doctype": "Student Log",
		"fields": ["name", "student_background", "details", "action_taken", "creation"],
		"severity": "Medium",
		"version": "1.0",
		"remediation": "Replace the placeholder text with the real content, or clear the field.",
		"evaluate": evaluate_student_log_dummy_text,
	},
	"quality_action_closure_evidence": {
		"rule_id": "quality_action_closure_evidence",
		"title": "Quality Action closed without owner, due date, resolution or action",
		"purpose": "CLAUDE.md §11 use case 4 -- closures must carry the evidence that justifies them.",
		"target_doctype": "Quality Action Resolution",
		"fields": ["name", "parent", "status", "assigned_to", "target_date", "resolution", "action_taken", "creation"],
		"severity": "High",
		"version": "1.0",
		"remediation": "Record the missing closure evidence, or reopen the Quality Action.",
		"evaluate": evaluate_quality_action_closure,
	},
}
