"""Runtime for the Insights-backed chart layer.

Resolves a chart id through chart_registry, and for charts whose Insights
query is real, executes it server-side with ordinary Frappe permissions
applied. Reuses admission_intelligence_embed.run_chart_query() rather than
opening a second execution path -- that function is the one whose
permission behaviour was proved on a real bench (a restricted user got a
hard refusal, the same user with access got real rows), and a second copy
would be a second thing to prove.

A placeholder chart returns `status: "placeholder"` and NO data. It does
not invent rows. The frontend keeps rendering that card from the criterion
API's own real numbers and badges it as awaiting its Insights definition --
so nothing on screen is fabricated, and the badge says exactly what is
outstanding.
"""

import frappe

from ucc_intelligence.analytics import chart_registry
from ucc_intelligence.analytics.admission_intelligence_embed import (
	rows_to_chart_series,
	run_chart_query,
)


def get_chart(chart_id):
	"""One chart's data and provenance. Never raises: an unknown id, an
	unbuilt query or a denied permission all come back as a status the card
	can render, because a chart failing must degrade to an explained empty
	card, never a broken dashboard (CLAUDE.md §14.3)."""
	spec = chart_registry.get(chart_id)
	if not spec:
		return {
			"ok": False,
			"chart_id": chart_id,
			"status": "unknown_chart",
			"message": "No chart is registered under that id.",
			"series": [],
		}

	base = {
		"ok": True,
		"chart_id": chart_id,
		"criterion": spec["criterion"],
		"type": spec["type"],
		"title": spec["title"],
		"definition_status": spec["status"],
		"insights_query_title": spec["insights_query_title"],
	}

	if spec["status"] == "computed":
		# Decision A: not an Insights chart. The frontend answers it from the
		# criterion API response it already holds, so this endpoint returns the
		# classification and no data -- fetching it here would be a second
		# round trip for numbers the page already has.
		return dict(base, status="computed", series=[], message=spec.get("composite_reason") or "")

	if spec["status"] != "real":
		return dict(base, status="placeholder", series=[], message=(
			"An Insights query is authored for this chart but has not been built "
			"and verified on this site yet."
		))

	result = run_chart_query(spec["insights_query_title"])
	if result["status"] != "available":
		return dict(base, status=result["status"], series=[], message=result.get("message") or "")
	return dict(base, status="available", series=rows_to_chart_series(result["rows"]))


def get_definitions(criterion=None):
	"""What the chart layer looks like right now -- every chart, whether its
	Insights definition is real, and which query answers it. Drives both the
	frontend badges and the Settings status page, so migration progress is
	something you can read rather than something asserted in a report."""
	charts = chart_registry.for_criterion(criterion) if criterion else chart_registry.CHARTS
	return {
		"ok": True,
		"counts": chart_registry.counts(),
		"charts": [
			{
				"chart_id": chart_id,
				"criterion": spec["criterion"],
				"type": spec["type"],
				"title": spec["title"],
				"definition_status": spec["status"],
				"insights_query_title": spec["insights_query_title"],
				"composite_reason": spec.get("composite_reason", ""),
			}
			for chart_id, spec in sorted(charts.items())
		],
	}


def get_charts(chart_ids):
	"""Batch, so one dashboard section is one round trip rather than one per
	card. Capped: a caller cannot ask for unbounded work."""
	if isinstance(chart_ids, str):
		chart_ids = frappe.parse_json(chart_ids) or []
	if not isinstance(chart_ids, list):
		return {"ok": False, "message": "chart_ids must be a list.", "charts": {}}
	chart_ids = [frappe.utils.cstr(c).strip() for c in chart_ids[:60] if frappe.utils.cstr(c).strip()]
	return {"ok": True, "charts": {chart_id: get_chart(chart_id) for chart_id in chart_ids}}
