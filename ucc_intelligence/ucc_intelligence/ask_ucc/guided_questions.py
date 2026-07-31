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
