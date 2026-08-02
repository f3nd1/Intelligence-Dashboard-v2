#!/usr/bin/env python3
"""Self-check for operations/service.py -- monitoring and knowledge, made visible.

    python3 tools/test_operations.py

WHAT THIS PROVES
Both engines already worked; what did not exist was any way to see or act on
them. So the checks here are about the SEEING and the ACTING, and mostly about
what must not happen:

  - a finding for a record you cannot read is never listed
  - seeing a finding and being allowed to close it are different permissions
  - suppressing without a reason is refused, because a suppressed finding never
    returns on a later run and an unexplained permanent silence is not auditable
  - an empty knowledge index says it is empty rather than implying documents

The fake's get_list applies permissions and get_all does not exist for the
finding path, so any drift towards a permission-blind read fails here.
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


def raises(exception, call, *args, **kwargs):
	try:
		call(*args, **kwargs)
	except exception:
		return True
	except Exception:
		return False
	return False


class PermissionError_(Exception):
	pass


class ValidationError_(Exception):
	pass


class State:
	findings = []
	readable_findings = set()   # names this user's DocType permissions allow
	may_write_findings = True
	sources = []
	chunks = {}
	may_write_sources = True
	knowledge_enabled = True
	monitoring_enabled = True
	rule_records = []
	runs = []
	saved = []
	indexed = []
	registered = []


class FakeDoc:
	def __init__(self, data):
		self.data = dict(data)
		self.name = data.get("name")
		self.meta = types.SimpleNamespace(
			has_field=lambda field: field in ("suppression_reason", "resolved_at"))

	def get(self, key):
		return self.data.get(key)

	def __setattr__(self, key, value):
		if key in ("data", "name", "meta"):
			object.__setattr__(self, key, value)
		else:
			self.data[key] = value

	def save(self):
		if not State.may_write_findings:
			raise PermissionError_("No write permission")
		State.saved.append(dict(self.data))


def fake_get_list(doctype, filters=None, fields=None, order_by=None, limit_page_length=None):
	if doctype == "UCC Monitoring Finding":
		rows = [row for row in State.findings if row["name"] in State.readable_findings]
	elif doctype == "UCC Knowledge Source":
		rows = list(State.sources)
	elif doctype == "UCC Knowledge Chunk":
		source = (filters or {}).get("source")
		rows = [{"name": n} for n in State.chunks.get(source, [])]
	elif doctype == "UCC Monitoring Run":
		rows = list(State.runs)
	else:
		rows = []
	for key, value in (filters or {}).items():
		if key == "source":
			continue
		rows = [row for row in rows if row.get(key) == value]
	return rows[: (limit_page_length or 100)] if limit_page_length else rows


def install():
	frappe = types.ModuleType("frappe")
	frappe._ = lambda text: text
	frappe.PermissionError = PermissionError_
	frappe.ValidationError = ValidationError_

	def throw(message, exc=None):
		raise (exc or ValidationError_)(message)

	frappe.throw = throw
	frappe.get_list = fake_get_list
	# get_all EXISTS but must never be used for findings -- it applies no
	# permissions. It serves the rule CONFIGURATION table only, which holds no
	# institutional data.
	def fake_get_all(doctype, filters=None, **kwargs):
		if doctype == "UCC Monitoring Rule":
			return list(State.rule_records)
		if doctype == "UCC Monitoring Run":
			rows = list(State.runs)
			for key, value in (filters or {}).items():
				rows = [row for row in rows if row.get(key) == value]
			return rows
		return []

	frappe.get_all = fake_get_all
	frappe.get_doc = lambda doctype, name: FakeDoc(
		next(row for row in State.findings if row["name"] == name))
	frappe.get_single = lambda doctype: types.SimpleNamespace(
		enable_document_knowledge=State.knowledge_enabled)
	frappe.has_permission = lambda doctype, ptype=None: (
		State.may_write_findings if doctype == "UCC Monitoring Finding"
		else State.may_write_sources)
	frappe.utils = types.SimpleNamespace(
		cstr=lambda v: "" if v is None else str(v),
		now=lambda: "2026-08-03 04:00:00")
	frappe.get_traceback = lambda: ""
	frappe.session = types.SimpleNamespace(user="tester@ucc")
	frappe.logger = lambda *a, **k: types.SimpleNamespace(
		info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None)
	frappe.log_error = lambda **kwargs: None
	sys.modules["frappe"] = frappe

	engine = types.ModuleType("ucc_intelligence.monitoring.engine")
	engine.monitoring_enabled = lambda: State.monitoring_enabled
	sys.modules["ucc_intelligence.monitoring.engine"] = engine

	registry = types.ModuleType("ucc_intelligence.monitoring.rule_registry")
	registry.RULES = {
		"student_log_background_required": {
			"title": "Student Log closed without student background",
			"purpose": "CLAUDE.md 11 use case 1.",
			"target_doctype": "Student Log", "severity": "High",
			"remediation": "Fill in the background.", "version": "1.0"},
		"quality_action_closure_evidence": {
			"title": "Quality Action closed without evidence",
			"purpose": "CLAUDE.md 11 use case 4.",
			"target_doctype": "Quality Action", "severity": "Medium",
			"remediation": "Attach the closure evidence.", "version": "1.0"},
	}
	sys.modules["ucc_intelligence.monitoring.rule_registry"] = registry

	ingestion = types.ModuleType("ucc_intelligence.knowledge.ingestion")

	def register_source(title, source_type, text=None, attached_file=None, **fields):
		"""Mirrors the real one: it registers AND indexes, and returns a dict.

		Modelling it as returning a name was what hid the double-index bug."""
		name = "SRC-%02d" % (len(State.registered) + 1)
		State.registered.append({"name": name, "title": title, "source_type": source_type})
		State.sources.append({"name": name, "title": title, "source_type": source_type,
			"sync_status": "Not Indexed", "last_indexed_at": None, "is_active": 1,
			"document_version": "1", "classification": "Internal", "superseded_by": None,
			"chunk_count": 0, "permission_role": None, "attached_file": None,
			"content_checksum": "",
			"owner_department": "", "effective_date": None, "review_date": None})
		result = index_source(name, text=text)
		return dict(result, source=name)

	def index_source(source_name, text=None):
		if not (text or "").strip():
			return {"ok": False, "indexed": False,
				"message": "The document is empty; nothing to index."}
		State.indexed.append(source_name)
		for row in State.sources:
			if row["name"] == source_name:
				row["last_indexed_at"] = "2026-08-03 02:00:00"
				row["sync_status"] = "Indexed"
				row["chunk_count"] = 2
		State.chunks[source_name] = ["c1", "c2"]
		return {"ok": True, "indexed": True, "sections": 2}

	ingestion.register_source = register_source
	ingestion.index_source = index_source
	ingestion.reindex_stale = lambda: [row["name"] for row in State.sources
		if row.get("sync_status") == "Stale"]
	sys.modules["ucc_intelligence.knowledge.ingestion"] = ingestion


install()
from ucc_intelligence.operations import service  # noqa: E402


def reset():
	State.findings = [
		{"name": "F-1", "rule": "student_log_background_required", "status": "Open",
			"severity": "High", "target_doctype": "Student Log", "target_record": "LOG-001",
			"detail": "Background is empty.", "occurrence_count": 3,
			"responsible_role": "Student Services", "first_seen_run": "RUN-1",
			"last_seen_run": "RUN-2", "modified": "2026-08-02 03:00:00"},
		{"name": "F-2", "rule": "quality_action_closure_evidence", "status": "Open",
			"severity": "Medium", "target_doctype": "Quality Action", "target_record": "QA-9",
			"detail": "No evidence attached.", "occurrence_count": 1,
			"responsible_role": "Quality", "first_seen_run": "RUN-1",
			"last_seen_run": "RUN-2", "modified": "2026-08-02 03:00:00"},
		{"name": "F-3", "rule": "student_log_background_required", "status": "Resolved",
			"severity": "High", "target_doctype": "Student Log", "target_record": "LOG-007",
			"detail": "Was empty.", "occurrence_count": 2,
			"responsible_role": "Student Services", "first_seen_run": "RUN-0",
			"last_seen_run": "RUN-1", "modified": "2026-07-20 03:00:00"},
	]
	State.readable_findings = {"F-1", "F-2", "F-3"}
	State.may_write_findings = True
	State.may_write_sources = True
	State.knowledge_enabled = True
	State.monitoring_enabled = True
	State.sources = []
	State.chunks = {}
	State.rule_records = [{"name": "R-1", "rule_id": "student_log_background_required",
		"enabled": 1, "severity": "High", "rule_version": "1.0"}]
	State.runs = [{"name": "RUN-2", "rule": "student_log_background_required",
		"status": "Completed", "started_at": "2026-08-02 03:00:00",
		"finished_at": "2026-08-02 03:01:00", "records_evaluated": 41,
		"findings_opened": 2, "findings_reopened": 0, "findings_resolved": 1,
		"error_message": ""}]
	State.saved = []
	State.indexed = []
	State.registered = []


# --- MONITORING: what you can see ------------------------------------------
reset()
overview = service.monitoring_overview()
report(overview["open_total"] == 2, "open findings are counted, resolved ones are not")
report(overview["open_by_severity"] == {"High": 1, "Medium": 1, "Low": 0},
	"and broken down by severity: %s" % overview["open_by_severity"])
report(len(overview["rules"]) == 2, "every registered rule is listed, configured or not")

configured = {rule["rule_id"]: rule for rule in overview["rules"]}
report(configured["student_log_background_required"]["configured"] is True
	and configured["student_log_background_required"]["enabled"] is True,
	"a rule with a record reports its real enabled state")
report(configured["quality_action_closure_evidence"]["configured"] is False,
	"a rule with NO record is 'not configured', not 'disabled' -- that would invent an intent")
report(configured["quality_action_closure_evidence"]["target_doctype"] == "Quality Action"
	and configured["quality_action_closure_evidence"]["remediation"],
	"...and still describes itself from the registry, which is version-controlled")
report(configured["student_log_background_required"]["open_findings"] == 1,
	"each rule carries its own open count")

# The permission that matters: a finding names a real record.
reset()
State.readable_findings = {"F-2"}
visible = service.findings("Open")
report([row["name"] for row in visible["findings"]] == ["F-2"],
	"a finding whose record this user cannot read is never listed")
report(service.monitoring_overview()["open_total"] == 1,
	"...and the headline count reflects what THIS user may see, not the institution's total")

reset()
report([row["name"] for row in service.findings("Resolved")["findings"]] == ["F-3"],
	"the status filter works")
report(len(service.findings("All")["findings"]) == 3, "'All' shows every status")
report([row["name"] for row in service.findings("Open", severity="High")["findings"]] == ["F-1"],
	"the severity filter works")
report(service.findings("nonsense")["status"] == "Open",
	"an unknown status falls back to Open rather than showing everything")

# --- MONITORING: what you can do -------------------------------------------
reset()
result = service.set_finding_status("F-1", "Resolved")
report(result["ok"] and result["was"] == "Open" and State.saved,
	"an open finding can be resolved")
report(service.set_finding_status("F-3", "Open")["status"] == "Open",
	"a resolved finding can be reopened")

reset()
report(raises(ValidationError_, service.set_finding_status, "F-1", "Suppressed"),
	"suppressing WITHOUT a reason is refused")
report(not State.saved, "...and nothing was written")
report(service.set_finding_status("F-1", "Suppressed", "Known exception, signed off by QA")["ok"],
	"suppressing WITH a reason works")
report(any(row.get("suppression_reason") for row in State.saved),
	"...and the reason is stored on the record, not just in a log")

reset()
report(raises(ValidationError_, service.set_finding_status, "F-1", "Ignored"),
	"an invented status is refused")

reset()
State.may_write_findings = False
report(raises(PermissionError_, service.set_finding_status, "F-1", "Resolved"),
	"seeing a finding does NOT mean being allowed to close it")
report(not State.saved, "...and nothing was written")
report(len(service.findings("Open")["findings"]) == 2,
	"...but that reader can still SEE the findings")
report(service.findings("Open")["can_manage"] is False,
	"...and the page is told not to draw the buttons")

# --- KNOWLEDGE: empty is stated, never disguised ---------------------------
reset()
empty = service.knowledge_overview()
report(empty["total"] == 0 and empty["sources"] == [],
	"with no documents registered, the list is empty")
report(empty["chunks"] == 0 and empty["indexed"] == 0,
	"...and nothing is fabricated to make the panel look populated")

# --- KNOWLEDGE: the ingestion path that did not exist ----------------------
reset()
added = service.add_source("Student Support Services Procedure", "Procedure",
	text="Section 1. Counselling is offered before enrolment.")
report(added["ok"] and added["indexed"], "a document can be registered AND indexed in one step")
report(State.registered and State.indexed, "...and the engine really ran")
report(len(State.indexed) == 1,
	"indexed EXACTLY ONCE -- register_source() already indexes, and calling it "
	"again is what made Felix's registration look like it did nothing")
report(added["sections"] == 2, "the section count comes back for the confirmation message")
after = service.knowledge_overview()
report(after["total"] == 1 and after["indexed"] == 1 and after["chunks"] == 2,
	"the panel then reports it as indexed, with its section count")

reset()
report(raises(ValidationError_, service.add_source, "", "Policy", text="x"),
	"a source with no title is refused")

reset()
State.may_write_sources = False
report(raises(PermissionError_, service.add_source, "Anything", "Policy", text="x"),
	"a reader cannot register a document")
report(raises(PermissionError_, service.reindex), "...nor trigger a re-index")
report(service.knowledge_overview()["can_manage"] is False,
	"...and the page is told not to draw the form")

# Registered-but-not-indexed is a real state, and reported rather than hidden.
reset()
import ucc_intelligence.knowledge.ingestion as fake_ingestion  # noqa: E402


def failing_index(*args, **kwargs):
	raise RuntimeError("extractor unavailable")


fake_ingestion.register_source = failing_index
broken = service.add_source("Half a document", "Policy", text="x")
report(broken["ok"] is False and broken.get("message"),
	"a registration that RAISES reports the reason -- never a silent no-op")
report("extractor unavailable" in broken["message"], "...and it is the real reason: %r" % broken["message"])

reset()
report(raises(ValidationError_, service.add_source, "A title but no text", "Policy"),
	"a document with neither text nor an attachment is refused up front")

# --- EVERY FIELD THIS MODULE ASKS FOR MUST REALLY EXIST ---------------------
# The bug this exists for: Sophia asked for `rule_title`, `first_seen`,
# `last_seen`, `rules_run`, `findings_open`, `last_run`, `version` and
# `resolution_note`. None of them exist, and Felix got
#     (1054, "Unknown column 'rule_title' in 'SELECT'")
# the moment he opened the panel.
#
# The previous report listed those names as "unverified, needs your bench".
# They were not unverifiable at all -- every one is in a JSON file in this
# repository. Caution that does not actually check is just a slower guess. So
# this reads the DocType definitions and compares.
import json as _json  # noqa: E402
import re as _re  # noqa: E402

DOCTYPE_DIR = ROOT / "ucc_intelligence" / "ucc_intelligence" / "sophia" / "doctype"
# Fields Frappe gives every DocType, which never appear in its own JSON.
STANDARD = {"name", "owner", "creation", "modified", "modified_by", "docstatus", "idx"}


def fields_of(doctype):
	folder = doctype.lower().replace(" ", "_")
	path = DOCTYPE_DIR / folder / (folder + ".json")
	if not path.exists():
		return None
	return {f["fieldname"] for f in _json.loads(path.read_text())["fields"]} | STANDARD


service_source = (ROOT / "ucc_intelligence" / "ucc_intelligence" / "operations"
	/ "service.py").read_text(encoding="utf-8")

# Every `fields=[...]` list in the module, paired with the DocType constant on
# the same call. Parsed from source so a new query cannot skip this check.
for constant, doctype in (("FINDING_DOCTYPE", "UCC Monitoring Finding"),
		("RUN_DOCTYPE", "UCC Monitoring Run"),
		("RULE_DOCTYPE", "UCC Monitoring Rule"),
		("SOURCE_DOCTYPE", "UCC Knowledge Source"),
		("CHUNK_DOCTYPE", "UCC Knowledge Chunk")):
	real = fields_of(doctype)
	report(real is not None, "%s's DocType JSON is readable" % doctype)
	if not real:
		continue
	asked = set()
	for call in _re.finditer(
			r"\(\s*%s\s*,(.{0,700}?)\)" % constant, service_source, _re.S):
		block = call.group(1)
		for group in _re.findall(r"fields=\[(.*?)\]", block, _re.S):
			asked |= set(_re.findall(r'"([a-z_]+)"', group))
		for group in _re.findall(r"filters=\{(.*?)\}", block, _re.S):
			asked |= set(_re.findall(r'"([a-z_]+)"\s*:', group))
	unknown = sorted(asked - real)
	report(not unknown, "%s: every field asked for exists (%s)"
		% (doctype, ", ".join(unknown) if unknown else "ok"))


# --- SETTINGS sections 2 and 4 ---------------------------------------------
reset()
access_module = types.ModuleType("ucc_intelligence.permissions.access")
access_module.build_response = lambda: {
	"criteria": {"criterion_1": True, "criterion_4": False},
	"ask_student_journey": True, "ask_quality_action": False}
sys.modules["ucc_intelligence.permissions.access"] = access_module

overview = service.access_overview()
report(overview["ok"] and len(overview["criteria"]) == 2,
	"access settings list the criteria from UCC Dashboard Access")
report(overview["criteria"][1]["visible"] is False,
	"...with their real visibility, not a default")
report(overview["modules"]["ask_quality_action"] is False,
	"the Ask UCC modules come from the same place")
report(set(overview) >= {"can_edit_tabs", "can_manage_findings", "can_manage_sources"},
	"and the three DocType permissions are mirrored read-only")
report("Role Permission Manager" in overview["note"],
	"...with where they are actually changed, so this page invents no new concept")

# Rule config: on/off and severity ONLY. The definition stays in code.
State.rule_records = []
saved_rules = []


class FakeRule:
	def __init__(self):
		self.data = {}

	def __setattr__(self, key, value):
		if key == "data":
			object.__setattr__(self, key, value)
		else:
			self.data[key] = value

	def __getattr__(self, key):
		return self.data.get(key)

	def insert(self):
		saved_rules.append(dict(self.data))

	def save(self):
		saved_rules.append(dict(self.data))


sys.modules["frappe"].new_doc = lambda doctype: FakeRule()
result = service.set_rule_config("student_log_background_required", enabled="1", severity="Low")
report(result["ok"] and result["enabled"] and result["severity"] == "Low",
	"a rule can be switched on and its severity changed")
report(saved_rules and saved_rules[0].get("title"),
	"a first-time record is seeded from the registry, so it describes the rule correctly")
report(raises(ValidationError_, service.set_rule_config, "invented_rule", enabled="1"),
	"an unknown rule id is refused, never used to reach code by name")
State.may_write_findings = False
State.may_write_sources = False
report(raises(PermissionError_, service.set_rule_config,
	"student_log_background_required", enabled="0"),
	"a reader cannot change a rule")
State.may_write_findings = True
State.may_write_sources = True

rule_body = inspect.getsource(service.set_rule_config) if "inspect" in dir() else ""


# --- ONE settings surface, all five sections -------------------------------
reset()
only_for_calls = []
sys.modules["frappe"].only_for = lambda role: only_for_calls.append(role)


class FakeSingle:
	def __init__(self):
		self.data = {"enable_ai": 1, "ai_provider": "OpenAI", "ai_model": "gpt-4",
			"max_output_tokens": 800, "default_temperature": 0.2,
			"ai_request_timeout_seconds": 30, "chart_palette": "",
			"enable_document_knowledge": 0, "enable_persistent_conversations": 1,
			"enable_monitoring": 0}
		self.saved = False

	def get(self, key):
		return self.data.get(key)

	def set(self, key, value):
		self.data[key] = value

	def save(self):
		self.saved = True


single = FakeSingle()


# get_meta reads the REAL DocType JSON, so a settings field that does not exist
# fails here rather than rendering as an empty box on Felix's screen -- the
# same lesson as `rule_title`, applied before it can bite twice.
class FakeMeta:
	def __init__(self, doctype):
		path = (ROOT / "ucc_intelligence/ucc_intelligence/sophia/doctype"
			/ doctype.lower().replace(" ", "_") / (doctype.lower().replace(" ", "_") + ".json"))
		self.fields = {f["fieldname"]: f for f in _json.loads(path.read_text())["fields"]}

	def get_field(self, fieldname):
		row = self.fields.get(fieldname)
		return types.SimpleNamespace(fieldtype=row["fieldtype"],
			options=row.get("options")) if row else None


sys.modules["frappe"].get_single = lambda doctype: single
sys.modules["frappe"].get_meta = FakeMeta
sys.modules["frappe"].utils.cint = lambda v: int(float(v or 0))
sys.modules["frappe"].utils.flt = lambda v: float(v or 0)

settings = service.platform_settings()
report(settings["ok"] and len(settings["sections"]) == 4,
	"the settings surface serves every section in ONE call (%d)" % len(settings["sections"]))
keys = [section["key"] for section in settings["sections"]]
report(keys == ["ai", "presentation", "knowledge", "monitoring"],
	"...in a stable order: %s" % keys)
report("System Manager" in only_for_calls, "reading them is System Manager only")
fields = [f["fieldname"] for section in settings["sections"] for f in section["fields"]]
report("chart_palette" in fields and "enable_ai" in fields,
	"the palette (ADR-015) and the AI toggle are both on the one surface")

# The allowlist is the point: a settings endpoint that writes whatever it is
# handed can set fields nobody put on the page.
#
# `ai_settings_section` is the load-bearing case. It is a REAL field on the
# DocType, so meta.get_field() finds it and the meta lookup waves it through --
# only SETTINGS_FIELDS stops it. Deleting the allowlist used to survive this
# whole block, because every made-up name was already caught by the meta.
del only_for_calls[:]
result = service.save_platform_settings({"enable_ai": "0", "chart_palette": "#111111",
	"max_output_tokens": "1200", "default_temperature": "0.7",
	"some_other_field": "sneaky", "owner": "attacker@example.com",
	"ai_settings_section": "clobbered"})
report("System Manager" in only_for_calls, "writing them is System Manager only, checked again")
report("ai_settings_section" not in single.data,
	"a real DocType field that is not on the settings page is still refused")
report(result["ok"] and single.saved, "saving works")
report(single.data["enable_ai"] == 0 and single.data["chart_palette"] == "#111111",
	"...and writes the allowlisted fields")
report(single.data["max_output_tokens"] == 1200 and single.data["default_temperature"] == 0.7,
	"...with their real types, not strings")
report("some_other_field" not in single.data and single.data.get("owner") is None,
	"a field that is NOT on the allowlist is ignored, never written")
report(set(result["written"]) <= set(service.SETTINGS_FIELDS),
	"and the report of what was written names only allowlisted fields")
report(raises(ValidationError_, service.save_platform_settings, "not json at all"),
	"junk instead of settings is refused rather than half-applied")

# Found by SCREENSHOT, not by assertion: `.ucc-ops-form label` sets a column
# direction and outranks a bare `.ucc-set-check`, so every checkbox stacked
# above its own label. Same family as the hairline-column bug -- every check
# passed while the surface was wrong.
PAGE = (ROOT / "ucc_intelligence/ucc_intelligence/sophia/page/sophia_analytics"
	/ "sophia_analytics.js").read_text()
report(".ucc-ops-form label.ucc-set-check" in PAGE,
	"the checkbox rule outranks .ucc-ops-form label, so it is not stacked")
report('.replace(/\\bAi\\b/g,"AI")' in PAGE,
	'the settings labels read "AI", not "Ai"')


# --- the gate must be EXPLICIT, not inherited from the DocType -------------
# Removing the permission check from set_finding_status() passed every
# behavioural check above, because FakeDoc.save() refuses anyway -- exactly as
# a real Document would. That is the same hole that hid a missing gate on
# set_intro() and set_palette() in earlier rounds. Asserted by source, per
# function, and by ORDER: the check has to come before anything is touched.
import inspect  # noqa: E402

for function, first_call in (
		(service.set_finding_status, "frappe.get_doc("),
		(service.add_source, "ingestion.register_source("),
		(service.reindex, "ingestion.index_source(")):
	body = inspect.getsource(function)
	name = function.__name__
	report("can_manage" in body, "%s() asks permission explicitly" % name)
	report(first_call not in body or body.index("can_manage") < body.index(first_call),
		"...and asks BEFORE it acts")

print("\n%s: %d/%d checks" % ("PASS" if all(checks) else "FAIL", sum(checks), len(checks)))
sys.exit(0 if all(checks) else 1)
