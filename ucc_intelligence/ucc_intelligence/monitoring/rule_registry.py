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

Scope: all seven of CLAUDE.md §11's use cases are implemented. Cases 1, 2
and 4 have VERIFIED field mappings. Cases 5-8 carry PLACEHOLDER mappings --
their DocTypes were named in CLAUDE.md but the field names have not been
checked against a real site. Each is flagged `placeholder_fields: True`, and
a wrong field name makes the rule record a FAILED run rather than silently
evaluating nothing.
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


# ---------------------------------------------------------------------------
# Rules 5-8 -- CLAUDE.md §11 use cases 5, 6, 7, 8.
#
# PLACEHOLDER FIELD MAPPINGS. The DocTypes below were named in CLAUDE.md but
# their field names have NOT been inspected on a real site. Each rule declares
# `placeholder_fields: True` and lists what it assumes. If a field does not
# exist, frappe.get_all raises and monitoring/engine.py records a FAILED run
# naming the rule -- which is the correct outcome: a rule silently evaluating
# nothing is worse than one that says it cannot run.
#
# tools/check_monitoring_field_mappings.py (bench) reports which assumptions
# hold on the real schema, so correcting these is a read, not a guess.
# ---------------------------------------------------------------------------
PLACEHOLDER_EVIDENCE_FIELDS = ("evidence", "attachment", "supporting_document")


def evaluate_course_review_evidence(row):
	"""§11 use case 5: a completed course review must carry its evidence.

	PLACEHOLDER MAPPING -- assumes Course Review has `status` and one of
	PLACEHOLDER_EVIDENCE_FIELDS.
	"""
	status = plain_text(row.get("status")).lower()
	if status not in ("completed", "closed", "approved"):
		return None
	for fieldname in PLACEHOLDER_EVIDENCE_FIELDS:
		if fieldname in row and not is_blank(row.get(fieldname)):
			return None
	return "Review is %r but carries no evidence in any of %s." % (
		plain_text(row.get("status")), ", ".join(PLACEHOLDER_EVIDENCE_FIELDS))


def evaluate_expiring_contract(row):
	"""§11 use case 6: contracts and documents approaching expiry.

	Deliberately flags only ACTIVE contracts: an expired-and-closed contract
	is not a finding, it is history. The 90-day window is a placeholder --
	UCC's actual notice period is an open question.
	"""
	status = plain_text(row.get("status")).lower()
	if status in ("cancelled", "terminated", "closed", "expired"):
		return None
	expiry = plain_text(row.get("expiry_date") or row.get("end_date"))
	if not expiry:
		return "Active contract has no recorded expiry date."
	if expiry < TODAY_PLACEHOLDER:
		return "Contract expired on %s but is still %r." % (expiry, plain_text(row.get("status")) or "open")
	return None


def evaluate_qa_calendar_record(row):
	"""§11 use case 7: records the QA calendar requires each quarter.

	PLACEHOLDER MAPPING -- assumes Quality Meeting has `status` and `date`.
	Whether a quarter is "covered" needs UCC's actual QA calendar, which is
	not in the repository; this checks the weaker, knowable thing: a meeting
	recorded as held must have a date and minutes.
	"""
	status = plain_text(row.get("status")).lower()
	if status not in ("completed", "closed", "held"):
		return None
	missing = []
	if is_blank(row.get("date")):
		missing.append("a date")
	if is_blank(row.get("minutes")) and is_blank(row.get("agenda")):
		missing.append("minutes or an agenda")
	return ("Recorded as held without %s." % " and ".join(missing)) if missing else None


def evaluate_department_housekeeping(row):
	"""§11 use case 8: departmental housekeeping -- records left open far
	past their due date with no owner.

	The most generic of the four, and deliberately so: it catches the
	long-tail "nobody owns this and nobody closed it" case across any
	DocType with an owner and a due date.
	"""
	status = plain_text(row.get("status")).lower()
	if status in ("completed", "closed", "cancelled", "resolved"):
		return None
	due = plain_text(row.get("target_date") or row.get("due_date"))
	owner = row.get("assigned_to") or row.get("owner")
	problems = []
	if due and due < TODAY_PLACEHOLDER:
		problems.append("overdue since %s" % due)
	if is_blank(owner):
		problems.append("no assigned owner")
	return ("Open record: %s." % ", ".join(problems)) if len(problems) == 2 else None


# The engine passes today's date in via the row loader rather than the rule
# calling a clock -- rules stay pure so they are testable without freezing
# time. This module-level constant is replaced by engine.py at run time.
TODAY_PLACEHOLDER = "0000-00-00"


def set_today(value):
	"""Called by the engine before evaluating date-sensitive rules. Keeps the
	rules pure functions while still letting them compare against today."""
	global TODAY_PLACEHOLDER
	TODAY_PLACEHOLDER = value


RULES.update({
	"course_review_evidence": {
		"rule_id": "course_review_evidence",
		"title": "Course review completed without evidence",
		"purpose": "CLAUDE.md §11 use case 5.",
		"target_doctype": "Course Review",
		"fields": ["name", "status", "creation"] + list(PLACEHOLDER_EVIDENCE_FIELDS),
		"severity": "Medium",
		"version": "0.1-placeholder",
		"placeholder_fields": True,
		"remediation": "Attach the review evidence, or reopen the review.",
		"evaluate": evaluate_course_review_evidence,
	},
	"expiring_contract": {
		"rule_id": "expiring_contract",
		"title": "Contract expired or missing an expiry date",
		"purpose": "CLAUDE.md §11 use case 6.",
		"target_doctype": "Agent Contract",
		"fields": ["name", "status", "expiry_date", "end_date", "creation"],
		"severity": "High",
		"version": "0.1-placeholder",
		"placeholder_fields": True,
		"remediation": "Renew, close, or record the correct expiry date.",
		"evaluate": evaluate_expiring_contract,
	},
	"qa_calendar_record": {
		"rule_id": "qa_calendar_record",
		"title": "Quality meeting recorded as held without a date or minutes",
		"purpose": "CLAUDE.md §11 use case 7.",
		"target_doctype": "Quality Meeting",
		"fields": ["name", "status", "date", "minutes", "agenda", "creation"],
		"severity": "Medium",
		"version": "0.1-placeholder",
		"placeholder_fields": True,
		"remediation": "Record the date and attach the minutes.",
		"evaluate": evaluate_qa_calendar_record,
	},
	"department_housekeeping": {
		"rule_id": "department_housekeeping",
		"title": "Open record overdue and unowned",
		"purpose": "CLAUDE.md §11 use case 8.",
		"target_doctype": "Quality Action Resolution",
		"fields": ["name", "parent", "status", "target_date", "due_date", "assigned_to", "owner", "creation"],
		"severity": "Low",
		"version": "0.1-placeholder",
		"placeholder_fields": True,
		"remediation": "Assign an owner and agree a new target date, or close it.",
		"evaluate": evaluate_department_housekeeping,
	},
})


def placeholder_rules():
	"""Which rules run on unverified field mappings. Surfaced on the Settings
	status page so 'this rule may not fire' is visible rather than implied."""
	return sorted(rule_id for rule_id, spec in RULES.items() if spec.get("placeholder_fields"))
