"""Live Insights-embed implementation of Criterion 4's admission_intelligence
(4 KPIs + 6 chart series) -- Option B, confirmed with Felix after a real
bench permission test proved private (non-public) Insights Query v3
execution respects real per-user Frappe permissions: a restricted test
user got 0 rows from Query.execute(), the same user with real access got
6 rows (docs/migration/insights-pilot-findings.md's "Update, 2026-07-29"
section; test script: docs/migration/scripts/test_insights_private_permissions.py).

Each of the 6 chart series is backed by a real Insights Query v3 record
created by docs/migration/scripts/build_admission_intelligence_embed.py,
authored against Site DB with use_live_connection=1 -- every request runs
a fresh live query against the site's own database, same as
criterion_4.py's plain-Python engine always did. This module never uses
Insights' public-dashboard/is_public mechanism anywhere -- proven unsafe
(insights-pilot-findings.md Section 4(b)): a public Insights dashboard
skips row/column permission filtering unconditionally, confirmed from the
real source, not assumed.

**Operational dependency that must stay visible**: permission enforcement
here depends entirely on ONE site-wide toggle,
`Insights Settings.apply_user_permissions`. It ships default=1 and was
confirmed ON during the real bench test this module's design is based on,
but it is a normal site setting any admin could switch off later -- if
that happens, every chart below silently stops filtering rows by the
viewer's Frappe DocType permissions (insights_table_v3.py's
apply_user_permissions() short-circuits to a no-op filter the moment this
setting is 0). This is not a per-chart or per-query setting -- there is
no way to pin it from this module. Whoever owns the Insights install
needs to know that turning it off breaks permission enforcement for every
embedded chart at once, not just degrade one.

`criterion_4.py`'s `build_admission_intelligence()` (the pre-Insights
engine) is untouched, still importable, and NOT called from here or wired
into the frontend for these 6 series anymore -- kept as dead code for
reference/rollback per Felix's explicit instruction, not deleted.

**Known gap versus the pre-Insights engine**: the `academic_year` request
filter the old engine applied to every query is not supported here.
Insights' `execute()` accepts an `adhoc_filters` parameter that could
plausibly do this, but its exact shape wasn't verified against live
Insights source in the time available this round -- flagged as an open
gap, not silently dropped.
"""

import frappe

from ucc_intelligence.analytics.engine import clean_text

# Must stay in sync with build_admission_intelligence_embed.py's own
# CHART_TITLES -- both hardcode the same 6 titles because a bench-console
# script and this installed app module can't share Python state at
# runtime. Six short strings duplicated once is simpler than building
# shared config infrastructure for it.
CHART_TITLES = {
	"applicants_by_year": "Sophia Pilot - Student Applicants per Year",
	"enrolled_by_year": "Sophia AI - Enrolled Students per Year",
	"applicants_by_country": "Sophia AI - Applicants per Country",
	"programmes": "Sophia AI - Popular Courses of Full Qualification",
	"agents": "Sophia AI - Number of Students per Agent",
	"counselling_to_admission": "Sophia AI - Counselling to Admission Duration",
}

# The real underlying DocType each chart's Insights query reads from -- used
# only for the blocked-source label, so a permission_denied entry displays
# the same way every other criterion's blocked sources already do
# (sophia_analytics.js's displayDoctypeName()), not an internal query title.
CHART_DOCTYPES = {
	"applicants_by_year": "Student Applicant",
	"enrolled_by_year": "Student Applicant",
	"applicants_by_country": "Student Applicant",
	"programmes": "Student Applicant",
	"agents": "Student Applicant",
	"counselling_to_admission": "Student Admission UCC",
}

# Keys a chart's execute() result rows might carry that are measures, not
# the grouping dimension -- used to find "the other column" in each row.
KNOWN_MEASURE_KEYS = ("count", "avg_duration")


def run_chart_query(title):
	"""Execute one chart's Insights Query v3 -- private (is_public never
	set), permission-checked via the same check_permission("read") +
	execute() call proved safe on a real bench
	(test_insights_private_permissions.py). Not insights.api.run_doc_method
	-- that wrapper also calls is_valid_http_method()/add_data_to_monitor(),
	which need a real frappe.request; this method always runs inside one
	(a real whitelisted HTTP call), so it's not the bug that hit bench
	console, but calling check_permission()+execute() directly is simpler
	and does the identical permission work either way."""
	query_name = frappe.db.get_value("Insights Query v3", {"title": title}, "name")
	if not query_name:
		return {"status": "unavailable", "message": "Chart query %r has not been created yet." % title, "rows": []}
	try:
		doc = frappe.get_doc("Insights Query v3", query_name)
		doc.check_permission("read")
		result = doc.execute(page_size=1000)
		return {"status": "available", "rows": result.get("rows") or []}
	except frappe.PermissionError as error:
		return {"status": "permission_denied", "message": clean_text(error), "rows": []}
	except Exception as error:
		return {"status": "query_error", "message": clean_text(error), "rows": []}


def rows_to_chart_series(rows):
	"""An Insights execute() result row looks like {dimension_field: value,
	"count": n} (or {..., "avg_duration": n, "count": n} for the duration
	chart) -- convert to the {label, value} shape sophia_analytics.js's
	metricRows() already expects (criterion_4.py's group_count_rows()
	produces the same shape, so the frontend needs no changes)."""
	if not rows:
		return []
	first_row = rows[0]
	value_key = "avg_duration" if "avg_duration" in first_row else "count"
	dimension_key = next((key for key in first_row.keys() if key not in KNOWN_MEASURE_KEYS), None)
	series = []
	for row in rows:
		label = clean_text(row.get(dimension_key)) or "Not specified"
		series.append({"label": label, "value": row.get(value_key) or 0})
	return series


def compute_kpis(applicants_by_year_series, enrolled_by_year_series):
	applicant_total = sum(item.get("value") or 0 for item in applicants_by_year_series)
	enrolled_total = sum(item.get("value") or 0 for item in enrolled_by_year_series)
	success_rate = round((float(enrolled_total) / float(applicant_total)) * 100.0, 2) if applicant_total else 0.0

	# "Shortlisted" (Approved status) isn't one of the 6 chart series -- a
	# single permission-respecting frappe.get_list count (same permission
	# model as everything else here) for one scalar number, rather than a
	# 7th Insights query for it.
	try:
		approved_total = len(frappe.get_list(
			"Student Applicant", filters={"application_status": "Approved"}, fields=["name"], limit_page_length=0,
		))
	except Exception:
		approved_total = 0

	return [
		{"id": "c411-applicants-total", "label": "No. of Student Applicants", "value": applicant_total, "unit": "records"},
		{"id": "c411-shortlisted-approved", "label": "No. of Shortlisted", "value": approved_total, "unit": "records"},
		{"id": "c411-enrolled-admitted", "label": "No. of Enrolled Students", "value": enrolled_total, "unit": "records"},
		{"id": "c411-success-rate", "label": "Success Rate", "value": success_rate, "unit": "percent"},
	]


def run():
	charts = {}
	chart_status = {}
	blocked_sources = []

	for data_key, title in CHART_TITLES.items():
		result = run_chart_query(title)
		chart_status[data_key] = result["status"]
		charts[data_key] = rows_to_chart_series(result["rows"]) if result["status"] == "available" else []
		if result["status"] == "permission_denied":
			blocked_sources.append({
				"status": "permission_denied",
				"doctype": CHART_DOCTYPES.get(data_key, title),
				"message": result.get("message"),
			})

	kpis = compute_kpis(charts.get("applicants_by_year") or [], charts.get("enrolled_by_year") or [])
	all_blocked = blocked_sources and len(blocked_sources) == len(CHART_TITLES)

	return {
		"status": "permission_denied" if all_blocked else "available",
		"kpis": kpis,
		"charts": charts,
		"chart_status": chart_status,
		"sources": blocked_sources,
		"notes": [
			"Charts are served live via Frappe Insights Query v3 (Site DB, "
			"use_live_connection=1), not the plain-Python engine.",
		],
	}
