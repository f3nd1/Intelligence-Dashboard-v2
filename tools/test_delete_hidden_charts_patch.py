#!/usr/bin/env python3
"""Self-check for the patch that deletes charts hidden under embedded dashboards.

    python3 tools/test_delete_hidden_charts_patch.py

WHY THIS EXISTS
This patch DELETES institutional configuration, once, on a real site. A
structural check that the file is listed in patches.txt proves it will be
called, not that it removes the right rows -- and the two ways it can be wrong
are opposite disasters: leaving hidden charts behind (the instruction not
carried out) or emptying tabs that are still using their charts (visible
content destroyed). Both are asserted here, against a fake site, before it ever
runs against a real one.
"""
import json
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]

checks = []


def report(ok, message):
	checks.append(bool(ok))
	print(("PASS" if ok else "FAIL") + ": " + message)
	return bool(ok)


# --- a fake site holding UCC Analytics Tab rows ------------------------------
class Site:
	rows = []
	writes = []       # every db.set_value call, in order
	logged = []
	table = True


def get_all(doctype, fields=None, filters=None, order_by=None):
	assert doctype == "UCC Analytics Tab", doctype
	rows = Site.rows
	# The patch filters on embedded_dashboard != "". Applied here rather than
	# ignored, so a patch that dropped the filter and swept every tab would
	# fail this test instead of passing it.
	for field, (operator, value) in (filters or {}).items():
		assert operator == "!=", operator
		rows = [row for row in rows if row.get(field) != value]
	return [dict(row) for row in rows]


def set_value(doctype, name, field, value, update_modified=True):
	Site.writes.append((doctype, name, field, value))
	for row in Site.rows:
		if row["name"] == name:
			row[field] = value


class Logger:
	def info(self, message):
		Site.logged.append(("info", message))

	def warning(self, message):
		Site.logged.append(("warning", message))


frappe = types.ModuleType("frappe")
frappe.get_all = get_all
frappe.db = types.SimpleNamespace(
	table_exists=lambda doctype: Site.table, set_value=set_value)
frappe.logger = lambda: Logger()
sys.modules["frappe"] = frappe

sys.path.insert(0, str(ROOT / "ucc_intelligence"))
from ucc_intelligence.patches.v1_0 import delete_charts_under_embedded_dashboards as patch  # noqa: E402


def charts(*ids):
	return json.dumps([{"chart": name, "span": 6} for name in ids])


def reset():
	Site.rows = [
		# hidden under an embed -- these go
		{"name": "criterion_4::overview", "criterion": "criterion_4", "tab": "overview",
			"charts": charts("q-innovation", "q-quality"), "embedded_dashboard": "d-1"},
		{"name": "criterion_2::2.1.1", "criterion": "criterion_2", "tab": "2.1.1",
			"charts": charts("q-agents"), "embedded_dashboard": "d-2"},
		# embedded already, nothing stored -- untouched, and not a write
		{"name": "criterion_1::overview", "criterion": "criterion_1", "tab": "overview",
			"charts": "[]", "embedded_dashboard": "d-3"},
		# ON SCREEN: charts, no dashboard. Must survive.
		{"name": "criterion_5::5.1.1", "criterion": "criterion_5", "tab": "5.1.1",
			"charts": charts("q-intake", "q-fees"), "embedded_dashboard": ""},
		# neither -- nothing to do
		{"name": "criterion_7::overview", "criterion": "criterion_7", "tab": "overview",
			"charts": "[]", "embedded_dashboard": ""},
	]
	Site.writes = []
	Site.logged = []
	Site.table = True


# --- it deletes exactly the unreachable ones --------------------------------
reset()
patch.execute()

emptied = {name for _, name, field, value in Site.writes if field == "charts" and value == "[]"}
report(emptied == {"criterion_4::overview", "criterion_2::2.1.1"},
	"exactly the tabs that embed a dashboard AND stored charts are emptied")
report(all(field == "charts" for _, _, field, _ in Site.writes),
	"...and nothing else on those records is written -- not the intro, not the dashboard")

surviving = {row["name"]: row["charts"] for row in Site.rows}
report(json.loads(surviving["criterion_5::5.1.1"]) != [],
	"a tab with charts and NO dashboard keeps them -- those are on screen and working")
report(len(Site.writes) == 2,
	"a tab that already had nothing stored is not rewritten for the sake of it")

# Real deletion, not a filter on the way out.
report(json.loads(surviving["criterion_4::overview"]) == []
	and json.loads(surviving["criterion_2::2.1.1"]) == [],
	"the stored value itself becomes empty -- the charts are gone, not hidden further")

# --- the record of what went ------------------------------------------------
lines = " | ".join(message for _, message in Site.logged)
report("3 painted chart(s) from 2 tab(s)" in lines,
	"the count of what was deleted is logged")
report("criterion_4 / overview -- q-innovation, q-quality" in lines
	and "criterion_2 / 2.1.1 -- q-agents" in lines,
	"...and every deleted chart is named against its tab, so there is a record")

# --- run twice: the second finds nothing ------------------------------------
Site.writes = []
Site.logged = []
patch.execute()
report(Site.writes == [], "a second run writes nothing -- the patch is idempotent")
report(any("nothing to delete" in message for _, message in Site.logged),
	"...and says so rather than reporting a deletion it did not make")

# --- damaged data does not stop the cleanup ---------------------------------
reset()
Site.rows.insert(0, {"name": "criterion_3::overview", "criterion": "criterion_3",
	"tab": "overview", "charts": "{not json", "embedded_dashboard": "d-9"})
patch.execute()
report({name for _, name, _, _ in Site.writes} == {"criterion_4::overview", "criterion_2::2.1.1"},
	"a row with unreadable JSON is skipped, and the rest of the cleanup still runs")
report(any(level == "warning" for level, _ in Site.logged),
	"...and the skipped row is reported rather than silently passed over")

# --- a site without the table -----------------------------------------------
reset()
Site.table = False
patch.execute()
report(Site.writes == [],
	"a site without the tab table is left alone instead of raising during migrate")

print("\n" + ("PASS" if all(checks) else "FAIL")
	+ ": %d/%d checks" % (sum(checks), len(checks)))
sys.exit(0 if all(checks) else 1)
