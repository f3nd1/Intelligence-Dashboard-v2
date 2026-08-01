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
SUPPORTED_TYPES = {
	"bar": "bar",
	"column": "bar",
	"row": "bar",
	"line": "line",
	"area": "line",
	"donut": "donut",
	"pie": "donut",
	"number": "number",
}

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
	if isinstance(value, dict):
		for key in ("column_name", "dimension_name", "measure_name", "name", "column", "value"):
			found = value.get(key)
			if isinstance(found, str) and found.strip():
				return found.strip()
	return ""


def _columns_of(value):
	if isinstance(value, (list, tuple)):
		return [column for column in (_column_of(item) for item in value) if column]
	single = _column_of(value)
	return [single] if single else []


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

	config = _config(frappe._dict(record))
	raw_type = _text(record.get("chart_type")) or _text(config.get("chart_type"))
	supported = SUPPORTED_TYPES.get(raw_type.lower())
	if not supported:
		blank["chart_type"] = raw_type
		blank["reason"] = ("Chart type %r is not supported here yet." % raw_type
			if raw_type else "This Insights chart has no chart type set.")
		return blank

	label_column = _column_of(config.get("x_axis"))
	value_columns = _columns_of(config.get("y_axis"))

	# The check that stops a confident wrong answer. If the author's column is
	# not in what the query returned, we do not know what they meant.
	if available:
		if label_column and label_column not in available:
			blank["chart_type"] = raw_type
			blank["reason"] = ("The chart is drawn on %r, which this query no longer "
				"returns." % label_column)
			return blank
		value_columns = [column for column in value_columns if column in available]
		if not label_column:
			blank["chart_type"] = raw_type
			blank["reason"] = "The chart has no x-axis set in Insights."
			return blank
		if not value_columns:
			blank["chart_type"] = raw_type
			blank["reason"] = "The chart has no y-axis column that this query returns."
			return blank

	legend = _text(config.get("legend_position")).lower()
	return {
		"status": "available",
		"chart": record.get("name"),
		"title": _text(record.get("title")),
		"chart_type": raw_type,
		"render_as": supported,
		"supported": True,
		"label_column": label_column,
		"value_columns": value_columns,
		"axis_label": _text(config.get("axis_label")),
		"legend_position": legend if legend in LEGEND_POSITIONS else "",
		"stacked": bool(config.get("stack")),
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
					"chart_type": _text(row.get("chart_type"))}
	return mapping
