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


# --- HOW THE CHART ID GETS IN -------------------------------------------
#
# The first version read UCC_PROBE_CHART out of globals(). Under `bench
# console` the name typed at the prompt lands in a namespace that is NOT the
# dict exec() is handed, so Felix's variable was genuinely set, printable by
# name, and invisible to the probe at the same time. It printed "NO CHART
# CHOSEN" at someone who had chosen one.
#
# The fix is that the id is an ARGUMENT -- an argument cannot be looked up in
# the wrong namespace. The frame walk stays only so the older instructions are
# not silently ignored, and it is checked HERE, from a namespace the probe's
# globals() genuinely cannot see. Asserting that precondition is the point: a
# test that put the variable in the exec globals would pass against the bug.
ucc_probe = probe["ucc_probe"]
chart_id_from_caller = probe["chart_id_from_caller"]
seen = {}
probe["frappe"].get_list = lambda doctype, **kwargs: [
	{"name": "o2kvutcfld", "title": "Innovation type mix", "chart_type": "Donut",
		"modified": "2026-08-03", "config": '{"chart_type": "Donut"}'}]


def capture(*args):
	"""Run the probe and return what it printed."""
	import io
	import contextlib
	buffer = io.StringIO()
	with contextlib.redirect_stdout(buffer):
		ucc_probe(*args)
	return buffer.getvalue()


report("NO CHART CHOSEN" in capture(), "with no id at all, it lists the charts")
report("o2kvutcfld" in capture("o2kvutcfld") and "NO CHART CHOSEN" not in capture("o2kvutcfld"),
	"an id passed as an ARGUMENT is used -- the path that cannot be looked up wrong")


def like_an_ipython_cell():
	UCC_PROBE_CHART = "o2kvutcfld"  # noqa: F841  -- local, as at the prompt
	assert "UCC_PROBE_CHART" not in probe, "precondition: not in the exec globals"
	return chart_id_from_caller(), capture()


found, output = like_an_ipython_cell()
report(found == "o2kvutcfld",
	"the old variable is still honoured from a namespace globals() cannot see")
report("NO CHART CHOSEN" not in output,
	"...so someone following the earlier instructions is not told they chose nothing")
report("UCC_PROBE_CHART" not in probe,
	"and the probe never wrote the name into its own globals to make that work")


# --- THE DECLARED PATHS -------------------------------------------------
#
# The 2026-08-03 run found nothing for seven of the nine, and the reason was
# not that Insights stores them elsewhere. It was that the probed chart was a
# DONUT, and all nine are axis-chart keys. The expected paths below are copied
# from Insights' chart.types.ts, so the probe now checks a path instead of
# hoping a name matches -- and `x_axis.label_rotation` is the proof it needed
# to: "rotation".startswith("rotate") is False, so the name matcher would have
# reported Rotate Values ABSENT on a chart that had it.
CONTROLS = dict((control, expected) for control, expected, _hint in probe["CONTROLS"])
report(CONTROLS["Rotate Values"] == "x_axis.label_rotation",
	"Rotate Values is checked at x_axis.label_rotation, per chart.types.ts")
report(CONTROLS["Y-Min"] == "y_axis.min" and CONTROLS["Y-Max"] == "y_axis.max",
	"...Y-Min/Y-Max at y_axis.min / y_axis.max, NOT y_min / y_max")
report(CONTROLS["Split Series"] == "split_by", "...Split Series at split_by")
report(not matches("x_axis.label_rotation", probe["CONTROL_WORDS"]["Rotate Values"]),
	"the NAME matcher misses label_rotation -- which is why the path is checked")

donut = {"chart_type": "Donut", "label_column": {"column_name": "t", "data_type": "String"},
	"x_axis": {"dimension": {"label": "status"}}, "label_position": "left"}
bar = {"chart_type": "Bar", "x_axis": {"dimension": {"column_name": "s"}, "label_rotation": 45},
	"y_axis": {"series": [{"show_data_labels": True}], "min": 10, "max": 250,
		"normalize": True, "show_axis_label": True, "show_scrollbar": True,
		"show_data_labels": True},
	"split_by": {"dimension": {"column_name": "programme"}}}
donut_paths = dict(walk(donut))
bar_paths = dict(walk(bar))
report(not any(path in donut_paths for path in CONTROLS.values()),
	"a Donut carries NONE of the nine -- the correct answer, not a failed search")
missing_on_bar = [c for c, path in CONTROLS.items() if path not in bar_paths]
report(missing_on_bar == ["Overlap"],
	"a Bar carries all of them (only Overlap left unset here): missing=%s" % missing_on_bar)

probe["frappe"].get_list = lambda doctype, **kwargs: [
	{"name": "d1", "title": "Donut", "chart_type": "Donut", "modified": "2026-08-03",
		"config": __import__("json").dumps(donut)}]
donut_output = capture("d1")
report("ALL NINE ARE AXIS-CHART KEYS" in donut_output,
	"...and the probe SAYS so on a Donut, instead of reporting nine mysteries")
report("CANDIDATE    label_column.data_type" in donut_output,
	"the data_type false match still shows -- as a candidate beside an ABSENT path")
report("       PRESENT " not in donut_output and donut_output.count("       ABSENT ") == 9,
	"...and all nine are reported ABSENT at their declared path, none PRESENT")

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
