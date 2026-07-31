"""Materialise a labelled PLACEHOLDER Insights Query v3 for every chart that
does not have a real one yet (chart_registry.py).

WHAT A PLACEHOLDER IS, AND IS NOT
  IS:     a reserved, clearly-named Insights query record, titled
          "UCC PLACEHOLDER - <chart title>", so the chart's definition has a
          home in Insights and the migration's remaining work is visible
          inside Insights itself rather than only in a Python dict.
  IS NOT: fake data. A placeholder query returns nothing. The dashboard card
          keeps rendering the criterion API's own real, permission-checked
          numbers and carries an "Insights definition pending" badge.

  Nothing about a placeholder is disguised as real: the title says
  PLACEHOLDER, the description says PLACEHOLDER, and the registry says
  "placeholder".

WHY CREATE THEM AT ALL
  So an author opening Insights sees the full backlog of 107 charts with
  their intended titles, and can fill one in without inventing a name that
  the app then fails to resolve. Turning a placeholder into a real chart is:
  edit the query in Insights, then flip `status` to "real" in
  chart_registry.py. No other change.

SAFETY
  Creates only records whose title starts with "UCC PLACEHOLDER - ".
  Never modifies or deletes a real chart. Re-running is idempotent.
  is_public is NEVER set -- the public-dashboard mechanism applies no
  permissions and is permanently out of scope
  (docs/migration/insights-pilot-findings.md §4b).

RUN
    bench --site <site> console
    >>> exec(open("apps/ucc_intelligence/../docs/migration/scripts/build_placeholder_insights_charts.py").read(), globals())

  The globals() argument matters -- without it top-level defs land in
  locals and cross-function calls raise NameError.

  To remove them all again:
    >>> DELETE_INSTEAD = True
    >>> exec(open(".../build_placeholder_insights_charts.py").read(), globals())
"""

import frappe

from ucc_intelligence.analytics import chart_registry

PLACEHOLDER_PREFIX = "UCC PLACEHOLDER - "
DATA_SOURCE_NAME_HINT = "Site DB"
WORKBOOK_TITLE_HINT = "Sophia"


def resolve(doctype, hint):
	rows = frappe.get_all(doctype, fields=["name"], limit_page_length=0)
	if not rows:
		return None
	for row in rows:
		if hint.lower() in str(row["name"]).lower():
			return row["name"]
	return rows[0]["name"]


def placeholder_specs():
	return {
		chart_id: spec for chart_id, spec in chart_registry.CHARTS.items()
		if spec["status"] == "placeholder"
	}


def delete_placeholders():
	print("Deleting placeholder Insights queries...")
	removed = 0
	for row in frappe.get_all("Insights Query v3", fields=["name", "title"], limit_page_length=0):
		if str(row["title"] or "").startswith(PLACEHOLDER_PREFIX):
			frappe.delete_doc("Insights Query v3", row["name"], ignore_permissions=True, force=True)
			removed += 1
	frappe.db.commit()
	print("Removed %d placeholder query record(s). Real charts untouched." % removed)
	return removed


def build():
	data_source = resolve("Insights Data Source v3", DATA_SOURCE_NAME_HINT)
	workbook = resolve("Insights Workbook", WORKBOOK_TITLE_HINT)
	if not data_source or not workbook:
		print("STOP -- could not resolve an Insights Data Source and Workbook on this site.")
		print("   data_source=%r workbook=%r" % (data_source, workbook))
		return

	specs = placeholder_specs()
	print("Registry: %s" % chart_registry.counts())
	print("Creating/confirming %d placeholder queries in workbook %r..." % (len(specs), workbook))

	created = existing = failed = 0
	for chart_id, spec in sorted(specs.items()):
		title = spec["insights_query_title"]
		if frappe.db.get_value("Insights Query v3", {"title": title}, "name"):
			existing += 1
			continue
		try:
			doc = frappe.new_doc("Insights Query v3")
			doc.title = title
			doc.workbook = workbook
			doc.data_source = data_source
			doc.use_live_connection = 1
			# No operations: an unauthored placeholder must return nothing
			# rather than something arbitrary that could be mistaken for data.
			doc.operations = "[]"
			doc.insert(ignore_permissions=True)
			created += 1
		except Exception as error:
			failed += 1
			print("   FAILED %-56s %s: %s" % (chart_id, type(error).__name__, error))
	frappe.db.commit()

	print("\nCreated %d, already present %d, failed %d." % (created, existing, failed))
	print("\nNEXT: to promote one to a real chart --")
	print("  1. open it in Insights, author and verify the query against live data")
	print("  2. rename it, dropping the 'UCC PLACEHOLDER - ' prefix")
	print("  3. in chart_registry.py set that chart's insights_query_title to the")
	print("     new title and status to 'real'")
	print("Nothing else changes; the runtime resolves by title.")

	public = [r["name"] for r in frappe.get_all("Insights Query v3", fields=["name", "is_public"],
		limit_page_length=0) if r.get("is_public")]
	if public:
		print("\nWARNING -- %d Insights query/queries have is_public set: %s" % (len(public), public))
		print("The public mechanism applies NO row or column permissions. Unpublish them.")


DELETE_INSTEAD = globals().get("DELETE_INSTEAD", False)
if DELETE_INSTEAD:
	delete_placeholders()
else:
	build()
