"""Guided ("FAQ") question buttons for the Ask UCC tab.

Ported verbatim from the legacy Ask UCC UI's own question maps
(custom-html-block/JAVASCRIPT.js: `studentQuestionMap` lines 1684-1728,
`recruitmentQuestionMap` 1729-1761, `qualityActionQuestionMap` 1762-1797)
and its per-module category labels (`renderCategoryOptions` 1881-1921).
Copied, not invented -- these are the buttons staff already know.

Two deliberate differences from the legacy behaviour, both about not
shipping buttons that cannot work:

1. **The `cohort` category is excluded entirely.** Every question in it is
   a cross-record query ("Show all open Quality Actions", "Who is in class
   today?"). The legacy UI sent those with a literal `"__GLOBAL__"`
   sentinel record id. Cross-record search was deliberately deferred in
   all three tool modules (see each ask_ucc/*.py docstring), so those
   buttons would reliably fail. They are held back with the capability,
   not shipped broken.

2. **Individual questions whose backing tool was deferred are excluded**
   via UNSUPPORTED_QUESTIONS below -- chiefly the finance/fees questions.
   Student Journey's finance data came from an unfiltered invoice
   name-match the port deliberately dropped as unreliable
   (ask_ucc/student_journey.py), and Recruitment Agent's revenue and
   recruited-student lists came from the brute-force row scans dropped in
   ask_ucc/recruitment_agent.py.

Both exclusions are applied by `supported_questions()` at render time
rather than by editing the maps, so the maps stay byte-comparable with the
legacy source and the test can prove they were not quietly reworded.

The AI answers from retrieved facts only, so a question whose facts are
missing would get an honest "not in the supplied facts" rather than a
wrong answer -- but a button that predictably can't be answered is still
a bad button, which is why these are filtered rather than left in.
"""

# Verbatim from JAVASCRIPT.js:1684-1728 -- [button label, question sent].
STUDENT_QUESTION_MAP = {
	"profile": [
		["Student profile", "Show this student's profile"],
		["Course", "What course is this student in?"],
		["Nationality", "What is this student's nationality?"],
		["Commencement", "When did this student start?"],
		["Completion", "When is this student completing the course?"],
	],
	"journey": [
		["Full timeline", "Show this student's journey"],
		["Current module", "Which module is this student in right now?"],
		["Class and group", "Show this student's class and student group"],
		["Current leave", "Is this student on leave now?"],
	],
	"academic": [
		["All results", "Show all this student's results and grades"],
		["Module completion", "Has this student finished all modules?"],
		["Graduation status", "Has this student graduated?"],
		["Results and grades", "Show all this student's results and grades"],
	],
	"attendance": [
		["Attendance summary", "Show this student's attendance"],
		["Current leave", "Is this student on leave now?"],
		["Leave history", "Show this student's leave records"],
	],
	"finance": [
		["Payment status", "Show this student's fee and payment status"],
		["Outstanding fees", "Does this student have outstanding fees?"],
		["Invoices", "Show this student's invoices"],
		["FPS status", "What is this student's FPS status?"],
	],
	"graduation": [
		["Readiness", "Is this student ready to graduate?"],
		["Risk summary", "Show this student's risk summary"],
		["Follow-up actions", "What follow-up actions are needed for this student?"],
		["Admission documents", "Show this student's attached admission documents"],
	],
	"cohort": [
		["Cohort dashboard", "Show the cohort dashboard"],
		["Class today", "Who are the students in class today?"],
		["Graduating this month", "Who is graduating this month?"],
		["Graduated months ago", "Who graduated 6 months ago?"],
		["Leave count", "How many students are on leave from 15 to 30 August 2026?"],
	],
}

# Verbatim from JAVASCRIPT.js:1729-1761.
RECRUITMENT_QUESTION_MAP = {
	"profile": [
		["Agent profile", "Show this agent's profile"],
		["Contract status", "Is this agent's contract active?"],
		["Contract dates", "Show this agent's contract dates"],
	],
	"journey": [
		["Agent journey", "Show this agent's complete journey"],
		["Latest contract", "Show this agent's latest contract"],
		["Expiry", "When does this agent's contract expire?"],
	],
	"academic": [
		["Students recruited", "How many students did this agent recruit?"],
		["Recruitment list", "Show students recruited by this agent"],
	],
	"attendance": [
		["Latest rating", "What is this agent's latest rating?"],
		["Rating threshold", "Does this agent meet the minimum rating?"],
	],
	"finance": [
		["Revenue contribution", "What revenue came from this agent?"],
		["Commission status", "Show this agent's commission status"],
	],
	"graduation": [
		["Renewal readiness", "Should this agent's contract be renewed?"],
		["Compliance issues", "Show this agent's compliance issues"],
		["Risk summary", "Show this agent's risk summary"],
	],
	"cohort": [
		["Active agents", "How many recruitment agents have active contracts?"],
		["Expiring contracts", "Which agent contracts are expiring soon?"],
	],
}

# Verbatim from JAVASCRIPT.js:1762-1797.
QUALITY_ACTION_QUESTION_MAP = {
	"profile": [
		["Quality Action overview", "Show this Quality Action"],
		["Problem", "What is the problem?"],
		["Current status", "What is the current status?"],
	],
	"journey": [
		["Root cause and resolution", "Show the root cause and resolution"],
		["Action taken", "What action has been taken?"],
		["Assigned person", "Who is assigned?"],
	],
	"academic": [
		["Due date", "When is it due?"],
		["Overdue check", "Is it overdue?"],
		["Completion status", "What is the current status?"],
	],
	"attendance": [
		["Closure readiness", "Is this Quality Action ready for closure?"],
		["Quality review", "Run a quality review of the root cause and action taken"],
		["Root-cause review", "Assess the root cause and resolution"],
	],
	"finance": [
		["Open Quality Actions", "Show all open Quality Actions"],
		["Overdue Quality Actions", "Show overdue Quality Actions"],
	],
	"graduation": [
		["NC findings", "Show NC findings"],
		["OFI findings", "Show OFI findings"],
	],
	"cohort": [
		["All open actions", "Show all open Quality Actions"],
		["All overdue actions", "Show overdue Quality Actions"],
		["All NC findings", "Show NC findings"],
		["All OFI findings", "Show OFI findings"],
	],
}

# Category labels, verbatim from renderCategoryOptions (JAVASCRIPT.js:1881-1921).
# The keys are shared across modules; only the labels differ.
STUDENT_CATEGORIES = [
	["profile", "Profile"],
	["journey", "Student Journey"],
	["academic", "Academic and Results"],
	["attendance", "Attendance and Leave"],
	["finance", "Fees and Payments"],
	["graduation", "Graduation and Risk"],
	["cohort", "Cohort Questions"],
]
RECRUITMENT_CATEGORIES = [
	["profile", "Profile and Contract"],
	["journey", "Agent Journey"],
	["academic", "Recruitment Performance"],
	["attendance", "Ratings"],
	["finance", "Revenue and Commission"],
	["graduation", "Compliance and Renewal"],
	["cohort", "Agent Portfolio"],
]
QUALITY_ACTION_CATEGORIES = [
	["profile", "Overview"],
	["journey", "Root Cause and Action"],
	["academic", "Status and Due Dates"],
	["attendance", "Review and Closure"],
	["finance", "Open and Overdue"],
	["graduation", "Finding Types"],
	["cohort", "Quality Action Portfolio"],
]

MODULE_QUESTIONS = {
	"student_journey": (STUDENT_QUESTION_MAP, STUDENT_CATEGORIES),
	"recruitment_agent": (RECRUITMENT_QUESTION_MAP, RECRUITMENT_CATEGORIES),
	"quality_action": (QUALITY_ACTION_QUESTION_MAP, QUALITY_ACTION_CATEGORIES),
}

# Whole categories held back because every question in them is cross-record.
UNSUPPORTED_CATEGORIES = {"cohort"}

# Individual questions whose backing capability was deliberately deferred.
# Keyed by module, matched on the question text so a reworded label can't
# silently re-enable one.
UNSUPPORTED_QUESTIONS = {
	"student_journey": {
		# ask_ucc/student_journey.py drops find_student_invoices() -- an
		# unfiltered invoice name-match too unreliable to answer from.
		"Show this student's fee and payment status",
		"Does this student have outstanding fees?",
		"Show this student's invoices",
		# handle_documents() counted attachments and called it compliance;
		# the legacy script's own warning conceded it proves nothing.
		"Show this student's attached admission documents",
		# FPS lives on fields this port doesn't read yet.
		"What is this student's FPS status?",
	},
	"recruitment_agent": {
		# Both came from the brute-force row scans dropped in
		# ask_ucc/recruitment_agent.py.
		"How many students did this agent recruit?",
		"Show students recruited by this agent",
		"What revenue came from this agent?",
		"Show this agent's commission status",
	},
	"quality_action": {
		# Cross-record, same as the cohort category.
		"Show all open Quality Actions",
		"Show overdue Quality Actions",
		"Show NC findings",
		"Show OFI findings",
	},
}


# ---------------------------------------------------------------------------
# Per-question routing -- which tool(s), and which fields of them, a question
# actually needs.
#
# The legacy assistant did NOT answer a question by dumping the record. It ran
# detect_intent() (server-scripts/UCC Ask - Student Journey.py:1314) to pick one
# intent, then one focused handler: handle_nationality() returned a single
# sentence about nationality, handle_course() a single sentence about the
# programme. Clicking "Nationality" and getting profile + academic record +
# attendance + graduation readiness is a regression against that, not a port of
# it.
#
# This restores the behaviour in the ported architecture's own terms. Rather
# than reintroducing detect_intent's ~190 lines of keyword rules, the guided
# questions are a fixed known set, so they route by exact text:
#
#     question -> {tool_name: (field, ...) or None}
#
# None means "the whole tool output" (the deliberately broad questions -- "Show
# this student's profile", "Show this student's journey"). A field tuple
# narrows within the tool, which is what makes a single-fact question render a
# single fact.
#
# The record-resolving primary tool always runs regardless of the route (it is
# what proves the record exists and the user may read it), but it only appears
# in the displayed facts when the route asks for it. See ai/orchestration.py.
#
# ponytail: exact-text routing, not keyword matching. A free-typed question
# still gets every tool, which is the right default when intent is unknown --
# and with AI on, more context is what the model wants. If free text later
# needs narrowing too, detect_intent's keyword lists are the thing to port,
# and they'd feed this same table.
_ALL = None

QUESTION_ROUTES = {
	"student_journey": {
		# --- profile: all from the one identity tool, one field each --------
		"Show this student's profile": {"get_student_profile": _ALL},
		"What course is this student in?": {
			"get_student_profile": ("student_name", "programme", "study_type"),
		},
		"What is this student's nationality?": {
			"get_student_profile": ("student_name", "nationality"),
		},
		"When did this student start?": {
			"get_student_profile": ("student_name", "commencement_date"),
		},
		"When is this student completing the course?": {
			"get_student_profile": ("student_name", "completion_date"),
		},
		# --- journey --------------------------------------------------------
		# The one question that genuinely means "everything": legacy
		# handle_lifecycle assembled the whole timeline.
		"Show this student's journey": {
			"get_student_profile": _ALL,
			"get_student_academic_record": _ALL,
			"get_student_attendance_and_leave": _ALL,
		},
		"Which module is this student in right now?": {
			"get_student_profile": ("student_name", "current_modules"),
		},
		"Show this student's class and student group": {
			"get_student_profile": ("student_name", "current_modules", "module_count"),
		},
		"Is this student on leave now?": {
			"get_student_attendance_and_leave": ("currently_on_leave", "leaves"),
		},
		# --- academic -------------------------------------------------------
		"Show all this student's results and grades": {"get_student_academic_record": _ALL},
		"Has this student finished all modules?": {
			"get_student_academic_record": (
				"total_modules", "submitted_count", "passed_count",
				"failed_count", "completion_percentage",
			),
		},
		"Has this student graduated?": {
			"get_student_profile": ("student_name", "academic_status", "graduated", "completion_date"),
		},
		# --- attendance -----------------------------------------------------
		"Show this student's attendance": {
			"get_student_attendance_and_leave": (
				"present", "late", "absent", "other", "total_records",
				"attendance_rate", "below_threshold", "monthly_trend",
			),
		},
		"Show this student's leave records": {
			"get_student_attendance_and_leave": ("leaves", "currently_on_leave"),
		},
		# --- graduation and risk --------------------------------------------
		"Is this student ready to graduate?": {
			"assess_student_graduation_readiness": ("ready_for_graduation", "blockers"),
		},
		"Show this student's risk summary": {
			"assess_student_graduation_readiness": ("risk_level", "risks", "recommended_actions"),
		},
		"What follow-up actions are needed for this student?": {
			"assess_student_graduation_readiness": ("recommended_actions", "risks"),
		},
	},
	"recruitment_agent": {
		"Show this agent's profile": {"get_agent_contract_summary": _ALL},
		"Is this agent's contract active?": {
			"get_agent_contract_summary": ("agent_name", "contract_status"),
		},
		"Show this agent's contract dates": {
			"get_agent_contract_summary": ("agent_name", "commencement_date", "expiry_date"),
		},
		"Show this agent's complete journey": {
			"get_agent_contract_summary": _ALL,
			"get_agent_ratings": _ALL,
			"assess_agent_contract_renewal": _ALL,
		},
		"Show this agent's latest contract": {"get_agent_contract_summary": _ALL},
		"When does this agent's contract expire?": {
			"get_agent_contract_summary": ("agent_name", "expiry_date", "contract_status"),
		},
		"What is this agent's latest rating?": {
			"get_agent_ratings": ("agent_name", "latest"),
		},
		"Does this agent meet the minimum rating?": {
			"get_agent_ratings": ("agent_name", "latest", "minimum_rating_likert", "meets_minimum_rating"),
		},
		"Should this agent's contract be renewed?": {
			"assess_agent_contract_renewal": ("recommendation", "issues"),
		},
		"Show this agent's compliance issues": {
			"assess_agent_contract_renewal": ("issues", "warnings"),
		},
		"Show this agent's risk summary": {
			"assess_agent_contract_renewal": ("issues", "warnings", "recommendation"),
		},
	},
	"quality_action": {
		"Show this Quality Action": {"get_quality_action_summary": _ALL},
		# problem / resolution / action taken / owner / due date all live
		# inside the resolution rows, so these share a route. Narrowing
		# further would mean restructuring the tool's output, which is a
		# bigger change than the reported problem warrants.
		"What is the problem?": {"get_quality_action_summary": ("title", "resolution_rows")},
		"Show the root cause and resolution": {"get_quality_action_summary": ("title", "resolution_rows")},
		"What action has been taken?": {"get_quality_action_summary": ("title", "resolution_rows")},
		"Who is assigned?": {"get_quality_action_summary": ("title", "resolution_rows")},
		"When is it due?": {"get_quality_action_summary": ("title", "resolution_rows")},
		"What is the current status?": {
			"get_quality_action_summary": ("title", "open_count", "completed_count", "overdue_count"),
		},
		"Is it overdue?": {
			"get_quality_action_summary": ("title", "overdue_count", "resolution_rows"),
		},
		"Is this Quality Action ready for closure?": {"assess_quality_action_closure": _ALL},
		"Run a quality review of the root cause and action taken": {"assess_quality_action_closure": _ALL},
		"Assess the root cause and resolution": {"assess_quality_action_closure": _ALL},
	},
}


def _normalise(question):
	return " ".join(str(question or "").split()).strip().lower()


_ROUTES_BY_NORMALISED = {
	module_key: {_normalise(q): route for q, route in routes.items()}
	for module_key, routes in QUESTION_ROUTES.items()
}


def route_for(module_key, question):
	"""The tool/field subset a question needs, or None for "no known route --
	run everything", which is the correct default for a free-typed question
	whose intent we cannot infer."""
	return _ROUTES_BY_NORMALISED.get(module_key, {}).get(_normalise(question))


def supported_questions(module_key):
	"""The legacy categories and questions for a module, minus the ones
	whose backing capability isn't built. Categories that end up empty are
	dropped rather than rendered as an empty button row."""
	question_map, categories = MODULE_QUESTIONS[module_key]
	unsupported = UNSUPPORTED_QUESTIONS.get(module_key, set())

	output = []
	for key, label in categories:
		if key in UNSUPPORTED_CATEGORIES:
			continue
		questions = [
			{"label": item[0], "question": item[1]}
			for item in question_map.get(key, [])
			if item[1] not in unsupported
		]
		if questions:
			output.append({"key": key, "label": label, "questions": questions})
	return output


# ---------------------------------------------------------------------------
# LOOKUP vs INTERPRETATION
#
# "What is this student's nationality?" is a field on a record. "Is this
# student ready to graduate?" is a judgement about several fields. Sending the
# first one to a language model costs money, adds latency, and puts an "AI
# generated" label on a value that was read straight out of the database --
# which is exactly the labelling CLAUDE.md §8.4 exists to prevent.
#
# So: a guided question with a known route is a VERIFIED LOOKUP and skips the
# AI layer entirely, UNLESS it is listed here. Free-typed questions always go
# to AI -- intent is unknown, so the safe assumption is that judgement is
# wanted.
#
# Listed by exact question text, the same key the routes use. An earlier note
# in this file said hand-tagging the questions was the thing to do "if an
# analytical question ever needs its own treatment". It does now.
INTERPRETIVE_QUESTIONS = {
	"student_journey": {
		"Is this student ready to graduate?",
		"Show this student's risk summary",
		"What follow-up actions are needed for this student?",
		"Has this student finished all modules?",
	},
	"recruitment_agent": {
		"Should this agent's contract be renewed?",
		"Show this agent's compliance issues",
		"Show this agent's risk summary",
		"Does this agent meet the minimum rating?",
	},
	"quality_action": {
		"Is this Quality Action ready for closure?",
		"Run a quality review of the root cause and action taken",
		"Assess the root cause and resolution",
	},
}

_INTERPRETIVE_BY_NORMALISED = {
	module_key: {_normalise(q) for q in questions}
	for module_key, questions in INTERPRETIVE_QUESTIONS.items()
}


def needs_interpretation(module_key, question):
	"""True when this question wants judgement rather than a field.

	A question with NO route is free text, so it needs interpretation by
	default: we cannot tell what was meant, and answering a judgement question
	with a bare field would be worse than the other way round.
	"""
	if route_for(module_key, question) is None:
		return True
	return _normalise(question) in _INTERPRETIVE_BY_NORMALISED.get(module_key, set())
