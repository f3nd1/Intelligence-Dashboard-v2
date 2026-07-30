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
for cut_field in ("enable_persistent_conversations", "conversation_retention_days", "default_action_approval_level"):
	report(cut_field not in fieldnames, "%r is genuinely absent (cut per Felix's decision), not just unused" % cut_field)
for kept_field in ("enable_ai", "ai_provider", "ai_model", "max_output_tokens", "default_temperature", "ai_request_timeout_seconds", "enable_document_knowledge", "enable_monitoring"):
	report(kept_field in fieldnames, "%r is present" % kept_field)
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


class FakeSettingsDoc(settings_doctype.UCCIntelligenceSettings):
	def __init__(self, temperature):
		self.default_temperature = temperature


for given, expected in [(-5.0, 0.0), (0.2, 0.2), (2.0, 2.0), (9.0, 2.0), (None, None)]:
	doc = FakeSettingsDoc(given)
	doc.validate()
	report(doc.default_temperature == expected, "default_temperature %r clamps to %r" % (given, expected))

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
