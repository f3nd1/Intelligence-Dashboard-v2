# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt
"""From a chart segment to the records behind it.

THE PROBLEM
An embedded chart's execute() returns SUMMARISED rows -- the probe on
2026-08-02 confirmed it against a real chart on a real tab:

    columns: ['engagement_type', 'count']
    {'engagement_type': 'Consultative', 'count': 40}

Clicking that bar filters the table to that one row. What Felix wants is the
40 Stakeholder Engagement Strategy records it counted.

WHERE THE FACTS IN THIS MODULE CAME FROM
docs/migration/scripts/probe_insights_drilldown.py, run live against
`vc55npin67` on 2026-08-02. Nothing here is recalled. The probe established:

    insights 3.12.2, both schemas installed, tab charts all Insights Query v3
    is_builder_query:    1
    use_live_connection: 1
    data_source (top):   None          <- empty; the real one is in the step
    operations:
      {"type":"source","table":{"type":"table","data_source":"Site DB",
                                "table_name":"tabStakeholder Engagement Strategy"}}
      {"type":"summarize","dimensions":[{"column_name":"engagement_type",...}],
                          "measures":[{"column_name":"count","aggregation":"count",...}]}

So this module READS that structure and never writes one. The table name, the
data source and the dimension column are lifted from the stored query; the 13
TableNotFound errors came from composing those from memory instead.

DOES INSIGHTS ALREADY DO THIS? NO -- SETTLED LIVE, 2026-08-02
Insights ships a DrillDown component, so it was checked rather than assumed
(docs/migration/scripts/probe_insights_native_drilldown.py, run on the bench):

  - it calls exactly two endpoints, `insights.api.alerts.get_alerts` and
    `...ibis.utils.validate_expression`. One fetches alert configuration; the
    other validates an expression string and touches no records at all.
  - there is NO drill-shaped Python anywhere in the Insights app. The feature
    is client-side: it re-runs the same execute() with an extra filter.

So Insights' drill-down NARROWS THE AGGREGATE. It never lists the source
records, which is the thing this module exists to do. It solves a different
problem, and nothing here defers to it.

The same run re-confirmed the baseline below on the installed version rather
than carrying it over from an earlier round: `execute()` builds an ibis query
and runs it through `execute_ibis_query` with no Frappe permission layer
anywhere -- "PERMISSION-BLIND -- raw_sql, and no permission-applying call".

WHY THE RECORDS COME FROM frappe.get_list AND NOT FROM INSIGHTS
This is the security decision, and it is the reason the module is shaped this
way at all.

Insights `execute()` runs SQL against the site database. It does not apply
Frappe's read permission, user permissions, or a DocType's
permission_query_conditions. `chart_data()` calls `doc.check_permission("read")`
-- but that is permission on the Insights Query DOCUMENT, not on the records it
counted. That is proportionate for an aggregate: "40 engagements are
Consultative" discloses one number. It is NOT proportionate for a list of the
40 records, which is Felix's exact concern: a drill-down that bypasses
permissions turns a summary count into a records leak.

`frappe.get_list` applies all three checks by construction. So the drill-down
uses the query to learn WHICH records to ask for, and Frappe to decide which of
them this user may see. A user who can read the chart but not the records gets
an empty list, not a leak -- and the count in the bar is deliberately allowed to
exceed the number of rows returned, because the count is the institution's
figure and the rows are this reader's slice of it.

The probe is what makes that possible: `data_source: "Site DB"` means the rows
ARE Frappe records in this site, and `use_live_connection: 1` means the chart
read them live rather than from an imported snapshot -- so get_list reads the
same rows the chart counted, not a copy of them.

WHAT IT REFUSES TO DO
Every case below returns `unsupported` with a reason, rather than a plausible
wrong answer:

  - a native SQL query (is_builder_query falsy) -- no pipeline to read
  - a data source that is not the site database -- records this platform
    cannot permission-check
  - a table_name that is not "tab<DocType>" -- nothing to map to
  - a dimension that is not a real field on that DocType -- a computed or
    date-bucketed column is not a filter
  - ANY operation in the pipeline other than source, filter and summarize --
    a join or a mutate changes which rows were counted, and showing the
    unjoined records would show more records than the chart counted

Failing closed is the point. A drill-down that quietly returns the wrong record
set is worse than one that says it cannot.
"""

import json

import frappe

from ucc_intelligence.analytics.admission_intelligence_embed import clean_text

CHART_DOCTYPE = "Insights Query v3"

# The probe printed "Site DB" for the source that is this Frappe site. Anything
# else is an external database, where Frappe permissions do not apply.
SITE_DATA_SOURCES = ("Site DB", "Site Database")

# Only these three can be honoured faithfully. See the module docstring.
SUPPORTED_OPERATIONS = ("source", "filter", "summarize")

# Operators frappe.get_list understands with the same meaning Insights gives
# them. Anything outside this list is declined rather than approximated.
FILTER_OPERATORS = ("=", "!=", ">", "<", ">=", "<=", "in", "not in", "like", "not like", "between")

# Fields every DocType has, which meta.has_field() reports False for.
STANDARD_FIELDS = ("name", "owner", "creation", "modified", "modified_by", "docstatus", "idx")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def _fail(status, message, **extra):
	payload = {"status": status, "records": [], "fields": [], "message": message,
		"page": 1, "page_size": 0, "has_more": False}
	payload.update(extra)
	return payload


def _operations(doc):
	"""The query's pipeline, whether it is stored as JSON text or as a list."""
	operations = doc.get("operations")
	if isinstance(operations, str):
		try:
			operations = json.loads(operations or "[]")
		except Exception:
			return []
	return [step for step in (operations or []) if isinstance(step, dict)]


def _source_of(operations):
	"""(table_name, data_source) from the source step, verbatim."""
	for step in operations:
		if step.get("type") == "source":
			table = step.get("table") or {}
			return table.get("table_name") or "", table.get("data_source") or ""
	return "", ""


def _dimensions_of(operations):
	"""The column names this query grouped by -- the only ones drillable.

	Restricting the caller to these is not tidiness. Accepting any column would
	let someone probe arbitrary field values through the drill-down endpoint by
	naming a field the chart never grouped by.
	"""
	columns = []
	for step in operations:
		if step.get("type") != "summarize":
			continue
		for dimension in (step.get("dimensions") or []):
			if isinstance(dimension, dict):
				column = dimension.get("column_name") or dimension.get("dimension_name")
				if column and column not in columns:
					columns.append(column)
	return columns


def _pipeline_filters(operations, doctype):
	"""The query's own filter steps, as frappe.get_list filters.

	The chart counted the rows that survived these. Dropping them would show
	records the bar never included, so an untranslatable one fails the whole
	drill-down rather than being skipped.

	The step shape is the one proven on this bench in
	build_admission_intelligence_embed.build_simple_series():
	    {"type":"filter","column":{"column_name":X},"operator":"=","value":V}
	"""
	meta = frappe.get_meta(doctype)
	filters = []
	for step in operations:
		if step.get("type") != "filter":
			continue
		column = (step.get("column") or {}).get("column_name")
		operator = step.get("operator")
		value = step.get("value")
		if not column or not _is_field(meta, column):
			return None, "the chart filters on %r, which is not a field on %s" % (column, doctype)
		if operator not in FILTER_OPERATORS:
			return None, "the chart uses the filter operator %r, which this drill-down cannot reproduce" % operator
		if isinstance(value, dict):
			return None, "the chart filters %r against a computed value this drill-down cannot reproduce" % column
		filters.append([column, operator, value])
	return filters, ""


def _is_field(meta, column):
	return column in STANDARD_FIELDS or bool(meta.has_field(column))


def _display_fields(doctype, column):
	"""A short, readable row: what it is, the value that was clicked, when."""
	meta = frappe.get_meta(doctype)
	fields = ["name"]
	for candidate in (meta.get("title_field"), column, "status", "modified"):
		if candidate and candidate not in fields and _is_field(meta, candidate):
			fields.append(candidate)
	return fields


def resolve(chart):
	"""What a chart can be drilled into, or why it cannot. Never raises."""
	chart = clean_text(chart)
	if not chart:
		return _fail("unsupported", "No chart given.", chart="")
	try:
		doc = frappe.get_doc(CHART_DOCTYPE, chart)
		doc.check_permission("read")
	except frappe.PermissionError as error:
		return _fail("permission_denied", clean_text(error), chart=chart)
	except frappe.DoesNotExistError:
		return _fail("unavailable", "This chart no longer exists in Insights.", chart=chart)
	except Exception as error:
		return _fail("query_error", clean_text(error), chart=chart)

	if not doc.get("is_builder_query"):
		return _fail("unsupported", chart=chart,
			message="This chart is written as SQL rather than built from a table, "
				"so there is no source table to open.")

	operations = _operations(doc)
	unsupported = [step.get("type") for step in operations
		if step.get("type") not in SUPPORTED_OPERATIONS]
	if unsupported:
		return _fail("unsupported", chart=chart,
			message="This chart's data is combined with a %s step, so the records "
				"behind a segment are not simply the rows of one table."
				% unsupported[0])

	table_name, data_source = _source_of(operations)
	# The probe found the top-level data_source empty and the real one inside
	# the source step, so the step wins and the field is only a fallback.
	data_source = data_source or doc.get("data_source") or ""
	if not table_name:
		return _fail("unsupported", "This chart has no source table.", chart=chart)
	if data_source not in SITE_DATA_SOURCES:
		return _fail("unsupported", chart=chart,
			message="This chart reads from %s, which is outside this site, so its "
				"records cannot be permission-checked here." % (data_source or "an unnamed source"))
	if not table_name.startswith("tab"):
		return _fail("unsupported", chart=chart,
			message="This chart reads the table %s, which is not a Frappe DocType." % table_name)

	doctype = table_name[3:]
	if not frappe.db.exists("DocType", doctype):
		return _fail("unsupported", "%s is not a DocType on this site." % doctype, chart=chart)

	columns = _dimensions_of(operations)
	if not columns:
		return _fail("unsupported", chart=chart,
			message="This chart is not grouped by anything, so a segment does not "
				"correspond to a set of records.")

	meta = frappe.get_meta(doctype)
	drillable = [column for column in columns if _is_field(meta, column)]
	if not drillable:
		return _fail("unsupported", chart=chart,
			message="This chart groups by %s, which is calculated rather than stored "
				"on %s, so it cannot be turned back into a filter."
				% (", ".join(columns), doctype))

	return {"status": "available", "chart": chart, "doctype": doctype,
		"columns": drillable, "operations": operations,
		"title": doc.get("title") or chart, "message": "",
		"records": [], "fields": [], "page": 1, "page_size": 0, "has_more": False}


def records(chart, column, value, page=1, page_size=DEFAULT_PAGE_SIZE):
	"""The records behind one chart segment, as this user is allowed to see them.

	Never raises, for the same reason chart_data() does not: a drill-down that
	fails shows as a failed drill-down, it does not take the tab down.
	"""
	resolved = resolve(chart)
	if resolved.get("status") != "available":
		return resolved

	doctype = resolved["doctype"]
	column = clean_text(column)
	if column not in resolved["columns"]:
		return _fail("unsupported", chart=chart, doctype=doctype,
			message="This chart is not grouped by %r." % column)

	# The gate that makes the rest safe to run at all. get_list would return an
	# empty list anyway, but an explicit refusal says why instead of looking
	# like a segment with no records in it.
	if not frappe.has_permission(doctype, "read"):
		return _fail("permission_denied", chart=chart, doctype=doctype,
			message="You do not have permission to open %s records." % doctype)

	filters, problem = _pipeline_filters(resolved["operations"], doctype)
	if filters is None:
		return _fail("unsupported", problem, chart=chart, doctype=doctype)

	# A chart groups blank values into one segment; clicking it has to ask for
	# both spellings of blank or it returns nothing.
	if value in (None, "", "null"):
		filters.append([column, "in", ["", None]])
	else:
		filters.append([column, "=", value])

	try:
		page = max(1, int(page or 1))
		page_size = max(1, min(int(page_size or DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE))
	except (TypeError, ValueError):
		page, page_size = 1, DEFAULT_PAGE_SIZE

	fields = _display_fields(doctype, column)
	try:
		# One row beyond the page tells us whether there is a next one, without
		# a second count query over a table that may be large.
		rows = frappe.get_list(
			doctype,
			filters=filters,
			fields=fields,
			order_by="modified desc",
			limit_start=(page - 1) * page_size,
			limit_page_length=page_size + 1,
		) or []
	except frappe.PermissionError as error:
		return _fail("permission_denied", clean_text(error), chart=chart, doctype=doctype)
	except Exception as error:
		return _fail("query_error", clean_text(error), chart=chart, doctype=doctype)

	has_more = len(rows) > page_size
	return {
		"status": "available",
		"chart": chart,
		"doctype": doctype,
		"column": column,
		"value": value,
		"fields": fields,
		"records": rows[:page_size],
		"page": page,
		"page_size": page_size,
		"has_more": has_more,
		"message": "",
	}
