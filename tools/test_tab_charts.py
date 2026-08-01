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
	defaults = {}
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
	if name not in State.charts:
		raise DoesNotExistError_(name)
	return FakeDoc(name)


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
	frappe.db = types.SimpleNamespace(exists=lambda doctype, name=None: name in ("Insights Query v3",))
	frappe.defaults = types.SimpleNamespace(
		get_user_default=lambda key: State.defaults.get(key),
		set_user_default=lambda key, value: State.defaults.__setitem__(key, value),
	)
	frappe.utils = types.SimpleNamespace(now=lambda: "2026-08-01 00:00:00")
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
	State.defaults = {}
	State.executed = []


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
report([c["chart"] for c in tab_charts.get_charts("criterion_3", "overview")["charts"]] == ["q-open"],
	"a chart added to one tab appears on that tab")
report([c["chart"] for c in tab_charts.get_charts("criterion_3", "3.1.1")["charts"]] == ["q-agents"],
	"and NOT on another tab of the same criterion")
report(tab_charts.get_charts("criterion_6", "overview")["charts"] == [],
	"and not on another criterion")
report(len(State.defaults) == 2 and all(json.loads(v) for v in State.defaults.values()),
	"the selection is written to the per-user store, one key per tab")

# A fresh module-level cache would hide a broken read; go back through get.
report([c["chart"] for c in tab_charts.get_charts("criterion_3", "overview")["charts"]] == ["q-open"],
	"the selection survives a re-read -- it is stored, not held in memory")
report(tab_charts.get_charts("criterion_3", "overview")["charts"][0]["title"] == "Open Actions",
	"the title is resolved live, so a renamed chart does not show a stale name")

# --- adding is permission-checked ------------------------------------------
reset()
report(raises(PermissionError_, tab_charts.add, "criterion_3", "overview", "q-secret"),
	"a chart the user cannot read CANNOT be added")
report(State.defaults == {}, "and nothing is written when the add is refused")
report(raises(PermissionError_, tab_charts.add, "criterion_3", "overview", "q-nonexistent"),
	"an id that does not exist is refused the same way, so errors leak no ids")

# --- a stored id is a preference, never a grant -----------------------------
reset()
tab_charts.add("criterion_3", "overview", "q-open")
State.readable.discard("q-open")          # access revoked after it was added
report(tab_charts.get_charts("criterion_3", "overview")["charts"] == [],
	"a chart you may no longer read stops appearing, even though it is still stored")
report(tab_charts.chart_data("q-open")["status"] == "permission_denied",
	"and executing it is refused")
report(State.executed == [], "the query never ran")
# ...and you can still get rid of it, or it would be stuck there forever.
tab_charts.remove("criterion_3", "overview", "q-open")
report(json.loads(State.defaults[tab_charts._key("criterion_3", "overview")]) == [],
	"removing works even for a chart you can no longer read")

# --- the criterion gate -----------------------------------------------------
reset()
State.criteria["criterion_5"] = False
report(raises(PermissionError_, tab_charts.get_charts, "criterion_5", "overview"),
	"a criterion hidden by ucc_dashboard_access cannot be read")
report(raises(PermissionError_, tab_charts.add, "criterion_5", "overview", "q-open"),
	"and cannot be added to")
report(tab_charts.get_charts("criterion_3", "overview")["ok"] is True,
	"a visible criterion still works")

# --- input validation -------------------------------------------------------
reset()
report(raises(ValidationError_, tab_charts.get_charts, "criterion_99", "overview"),
	"an invented criterion is rejected")
report(raises(ValidationError_, tab_charts.get_charts, "criterion_3", "../../etc/passwd"),
	"a tab key cannot contain path characters -- it becomes part of a stored key")
report(raises(ValidationError_, tab_charts.get_charts, "criterion_3", "x" * 60),
	"an over-long tab key is rejected")

# --- bounded ----------------------------------------------------------------
reset()
State.charts = {"q-%d" % i: "Chart %d" % i for i in range(20)}
State.readable = set(State.charts)
for index in range(tab_charts.MAX_PER_TAB):
	tab_charts.add("criterion_3", "overview", "q-%d" % index)
report(len(tab_charts.get_charts("criterion_3", "overview")["charts"]) == tab_charts.MAX_PER_TAB,
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
State.defaults[tab_charts._key("criterion_3", "overview")] = "{not json"
report(tab_charts.get_charts("criterion_3", "overview")["charts"] == [],
	"a corrupt stored value costs the layout, not the page")

print(("PASS" if all(checks) else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
sys.exit(0 if all(checks) else 1)
