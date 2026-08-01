"""Which keys an Insights Chart v3 `config` ACTUALLY contains.

WHY THIS EXISTS
`chart_presentation.py` reads six keys, confirmed by the 2026-08-02 probe:

    chart_type, x_axis, y_axis, legend_position, axis_label, stack

The v3 builder exposes more controls than that -- Rotate Values, Overlap,
Normalize, Show Data Labels, the Show Axis Label toggle, Show Scrollbar, Y-Min,
Y-Max, Split Series. Each presumably writes SOMETHING into `config`. What it
writes is unknown, because the builder shows UI LABELS and a label is not a
field name.

Guessing `rotate_values` from "Rotate Values" is exactly the class of mistake
that produced 13 TableNotFound errors earlier in this migration: a shape
written from plausibility rather than copied from a version proven on a bench.
So nothing is implemented for these controls. This prints what is really in
there, and the implementation follows the output.

HOW TO GET A USEFUL ANSWER
An unset control may write nothing at all, so a chart with everything left at
its default will not reveal much. Build (or edit) ONE chart in Insights with as
many of those controls turned on or changed as the chart type allows, save it,
then run this. Section 3 lists every key that is not already known, which is
precisely the list worth implementing.

RUN
    bench --site <site> console
    >>> exec(open("/home/felixoking/Intelligence-Dashboard-v2/docs/migration/scripts/probe_insights_chart_config.py").read(), globals())

SAFETY
Read-only. Creates nothing, changes nothing, executes nothing.
"""

import json

import frappe

CHART_DOCTYPE = "Insights Chart v3"

# What chart_presentation.py already reads. Everything else is the answer.
KNOWN_KEYS = ("chart_type", "x_axis", "y_axis", "legend_position", "axis_label", "stack")

# The controls with no confirmed key name. Listed so the output can be read
# against them directly rather than from memory of the builder UI.
UNMAPPED_CONTROLS = (
	"Rotate Values", "Overlap", "Normalize", "Show Data Labels",
	"Show Axis Label (the toggle, not the label text)", "Show Scrollbar",
	"Y-Min", "Y-Max", "Split Series",
)


def head(number, title):
	print("\n" + "=" * 72)
	print("%s. %s" % (number, title))
	print("=" * 72)


def config_of(row):
	raw = row.get("config")
	if isinstance(raw, dict):
		return raw
	try:
		parsed = json.loads(raw or "{}")
	except Exception:
		return {}
	return parsed if isinstance(parsed, dict) else {}


def describe(value):
	"""The value AND its type -- a key is only usable once both are known."""
	if isinstance(value, (dict, list)):
		text = json.dumps(value, default=str)
		return "%-8s %s" % (type(value).__name__, text[:110])
	return "%-8s %r" % (type(value).__name__, value)


def run():
	if not frappe.db.exists("DocType", CHART_DOCTYPE):
		print("STOP -- %s is not installed on this site." % CHART_DOCTYPE)
		return

	rows = frappe.get_list(
		CHART_DOCTYPE,
		fields=["name", "title", "chart_type", "config"],
		order_by="modified desc",
		limit_page_length=0,
	) or []

	head(1, "EVERY CHART'S CONFIG, IN FULL")
	print("   %d chart(s) readable by this user.\n" % len(rows))
	for row in rows:
		config = config_of(row)
		print("   --- %s | %s | type=%s ---" % (
			row["name"], (row.get("title") or "(untitled)")[:44], row.get("chart_type") or "?"))
		if not config:
			print("      config is empty\n")
			continue
		for key in sorted(config):
			print("      %-24s %s" % (key, describe(config[key])))
		print()

	head(2, "EVERY KEY SEEN, AND WHERE")
	seen = {}
	for row in rows:
		for key, value in config_of(row).items():
			seen.setdefault(key, []).append((row["name"], row.get("chart_type") or "?", value))
	for key in sorted(seen):
		mark = "known" if key in KNOWN_KEYS else "NEW"
		charts = seen[key]
		print("   %-24s %-6s in %d chart(s)" % (key, mark, len(charts)))
		for name, chart_type, value in charts[:3]:
			print("        %-14s %-8s %s" % (name, chart_type, describe(value)[:90]))

	head(3, "THE ANSWER: KEYS NOT YET READ BY chart_presentation.py")
	unknown = [key for key in sorted(seen) if key not in KNOWN_KEYS]
	if unknown:
		for key in unknown:
			print("   %s" % key)
		print("\n   These are implementable -- the name and the value type are now")
		print("   both established from real records.")
	else:
		print("   none. Either every control is at its default, or v3 does not")
		print("   store them in `config` at all.")
		print("\n   If it is the former: open ONE chart in Insights, change as many")
		print("   of the controls below as its type allows, save, and re-run this.")

	head(4, "CONTROLS STILL WITHOUT A CONFIRMED KEY")
	print("   Nothing is implemented for these, deliberately. A key inferred")
	print("   from a UI label is a guess, and guessing a shape is what produced")
	print("   the 13 TableNotFound errors earlier in this migration.\n")
	for control in UNMAPPED_CONTROLS:
		print("   - %s" % control)
	print("\n   Match them against section 3 by hand. A control that appears")
	print("   there under some other name is ready to implement; one that")
	print("   appears nowhere is not stored in config and needs a different")
	print("   probe entirely.")


run()
