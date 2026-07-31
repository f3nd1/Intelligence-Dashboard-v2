"""Create a real Insights Query v3 for every AUTHORED chart spec
(analytics/chart_definitions.py), then report which ones actually return
data.

WHAT "AUTHORED" MEANS
The query is designed -- DocType, group-by dimension, measure, filters --
but has never existed on a site. This script materialises it and executes
it once. A spec that errors (field does not exist on this site's schema,
DocType absent) is reported, not silently skipped, because a chart that
looks built and returns nothing is worse than one that says it failed.

WHAT IT DOES NOT DO
It does not flip anything to "real" in chart_definitions.py. A chart becomes
"real" only after a human has looked at its output and agreed it is correct.
This script tells you which ones are ready for that.

The dimension fields were chosen by reading each criterion module's
SOURCE_CANDIDATES and the chart's own title. They have NOT been checked
against this site's live schema -- that is exactly what running this does.
Expect some to fail on the first run; the failures are the useful output.

RUN
    bench --site <site> console
    >>> exec(open("apps/ucc_intelligence/../docs/migration/scripts/build_insights_charts_from_specs.py").read(), globals())

  The globals() argument matters -- without it top-level defs land in locals
  and cross-function calls raise NameError.

SAFETY
  Creates only titles beginning "UCC AUTHORED - ". Never touches a real or
  placeholder chart. Idempotent. is_public is never set.
"""

import frappe

from ucc_intelligence.analytics import chart_registry
from ucc_intelligence.analytics.admission_intelligence_embed import rows_to_chart_series

AUTHORED_PREFIX = "UCC AUTHORED - "
DATA_SOURCE_HINT = "Site DB"
WORKBOOK_HINT = "Sophia"


def resolve(doctype, hint):
	rows = frappe.get_all(doctype, fields=["name"], limit_page_length=0)
	if not rows:
		return None
	for row in rows:
		if hint.lower() in str(row["name"]).lower():
			return row["name"]
	return rows[0]["name"]


def authored_charts():
	return {cid: spec for cid, spec in chart_registry.CHARTS.items() if spec["status"] == "authored"}


# Fields that must NEVER become a chart dimension, however desperate the
# resolver gets.
#
# `docstatus` is Frappe's internal draft/submitted/cancelled flag. It exists
# on every DocType, so it resolved for everything -- and it was in the
# always-allowed list below, so it was returned WITHOUT even checking the
# schema. That made it the universal fallback: ten charts ended up as a
# single bar labelled "0". "Course Design Status Distribution" showing one
# bar called 0 is worse than an empty placeholder, because it looks like
# analysis. A chart with no real business status must stay unbuilt.
BANNED_DIMENSIONS = {"docstatus", "idx", "owner", "modified_by", "_user_tags",
	"_comments", "_assign", "_liked_by", "parent", "parentfield", "parenttype"}

# Fields that exist on every DocType and need no has_field check. `docstatus`
# used to be in here, which is precisely how it bypassed validation.
ALWAYS_PRESENT = {"name", "creation", "modified"}


def resolve_dimension(doctype, candidates):
	"""The first candidate field that really exists on THIS site's schema AND
	is a legitimate business dimension.

	Returns (field, note). A None field is a chart that stays unbuilt --
	which is the correct outcome when no real status field exists, and the
	whole point of BANNED_DIMENSIONS.
	"""
	try:
		meta = frappe.get_meta(doctype)
	except Exception:
		return None, "DocType %r does not exist on this site" % doctype

	for candidate in candidates:
		if candidate in BANNED_DIMENSIONS:
			# Declared in a spec by mistake: skip it rather than silently
			# charting an internal flag.
			continue
		if candidate in ALWAYS_PRESENT or meta.has_field(candidate):
			return candidate, ""

	# Nothing matched. List what IS there, so the next round is a read rather
	# than another guess -- excluding the banned ones, which are never answers.
	similar = [f.fieldname for f in meta.fields
		if f.fieldname not in BANNED_DIMENSIONS
		and f.fieldtype in ("Select", "Link", "Data")
		and any(token in f.fieldname for token in
			("status", "type", "level", "category", "rating", "state", "group", "stage", "outcome", "result"))]
	return None, "none of %s exist on %s -- real candidates on this schema: %s" % (
		candidates, doctype, similar[:12] or "none found")


def build_operations(spec, data_source, dimension_field):
	"""Insights v3 operations, copied EXACTLY from the shape
	build_admission_intelligence_embed.build_simple_series() uses.

	The first run produced 13 TableNotFound errors on tables that plainly
	exist (Quality Action, Employee, Supplier, Agent, Quality Inspection).
	The cause was not use_live_connection -- that was already set. It was the
	table name: Insights addresses the physical table, so it must be
	"tab" + DocType, not the DocType. Three other shapes were wrong the same
	way, all from writing this from memory instead of copying the version
	that had already been proven on a bench:

	  table_name   "tabQuality Action", not "Quality Action"
	  measures     {"measure_name","column_name","data_type","aggregation"}
	  dimensions   {"dimension_name","column_name","data_type"}
	  filter       {"column": {"column_name": ...}} with no "type" key
	"""
	operations = [{
		"type": "source",
		"table": {"type": "table", "data_source": data_source, "table_name": "tab" + spec["doctype"]},
	}]
	for field, operator, value in spec.get("filters") or []:
		operations.append({
			"type": "filter",
			"column": {"column_name": field},
			"operator": operator,
			"value": value,
		})
	dimension = {"dimension_name": dimension_field, "column_name": dimension_field,
		"data_type": "String"}
	if spec.get("granularity"):
		# Dimension = {..., granularity?} per Insights' own query.types.ts
		# (recorded in create_insights_pilot.py). The KEY is documented; no
		# VALUE string has been proven on a bench, so a chart using this stays
		# unpromoted until one run confirms it. A wrong value errors visibly.
		dimension["data_type"] = "Date"
		dimension["granularity"] = spec["granularity"]
	operations.append({
		"type": "summarize",
		"measures": [{"measure_name": "count", "column_name": "count",
			"data_type": "Integer", "aggregation": "count"}],
		"dimensions": [dimension],
	})
	return operations


def run():
	data_source = resolve("Insights Data Source v3", DATA_SOURCE_HINT)
	workbook = resolve("Insights Workbook", WORKBOOK_HINT)
	if not data_source or not workbook:
		print("STOP -- could not resolve Insights Data Source / Workbook (got %r / %r)." % (data_source, workbook))
		return

	charts = authored_charts()
	print("=" * 72)
	print("BUILDING %d AUTHORED CHART QUERIES" % len(charts))
	print("Registry: %s" % chart_registry.counts())
	print("=" * 72)

	built, skipped, bad_field, failed = [], [], [], []
	resolved_fields = {}

	for chart_id, chart in sorted(charts.items()):
		spec = chart["spec"]
		title = chart["insights_query_title"]

		dimension_field, why = resolve_dimension(spec["doctype"], spec["dimension_candidates"])
		if not dimension_field:
			bad_field.append((chart_id, why))
			print("SCHEMA  %-34s %s" % (chart_id, why))
			continue
		resolved_fields[chart_id] = dimension_field

		existing = frappe.db.get_value("Insights Query v3", {"title": title}, "name")
		if existing:
			# A query built by the FIRST run carries the broken operations. Fix
			# it in place rather than leaving a permanently-failing record that
			# looks built.
			frappe.db.set_value("Insights Query v3", existing, "use_live_connection", 1)
			doc = frappe.get_doc("Insights Query v3", existing)
			doc.operations = build_operations(spec, data_source, dimension_field)
			doc.is_builder_query = 1
			doc.save(ignore_permissions=True)
			skipped.append(chart_id)
			continue

		try:
			doc = frappe.new_doc("Insights Query v3")
			doc.title = title
			doc.workbook = workbook
			doc.data_source = data_source
			doc.is_builder_query = 1
			doc.use_live_connection = 1
			doc.operations = build_operations(spec, data_source, dimension_field)
			doc.insert(ignore_permissions=True)
			built.append(chart_id)
		except Exception as error:
			failed.append((chart_id, "%s: %s" % (type(error).__name__, error)))
			print("FAILED  %-34s %s: %s" % (chart_id, type(error).__name__, error))
	frappe.db.commit()

	if resolved_fields:
		print("\n--- dimension fields resolved against the live schema ---")
		for chart_id, field in sorted(resolved_fields.items()):
			declared = charts[chart_id]["spec"]["dimension_candidates"][0]
			marker = "" if field == declared else "   (fell back from %r)" % declared
			print("   %-34s %s%s" % (chart_id, field, marker))

	print("\n--- executing each built query once ---")
	returning, empty, exec_failed = [], [], []
	for chart_id in sorted(set(built) | set(skipped)):
		title = charts[chart_id]["insights_query_title"]
		name = frappe.db.get_value("Insights Query v3", {"title": title}, "name")
		if not name:
			continue
		try:
			doc = frappe.get_doc("Insights Query v3", name)
			rows = doc.execute(page_size=100).get("rows") or []
			if rows:
				# Preview through the SAME normaliser the dashboard uses, so what
				# this prints is what staff will see. A raw row shows
				# {'status': ''}; the dashboard renders "Not specified". Blank
				# categories are LABELLED, not dropped -- "2 agents have no
				# status recorded" is real information, and dropping them would
				# silently under-count the chart.
				series = rows_to_chart_series(rows)
				returning.append((chart_id, len(rows), series))
				blanks = sum(1 for item in series if item["label"] == "Not specified")
				note = "   (%d blank category)" % blanks if blanks else ""
				print("OK      %-34s %d row(s)  e.g. %s%s" % (
					chart_id, len(rows), {series[0]["label"]: series[0]["value"]}, note))
			else:
				empty.append(chart_id)
				print("EMPTY   %-34s query runs but returns nothing" % chart_id)
		except Exception as error:
			exec_failed.append((chart_id, "%s: %s" % (type(error).__name__, error)))
			print("EXECERR %-34s %s: %s" % (chart_id, type(error).__name__, error))

	print("\n" + "=" * 72)
	print("built=%d  already-present=%d  schema-mismatch=%d  create-failed=%d"
		% (len(built), len(skipped), len(bad_field), len(failed)))
	print("returning-data=%d  empty=%d  exec-failed=%d" % (len(returning), len(empty), len(exec_failed)))
	single_bar = [c for c, _, series in returning if len(series) == 1]
	if single_bar:
		print("\nSINGLE-CATEGORY -- one bar is not a distribution. Check the dimension")
		print("before promoting any of these: %s" % single_bar)
	print("=" * 72)

	if returning:
		print("\nREADY TO PROMOTE -- review each, then set status to 'real' in")
		print("analytics/chart_definitions.py (and change the title prefix):")
		for chart_id, count, series in returning:
			preview = ", ".join("%s=%s" % (item["label"], item["value"]) for item in series[:4])
			print("   %-34s %d rows   %s" % (chart_id, count, preview))
		print("\nReview each preview above. A single category, or one called")
		print("'Not specified' holding everything, means the dimension is wrong --")
		print("do NOT promote it. Promote by adding the chart id to")
		print("chart_registry.BENCH_VERIFIED_CHARTS.")
	if bad_field:
		print("\nSPEC CORRECTIONS NEEDED -- no candidate matched the live schema.")
		print("Each line lists the real status-ish fields on that DocType. Add the")
		print("right one to that chart's candidate list in chart_definitions.py:")
		for chart_id, why in bad_field:
			print("   %-34s %s" % (chart_id, why))
	if empty:
		print("\nEMPTY -- query is valid but this site has no matching rows.")
		print("Could be correct (no data yet) or a wrong filter. Check before promoting:")
		for chart_id in empty:
			print("   %s" % chart_id)


run()
