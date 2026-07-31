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


def field_exists(doctype, fieldname):
	"""Whether this site's schema actually has the field the spec assumes.
	Checked BEFORE building, so a wrong guess is reported as a wrong guess
	rather than as a mysterious empty chart."""
	try:
		meta = frappe.get_meta(doctype)
	except Exception:
		return False, "DocType %r does not exist on this site" % doctype
	if fieldname in ("name", "creation", "modified", "owner", "docstatus"):
		return True, ""
	if not meta.has_field(fieldname):
		candidates = [f.fieldname for f in meta.fields
			if f.fieldtype in ("Select", "Link", "Data") and (
				"status" in f.fieldname or "type" in f.fieldname or "level" in f.fieldname)]
		return False, "field %r not on %s (similar: %s)" % (fieldname, doctype, candidates[:6] or "none")
	return True, ""


def build_operations(spec):
	"""Insights v3 operations for a group-by count.

	NOTE: this mirrors the operations shape build_admission_intelligence_embed.py
	produced and verified on a real bench. If Insights' schema differs on this
	site's version, THIS is the function to correct -- everything else is
	version-independent.
	"""
	operations = [{
		"type": "source",
		"table": {"data_source": spec["_data_source"], "table_name": spec["doctype"], "type": "table"},
	}]
	for field, operator, value in spec.get("filters") or []:
		operations.append({
			"type": "filter",
			"column": {"type": "column", "column_name": field},
			"operator": operator,
			"value": value,
		})
	operations.append({
		"type": "summarize",
		"measures": [{"type": "measure", "measure_name": "count", "aggregation": "count", "data_type": "Integer"}],
		"dimensions": [{"type": "dimension", "column_name": spec["dimension"], "data_type": "String"}],
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

	for chart_id, chart in sorted(charts.items()):
		spec = dict(chart["spec"])
		spec["_data_source"] = data_source
		title = chart["insights_query_title"]

		ok, why = field_exists(spec["doctype"], spec["dimension"])
		if not ok:
			bad_field.append((chart_id, why))
			print("SCHEMA  %-34s %s" % (chart_id, why))
			continue

		if frappe.db.get_value("Insights Query v3", {"title": title}, "name"):
			skipped.append(chart_id)
			continue

		try:
			doc = frappe.new_doc("Insights Query v3")
			doc.title = title
			doc.workbook = workbook
			doc.data_source = data_source
			doc.use_live_connection = 1
			doc.operations = frappe.as_json(build_operations(spec))
			doc.insert(ignore_permissions=True)
			built.append(chart_id)
		except Exception as error:
			failed.append((chart_id, "%s: %s" % (type(error).__name__, error)))
			print("FAILED  %-34s %s: %s" % (chart_id, type(error).__name__, error))
	frappe.db.commit()

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
				returning.append((chart_id, len(rows)))
				print("OK      %-34s %d row(s)  e.g. %s" % (chart_id, len(rows), rows[0]))
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
	print("=" * 72)

	if returning:
		print("\nREADY TO PROMOTE -- review each, then set status to 'real' in")
		print("analytics/chart_definitions.py (and change the title prefix):")
		for chart_id, count in returning:
			print("   %-34s %d rows" % (chart_id, count))
	if bad_field:
		print("\nSPEC CORRECTIONS NEEDED -- the dimension field guess was wrong.")
		print("Each line names the field that does not exist and offers similar ones:")
		for chart_id, why in bad_field:
			print("   %-34s %s" % (chart_id, why))
	if empty:
		print("\nEMPTY -- query is valid but this site has no matching rows.")
		print("Could be correct (no data yet) or a wrong filter. Check before promoting:")
		for chart_id in empty:
			print("   %s" % chart_id)


run()
