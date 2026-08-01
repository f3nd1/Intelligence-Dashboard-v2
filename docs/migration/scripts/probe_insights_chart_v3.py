"""What an Insights Chart v3 record actually holds, read from the live site.

WHY
Sophia's tabs embed `Insights Query v3` records. A Query carries DATA and
nothing else -- which is why every embedded chart renders as a table. Chart
type, colours, axis assignment, axis labels, legend and title live on a
separate `Insights Chart v3` record, and Sophia has never read one.

Before anything renders from a Chart record, the shape of that record has to
come off this bench rather than out of a memory. The v2 chart-type list
(Number/Line/Bar/Row/Pie/Table/Progress/Scatter/Funnel/Trend/Mixed Axis/Pivot
Table) is historical: the 2026-08-02 probe established that Sophia's charts are
all v3, and v3 may name its types differently or not use a Select at all.

WHAT THIS DOES NOT TOUCH
Drill-down. `analytics/drilldown.py` reads the QUERY's operations -- the source
step, the filter steps, the summarize step -- and fetches records with
frappe.get_list. Every Chart points at a Query, so that path is unchanged by
anything found here. This probe deliberately also prints the Chart -> Query
link so it can be proved that the same Query is still reachable.

RUN
    bench --site <site> console
    >>> exec(open("/home/felixoking/Intelligence-Dashboard-v2/docs/migration/scripts/probe_insights_chart_v3.py").read(), globals())

SAFETY
Read-only. Creates nothing, changes nothing, executes nothing.
"""

import json
import os

import frappe

CHART_DOCTYPE = "Insights Chart v3"
QUERY_DOCTYPE = "Insights Query v3"
TAB_DOCTYPE = "UCC Analytics Tab"

# Words that would identify a charting library in a filename, for section 6.
CHART_LIBRARY_HINTS = ("echart", "chart", "plotly", "d3", "vega", "apex", "highcharts")


def head(number, title):
	print("\n" + "=" * 72)
	print("%s. %s" % (number, title))
	print("=" * 72)


def brief(value, limit=1400):
	try:
		text = frappe.as_json(value)
	except Exception:
		text = str(value)
	return text if len(text) <= limit else text[:limit] + "\n        ... [truncated]"


# --- 1 -----------------------------------------------------------------------

def probe_meta():
	head(1, "EVERY FIELD ON %s" % CHART_DOCTYPE)
	if not frappe.db.exists("DocType", CHART_DOCTYPE):
		print("   ABSENT -- there is no %s on this site." % CHART_DOCTYPE)
		return None
	print("   %d record(s)\n" % frappe.db.count(CHART_DOCTYPE))
	meta = frappe.get_meta(CHART_DOCTYPE)
	print("   %-24s %-16s %s" % ("FIELDNAME", "TYPE", "LABEL / OPTIONS"))
	print("   " + "-" * 66)
	for field in meta.fields:
		detail = field.label or ""
		if field.fieldtype in ("Link", "Table", "Table MultiSelect"):
			detail = "%s -> %s" % (detail, field.options)
		elif field.fieldtype == "Select" and field.options:
			# This is the answer to "what are the valid chart types on v3",
			# straight off the field definition rather than from a list.
			detail = "%s :: %s" % (detail, str(field.options).replace("\n", " | "))
		print("   %-24s %-16s %s" % (field.fieldname, field.fieldtype, detail))

	links = [f.fieldname for f in meta.fields
		if f.fieldtype == "Link" and f.options == QUERY_DOCTYPE]
	print("\n   fields linking to %s: %s" % (QUERY_DOCTYPE, links or "NONE (see section 3)"))
	return meta


# --- 2 -----------------------------------------------------------------------

def probe_records():
	head(2, "EVERY %s RECORD, IN FULL" % CHART_DOCTYPE)
	print("   The complete stored document for each one. Chart type, colours,")
	print("   axis assignment, labels and legend are all in here somewhere --")
	print("   this prints everything so none of it has to be guessed at.\n")
	names = [row["name"] for row in frappe.get_all(CHART_DOCTYPE,
		fields=["name"], order_by="modified desc", limit_page_length=0)]
	charts = []
	for name in names:
		try:
			doc = frappe.get_doc(CHART_DOCTYPE, name)
		except Exception as error:
			print("   %-14s could not load: %s" % (name, error))
			continue
		data = doc.as_dict()
		# Frappe bookkeeping is noise here.
		for key in ("owner", "creation", "modified", "modified_by", "docstatus",
				"idx", "parent", "parentfield", "parenttype", "doctype"):
			data.pop(key, None)
		charts.append(doc)
		print("   --- %s ---" % name)
		print("   %s\n" % brief(data, 2000))
	return charts


# --- 3 -----------------------------------------------------------------------

def chart_query_of(doc):
	"""Whichever field on this Chart points at a Query, whatever it is called.

	Reported rather than assumed: if v3 stores the link inside a JSON config
	instead of a Link field, the printed value is where that shows up.
	"""
	for key in ("query", "query_name", "data_query", "insights_query"):
		value = doc.get(key)
		if value:
			return key, value
	for key, value in (doc.as_dict() or {}).items():
		if isinstance(value, str) and frappe.db.exists(QUERY_DOCTYPE, value):
			return key, value
	return "", ""


def probe_links(charts):
	head(3, "HOW EACH CHART REACHES ITS QUERY (drill-down depends on this)")
	print("   drilldown.py reads the QUERY's operations. If every Chart resolves")
	print("   to a Query here, drill-down needs no change at all.\n")
	pairs = []
	for doc in charts:
		field, query = chart_query_of(doc)
		title = doc.get("title") or doc.name
		print("   %-14s %-42s -> %s = %s" % (doc.name, title[:42], field or "(none found)", query or "?"))
		if query:
			pairs.append((doc.name, title, query))
	return pairs


# --- 4 -----------------------------------------------------------------------

def sophia_chart_ids():
	if not frappe.db.exists("DocType", TAB_DOCTYPE):
		return []
	ids = []
	for row in frappe.get_all(TAB_DOCTYPE, fields=["name", "charts"]):
		try:
			for item in json.loads(row.get("charts") or "[]"):
				chart = item.get("chart") if isinstance(item, dict) else item
				if chart and chart not in ids:
					ids.append(chart)
		except Exception:
			continue
	return ids


def probe_tab_coverage(pairs):
	head(4, "DO FELIX'S 3 CONFIGURED TAB CHARTS HAVE CHART RECORDS?")
	configured = sophia_chart_ids()
	if not configured:
		print("   no charts configured on any Sophia tab")
		return
	by_query = {}
	for chart_name, title, query in pairs:
		by_query.setdefault(query, []).append((chart_name, title))
	for query in configured:
		query_title = frappe.db.get_value(QUERY_DOCTYPE, query, "title") or "(unknown)"
		found = by_query.get(query) or []
		print("   %-14s %-46s -> %s" % (query, query_title[:46],
			", ".join("%s (%s)" % (name, title[:30]) for name, title in found)
			if found else "NO CHART RECORD -- would still render as a table"))


# --- 5 -----------------------------------------------------------------------

def probe_coverage_overall(pairs):
	head(5, "HOW MANY OF THE %d QUERIES HAVE A CHART AT ALL" % frappe.db.count(QUERY_DOCTYPE))
	print("   This decides what the picker should offer, and what happens to a")
	print("   query nobody has built a chart for.\n")
	total = frappe.db.count(QUERY_DOCTYPE)
	with_chart = len({query for _, _, query in pairs})
	print("   queries:            %d" % total)
	print("   queries with a chart: %d" % with_chart)
	print("   queries with none:    %d" % (total - with_chart))


# --- 6 -----------------------------------------------------------------------

def probe_rendering():
	head(6, "WHAT INSIGHTS ITSELF RENDERS WITH (the build-vs-embed decision)")
	print("   Sophia will not hand-roll SVG again. So: which charting library")
	print("   does Insights ship, is it already served on this site, and does")
	print("   Insights expose a route that renders one chart on its own?\n")
	try:
		app_path = frappe.get_app_path("insights")
	except Exception as error:
		print("   the insights app path is unavailable: %s" % error)
		return

	print("   --- JS this app injects into Desk (hooks) ---")
	for hook in ("app_include_js", "app_include_css", "website_route_rules", "website_redirects"):
		try:
			value = frappe.get_hooks(hook, app_name="insights")
		except Exception:
			value = None
		print("   %-22s %s" % (hook, value or "(none)"))

	print("\n   --- charting libraries present in the insights app ---")
	seen = set()
	for root, _dirs, files in os.walk(app_path):
		if "node_modules" in root:
			continue
		for filename in files:
			lower = filename.lower()
			if not lower.endswith((".js", ".css", ".mjs")):
				continue
			if not any(hint in lower for hint in CHART_LIBRARY_HINTS):
				continue
			relative = os.path.join(root, filename).replace(app_path, "").lstrip("/")
			key = relative.split("/")[0] + "/" + filename
			if key in seen:
				continue
			seen.add(key)
			print("   %s" % relative)
	if not seen:
		print("   none found by filename -- the chart library is probably bundled")
		print("   into the built SPA rather than shipped as a separate asset")

	print("\n   --- pages Insights serves (an embeddable route, if any) ---")
	www = os.path.join(app_path, "www")
	if os.path.isdir(www):
		for entry in sorted(os.listdir(www))[:40]:
			print("   www/%s" % entry)
	else:
		print("   no www/ directory")

	public = os.path.join(app_path, "public")
	if os.path.isdir(public):
		print("\n   --- top level of public/ ---")
		for entry in sorted(os.listdir(public))[:40]:
			print("   public/%s" % entry)


def run():
	meta = probe_meta()
	if not meta:
		return
	charts = probe_records()
	pairs = probe_links(charts)
	probe_tab_coverage(pairs)
	probe_coverage_overall(pairs)
	probe_rendering()
	head("NEXT", "WHAT TO PASTE BACK")
	print("All six sections. Section 1 is the schema, 2 is where the colours and")
	print("axis assignment actually live, 3 proves drill-down still reaches the")
	print("Query, 4 and 5 decide the picker, and 6 decides whether Sophia draws")
	print("the charts or reuses what Insights already ships.")


run()
