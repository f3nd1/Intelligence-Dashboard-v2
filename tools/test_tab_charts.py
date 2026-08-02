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
	messages = []      # anything frappe.throw() put in front of the user
	rows = [{"status": "Open", "count": 3}]
	doctypes = {"Insights Query v3", "UCC Analytics Tab"}   # Insights Chart v3 absent by default
	insights_charts = []   # Insights Chart v3 records this user may read
	palette = None         # UCC Intelligence Settings.chart_palette
	executed = []
	query_workbook = {}    # query name -> its Insights Workbook, "" for none
	workbook_titles = {}   # workbook name -> title, absent = unreadable record
	dashboards = {}          # Insights Dashboard v3 name -> title
	readable_dashboards = set()   # of those, what THIS user may read
	dashboard_workbook = {}       # dashboard name -> its Insights Workbook
	dashboard_charts = {}         # dashboard name -> its linked_charts rows
	drilldowns = {}               # query name -> what drilldown.resolve returns
	unreadable_charts = set()     # Insights Chart v3 records this user may NOT read


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
	if doctype == "Insights Chart v3":
		rows = []
		for row in State.insights_charts:
			# A chart record this user cannot read is simply not returned --
			# that is what real get_list does, and it is the hop that keeps a
			# dashboard from listing a chart someone may not open.
			if row["name"] in State.unreadable_charts:
				continue
			for key, value in (filters or {}).items():
				if isinstance(value, list) and len(value) == 2 and value[0] == "in":
					if row.get(key) not in value[1]:
						break
				elif row.get(key) != value:
					break
			else:
				rows.append(dict(row))
		return rows[: (limit_page_length or 20)] if limit_page_length else rows
	# Workbook TITLES. Only the ones asked for, and only ones that exist -- a
	# workbook record this user cannot read simply is not returned, which is
	# what makes the id-as-label fallback reachable.
	if doctype == "Insights Dashboard v3":
		wanted = (filters or {}).get("name")
		names = [n for n in sorted(State.dashboards) if n in State.readable_dashboards]
		if wanted:
			names = [n for n in names if n == wanted]
		like = (filters or {}).get("title")
		if like:
			term = like[1].strip("%").lower()
			names = [n for n in names if term in State.dashboards[n].lower()]
		return [{"name": n, "title": State.dashboards[n],
				"workbook": State.dashboard_workbook.get(n, "")}
			for n in names[: (limit_page_length or 20)]]
	if doctype == "Insights Workbook":
		wanted = set(((filters or {}).get("name") or ["in", []])[1])
		return [{"name": name, "title": title}
			for name, title in sorted(State.workbook_titles.items()) if name in wanted]
	names = sorted(State.readable)
	wanted = (filters or {}).get("name")
	if wanted:
		names = [n for n in names if n in set(wanted[1])]
	like = (filters or {}).get("title")
	if like:
		term = like[1].strip("%").lower()
		names = [n for n in names if term in State.charts[n].lower()]
	return [{"name": n, "title": State.charts[n],
			"workbook": State.query_workbook.get(n, "")}
		for n in names[: (limit_page_length or 20)]]


class FakeDashboard:
	"""Enough of an Insights Dashboard v3 to exercise the four permission hops:
	it refuses check_permission when unreadable, and carries linked_charts."""

	def __init__(self, name):
		self.name = name

	def check_permission(self, ptype="read"):
		if self.name not in State.readable_dashboards:
			raise PermissionError_("no permission")

	def get(self, field):
		if field != "linked_charts":
			return None
		return [{"chart": c} for c in State.dashboard_charts.get(self.name, [])]


def fake_get_doc(doctype, name):
	if doctype == "Insights Dashboard v3":
		if name not in State.dashboards:
			raise DoesNotExistError_(name)
		return FakeDashboard(name)
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
		# Real frappe.throw() puts the message in front of the user BEFORE it
		# raises, and the message log reaches the browser whether or not the
		# exception is later caught. Modelling only the raise is what let the
		# "Audit records cannot be edited." regression through: tab_audit
		# swallowed the exception, so the test saw nothing, and Felix saw an
		# error on every successful edit.
		State.messages.append(str(message))
		raise (exc or ValidationError_)(message)

	frappe.throw = throw
	frappe.get_doc = fake_get_doc
	frappe.new_doc = fake_new_doc
	frappe.has_permission = lambda doctype, ptype=None: (
		State.may_write if doctype == "UCC Analytics Tab" else True)

	def exists(doctype, name=None):
		if doctype == "DocType":
			return name in ("Insights Query v3", "UCC Analytics Tab",
				"Insights Chart v3", "Insights Dashboard v3") and name in State.doctypes
		if doctype == "UCC Analytics Tab":
			return name in State.tabs
		return name in State.charts

	frappe.db = types.SimpleNamespace(
		exists=exists,
		get_single_value=lambda doctype, field: State.palette)
	frappe.get_all = fake_get_all
	frappe.log_error = lambda **kwargs: None
	frappe.get_traceback = lambda: ""
	frappe.utils = types.SimpleNamespace(
		now=lambda: "2026-08-02 09:30:00",
		cstr=lambda v: "" if v is None else str(v))
	frappe._dict = dict
	frappe.logger = lambda *a, **k: types.SimpleNamespace(
		info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None)
	frappe.session = types.SimpleNamespace(user="tester@ucc")
	sys.modules["frappe"] = frappe
	model = types.ModuleType("frappe.model")
	document = types.ModuleType("frappe.model.document")

	class Flags(dict):
		__getattr__ = dict.get
		__setattr__ = dict.__setitem__

	class Document:
		def __init__(self, *a, **k):
			self.flags = Flags()

	document.Document = Document
	sys.modules["frappe.model"] = model
	sys.modules["frappe.model.document"] = document

	# drilldown.py has its own 30-check suite; stubbed here so THIS test
	# exercises the chain that reaches it, not the resolution inside it.
	drill = types.ModuleType("ucc_intelligence.analytics.drilldown")
	drill.resolve = lambda chart: State.drilldowns.get(chart,
		{"status": "unsupported", "doctype": "", "columns": [],
			"message": "Not drillable."})
	sys.modules["ucc_intelligence.analytics.drilldown"] = drill
	return frappe


install_fake_frappe()
from ucc_intelligence.analytics import tab_charts  # noqa: E402
from ucc_intelligence.permissions import access  # noqa: E402
from ucc_intelligence.sophia.doctype.ucc_analytics_tab_change import (  # noqa: E402
	ucc_analytics_tab_change as audit_controller)


class RealAudit(audit_controller.UCCAnalyticsTabChange):
	"""FakeAudit, but running the REAL controller through the REAL hook order.

	Frappe's insert() is before_insert -> write the row -> on_update, and
	on_update fires for inserts as well as updates. Stubbing insert() without
	those hooks is what hid the regression: the controller's own guard was
	firing against the insert that created the record.
	"""

	def __init__(self):
		super().__init__()
		self.data = {}

	def update(self, values):
		self.data.update(values)

	def insert(self, ignore_permissions=False):
		if State.audit_fails:
			raise RuntimeError("audit backend unavailable")
		assert ignore_permissions, "an audit record the actor could refuse to write is not an audit record"
		self.before_insert()
		State.audit.append(dict(self.data))
		self.on_update()


FakeAudit = RealAudit

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
	State.messages = []
	State.doctypes = {"Insights Query v3", "UCC Analytics Tab"}
	State.insights_charts = []
	State.palette = None
	State.executed = []
	State.query_workbook = {}
	State.workbook_titles = {}
	State.dashboards = {}
	State.readable_dashboards = set()
	State.dashboard_workbook = {}
	State.dashboard_charts = {}
	State.drilldowns = {}
	State.unreadable_charts = set()


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
for endpoint in ("add", "remove", "set_size", "set_order", "set_intro", "set_question", "set_palette"):
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

# --- #0: a successful change reports success --------------------------------
# The whole run above wrote seven audit records. Not one of them may have put
# anything in front of the user. The regression this catches: on_update fires
# on insert too, so the controller's own immutability guard threw against the
# insert that created the record -- the row landed, the exception was swallowed
# by record(), and "Audit records cannot be edited." reached the browser anyway.
report(State.messages == [],
	"a successful change shows the user no error (%r)" % State.messages)

# ...and the guard it now skips on insert still refuses a real edit.
existing = FakeAudit()
existing.update({"criterion": "criterion_3", "tab": "overview", "action": "chart_added"})
existing.insert(ignore_permissions=True)
loaded = FakeAudit()          # as a second save would arrive: no insert flag
report(raises(PermissionError_, loaded.on_update),
	"an audit record still cannot be edited after it exists")

# A change that changes nothing is not a change.
State.messages = []
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

# --- PRESENTATION: reading Insights Chart v3 (2026-08-02) -------------------
# Sophia embeds Queries, which carry data and no presentation. Chart type,
# axes, legend and labels live on a separate Chart record. Colour does NOT --
# the live probe dumped all seven records and there is no colour field, so
# Sophia owns it. See analytics/chart_presentation.py.
from ucc_intelligence.analytics import chart_presentation  # noqa: E402

reset()
tab_charts.add("criterion_3", "overview", "q-open")

# No Chart record: the table is the answer, and it says so.
data = tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")
report(data["presentation"]["status"] == "table_only",
	"a query with no Insights chart falls back to the table")
report("No Insights chart" in data["presentation"]["reason"],
	"...and the reason is stated, not blank: %r" % data["presentation"]["reason"])
report(data["presentation"]["palette"] == chart_presentation.DEFAULT_PALETTE,
	"...and it still carries the default palette")

# With a Chart record whose columns match the query's real ones.
State.doctypes.add("Insights Chart v3")
State.insights_charts = [{
	"name": "chart-1", "title": "Open by status", "chart_type": "Bar",
	"query": "q-open", "data_query": None,
	"config": json.dumps({"x_axis": "status", "y_axis": ["count"],
		"legend_position": "bottom", "axis_label": "Actions", "stack": 0}),
}]
data = tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")
presentation = data["presentation"]
report(presentation["status"] == "available", "a chart-backed query renders as a chart")
report(presentation["render_as"] == "bar" and presentation["chart_type"] == "Bar",
	"the free-text chart_type maps to a supported renderer")
report(presentation["x_column"] == "status" and presentation["y_columns"] == ["count"],
	"the axes come off the Chart record, not from guessing the query's columns")
report(presentation["legend_position"] == "bottom" and presentation["axis_label"] == "Actions",
	"legend position and axis label carry through")

# The ten types the v3 builder actually offers, read off the UI on 2026-08-02.
# Asserted as a set so the gap is explicit rather than discovered chart by
# chart, and so adding a renderer has to update this line deliberately.
V3_BUILDER_TYPES = ["Number", "Bar", "Line", "Row", "Donut", "Funnel", "Table",
	"Map", "Bubble", "Sankey"]
drawn, fell_back = [], []
for chart_type in V3_BUILDER_TYPES:
	State.insights_charts[0]["chart_type"] = chart_type
	result = tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")["presentation"]
	(drawn if result["status"] == "available" else fell_back).append(chart_type)
report(drawn == ["Number", "Bar", "Line", "Row", "Donut", "Funnel"],
	"of the ten v3 chart types, these six are drawn: %s" % drawn)
report(fell_back == ["Table", "Map", "Bubble", "Sankey"],
	"...and these four show their rows instead: %s" % fell_back)

# "Table" is not a gap and must not apologise for itself.
State.insights_charts[0]["chart_type"] = "Table"
table = tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")["presentation"]
report("not drawn here yet" not in table["reason"] and "table" in table["reason"].lower(),
	"a Table chart is shown as a table without calling it unsupported: %r" % table["reason"])

# chart_type is FREE TEXT, so an unknown one must degrade, never break.
State.insights_charts[0]["chart_type"] = "Sankey"
degraded = tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")["presentation"]
report(degraded["status"] == "table_only" and "Sankey" in degraded["reason"],
	"an unsupported chart type names the type it could not draw: %r" % degraded["reason"])
State.insights_charts[0]["chart_type"] = "Bar"

# The check that stops a confident wrong answer.
State.insights_charts[0]["config"] = json.dumps({"x_axis": "department", "y_axis": ["count"]})
stale = tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")["presentation"]
report(stale["status"] == "table_only" and "department" in stale["reason"],
	"a config column the query no longer returns is never rendered against")

# Both config shapes -- plain strings and nested dicts -- are read.
State.insights_charts[0]["config"] = json.dumps({
	"x_axis": {"column_name": "status"}, "y_axis": [{"measure_name": "count"}]})
nested = tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")["presentation"]
report(nested["x_column"] == "status" and nested["y_columns"] == ["count"],
	"config written as nested dicts reads the same as plain strings")

# A chart the user cannot read must not resolve for them.
State.insights_charts = []
hidden = tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")["presentation"]
report(hidden["status"] == "table_only",
	"a Chart record this user cannot read gives them the table, not someone else's chart")

# --- COLOUR: Sophia's, not Insights' ----------------------------------------
report(chart_presentation.normalise_palette("#FFF\n#2563EB, #000000") ==
	["#FFF", "#2563EB", "#000000"],
	"a palette typed as lines or commas parses")
report(chart_presentation.normalise_palette("red; drop table charts--") == [],
	"anything that is not a hex colour never reaches the browser")
report(chart_presentation.normalise_palette("1234567") == [],
	"...including a value that is the right length and all-hex but has no '#'")
report(chart_presentation.normalise_palette('#fff" onload="alert(1)') == [],
	"...and one carrying an attribute break, which is what makes this a security check")
report(all(colour.startswith("#") for colour in
	chart_presentation.normalise_palette(["#2563EB", "2563EB", "rgb(0,0,0)", "#12345"])),
	"every colour that survives starts with '#' -- the value goes into a style attribute")
report(chart_presentation.normalise_palette(["#2563EB", "#2563EB"]) == ["#2563EB"],
	"duplicates collapse")
report(len(chart_presentation.normalise_palette(["#00000%d" % (i % 10) for i in range(60)]))
	<= chart_presentation.MAX_PALETTE, "and the list is capped")

State.palette = "#111111\n#222222"
report(chart_presentation.default_palette() == ["#111111", "#222222"],
	"the institution default comes from UCC Intelligence Settings")
State.palette = None

# Per-chart override, on the tab, audited like every other change.
reset()
State.doctypes.add("Insights Chart v3")
tab_charts.add("criterion_3", "overview", "q-open")
tab_charts.set_palette("criterion_3", "overview", "q-open", "#ABCDEF")
report(tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")
	["presentation"]["palette"] == ["#ABCDEF"],
	"a per-chart override beats the institution default")
report(any(entry["action"] == "chart_recoloured" for entry in State.audit),
	"...and recolouring is audited like every other tab change")
report(tab_charts.chart_data("q-open")["presentation"]["palette"]
	== chart_presentation.DEFAULT_PALETTE,
	"the override is scoped to its tab -- asked without one, the default applies")
tab_charts.set_palette("criterion_3", "overview", "q-open", "")
report(tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")
	["presentation"]["palette"] == chart_presentation.DEFAULT_PALETTE,
	"clearing the override returns the chart to the default")

State.may_write = False
report(raises(PermissionError_, tab_charts.set_palette,
	"criterion_3", "overview", "q-open", "#123456"),
	"a reader cannot recolour a chart")
State.may_write = True

# --- THE 2026-08-03 CONFIG PROBE: what is honoured, and what is not ---------
reset()
State.doctypes.add("Insights Chart v3")
State.readable.add("q-open")
BASE = {"x_axis": "status", "y_axis": ["count"]}


def with_config(**extra):
	config = dict(BASE)
	config.update(extra)
	State.insights_charts = [{"name": "chart-c", "title": "Open by status",
		"chart_type": "Bar", "query": "q-open", "data_query": None,
		"config": json.dumps(config)}]
	return chart_presentation.presentation_for("q-open", columns=["status", "count"])


# limit: honoured, because a number cannot be misread.
report(with_config(limit=10)["limit"] == 10, "the chart's limit is read")
report(with_config()["limit"] == 0, "no limit means no limit, not a default one")
for junk in ("", None, "ten", -3, 0):
	report(with_config(limit=junk)["limit"] == 0,
		"a junk limit (%r) is ignored rather than guessed at" % junk)

# filters: the chart is WITHHELD, because Sophia executes the query and
# Insights applies the chart's filters on top -- the figures would differ.
filtered = with_config(filters=[{"column": "status", "operator": "=", "value": "Open"}])
report(filtered["status"] == "table_only" and "would not match" in filtered["reason"],
	"a chart with its own filters is withheld, not drawn from unfiltered rows")
report(with_config(filters=[])["status"] == "available",
	"an EMPTY filter list is not a filter -- that chart still draws")
report(with_config(filters={})["status"] == "available", "...nor is an empty object")

# THE SHAPE INSIGHTS ACTUALLY WRITES.
#
# The two checks above tested `[]` and `{}` -- both shapes I assumed, neither
# the one on the bench. Insights stores a filter GROUP, and an empty group is a
# dict with two keys, so it counted as "has filters" and withheld every chart.
#
# These are the VERBATIM values Felix read out of the database, by direct
# console query, for the three charts on his Sophia tabs. Not a fixture shaped
# to match the fix -- the live rows, chart id and all. He had set no filters on
# any of them.
LIVE_EMPTY_FILTERS = {
	"noe64v5472": {"filters": [], "logical_operator": "And"},
	"o80uuu7v3d": {"filters": [], "logical_operator": "And"},
	"o2kvutcfld": {"filters": [], "logical_operator": "And"},
}
for chart_id, live in LIVE_EMPTY_FILTERS.items():
	report(chart_presentation.filter_count(live) == 0,
		"live chart %s: its empty filter GROUP counts as 0 filters" % chart_id)
	report(with_config(filters=live)["status"] == "available",
		"...so it draws, instead of being withheld as filtered")

# ...and a group that really does hold one still withholds, so the fix did not
# simply switch the guard off.
real_group = {"filters": [{"column": "status", "operator": "=", "value": "Open"}],
	"logical_operator": "And"}
report(chart_presentation.filter_count(real_group) == 1,
	"a filter group holding ONE filter counts as 1")
report(with_config(filters=real_group)["status"] == "table_only",
	"...and that chart is still withheld")
nested = {"filters": [{"filters": [], "logical_operator": "Or"}, real_group],
	"logical_operator": "And"}
report(chart_presentation.filter_count(nested) == 1,
	"a nested group counts only the filters inside it, not the groups")
report(chart_presentation.filter_count({"filters": [], "logical_operator": "And"}) == 0
	and chart_presentation.filter_count("something unrecognised") == 1,
	"an unknown non-empty shape still withholds -- ADR-016, refuse rather than infer")

# The keys whose MEANING is unconfirmed are not read at all. Asserted as an
# absence so nobody quietly wires one later on the strength of its name.
unconfirmed = with_config(order_by="count desc", value_column="count",
	label_column="status", label_position="left", date_column="creation",
	location_column="country", size_column="count", source_column="a",
	target_column="b", number_columns=["count"], number_column_options={},
	show_inline_labels=True)
for key in ("order_by", "value_column", "label_column", "label_position",
		"date_column", "location_column", "size_column", "source_column",
		"target_column", "number_columns", "number_column_options",
		"show_inline_labels"):
	report(key not in unconfirmed,
		"%s is NOT read -- its key is confirmed, its meaning is not" % key)
report(unconfirmed["status"] == "available",
	"...and their presence does not stop the chart drawing")

# THE 2026-08-03 BUG: x_axis as a LIST.
# _column_of's docstring said it read "a plain string, a dict, or a list of
# either" from the day it was written. It never handled the list. So
# bool(config["x_axis"]) was True -- every diagnostic said the axis was set --
# while the parse returned "" and the card said "no X Axis Column set".
for shape, label in (
		([{"column_name": "status"}], "a list of dicts"),
		(["status"], "a list of strings"),
		([{}, {"column_name": "status"}], "a list whose first entry is empty")):
	listed = with_config(x_axis=shape, y_axis=[{"measure_name": "count"}])
	report(listed["status"] == "available" and listed["x_column"] == "status",
		"an x_axis written as %s resolves (was the 'no X Axis' bug)" % label)
report(with_config(x_axis=[], y_axis=["count"])["status"] == "table_only",
	"an EMPTY list is still no axis")
report(chart_presentation._column_of(
	[{"aggregation": "", "column_name": "", "data_type": ""}]) == "",
	"a list containing only the empty placeholder yields no column")

# THE DONUT BUG (2026-08-03, Felix's third card).
# Its x_axis is {"dimension": {}} -- an empty wrapper -- while label_column
# holds "benchmark_type". Reading x_axis universally left it blank, and the
# probe's truthiness check called that "should draw this": a false positive on
# exactly the chart that did not draw.
State.rows = [{"benchmark_type": "Process", "count": 12}]
State.insights_charts = [{"name": "chart-d", "title": "Innovation type mix",
	"chart_type": "Donut", "query": "q-open", "data_query": None,
	"config": json.dumps({"x_axis": {"dimension": {}},
		"label_column": "benchmark_type", "value_column": "count"})}]
donut = chart_presentation.presentation_for("q-open", columns=["benchmark_type", "count"])
report(donut["status"] == "available" and donut["render_as"] == "donut",
	"a Donut configured with label_column/value_column now draws")
report(donut["x_column"] == "benchmark_type" and donut["y_columns"] == ["count"],
	"...resolving the columns the chart actually names (%s / %s)"
	% (donut["x_column"], donut["y_columns"]))

# The FALLBACK chain alone fixes Felix's Donut, because its x_axis is empty.
# What the type ORDERING adds is the case where both keys hold real, DIFFERENT
# columns -- then the order decides, and getting it wrong draws a truthful
# chart of the wrong thing, which is the worst outcome available.
State.insights_charts[0]["config"] = json.dumps({
	"x_axis": "status", "label_column": "benchmark_type", "value_column": "count"})
State.rows = [{"status": "Open", "benchmark_type": "Process", "count": 12}]
both = chart_presentation.presentation_for(
	"q-open", columns=["status", "benchmark_type", "count"])
report(both["x_column"] == "benchmark_type",
	"a Donut with BOTH keys populated uses label_column, not x_axis (%s)" % both["x_column"])

# An axis chart keeps preferring x_axis, so this did not just swap the bug over.
State.insights_charts[0].update({"chart_type": "Bar", "config": json.dumps(
	{"x_axis": "status", "label_column": "benchmark_type", "y_axis": ["count"]})})
State.rows = [{"status": "Open", "count": 3, "benchmark_type": "Process"}]
bar = chart_presentation.presentation_for(
	"q-open", columns=["status", "count", "benchmark_type"])
report(bar["x_column"] == "status",
	"a Bar still prefers x_axis when BOTH are present (%s)" % bar["x_column"])

# ...and each falls back to the other rather than failing.
State.insights_charts[0].update({"chart_type": "Donut", "config": json.dumps(
	{"x_axis": "status", "y_axis": ["count"]})})
report(chart_presentation.presentation_for("q-open",
	columns=["status", "count"])["x_column"] == "status",
	"a Donut with only x_axis still draws -- the order is a preference, not a rule")

# The empty wrapper on its own is still no axis.
report(chart_presentation._column_of({"dimension": {}}) == "",
	"an empty {'dimension': {}} wrapper yields no column")
report(chart_presentation._column_of({"dimension": {"column_name": "benchmark_type"}})
	== "benchmark_type", "...and a populated one does")

# resolve_axes() is what the bench probe calls, so probe and app cannot diverge.
report(chart_presentation.resolve_axes(
	{"label_column": "benchmark_type"}, "donut") == ("benchmark_type", []),
	"resolve_axes() is public, so the probe reports what the app really resolves")

reset()
State.doctypes.add("Insights Chart v3")
with_config()   # restore the plain Bar chart the message tests below expect

# A misleading message is its own bug. These three situations are different
# and must never share a sentence.
no_rows = chart_presentation.presentation_for("q-open", columns=[])
report(no_rows["status"] == "table_only" and "returned no rows" in no_rows["reason"]
	and "X Axis" not in no_rows["reason"],
	"a query with NO ROWS never blames the axis: %r" % no_rows["reason"])
unreadable = with_config(x_axis={"mystery_key": "status"})
report("could not read" in unreadable["reason"] and "not something to fix in Insights" in unreadable["reason"],
	"an axis Sophia cannot PARSE says so, instead of sending Felix to set it again")
# with_config() always merges the BASE x_axis in, so a genuinely-unset axis
# needs the config written directly.
State.insights_charts = [{"name": "chart-c", "title": "No axes at all",
	"chart_type": "Bar", "query": "q-open", "data_query": None,
	"config": json.dumps({"y_axis": ["count"]})}]
missing = chart_presentation.presentation_for("q-open", columns=["status", "count"])
report("no X Axis Column set" in missing["reason"],
	"...and a genuinely unset axis still says to go and set it: %r" % missing["reason"])

# xAxis/yAxis are the builder's unfilled scaffolding, never a fallback.
PLACEHOLDER = {"aggregation": "", "column_name": "", "data_type": "", "dimension_name": ""}
report(chart_presentation._column_of(PLACEHOLDER) == "",
	"the camelCase placeholder shape yields NO column, so it can never resolve a chart")
# Whitespace is not a column name either. The column-validation gate downstream
# would reject "   " anyway, so this is belt-and-braces -- but a mutation that
# removed the strip() survived every behavioural test precisely BECAUSE the
# later gate hid it, and an intent that is only enforced by accident is not
# enforced.
report(chart_presentation._column_of({"column_name": "   "}) == "",
	"a whitespace-only column name is no column")
report(chart_presentation._column_of("  status  ") == "status",
	"...and a real one is trimmed rather than rejected")
camel = with_config(xAxis=PLACEHOLDER, yAxis=[PLACEHOLDER])
report(camel["x_column"] == "status" and camel["y_columns"] == ["count"],
	"a chart carrying BOTH spellings uses the snake_case one, which holds the real names")
State.insights_charts = [{"name": "chart-c", "title": "Only camelCase",
	"chart_type": "Bar", "query": "q-open", "data_query": None,
	"config": json.dumps({"xAxis": PLACEHOLDER, "yAxis": [PLACEHOLDER]})}]
only_camel = chart_presentation.presentation_for("q-open", columns=["status", "count"])
report(only_camel["status"] == "table_only",
	"a chart with ONLY the EMPTY placeholder pair is unconfigured, and says so")

# ...but a camelCase pair holding REAL column names is used, because Felix set
# axes on a chart and Sophia reported none. Safe because condition 3 -- the
# name must match a column the query returned -- still applies.
State.insights_charts = [{"name": "chart-c", "title": "camelCase with real values",
	"chart_type": "Bar", "query": "q-open", "data_query": None,
	"config": json.dumps({"xAxis": {"column_name": "status"},
		"yAxis": [{"measure_name": "count"}]})}]
real_camel = chart_presentation.presentation_for("q-open", columns=["status", "count"])
report(real_camel["status"] == "available" and real_camel["x_column"] == "status",
	"a camelCase pair holding REAL column names is used as a fallback")
State.insights_charts[0]["config"] = json.dumps({"xAxis": {"column_name": "not_a_column"}})
bogus = chart_presentation.presentation_for("q-open", columns=["status", "count"])
report(bogus["status"] == "table_only",
	"...but only when the name is a column the query really returns")

# --- LABELS: never a bare id ------------------------------------------------
# Insights creates an untitled backing query when a chart is built. Four of
# those reached Felix's tabs and rendered as `o80pe2gco2`, `o2kqldogas`,
# `noe9aqlhd8` -- four hashes where four chart names should have been.
reset()
State.charts["q-untitled"] = ""          # a query with no title at all
State.readable.add("q-untitled")
State.doctypes.add("Insights Chart v3")

# With a Chart: the Chart's name is the label, even though the chart is not
# drawable yet -- which is the case that was broken, since an unconfigured
# chart took the fallback branch and carried no title with it.
State.insights_charts = [{"name": "chart-9", "title": "Innovation type mix",
	"chart_type": "Donut", "query": "q-untitled", "data_query": None,
	"config": json.dumps({})}]
tab_charts.add("criterion_3", "overview", "q-untitled")
card = tab_charts.chart_data("q-untitled", criterion="criterion_3", tab="overview")
report(card["title"] == "Innovation type mix",
	"an untitled query shows its CHART's title, not a hash (%r)" % card["title"])
report(card["presentation"]["status"] == "table_only",
	"...even though the chart itself is not drawable yet")
report("X Axis Column" in card["presentation"]["reason"],
	"...and the reason names the control to set: %r" % card["presentation"]["reason"])

# A titled query AND a titled chart: the chart wins, because that is what the
# person building it named the thing they built.
State.charts["q-untitled"] = "raw stakeholder rows"
report(tab_charts.chart_data("q-untitled", criterion="criterion_3", tab="overview")["title"]
	== "Innovation type mix", "the chart's title beats the query's")

# No chart at all, no title either: labelled, never a raw hash.
State.insights_charts = []
State.charts["q-untitled"] = ""
bare = tab_charts.chart_data("q-untitled", criterion="criterion_3", tab="overview")
report(bare["title"] != "q-untitled" and "q-untitled" in bare["title"],
	"with neither title, the id is LABELLED rather than dumped raw (%r)" % bare["title"])

# The picker follows the same rule -- 52 hashes is not a list anyone can use.
State.insights_charts = [{"name": "chart-9", "title": "Innovation type mix",
	"chart_type": "Donut", "query": "q-untitled", "data_query": None, "config": "{}"}]
picked = {row["chart"]: row["title"] for row in tab_charts.search("")["charts"]}
report(picked["q-untitled"] == "Innovation type mix",
	"the picker lists by title too, never by id (%r)" % picked["q-untitled"])
report(not any(title == chart for chart, title in picked.items()),
	"no row in the picker is labelled with its own id")

# --- #4: a card's OWN title -------------------------------------------------
# Insights names a query for whoever built it. A criterion tab is read by an
# auditor, and "Chart 1" tells them nothing.
reset()
State.doctypes.add("Insights Chart v3")
State.insights_charts = [{"name": "chart-t", "title": "Chart 1", "chart_type": "Bar",
	"query": "q-open", "data_query": None, "config": "{}"}]
tab_charts.add("criterion_3", "overview", "q-open")
report(tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")["title"]
	== "Chart 1", "with no override, the Insights title is used as before")
tab_charts.set_display_title("criterion_3", "overview", "q-open", "Open actions by status")
report(tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")["title"]
	== "Open actions by status", "a card's own title beats the Insights record's")
report(any(entry["action"] == "chart_retitled" for entry in State.audit),
	"...and renaming is audited like every other tab change")
report(tab_charts.chart_data("q-open")["title"] == "Chart 1",
	"the override is scoped to its tab, like the palette")
tab_charts.set_display_title("criterion_3", "overview", "q-open", "")
report(tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")["title"]
	== "Chart 1", "clearing it returns the record's own title")
tab_charts.set_display_title("criterion_3", "overview", "q-open", "x" * 500)
stored_title = tab_charts.chart_data("q-open", criterion="criterion_3", tab="overview")["title"]
report(len(stored_title) == tab_charts.MAX_TITLE_LENGTH,
	"an absurd title is truncated, not stored whole (%d)" % len(stored_title))
State.may_write = False
report(raises(PermissionError_, tab_charts.set_display_title,
	"criterion_3", "overview", "q-open", "Nope"),
	"a reader cannot rename a card")
State.may_write = True

# --- THE PICKER: both kinds, marked -----------------------------------------
reset()
State.doctypes.add("Insights Chart v3")
State.insights_charts = [{"name": "chart-1", "title": "Open by status",
	"chart_type": "Donut", "query": "q-open", "data_query": None, "config": "{}"}]
listed = {row["chart"]: row for row in tab_charts.search("")["charts"]}
report(listed["q-open"]["has_chart"] and listed["q-open"]["chart_type"] == "Donut",
	"the picker marks a query that has a chart, and says which type")
report("q-agents" in listed and not listed["q-agents"]["has_chart"],
	"a chart-less query is still OFFERED -- 45 of 52 would vanish otherwise")
report("q-secret" not in listed,
	"...but a query this user cannot read is still absent")

# ONE row per chart, even when Insights reaches it through two queries.
reset()
State.doctypes.add("Insights Chart v3")
State.charts["q-backing"] = ""            # the untitled data_query Insights made
State.readable.add("q-backing")
State.insights_charts = [{"name": "chart-1", "title": "Open by status",
	"chart_type": "Bar", "query": "q-open", "data_query": "q-backing", "config": "{}"}]
rows = tab_charts.search("")["charts"]
report(len([row for row in rows if row.get("chart_type") == "Bar"]) == 1,
	"a chart reachable through two queries is offered ONCE, not twice")
report(any(row["chart"] == "q-open" for row in rows)
	and not any(row["chart"] == "q-backing" for row in rows),
	"...and it is the authored query that survives, not the generated backing one")
report(all(row["title"] != row["chart"] for row in rows),
	"no surviving row is labelled with its own id")


# --- THE PICKER FILTER: charts only / table only ----------------------------
#
# The property that makes this more than a one-line UI change: the filter has
# to run BEFORE the page is cut. The DB limit used to be the page size, so
# "Charts only" would have searched the 20 most recent rows for the 7 charts
# among 52 queries and shown however few landed in that window. A filter that
# reports nothing while matches exist is worse than no filter, so the fixture
# below deliberately buries the only chart PAST the page size.
reset()
State.doctypes.add("Insights Chart v3")
for index in range(40):
	name = "q-bulk-%02d" % index
	State.charts[name] = "Bulk query %02d" % index
	State.readable.add(name)
State.charts["q-buried"] = "Buried behind forty others"
State.readable.add("q-buried")
State.insights_charts = [{"name": "chart-b", "title": "Buried chart",
	"chart_type": "Bar", "query": "q-buried", "data_query": None, "config": "{}"}]

everything = tab_charts.search("", limit=5)
report(len(everything["charts"]) == 5 and everything["counts"]["all"] > 5,
	"the page is still %d rows, while the count describes them all (%d)"
	% (len(everything["charts"]), everything["counts"]["all"]))

only_charts = tab_charts.search("", limit=5, kind="charts")
report([row["chart"] for row in only_charts["charts"]] == ["q-buried"],
	"'Charts only' finds the ONE chart buried past the page size")
report(all(row["has_chart"] for row in only_charts["charts"]),
	"...and every row it returns really has a chart")
report(only_charts["counts"]["charts"] == 1
	and only_charts["counts"]["tables"] == len(State.readable) - 1,
	"the counts add up over the whole search, not the page")
report(only_charts["counts"]["all"]
	== only_charts["counts"]["charts"] + only_charts["counts"]["tables"],
	"...and all = charts + tables, so no row is in neither bucket")

only_tables = tab_charts.search("", limit=50, kind="tables")
report(not any(row["has_chart"] for row in only_tables["charts"]),
	"'Table only' returns nothing that has a chart built on it")
report("q-buried" not in [row["chart"] for row in only_tables["charts"]],
	"...and specifically excludes the one that does")

# A filter narrows what is LISTED. It must not reach anything the unfiltered
# list could not, which is the only way this could become a permission problem.
report("q-secret" not in [row["chart"] for row in
		tab_charts.search("", limit=50, kind="tables")["charts"]]
	and "q-secret" not in [row["chart"] for row in
		tab_charts.search("", limit=50, kind="charts")["charts"]],
	"neither filter reaches a query this user cannot read")
report(tab_charts.search("", limit=5, kind="nonsense")["kind"] == "all",
	"an unknown kind falls back to All rather than returning an empty list")
report(tab_charts.search("", limit=5)["kind"] == "all",
	"...and the default is All, so the picker opens showing everything")
report(bool(only_charts["charts"]) and bool(everything["charts"])
	and set(only_charts["charts"][0]) == set(everything["charts"][0]),
	"a filtered row has exactly the same shape as an unfiltered one")


# --- STEP 1: WORKBOOKS ------------------------------------------------------
#
# Same three failure classes as the kind filter, one level up: narrowing after
# the page is cut, counting after narrowing, and an unknown value returning an
# empty list instead of falling back. The fixture buries the chart-bearing
# workbook's contents past the page size for the first of those.
reset()
State.doctypes.add("Insights Chart v3")
for index in range(30):
	name = "q-wb1-%02d" % index
	State.charts[name] = "Finance query %02d" % index
	State.readable.add(name)
	State.query_workbook[name] = "wb-finance"
for name, title in (("q-qa-1", "Quality Actions open"), ("q-qa-2", "Quality Actions closed")):
	State.charts[name] = title
	State.readable.add(name)
	State.query_workbook[name] = "wb-quality"
State.charts["q-loose"] = "A query in no workbook"
State.readable.add("q-loose")
State.charts["q-secret-wb"] = "Payroll detail"          # NOT readable
State.query_workbook["q-secret-wb"] = "wb-payroll"
State.workbook_titles = {"wb-finance": "Finance", "wb-quality": "Quality",
	"wb-payroll": "Payroll"}
State.insights_charts = [{"name": "chart-qa", "title": "Quality Actions open",
	"chart_type": "Bar", "query": "q-qa-1", "data_query": None, "config": "{}"}]

books = tab_charts.workbooks()
by_name = {entry["workbook"]: entry for entry in books["workbooks"]}
report(set(by_name) == {"wb-finance", "wb-quality", ""},
	"step 1 lists exactly the workbooks holding something readable: %s" % sorted(by_name))
report("wb-payroll" not in by_name,
	"a workbook whose ONLY query this user cannot read is not listed at all")
report(by_name[""]["title"] == "Not in a workbook",
	"a query belonging to no workbook gets its own honest bucket, not someone else's")
report(by_name["wb-finance"]["title"] == "Finance"
	and by_name["wb-quality"]["title"] == "Quality",
	"workbooks are titled, not shown as ids")
report(by_name["wb-finance"]["counts"]["all"] == 30,
	"the per-workbook count covers all 30, not the %d-row page"
	% len(tab_charts.search("", limit=5)["charts"]))
report(by_name["wb-quality"]["counts"]["charts"] == 1
	and by_name["wb-quality"]["counts"]["tables"] == 1,
	"...and splits into charts and tables, the same buckets as the pills")
report(books["total_counts"]["all"]
	== sum(entry["counts"]["all"] for entry in books["workbooks"]),
	"the All-workbooks total equals the sum of the parts -- nothing is double-counted")
report([entry["workbook"] for entry in books["workbooks"]][0] == "wb-finance",
	"the fullest workbook is listed first, so the likely one is not last")

# An unreadable workbook RECORD, with readable queries inside it. The title
# lookup returns nothing and the picker must still list it.
State.workbook_titles.pop("wb-quality")
report({entry["workbook"]: entry["title"] for entry in tab_charts.workbooks()["workbooks"]}
	.get("wb-quality") == "wb-quality",
	"a workbook whose own record is unreadable keeps its id as a label, never vanishes")
State.workbook_titles["wb-quality"] = "Quality"

# --- STEP 2: SCOPED TO ONE WORKBOOK -----------------------------------------
scoped = tab_charts.search("", limit=5, workbook="wb-quality")
report({row["chart"] for row in scoped["charts"]} == {"q-qa-1", "q-qa-2"},
	"step 2 shows that workbook's items and no others")
report(scoped["counts"]["all"] == 2 and scoped["counts"]["charts"] == 1,
	"the pills count THIS workbook (%s), not the whole site" % scoped["counts"])
report(tab_charts.search("", limit=5, workbook="wb-quality", kind="charts")["counts"]["all"] == 2,
	"...and are counted before the kind narrows it, so the pills stay stable")
report([row["chart"] for row in
		tab_charts.search("", limit=5, workbook="wb-quality", kind="charts")["charts"]]
	== ["q-qa-1"],
	"workbook AND kind compose: one row, in that workbook, with a chart")

# Buried past the page size, in a workbook that is not the first listed.
report(len(tab_charts.search("", limit=5, workbook="wb-finance")["charts"]) == 5
	and tab_charts.search("", limit=5, workbook="wb-finance")["counts"]["all"] == 30,
	"a 5-row page of a 30-item workbook still reports 30")

report({row["chart"] for row in tab_charts.search("", limit=50,
		workbook=tab_charts.ALL_WORKBOOKS)["charts"]}
	== {row["chart"] for row in tab_charts.search("", limit=50)["charts"]},
	"'All workbooks' is exactly the unscoped list -- the escape hatch is not a third behaviour")
report("q-secret-wb" not in [row["chart"] for row in
		tab_charts.search("", limit=50, workbook="wb-payroll")["charts"]],
	"naming a workbook directly does NOT reach a query inside it this user cannot read")
report(tab_charts.search("", limit=50, workbook="wb-does-not-exist")["charts"] == [],
	"an unknown workbook shows nothing rather than silently falling back to everything")
report(tab_charts.search("", limit=50, workbook="")["counts"]["all"]
	== tab_charts.search("", limit=50)["counts"]["all"],
	"...while a BLANK workbook means 'not narrowed', same as omitting it")
report(tab_charts.search("", limit=50, workbook="wb-quality")["workbook"] == "wb-quality",
	"the response says which workbook it answered for")


# --- PHASE 1 PILOT: one embedded Insights dashboard per tab -----------------
#
# Additive by construction. A tab without the field set must behave exactly as
# it did, and clearing the field must put an embedded tab back -- that is what
# makes this reversible without a migration.
reset()
State.dashboards = {"dash-ok": "Sophia Pilot", "dash-hidden": "Payroll dashboard"}
State.readable_dashboards = {"dash-ok"}

report(tab_charts.get_tab("criterion_1", "overview")["embedded_dashboard"] == "",
	"a tab with nothing embedded says so, rather than omitting the field")

tab_charts.set_dashboard("criterion_1", "overview", "dash-ok")
after = tab_charts.get_tab("criterion_1", "overview")
report(after["embedded_dashboard"] == "dash-ok", "the dashboard id is stored and returned")
report(after["embedded_dashboard_readable"] is True,
	"...with whether THIS user can open it, so the page can say why it is blank")
report(after["charts"] == [], "the painted chart list is untouched by embedding")

# The write refuses an id this user cannot read. Not the security boundary --
# the iframe's own session is -- but a typo caught here beats an empty frame
# everyone assumes is a bug in the embed.
report(raises(ValidationError_, tab_charts.set_dashboard,
	"criterion_1", "overview", "dash-hidden"),
	"a dashboard this user cannot read is refused on write")
report(raises(ValidationError_, tab_charts.set_dashboard,
	"criterion_1", "overview", "dash-does-not-exist"),
	"...and so is one that does not exist")
report(tab_charts.get_tab("criterion_1", "overview")["embedded_dashboard"] == "dash-ok",
	"...and neither refusal disturbed what was already set")

# Read is deliberately softer than write: a dashboard that STOPS being readable
# must not make the whole tab fail to load.
State.readable_dashboards = set()
soft = tab_charts.get_tab("criterion_1", "overview")
report(soft["embedded_dashboard"] == "dash-ok" and soft["embedded_dashboard_readable"] is False,
	"a dashboard that became unreadable still loads the tab, flagged not readable")
State.readable_dashboards = {"dash-ok"}

report(any(entry["action"] == "dashboard_embedded" for entry in State.audit),
	"embedding is written to the tab's audit trail")
tab_charts.set_dashboard("criterion_1", "overview", "")
report(tab_charts.get_tab("criterion_1", "overview")["embedded_dashboard"] == "",
	"clearing the field reverts the tab -- no migration to undo")
report(any(entry["action"] == "dashboard_unembedded" for entry in State.audit),
	"...and that is audited too")

State.may_write = False
report(raises(PermissionError_, tab_charts.set_dashboard,
	"criterion_1", "overview", "dash-ok"),
	"embedding needs the same tab edit permission as every other tab setting")
State.may_write = True

# ONE SHAPE PER TAB, enforced on the server. The page stops offering
# "+ Add chart" on an embedded tab, but a browser left open on the old markup
# still holds the button, and hiding a control has never been the boundary.
reset()
State.dashboards = {"dash-ok": "Sophia Pilot"}
State.readable_dashboards = {"dash-ok"}
tab_charts.add("criterion_1", "overview", "q-open")
report(len(tab_charts.get_tab("criterion_1", "overview")["charts"]) == 1,
	"a chart can be added to a tab with no dashboard")
tab_charts.set_dashboard("criterion_1", "overview", "dash-ok")
report(raises(ValidationError_, tab_charts.add, "criterion_1", "overview", "q-agents"),
	"...and REFUSED once the tab embeds a dashboard, on the server")
# EMBEDDING DELETES THE PAINTED CHARTS (decided 2026-08-04). They used to be
# kept and hidden so that clearing the field restored them. That fallback is
# retired, so the charts go -- and "gone" has to mean gone from STORAGE, not
# merely absent from what get_tab chooses to return.
after = tab_charts.get_tab("criterion_1", "overview")
report(after["charts"] == [] and after["embedded_dashboard"] == "dash-ok",
	"embedding a dashboard DELETES the tab's painted charts")
stored = json.loads(State.tabs["criterion_1::overview"]["charts"])
report(stored == [],
	"...from the stored record itself, not just from what the tab returns")
tab_charts.set_dashboard("criterion_1", "overview", "")
report(tab_charts.get_tab("criterion_1", "overview")["charts"] == [],
	"...and clearing the dashboard does NOT bring them back -- there is no fallback")
deleted = [line for line in State.audit if line["action"] == "charts_deleted"]
report(len(deleted) == 1 and "q-open" in deleted[0]["summary"]
	and "q-open" in deleted[0]["before_value"],
	"the deletion is recorded in the tab's history, naming what was removed")


# --- the dashboard picker: same shape, same guarantees ----------------------
reset()
State.doctypes.add("Insights Dashboard v3")
State.dashboards = {"d-1": "Applicants per year", "d-2": "Quality overview",
	"d-3": "Payroll"}
State.readable_dashboards = {"d-1", "d-2"}
State.dashboard_workbook = {"d-1": "wb-admissions", "d-2": "wb-quality",
	"d-3": "wb-payroll"}
State.workbook_titles = {"wb-admissions": "Admissions", "wb-quality": "Quality",
	"wb-payroll": "Payroll"}

books = tab_charts.dashboard_workbooks()
listed = {entry["workbook"]: entry for entry in books["workbooks"]}
report(set(listed) == {"wb-admissions", "wb-quality"},
	"step 1 lists only workbooks holding a dashboard this user can read: %s" % sorted(listed))
report("wb-payroll" not in listed,
	"a workbook whose only dashboard is unreadable is not offered at all")
report(listed["wb-admissions"]["title"] == "Admissions",
	"workbooks are titled, not shown as ids")
report(books["total"] == 2, "the total counts readable dashboards, not all of them")

scoped = tab_charts.search_dashboards("", limit=20, workbook="wb-quality")
report([row["dashboard"] for row in scoped["dashboards"]] == ["d-2"],
	"step 2 shows that workbook's dashboards and no others")
report("d-3" not in [row["dashboard"] for row in
		tab_charts.search_dashboards("", limit=20, workbook="wb-payroll")["dashboards"]],
	"naming a workbook directly does not reach a dashboard this user cannot read")
report(tab_charts.search_dashboards("", limit=1)["total"] == 2,
	"the total describes the whole search, not the one-row page")
report(len(tab_charts.search_dashboards("", limit=1)["dashboards"]) == 1,
	"...while the page itself is cut to the limit")
report(all(row["title"] != row["dashboard"] for row in
		tab_charts.search_dashboards("")["dashboards"]),
	"no dashboard is offered labelled with its own id")


# --- THE RECORDS STRIP: the drill-down chain, and its permission hops -------
#
# Four hops: the dashboard (check_permission), its linked_charts (child rows of
# a document just proven readable), each chart (get_list), the records
# (drilldown.py, untouched). The strip can only offer what a person could
# already open in Insights.
reset()
State.doctypes.add("Insights Dashboard v3")
State.doctypes.add("Insights Chart v3")
State.dashboards = {"d-1": "Applicants"}
State.readable_dashboards = {"d-1"}
State.dashboard_charts = {"d-1": ["chart-open", "chart-sql", "chart-hidden"]}
State.insights_charts = [
	{"name": "chart-open", "title": "Applicants by status", "chart_type": "Bar",
		"query": "q-open", "data_query": None, "config": "{}"},
	{"name": "chart-sql", "title": "Written as SQL", "chart_type": "Bar",
		"query": "q-agents", "data_query": None, "config": "{}"},
	# On the dashboard, but this user cannot read it -- get_list drops it.
	{"name": "chart-hidden", "title": "Payroll", "chart_type": "Bar",
		"query": "q-secret", "data_query": None, "config": "{}"},
]
State.unreadable_charts = {"chart-hidden"}
State.drilldowns = {
	"q-open": {"status": "available", "doctype": "Student Applicant",
		"columns": ["status"], "message": ""},
	"q-agents": {"status": "unsupported", "doctype": "", "columns": [],
		"message": "This chart is written as SQL rather than built from a table."},
}

strip = tab_charts.dashboard_drilldowns("d-1")
titles = [row["title"] for row in strip["charts"]]
report(strip["ok"] and len(strip["charts"]) == 2,
	"the strip lists the dashboard's charts this user can read (%s)" % titles)
report("Payroll" not in titles,
	"a chart ON the dashboard that this user cannot read is not listed at all")
report(len(strip["charts"]) == 2 and strip["charts"][0]["status"] == "available",
	"drillable charts are listed first, so the buttons are not hunted for")
report(len(strip["charts"]) == 2 and strip["charts"][1]["status"] != "available"
	and "written as SQL" in strip["charts"][1]["message"],
	"...and one that cannot be drilled carries its REASON, rather than vanishing")
report(bool(strip["charts"]) and strip["charts"][0]["doctype"] == "Student Applicant"
	and strip["charts"][0]["chart"] == "q-open",
	"each button carries the query drilldown.py needs and the DocType it opens")

State.readable_dashboards = set()
denied = tab_charts.dashboard_drilldowns("d-1")
report(denied["ok"] is False and "not available" in denied["message"],
	"a dashboard this user cannot read yields no chart list, with a reason")
State.readable_dashboards = {"d-1"}

State.dashboard_charts = {"d-1": []}
empty = tab_charts.dashboard_drilldowns("d-1")
report(empty["ok"] and empty["charts"] == [] and empty["source"] == "linked_charts",
	"an empty linked_charts says which field was empty, not just 'no charts'")

# The MESSAGE, not just the refusal. Without the guard a blank id still fails
# -- by reaching get_doc("") and being reported as "no longer in Insights",
# which is a different and wrong explanation.
blank = tab_charts.dashboard_drilldowns("")
report(blank["ok"] is False and "No dashboard given" in blank["message"],
	"a blank dashboard id is refused BEFORE any lookup, and says so: %r"
	% blank["message"])


# --- THE SERIES USES THE RESOLVED AXES, NOT A GUESS -------------------------
#
# Found while checking whether any of the nine controls was worth wiring, and
# it is worse than any of them: chart_presentation resolved the axes, validated
# them against the columns the query really returns, put them in the contract
# -- and the series builder ignored all of that and picked the measure by
# NAME. Correct for the six admission charts it was written for, which all
# measure `count`. For a chart measuring anything else, every value came out 0
# and the card drew a flat chart, with the real numbers sitting in the table
# view beside it. 259 checks passed while it did that.
from ucc_intelligence.analytics.admission_intelligence_embed import (  # noqa: E402
	rows_to_chart_series)

report(rows_to_chart_series([{"status": "Open", "count": 12}, {"status": "Shut", "count": 5}])
	== [{"label": "Open", "value": 12}, {"label": "Shut", "value": 5}],
	"the admission path, with no columns passed, is exactly as it was")
report(rows_to_chart_series([{"status": "Open", "total_fees": 9800}],
	label_column="status", value_column="total_fees") == [{"label": "Open", "value": 9800}],
	"a measure that is not `count` is READ, not silently drawn as zero")
report(rows_to_chart_series([{"status": "Open", "total_fees": 9800}])
	== [{"label": "Open", "value": 0}],
	"...and without the columns it still guesses, which is the bug being fixed")
report(rows_to_chart_series([{"programme": "BSc", "status": "Open", "count": 12}],
	label_column="status", value_column="count") == [{"label": "Open", "value": 12}],
	"with two dimensions the X AXIS wins, not whichever key came first")
report(rows_to_chart_series([{"status": "Open", "count": 12}],
	label_column="gone", value_column="also_gone") == [{"label": "Open", "value": 12}],
	"a column the query no longer returns falls back rather than drawing blanks")

# And the caller passes them. Asserted at the call site, because the parameter
# existing is worth nothing if chart_data() never fills it in.
import inspect as _inspect  # noqa: E402

chart_data_source = _inspect.getsource(tab_charts.chart_data)
report("label_column=presentation" in chart_data_source
	and "value_column=" in chart_data_source,
	"chart_data() passes the resolved axes into the series builder")

print(("PASS" if all(checks) else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
sys.exit(0 if all(checks) else 1)
