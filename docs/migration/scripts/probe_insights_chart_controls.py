"""ONE chart, every config key at every depth, matched against the 9 unmapped controls.

WHY THIS EXISTS, AND WHY IT IS NOT THE EARLIER CONFIG PROBE
`probe_insights_chart_config.py` dumps every readable chart's config, but only
at the TOP LEVEL. That is a real limitation: Insights v3 nests presentation
options inside their axis, so a control like Normalize or Show Data Labels can
be sitting in `y_axis.normalize` and never appear in a flat key list. A probe
that cannot see a key is indistinguishable from a control that stores nothing,
and those two answers lead to opposite decisions.

So this one walks the config to FULL DEPTH and reports dotted paths.

It also targets ONE chart deliberately. Felix has toggled real, non-default
values on a single chart specifically so the keys can be confirmed rather than
guessed. Averaging that chart in with eight others at their defaults would bury
the signal.

WHAT IT WILL NOT DO
It will not tell you `rotate_values` is the key for "Rotate Values" because the
names look alike. ADR-016: a key inferred from a UI label is a guess, and a
guessed shape is what produced 13 TableNotFound errors earlier in this
migration. Name similarity is reported as a CANDIDATE, never as a confirmation,
and section 5 exists precisely to say "nothing here corresponds to that
control" out loud rather than reaching for the nearest plausible key.

The corroboration that actually settles it is section 4: the same chart's keys
compared against every OTHER chart. A key that exists here and nowhere else,
or holds a different value here, is a key Felix just changed. That is evidence
from the data, not from the English.

RUN
    bench --site <site> console
    >>> exec(open("/home/felixoking/ucc-sms-v2/docs/migration/scripts/probe_insights_chart_controls.py").read(), globals())
    ...prints the list of charts...
    >>> ucc_probe("the-id-from-the-first-column")

THE ID IS AN ARGUMENT, NOT A VARIABLE, AND THAT IS THE POINT
The first version read UCC_PROBE_CHART out of globals(). Under `bench console`
the name typed at the prompt can land in a namespace that is NOT the dict
exec() is handed, so the variable was genuinely set, printable by name, and
invisible to this script at the same time. An argument cannot be looked up in
the wrong place. chart_id_from_caller() still honours the old variable so
nobody following the earlier instructions is silently ignored, but it is a
courtesy, not the mechanism.

SAFETY
Read-only. Creates nothing, changes nothing, executes nothing, writes nothing
back to any record.
"""

import inspect
import json

import frappe

CHART_DOCTYPE = "Insights Chart v3"

# Everything chart_presentation.py reads today, or has deliberately decided not
# to read. A key outside this set is the interesting kind.
KNOWN_KEYS = (
	"chart_type", "x_axis", "y_axis", "legend_position", "axis_label", "stack",
	"filters", "limit", "order_by", "value_column", "label_column",
	"label_position", "number_columns", "number_column_options",
	"date_column", "location_column", "size_column", "source_column",
	"target_column", "show_inline_labels",
)

# The nine controls with no confirmed key name, and what a real value for each
# would LOOK like. The shape is the useful half: a control that stores a number
# cannot be a key holding True, however well the names match.
CONTROLS = (
	("Rotate Values", "a number of degrees (45, 90) or a string like '45'"),
	("Overlap", "a boolean, or a number if it is an overlap percentage"),
	("Normalize", "a boolean"),
	("Show Data Labels", "a boolean"),
	("Show Axis Label (the toggle, not the label text)", "a boolean"),
	("Show Scrollbar", "a boolean"),
	("Y-Min", "a number"),
	("Y-Max", "a number"),
	("Split Series", "a boolean, or a column name"),
)

# Used only to SHORTLIST candidates for a human to judge. Never to conclude.
#
# Each entry is a tuple of ALTERNATIVES; each alternative is a set of words that
# must ALL appear as whole tokens in the path. Substring matching was the first
# attempt and it was useless -- searching for "y" made `chart_type` a candidate
# for Y-Min, and "bar" made `show_scrollbar` a candidate for everything. A
# shortlist that lists everything is not a shortlist.
CONTROL_WORDS = {
	"Rotate Values": (("rotate",), ("angle",), ("tilt",)),
	"Overlap": (("overlap",),),
	"Normalize": (("normalize",), ("normalise",), ("percent",), ("stack", "100")),
	"Show Data Labels": (("data", "labels"), ("data", "label"), ("inline", "labels")),
	"Show Axis Label (the toggle, not the label text)":
		(("axis", "label"), ("axis", "labels"), ("axislabel",)),
	"Show Scrollbar": (("scrollbar",), ("scroll",), ("zoom",), ("slider",)),
	"Y-Min": (("min",), ("ymin",)),
	"Y-Max": (("max",), ("ymax",)),
	"Split Series": (("split",), ("breakdown",)),
}


def tokens_of(path):
	"""`y_axis.series[0].show_data_labels` -> the words in it, no punctuation."""
	cleaned = path.lower()
	for character in "._[]":
		cleaned = cleaned.replace(character, " ")
	return [token for token in cleaned.split() if not token.isdigit()]


def matches(path, alternatives):
	"""True when every word of ANY alternative is a whole token in the path."""
	tokens = tokens_of(path)
	for words in alternatives:
		if all(any(token == word or token.startswith(word) for token in tokens)
				for word in words):
			return True
	return False


def head(number, title):
	print("\n" + "=" * 74)
	print("%s. %s" % (number, title))
	print("=" * 74)


def config_of(row):
	raw = row.get("config")
	if isinstance(raw, dict):
		return raw
	try:
		parsed = json.loads(raw or "{}")
	except Exception:
		return {}
	return parsed if isinstance(parsed, dict) else {}


def walk(node, prefix=""):
	"""Every (dotted path, value) in the config, to full depth.

	Flat key listing is what would hide `y_axis.normalize`. Lists are indexed so
	a per-series option keeps the series it belongs to.
	"""
	out = []
	if isinstance(node, dict):
		for key in sorted(node):
			path = "%s.%s" % (prefix, key) if prefix else str(key)
			out.append((path, node[key]))
			out.extend(walk(node[key], path))
	elif isinstance(node, (list, tuple)):
		for index, item in enumerate(node):
			path = "%s[%d]" % (prefix, index)
			if isinstance(item, (dict, list, tuple)):
				out.extend(walk(item, path))
			else:
				out.append((path, item))
	return out


def describe(value):
	"""Value AND type. A key is only usable once both are known."""
	if isinstance(value, (dict, list)):
		return "%-7s %s" % (type(value).__name__, json.dumps(value, default=str)[:96])
	return "%-7s %r" % (type(value).__name__, value)


def leaf_paths(config):
	"""Paths whose value is a scalar -- the ones a control could be stored in."""
	return [(path, value) for path, value in walk(config)
		if not isinstance(value, (dict, list, tuple))]


def chart_id_from_caller():
	"""UCC_PROBE_CHART, wherever the console actually put it.

	globals() alone was NOT enough, and this cost Felix a round trip. Under
	`bench console` the name typed at the prompt can land in a namespace that
	is not the dict exec() is handed, so the variable was genuinely set,
	printable by name, and invisible to this script at the same time -- three
	facts that look contradictory and are not.

	So it looks in every namespace up the call stack rather than reasoning
	about which dict IPython uses in which version. And the real fix is not
	this function at all: ucc_probe("the-id") takes the id as an ARGUMENT,
	which cannot be looked up in the wrong place. This exists only so that
	someone following the older instructions is not silently ignored.
	"""
	value = globals().get("UCC_PROBE_CHART")
	if value:
		return value
	frame = inspect.currentframe()
	while frame:
		for namespace in (frame.f_locals, frame.f_globals):
			value = namespace.get("UCC_PROBE_CHART")
			if value:
				return value
		frame = frame.f_back
	return ""


def ucc_probe(chart_id=""):
	"""Run the probe. Pass the chart id: ucc_probe("o2kvutcfld")."""
	if not frappe.db.exists("DocType", CHART_DOCTYPE):
		print("STOP -- %s is not installed on this site." % CHART_DOCTYPE)
		return

	chart_id = (chart_id or chart_id_from_caller() or "").strip()
	all_rows = frappe.get_list(CHART_DOCTYPE,
		fields=["name", "title", "chart_type", "config", "modified"],
		order_by="modified desc", limit_page_length=0) or []

	if not chart_id:
		head(0, "NO CHART CHOSEN -- pick one from this list")
		print("   Most recently changed first, so the chart you just saved is")
		print("   almost certainly at the top.\n")
		for row in all_rows[:15]:
			print("   %-14s %-40s %-9s %s" % (row["name"],
				(row.get("title") or "(untitled)")[:38],
				row.get("chart_type") or "?", row.get("modified")))
		print("\n   Copy its id from the FIRST column, then run ONE line -- no")
		print("   need to paste the long exec line again:\n")
		print('       ucc_probe("paste-the-id-here")')
		return

	found = next((row for row in all_rows if row["name"] == chart_id), None)
	if not found:
		print("STOP -- no chart %r is readable by this user." % chart_id)
		print("       Either the id is wrong, or your account cannot read it.")
		print("       Run ucc_probe() with no id to list what you can see.")
		return

	config = config_of(found)
	paths = walk(config)
	leaves = leaf_paths(config)

	head(1, "THE CHART, AND ITS CONFIG IN FULL")
	print("   id          %s" % found["name"])
	print("   title       %s" % (found.get("title") or "(untitled)"))
	print("   chart_type  %s" % (found.get("chart_type") or "?"))
	print("   modified    %s" % found.get("modified"))
	print("   config keys %d at top level, %d paths at full depth\n"
		% (len(config), len(paths)))
	if not config:
		print("   config is EMPTY. Nothing was saved on this chart -- check you")
		print("   pressed save in Insights, and that this is the right chart.")
		return
	print("   raw JSON, verbatim:")
	print("   " + json.dumps(config, indent=2, default=str, sort_keys=True).replace("\n", "\n   "))

	head(2, "EVERY PATH, FLAGGED KNOWN OR NEW")
	print("   NEW means chart_presentation.py does not read it. Nested paths are")
	print("   dotted -- a control stored inside its axis would be invisible to a")
	print("   flat key list, which is why this walks to full depth.\n")
	for path, value in paths:
		top = path.split(".")[0].split("[")[0]
		mark = "known" if top in KNOWN_KEYS and "." not in path else "NEW"
		print("   %-6s %-34s %s" % (mark, path, describe(value)))

	head(3, "THE NINE CONTROLS -- WHAT WAS FOUND FOR EACH")
	print("   A CANDIDATE is a name that looks related. It is NOT a confirmation.")
	print("   Read its value against the 'expects' line: a control that stores a")
	print("   number cannot be a key holding True, however well the names match.\n")
	unresolved = []
	for control, expects in CONTROLS:
		alternatives = CONTROL_WORDS[control]
		hits = [(path, value) for path, value in leaves
			if matches(path, alternatives)]
		print("   %s" % control)
		print("       expects: %s" % expects)
		if hits:
			for path, value in hits[:6]:
				print("       CANDIDATE  %-30s %s" % (path, describe(value)))
		else:
			print("       NO KEY IN THIS CONFIG HAS A NAME RESEMBLING THIS CONTROL.")
			print("       Either it is stored under an unrelated name -- check")
			print("       section 4 -- or it is not stored in config at all.")
			unresolved.append(control)
		print()

	head(4, "CORROBORATION -- what is different about THIS chart")
	print("   The evidence that actually settles a key is not its name. It is")
	print("   that this chart has it and the others do not, because Felix just")
	print("   changed it here. Match a value you set against a path below.\n")
	others = [row for row in all_rows if row["name"] != chart_id]
	other_paths = set()
	for row in others:
		other_paths.update(path for path, _value in walk(config_of(row)))
	only_here = [(path, value) for path, value in leaves if path not in other_paths]
	if only_here:
		print("   Paths present on THIS chart and on no other (%d chart(s) compared):"
			% len(others))
		for path, value in only_here:
			print("       %-34s %s" % (path, describe(value)))
	else:
		print("   No path is unique to this chart. Every key it carries, the other")
		print("   charts carry too -- so the controls either write nothing, or")
		print("   write into keys that already existed at their defaults. In that")
		print("   case compare the VALUES below rather than the key names.")
	print()
	differing = []
	for path, value in leaves:
		elsewhere = set()
		for row in others:
			for other_path, other_value in leaf_paths(config_of(row)):
				if other_path == path and not isinstance(other_value, (dict, list)):
					elsewhere.add(repr(other_value))
		if elsewhere and repr(value) not in elsewhere:
			differing.append((path, value, sorted(elsewhere)[:3]))
	if differing:
		print("   Paths whose VALUE here differs from every other chart's:")
		for path, value, elsewhere in differing:
			print("       %-30s here=%-14r elsewhere=%s" % (path, value, ", ".join(elsewhere)))
	else:
		print("   No path differs in value from the other charts either.")

	head(5, "WHAT THIS PROBE COULD NOT ANSWER")
	if unresolved:
		print("   These controls have NO key in this chart's config whose name")
		print("   resembles them. Stated plainly rather than matched to the")
		print("   nearest plausible key:\n")
		for control in unresolved:
			print("   - %s" % control)
		print("\n   For each, one of three things is true, and section 4 usually")
		print("   distinguishes them:")
		print("     a) it is stored under an unrelated name -- look for it in the")
		print("        'unique to this chart' or 'differs in value' lists above;")
		print("     b) it is not stored in `config` at all but on the Chart record")
		print("        itself, or in the workbook -- a different probe;")
		print("     c) the control was not actually saved. Re-check in Insights.")
	else:
		print("   Every one of the nine has at least a candidate. None of them is")
		print("   confirmed by that alone -- check each value against its")
		print("   'expects' line and against section 4 before anything is wired.")

	head(6, "WHAT TO SEND BACK")
	print("   All of it, sections 1 to 5. Section 1's raw JSON is the part that")
	print("   settles things; the rest is this script's reading of it, and a")
	print("   reading can be wrong in a way the raw record cannot.")


ucc_probe()
