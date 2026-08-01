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
		self.meta = types.SimpleNamespace(has_field=lambda field: field in ("resolution_note",))

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
	frappe.get_all = lambda doctype, **kwargs: (
		list(State.rule_records) if doctype == "UCC Monitoring Rule" else [])
	frappe.get_doc = lambda doctype, name: FakeDoc(
		next(row for row in State.findings if row["name"] == name))
	frappe.get_single = lambda doctype: types.SimpleNamespace(
		enable_document_knowledge=State.knowledge_enabled)
	frappe.has_permission = lambda doctype, ptype=None: (
		State.may_write_findings if doctype == "UCC Monitoring Finding"
		else State.may_write_sources)
	frappe.utils = types.SimpleNamespace(cstr=lambda v: "" if v is None else str(v))
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
		name = "SRC-%02d" % (len(State.registered) + 1)
		State.registered.append({"name": name, "title": title, "source_type": source_type})
		State.sources.append({"name": name, "title": title, "source_type": source_type,
			"sync_status": "Not indexed", "last_indexed": None, "is_active": 1,
			"version": "1", "classification": "Internal", "superseded_by": None,
			"owner_department": "", "effective_date": None, "review_date": None})
		return name

	def index_source(source_name, text=None):
		State.indexed.append(source_name)
		for row in State.sources:
			if row["name"] == source_name:
				row["last_indexed"] = "2026-08-03 02:00:00"
				row["sync_status"] = "Indexed"
		State.chunks[source_name] = ["c1", "c2"]

	ingestion.register_source = register_source
	ingestion.index_source = index_source
	ingestion.reindex_stale = lambda: [row["name"] for row in State.sources
		if row.get("sync_status") == "Stale"]
	sys.modules["ucc_intelligence.knowledge.ingestion"] = ingestion


install()
from ucc_intelligence.operations import service  # noqa: E402


def reset():
	State.findings = [
		{"name": "F-1", "rule_id": "student_log_background_required",
			"rule_title": "Student Log closed without student background", "status": "Open",
			"severity": "High", "target_doctype": "Student Log", "target_record": "LOG-001",
			"detail": "Background is empty.", "first_seen": "2026-08-01", "last_seen": "2026-08-02"},
		{"name": "F-2", "rule_id": "quality_action_closure_evidence",
			"rule_title": "Quality Action closed without evidence", "status": "Open",
			"severity": "Medium", "target_doctype": "Quality Action", "target_record": "QA-9",
			"detail": "No evidence attached.", "first_seen": "2026-08-01", "last_seen": "2026-08-02"},
		{"name": "F-3", "rule_id": "student_log_background_required",
			"rule_title": "Student Log closed without student background", "status": "Resolved",
			"severity": "High", "target_doctype": "Student Log", "target_record": "LOG-007",
			"detail": "Was empty.", "first_seen": "2026-07-01", "last_seen": "2026-07-20"},
	]
	State.readable_findings = {"F-1", "F-2", "F-3"}
	State.may_write_findings = True
	State.may_write_sources = True
	State.knowledge_enabled = True
	State.monitoring_enabled = True
	State.sources = []
	State.chunks = {}
	State.rule_records = [{"name": "R-1", "rule_id": "student_log_background_required",
		"enabled": 1, "last_run": "2026-08-02 03:00:00", "severity": "High"}]
	State.runs = [{"name": "RUN-1", "status": "Completed", "started_at": "2026-08-02 03:00:00",
		"finished_at": "2026-08-02 03:01:00", "rules_run": 2, "findings_open": 2,
		"findings_resolved": 1}]
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
report(any(row.get("resolution_note") for row in State.saved),
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
report(State.registered and State.indexed, "...and both engine calls really ran")
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


def failing_index(source_name, text=None):
	raise RuntimeError("extractor unavailable")


fake_ingestion.index_source = failing_index
partial = service.add_source("Half a document", "Policy", text="x")
report(partial["ok"] and partial["indexed"] is False and partial.get("message"),
	"a source that registers but fails to index says so instead of rolling back")

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
