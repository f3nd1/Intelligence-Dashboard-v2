#!/usr/bin/env python3
"""Self-check for the UCC Intelligence Settings page
(docs/architecture/settings-page-plan.md).

Covers: settings/status.py's individual checks against a stubbed frappe,
the default_temperature clamp in the DocType controller, the DocType JSON
shape (confirming the memory toggle and controlled-actions field are
genuinely absent, not just unused -- per Felix's decisions to cut them),
and that get_settings_status() gates on System Manager before returning
anything.

    python3 tools/test_ucc_intelligence_settings.py
"""
import json
import re
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


class State:
	insights_query_names = {}  # title -> name, only for titles that "exist"
	insights_settings = {}
	dashboard_access_rows = []
	site_config = {}
	meta_available = set()


def _get_value(doctype, filters, fieldname):
	if doctype == "Insights Query v3":
		return State.insights_query_names.get(filters.get("title"))
	return None


def _get_singles_dict(doctype):
	if doctype == "Insights Settings":
		return dict(State.insights_settings)
	return {}


def _get_all(doctype, filters=None, fields=None, limit_page_length=None, ignore_permissions=False):
	if doctype == "UCC Dashboard Access":
		return [dict(r) for r in State.dashboard_access_rows]
	return []


def _get_meta(doctype):
	if doctype not in State.meta_available:
		raise RuntimeError("DocType %s not found" % doctype)
	return object()


class FakeConf(dict):
	pass


class FakeUtils:
	now = staticmethod(lambda: "2026-07-30 00:00:00")


frappe_stub = types.ModuleType("frappe")
frappe_stub.get_value = None
frappe_stub.db = types.SimpleNamespace(get_value=_get_value, get_singles_dict=_get_singles_dict)
frappe_stub.get_all = _get_all
frappe_stub.get_meta = _get_meta
frappe_stub.conf = FakeConf()
frappe_stub.utils = FakeUtils()
frappe_stub.whitelist = lambda *a, **k: (lambda f: f)
frappe_stub.only_for = lambda *a, **k: None
frappe_stub.logger = lambda *a, **k: types.SimpleNamespace(
	info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None,
)


class FrappeThrow(Exception):
	pass


def _throw(message, title=None, **kwargs):
	raise FrappeThrow(message)


frappe_stub.throw = _throw
frappe_stub._ = lambda text, *a, **k: text
sys.modules["frappe"] = frappe_stub

frappe_model_stub = types.ModuleType("frappe.model")
frappe_model_document_stub = types.ModuleType("frappe.model.document")


class _FakeDocument:
	pass


frappe_model_document_stub.Document = _FakeDocument
sys.modules["frappe.model"] = frappe_model_stub
sys.modules["frappe.model.document"] = frappe_model_document_stub

import ucc_intelligence.settings.status as status  # noqa: E402 -- stub must load first

# ============================================================
# get_dashboard_access_summary
# ============================================================
State.dashboard_access_rows = [
	{"role": "Admissions Officer"},
	{"role": "Quality Lead"},
	{"role": "Admissions Officer"},  # duplicate role name -- should not double-count
]
summary = status.get_dashboard_access_summary()
report(summary["configured_role_count"] == 2, "dashboard access summary de-duplicates role names (2 unique from 3 rows)")
report(summary["roles"] == ["Admissions Officer", "Quality Lead"], "dashboard access summary preserves first-seen role order")

# ============================================================
# get_insights_chart_status
# ============================================================
from ucc_intelligence.analytics.admission_intelligence_embed import CHART_TITLES  # noqa: E402

State.insights_query_names = {
	CHART_TITLES["applicants_by_year"]: "q-1",
	CHART_TITLES["enrolled_by_year"]: "q-2",
}
chart_status = status.get_insights_chart_status()
report(chart_status["built_count"] == 2, "insights chart status counts exactly the 2 built charts")
report(chart_status["total_count"] == len(CHART_TITLES), "insights chart status total matches CHART_TITLES' full set (%d)" % len(CHART_TITLES))
built_keys = {c["data_key"] for c in chart_status["charts"] if c["built"]}
report(built_keys == {"applicants_by_year", "enrolled_by_year"}, "insights chart status correctly flags which specific charts are built")

# ============================================================
# get_insights_permission_setting
# ============================================================
State.insights_settings = {"apply_user_permissions": 1}
report(status.get_insights_permission_setting()["apply_user_permissions"] is True, "apply_user_permissions=1 reports True")
State.insights_settings = {"apply_user_permissions": 0}
report(status.get_insights_permission_setting()["apply_user_permissions"] is False, "apply_user_permissions=0 reports False, not silently truthy")

# ============================================================
# get_ai_provider_configured -- presence only, via site_config
# ============================================================
State.site_config = {}
frappe_stub.conf = FakeConf()
report(status.get_ai_provider_configured()["configured"] is False, "no site_config key set -> configured=False")
frappe_stub.conf = FakeConf({status.AI_API_KEY_SITE_CONFIG_KEY: "some-secret-value"})
report(status.get_ai_provider_configured()["configured"] is True, "site_config key present -> configured=True")
report("site_config_key" in status.get_ai_provider_configured(), "response names the site_config key, never the value")
report(
	str(status.get_ai_provider_configured().get("configured_value", "")) == "",
	"response never echoes the actual secret value back",
)

# ============================================================
# get_db_reachable
# ============================================================
State.meta_available = {"Student Applicant"}
report(status.get_db_reachable() is True, "db_reachable True when Student Applicant meta resolves")
State.meta_available = set()
report(status.get_db_reachable() is False, "db_reachable False when meta lookup fails, not an uncaught exception")

# ============================================================
# get_status_summary -- shape check
# ============================================================
State.meta_available = {"Student Applicant"}
full = status.get_status_summary()
for key in ("ok", "generated_at", "dashboard_access", "insights_charts", "insights_permission_setting", "ai_provider_configured", "db_reachable"):
	report(key in full, "get_status_summary() includes %r" % key)
report("ai_fields_filled" not in full, "AI provider/model 'fields filled' check is NOT in the server response -- computed client-side from frm.doc instead")

# ============================================================
# DocType JSON shape -- confirm the cut fields are genuinely absent
# ============================================================
doctype_json = json.loads((ROOT / "ucc_intelligence/ucc_intelligence/sophia/doctype/ucc_intelligence_settings/ucc_intelligence_settings.json").read_text())
fieldnames = {f["fieldname"] for f in doctype_json["fields"]}
report(doctype_json.get("issingle") == 1, "UCC Intelligence Settings is a Single DocType")
report(doctype_json.get("module") == "Sophia", "DocType is registered under the Sophia module, matching UCC Dashboard Access")
# conversation_retention_days and default_action_approval_level stay cut: the
# first because retention is a single fixed 30 days (no second rule to choose
# between), the second because no controlled-actions feature exists to gate.
# enable_persistent_conversations was cut in the first round for exactly that
# reason too -- but UCC AI Conversation/Message now exist, so it graduated to
# a real toggle (asserted below, not here).
for cut_field in ("conversation_retention_days", "default_action_approval_level"):
	report(cut_field not in fieldnames, "%r is genuinely absent (cut per Felix's decision), not just unused" % cut_field)
for kept_field in ("enable_ai", "ai_provider", "ai_model", "max_output_tokens", "default_temperature", "ai_request_timeout_seconds", "enable_document_knowledge", "enable_monitoring", "enable_persistent_conversations"):
	report(kept_field in fieldnames, "%r is present" % kept_field)

# The memory toggle is REAL, not a placeholder -- it must default on (matching
# prior behaviour, where conversations were always stored) and its description
# must not call itself a placeholder the way the two genuine placeholders do.
memory_field = next(f for f in doctype_json["fields"] if f["fieldname"] == "enable_persistent_conversations")
report(memory_field.get("default") == "1", "enable_persistent_conversations defaults ON, preserving existing behaviour")
report("Placeholder" not in memory_field.get("description", ""), "the memory toggle is not described as a placeholder -- it is genuinely wired up")
for placeholder_fieldname in ("enable_document_knowledge", "enable_monitoring"):
	placeholder_field = next(f for f in doctype_json["fields"] if f["fieldname"] == placeholder_fieldname)
	report("Placeholder" in placeholder_field.get("description", ""),
		"%r is still honestly labelled a placeholder" % placeholder_fieldname)
report(
	"api_key" not in " ".join(fieldnames).lower() and "secret" not in " ".join(fieldnames).lower(),
	"no field name suggests a stored secret -- the API key deliberately has no field this round",
)
perm = doctype_json["permissions"][0]
report(perm["role"] == "System Manager" and perm["read"] == 1 and perm["write"] == 1,
	"System Manager has read/write, matching UCC Dashboard Access's own permission model")

# ============================================================
# default_temperature clamp (DocType controller)
# ============================================================
import ucc_intelligence.sophia.doctype.ucc_intelligence_settings.ucc_intelligence_settings as settings_doctype  # noqa: E402


class FakeField:
	def __init__(self, fieldname, fieldtype, label=None):
		self.fieldname = fieldname
		self.fieldtype = fieldtype
		self.label = label or fieldname


class FakeMeta:
	"""Mirrors the real DocType's own field list, read from the JSON rather
	than hand-listed, so a field added there is covered here automatically."""
	fields = [FakeField(f["fieldname"], f["fieldtype"], f.get("label")) for f in doctype_json["fields"]]


class FakeSettingsDoc(settings_doctype.UCCIntelligenceSettings):
	def __init__(self, **values):
		self.meta = FakeMeta()
		self.__dict__.setdefault("default_temperature", None)
		self.__dict__.update(values)

	def get(self, fieldname):
		return getattr(self, fieldname, None)


for given, expected in [(-5.0, 0.0), (0.2, 0.2), (2.0, 2.0), (9.0, 2.0), (None, None)]:
	doc = FakeSettingsDoc(default_temperature=given)
	doc.validate()
	report(doc.default_temperature == expected, "default_temperature %r clamps to %r" % (given, expected))


# ============================================================
# SECURITY: no field on this DocType may hold an API key.
#
# The AI Provider field was a plain Data field and a real key was pasted
# into it, in cleartext, on a saved and viewable form. Making that one
# field a Select fixes that one field. These check the DocType as a whole
# refuses a key, so a field added later inherits the protection.
# ============================================================
provider_field = next(f for f in doctype_json["fields"] if f["fieldname"] == "ai_provider")
report(provider_field["fieldtype"] == "Select",
	"SECURITY: AI Provider is a Select -- free text is what let a key be pasted in")
report([o for o in provider_field["options"].split("\n") if o] == ["OpenAI"],
	"SECURITY: OpenAI is the ONLY option -- no provider is invented while CLAUDE.md §19 approval is open")
report("NEVER a key" in provider_field["description"] and "site_config" in provider_field["description"],
	"SECURITY: the field says on the form itself where the key actually belongs")
report(next(f for f in doctype_json["fields"] if f["fieldname"] == "ai_model")["fieldtype"] == "Select",
	"SECURITY: AI Model is a Select too -- it was the other free-text box on the AI row")
for field in doctype_json["fields"]:
	report(field["fieldtype"] != "Password",
		"SECURITY: %r is not a Password field -- a stored secret is still a stored secret" % field["fieldname"])

# Shapes that must be REFUSED, on every text-ish field, not just ai_provider.
KEY_SHAPES = [
	"sk-proj-" + "A" * 40,          # the shape actually pasted
	"sk-" + "B" * 48,               # classic OpenAI
	"sk-ant-api03-" + "C" * 40,     # Anthropic, in case a provider is added
	"Bearer sk-" + "D" * 40,        # pasted with the header prefix
	"  sk-" + "E" * 32 + "  ",      # pasted with whitespace
]
TEXT_FIELDS = [f["fieldname"] for f in doctype_json["fields"]
	if f["fieldtype"] in ("Data", "Select", "Small Text", "Text", "Long Text", "Code", "Password")]
report(len(TEXT_FIELDS) >= 2, "SECURITY: there are text fields to protect (%s)" % TEXT_FIELDS)

for fieldname in TEXT_FIELDS:
	for shape in KEY_SHAPES:
		doc = FakeSettingsDoc(**{fieldname: shape})
		try:
			doc.validate()
			report(False, "SECURITY: %s accepted an API-key-shaped value -- it MUST be rejected" % fieldname)
		except FrappeThrow as error:
			# The refusal must not echo the secret into the error, the error
			# log, or the user's screen.
			report(shape.strip() not in str(error),
				"SECURITY: %s rejects a key and does NOT echo the value back" % fieldname)

# ...and must not become unusable for legitimate values.
for fieldname, legitimate in [("ai_provider", "OpenAI"), ("ai_model", "gpt-4o-mini"), ("ai_model", "o3-mini")]:
	doc = FakeSettingsDoc(**{fieldname: legitimate})
	try:
		doc.validate()
		report(True, "SECURITY: %s still accepts the legitimate value %r" % (fieldname, legitimate))
	except FrappeThrow:
		report(False, "SECURITY: %s wrongly rejected the legitimate value %r" % (fieldname, legitimate))

# The key must be read from site_config and NOWHERE else.
client_source = (ROOT / "ucc_intelligence" / "ucc_intelligence" / "ai" / "client.py").read_text(encoding="utf-8")
report(client_source.count("frappe.conf.get(AI_API_KEY_SITE_CONFIG_KEY)") >= 1,
	"SECURITY: client.py reads the key from frappe.conf (site_config.json)")
report("settings.api_key" not in client_source and "settings.ai_api_key" not in client_source
	and "settings.ai_key" not in client_source,
	"SECURITY: client.py never reads a key off the Settings DocType")
for read_site_config in ("def complete(", "def list_models("):
	body_start = client_source.index(read_site_config)
	body = client_source[body_start:body_start + 2500]
	report("frappe.conf.get(AI_API_KEY_SITE_CONFIG_KEY)" in body,
		"SECURITY: %s reads the key FRESH from site_config on every call -- a rotated key takes effect immediately"
		% read_site_config.strip("def ("))
# Module-level = evaluated once at import; the key would then survive a
# rotation until the workers restart. Every read must be inside a function.
report(re.search(r"^\w+\s*=\s*frappe\.conf\.get", client_source, re.M) is None,
	"SECURITY: the key is not captured into a module-level variable at import time")
report("AI_API_KEY_SITE_CONFIG_KEY = \"ucc_intelligence_ai_api_key\"" in client_source,
	"SECURITY: the site_config key NAME is the documented convention, unchanged")

# ============================================================
# get_settings_status gates on System Manager before returning data
# ============================================================
import ucc_intelligence.api as api  # noqa: E402

gate_calls = []
frappe_stub.only_for = lambda role: gate_calls.append(role)
result = api.get_settings_status()
report(gate_calls == ["System Manager"], "get_settings_status() calls frappe.only_for('System Manager') before returning data")
report(result.get("ok") is True, "get_settings_status() returns the real status summary after the gate")

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
