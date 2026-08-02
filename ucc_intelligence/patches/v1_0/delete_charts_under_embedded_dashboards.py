# Copyright (c) 2026, United Ceres College Pte Ltd
"""Delete the painted charts left underneath embedded Insights dashboards.

Embedding a dashboard used to KEEP a tab's individual charts, hidden, so that
"Stop embedding" could put the tab back (the Option A fallback). Felix retired
that on 2026-08-04: every tab is one embedded dashboard, there is no fallback,
and charts nobody can see sitting in a record nobody reads are configuration
pretending to be a safety net.

So this removes them, permanently, from every tab that has a dashboard
embedded -- across all criteria, not only the ones anyone remembers setting up.

WHAT IS NOT TOUCHED
  Tabs with charts and NO embedded dashboard. Those charts are on screen and
  working; deleting them would blank a tab someone is using. They stop being
  reachable only when that tab is given a dashboard, which deletes them then
  and says so in the audit trail.

  The `intro` text, on any tab. An embedded tab no longer displays it, but
  hiding a block is not a reason to erase what someone wrote.

Every deletion is logged with the criterion, the tab, and the chart ids
removed, so there is a record of exactly what went even though the instruction
to remove it was unconditional.

Idempotent: a second run finds nothing to do, because the first emptied them.
"""

import json

import frappe

DOCTYPE = "UCC Analytics Tab"


def execute():
	if not frappe.db.table_exists(DOCTYPE):
		return

	rows = frappe.get_all(DOCTYPE, fields=["name", "criterion", "tab", "charts"],
		filters={"embedded_dashboard": ["!=", ""]})

	cleared = []
	for row in rows:
		charts = _chart_ids(row.get("charts"))
		if not charts:
			continue
		# db_set on the field alone: this is a data cleanup, not an edit anyone
		# made, so it does not need to run the DocType's save hooks or stamp a
		# modifying user onto institutional configuration.
		frappe.db.set_value(DOCTYPE, row["name"], "charts", "[]", update_modified=False)
		cleared.append((row.get("criterion"), row.get("tab"), charts))

	if not cleared:
		frappe.logger().info("ucc_intelligence: no painted charts were hidden under an "
			"embedded dashboard; nothing to delete")
		return

	total = sum(len(charts) for _, _, charts in cleared)
	frappe.logger().info(
		"ucc_intelligence: deleted %d painted chart(s) from %d tab(s) that embed a "
		"dashboard" % (total, len(cleared)))
	for criterion, tab, charts in cleared:
		frappe.logger().info("ucc_intelligence:   %s / %s -- %s"
			% (criterion, tab, ", ".join(charts)))


def _chart_ids(raw):
	"""The chart ids in a stored `charts` value, whatever shape it is in.

	Written defensively on purpose: this runs once, over real institutional
	records, and a row whose JSON is malformed must not stop the rest of the
	cleanup. Such a row is reported and skipped rather than guessed at.
	"""
	if not raw:
		return []
	try:
		items = json.loads(raw)
	except (ValueError, TypeError):
		frappe.logger().warning("ucc_intelligence: unreadable charts value skipped: %r" % (raw,))
		return []
	if not isinstance(items, list):
		return []
	ids = []
	for item in items:
		if isinstance(item, dict) and item.get("chart"):
			ids.append(str(item["chart"]))
		elif isinstance(item, str) and item:
			ids.append(item)
	return ids
