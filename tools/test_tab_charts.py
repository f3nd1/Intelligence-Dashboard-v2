#!/usr/bin/env python3
"""Self-check for analytics/tab_charts.py -- the per-tab Insights charts.

    python3 tools/test_tab_charts.py

WHAT THIS PROVES
The structural checks in test_end_to_end.py confirm the permission calls are
WRITTEN. This runs the module against a fake Frappe and confirms they WORK:
that a chart you cannot read is never listed, never storable, never returned
from storage, and never executed -- and that removing one always works even
then, or a revoked chart would be stuck on your tab forever.

The fake is deliberately strict. `get_list` applies the readable set and
`get_all` does not exist at all, so any drift towards the permission-blind
call fails here rather than on a bench.
"""
import json
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


# --- the fake site ----------------------------------------------------------
class PermissionError_(Exception):
	pass


class ValidationError_(Exception):
	pass


class DoesNotExistError_(Exception):
	pass


class State:
	charts = {}        # name -> title, everything that exists in Insights
	readable = set()   # of those, what THIS user may read
	criteria = {}      # criterion -> visible?
	tabs = {}          # "<criterion>::<tab>" -> the shared config record
	may_write = True   # write permission on UCC Analytics Tab
	audit = []         # UCC Analytics Tab Change records, newest last
	audit_fails = False
	rows = [{"status": "Open", "count": 3}]
	executed = []


class FakeDoc:
	def __init__(self, name):
		self.name = name
		self.title = State.charts[name]

	def get(self, key):
		return getattr(self, key, None)

	def check_permission(self, ptype):
		if self.name not in State.readable:
			raise PermissionError_("Not permitted to read %s" % self.name)

	def execute(self, page_size=None):
		State.executed.append(self.name)
		return {"rows": list(State.rows)}


class FakeAudit:
	"""One UCC Analytics Tab Change. insert() is the only way one exists, and
	it ignores permissions on purpose -- see analytics/tab_audit.py."""

	def __init__(self):
		self.data = {}

	def update(self, values):
		self.data.update(values)

	def insert(self, ignore_permissions=False):
		if State.audit_fails:
			raise RuntimeError("audit backend unavailable")
		assert ignore_permissions, "an audit record the actor could refuse to write is not an audit record"
		State.audit.append(dict(self.data))


class FakeTab:
	"""One UCC Analytics Tab record. save()/insert() re-check write permission
	the way a real Document does, so a missing _require_edit() still fails."""

	def __init__(self, name=None):
		self.name = name
		self.data = dict(State.tabs.get(name) or {})

	def get(self, key):
		return self.data.get(key)

	def update(self, values):
		self.data.update(values)

	def _write(self):
		if not State.may_write:
			raise PermissionError_("No write permission on UCC Analytics Tab")
		name = self.name or "%s::%s" % (self.data.get("criterion"), self.data.get("tab"))
		self.name = name
		State.tabs[name] = dict(self.data)

	save = _write
	insert = _write


def fake_get_list(doctype, filters=None, fields=None, order_by=None, limit_page_length=None):
	names = sorted(State.readable)
	wanted = (filters or {}).get("name")
	if wanted:
		names = [n for n in names if n in set(wanted[1])]
	like = (filters or {}).get("title")
	if like:
		term = like[1].strip("%").lower()
		names = [n for n in names if term in State.charts[n].lower()]
	return [{"name": n, "title": State.charts[n]} for n in names[: (limit_page_length or 20)]]


def fake_get_doc(doctype, name):
	if doctype == "UCC Analytics Tab":
		if name not in State.tabs:
			raise DoesNotExistError_(name)
		return FakeTab(name)
	if name not in State.charts:
		raise DoesNotExistError_(name)
	return FakeDoc(name)


def fake_new_doc(doctype):
	if doctype == "UCC Analytics Tab Change":
		return FakeAudit()
	assert doctype == "UCC Analytics Tab"
	return FakeTab()


def fake_get_all(doctype, filters=None, fields=None, order_by=None,
		limit_page_length=None, ignore_permissions=False):
	assert doctype == "UCC Analytics Tab Change"
	rows = [dict(entry) for entry in State.audit
		if entry["criterion"] == (filters or {}).get("criterion")
		and entry["tab"] == (filters or {}).get("tab")]
	return list(reversed(rows))[: (limit_page_length or 50)]


def install_fake_frappe():
	frappe = types.ModuleType("frappe")
	frappe._ = lambda text: types.SimpleNamespace(format=lambda *a, **k: text, __str__=lambda s: text)
	frappe._ = lambda text: text
	frappe.PermissionError = PermissionError_
	frappe.ValidationError = ValidationError_
	frappe.DoesNotExistError = DoesNotExistError_
	frappe.get_list = fake_get_list
	frappe.get_doc = fake_get_doc

	def throw(message, exc=None):
		raise (exc or ValidationError_)(message)

	frappe.throw = throw
	frappe.get_doc = fake_get_doc
	frappe.new_doc = fake_new_doc
	frappe.has_permission = lambda doctype, ptype=None: (
		State.may_write if doctype == "UCC Analytics Tab" else True)

	def exists(doctype, name=None):
		if doctype == "DocType":
			return name in ("Insights Query v3", "UCC Analytics Tab")
		if doctype == "UCC Analytics Tab":
			return name in State.tabs
		return name in State.charts

	frappe.db = types.SimpleNamespace(exists=exists)
	frappe.get_all = fake_get_all
	frappe.log_error = lambda **kwargs: None
	frappe.get_traceback = lambda: ""
	frappe.utils = types.SimpleNamespace(now=lambda: "2026-08-02 09:30:00")
	frappe.logger = lambda *a, **k: types.SimpleNamespace(
		info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None)
	frappe.session = types.SimpleNamespace(user="tester@ucc")
	sys.modules["frappe"] = frappe
	model = types.ModuleType("frappe.model")
	document = types.ModuleType("frappe.model.document")
	document.Document = type("Document", (), {})
	sys.modules["frappe.model"] = model
	sys.modules["frappe.model.document"] = document
	return frappe


install_fake_frappe()
from ucc_intelligence.analytics import tab_charts  # noqa: E402
from ucc_intelligence.permissions import access  # noqa: E402

# The criterion gate reads access.build_response(); stub it rather than build a
# whole UCC Dashboard Access fixture -- access.py has its own tests.
access.build_response = lambda: {"criteria": dict(State.criteria)}


def reset():
	State.charts = {"q-open": "Open Actions", "q-secret": "Payroll by Band", "q-agents": "Agents"}
	State.readable = {"q-open", "q-agents"}
	State.criteria = {key: True for key in access.CRITERION_KEYS}
	State.tabs = {}
	State.may_write = True
	State.audit = []
	State.audit_fails = False
	State.executed = []


def source_of(function_name):
	"""One function's source text, from the real module."""
	text = open(ROOT / "ucc_intelligence" / "ucc_intelligence" / "analytics" / "tab_charts.py",
		encoding="utf-8").read()
	start = text.index("def %s(" % function_name)
	rest = text[start + 1:]
	end = rest.index("\ndef ") if "\ndef " in rest else len(rest)
	return rest[:end]


def raises(exc, fn, *args):
	try:
		fn(*args)
	except exc:
		return True
	except Exception:
		return False
	return False


# --- the picker only offers what you can read -------------------------------
reset()
offered = {row["chart"] for row in tab_charts.search()["charts"]}
report(offered == {"q-open", "q-agents"},
	"the picker lists only charts this user can read (%s)" % sorted(offered))
report("q-secret" not in offered, "a chart the user cannot read is never offered")
report({row["chart"] for row in tab_charts.search("agent")["charts"]} == {"q-agents"},
	"the search term filters by title")

# --- per tab, and persisted -------------------------------------------------
reset()
tab_charts.add("criterion_3", "overview", "q-open")
tab_charts.add("criterion_3", "3.1.1", "q-agents")
report([c["chart"] for c in tab_charts.get_tab("criterion_3", "overview")["charts"]] == ["q-open"],
	"a chart added to one tab appears on that tab")
report([c["chart"] for c in tab_charts.get_tab("criterion_3", "3.1.1")["charts"]] == ["q-agents"],
	"and NOT on another tab of the same criterion")
report(tab_charts.get_tab("criterion_6", "overview")["charts"] == [],
	"and not on another criterion")
report(len(State.tabs) == 2 and all(json.loads(v["charts"]) for v in State.tabs.values()),
	"the selection is written to ONE shared record per tab")

# A fresh module-level cache would hide a broken read; go back through get.
report([c["chart"] for c in tab_charts.get_tab("criterion_3", "overview")["charts"]] == ["q-open"],
	"the selection survives a re-read -- it is stored, not held in memory")
report(tab_charts.get_tab("criterion_3", "overview")["charts"][0]["title"] == "Open Actions",
	"the title is resolved live, so a renamed chart does not show a stale name")

# --- adding is permission-checked ------------------------------------------
reset()
report(raises(PermissionError_, tab_charts.add, "criterion_3", "overview", "q-secret"),
	"a chart the user cannot read CANNOT be added")
report(State.tabs == {}, "and nothing is written when the add is refused")
report(raises(PermissionError_, tab_charts.add, "criterion_3", "overview", "q-nonexistent"),
	"an id that does not exist is refused the same way, so errors leak no ids")

# --- a stored id is a preference, never a grant -----------------------------
reset()
tab_charts.add("criterion_3", "overview", "q-open")
State.readable.discard("q-open")          # access revoked after it was added
report(tab_charts.get_tab("criterion_3", "overview")["charts"] == [],
	"a chart you may no longer read stops appearing, even though it is still stored")
report(tab_charts.chart_data("q-open")["status"] == "permission_denied",
	"and executing it is refused")
report(State.executed == [], "the query never ran")
# ...and you can still get rid of it, or it would be stuck there forever.
tab_charts.remove("criterion_3", "overview", "q-open")
report(json.loads(State.tabs[tab_charts._key("criterion_3", "overview")]["charts"]) == [],
	"removing works even for a chart you can no longer read")

# --- the criterion gate -----------------------------------------------------
reset()
State.criteria["criterion_5"] = False
report(raises(PermissionError_, tab_charts.get_tab, "criterion_5", "overview"),
	"a criterion hidden by ucc_dashboard_access cannot be read")
report(raises(PermissionError_, tab_charts.add, "criterion_5", "overview", "q-open"),
	"and cannot be added to")
report(tab_charts.get_tab("criterion_3", "overview")["ok"] is True,
	"a visible criterion still works")

# --- input validation -------------------------------------------------------
reset()
report(raises(ValidationError_, tab_charts.get_tab, "criterion_99", "overview"),
	"an invented criterion is rejected")
report(raises(ValidationError_, tab_charts.get_tab, "criterion_3", "../../etc/passwd"),
	"a tab key cannot contain path characters -- it becomes part of a stored key")
report(raises(ValidationError_, tab_charts.get_tab, "criterion_3", "x" * 60),
	"an over-long tab key is rejected")

# --- bounded ----------------------------------------------------------------
reset()
State.charts = {"q-%d" % i: "Chart %d" % i for i in range(20)}
State.readable = set(State.charts)
for index in range(tab_charts.MAX_PER_TAB):
	tab_charts.add("criterion_3", "overview", "q-%d" % index)
report(len(tab_charts.get_tab("criterion_3", "overview")["charts"]) == tab_charts.MAX_PER_TAB,
	"a tab holds up to MAX_PER_TAB charts (%d)" % tab_charts.MAX_PER_TAB)
report(raises(Exception, tab_charts.add, "criterion_3", "overview", "q-19"),
	"and refuses the next one rather than growing without limit")

# --- adding the same chart twice is not an error ----------------------------
reset()
tab_charts.add("criterion_3", "overview", "q-open")
result = tab_charts.add("criterion_3", "overview", "q-open")
report([c["chart"] for c in result["charts"]] == ["q-open"],
	"adding a chart already on the tab is a no-op, not a duplicate")

# --- execution --------------------------------------------------------------
reset()
data = tab_charts.chart_data("q-open")
report(data["status"] == "available" and data["series"] == [{"label": "Open", "value": 3}],
	"an authorised chart executes and returns a label/value series")
report(State.executed == ["q-open"], "exactly one execute, for the chart asked for")
report(tab_charts.chart_data("q-missing")["status"] == "unavailable",
	"a chart deleted from Insights reports unavailable rather than raising")

# --- corrupt stored value ---------------------------------------------------
reset()
State.tabs[tab_charts._key("criterion_3", "overview")] = {"charts": "{not json", "intro": "", "hidden_questions": "[]"}
report(tab_charts.get_tab("criterion_3", "overview")["charts"] == [],
	"a corrupt stored value costs the layout, not the page")

# --- the ORIGINAL stored shape still reads -----------------------------------
# The first version stored a bare list of chart ids, before sizes, intros and
# question choices existed. Anyone who used the feature before this round has
# one of those, and it must not read as an empty tab.
reset()
State.tabs[tab_charts._key("criterion_3", "overview")] = {"charts": json.dumps(["q-open", "q-agents"]), "intro": "", "hidden_questions": "[]"}
legacy = tab_charts.get_tab("criterion_3", "overview")
report([c["chart"] for c in legacy["charts"]] == ["q-open", "q-agents"],
	"a tab stored in the original list-of-ids shape still loads its charts")
report(all(c["span"] == tab_charts.DEFAULT_SPAN for c in legacy["charts"]),
	"...at the default width, rather than being discarded for having none")

# --- card size (#5) ----------------------------------------------------------
reset()
tab_charts.add("criterion_3", "overview", "q-open")
report(tab_charts.get_tab("criterion_3", "overview")["charts"][0]["span"] == tab_charts.DEFAULT_SPAN,
	"a new card starts at the default width")
sized = tab_charts.set_size("criterion_3", "overview", "q-open", 12)
report(sized["charts"][0]["span"] == 12, "a dragged card stores the column span it landed on")
report(tab_charts.get_tab("criterion_3", "overview")["charts"][0]["span"] == 12, "and it persists")
report(tab_charts.set_size("criterion_3", "overview", "q-open", "4")["charts"][0]["span"] == 4,
	"a span arriving as a string from the browser is accepted")
for bad in ("enormous", 0, 13, -3, None):
	report(raises(ValidationError_, tab_charts.set_size, "criterion_3", "overview", "q-open", bad),
		"a width off the 12-column grid is rejected (%r)" % (bad,))
report(tab_charts.get_tab("criterion_3", "overview")["charts"][0]["span"] == 4,
	"...and none of them changed the stored width")

# The four old size NAMES are still readable, because tabs configured before
# drag-resize hold them.
reset()
State.tabs[tab_charts._key("criterion_3", "overview")] = {
	"charts": json.dumps([{"chart": "q-open", "size": "large"}, {"chart": "q-agents", "size": "small"}]),
	"intro": "", "hidden_questions": "[]"}
spans = [c["span"] for c in tab_charts.get_tab("criterion_3", "overview")["charts"]]
report(spans == [9, 3], "a card stored under an old size name still knows its width (%s)" % spans)

# --- the tab intro (#4) ------------------------------------------------------
reset()
report(tab_charts.get_tab("criterion_3", "overview")["intro"] == "",
	"a tab has NO intro by default -- no forced default text")
tab_charts.set_intro("criterion_3", "overview", "**Scope.** Agents only.")
report(tab_charts.get_tab("criterion_3", "overview")["intro"] == "**Scope.** Agents only.",
	"an intro is stored as written, markdown and all")
report(tab_charts.get_tab("criterion_3", "3.1.1")["intro"] == "",
	"and it is per tab, not per criterion")
tab_charts.set_intro("criterion_3", "overview", "x" * (tab_charts.MAX_INTRO_LENGTH + 500))
report(len(tab_charts.get_tab("criterion_3", "overview")["intro"]) == tab_charts.MAX_INTRO_LENGTH,
	"an over-long intro is truncated, not stored whole")

# --- the intro shares the chart record, it does not replace it ---------------
reset()
tab_charts.add("criterion_3", "overview", "q-open")
tab_charts.set_intro("criterion_3", "overview", "Notes.")
both = tab_charts.get_tab("criterion_3", "overview")
report(both["intro"] == "Notes." and [c["chart"] for c in both["charts"]] == ["q-open"],
	"intro and charts live in ONE stored record -- writing one does not drop the other")
report(len(State.tabs) == 1, "and it really is one record, not a second store alongside")

# --- hidden management questions (#6) ---------------------------------------
reset()
report(tab_charts.get_tab("criterion_3", "overview")["questions"]["hidden"] == [],
	"nothing is hidden by default, so every criterion that answers questions keeps doing so")
tab_charts.set_question("criterion_3", "overview", "metric-7", False)
report(tab_charts.get_tab("criterion_3", "overview")["questions"]["hidden"] == ["metric-7"],
	"hiding a question stores WHICH question, and nothing else")
tab_charts.set_question("criterion_3", "overview", "metric-7", False)
report(tab_charts.get_tab("criterion_3", "overview")["questions"]["hidden"] == ["metric-7"],
	"hiding it twice does not duplicate it")
tab_charts.set_question("criterion_3", "overview", "metric-7", True)
report(tab_charts.get_tab("criterion_3", "overview")["questions"]["hidden"] == [],
	"showing it again removes it from the hidden list")
report(tab_charts.get_tab("criterion_3", "3.1.1")["questions"]["hidden"] == [],
	"hiding is per tab")
report(raises(ValidationError_, tab_charts.set_question, "criterion_3", "overview", "", False),
	"an empty question id is rejected")
report(raises(ValidationError_, tab_charts.set_question, "criterion_3", "overview", "x" * 400, False),
	"and an absurdly long one is too")

# --- the table view shares the chart's ONE execute ---------------------------
reset()
State.rows = [{"status": "Open", "count": 3}, {"status": "Closed", "count": 5}]
data = tab_charts.chart_data("q-open")
report(data["columns"] == ["status", "count"], "the table gets the query's own columns")
report(data["rows"] == State.rows, "and its own rows, unmodified")
report([item["value"] for item in data["series"]] == [3, 5],
	"the diagram series comes from those same rows")
report(len(State.executed) == 1,
	"ONE execute feeds both views -- the table cannot disagree with the bar")

# --- the criterion gate covers the new endpoints too -------------------------
reset()
State.criteria["criterion_5"] = False
for call in [
	lambda: tab_charts.set_intro("criterion_5", "overview", "x"),
	lambda: tab_charts.set_size("criterion_5", "overview", "q-open", "full"),
	lambda: tab_charts.set_question("criterion_5", "overview", "m", False),
]:
	report(raises(PermissionError_, call), "a hidden criterion refuses the new write endpoints too")

# --- INSTITUTION-WIDE, NOT PER USER -----------------------------------------
# The whole point of the 2026-08-02 change: Sophia is EduTrust evidence, not a
# personal workspace. What one person configures is what the auditor sees.
reset()
tab_charts.add("criterion_3", "overview", "q-open")
tab_charts.set_intro("criterion_3", "overview", "Agents only.")
tab_charts.set_question("criterion_3", "overview", "metric-7", False)
report(list(State.tabs) == ["criterion_3::overview"],
	"charts, intro and hidden questions all land in ONE record, named <criterion>::<tab>")
record = State.tabs["criterion_3::overview"]
report(sorted(k for k in record if k in ("charts", "intro", "hidden_questions"))
	== ["charts", "hidden_questions", "intro"],
	"and in the three fields they are documented to be in")
report(record["criterion"] == "criterion_3" and record["tab"] == "overview",
	"the record carries its own criterion and tab, so it is readable in Desk")

# Nothing is keyed by user. A second person reading the same tab gets the same
# thing -- which is only provable by there being no user in the key at all.
report("::" in tab_charts._key("criterion_3", "overview")
	and "tester@ucc" not in tab_charts._key("criterion_3", "overview"),
	"the storage key contains NO user -- one tab, one configuration, everyone")
report("frappe.defaults" not in open(
	ROOT / "ucc_intelligence" / "ucc_intelligence" / "analytics" / "tab_charts.py",
	encoding="utf-8").read().split("LEGACY_DEFAULTS_PREFIX")[-1],
	"the per-user store is not written to any more")

# --- ONLY AN EDITOR MAY CHANGE IT -------------------------------------------
reset()
tab_charts.add("criterion_3", "overview", "q-open")
tab_charts.set_intro("criterion_3", "overview", "Set by an editor.")
State.may_write = False
for call, what in [
	(lambda: tab_charts.add("criterion_3", "overview", "q-agents"), "add a chart"),
	(lambda: tab_charts.remove("criterion_3", "overview", "q-open"), "remove a chart"),
	(lambda: tab_charts.set_size("criterion_3", "overview", "q-open", "full"), "resize a chart"),
	(lambda: tab_charts.set_intro("criterion_3", "overview", "hijacked"), "edit the intro"),
	(lambda: tab_charts.set_question("criterion_3", "overview", "m", False), "hide a question"),
]:
	report(raises(PermissionError_, call), "a viewer without write permission cannot %s" % what)

# Each endpoint must ask BEFORE it writes, not rely on the DocType refusing.
# The loop above cannot tell those apart -- both raise PermissionError -- so
# the explicit gate is asserted per endpoint by name. Removing one from
# set_intro() passed the loop and failed here, which is why this exists.
for endpoint in ("add", "remove", "set_size", "set_intro", "set_question"):
	body = source_of(endpoint)
	report("_require_edit()" in body, "%s() asks permission before touching anything" % endpoint,
		)
	report(body.index("_require_edit()") < (body.index("_store(") if "_store(" in body else len(body)),
		"...and asks BEFORE it writes")

viewer = tab_charts.get_tab("criterion_3", "overview")
report(viewer["can_edit"] is False, "and the response tells the page not to show the controls")
report([c["chart"] for c in viewer["charts"]] == ["q-open"],
	"but they still SEE the shared configuration")
report(viewer["intro"] == "Set by an editor.", "including the intro someone else wrote")
report(State.tabs["criterion_3::overview"]["intro"] == "Set by an editor.",
	"and nothing they attempted was written")

State.may_write = True
report(tab_charts.get_tab("criterion_3", "overview")["can_edit"] is True,
	"an editor is told they may edit")

# The gate is the DocType's own write permission, so widening it is a Desk
# change. Asserted here rather than described, because "uses the existing
# pattern" is a claim about which call is made.
source = open(ROOT / "ucc_intelligence" / "ucc_intelligence" / "analytics" / "tab_charts.py",
	encoding="utf-8").read()
report('frappe.has_permission(CONFIG_DOCTYPE, "write")' in source,
	"the edit gate is write permission on the config DocType, not a hardcoded role")
store_code = "\n".join(line for line in source.split("def _store(")[1].split("def readable(")[0].splitlines()
	if not line.strip().startswith("#") and "\"\"\"" not in line and "ignore_permissions is NOT" not in line)
report("ignore_permissions" not in store_code,
	"writes go through the DocType's own permission check as well -- the gate holds twice")

# --- reads stay open, writes do not -----------------------------------------
# A shared configuration nobody can read is not shared. The read is documented
# as ignore_permissions for exactly the reason access.py already does it.
reset()
tab_charts.add("criterion_3", "overview", "q-open")
State.may_write = False
report(tab_charts.get_tab("criterion_3", "overview")["charts"] != [],
	"a viewer can read the shared configuration")
# ...but sharing the CONFIG never shares the DATA.
State.readable.discard("q-open")
report(tab_charts.get_tab("criterion_3", "overview")["charts"] == [],
	"a chart on the shared tab still disappears for someone who may not read its query")
report(tab_charts.chart_data("q-open")["status"] == "permission_denied",
	"and executing it is still refused, per user")

# --- ORDER (#2) --------------------------------------------------------------
# The stored list IS the display order, so a reorder rewrites it rather than
# adding a second field that could disagree.
reset()
State.charts["q-third"] = "Third"
State.readable.add("q-third")
for chart in ("q-open", "q-agents", "q-third"):
	tab_charts.add("criterion_3", "overview", chart)
report([c["chart"] for c in tab_charts.get_tab("criterion_3", "overview")["charts"]]
	== ["q-open", "q-agents", "q-third"], "charts come back in the order they were added")
moved = tab_charts.set_order("criterion_3", "overview", ["q-third", "q-open", "q-agents"])
report([c["chart"] for c in moved["charts"]] == ["q-third", "q-open", "q-agents"],
	"a reorder rewrites the stored order")
report([c["chart"] for c in tab_charts.get_tab("criterion_3", "overview")["charts"]]
	== ["q-third", "q-open", "q-agents"], "and it persists")

# A reorder that omits a card must not delete it -- a drag is not a delete.
kept = tab_charts.set_order("criterion_3", "overview", ["q-agents"])
report(sorted(c["chart"] for c in kept["charts"]) == ["q-agents", "q-open", "q-third"],
	"a card left out of the order keeps its place instead of vanishing")
report(kept["charts"][0]["chart"] == "q-agents", "and the ones that were named lead")
report(tab_charts.set_order("criterion_3", "overview", ["q-open", "not-on-this-tab"]),
	"an unknown id in the order is ignored rather than raising")
report(raises(ValidationError_, tab_charts.set_order, "criterion_3", "overview", "not a list"),
	"a malformed order is rejected")
report([c["chart"] for c in tab_charts.set_order(
	"criterion_3", "overview", json.dumps(["q-third", "q-open", "q-agents"]))["charts"]]
	== ["q-third", "q-open", "q-agents"],
	"an order arriving as a JSON string from the browser is accepted")

# --- AUDIT TRAIL (#1) --------------------------------------------------------
# These tabs feed EduTrust evidence, so every change records who and when.
reset()
tab_charts.add("criterion_3", "overview", "q-open")
tab_charts.set_size("criterion_3", "overview", "q-open", 9)
tab_charts.set_intro("criterion_3", "overview", "Scope note.")
tab_charts.set_question("criterion_3", "overview", "metric-7", False)
tab_charts.add("criterion_3", "overview", "q-agents")
tab_charts.set_order("criterion_3", "overview", ["q-agents", "q-open"])
tab_charts.remove("criterion_3", "overview", "q-open")

actions = [entry["action"] for entry in State.audit]
report(actions == ["chart_added", "chart_resized", "intro_edited", "question_hidden",
	"chart_added", "charts_reordered", "chart_removed"],
	"every kind of change is recorded, in order (%s)" % actions)
report(all(entry["changed_by"] == "tester@ucc" and entry["changed_at"] for entry in State.audit),
	"each one records who and when")
report(all(entry["criterion"] == "criterion_3" and entry["tab"] == "overview" for entry in State.audit),
	"and which tab it was")
resize = next(e for e in State.audit if e["action"] == "chart_resized")
report(resize["before_value"] == "6" and resize["after_value"] == "9",
	"a resize records the before and after width (%s -> %s)" % (resize["before_value"], resize["after_value"]))
report("6 to 9" in resize["summary"], "and says so in words: %r" % resize["summary"])
intro = next(e for e in State.audit if e["action"] == "intro_edited")
report(intro["before_value"] == "" and intro["after_value"] == "Scope note.",
	"an intro edit records the text before and after")
report(intro["summary"] == "Added the tab introduction",
	"and distinguishes adding from editing: %r" % intro["summary"])
order = next(e for e in State.audit if e["action"] == "charts_reordered")
report("q-open" in order["before_value"] and "q-agents" in order["after_value"],
	"a reorder records both orders")

# A change that changes nothing is not a change.
before_count = len(State.audit)
tab_charts.set_size("criterion_3", "overview", "q-agents", 6)
tab_charts.set_intro("criterion_3", "overview", "Scope note.")
tab_charts.remove("criterion_3", "overview", "never-was-here")
report(len(State.audit) == before_count,
	"a no-op write records nothing -- the trail is changes, not requests")

# The audit trail holds configuration, never figures.
report(not any("62" in str(entry) or "96.77" in str(entry) for entry in State.audit),
	"no institutional data reaches the audit trail")

# An audit write that fails must not cost the user their change.
reset()
State.audit_fails = True
tab_charts.add("criterion_3", "overview", "q-open")
report([c["chart"] for c in tab_charts.get_tab("criterion_3", "overview")["charts"]] == ["q-open"],
	"the change still lands when the audit write fails")
State.audit_fails = False

# ...and reading the history back is validated like any other read.
reset()
tab_charts.add("criterion_3", "overview", "q-open")
report(len(tab_charts.history("criterion_3", "overview")["changes"]) == 1,
	"the history reads back")
State.criteria["criterion_5"] = False
report(raises(PermissionError_, tab_charts.history, "criterion_5", "overview"),
	"a criterion this user cannot see has no readable history either")

print(("PASS" if all(checks) else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
sys.exit(0 if all(checks) else 1)
