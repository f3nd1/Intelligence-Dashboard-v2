#!/usr/bin/env python3
"""Self-check for monitoring (CLAUDE.md Phase 11).

Two things are worth testing here and they are different in kind:

1. The RULES are pure functions -- a dict in, a detail string or None out.
   Tested directly, with the boundary cases that decide whether a rule is
   useful or just noisy (an open record is not yet a failure; "N/A" is not
   a filled-in field; a marker inside a longer word must not fire).

2. The ENGINE's job is bookkeeping, and its one real property is
   IDEMPOTENCE: a rule that runs daily against mostly-unchanged records
   must not accumulate duplicate findings. That is tested by running the
   same rule repeatedly against a fake database and asserting the finding
   count, not by asserting that one call returns something.

    python3 tools/test_ucc_intelligence_monitoring.py
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
checks = []


def report(ok, message):
	print(("PASS" if ok else "FAIL") + ": " + message)
	checks.append(bool(ok))
	return ok


sys.path.insert(0, str(ROOT / "ucc_intelligence"))


# ============================================================
# A fake database with just enough behaviour to exercise the engine.
# ============================================================
class State:
	tables = {}      # doctype -> {name: dict}
	rows = {}        # doctype -> list of dicts (query targets)
	settings = None
	counter = 0
	fail_query = False


class FakeDoc(dict):
	def __init__(self, values):
		super().__init__(values)
		self.__dict__ = self

	def __getattr__(self, name):
		# A real Frappe Document returns None for a field that has never been
		# set, rather than raising. The engine relies on that (`run.findings_opened
		# or 0`), so the fake must behave the same or the test passes for the
		# wrong reason.
		if name.startswith("__"):
			raise AttributeError(name)
		return None

	def insert(self, ignore_permissions=False):
		State.counter += 1
		if not self.get("name"):
			self["name"] = "%s-%04d" % (self["doctype"][:6].replace(" ", ""), State.counter)
		# autoname: field:rule_id
		if self["doctype"] == "UCC Monitoring Rule":
			self["name"] = self["rule_id"]
		State.tables.setdefault(self["doctype"], {})[self["name"]] = self
		return self

	def save(self, ignore_permissions=False):
		State.tables.setdefault(self["doctype"], {})[self["name"]] = self
		return self


def _get_doc(arg, name=None):
	if isinstance(arg, dict):
		return FakeDoc(dict(arg))
	return State.tables.get(arg, {})[name]


def _get_all(doctype, filters=None, fields=None, limit_page_length=None,
		ignore_permissions=False, order_by=None, pluck=None):
	if doctype in ("UCC Monitoring Finding", "UCC Monitoring Rule", "UCC Monitoring Run"):
		rows = list(State.tables.get(doctype, {}).values())
		if filters:
			for key, value in filters.items():
				rows = [r for r in rows if r.get(key) == value]
		return [dict(r) for r in rows]
	if State.fail_query:
		raise RuntimeError("simulated query failure")
	rows = State.rows.get(doctype, [])
	if filters and "creation" in filters:
		_, cutoff = filters["creation"]
		rows = [r for r in rows if str(r.get("creation") or "") >= str(cutoff)]
	return [dict(r) for r in rows]


def _exists(doctype, name):
	return name in State.tables.get(doctype, {})


frappe_stub = types.ModuleType("frappe")
frappe_stub.get_doc = _get_doc
frappe_stub.get_all = _get_all
frappe_stub.get_list = _get_all
frappe_stub.get_single = lambda doctype: State.settings
frappe_stub.db = types.SimpleNamespace(exists=_exists)
frappe_stub._ = lambda text, *a, **k: text
frappe_stub.log_error = lambda *a, **k: None


class FrappeThrow(Exception):
	pass


def _throw(message, **kwargs):
	raise FrappeThrow(message)


frappe_stub.throw = _throw
utils = types.ModuleType("frappe.utils")
utils.now = staticmethod(lambda: "2026-07-31 04:00:00")
utils.cstr = lambda v: "" if v is None else str(v)
utils.cint = lambda v: int(v) if str(v or "").strip().lstrip("-").isdigit() else 0
frappe_stub.utils = utils
sys.modules["frappe"] = frappe_stub
sys.modules["frappe.utils"] = utils

from ucc_intelligence.monitoring import engine, rule_registry  # noqa: E402


# ============================================================
# The rules themselves -- pure functions, tested directly
# ============================================================
SL_BACKGROUND = rule_registry.RULES["student_log_background_required"]["evaluate"]

report(SL_BACKGROUND({"status": "Open", "student_background": ""}) is None,
	"an OPEN log with no background is not a finding -- it is simply not finished yet")
report(SL_BACKGROUND({"status": "Completed", "student_background": ""}) is not None,
	"a COMPLETED log with no background IS a finding -- that is the rule's whole point")
report(SL_BACKGROUND({"status": "Closed", "student_background": "<p>&nbsp;</p>"}) is not None,
	"empty HTML from the text editor counts as blank, not as content")
report(SL_BACKGROUND({"status": "Closed", "student_background": "N/A"}) is not None,
	"'N/A' is not a filled-in background")
report(SL_BACKGROUND({"status": "Closed", "student_background": "Student relocated from Johor in 2024."}) is None,
	"a real background passes")
report("Completed" in (SL_BACKGROUND({"status": "Completed", "student_background": ""}) or ""),
	"the detail names the actual status, so the finding is readable without opening the record")

SL_DUMMY = rule_registry.RULES["student_log_dummy_text"]["evaluate"]
report(SL_DUMMY({"student_background": "Lorem ipsum dolor sit amet"}) is not None,
	"lorem ipsum is caught")
report(SL_DUMMY({"details": "TBC"}) is not None, "TBC is caught")
report(SL_DUMMY({"action_taken": "<b>Placeholder</b> text"}) is not None,
	"a marker inside HTML markup is still caught")
report(SL_DUMMY({"student_background": "Discussed timetable clash with the student."}) is None,
	"real content is not flagged")
report(SL_DUMMY({"student_background": "Student attends the Tbcaster programme."}) is None,
	"a marker inside a longer word does NOT fire -- that would make the rule noise")
report(SL_DUMMY({"student_background": None, "details": None}) is None,
	"empty fields are not dummy text (that is the other rule's job)")
detail = SL_DUMMY({"details": "TBD", "student_background": "lorem ipsum here"})
report("student_background" in detail and "details" in detail,
	"every offending field is named, not just the first one found")

QA_CLOSURE = rule_registry.RULES["quality_action_closure_evidence"]["evaluate"]
report(QA_CLOSURE({"status": "Open", "assigned_to": "", "target_date": "", "resolution": "", "action_taken": ""}) is None,
	"an open Quality Action row is not judged on closure evidence")
closed_empty = QA_CLOSURE({"status": "Completed", "assigned_to": "", "target_date": "",
	"resolution": "", "action_taken": ""})
report(closed_empty is not None, "a closed row with no evidence is a finding")
for phrase in ("owner", "target date", "resolution", "action taken"):
	report(phrase in closed_empty, "the detail names the missing %r specifically" % phrase)
report(QA_CLOSURE({"status": "Completed", "assigned_to": "hr@ucc", "target_date": "2026-01-01",
	"resolution": "Process updated.", "action_taken": "Retrained staff."}) is None,
	"a properly evidenced closure passes")

# Every registered rule must be well-formed -- a rule missing a field list
# would silently evaluate against nothing.
for rule_id, definition in rule_registry.RULES.items():
	report(definition["rule_id"] == rule_id, "%s: rule_id matches its registry key" % rule_id)
	for key in ("title", "purpose", "target_doctype", "fields", "severity", "version", "evaluate"):
		report(key in definition, "%s: declares %r" % (rule_id, key))
	report("name" in definition["fields"], "%s: loads `name`, which the finding key needs" % rule_id)
	report(definition["fields"] != ["*"] and "*" not in definition["fields"],
		"%s: names its fields explicitly rather than selecting everything" % rule_id)
	report(definition["evaluate"]({f: None for f in definition["fields"]}) is None
		or True, "%s: evaluates an all-empty row without raising" % rule_id)


# ============================================================
# The engine -- idempotence is the property that matters
# ============================================================
def reset(rows):
	State.tables = {}
	State.rows = {"Student Log": rows}
	State.counter = 0
	State.fail_query = False


def findings():
	return list(State.tables.get("UCC Monitoring Finding", {}).values())


BAD = {"name": "SL-1", "status": "Completed", "student_background": "", "creation": "2026-01-01"}
GOOD = {"name": "SL-2", "status": "Completed", "student_background": "Real notes.", "creation": "2026-01-01"}

reset([BAD, GOOD])
first = engine.run_rule("student_log_background_required")
report(first["status"] == "Completed", "a run completes")
report(first["records_evaluated"] == 2, "both records were evaluated")
report(first["findings_opened"] == 1, "exactly the one failing record produced a finding")
report(len(findings()) == 1, "one finding row exists")
report(findings()[0]["target_record"] == "SL-1", "the finding names the failing record")

# THE property: rerunning must not duplicate.
second = engine.run_rule("student_log_background_required")
report(len(findings()) == 1, "RERUN: still exactly one finding -- the rule is idempotent")
report(second["findings_opened"] == 0, "RERUN: nothing new was opened")
report(findings()[0]["occurrence_count"] == 2, "RERUN: the existing finding counts the second sighting")

for _ in range(5):
	engine.run_rule("student_log_background_required")
report(len(findings()) == 1, "RERUN x7: still one finding, not seven")
report(findings()[0]["occurrence_count"] == 7, "RERUN x7: the count tracks every sighting")

# Fixed record -> resolved, not deleted.
State.rows["Student Log"] = [dict(BAD, student_background="Now filled in."), GOOD]
third = engine.run_rule("student_log_background_required")
report(third["findings_resolved"] == 1, "a fixed record resolves its finding")
report(len(findings()) == 1, "the finding is RESOLVED, not deleted -- the history is the point")
report(findings()[0]["status"] == "Resolved", "...and its status says so")
report(bool(findings()[0]["resolved_at"]), "resolution is timestamped")

# Regression -> reopen the same row, not a second one.
State.rows["Student Log"] = [BAD, GOOD]
fourth = engine.run_rule("student_log_background_required")
report(fourth["findings_reopened"] == 1, "a regressed record REOPENS its finding")
report(len(findings()) == 1, "...on the same row, so the history stays in one place")
report(findings()[0]["status"] == "Open" and not findings()[0]["resolved_at"],
	"a reopened finding is Open again and its resolved timestamp is cleared")

# Suppression must survive a rerun.
findings()[0]["status"] = "Suppressed"
findings()[0]["suppression_reason"] = "Agreed exception, reviewed 2026-07-31."
before = dict(findings()[0])
engine.run_rule("student_log_background_required")
report(findings()[0]["status"] == "Suppressed",
	"a SUPPRESSED finding is not resurrected by a rerun -- someone recorded a reason")
report(findings()[0]["occurrence_count"] == before["occurrence_count"],
	"...and is not touched at all")

# A disabled rule evaluates nothing.
State.tables["UCC Monitoring Rule"]["student_log_background_required"]["enabled"] = 0
disabled = engine.run_rule("student_log_background_required")
report(disabled["records_evaluated"] == 0 and disabled["status"] == "Completed",
	"a disabled rule completes without evaluating anything")
State.tables["UCC Monitoring Rule"]["student_log_background_required"]["enabled"] = 1

# effective_date must not retroactively fault historic records.
reset([dict(BAD, creation="2020-01-01")])
engine.get_rule_doc("student_log_background_required")["effective_date"] = "2026-01-01"
scoped = engine.run_rule("student_log_background_required")
report(scoped["records_evaluated"] == 0,
	"a record predating the rule's effective date is not evaluated")
report(len(findings()) == 0, "...and produces no finding")

# A failing rule records a Failed run instead of taking the batch down.
reset([BAD])
State.fail_query = True
failed = engine.run_rule("student_log_background_required")
report(failed["status"] == "Failed", "a query failure is recorded as a Failed run")
report("simulated" in (failed["error_message"] or ""), "the failure reason is captured")
State.fail_query = False
reset([BAD])
report(len(engine.run_all_rules()) == len(rule_registry.RULES),
	"run_all_rules runs every registered rule")

# An unknown rule id is rejected, never used to reach code by name.
try:
	engine.run_rule("../../etc/passwd")
	report(False, "an unknown rule id should be rejected")
except FrappeThrow:
	report(True, "an unknown rule id is rejected against the fixed registry")

# The settings gate: monitoring must not start scanning on install.
State.settings = None
report(engine.monitoring_enabled() is False,
	"monitoring defaults OFF when settings are unreadable -- it reads every record in scope")
report("skipped" in engine.scheduled_run(), "the scheduled entry point skips when monitoring is off")


class FakeSettings:
	enable_monitoring = 1


State.settings = FakeSettings()
reset([BAD])
report("runs" in engine.scheduled_run(), "the scheduled entry point runs when monitoring is on")

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
