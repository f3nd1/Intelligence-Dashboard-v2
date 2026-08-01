#!/usr/bin/env python3
"""Self-check for analytics/drilldown.py -- chart segment to underlying records.

    python3 tools/test_drilldown.py

WHAT THIS PROVES
The dangerous version of this feature works perfectly and leaks records. So the
checks that matter here are the negative ones: that a reader who may see the
bar but not the rows gets nothing, that records are fetched through the
permission-applying call and never through Insights' own SQL, and that every
query shape the module cannot reproduce faithfully is refused rather than
approximated.

THE FIXTURE IS THE REAL ONE
The stakeholder query below is the operations structure the live probe printed
on 2026-08-02 from `vc55npin67`, copied verbatim -- including the empty
top-level data_source and the "Site DB" that lives inside the source step.
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


class PermissionError_(Exception):
	pass


class DoesNotExistError_(Exception):
	pass


# --- the live shape, copied from the probe ----------------------------------
STAKEHOLDER_OPERATIONS = [
	{
		"table": {
			"data_source": "Site DB",
			"table_name": "tabStakeholder Engagement Strategy",
			"type": "table",
		},
		"type": "source",
	},
	{
		"dimensions": [
			{"column_name": "engagement_type", "data_type": "String",
				"dimension_name": "engagement_type"},
		],
		"measures": [
			{"aggregation": "count", "column_name": "count", "data_type": "Integer",
				"measure_name": "count"},
		],
		"type": "summarize",
	},
]


class State:
	queries = {}
	readable_queries = set()
	doctype_read = {}      # DocType -> may this user read it at all
	records = {}           # DocType -> [row, ...]
	hidden = set()         # record names this user may not see (row-level)
	executed = []          # anything that reached Insights' own SQL
	fields = {}            # DocType -> real fieldnames
	title_fields = {}


class FakeQuery:
	def __init__(self, name):
		self.data = dict(State.queries[name])
		self.name = name

	def get(self, key):
		return self.data.get(key)

	def check_permission(self, ptype):
		if self.name not in State.readable_queries:
			raise PermissionError_("Not permitted to read %s" % self.name)

	def execute(self, **kwargs):
		# Reaching this from a drill-down would mean records came back through
		# Insights' SQL, which applies no Frappe permissions at all.
		State.executed.append(self.name)
		return {"rows": []}


class FakeMeta:
	def __init__(self, doctype):
		self.doctype = doctype

	def has_field(self, fieldname):
		return fieldname in State.fields.get(self.doctype, ())

	def get(self, key):
		if key == "title_field":
			return State.title_fields.get(self.doctype)
		return None


def matches(row, condition):
	field, operator, value = condition
	actual = row.get(field)
	if operator == "=":
		return actual == value
	if operator == "!=":
		return actual != value
	if operator == "in":
		return actual in value
	if operator == "not in":
		return actual not in value
	if operator == "like":
		return str(value).strip("%") in str(actual or "")
	if operator == ">":
		return actual > value
	if operator == "<":
		return actual < value
	raise AssertionError("unhandled operator in the fake: %r" % operator)


def fake_get_list(doctype, filters=None, fields=None, order_by=None,
		limit_start=0, limit_page_length=20):
	"""The permission-applying read, modelled as one.

	Two refusals, both real: no read permission on the DocType at all, and
	row-level filtering of individual records. get_list does both; Insights'
	execute() does neither, which is the entire reason this module exists.
	"""
	if not State.doctype_read.get(doctype, True):
		raise PermissionError_("No read permission on %s" % doctype)
	rows = [row for row in State.records.get(doctype, [])
		if row["name"] not in State.hidden
		and all(matches(row, condition) for condition in (filters or []))]
	rows = rows[limit_start:limit_start + limit_page_length]
	return [{field: row.get(field) for field in (fields or ["name"])} for row in rows]


def install_fake_frappe():
	frappe = types.ModuleType("frappe")
	frappe.PermissionError = PermissionError_
	frappe.DoesNotExistError = DoesNotExistError_
	frappe.ValidationError = type("ValidationError", (Exception,), {})

	def get_doc(doctype, name):
		if name not in State.queries:
			raise DoesNotExistError_(name)
		return FakeQuery(name)

	def fake_get_all(doctype, filters=None, fields=None, order_by=None,
			limit_start=0, limit_page_length=20, **kwargs):
		"""The permission-BLIND reader, present so a slip to it is catchable.

		frappe.get_all is get_list with permissions off. It exists in the fake
		for one reason: if this module ever reaches for it, the leak tests must
		fail loudly instead of the fake raising AttributeError and looking like
		an unrelated error.
		"""
		rows = [row for row in State.records.get(doctype, [])
			if all(matches(row, condition) for condition in (filters or []))]
		rows = rows[limit_start:limit_start + limit_page_length]
		return [{field: row.get(field) for field in (fields or ["name"])} for row in rows]

	frappe.get_doc = get_doc
	frappe.get_list = fake_get_list
	frappe.get_all = fake_get_all
	frappe.get_meta = FakeMeta
	frappe.has_permission = lambda doctype, ptype=None: State.doctype_read.get(doctype, True)
	frappe.db = types.SimpleNamespace(
		exists=lambda doctype, name=None: (
			name in State.fields if doctype == "DocType" else name in State.queries))
	frappe.throw = lambda message, exc=None: (_ for _ in ()).throw
	sys.modules["frappe"] = frappe
	model = types.ModuleType("frappe.model")
	document = types.ModuleType("frappe.model.document")
	document.Document = type("Document", (), {})
	sys.modules["frappe.model"] = model
	sys.modules["frappe.model.document"] = document
	return frappe


install_fake_frappe()
from ucc_intelligence.analytics import drilldown  # noqa: E402


def reset():
	State.queries = {
		"vc55npin67": {
			"title": "UCC AUTHORED - Stakeholder engagement by status",
			"is_builder_query": 1,
			"use_live_connection": 1,
			"data_source": None,                    # empty, exactly as probed
			"operations": STAKEHOLDER_OPERATIONS,
		},
	}
	State.readable_queries = {"vc55npin67"}
	State.fields = {
		"Stakeholder Engagement Strategy": ("engagement_type", "strategy_title", "status"),
	}
	State.title_fields = {"Stakeholder Engagement Strategy": "strategy_title"}
	State.doctype_read = {"Stakeholder Engagement Strategy": True}
	State.records = {"Stakeholder Engagement Strategy": [
		{"name": "SES-%03d" % index, "engagement_type": kind,
			"strategy_title": "Strategy %d" % index, "status": "Active", "modified": "2026-08-0%d" % (index % 9 + 1)}
		for index, kind in enumerate(["Consultative"] * 40 + ["Collaborative"] * 16
			+ ["Empowering"] * 7 + [""] * 3)]}
	State.hidden = set()
	State.executed = []


def add_query(name, **fields):
	base = {"title": name, "is_builder_query": 1, "use_live_connection": 1,
		"data_source": None, "operations": []}
	base.update(fields)
	State.queries[name] = base
	State.readable_queries.add(name)


# --- it reads the real structure --------------------------------------------
reset()
resolved = drilldown.resolve("vc55npin67")
report(resolved["status"] == "available", "the probed chart resolves: %s" % resolved["status"])
report(resolved["doctype"] == "Stakeholder Engagement Strategy",
	"the DocType comes off the source step's table_name, tab prefix stripped (%s)"
	% resolved["doctype"])
report(resolved["columns"] == ["engagement_type"],
	"the drillable column comes off the summarize step (%s)" % resolved["columns"])

# The top-level field was empty on the real record; the step is where it lives.
report(drilldown._source_of(STAKEHOLDER_OPERATIONS) == (
	"tabStakeholder Engagement Strategy", "Site DB"),
	"data_source is read from the source step, not the empty top-level field")

# --- the records come back, and they are the right ones ---------------------
result = drilldown.records("vc55npin67", "engagement_type", "Consultative", page_size=100)
report(result["status"] == "available", "a segment opens: %s" % result["status"])
report(len(result["records"]) == 40,
	"and returns the 40 records the bar counted (%d)" % len(result["records"]))
report(all(row["engagement_type"] == "Consultative" for row in result["records"]),
	"every returned record really is in that segment")
report("strategy_title" in result["fields"],
	"the DocType's title field is shown, not just the id (%s)" % result["fields"])
report(State.executed == [],
	"NOTHING went through Insights' own SQL -- records come from get_list only")

# --- the leak tests ---------------------------------------------------------
# This is the check the whole module exists for.
reset()
State.doctype_read["Stakeholder Engagement Strategy"] = False
denied = drilldown.records("vc55npin67", "engagement_type", "Consultative")
report(denied["status"] == "permission_denied" and denied["records"] == [],
	"a user who cannot read the DocType gets nothing, and is told why")

reset()
State.hidden = {"SES-%03d" % index for index in range(0, 20)}
partial = drilldown.records("vc55npin67", "engagement_type", "Consultative", page_size=100)
report(len(partial["records"]) == 20,
	"row-level permissions still apply inside a segment (%d of 40 visible)"
	% len(partial["records"]))
report(all(row["name"] not in State.hidden for row in partial["records"]),
	"and not one hidden record is among them")

reset()
State.readable_queries = set()
report(drilldown.records("vc55npin67", "engagement_type", "Consultative")["status"]
	== "permission_denied",
	"a chart the user cannot read cannot be drilled into either")

# A column the chart never grouped by must not become a way to probe values.
reset()
probing = drilldown.records("vc55npin67", "status", "Active")
report(probing["status"] == "unsupported" and probing["records"] == [],
	"a column the chart is not grouped by is refused (%s)" % probing["message"])

# --- what it refuses to guess at --------------------------------------------
reset()
add_query("native", is_builder_query=0, operations=[])
report(drilldown.resolve("native")["status"] == "unsupported",
	"a native SQL query is refused rather than guessed at")

add_query("external", operations=[{"type": "source", "table": {
	"type": "table", "data_source": "Warehouse", "table_name": "tabThing"}}])
external = drilldown.resolve("external")
report(external["status"] == "unsupported" and "outside this site" in external["message"],
	"an external data source is refused -- Frappe cannot permission-check it")

add_query("raw", operations=[{"type": "source", "table": {
	"type": "table", "data_source": "Site DB", "table_name": "some_view"}}])
report(drilldown.resolve("raw")["status"] == "unsupported",
	"a table that is not tab<DocType> is refused")

add_query("joined", operations=[
	STAKEHOLDER_OPERATIONS[0],
	{"type": "join", "table": {"table_name": "tabOther"}},
	STAKEHOLDER_OPERATIONS[1]])
joined = drilldown.resolve("joined")
report(joined["status"] == "unsupported" and "join" in joined["message"],
	"a join is refused -- the records behind a segment are no longer one table's rows")

add_query("computed", operations=[STAKEHOLDER_OPERATIONS[0], {
	"type": "summarize",
	"dimensions": [{"column_name": "month(creation)", "dimension_name": "month"}],
	"measures": []}])
report(drilldown.resolve("computed")["status"] == "unsupported",
	"a calculated dimension is refused -- it cannot be turned back into a filter")

add_query("ungrouped", operations=[STAKEHOLDER_OPERATIONS[0]])
report(drilldown.resolve("ungrouped")["status"] == "unsupported",
	"a chart with no grouping has no segments to open")

report(drilldown.resolve("no-such-chart")["status"] == "unavailable",
	"a chart that no longer exists says so")

# --- the chart's own filters are honoured -----------------------------------
reset()
add_query("filtered", operations=[
	STAKEHOLDER_OPERATIONS[0],
	{"type": "filter", "column": {"column_name": "status"}, "operator": "=", "value": "Active"},
	STAKEHOLDER_OPERATIONS[1]])
State.records["Stakeholder Engagement Strategy"].append(
	{"name": "SES-999", "engagement_type": "Consultative", "strategy_title": "Closed one",
		"status": "Closed", "modified": "2026-08-01"})
kept = drilldown.records("filtered", "engagement_type", "Consultative", page_size=100)
report(all(row.get("status") == "Active" for row in kept["records"])
	and len(kept["records"]) == 40,
	"the chart's own filter steps are applied too, so the list matches the bar")

add_query("weird_filter", operations=[
	STAKEHOLDER_OPERATIONS[0],
	{"type": "filter", "column": {"column_name": "status"}, "operator": "matches_regex", "value": "x"},
	STAKEHOLDER_OPERATIONS[1]])
weird = drilldown.records("weird_filter", "engagement_type", "Consultative")
report(weird["status"] == "unsupported" and weird["records"] == [],
	"an operator it cannot reproduce fails the whole drill-down, showing no records")

# --- paging -----------------------------------------------------------------
reset()
first = drilldown.records("vc55npin67", "engagement_type", "Consultative", page=1, page_size=10)
report(len(first["records"]) == 10 and first["has_more"],
	"a page is a page, and it knows there is another")
second = drilldown.records("vc55npin67", "engagement_type", "Consultative", page=2, page_size=10)
report([row["name"] for row in second["records"]] != [row["name"] for row in first["records"]],
	"page 2 is different records from page 1")
last = drilldown.records("vc55npin67", "engagement_type", "Consultative", page=4, page_size=10)
report(len(last["records"]) == 10 and not last["has_more"], "the last page knows it is the last")
capped = drilldown.records("vc55npin67", "engagement_type", "Consultative", page_size=100000)
report(capped["page_size"] == drilldown.MAX_PAGE_SIZE,
	"an outsized page size is capped at %d, not honoured" % drilldown.MAX_PAGE_SIZE)
report(drilldown.records("vc55npin67", "engagement_type", "Consultative",
	page="x", page_size="y")["status"] == "available",
	"junk paging arguments fall back to the defaults rather than raising")

# --- the blank segment ------------------------------------------------------
blank = drilldown.records("vc55npin67", "engagement_type", "", page_size=100)
report(len(blank["records"]) == 3,
	"clicking the blank segment finds the blank records (%d)" % len(blank["records"]))

# --- it never raises --------------------------------------------------------
reset()
State.records = {}


def boom(*args, **kwargs):
	raise RuntimeError("database on fire")


sys.modules["frappe"].get_list = boom
report(drilldown.records("vc55npin67", "engagement_type", "Consultative")["status"] == "query_error",
	"a failing fetch is a failed drill-down, not a broken tab")
sys.modules["frappe"].get_list = fake_get_list

print("\n%s: %d/%d checks" % ("PASS" if all(checks) else "FAIL", sum(checks), len(checks)))
sys.exit(0 if all(checks) else 1)
