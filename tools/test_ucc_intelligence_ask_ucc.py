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
	resolution_field_meta = "resolutions"  # which field find_resolution_field() should discover
	settings = None
	conf = {}
	conversations = []  # list of FakeDoc (UCC AI Conversation)
	messages = []
	usage_logs = []
	post_request_response = None
	post_request_error = None


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


def _get_doc(doctype, name):
	if doctype == "Quality Action":
		if name not in State.quality_actions:
			raise frappe_stub.DoesNotExistError("no such Quality Action")
		return State.quality_actions[name]
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
result = orchestration.ask_quality_action("Is this ready to close?", "QA-0001")
report(result["ai_status"] == "disabled", "orchestration reports disabled and still returns facts when AI is off")
report(result["answer"] is None and result["facts"]["summary"]["status"] == "available", "facts are populated even though there's no AI answer (progressive enhancement)")
report(result["tools_called"] == ["get_quality_action_summary", "assess_quality_action_closure"], "both tools are called for a resolvable record")

result = orchestration.ask_quality_action("What about it?", "QA-does-not-exist")
report(result["ai_status"] == "not_found", "orchestration surfaces the tool's not_found status directly, only 1 tool attempted")
report(result["tools_called"] == ["get_quality_action_summary"], "closure assessment is not attempted when the record itself doesn't resolve")

State.settings = FakeDoc({"enable_ai": 1, "ai_provider": "OpenAI", "ai_model": "gpt-4o-mini", "max_output_tokens": 500, "default_temperature": 0.2, "ai_request_timeout_seconds": 30})
State.post_request_response = {"choices": [{"message": {"content": "1 of 2 resolution rows is ready for closure."}}], "model": "gpt-4o-mini", "usage": {"total_tokens": 55}}
result = orchestration.ask_quality_action("Is this ready to close?", "QA-0001")
report(result["ai_status"] == "available" and result["answer"]["text"].startswith("1 of 2"), "a clean AI answer passes through end to end")

# the guardrail actually fires inside orchestration too, not just in isolation
State.post_request_response = {"choices": [{"message": {"content": "Also check qa9f3k2z01 for a similar issue."}}], "model": "gpt-4o-mini", "usage": {"total_tokens": 12}}
result = orchestration.ask_quality_action("Is this ready to close?", "QA-0001")
report(result["ai_status"] == "guardrail_blocked", "orchestration blocks an AI answer that references an unverified record, end to end")
report(result["answer"] is None, "a guardrail-blocked response never sets answer -- facts-only is what gets returned")


# ============================================================
# ask_ucc/conversations.py -- persistence
# ============================================================
State.conversations = []
State.messages = []
State.usage_logs = []
State.post_request_response = {"choices": [{"message": {"content": "1 of 2 resolution rows is ready."}}], "model": "gpt-4o-mini", "usage": {"total_tokens": 30}}
result = orchestration.ask_quality_action("Is this ready to close?", "QA-0001")
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
response = contracts.build_response(conversation, result)
for key in ("ok", "conversation_id", "ai_status", "answer", "facts", "sources", "warnings"):
	report(key in response, "response contract includes %r" % key)
report(response["sources"][0] == {"doctype": "Quality Action", "record": "QA-0001", "status": "available"}, "sources correctly cites the real resolved Quality Action")

import ucc_intelligence.api as api  # noqa: E402

State.conversations = []
State.messages = []
State.usage_logs = []
State.post_request_response = {"choices": [{"message": {"content": "1 of 2 resolution rows is ready for closure."}}], "model": "gpt-4o-mini", "usage": {"total_tokens": 44}}
full_response = api.ask_quality_action("Is this ready to close?", "QA-0001")
report(full_response["ok"] is True, "api.ask_quality_action() returns ok=True end to end")
report(full_response["ai_status"] == "available", "api.ask_quality_action() end-to-end AI path works with everything stubbed")
report(len(State.conversations) == 1 and len(State.messages) == 2 and len(State.usage_logs) == 1,
	"api.ask_quality_action() persists exactly 1 conversation, 2 messages (user+assistant), 1 usage log")

try:
	api.ask_quality_action("", "QA-0001")
	report(False, "an empty question should raise, not silently proceed")
except Exception:
	report(True, "an empty question raises rather than silently proceeding")

try:
	api.ask_quality_action("A question", "")
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
blocked_response = api.ask_quality_action("What is this?", "QA-blocked")
report(blocked_response["sources"][0]["status"] == "permission_denied", "a permission-denied source reports permission_denied through the full stack, not a silent bypass or a crash")
frappe_stub.get_doc = _get_doc


passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
