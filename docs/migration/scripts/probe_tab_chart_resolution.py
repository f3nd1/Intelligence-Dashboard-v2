"""Why a tab card says "no X Axis Column set" when the axes ARE set.

THE SYMPTOM (2026-08-03)
Felix set X Axis and Y Axis on the Chart itself in Insights. Sophia still says
"This chart has no X Axis Column set in Insights."

That message can only be produced AFTER Sophia has found a Chart record -- a
query with no chart says "No Insights chart has been built for this query"
instead. So the chart IS being found, and its `config` genuinely has no
`x_axis`. There are three candidate explanations and they need different fixes:

  A. The tab points at the WRONG Insights record. Insights creates a backing
     `data_query` when a chart is built, so a tab entry added before the chart
     existed may resolve to a different chart than the one Felix edited.

  B. The axes were written under DIFFERENT KEYS. The 2026-08-02 probe found
     `x_axis`/`y_axis` populated and `xAxis`/`yAxis` empty on older charts. If
     the current builder writes the camelCase pair instead, a freshly-edited
     chart would have real values under keys Sophia was told to ignore.

  C. The axes are stored somewhere other than `config` entirely.

WHAT THE 2026-08-03 RUN ACTUALLY FOUND, and what it got wrong
Two of three cards resolved and drew. The third -- a Donut -- did not, and this
script reported "axes are present under x_axis; Sophia should draw this" about
it. That was a FALSE POSITIVE: its x_axis is {"dimension": {}}, an empty
wrapper, and `bool({"dimension": {}})` is True. The real value was in
`label_column`.

So this script no longer judges by truthiness. It imports
`analytics.chart_presentation` and prints what the APP resolves, including the
key order it tried and the final verdict. A probe that can disagree with the
code is worse than no probe.

This prints enough to tell them apart. It does NOT change anything, and the
fix is chosen from the output rather than from a hypothesis.

RUN
    bench --site <site> console
    >>> exec(open("/home/felixoking/Intelligence-Dashboard-v2/docs/migration/scripts/probe_tab_chart_resolution.py").read(), globals())

SAFETY
Read-only. Creates nothing, changes nothing, executes one query per card to
learn its column names.
"""

import json

import frappe

from ucc_intelligence.analytics import chart_presentation

TAB_DOCTYPE = "UCC Analytics Tab"
QUERY_DOCTYPE = "Insights Query v3"
CHART_DOCTYPE = "Insights Chart v3"

AXIS_KEYS = ("x_axis", "y_axis", "xAxis", "yAxis")


def head(number, title):
	print("\n" + "=" * 72)
	print("%s. %s" % (number, title))
	print("=" * 72)


def config_of(row):
	raw = row.get("config") if isinstance(row, dict) else row.config
	if isinstance(raw, dict):
		return raw
	try:
		parsed = json.loads(raw or "{}")
	except Exception:
		return {}
	return parsed if isinstance(parsed, dict) else {}


def tab_entries():
	"""Every card on every tab, with the tab it sits on."""
	entries = []
	for row in frappe.get_all(TAB_DOCTYPE, fields=["name", "criterion", "tab", "charts"]):
		try:
			items = json.loads(row.get("charts") or "[]")
		except Exception:
			continue
		for item in items:
			chart = item.get("chart") if isinstance(item, dict) else item
			if chart:
				entries.append((row.get("name"), chart))
	return entries


def run():
	head(1, "WHAT EACH TAB CARD POINTS AT, AND WHAT RESOLVES FROM IT")
	entries = tab_entries()
	if not entries:
		print("   no cards are configured on any tab")
		return
	print("   %d card(s) across all tabs\n" % len(entries))

	for tab_name, stored_id in entries:
		print("   " + "-" * 66)
		print("   card on %s  ->  stored id: %s" % (tab_name, stored_id))

		is_query = bool(frappe.db.exists(QUERY_DOCTYPE, stored_id))
		is_chart = bool(frappe.db.exists(CHART_DOCTYPE, stored_id))
		print("      that id is a QUERY: %s   a CHART: %s" % (is_query, is_chart))
		if is_query:
			print("      query title: %r" % (frappe.db.get_value(QUERY_DOCTYPE, stored_id, "title") or ""))

		# Exactly what chart_presentation.chart_record_for() does, printed.
		found = None
		for field in ("query", "data_query"):
			rows = frappe.get_list(CHART_DOCTYPE, filters={field: stored_id},
				fields=["name", "title", "chart_type", "config", "query", "data_query"],
				order_by="modified desc", limit_page_length=5) or []
			print("      charts whose `%s` = this id: %s"
				% (field, [r["name"] for r in rows] or "none"))
			if rows and not found:
				found = rows[0]

		if not found:
			print("      -> NO CHART RESOLVES. The card would say 'No Insights chart")
			print("         has been built for this query.' If Felix HAS built one,")
			print("         explanation A applies: it points at a different record.")
			continue

		print("      -> RESOLVES TO: %s  %r  (type %r)"
			% (found["name"], found.get("title") or "", found.get("chart_type") or ""))
		config = config_of(found)
		print("      config keys: %s" % sorted(config))
		for key in AXIS_KEYS:
			if key in config:
				print("        %-8s %s" % (key, json.dumps(config[key], default=str)[:120]))

		# THE RESOLVED COLUMN, from the app's OWN code -- not a truthiness
		# check on x_axis.
		#
		# The 2026-08-03 run said "axes are present under x_axis; Sophia should
		# draw this" for a Donut whose x_axis was {"dimension": {}} -- an empty
		# wrapper. bool({"dimension": {}}) is True, so the probe declared a
		# chart healthy that could not draw. A probe that disagrees with the
		# code is worse than no probe, so this now CALLS the code.
		render_as = chart_presentation.SUPPORTED_TYPES.get(
			(found.get("chart_type") or "").lower())
		if not render_as:
			print("      -> chart type %r is not one Sophia draws; the card shows"
				% (found.get("chart_type") or ""))
			print("         its rows as a table, which is a real view, not a failure.")
		else:
			label, values = chart_presentation.resolve_axes(config, render_as)
			print("      keys tried, in order: %s"
				% (chart_presentation.axis_keys_for(render_as),))
			print("      RESOLVED label column: %r" % label)
			print("      RESOLVED value columns: %r" % values)
			if label and values:
				print("      -> Sophia resolves both. If the card still does not draw,")
				print("         the columns do not match what the query returns -- see below.")
			elif label:
				print("      -> no VALUE column resolves. The card will show its rows.")
			else:
				print("      -> no LABEL column resolves from any key. The card will")
				print("         show its rows and say why.")

		# What the query really returns, since a config column that is not a
		# real column is also withheld -- and looks identical from the outside.
		try:
			query_id = found.get("query") or found.get("data_query")
			doc = frappe.get_doc(QUERY_DOCTYPE, query_id)
			doc.check_permission("read")
			rows = (doc.execute(page_size=1) or {}).get("rows") or []
			columns = list(rows[0].keys()) if rows else []
			print("      the query returns columns: %s" % (columns or "no rows"))
			# The final word: run the whole presentation exactly as the card
			# does, and print its verdict verbatim.
			verdict = chart_presentation.presentation_for(
				found.get("query") or found.get("data_query"), columns=columns)
			print("      SOPHIA'S OWN VERDICT: %s" % verdict.get("status"))
			if verdict.get("reason"):
				print("        reason: %s" % verdict["reason"])
		except Exception as error:
			print("      could not execute the query: %s" % error)

	head("1c", "NOTE ON A PREVIOUS RUN")
	print("   The 2026-08-03 run printed 'Insights Query v3 None not found' for")
	print("   every card. That was THIS SCRIPT's bug, not the app's: it asked")
	print("   get_list for name/title/chart_type/config and then read `query`,")
	print("   which it had never fetched. Fixed. It said nothing about Sophia.")

	head(2, "WHICH CHARTS FELIX HAS EDITED MOST RECENTLY")
	print("   If the chart he edited is NOT one of the records above, the tab")
	print("   is pointing somewhere else and explanation A is the answer.\n")
	for row in frappe.get_list(CHART_DOCTYPE,
			fields=["name", "title", "chart_type", "query", "data_query", "modified"],
			order_by="modified desc", limit_page_length=10) or []:
		print("   %-14s %-40s type=%-8s query=%s  modified=%s"
			% (row["name"], (row.get("title") or "")[:40], row.get("chart_type") or "?",
				row.get("query") or row.get("data_query") or "?", row.get("modified")))

	head("NEXT", "WHAT TO PASTE BACK")
	print("Both sections. Section 1 says what each card resolves to and whether")
	print("its axes are anywhere; section 2 says whether that is the chart you")
	print("actually edited. Between them the explanation is A, B or C, and the")
	print("fix is different for each.")


run()
