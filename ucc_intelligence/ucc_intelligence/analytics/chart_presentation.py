# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt
"""How a chart should LOOK, read from its Insights Chart v3 record.

THE PROBLEM
Sophia's tabs embed `Insights Query v3` records. A Query carries data and
nothing else -- no chart type, no axis assignment, no labels -- which is why
every embedded chart rendered as a table. All of that lives on a separate
`Insights Chart v3` record that Sophia never read.

WHAT THE LIVE PROBE ESTABLISHED (2026-08-02, probe_insights_chart_v3.py)
Read off the bench, not from source or memory:

    Insights Chart v3 fields:
        title, workbook, query (Link -> Insights Query v3),
        data_query (Link -> Insights Query v3), sort_order, folder,
        chart_type (Data -- FREE TEXT, not a Select), is_public,
        config (JSON), old_name

    config holds: chart_type, x_axis, y_axis, legend_position, axis_label,
                  stack, limit, order_by, filters

HOW A CHART IS MADE (recorded 2026-08-02, from Felix using the real builder)
Not from inside a Query, which is what this module first assumed. Charts are
their own section in the Insights sidebar -- Queries / Charts / Dashboards --
and a Chart is created there and then pointed at a Query with a dropdown. That
is why `query` and `data_query` are Link fields on the Chart rather than the
Query holding a chart: the Chart points at the Query, never the reverse.

WHAT THE 2026-08-03 CONFIG PROBE SETTLED (probe_insights_chart_config.py)
16 real keys across 9 live charts. What each one does about it, and why:

  READ AND HONOURED
    chart_type, x_axis, y_axis, legend_position, axis_label  (as before)
    limit    -> the series is truncated to it and the card says so. A number
                is a number; there is nothing to misread.
    filters  -> if the chart carries ANY, the chart is WITHHELD and the table
                is shown instead. Sophia executes the QUERY, not the chart, so
                a chart filter is not applied to these rows -- drawing anyway
                would put more data on the card than Insights shows for the
                same chart. On a dashboard used as EduTrust evidence that is
                not a cosmetic difference. See "filters" below.

                THE STORED SHAPE IS A GROUP, NOT A LIST. Confirmed by direct
                database query on the live site:

                    {"filters": [], "logical_operator": "And"}

                is what a chart with NO filters carries. Counting it as "has
                filters" withheld every chart on the platform. filter_count()
                walks the group; nothing here tests the value's shape.

  A NOTE ON NAMES
    The contract calls the resolved axes `x_column` and `y_columns`, NOT
    `label_column`/`value_columns`. Insights has its own `label_column` and
    `value_column` keys which are deliberately unread, and two different things
    under one name is how a "not read" rule quietly stops being true.

  DELIBERATELY NOT READ -- the key name is confirmed, the MEANING is not
    order_by            re-sorting on a misread shape silently reorders an
                        evidence chart, and a wrong order looks like a finding
    label_position      no evidence of what it positions
    number_column_options   no evidence of what it configures

  READ SINCE 2026-08-03, ON EVIDENCE
    label_column, value_column, number_columns -- these were refused on
    2026-08-03 because nothing corroborated their meaning beyond their names.
    Felix's Donut then produced the corroboration: its x_axis is
    {"dimension": {}} (empty) while label_column holds "benchmark_type", a
    real column its query returns. A chart type whose ONLY populated axis key
    is that one, holding a real column name, is evidence -- not a name guess.
    See axis_keys_for().
    date_column         no confirmation it is an x-axis rather than, say, a
                        filter field or a granularity control
    location_column     configures Map
    size_column         configures Bubble
    source_column       \ configure Sankey
    target_column       /
    show_inline_labels  seen on one chart as a bool. It MIGHT be "Show Data
                        Labels". Wiring it on the strength of its name is the
                        exact move ADR-016 forbids.

  The four Map/Bubble/Sankey keys will stay unread even once confirmed: those
  chart types are refusals, not gaps (see SUPPORTED_TYPES), so reading their
  configuration would be half-state for a diagram that is never drawn.

  Unblocking any of the rest is one isolated experiment each: change that one
  control in Insights, save, re-run the probe on that chart, and see which key
  moved. Nothing here is blocked on anything larger.

xAxis / yAxis: THE 2026-08-03 CLAIM WAS TOO STRONG, AND IS CORRECTED HERE
This docstring previously said the camelCase pair was ignored "on purpose,
permanently". That was written from nine charts that all happened to have the
snake_case pair populated, and stated with more confidence than the evidence
carried.

Then Felix set X and Y axes on a chart and Sophia still reported none. That is
new evidence: either the tab resolves to a different record, or the current
builder writes the axes somewhere this module was told never to look.

So the camelCase pair is now a FALLBACK, used only when all three hold:
  1. the snake_case key is absent or empty, AND
  2. the camelCase value resolves to a non-empty column name, AND
  3. that name matches a column the query actually returned.

Condition 3 is what makes this safe rather than a guess: the empty placeholder
shape still yields nothing, and a name that is not a real column is still
withheld. The worst case is unchanged behaviour, never a wrong chart.

`docs/migration/scripts/probe_tab_chart_resolution.py` settles which of the
three explanations is actually true. This fallback is a safety net, not the
diagnosis -- if the tab is pointing at the wrong record, it changes nothing and
the probe is what says so.

ORIGINAL FINDING, still true of the charts it was taken from:
Three charts (o2kvutcfld, tt51l7mma3, ni4pnlah9o) carry BOTH `x_axis` and
`xAxis`. The snake_case pair holds the real column names; the camelCase pair
holds the empty placeholder shape the builder initialises:

    {"aggregation": "", "column_name": "", ...}

On THOSE charts they are unfilled scaffolding, and a naive fallback would have
resolved a chart to a column named "". `_column_of()` returns "" for that
shape, and a test asserts it, so the fallback above cannot be fooled by one.

WHAT THE BUILDER EXPOSES, AND WHAT IS READ HERE
Read off the v3 builder UI. The left column is what a person sees; the right
is whether this module acts on it.

    Title                -> READ, from the record's own `title` field
    X Axis Column        -> READ, as config.x_axis -> `x_column`
    Y Axis Series        -> READ, as config.y_axis (all series) -> `y_columns`
    Stack                -> NO LONGER READ (see below)
    Show Axis Label      -> the LABEL is read (config.axis_label); the
                            show/hide toggle itself is not
    (legend position)    -> READ AND DRAWN (the donut's legend)
    Rotate Values        -> ignored
    Overlap              -> ignored
    Normalize            -> ignored
    Show Data Labels     -> ignored
    Show Scrollbar       -> ignored
    Y-Min / Y-Max        -> ignored
    Split Series         -> ignored

Of the nine builder controls whose keys were unknown on 2026-08-02, the
2026-08-03 probe found EIGHT of them nowhere in `config` on any of nine live
charts: Rotate Values, Overlap, Normalize, the Show Axis Label toggle, Show
Scrollbar, Y-Min, Y-Max and Split Series. They are either stored somewhere
other than the Chart's config, or they are client-side display state Insights
never persists. Nothing is implemented for them, and nothing should be until
one of them is isolated and re-probed.

    52 queries exist. 7 have a chart. 45 do not.
    NO COLOUR FIELD ANYWHERE -- see "colour" below.
    Every chart resolves to a query, so drill-down is unaffected.

`chart_type` IS FREE TEXT, SO THERE IS NO VALID SET
An open Data field has no enumerable set of legal values, and any list written
here would be a guess that ages. So this module does not try to know which
types are VALID. It knows which are SUPPORTED, and anything else degrades to a
labelled table -- never a broken card, never a blank one. Observed on this
site so far: Bar, Line, Donut.

COLOUR IS NOT ON THE RECORD, AND IS NOT INVENTED HERE
The probe dumped all 7 records in full: there is no colour field, no palette,
no series colour. Insights applies a palette at render time from somewhere not
saved on the document. Rather than parse a hash-named JS bundle for it -- which
would break on every Insights rebuild -- Sophia owns colour:

    default:        UCC Intelligence Settings.chart_palette
    per-chart:      the `palette` key on a UCC Analytics Tab chart entry

The shipped default was CHOSEN TO RESEMBLE Insights' current palette. It is
NOT read from Insights and will not track changes to it. See
docs/architecture/decisions/ADR-015-sophia-owns-chart-colour.md.

WHY A COLUMN IS NEVER GUESSED
`config`'s x_axis/y_axis may be plain strings or nested dicts depending on how
the chart was built. This reads both, then REQUIRES the result to match a
column the query actually returned. If it does not match, the presentation is
withheld and the card falls back to the table with a stated reason. Rendering a
chart against a column that might not be the one the author picked would be a
confident wrong answer, which is worse than a table.

PERMISSIONS
Chart records are read through `frappe.get_list`, which applies read
permission and user permissions -- so a chart a user may not read is never
resolved for them, and they get the table. Presentation is cosmetic and
carries no institutional data, but it is gated anyway: a chart's title can
itself be sensitive.
"""

import json

import frappe

CHART_DOCTYPE = "Insights Chart v3"
QUERY_DOCTYPE = "Insights Query v3"
SETTINGS_DOCTYPE = "UCC Intelligence Settings"

# What Sophia can actually draw. Compared case-insensitively, because
# chart_type is free text and nothing normalises it on the way in.
#
# Deliberately NOT "the valid set". Adding a type here means the renderer
# handles it; everything else falls back to the labelled table, which is a
# real view of real rows and not a failure state.
#
# THE TEN TYPES THE v3 BUILDER OFFERS, read off the UI on 2026-08-02:
#     Number, Bar, Line, Row, Donut, Funnel, Table, Map, Bubble, Sankey
# Six are drawn (Number, Bar, Line, Row, Donut, Funnel), Table is the table by
# definition, and three fall back: Map, Bubble, Sankey.
#
# FOUR OF THE FIVE UNDRAWN TYPES WERE ASSESSED ON 2026-08-03. Only Funnel was
# built. The other three are NOT gaps to close later -- they are refusals, and
# the reason is the same for each: Sophia's series contract is one label and
# one value per row, and none of those three can be drawn honestly from that.
#
#   Funnel  -> BUILT. Ordered stages, each a proportion of the largest. That is
#              exactly a label/value series, so it draws truthfully.
#   Map     -> REFUSED. Needs geographic boundaries this app does not have and
#              cannot fabricate. A "map" that is really a list of place names
#              would misrepresent the data more than a table does.
#   Bubble  -> REFUSED. Needs x, y and size per point -- three numbers where
#              the contract carries one. Anything drawn would be inventing two.
#   Sankey  -> REFUSED. Needs source/target flow PAIRS. A label/value series
#              has no edges, so there is no flow to draw.
#
# A bad renderer is worse than an honest fallback: a table is a real view of
# real rows, whereas a wrong diagram is read as fact. All three keep saying
# plainly that their rows are shown instead.
SUPPORTED_TYPES = {
	"bar": "bar",
	"row": "bar",
	"line": "line",
	"donut": "donut",
	"number": "number",
	"funnel": "funnel",
	# Not in v3's list. Kept as free aliases so a rename or a v2-era record
	# lands on the right renderer instead of the fallback -- but flagged as
	# UNOBSERVED so nobody reads them as evidence of what v3 offers.
	"column": "bar",
	"area": "line",
	"pie": "donut",
}

# "Table" is one of the ten. It is not a gap and must not apologise for
# itself: a chart whose type IS a table is correctly shown as a table, and
# calling that "not supported yet" would be false.
TABLE_TYPES = ("table",)

# Chosen to resemble what Insights shows today. NOT read from Insights -- see
# the module docstring and ADR-015. Ten, because a legend past ten series is
# unreadable anyway and the eleventh wrapping to colour one is honest.
DEFAULT_PALETTE = [
	"#2563EB", "#0EA5E9", "#14B8A6", "#22C55E", "#EAB308",
	"#F97316", "#EF4444", "#EC4899", "#8B5CF6", "#64748B",
]

MAX_PALETTE = 24
LEGEND_POSITIONS = ("top", "bottom", "left", "right", "none")


def _text(value):
	return frappe.utils.cstr(value or "").strip()


def _config(doc):
	raw = doc.get("config")
	if isinstance(raw, dict):
		return raw
	try:
		parsed = json.loads(raw or "{}")
	except Exception:
		return {}
	return parsed if isinstance(parsed, dict) else {}


def _column_of(value):
	"""A column name out of whatever shape config used for it.

	x_axis/y_axis may be a plain string, a dict, or a list of either. All three
	are read; none is assumed. Whatever comes out is still checked against the
	query's real columns before it is used.
	"""
	if isinstance(value, str):
		return value.strip()
	# A LIST was in this docstring from the day it was written and was never
	# handled. That is the bug behind "This chart has no X Axis Column set" on
	# a chart whose axes ARE set: `bool(config["x_axis"])` is True for a list,
	# so every diagnostic said the axis was present, while this returned "".
	# The first resolvable entry wins -- the x-axis is one column, and a list
	# of one is how the builder writes it.
	if isinstance(value, (list, tuple)):
		for item in value:
			found = _column_of(item)
			if found:
				return found
		return ""
	if isinstance(value, dict):
		for key in ("column_name", "dimension_name", "measure_name", "name", "column", "value"):
			found = value.get(key)
			if isinstance(found, str) and found.strip():
				return found.strip()
		# One level deeper. A Donut's x_axis is {"dimension": {}} on this site
		# -- an empty wrapper -- and the populated form of that same shape is
		# {"dimension": {"column_name": ...}}. Recursing reads the second
		# without inventing anything about the first, which still yields "".
		for nested in value.values():
			if isinstance(nested, (dict, list, tuple)):
				found = _column_of(nested)
				if found:
					return found
	return ""


def _columns_of(value):
	if isinstance(value, (list, tuple)):
		return [column for column in (_column_of(item) for item in value) if column]
	single = _column_of(value)
	return [single] if single else []


# Which config keys hold the axes, per renderer. First match wins; the rest
# are tried in order, so nothing is lost if a chart is configured unusually.
CATEGORY_AXIS_KEYS = (
	("x_axis", "label_column", "xAxis"),
	("y_axis", "value_column", "number_columns", "yAxis"),
)
LABELLED_AXIS_KEYS = (
	("label_column", "x_axis", "xAxis"),
	("value_column", "number_columns", "y_axis", "yAxis"),
)
# donut/number are label+value shapes; bar/line/funnel are axis shapes.
LABELLED_RENDERERS = ("donut", "number")


def axis_keys_for(render_as):
	"""The key order to try for this renderer."""
	return LABELLED_AXIS_KEYS if render_as in LABELLED_RENDERERS else CATEGORY_AXIS_KEYS


def filter_count(node):
	"""How many REAL filter entries a chart's `filters` config holds.

	Public so the bench probe can call the same code the verdict uses.

	Insights does not store a bare list. It stores a filter GROUP:

	    {"filters": [], "logical_operator": "And"}

	confirmed by direct database query on all three of Felix's tab charts,
	every one of which he had set no filters on. The previous check asked
	whether the value was one of (None, "", [], {}) -- shapes taken from my own
	assumption, never from the bench -- so an empty group, being a dict with two
	keys, counted as "has filters" and withheld all three charts. The mutation
	test that was supposed to cover this tested `filters=[]` and `filters={}`:
	both of the shapes I had imagined, neither of the one Insights writes.

	So the count walks the tree instead of testing a shape. A group recurses
	into its own `filters`; a leaf entry counts as one. Anything unrecognised
	and non-empty counts as one too -- withholding a chart whose filter shape
	is unknown is the ADR-016 answer, and the failure that gets noticed rather
	than the one that quietly shows wrong figures.
	"""
	if isinstance(node, dict):
		if "filters" in node:
			return filter_count(node["filters"])
		return 1 if node else 0
	if isinstance(node, (list, tuple)):
		return sum(filter_count(item) for item in node)
	if node in (None, "", 0):
		return 0
	return 1


def resolve_axes(config, render_as):
	"""(label column, value columns) as presentation_for resolves them.

	Public so the bench probe can call the REAL resolution instead of
	re-implementing it. The probe's "axes are present; Sophia should draw this"
	verdict was a truthiness check on x_axis, and it was a false positive on
	exactly the chart that did not draw. A probe that disagrees with the code
	is worse than no probe.
	"""
	label_keys, value_keys = axis_keys_for(render_as)
	label = ""
	for key in label_keys:
		label = _column_of(config.get(key))
		if label:
			break
	values = []
	for key in value_keys:
		values = _columns_of(config.get(key))
		if values:
			break
	return label, values


def default_palette():
	"""The institution's default series colours."""
	try:
		stored = frappe.db.get_single_value(SETTINGS_DOCTYPE, "chart_palette")
	except Exception:
		stored = None
	return normalise_palette(stored) or list(DEFAULT_PALETTE)


def normalise_palette(value):
	"""A palette from a stored string or list, or [] if there isn't a usable one.

	Accepts newline- or comma-separated hex, because the settings field is a
	Small Text somebody types into. Anything that is not a hex colour is
	dropped rather than passed to the browser.
	"""
	if not value:
		return []
	if isinstance(value, str):
		try:
			parsed = json.loads(value)
			items = parsed if isinstance(parsed, list) else None
		except Exception:
			items = None
		if items is None:
			items = [part for chunk in value.split("\n") for part in chunk.split(",")]
	else:
		items = list(value)
	colours = []
	for item in items:
		colour = _text(item)
		if not colour.startswith("#"):
			continue
		if len(colour) not in (4, 7):
			continue
		if any(character not in "0123456789abcdefABCDEF" for character in colour[1:]):
			continue
		if colour not in colours:
			colours.append(colour)
	return colours[:MAX_PALETTE]


def label_for(query, query_title="", record=None):
	"""What a human should see for this query. NEVER the id.

	An Insights record's `name` is a hash -- `o80pe2gco2` means nothing to
	anyone, and four cards showing four hashes is not a dashboard. The order is
	deliberate:

	    1. the Chart's title    -- what the author named the thing they built
	    2. the Query's title    -- what the data was called
	    3. the id               -- only if BOTH are empty, and then labelled as
	                               an untitled chart rather than dumped raw

	Insights creates a backing query when a chart is built, and those arrive
	with no title at all. That is exactly how four hashes reached the tabs.
	"""
	if record is None:
		record = chart_record_for(query)
	chart_title = _text((record or {}).get("title"))
	if chart_title:
		return chart_title
	title = _text(query_title)
	if title:
		return title
	return "Untitled chart (%s)" % _text(query)


def chart_record_for(query):
	"""The Insights Chart v3 record built on this query, if this user may read it.

	get_list, not get_all -- a chart the user cannot read must not resolve for
	them. Both link fields the probe found are checked, `query` first.
	"""
	query = _text(query)
	if not query or not frappe.db.exists("DocType", CHART_DOCTYPE):
		return None
	for field in ("query", "data_query"):
		try:
			rows = frappe.get_list(
				CHART_DOCTYPE,
				filters={field: query},
				fields=["name", "title", "chart_type", "config"],
				order_by="modified desc",
				limit_page_length=1,
			)
		except Exception:
			continue
		if rows:
			return rows[0]
	return None


def presentation_for(query, columns=None, palette=None):
	"""How to draw this query, or why it cannot be drawn. Never raises.

	`columns` is what the query's execute() actually returned. Passing it is
	what makes this safe: a config column that is not among them is treated as
	unresolvable rather than rendered against.
	"""
	available = [_text(column) for column in (columns or []) if _text(column)]
	blank = {
		"status": "table_only",
		"chart_type": "",
		"supported": False,
		"reason": "",
		"palette": normalise_palette(palette) or default_palette(),
	}
	try:
		record = chart_record_for(query)
	except Exception as error:
		blank["reason"] = _text(error)
		return blank
	if not record:
		blank["reason"] = "No Insights chart has been built for this query."
		return blank
	# Carried on EVERY branch, not just the drawing one. A chart that exists but
	# has no axes set yet still has a name, and that name is what the card shows
	# instead of a hash.
	blank["chart"] = record.get("name")
	blank["title"] = _text(record.get("title"))

	config = _config(frappe._dict(record))
	raw_type = _text(record.get("chart_type")) or _text(config.get("chart_type"))
	if raw_type.lower() in TABLE_TYPES:
		blank["chart_type"] = raw_type
		blank["reason"] = "This Insights chart is a table."
		return blank

	supported = SUPPORTED_TYPES.get(raw_type.lower())
	if not supported:
		blank["chart_type"] = raw_type
		blank["reason"] = ("Chart type %r is not drawn here yet, so its rows are "
			"shown instead." % raw_type
			if raw_type else "This Insights chart has no chart type set.")
		return blank

	# WHICH KEYS HOLD THE AXES DEPENDS ON THE CHART TYPE (evidence, 2026-08-03)
	#
	# Felix's Donut has x_axis = {"dimension": {}} -- genuinely empty -- while
	# `label_column` holds "benchmark_type", a real column the query returns.
	# So a Donut is configured through label_column/value_column and an
	# axis chart through x_axis/y_axis, and reading x_axis universally is what
	# left the Donut blank.
	#
	# This is NOT the name-inference ADR-016 forbids. The 2026-08-03 config
	# probe declined to read `label_column` precisely because nothing
	# corroborated what it meant; a live chart whose only populated axis key is
	# that one, holding a real column name, IS that corroboration.
	#
	# Both orders are tried either way, so a chart configured unusually still
	# resolves -- and every candidate is checked against the columns the query
	# really returned before it is used.
	label_keys, value_keys = axis_keys_for(supported)
	label_column = ""
	for key in label_keys:
		label_column = _column_of(config.get(key))
		if label_column:
			break
	value_columns = []
	for key in value_keys:
		value_columns = _columns_of(config.get(key))
		if value_columns:
			break


	# The check that stops a confident wrong answer. If the author's column is
	# not in what the query returned, we do not know what they meant.
	# NO COLUMNS AT ALL is not an axis problem, and must never be reported as
	# one. It means the query returned nothing -- a broken query, an empty
	# table, or rows this user cannot see -- and saying "no X Axis Column set"
	# would send someone to Insights to fix a setting that is already correct.
	if not available:
		blank["chart_type"] = raw_type
		blank["reason"] = ("This chart's query returned no rows, so there is nothing "
			"to draw. The chart's own settings are not the problem.")
		return blank

	if available:
		if label_column and label_column not in available:
			blank["chart_type"] = raw_type
			blank["reason"] = ("The chart is drawn on %r, which this query no longer "
				"returns." % label_column)
			return blank
		value_columns = [column for column in value_columns if column in available]
		if not label_column:
			blank["chart_type"] = raw_type
			# Two different situations, two different sentences. Telling someone
			# to go and set an axis they have already set is worse than saying
			# nothing: they will set it again and it still will not work.
			blank["reason"] = ("This chart has an X Axis setting that Sophia could "
				"not read. Its value is not a column name Sophia recognises — this "
				"is a Sophia limitation, not something to fix in Insights."
				if config.get("x_axis") or config.get("xAxis")
				else "This chart has no X Axis Column set in Insights. Open it in "
					"Insights, set X Axis Column and Y Axis Series, and it will "
					"draw here.")
			return blank
		if not value_columns:
			blank["chart_type"] = raw_type
			blank["reason"] = ("This chart has no Y Axis Series that this query "
				"returns. Set Y Axis Series in Insights and it will draw here.")
			return blank

	# A CHART FILTER MEANS THE NUMBERS WOULD NOT MATCH INSIGHTS.
	#
	# Sophia executes the QUERY. Insights renders the CHART, which applies its
	# own filters on top of the query's. So a chart with filters shows fewer
	# rows in Insights than these rows contain -- and drawing them anyway would
	# put a larger figure on a card that carries the chart's name.
	#
	# Withheld rather than approximated. Applying the filters here would mean
	# reproducing a filter shape that has not been proven on this bench, which
	# is the mistake ADR-016 exists to prevent.
	if filter_count(config.get("filters")):
		blank["chart_type"] = raw_type
		blank["reason"] = ("This chart applies its own filters in Insights, which are "
			"not applied to these rows -- so the figures would not match. The rows "
			"below are the query's own, unfiltered.")
		return blank

	# LIMIT is honoured. It is a plain number, so there is nothing to misread,
	# and a chart configured as "top 10" that silently drew 40 bars would be
	# showing something its author did not ask for.
	limit = config.get("limit")
	try:
		limit = int(limit) if limit not in (None, "") else 0
	except (TypeError, ValueError):
		limit = 0
	if limit < 1:
		limit = 0

	legend = _text(config.get("legend_position")).lower()
	return {
		"status": "available",
		"chart": record.get("name"),
		"title": _text(record.get("title")),
		"chart_type": raw_type,
		"render_as": supported,
		"supported": True,
		"x_column": label_column,
		"y_columns": value_columns,
		"axis_label": _text(config.get("axis_label")),
		"legend_position": legend if legend in LEGEND_POSITIONS else "",
		"limit": limit,
		# `stack` IS NO LONGER READ (decided 2026-08-03).
		#
		# It was parsed into this contract and honoured by nothing, which is the
		# worst of both: it looked supported and was not. Stacking only means
		# anything with two or more measures per category, and Sophia's series
		# contract is one label and one value per row -- there is no second
		# series to stack. Reading a value we structurally cannot draw is a
		# promise this module cannot keep, so it stops making it.
		#
		# When multi-series lands, `config.get("stack")` is where it comes back
		# from; the key name is confirmed, only the renderer is missing.
		"palette": normalise_palette(palette) or default_palette(),
		"reason": "",
	}


def charts_by_query():
	"""{query id: chart title} for every chart this user may read.

	One call rather than one per row, so the picker can mark 52 queries without
	52 lookups.
	"""
	if not frappe.db.exists("DocType", CHART_DOCTYPE):
		return {}
	try:
		rows = frappe.get_list(
			CHART_DOCTYPE,
			fields=["name", "title", "chart_type", "query", "data_query"],
			limit_page_length=0,
		) or []
	except Exception:
		return {}
	mapping = {}
	for row in rows:
		for field in ("query", "data_query"):
			query = _text(row.get(field))
			if query and query not in mapping:
				mapping[query] = {"chart": row.get("name"),
					"title": _text(row.get("title")),
					"chart_type": _text(row.get("chart_type")),
					# Which of the two links this is. The picker keeps the
					# AUTHORED query and drops the generated backing one, so
					# the surviving row is the one a person recognises.
					"authored": field == "query"}
			# `query` and `data_query` can point at DIFFERENT queries: Insights
			# creates a backing query when a chart is built. Both are mapped, so
			# whichever of them reaches a tab still resolves to this chart and
			# still gets its title rather than a hash.
	return mapping
