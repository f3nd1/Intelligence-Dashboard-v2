#!/usr/bin/env python3
"""Self-check for controlled actions (CLAUDE.md Phase 12).

The property worth testing is not "propose works". It is that NOTHING CAN
EXECUTE WITHOUT A HUMAN. Everything below exists to attack that from a
different angle: execute straight from Draft, execute an unapproved
request, execute twice, execute an action that is not on the allowlist,
execute against a record the user cannot write.

    python3 tools/test_ucc_intelligence_actions.py
"""
import json
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


class State:
	docs = {}
	counter = 0
	user = "staff@ucc.edu.sg"
	roles = ["All"]
	write_denied = set()
	read_denied = set()
	applied = []          # (doc, workflow_action) the framework was asked to apply
	workflow_allows = True


class FakeDoc(dict):
	def __init__(self, values):
		super().__init__(values)
		self.__dict__ = self

	def __getattr__(self, name):
		if name.startswith("__"):
			raise AttributeError(name)
		return None

	def insert(self, ignore_permissions=False):
		State.counter += 1
		self["name"] = self.get("name") or "%s-%04d" % (self["doctype"][:8].replace(" ", ""), State.counter)
		State.docs[(self["doctype"], self["name"])] = self
		return self

	def save(self, ignore_permissions=False):
		State.docs[(self["doctype"], self["name"])] = self
		return self

	def reload(self):
		return self

	def check_permission(self, ptype):
		key = (self["doctype"], self["name"])
		denied = State.write_denied if ptype == "write" else State.read_denied
		if key in denied:
			raise FrappePermissionError("No permission to %s %s" % (ptype, self["name"]))
		return True


class FrappeThrow(Exception):
	pass


class FrappePermissionError(Exception):
	pass


def _get_doc(arg, name=None):
	if isinstance(arg, dict):
		return FakeDoc(dict(arg))
	key = (arg, name)
	if key not in State.docs:
		raise FrappeThrow("no such %s %s" % (arg, name))
	return State.docs[key]


def _get_list(doctype, filters=None, fields=None, order_by=None, limit_page_length=None):
	rows = [dict(v) for (dt, _), v in State.docs.items() if dt == doctype]
	for key, value in (filters or {}).items():
		rows = [r for r in rows if r.get(key) == value]
	return rows


def _db_get_value(doctype, filters, fieldname):
	for (dt, name), doc in State.docs.items():
		if dt != doctype:
			continue
		if isinstance(filters, dict) and all(doc.get(k) == v for k, v in filters.items()):
			return doc.get(fieldname) if fieldname != "name" else name
	return None


def _db_set_value(doctype, name, field, value):
	State.docs[(doctype, name)][field] = value


frappe_stub = types.ModuleType("frappe")
frappe_stub.get_doc = _get_doc
frappe_stub.get_list = _get_list
frappe_stub.get_all = _get_list
frappe_stub.db = types.SimpleNamespace(get_value=_db_get_value, set_value=_db_set_value)
frappe_stub.session = types.SimpleNamespace(user=State.user)
frappe_stub._ = lambda text, *a, **k: text
frappe_stub.throw = lambda msg, **kw: (_ for _ in ()).throw(FrappeThrow(msg))
frappe_stub.log_error = lambda *a, **k: None
frappe_stub.as_json = lambda v: json.dumps(v, default=str)
frappe_stub.parse_json = lambda v: json.loads(v) if isinstance(v, str) else v
frappe_stub.PermissionError = FrappePermissionError
utils = types.ModuleType("frappe.utils")
utils.now = staticmethod(lambda: "2026-07-31 09:00:00")
utils.today = staticmethod(lambda: "2026-07-31")
utils.cstr = lambda v: "" if v is None else str(v)
utils.cint = lambda v: int(v) if str(v or "").strip().lstrip("-").isdigit() else 0
frappe_stub.utils = utils

# frappe.model.workflow.apply_workflow -- the framework gate. Stubbed to
# RECORD what was asked of it, so the tests can prove the service delegates
# rather than setting workflow_state itself.
workflow_module = types.ModuleType("frappe.model.workflow")


def apply_workflow(doc, action):
	State.applied.append((doc["name"], action))
	if not State.workflow_allows:
		raise FrappeThrow("Workflow transition not allowed for this user")
	nxt = {"Submit for Approval": "Pending Approval", "Approve": "Approved",
		"Reject": "Rejected", "Execute": "Executed"}[action]
	doc["workflow_state"] = nxt
	return doc


workflow_module.apply_workflow = apply_workflow
model_module = types.ModuleType("frappe.model")
model_module.workflow = workflow_module
sys.modules["frappe"] = frappe_stub
sys.modules["frappe.utils"] = utils
sys.modules["frappe.model"] = model_module
sys.modules["frappe.model.workflow"] = workflow_module

from ucc_intelligence.actions import registry, service  # noqa: E402


# ============================================================
# The allowlist is the boundary between model output and code
# ============================================================
report(all(spec["level"] <= registry.LEVEL_CONFIRM_BEFORE_EXECUTE for spec in registry.ACTIONS.values()),
	"NO action is above level 2 -- levels 3 and 4 are not implemented, as CLAUDE.md §12 requires")
report(registry.summary()["max_level"] == 2, "the registry reports its own ceiling honestly")
for key, spec in registry.ACTIONS.items():
	report(callable(spec["execute"]), "%s has a real executor" % key)
	report(bool(spec["description"]), "%s explains what it does" % key)
	if spec["placeholder"]:
		report("PLACEHOLDER" in spec["description"],
			"%s is a placeholder and says so in its own description" % key)

try:
	service.propose("../../etc/passwd", "evil")
	report(False, "an unknown action type should be refused")
except FrappeThrow:
	report(True, "an action type not on the allowlist is REFUSED -- model output cannot reach code by name")


# ============================================================
# Propose creates a Draft and nothing else
# ============================================================
State.docs.clear()
proposed = service.propose("draft_reminder", "Chase missing background",
	payload={"draft_text": "Please complete the student background."},
	reason="Monitoring finding", sources=[{"doctype": "Student Log", "record": "SL-1"}])
report(proposed["ok"] and proposed["created"], "propose() creates a request")
request_name = proposed["action_request"]
doc = State.docs[("UCC AI Action Request", request_name)]
report(doc["workflow_state"] == service.STATE_DRAFT, "a new request starts in Draft")
report(doc["execution_status"] == "Not Executed", "nothing has executed")
report(doc["requested_by"] == State.user, "the proposer is recorded")
report(bool(doc["idempotency_key"]), "an idempotency key is stored")

again = service.propose("draft_reminder", "Chase missing background",
	payload={"draft_text": "Please complete the student background."},
	reason="Monitoring finding", sources=[{"doctype": "Student Log", "record": "SL-1"}])
report(not again["created"] and again["action_request"] == request_name,
	"IDEMPOTENT: the identical proposal reuses the request, it does not create a second")


# ============================================================
# THE PROPERTY: nothing executes without a human approving it
# ============================================================
try:
	service.execute(request_name)
	report(False, "executing a DRAFT request should be refused")
except FrappeThrow as error:
	report("Approved" in str(error), "executing straight from Draft is REFUSED, naming the required state")
report(State.docs[("UCC AI Action Request", request_name)]["execution_status"] == "Not Executed",
	"...and nothing ran")

service.transition(request_name, "Submit for Approval")
report(State.docs[("UCC AI Action Request", request_name)]["workflow_state"] == service.STATE_PENDING,
	"Submit for Approval moves it to Pending")
try:
	service.execute(request_name)
	report(False, "executing a PENDING request should be refused")
except FrappeThrow:
	report(True, "executing while merely Pending is REFUSED -- pending is not approval")

service.transition(request_name, "Approve")
report(State.docs[("UCC AI Action Request", request_name)]["approved_by"] == State.user,
	"the approver is recorded separately from the proposer")

result = service.execute(request_name)
report(result["ok"], "an APPROVED request executes")
report("DRAFT ONLY" in result["result"], "a level-1 action produces text and says it sent nothing")
report(State.docs[("UCC AI Action Request", request_name)]["execution_status"] == "Succeeded",
	"execution status is recorded")
report(("Execute" in [a for _, a in State.applied]),
	"execution moves the request through the WORKFLOW, not by setting the field directly")

repeat = service.execute(request_name)
report(repeat.get("already_executed") is True,
	"IDEMPOTENT: executing twice does NOT run the action a second time")


# ============================================================
# The service must delegate to Frappe's workflow, not reimplement it
# ============================================================
service_source = (ROOT / "ucc_intelligence/ucc_intelligence/actions/service.py").read_text(encoding="utf-8")
report("apply_workflow" in service_source,
	"transitions go through frappe.model.workflow.apply_workflow (Felix's decision: native Workflow)")
code_lines = [line for line in service_source.splitlines() if not line.strip().startswith("#")]
code_only = "\n".join(code_lines)
report('doc.workflow_state = ' not in code_only and 'doc["workflow_state"] =' not in code_only,
	"the service NEVER sets workflow_state itself -- the framework owns state")

State.workflow_allows = False
State.docs.clear()
State.applied = []
blocked = service.propose("draft_reminder", "x", payload={"draft_text": "y"})
try:
	service.transition(blocked["action_request"], "Approve")
	report(False, "a workflow-denied transition should propagate")
except FrappeThrow:
	report(True, "when the WORKFLOW denies a transition, the service does not override it")
State.workflow_allows = True


# ============================================================
# Permissions are re-checked at EXECUTE, not trusted from propose
# ============================================================
State.docs.clear()
State.docs[("UCC Monitoring Finding", "F-1")] = FakeDoc(
	{"doctype": "UCC Monitoring Finding", "name": "F-1", "status": "Open"})
suppression = service.propose("suppress_monitoring_finding", "Suppress F-1",
	payload={"suppression_reason": "Agreed exception, reviewed 2026-07-31."},
	target_record="F-1")
name = suppression["action_request"]
service.transition(name, "Submit for Approval")
service.transition(name, "Approve")

# Access is revoked in the window between approval and execution.
State.write_denied.add(("UCC Monitoring Finding", "F-1"))
try:
	service.execute(name)
	report(False, "execution should re-check write permission on the target")
except FrappePermissionError:
	report(True, "PERMISSIONS RE-CHECKED AT EXECUTE -- access revoked after approval stops it")
report(State.docs[("UCC Monitoring Finding", "F-1")]["status"] == "Open",
	"...and the target record was NOT modified")

State.write_denied.clear()
done = service.execute(name)
report(done["ok"], "with permission restored, it executes")
report(State.docs[("UCC Monitoring Finding", "F-1")]["status"] == "Suppressed", "the real write happened")
report(bool(State.docs[("UCC AI Action Request", name)]["rollback_hint"]),
	"a rollback hint is recorded at execution time, while the information is still to hand")

# A suppression with no reason must be refused by the executor itself.
State.docs[("UCC Monitoring Finding", "F-2")] = FakeDoc(
	{"doctype": "UCC Monitoring Finding", "name": "F-2", "status": "Open"})
no_reason = service.propose("suppress_monitoring_finding", "Suppress F-2", payload={}, target_record="F-2")
service.transition(no_reason["action_request"], "Submit for Approval")
service.transition(no_reason["action_request"], "Approve")
outcome = service.execute(no_reason["action_request"])
report(not outcome["ok"], "suppressing WITHOUT a recorded reason fails")
report(State.docs[("UCC Monitoring Finding", "F-2")]["status"] == "Open", "...and changes nothing")


# ============================================================
# Proposing against an unreadable record fails early
# ============================================================
State.docs[("UCC Monitoring Finding", "F-3")] = FakeDoc(
	{"doctype": "UCC Monitoring Finding", "name": "F-3", "status": "Open"})
State.read_denied.add(("UCC Monitoring Finding", "F-3"))
try:
	service.propose("suppress_monitoring_finding", "Suppress F-3",
		payload={"suppression_reason": "x"}, target_record="F-3")
	report(False, "proposing against an unreadable record should fail")
except FrappePermissionError:
	report(True, "a proposal against a record the proposer cannot READ never reaches an approver's queue")
State.read_denied.clear()


# ============================================================
# The workflow fixture must match what the service expects
# ============================================================
fixture = json.loads((ROOT / "ucc_intelligence/ucc_intelligence/fixtures/workflow.json").read_text(encoding="utf-8"))[0]
report(fixture["document_type"] == service.DOCTYPE, "the workflow is bound to the Action Request DocType")
report(fixture["workflow_state_field"] == "workflow_state", "it drives the field the service reads")
states = {s["state"] for s in fixture["states"]}
for required in (service.STATE_DRAFT, service.STATE_PENDING, service.STATE_APPROVED, service.STATE_EXECUTED):
	report(required in states, "the workflow defines the %r state the service uses" % required)
approve = next(t for t in fixture["transitions"] if t["action"] == "Approve")
report(approve["allow_self_approval"] == 0,
	"SELF-APPROVAL IS OFF for Approve -- the proposer cannot approve their own request")
execute_transition = next(t for t in fixture["transitions"] if t["action"] == "Execute")
report(execute_transition["state"] == service.STATE_APPROVED,
	"Execute is reachable ONLY from Approved -- there is no path that skips a human")
report(not any(t["next_state"] == service.STATE_EXECUTED and t["state"] != service.STATE_APPROVED
	for t in fixture["transitions"]), "no other transition reaches Executed")

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
