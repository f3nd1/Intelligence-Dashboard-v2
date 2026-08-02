#!/usr/bin/env python3
"""Self-check for docs/migration/scripts/probe_insights_chart_controls.py.

    python3 tools/test_probe_chart_controls.py

WHY A PROBE NEEDS ITS OWN TEST
A probe is read as evidence. The last two rounds both turned on a probe that
was confidently wrong -- one declared a Donut healthy because bool({}) is True,
and the filter check tested shapes that only existed in my head. A probe that
disagrees with reality is worse than no probe, because it is believed.

This one is checked on the two things it can get wrong on its own:

  walk()    must reach NESTED paths. A flat key listing would miss
            `y_axis.normalize` entirely, and "not found" and "not looked for"
            are indistinguishable in the output while leading to opposite
            decisions.
  matches() must not shortlist everything. The first version searched for the
            substring "y", which made `chart_type` a candidate for Y-Min, and
            "bar", which made `show_scrollbar` a candidate for Show Data
            Labels. A shortlist that lists everything is not a shortlist.

The config below is INVENTED. It proves the probe's mechanics, and nothing
whatever about what Insights really stores -- that answer only comes from the
bench, which is the entire point of the probe existing.
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROBE = ROOT / "docs/migration/scripts/probe_insights_chart_controls.py"

checks = []


def report(ok, message):
	checks.append(bool(ok))
	print(("PASS" if ok else "FAIL") + ": " + message)
	return bool(ok)


# The probe imports frappe at module scope and calls run() at the bottom, so it
# is loaded with a frappe that has no charts -- run() prints the "pick one" list
# and returns, leaving the functions available to test.
frappe = types.ModuleType("frappe")
frappe.db = types.SimpleNamespace(exists=lambda *a, **k: True)
frappe.get_list = lambda *a, **k: []
sys.modules["frappe"] = frappe

probe = {"__name__": "ucc_probe_under_test"}
_stdout = sys.stdout
sys.stdout = open("/dev/null", "w")
exec(PROBE.read_text(), probe)
sys.stdout.close()
sys.stdout = _stdout

walk = probe["walk"]
matches = probe["matches"]
tokens_of = probe["tokens_of"]
CONTROL_WORDS = probe["CONTROL_WORDS"]

NESTED = {
	"chart_type": "Bar",
	"y_axis": {
		"series": [{"column_name": "count", "show_data_labels": True}],
		"normalize": True, "y_min": 10, "y_max": 250,
	},
	"rotate_x_labels": 45,
}

paths = dict(walk(NESTED))
report("y_axis.normalize" in paths and paths["y_axis.normalize"] is True,
	"walk() reaches a key nested inside its axis")
report("y_axis.series[0].show_data_labels" in paths,
	"...and one nested inside a list, keeping the series it belongs to")
report("y_axis.series[0].column_name" in paths,
	"...with the index in the path, so per-series options stay distinguishable")

# The shortlist must be a shortlist. Each of these was a real false positive
# from the substring version.
report(not matches("chart_type", CONTROL_WORDS["Y-Min"]),
	"chart_type is NOT a Y-Min candidate (the letter 'y' is not a word)")
report(not matches("show_scrollbar", CONTROL_WORDS["Show Data Labels"]),
	"show_scrollbar is NOT a Show Data Labels candidate ('bar' is not 'labels')")
report(not matches("x_axis.column_name", CONTROL_WORDS[
	"Show Axis Label (the toggle, not the label text)"]),
	"x_axis.column_name is NOT a Show Axis Label candidate -- 'label' is absent")
report(not matches("y_axis.y_max", CONTROL_WORDS["Y-Min"]),
	"y_max is NOT a Y-Min candidate")

# ...and it must still find the real ones.
report(matches("y_axis.y_min", CONTROL_WORDS["Y-Min"]), "y_min IS a Y-Min candidate")
report(matches("y_axis.y_max", CONTROL_WORDS["Y-Max"]), "y_max IS a Y-Max candidate")
report(matches("rotate_x_labels", CONTROL_WORDS["Rotate Values"]),
	"rotate_x_labels IS a Rotate Values candidate")
report(matches("y_axis.series[0].show_data_labels", CONTROL_WORDS["Show Data Labels"]),
	"show_data_labels IS a Show Data Labels candidate, nested and all")
report(matches("y_axis.normalize", CONTROL_WORDS["Normalize"]),
	"normalize IS a Normalize candidate")
report(matches("show_scrollbar", CONTROL_WORDS["Show Scrollbar"]),
	"show_scrollbar IS a Show Scrollbar candidate")

report(tokens_of("y_axis.series[0].show_data_labels")
	== ["y", "axis", "series", "show", "data", "labels"],
	"tokens_of() splits on dots, brackets and underscores and drops the index")

# The probe must not write. Asserted by source, because a probe that edits the
# thing it is measuring is the worst possible tool.
source = PROBE.read_text()
forbidden = [name for name in ("frappe.get_doc", ".save(", ".insert(", ".db.set_value",
		"frappe.delete_doc", ".db.sql")
	if name in source]
report(not forbidden, "the probe writes nothing: %s" % (forbidden or "no write calls"))
report("frappe.get_list" in source, "...and reads through get_list, which applies permissions")

print("\n%s: %d/%d checks" % ("PASS" if all(checks) else "FAIL", sum(checks), len(checks)))
sys.exit(0 if all(checks) else 1)
