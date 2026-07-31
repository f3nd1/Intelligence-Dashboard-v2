#!/usr/bin/env python3
"""Self-check for Ask UCC's first build -- the Quality Action module
(docs/architecture/ask-ucc-phase-plan.md §6).

Covers: quality_action.py's tool functions against synthetic data
mirroring the exact legacy formulas (server-scripts/UCC Ask - Quality
Action.py's find_resolution_field/root_cause_review/action_review), the
citation guardrail actually catching a fabricated reference (not just the
happy path -- the plan explicitly required this), ai/client.py's
config-gated early-return paths, orchestration's end-to-end assembly with
a stubbed AI client, and api.py's ask_quality_action() including
conversation/message/usage-log persistence.

    python3 tools/test_ucc_intelligence_ask_ucc.py
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
checks = []


def report(ok, message):
	print(("PASS" if ok else "FAIL") + ": " + message)
	checks.append(ok)
	return ok


sys.path.insert(0, str(ROOT / "ucc_intelligence"))


# ============================================================
# Stub frappe
# ============================================================
class State:
	quality_actions = {}  # name -> FakeDoc
	agent_contracts = {}
	student_applicants = {}
	students = {}
	list_rows = {}  # doctype -> rows
	resolution_field_meta = "resolutions"  # which field find_resolution_field() should discover
	settings = None
	conf = {}
	conversations = []  # list of FakeDoc (UCC AI Conversation)
	messages = []
	usage_logs = []
	post_request_response = None
	post_request_error = None
	denied_doctypes = set()


class FakeDoc(dict):
	def get(self, key, default=None):
		return dict.get(self, key, default)

	def __getattr__(self, name):
		try:
			return self[name]
		except KeyError:
			raise AttributeError(name)


class FakeMetaField:
	def __init__(self, fieldname, fieldtype, options=None):
		self.fieldname = fieldname
		self.fieldtype = fieldtype
		self.options = options


class FakeMeta:
	def __init__(self, doctype):
		self.doctype = doctype
		if doctype == "Quality Action":
			self.fields = [FakeMetaField(State.resolution_field_meta, "Table", "Quality Action Resolution")]
		else:
			self.fields = []

	def has_field(self, fieldname):
		return any(f.fieldname == fieldname for f in self.fields) or fieldname == State.resolution_field_meta


class FakeNewDoc:
	"""Mimics enough of frappe.model.document.Document for
	ask_ucc/conversations.py: attribute set/get, insert() assigning a name
	and recording itself into the right State list, save() as a no-op
	persist."""
	_counters = {"UCC AI Conversation": 0, "UCC AI Message": 0, "UCC AI Usage Log": 0}

	def __init__(self, doctype):
		self.doctype = doctype
		self.name = None

	def insert(self, ignore_permissions=False):
		FakeNewDoc._counters[self.doctype] = FakeNewDoc._counters.get(self.doctype, 0) + 1
		self.name = "%s-%d" % (self.doctype.replace(" ", "-").lower(), FakeNewDoc._counters[self.doctype])
		if self.doctype == "UCC AI Conversation":
			State.conversations.append(self)
		elif self.doctype == "UCC AI Message":
			State.messages.append(self)
		elif self.doctype == "UCC AI Usage Log":
			State.usage_logs.append(self)
		return self

	def save(self):
		return self


DOC_STORES = {
	"Quality Action": "quality_actions",
	"Agent Contract": "agent_contracts",
	"Student Applicant": "student_applicants",
	"Student": "students",
}


def _get_doc(doctype, name):
	store_name = DOC_STORES.get(doctype)
	if store_name:
		store = getattr(State, store_name)
		if name not in store:
			raise frappe_stub.DoesNotExistError("no such %s" % doctype)
		return store[name]
	if doctype == "Supplier Rating":
		for row in State.list_rows.get("Supplier Rating", []):
			if row.get("name") == name:
				return FakeDoc(row)
		raise frappe_stub.DoesNotExistError("no such Supplier Rating")
	if doctype == "Student Admission UCC":
		for row in State.list_rows.get("Student Admission UCC", []):
			if row.get("name") == name:
				return FakeDoc(row)
		raise frappe_stub.DoesNotExistError("no such Student Admission UCC")
	if doctype == "UCC AI Conversation":
		for c in State.conversations:
			if c.name == name:
				return c
	raise frappe_stub.DoesNotExistError("no such %s" % doctype)


def _new_doc(doctype):
	return FakeNewDoc(doctype)


def _get_all(doctype, filters=None, order_by=None, limit_page_length=None):
	if doctype == "UCC AI Conversation":
		matches = [
			c for c in State.conversations
			if all(getattr(c, k, None) == v for k, v in (filters or {}).items())
		]
		return [{"name": c.name} for c in matches[:1]] if matches else []
	return []


def _get_meta(doctype):
	return FakeMeta(doctype)


def _get_single(doctype):
	if doctype == "UCC Intelligence Settings":
		return State.settings
	raise frappe_stub.DoesNotExistError(doctype)


def _make_post_request(url, headers=None, data=None, timeout=None):
	if State.post_request_error:
		raise State.post_request_error
	return State.post_request_response


class FakeUtils:
	cstr = staticmethod(lambda v: "" if v is None else str(v))
	cint = staticmethod(lambda v: int(v) if str(v).strip().lstrip("-").isdigit() else 0)
	today = staticmethod(lambda: "2026-07-30")
	now = staticmethod(lambda: "2026-07-30 12:00:00")
	formatdate = staticmethod(lambda v, fmt=None: str(v))
	generate_hash = staticmethod(lambda length=10: "h" * length)


class _Session:
	user = "staff@ucc.edu.sg"


frappe_stub = types.ModuleType("frappe")
frappe_stub.get_doc = _get_doc
frappe_stub.new_doc = _new_doc
frappe_stub.get_all = _get_all


def _get_list(doctype, filters=None, fields=None, order_by=None, limit_page_length=None):
	if doctype in State.denied_doctypes:
		raise frappe_stub.PermissionError("not permitted to read " + doctype)
	rows = [dict(r) for r in State.list_rows.get(doctype, [])]
	for key, value in (filters or {}).items():
		if isinstance(value, list):
			continue  # docstatus-style operator filters: not modelled, pass through
		rows = [r for r in rows if r.get(key) == value]
	return rows


frappe_stub.get_list = _get_list
frappe_stub.get_meta = _get_meta
frappe_stub.get_single = _get_single
frappe_stub.session = _Session()
frappe_stub.utils = FakeUtils()
frappe_stub.conf = State.conf
frappe_stub.as_json = lambda v: str(v)
frappe_stub.make_post_request = _make_post_request
frappe_stub.generate_hash = lambda length=10: "h" * length
frappe_stub.whitelist = lambda *a, **k: (lambda f: f)
frappe_stub.logger = lambda *a, **k: types.SimpleNamespace(
	info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None,
)
frappe_stub.throw = lambda msg: (_ for _ in ()).throw(Exception(msg))


class _DoesNotExistError(Exception):
	pass


class _PermissionError(Exception):
	pass


frappe_stub.DoesNotExistError = _DoesNotExistError
frappe_stub.PermissionError = _PermissionError
sys.modules["frappe"] = frappe_stub

frappe_model_stub = types.ModuleType("frappe.model")
frappe_model_document_stub = types.ModuleType("frappe.model.document")
frappe_model_document_stub.Document = object
sys.modules["frappe.model"] = frappe_model_stub
sys.modules["frappe.model.document"] = frappe_model_document_stub

frappe_utils_module = types.ModuleType("frappe.utils")
frappe_utils_module.add_days = lambda date_str, days: "2026-08-29"
sys.modules["frappe.utils"] = frappe_utils_module

import ucc_intelligence.ask_ucc.quality_action as qa_tools  # noqa: E402
import ucc_intelligence.ai.guardrails as guardrails  # noqa: E402
import ucc_intelligence.ai.client as ai_client  # noqa: E402
import ucc_intelligence.ai.orchestration as orchestration  # noqa: E402
import ucc_intelligence.ask_ucc.conversations as conversations  # noqa: E402
import ucc_intelligence.ask_ucc.contracts as contracts  # noqa: E402


def make_row(**kw):
	base = {"finding_type": "NC", "status": "Open", "full_name": "Jane Tan", "target_date": "2020-01-01", "completion_by": None, "problem": "", "resolution": "", "action_taken": ""}
	base.update(kw)
	return FakeDoc(base)


# ============================================================
# quality_action.py tool functions
# ============================================================
State.quality_actions["QA-0001"] = FakeDoc({
	"name": "QA-0001",
	"custom_subject": "Late fee reconciliation NC",
	"resolutions": [
		make_row(finding_type="NC", status="Completed", full_name="Jane Tan", target_date="2020-01-01", completion_by="2020-01-10",
			problem="Fees were not reconciled monthly.",
			resolution="Because the finance team lacked a checklist, reconciliation was inconsistent. Implement a monthly checklist and monitor compliance to prevent recurrence.",
			action_taken="Checklist implemented and verified; evidence attached as a screenshot."),
		make_row(finding_type="OFI", status="Open", full_name="Ravi Kumar", target_date="2020-01-01", completion_by=None,
			problem="", resolution="", action_taken=""),
	],
})

report(qa_tools.find_resolution_field() == "resolutions", "find_resolution_field discovers the child table via meta Table+options, not a hardcoded name")

summary = qa_tools.get_quality_action_summary("QA-0001")
report(summary["status"] == "available", "get_quality_action_summary resolves an existing record")
report(summary["title"] == "Late fee reconciliation NC", "title resolves via the custom_subject candidate field")
report(summary["open_count"] == 1 and summary["completed_count"] == 1, "open/completed counts match the 2 synthetic rows (1 Completed, 1 Open)")
report(len(summary["resolution_rows"]) == 2, "both resolution rows are summarised")

missing = qa_tools.get_quality_action_summary("QA-does-not-exist")
report(missing["status"] == "not_found", "a non-existent Quality Action reports not_found, not a crash")

closure = qa_tools.assess_quality_action_closure("QA-0001")
report(closure["status"] == "available", "assess_quality_action_closure resolves an existing record")
report(closure["ready_count"] == 1, "exactly 1 of 2 rows is ready (the well-documented Completed row)")
report(closure["assessments"][0]["ready"] is True, "row 1 (complete, well-documented) is assessed ready")
report(closure["assessments"][1]["ready"] is False, "row 2 (open, no resolution/action text) is assessed not ready")
report("Status is not completed." in closure["assessments"][1]["reasons"], "not-ready row 2 gives 'Status is not completed.' as a reason, matching the legacy rule")


# ============================================================
# ai/guardrails.py -- MUST catch a fabricated citation, not just pass the happy path
# ============================================================
ok, reason = guardrails.validate("The Quality Action QA-0001 has 1 open item.", ["QA-0001", "Late fee reconciliation NC"])
report(ok is True, "a clean answer referencing only supplied facts passes the guardrail")

ok, reason = guardrails.validate("See also related Quality Action qa9f3k2z01 for context.", ["QA-0001", "Late fee reconciliation NC"])
report(ok is False, "an answer referencing a record-shaped token NOT in the supplied facts is REJECTED")
report(reason is not None and "qa9f3k2z01" in reason, "the rejection reason names the specific unverified token")

ok, reason = guardrails.validate("", ["QA-0001"])
report(ok is False, "an empty answer is rejected")

ok, reason = guardrails.validate("x" * 5000, ["QA-0001"])
report(ok is False, "an excessively long answer is rejected")

ok, reason = guardrails.validate("This appears reasonably complete and well documented.", ["QA-0001"])
report(ok is True, "ordinary English words that happen to match the token length range are NOT flagged (no digits in them)")


# ============================================================
# ai/client.py -- config-gated early-return paths (no network call made)
# ============================================================
State.settings = FakeDoc({"enable_ai": 0, "ai_provider": "OpenAI", "ai_model": "gpt-4o-mini", "max_output_tokens": 500, "default_temperature": 0.2, "ai_request_timeout_seconds": 30})
report(ai_client.is_enabled() is False, "is_enabled() False when enable_ai=0")
result = ai_client.complete("system", "user")
report(result["ok"] is False and result["status"] == "disabled", "complete() returns status=disabled without attempting a network call")

State.settings = FakeDoc({"enable_ai": 1, "ai_provider": "", "ai_model": "", "max_output_tokens": 0, "default_temperature": None, "ai_request_timeout_seconds": 0})
result = ai_client.complete("system", "user")
report(result["ok"] is False and result["status"] == "unavailable", "complete() reports unavailable when provider/model are empty")

State.settings = FakeDoc({"enable_ai": 1, "ai_provider": "OpenAI", "ai_model": "gpt-4o-mini", "max_output_tokens": 500, "default_temperature": 0.2, "ai_request_timeout_seconds": 30})
frappe_stub.conf = {}
result = ai_client.complete("system", "user")
report(result["ok"] is False and result["status"] == "unavailable" and "site_config" in result["message"], "complete() reports unavailable, naming site_config, when no API key is configured")

frappe_stub.conf = {ai_client.AI_API_KEY_SITE_CONFIG_KEY: "sk-fake-test-key"}
State.settings = FakeDoc({"enable_ai": 1, "ai_provider": "Anthropic", "ai_model": "some-model", "max_output_tokens": 500, "default_temperature": 0.2, "ai_request_timeout_seconds": 30})
result = ai_client.complete("system", "user")
report(result["ok"] is False and "OpenAI" in result["message"], "complete() reports unavailable for a provider with no implementation yet, doesn't silently call OpenAI anyway")

# a successful call, real shape
State.settings = FakeDoc({"enable_ai": 1, "ai_provider": "OpenAI", "ai_model": "gpt-4o-mini", "max_output_tokens": 500, "default_temperature": 0.2, "ai_request_timeout_seconds": 30})
State.post_request_response = {"choices": [{"message": {"content": "The item is open."}}], "model": "gpt-4o-mini", "usage": {"total_tokens": 42}}
result = ai_client.complete("system", "user")
report(result["ok"] is True and result["text"] == "The item is open." and result["token_usage"] == 42, "a successful provider response is parsed into the expected shape")

# an exception during the call never leaks into the returned message
State.post_request_response = None
State.post_request_error = RuntimeError("connection reset by peer, Authorization: Bearer sk-should-never-appear")
result = ai_client.complete("system", "user")
report(result["ok"] is False, "a network error is caught, not raised")
report("sk-should-never-appear" not in result["message"], "the classified error message never echoes the raw exception text (which could contain the key)")
State.post_request_error = None


# ============================================================
# ai/orchestration.py -- end to end with the stubbed client
# ============================================================
State.settings = FakeDoc({"enable_ai": 0})
result = orchestration.ask("quality_action", "Is this ready to close?", "QA-0001")
report(result["ai_status"] == "disabled", "orchestration reports disabled and still returns facts when AI is off")
report(result["answer"] is None and result["facts"]["get_quality_action_summary"]["status"] == "available", "facts are populated even though there's no AI answer (progressive enhancement)")
report(result["tools_called"] == ["get_quality_action_summary", "assess_quality_action_closure"], "both tools are called for a resolvable record")

result = orchestration.ask("quality_action", "What about it?", "QA-does-not-exist")
report(result["ai_status"] == "not_found", "orchestration surfaces the tool's not_found status directly, only 1 tool attempted")
report(result["tools_called"] == ["get_quality_action_summary"], "closure assessment is not attempted when the record itself doesn't resolve")

State.settings = FakeDoc({"enable_ai": 1, "ai_provider": "OpenAI", "ai_model": "gpt-4o-mini", "max_output_tokens": 500, "default_temperature": 0.2, "ai_request_timeout_seconds": 30})
State.post_request_response = {"choices": [{"message": {"content": "1 of 2 resolution rows is ready for closure."}}], "model": "gpt-4o-mini", "usage": {"total_tokens": 55}}
result = orchestration.ask("quality_action", "Is this ready to close?", "QA-0001")
report(result["ai_status"] == "available" and result["answer"]["text"].startswith("1 of 2"), "a clean AI answer passes through end to end")

# the guardrail actually fires inside orchestration too, not just in isolation
State.post_request_response = {"choices": [{"message": {"content": "Also check qa9f3k2z01 for a similar issue."}}], "model": "gpt-4o-mini", "usage": {"total_tokens": 12}}
result = orchestration.ask("quality_action", "Is this ready to close?", "QA-0001")
report(result["ai_status"] == "guardrail_blocked", "orchestration blocks an AI answer that references an unverified record, end to end")
report(result["answer"] is None, "a guardrail-blocked response never sets answer -- facts-only is what gets returned")


# ============================================================
# ask_ucc/conversations.py -- persistence
# ============================================================
State.conversations = []
State.messages = []
State.usage_logs = []
State.post_request_response = {"choices": [{"message": {"content": "1 of 2 resolution rows is ready."}}], "model": "gpt-4o-mini", "usage": {"total_tokens": 30}}
result = orchestration.ask("quality_action", "Is this ready to close?", "QA-0001")
conversation = conversations.get_or_create_conversation("Quality Action", "Quality Action", "QA-0001")
report(conversation.name is not None, "a new conversation is created and given a name")
report(len(State.conversations) == 1, "exactly one conversation row exists after the first call")

conversation_again = conversations.get_or_create_conversation("Quality Action", "Quality Action", "QA-0001")
report(conversation_again.name == conversation.name, "a second call for the same (user, module, record) reuses the existing conversation, doesn't create a new one")
report(len(State.conversations) == 1, "still exactly one conversation row -- confirmed reuse, not just a matching name by coincidence")

conversations.record_message(conversation, "user", "Is this ready to close?")
report(len(State.messages) == 1 and State.messages[0].role == "user", "a user message is recorded")

conversations.record_usage_log(conversation, "Quality Action", result)
report(len(State.usage_logs) == 1, "a usage log row is recorded")
report(State.usage_logs[0].tools_called == str(result["tools_called"]), "usage log records which tools were actually called")


# ============================================================
# The memory toggle (UCC Intelligence Settings.enable_persistent_conversations)
# -- REAL, not a placeholder: it must genuinely stop conversation storage.
# ============================================================
State.settings = FakeDoc({"enable_ai": 1, "ai_provider": "OpenAI", "ai_model": "gpt-4o-mini", "max_output_tokens": 500,
	"default_temperature": 0.2, "ai_request_timeout_seconds": 30, "enable_persistent_conversations": 1})
report(conversations.persistence_enabled() is True, "persistence_enabled() True when the toggle is on")
State.settings = FakeDoc({"enable_ai": 1, "ai_provider": "OpenAI", "ai_model": "gpt-4o-mini", "max_output_tokens": 500,
	"default_temperature": 0.2, "ai_request_timeout_seconds": 30, "enable_persistent_conversations": 0})
report(conversations.persistence_enabled() is False, "persistence_enabled() False when the toggle is off")

# toggle OFF: no conversation, no messages -- but the audit log still written
State.conversations = []
State.messages = []
State.usage_logs = []
returned = conversations.persist_turn("Quality Action", "Quality Action", "QA-0001", "Is this ready?", result)
report(returned is None, "persist_turn returns None when persistence is off (contract already allows a null conversation_id)")
report(len(State.conversations) == 0 and len(State.messages) == 0, "toggle OFF stores NO conversation and NO messages")
report(len(State.usage_logs) == 1, "toggle OFF still writes the Usage Log -- audit trail is deliberately not gated by a memory setting")
report(State.usage_logs[0].conversation is None, "the usage log row tolerates a null conversation link when persistence is off")

# toggle ON: full persistence
State.settings = FakeDoc({"enable_ai": 1, "ai_provider": "OpenAI", "ai_model": "gpt-4o-mini", "max_output_tokens": 500,
	"default_temperature": 0.2, "ai_request_timeout_seconds": 30, "enable_persistent_conversations": 1})
State.conversations = []
State.messages = []
State.usage_logs = []
returned = conversations.persist_turn("Quality Action", "Quality Action", "QA-0001", "Is this ready?", result)
report(returned is not None, "persist_turn returns the conversation when persistence is on")
report(len(State.conversations) == 1 and len(State.messages) == 2 and len(State.usage_logs) == 1,
	"toggle ON stores 1 conversation, 2 messages (user+assistant), 1 usage log")

# a settings-read fault must not silently start dropping history
_broken_get_single = frappe_stub.get_single
frappe_stub.get_single = lambda dt: (_ for _ in ()).throw(Exception("settings unreadable"))
report(conversations.persistence_enabled() is True, "persistence_enabled() defaults ON when the setting can't be read at all -- a read fault must not silently discard conversations")
frappe_stub.get_single = _broken_get_single


# ============================================================
# ask_ucc/contracts.py + api.py end to end
# ============================================================
response = contracts.build_response("quality_action", conversation, result)
for key in ("ok", "conversation_id", "ai_status", "answer", "facts", "sources", "warnings"):
	report(key in response, "response contract includes %r" % key)
report(response["sources"][0] == {"doctype": "Quality Action", "record": "QA-0001", "status": "available"}, "sources correctly cites the real resolved Quality Action")

import ucc_intelligence.api as api  # noqa: E402

State.conversations = []
State.messages = []
State.usage_logs = []
State.post_request_response = {"choices": [{"message": {"content": "1 of 2 resolution rows is ready for closure."}}], "model": "gpt-4o-mini", "usage": {"total_tokens": 44}}
full_response = api.ask_ucc("quality_action", "Is this ready to close?", "QA-0001")
report(full_response["ok"] is True, "api.ask_ucc() returns ok=True end to end")
report(full_response["ai_status"] == "available", "api.ask_ucc() end-to-end AI path works with everything stubbed")
report(len(State.conversations) == 1 and len(State.messages) == 2 and len(State.usage_logs) == 1,
	"api.ask_ucc() persists exactly 1 conversation, 2 messages (user+assistant), 1 usage log")

try:
	api.ask_ucc("quality_action", "", "QA-0001")
	report(False, "an empty question should raise, not silently proceed")
except Exception:
	report(True, "an empty question raises rather than silently proceeding")

try:
	api.ask_ucc("quality_action", "A question", "")
	report(False, "a missing quality_action should raise, not silently proceed")
except Exception:
	report(True, "a missing quality_action raises rather than silently proceeding")

# a permission-denied tool result surfaces through the full contract, not silently
State.quality_actions["QA-blocked"] = FakeDoc({"name": "QA-blocked"})


def _blocked_get_doc(doctype, name):
	if doctype == "Quality Action" and name == "QA-blocked":
		raise frappe_stub.PermissionError("not permitted")
	return _get_doc(doctype, name)


frappe_stub.get_doc = _blocked_get_doc
blocked_response = api.ask_ucc("quality_action", "What is this?", "QA-blocked")
report(blocked_response["sources"][0]["status"] == "permission_denied", "a permission-denied source reports permission_denied through the full stack, not a silent bypass or a crash")
frappe_stub.get_doc = _get_doc



# ============================================================
# Recruitment Agent module -- same pipeline, own tools + heuristics
# ============================================================
import ucc_intelligence.ask_ucc.recruitment_agent as ra_tools  # noqa: E402

State.agent_contracts["AC-0001"] = FakeDoc({
	"name": "AC-0001",
	"party_name": "Bright Futures Education",
	"personal_id": "UEN-12345",
	"commencement_date": "2024-01-01",
	"end_date": "2027-12-31",
})
State.list_rows["Supplier Rating"] = [
	{"name": "SR-1", "supplier_name": "Bright Futures Education", "modified": "2026-01-01",
	 "rating_likert": "4.2", "status": "Approved", "evaluation_stage": "Annual"},
]

summary = ra_tools.get_agent_contract_summary("AC-0001")
report(summary["status"] == "available", "RA: get_agent_contract_summary resolves an existing contract")
report(summary["agent_name"] == "Bright Futures Education", "RA: agent name resolves via the party_name candidate")
report(summary["contract_status"] == "Active", "RA: contract_status computes Active from dates, per the legacy ladder")

ratings = ra_tools.get_agent_ratings("AC-0001")
report(ratings["status"] == "available" and len(ratings["ratings"]) == 1, "RA: ratings resolve via the candidate filter list")
report(ratings["meets_minimum_rating"] is True, "RA: 4.2 meets the 3.5 minimum")

renewal = ra_tools.assess_agent_contract_renewal("AC-0001")
report(renewal["issues"] == [], "RA: a compliant contract produces no issues")
report(renewal["recommendation"].startswith("Eligible for continuation"), "RA: a compliant contract is recommended for continuation")

# expired contract -> Expired status, and the first rung of the renewal ladder
State.agent_contracts["AC-EXPIRED"] = FakeDoc({
	"name": "AC-EXPIRED", "party_name": "Old Partner Ltd",
	"commencement_date": "2019-01-01", "end_date": "2020-01-01",
})
expired = ra_tools.assess_agent_contract_renewal("AC-EXPIRED")
report(expired["contract_status"] == "Expired", "RA: a past end_date computes Expired")
report("Contract status is Expired." in expired["issues"], "RA: expired status is reported as a compliance issue")
report(expired["recommendation"].startswith("Do not renew automatically"), "RA: expired hits the first rung of the renewal ladder")

# below-threshold rating -> the 3.5 rule fires
State.agent_contracts["AC-LOW"] = FakeDoc({
	"name": "AC-LOW", "party_name": "Weak Rating Agency",
	"commencement_date": "2024-01-01", "end_date": "2027-12-31",
})
State.list_rows["Supplier Rating"].append(
	{"name": "SR-2", "supplier_name": "Weak Rating Agency", "modified": "2026-01-01",
	 "rating_likert": "2.1", "status": "Conditional"})
low = ra_tools.assess_agent_contract_renewal("AC-LOW")
report("Latest rating_likert is below the 3.5 minimum." in low["issues"], "RA: a sub-3.5 rating is flagged as an issue")
report(low["recommendation"].startswith("Do not renew without corrective action"), "RA: a sub-3.5 rating blocks renewal")
report(any("requires attention" in i for i in low["issues"]), "RA: a Conditional rating status is flagged for attention")

report(ra_tools.get_agent_contract_summary("AC-nope")["status"] == "not_found", "RA: a missing contract reports not_found")


# ============================================================
# Student Journey module -- same pipeline, own tools + heuristics
# ============================================================
import ucc_intelligence.ask_ucc.student_journey as sj_tools  # noqa: E402

State.student_applicants["SA-0001"] = FakeDoc({
	"name": "SA-0001", "first_name": "Mei", "last_name": "Lim",
	"student_type": "Full Time", "nationality": "Singaporean", "program": "Diploma in Business",
})
State.students["STU-1"] = FakeDoc({"name": "STU-1", "student_name": "Mei Lim", "custom_academic_status": "Active"})
State.list_rows["Student Admission UCC"] = [{
	"name": "AD-1", "student_applicant": "SA-0001", "student": "STU-1", "student_name": "Mei Lim",
	"program": "Diploma in Business", "date_of_commencement": "2024-01-15",
	"completion_date": "", "application_status": "Admitted", "modified": "2026-01-01",
	"modules": [
		FakeDoc({"module_code": "BUS101", "module_name": "Intro to Business", "abbreviation": "IB",
			"start_date": "2024-02-01", "end_date": "2024-05-01"}),
		FakeDoc({"module_code": "BUS102", "module_name": "Accounting Basics", "abbreviation": "AB",
			"start_date": "2024-06-01", "end_date": "2099-01-01"}),
	],
}]
State.list_rows["Assessment Result"] = [{
	"name": "AR-1", "docstatus": 1, "student": "STU-1", "course": "BUS101",
	"assessment_name": "BUS101 Final", "total_score": 78, "maximum_score": 100,
	"grade": "B", "assessment_date": "2024-05-10", "modified": "2024-05-10",
}]
State.list_rows["Student Attendance"] = [
	{"name": "AT-%d" % i, "student": "STU-1", "date": "2024-03-0%d" % (i + 1), "status": "Present"}
	for i in range(8)
] + [
	{"name": "AT-X", "student": "STU-1", "date": "2024-03-09", "status": "Absent"},
	{"name": "AT-Y", "student": "STU-1", "date": "2024-03-10", "status": "Absent"},
]
State.list_rows["Student Leave Application"] = []

profile = sj_tools.get_student_profile("SA-0001")
report(profile["status"] == "available", "SJ: get_student_profile resolves an existing applicant")
report(profile["student_name"] == "Mei Lim", "SJ: full name assembles from first/middle/last")
report(profile["student_id"] == "STU-1", "SJ: the linked Student id resolves via the admission record")
report(profile["commencement_date"] == "2024-01-15", "SJ: commencement resolves via the date_of_commencement candidate")
report(profile["graduated"] is False, "SJ: academic status Active is not treated as graduated")

academic = sj_tools.get_student_academic_record("SA-0001")
report(academic["total_modules"] == 2, "SJ: both admission modules are loaded from the child table")
report(academic["submitted_count"] == 1 and academic["not_graded_count"] == 1,
	"SJ: the assessment result matches BUS101 only, leaving BUS102 ungraded")
report(academic["passed_count"] == 1, "SJ: grade B classifies as passed via numeric_grade_passed")
report(academic["average_score"] == 78.0, "SJ: average score computed from the matched result")
report(academic["modules_not_ended"] == 1, "SJ: the module ending in 2099 counts as not ended")

attendance = sj_tools.get_student_attendance_and_leave("SA-0001")
report(attendance["present"] == 8 and attendance["absent"] == 2, "SJ: attendance totals count correctly")
report(attendance["attendance_rate"] == 80.0, "SJ: attendance rate is (present+late)/total, per the legacy formula")
report(attendance["below_threshold"] is True, "SJ: 80% is flagged below the 90% threshold")
report(attendance["currently_on_leave"] is False, "SJ: no leave records means not currently on leave")

readiness = sj_tools.assess_student_graduation_readiness("SA-0001")
report(readiness["ready_for_graduation"] is False, "SJ: outstanding modules block graduation readiness")
report(any("have not ended" in b for b in readiness["blockers"]), "SJ: the not-ended module is reported as a blocker")
report(any("not submitted" in b for b in readiness["blockers"]), "SJ: the missing result is reported as a blocker")
report(readiness["finance"] == "unavailable",
	"SJ: finance is explicitly reported unavailable, NOT silently dropped from the blocker list")
report(readiness["risk_level"] in ("Medium", "High"), "SJ: risks produce a non-Low risk level")
report(any("below 90%" in r for r in readiness["risks"]), "SJ: low attendance is reported as a risk")

report(sj_tools.get_student_profile("SA-nope")["status"] == "not_found", "SJ: a missing applicant reports not_found")


# ============================================================
# THE GUARDRAIL, PER MODULE -- a fabricated citation must be caught for
# all three, not just the one it was first built against.
# ============================================================
State.settings = FakeDoc({"enable_ai": 1, "ai_provider": "OpenAI", "ai_model": "gpt-4o-mini",
	"max_output_tokens": 500, "default_temperature": 0.2, "ai_request_timeout_seconds": 30,
	"enable_persistent_conversations": 1})

GUARDRAIL_CASES = [
	("quality_action", "QA-0001", "Late fee reconciliation NC"),
	("recruitment_agent", "AC-0001", "Bright Futures Education"),
	("student_journey", "SA-0001", "Mei Lim"),
]

for module_key, record_name, human_name in GUARDRAIL_CASES:
	# clean answer -> passes
	State.post_request_response = {"choices": [{"message": {"content": "%s looks fine." % human_name}}],
		"model": "gpt-4o-mini", "usage": {"total_tokens": 20}}
	clean = orchestration.ask(module_key, "How is it?", record_name)
	report(clean["ai_status"] == "available",
		"GUARDRAIL/%s: a clean answer referencing only supplied facts passes" % module_key)

	# fabricated record id -> blocked
	State.post_request_response = {"choices": [{"message": {"content": "Also see record zx9q4m1p07 for context."}}],
		"model": "gpt-4o-mini", "usage": {"total_tokens": 20}}
	fabricated = orchestration.ask(module_key, "How is it?", record_name)
	report(fabricated["ai_status"] == "guardrail_blocked",
		"GUARDRAIL/%s: a FABRICATED record reference is rejected" % module_key)
	report(fabricated["answer"] is None,
		"GUARDRAIL/%s: a blocked answer is never returned -- facts only" % module_key)
	report("zx9q4m1p07" in (fabricated["answer_error"] or ""),
		"GUARDRAIL/%s: the rejection names the fabricated identifier" % module_key)

	# the human name itself must NOT be treated as fabricated
	report(human_name in clean["known_record_names"],
		"GUARDRAIL/%s: the human-readable name is an accepted identifier, not just the record id" % module_key)


# ============================================================
# api.ask_ucc() across all three modules, plus module validation
# ============================================================
for module_key, record_name, _ in GUARDRAIL_CASES:
	State.post_request_response = {"choices": [{"message": {"content": "All good."}}],
		"model": "gpt-4o-mini", "usage": {"total_tokens": 10}}
	State.conversations = []
	State.messages = []
	State.usage_logs = []
	response = api.ask_ucc(module_key, "How is it?", record_name)
	report(response["ok"] is True and response["module"] == module_key,
		"api.ask_ucc(%s) returns ok and echoes the module" % module_key)
	report(response["sources"] and response["sources"][0]["record"] == record_name,
		"api.ask_ucc(%s) cites the real resolved record" % module_key)
	report(len(State.conversations) == 1 and len(State.usage_logs) == 1,
		"api.ask_ucc(%s) persists a conversation and a usage log" % module_key)

try:
	api.ask_ucc("not_a_module", "A question", "SOME-RECORD")
	report(False, "an unknown module should be rejected")
except Exception:
	report(True, "an unknown module key is rejected, never used to reach code by name")

# get_ask_ucc_modules is gated by dashboard access, not hardcoded
modules_response = api.get_ask_ucc_modules()
report(modules_response["ok"] is True, "get_ask_ucc_modules returns ok")
report(isinstance(modules_response["modules"], list), "get_ask_ucc_modules returns a module list")



# ============================================================
# GUIDED QUESTIONS -- must match the legacy maps EXACTLY, not be invented
# ============================================================
import ucc_intelligence.ask_ucc.guided_questions as guided  # noqa: E402
import re as _re

legacy_js = (ROOT / "custom-html-block" / "JAVASCRIPT.js").read_text(encoding="utf-8")


def legacy_pairs(map_name):
	"""Re-extract a question map straight from the legacy source, so this
	proves the port matches the real thing rather than matching itself."""
	start = legacy_js.index("const %s = {" % map_name)
	end = legacy_js.index("\n};", start)
	block_src = legacy_js[start:end]
	# each entry is ["label", "question"] possibly with escaped apostrophes
	return [
		(a.replace("\\'", "'"), b.replace("\\'", "'"))
		for a, b in _re.findall(r'\["([^"]*)",\s*"((?:[^"\\]|\\.)*)"\]', block_src)
	]


for map_name, module_key in [
	("studentQuestionMap", "student_journey"),
	("recruitmentQuestionMap", "recruitment_agent"),
	("qualityActionQuestionMap", "quality_action"),
]:
	legacy = legacy_pairs(map_name)
	report(len(legacy) > 10, "legacy %s re-extracted from JAVASCRIPT.js (%d questions)" % (map_name, len(legacy)))
	ported_map = guided.MODULE_QUESTIONS[module_key][0]
	ported = [(item[0], item[1]) for questions in ported_map.values() for item in questions]
	report(sorted(ported) == sorted(legacy),
		"GUIDED/%s: ported question map matches the legacy source EXACTLY (labels and question text)" % module_key)

# category labels match the legacy renderCategoryOptions sets
for module_key, expected_first in [
	("student_journey", "Profile"),
	("recruitment_agent", "Profile and Contract"),
	("quality_action", "Overview"),
]:
	categories = guided.MODULE_QUESTIONS[module_key][1]
	report(categories[0][1] == expected_first,
		"GUIDED/%s: category labels are the module's own legacy set, not the student one" % module_key)
	report([c[0] for c in categories] == ["profile", "journey", "academic", "attendance", "finance", "graduation", "cohort"],
		"GUIDED/%s: the seven legacy category keys are all present" % module_key)

# the filtering is real and honest
for module_key in ("student_journey", "recruitment_agent", "quality_action"):
	supported = guided.supported_questions(module_key)
	keys = [c["key"] for c in supported]
	report("cohort" not in keys,
		"GUIDED/%s: the cohort category is held back (every question in it is cross-record, which is deferred)" % module_key)
	report(len(supported) > 0, "GUIDED/%s: at least one category survives filtering" % module_key)
	shown = {q["question"] for c in supported for q in c["questions"]}
	unsupported = guided.UNSUPPORTED_QUESTIONS.get(module_key, set())
	report(not (shown & unsupported),
		"GUIDED/%s: no question whose backing tool was deferred is offered" % module_key)
	report(all(c["questions"] for c in supported),
		"GUIDED/%s: no empty category is rendered" % module_key)

student_supported = {q["question"] for c in guided.supported_questions("student_journey") for q in c["questions"]}
report("Show this student's profile" in student_supported, "GUIDED: a real, answerable question IS offered")
report("Show this student's invoices" not in student_supported,
	"GUIDED: the finance question backed by the dropped invoice name-match is NOT offered")


# ============================================================
# RECORD SEARCH -- must return real matching records, by human name
# ============================================================
State.list_rows["Student Applicant"] = [
	{"name": "EDU-APP-2025-00001", "first_name": "Mei", "middle_name": "", "last_name": "Lim"},
	{"name": "EDU-APP-2025-00002", "first_name": "Ravi", "middle_name": "", "last_name": "Kumar"},
]


def _search_get_list(doctype, fields=None, or_filters=None, order_by=None, limit_page_length=None):
	if doctype in State.denied_doctypes:
		raise frappe_stub.PermissionError("not permitted to read " + doctype)
	rows = [dict(r) for r in State.list_rows.get(doctype, [])]
	if not or_filters:
		return rows
	out = []
	for row in rows:
		for fieldname, _op, pattern in or_filters:
			needle = pattern.strip("%").lower()
			if needle and needle in str(row.get(fieldname, "")).lower():
				out.append(row)
				break
	return out


_prev_get_list = frappe_stub.get_list
frappe_stub.get_list = _search_get_list


class _SearchMeta:
	def __init__(self, doctype):
		self.doctype = doctype

	def has_field(self, fieldname):
		rows = State.list_rows.get(self.doctype) or [{}]
		return fieldname in rows[0]


_prev_get_meta = frappe_stub.get_meta
frappe_stub.get_meta = lambda dt: _SearchMeta(dt)

result = api.search_ask_ucc_records("student_journey", "Mei")
report(result["ok"] is True, "SEARCH: returns ok")
report(len(result["records"]) == 1, "SEARCH: typing a HUMAN NAME ('Mei') returns exactly the matching record")
report(result["records"][0]["id"] == "EDU-APP-2025-00001", "SEARCH: the returned record is the right one")
report(result["records"][0]["label"] == "Mei Lim", "SEARCH: the label is the composed human name, not the opaque id")

by_id = api.search_ask_ucc_records("student_journey", "EDU-APP-2025-00002")
report(len(by_id["records"]) == 1 and by_id["records"][0]["id"] == "EDU-APP-2025-00002",
	"SEARCH: searching by record id still works (both paths, like the legacy version)")

report(api.search_ask_ucc_records("student_journey", "")["records"] == [],
	"SEARCH: an empty term returns nothing rather than dumping every record")
report(api.search_ask_ucc_records("student_journey", "zzzznomatch")["records"] == [],
	"SEARCH: a non-matching term returns no records")

State.denied_doctypes.add("Student Applicant")
denied = api.search_ask_ucc_records("student_journey", "Mei")
report(denied["records"] == [] and denied.get("status") == "permission_denied",
	"SEARCH: a permission-denied DocType reports permission_denied, never leaks rows")
State.denied_doctypes.clear()

try:
	api.search_ask_ucc_records("not_a_module", "x")
	report(False, "SEARCH: an unknown module should be rejected")
except Exception:
	report(True, "SEARCH: an unknown module is rejected -- fields can never be caller-supplied")

for module_key, expected in [
	("student_journey", "first_name"),
	("recruitment_agent", "party_name"),
	("quality_action", "custom_subject"),
]:
	fields = orchestration.MODULES[module_key]["search_fields"]
	report(expected in fields,
		"SEARCH/%s: searches its own legacy human-name field (%s), not just `name`" % (module_key, expected))

frappe_stub.get_list = _prev_get_list
frappe_stub.get_meta = _prev_get_meta

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
