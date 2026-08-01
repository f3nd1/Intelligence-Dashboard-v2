# Copyright (c) 2026, United Ceres College Pte Ltd
"""Move per-user Sophia tab configuration into the shared UCC Analytics Tab.

Charts, tab intro text and hidden questions were stored in `frappe.defaults`,
per user, under keys like `ucc_sophia_tab_charts:criterion_3:overview`. They are
institutional configuration -- what one person sets is what the auditor should
see -- so they now live in one shared record per tab.

Nothing already configured is lost: this reads every one of those defaults and
writes it into the shared record.

WHEN TWO PEOPLE CONFIGURED THE SAME TAB
Realistically one person has, but the rule is stated rather than left to
whichever row the database returned first:

  charts            union, in the order first seen, capped at MAX_PER_TAB.
                    Losing someone's chart would be the worse error.
  hidden questions  union. Hiding is a curation decision; keeping a question
                    hidden that someone hid is safer than resurfacing it, and
                    it is one click to show again.
  intro             the FIRST non-empty one, with every other candidate written
                    to the log so nothing disappears unrecorded. Concatenating
                    two people's prose would produce text neither wrote.

Idempotent: a tab that already has a shared record is left alone, so re-running
migrate never overwrites what someone has since edited on the shared version.
"""

import json

import frappe

from ucc_intelligence.analytics.tab_charts import (
	CONFIG_DOCTYPE, DEFAULT_SPAN, GRID_COLUMNS, LEGACY_DEFAULTS_PREFIX, LEGACY_SIZE_SPANS,
	MAX_PER_TAB, MAX_QUESTION_IDS,
)


def parse(raw):
	"""The stored value, in either shape it ever had: the original bare list of
	chart ids, or the later {charts, intro, questions} object."""
	try:
		stored = json.loads(raw or "")
	except (TypeError, ValueError):
		return None
	if isinstance(stored, list):
		stored = {"charts": stored}
	if not isinstance(stored, dict):
		return None

	charts = []
	for item in stored.get("charts") or []:
		if isinstance(item, str) and item:
			charts.append({"chart": item, "span": DEFAULT_SPAN})
		elif isinstance(item, dict) and item.get("chart"):
			# Written before drag-resize, so these carry a size NAME. Mapped
			# here rather than left for the reader, so the migrated record is
			# already in the shape everything now expects.
			try:
				span = int(item.get("span"))
			except (TypeError, ValueError):
				span = LEGACY_SIZE_SPANS.get(item.get("size"), DEFAULT_SPAN)
			charts.append({"chart": str(item["chart"]), "span": max(1, min(span, GRID_COLUMNS))})

	questions = stored.get("questions") or {}
	hidden = questions.get("hidden") if isinstance(questions, dict) else None
	return {
		"charts": charts,
		"intro": stored.get("intro") if isinstance(stored.get("intro"), str) else "",
		"hidden": [str(q) for q in (hidden or []) if isinstance(q, str) and q],
	}


def execute():
	if not frappe.db.table_exists(CONFIG_DOCTYPE):
		return

	rows = frappe.db.sql(
		"""SELECT parent AS user, defkey, defvalue FROM `tabDefaultValue`
		   WHERE defkey LIKE %s ORDER BY parent, defkey""",
		(LEGACY_DEFAULTS_PREFIX + ":%",), as_dict=True) or []
	if not rows:
		return

	merged = {}
	for row in rows:
		parts = row["defkey"].split(":")
		if len(parts) != 3:
			continue
		_, criterion, tab = parts
		parsed = parse(row["defvalue"])
		if not parsed:
			continue
		target = merged.setdefault((criterion, tab), {"charts": [], "intro": "", "hidden": [], "users": []})
		target["users"].append(row["user"])
		seen = {item["chart"] for item in target["charts"]}
		for item in parsed["charts"]:
			if item["chart"] not in seen:
				target["charts"].append(item)
				seen.add(item["chart"])
		for question in parsed["hidden"]:
			if question not in target["hidden"]:
				target["hidden"].append(question)
		if parsed["intro"] and not target["intro"]:
			target["intro"] = parsed["intro"]
		elif parsed["intro"] and parsed["intro"] != target["intro"]:
			frappe.log_error(
				title="UCC tab intro not migrated (a shared intro was already chosen)",
				message="%s/%s, from %s:\n\n%s" % (criterion, tab, row["user"], parsed["intro"]))

	created = 0
	for (criterion, tab), config in sorted(merged.items()):
		name = "%s::%s" % (criterion, tab)
		if frappe.db.exists(CONFIG_DOCTYPE, name):
			continue
		record = frappe.new_doc(CONFIG_DOCTYPE)
		record.update({
			"criterion": criterion,
			"tab": tab,
			"intro": config["intro"],
			"charts": json.dumps(config["charts"][:MAX_PER_TAB]),
			"hidden_questions": json.dumps(config["hidden"][:MAX_QUESTION_IDS]),
		})
		record.insert(ignore_permissions=True)
		created += 1

	# The old defaults are deliberately LEFT IN PLACE. They are small, they are
	# the only copy of what each person had, and deleting them would make this
	# patch unrepeatable if the shared records ever needed rebuilding.
	frappe.db.commit()
	print("UCC Analytics Tab: migrated %d tab(s) from %d per-user record(s)" % (created, len(rows)))
