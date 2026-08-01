#!/usr/bin/env python3
"""Self-check for the verified-vs-AI split and the read-time data check.

    python3 tools/test_ask_ucc_answer_kind.py

WHAT THIS PROVES
The interface labels an answer "VERIFIED RECORD ANSWER" or "AI ANALYSIS" from
one field: `answer_kind`. That label is a claim about what happened on the
server, so this runs the real routing and confirms:

  - a field lookup never reaches the AI layer at all (not "reaches it and is
    labelled differently" -- never reaches it), and
  - a judgement question still does.

If those two ever swap, a value read from a database gets an AI label or a
model's opinion gets a verified one. Both are the failure this whole labelling
scheme exists to prevent, so both are asserted here rather than assumed from
the fact that the code reads that way.
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ucc_intelligence"))

checks = []


def report(ok, message):
	checks.append(bool(ok))
	print(("PASS" if ok else "FAIL") + ": " + message)
	return bool(ok)


TODAY = "2026-08-01"


def install_fake_frappe():
	frappe = types.ModuleType("frappe")
	frappe._ = lambda text: text
	frappe.PermissionError = type("PermissionError", (Exception,), {})
	frappe.ValidationError = type("ValidationError", (Exception,), {})
	frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
	frappe.throw = lambda message, exc=None: (_ for _ in ()).throw((exc or Exception)(message))
	frappe.logger = lambda *a, **k: types.SimpleNamespace(
		info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None)
	frappe.log_error = lambda **kwargs: None
	frappe.get_traceback = lambda: ""
	frappe.session = types.SimpleNamespace(user="tester@ucc")
	frappe.conf = {}

	def getdate(value=None):
		import datetime
		text = str(value or TODAY)
		return datetime.date(*[int(part) for part in text.split(" ")[0].split("-")])

	frappe.utils = types.SimpleNamespace(
		now=lambda: TODAY + " 15:14:00", nowdate=lambda: TODAY, getdate=getdate,
		cstr=lambda v: "" if v is None else str(v))
	sys.modules["frappe"] = frappe
	model = types.ModuleType("frappe.model")
	document = types.ModuleType("frappe.model.document")
	document.Document = type("Document", (), {})
	sys.modules["frappe.model"] = model
	sys.modules["frappe.model.document"] = document
	return frappe


install_fake_frappe()
from ucc_intelligence.ai import orchestration  # noqa: E402
from ucc_intelligence.ask_ucc import contracts, data_checks, guided_questions  # noqa: E402

# --- a fake student_journey module -----------------------------------------
PROFILE = {
	"status": "available",
	"student_applicant": "UCC-APP-250019",
	"student_name": "MENG, JINYANG",
	"nationality": "China",
	"programme": "Diploma",
	"academic_status": "Active",
	"graduated": False,
	"commencement_date": "2025-12-01",
	"completion_date": "2026-08-01",
}

calls = {"ai": 0}
orchestration.MODULES["student_journey"]["tools"] = {
	"get_student_profile": lambda name: dict(PROFILE),
	"get_student_academic_record": lambda name: {"status": "available", "modules_complete": True},
	"get_student_attendance_and_leave": lambda name: {"status": "available", "currently_on_leave": False},
}


class FakeClient:
	@staticmethod
	def is_enabled():
		return True

	@staticmethod
	def complete(system_prompt, user_prompt):
		calls["ai"] += 1
		return {"ok": True, "text": "Not ready to confirm yet.", "model": "test-model", "latency_ms": 10}


orchestration.ai_client = FakeClient
orchestration.guardrails = types.SimpleNamespace(validate=lambda text, names: (True, ""))
orchestration.prompts = types.SimpleNamespace(
	system_prompt_for=lambda key: "sys", build_user_prompt=lambda q, f: "user")


def ask(question):
	calls["ai"] = 0
	return orchestration.ask("student_journey", question, "UCC-APP-250019")


# --- a field lookup must NOT reach the model --------------------------------
for question in [
	"What is this student's nationality?",
	"When did this student start?",
	"Has this student graduated?",
	"What course is this student in?",
]:
	result = ask(question)
	report(result["answer_kind"] == "verified_record", "%r is a verified record answer" % question[:44])
	report(calls["ai"] == 0, "   ...and no model was called for it")
	report(result["answer"] is None, "   ...and it carries no AI text to mislabel")

# --- a judgement question must ---------------------------------------------
for question in [
	"Is this student ready to graduate?",
	"Show this student's risk summary",
	"What follow-up actions are needed for this student?",
]:
	result = ask(question)
	report(result["answer_kind"] == "ai_analysis", "%r is AI analysis" % question[:44])
	report(calls["ai"] == 1, "   ...and the model was called exactly once")

# --- free text: intent unknown, so interpretation is the safe assumption ----
result = ask("does anything look wrong with this record")
report(result["answer_kind"] == "ai_analysis", "a free-typed question goes to AI")
report(calls["ai"] == 1, "   ...and calls the model")

# --- AI off: a lookup is unaffected, a judgement question says so -----------
FakeClient.is_enabled = staticmethod(lambda: False)
report(ask("What is this student's nationality?")["answer_kind"] == "verified_record",
	"with AI switched off a lookup still answers -- it never needed AI")
judgement = ask("Is this student ready to graduate?")
report(judgement["answer_kind"] == "unavailable" and judgement["ai_status"] == "disabled",
	"with AI switched off a judgement question reports that it could not be interpreted")
FakeClient.is_enabled = staticmethod(lambda: True)

# --- an unreadable record is neither kind ----------------------------------
orchestration.MODULES["student_journey"]["tools"]["get_student_profile"] = (
	lambda name: {"status": "permission_denied", "message": "Not permitted"})
blocked = ask("What is this student's nationality?")
report(blocked["answer_kind"] == "unavailable" and blocked["ai_status"] == "permission_denied",
	"a record this user may not read is never dressed up as a verified answer")
report(calls["ai"] == 0, "   ...and no model saw it either")
orchestration.MODULES["student_journey"]["tools"]["get_student_profile"] = lambda name: dict(PROFILE)

# --- the data check: two fields compared, no model --------------------------
warnings = data_checks.run("student_journey", PROFILE)
report(len(warnings) == 1 and warnings[0]["code"] == "completion_date_reached_not_graduated",
	"completion date reached with graduation not recorded raises exactly one warning")
report("Confirm whether the graduation status needs updating" in warnings[0]["message"],
	"and it asks for confirmation rather than asserting a conclusion")
report(data_checks.run("student_journey", dict(PROFILE, graduated=True)) == [],
	"a student who HAS graduated raises nothing")
report(data_checks.run("student_journey", dict(PROFILE, academic_status="Graduated")) == [],
	"nor does one whose status already says so in words")
report(data_checks.run("student_journey", dict(PROFILE, completion_date="2027-01-01")) == [],
	"nor does one whose completion date is still in the future")
report(data_checks.run("student_journey", dict(PROFILE, completion_date="Not recorded")) == [],
	"an unrecorded completion date is not an inconsistency")
report(data_checks.run("student_journey", {"status": "permission_denied"}) == [],
	"an unreadable record is not checked")
report(data_checks.run("quality_action", {"status": "available"}) == [],
	"a module with no checks defined returns nothing rather than raising")

# --- the response contract --------------------------------------------------
result = ask("Has this student graduated?")
response = contracts.build_response("student_journey", None, result)
report(response["answer_kind"] == "verified_record", "the contract carries answer_kind through")
report(response["checked_at"], "and a timestamp the card can show")
context = response["record_context"]
report(context and context["record"] == "UCC-APP-250019", "the context panel gets the record id")
report([f["label"] for f in context["fields"]][:2] == ["Name", "Record"],
	"and its fields are the fixed summary list, in order")
report(all(not isinstance(f["value"], bool) for f in context["fields"]),
	"booleans are rendered as Yes/No, not true/false")
report(len(response["warnings"]) == 1, "the warning travels with the answer")

blocked_response = contracts.build_response("student_journey", None, {
	"answer_kind": "unavailable", "primary": {"status": "permission_denied"}, "facts": {}})
report(blocked_response["record_context"] is None,
	"an unreadable record populates NO context panel -- no shell of empty rows")

# --- every interpretive question is one the UI actually offers ---------------
for module_key, questions in guided_questions.INTERPRETIVE_QUESTIONS.items():
	offered = {item["question"] for category in guided_questions.supported_questions(module_key)
		for item in category["questions"]}
	missing = sorted(questions - offered)
	report(not missing, "%s: every interpretive question is a real button (%s)" % (module_key, missing))

print(("PASS" if all(checks) else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
sys.exit(0 if all(checks) else 1)
