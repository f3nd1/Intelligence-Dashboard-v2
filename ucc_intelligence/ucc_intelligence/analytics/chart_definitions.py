"""Authored Frappe Insights definitions, chart by chart, criterion by
criterion.

HOW THESE WERE PRODUCED
Each criterion module's SOURCE_CANDIDATES (source key -> DocType) and its
CONFIG sections were read, and each chart was judged individually against
what it is actually asking. They are NOT mechanically derived from the
metric code -- deriving them would have produced a query per metric, which
is not what these charts show.

THE FINDING THAT SHAPED THIS FILE
The 107 charts fall into two genuinely different kinds, and only one of them
is expressible as a single Insights query:

  AUTHORED  A group-by over ONE DocType returning label/value rows.
            "Status Distribution" = count Quality Action by status.
            These have a real spec below and the bench script builds them.

  COMPOSITE A visualisation OVER THE CRITERION ENGINE'S OWN COMPUTED
            METRIC SET, not over a table. "Control Coverage" is how many of
            this subcriterion's configured controls resolved; "Source
            Availability" is which DocTypes this user may read; "Evidence
            Readiness" and "Exception Profile" score across many metrics at
            once. An Insights query returns rows from a data source -- it
            cannot express "how much of my own metric catalogue came back
            available", because that is a property of the request, not of
            the data.

            These are recorded below with the reason, and stay placeholder.
            Making them real needs a decision (see the consolidated list):
            either a derived table/view Insights can query, or accept that
            this class of chart is not an Insights chart.

STATUS VALUES
  "authored"     spec written and ready; build_insights_charts_from_specs.py
                 creates the Insights Query, after which it is verified and
                 flipped to "real".
  "real"         the Insights Query exists and was verified on a bench.
  "placeholder"  no spec -- either composite (see above) or not yet reached.

Nothing here is marked real that has not been verified on a bench. The six
admission_intelligence charts are the only "real" entries today.
"""

# Reasons a chart is composite rather than a single query. Named constants so
# the same reason reads identically everywhere and can be counted.
COMPOSITE_COVERAGE = (
	"COMPOSITE: measures how many of this subcriterion's configured controls "
	"resolved, which is a property of the criterion engine's metric catalogue, "
	"not of any one table."
)
COMPOSITE_AVAILABILITY = (
	"COMPOSITE: shows which source DocTypes the CURRENT USER may read. That is "
	"per-request permission state, not data -- no query can return it."
)
COMPOSITE_TARGETS = (
	"COMPOSITE: gap between each metric and its configured target, computed "
	"across the whole metric set."
)
COMPOSITE_EXCEPTIONS = (
	"COMPOSITE: aggregates exception counts across many metrics and DocTypes at "
	"once; a single group-by cannot express it."
)
COMPOSITE_READINESS = (
	"COMPOSITE: scores evidence presence across several DocTypes per dimension; "
	"needs a derived table before Insights can query it."
)
COMPOSITE_LIFECYCLE = (
	"COMPOSITE: stage progression across several DocTypes (application -> "
	"screening -> contract -> onboarding); one query cannot span the chain."
)

# --- helper so an authored spec is one readable line -------------------------
def q(doctype, dimension, label, measure="count", filters=None, order="value desc", limit=20):
	"""One authored Insights query: group `doctype` by a dimension, count rows.

	`dimension` may be a single field name or a LIST of candidates. Candidates
	exist because the first bench run rejected 17 of 30 specs on field names:
	guessing one name per chart from a DocType's purpose is unreliable, and a
	single wrong guess kills the chart. The builder resolves candidates
	against the live schema and takes the first that exists -- the same
	verify-before-build discipline build_admission_intelligence_embed.py
	already uses (resolve_field_live).

	`filters` is a list of [field, operator, value]. Declarative, so the
	builder can create the Insights Query without this module knowing
	anything about Insights' internals.
	"""
	return {
		"doctype": doctype,
		"dimension_candidates": [dimension] if isinstance(dimension, str) else list(dimension),
		"measure": measure,
		"label": label,
		"filters": filters or [],
		"order": order,
		"limit": limit,
	}


def composite(reason):
	return {"composite": True, "reason": reason}


# ===========================================================================
# CRITERION 1 -- Leadership and Strategic Planning        2 authored / 6
# ===========================================================================
CRITERION_1 = {
	"criterion_1-11-status": q("Oversight Framework", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Oversight controls by status"),
	"criterion_1-12-status": q("Quality Goal", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Strategic quality goals by status"),
	"criterion_1-11-coverage": composite(COMPOSITE_COVERAGE),
	"criterion_1-12-coverage": composite(COMPOSITE_COVERAGE),
	"criterion_1-overview-sources": composite(COMPOSITE_AVAILABILITY),
	"criterion_1-overview-targets": composite(COMPOSITE_TARGETS),
}

# ===========================================================================
# CRITERION 2 -- Corporate Administration                 4 authored / 10
# ===========================================================================
CRITERION_2 = {
	"criterion_2-21-status": q("Employee", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Employees by status"),
	"criterion_2-22-status": q("Stakeholder Engagement Strategy", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Stakeholder engagement by status"),
	"criterion_2-23-status": q("Material Vetting Form", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Information/knowledge records by status"),
	"criterion_2-24-status": q("Quality Action", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Feedback-driven Quality Actions by status"),
	"criterion_2-21-coverage": composite(COMPOSITE_COVERAGE),
	"criterion_2-22-coverage": composite(COMPOSITE_COVERAGE),
	"criterion_2-23-coverage": composite(COMPOSITE_COVERAGE),
	"criterion_2-24-coverage": composite(COMPOSITE_COVERAGE),
	"criterion_2-overview-sources": composite(COMPOSITE_AVAILABILITY),
	"criterion_2-overview-targets": composite(COMPOSITE_TARGETS),
}

# ===========================================================================
# CRITERION 3 -- External Recruitment Agents              7 authored / 19
# ===========================================================================
CRITERION_3 = {
	"c311-listing": q("Agent", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Agents by listing status"),
	"c311-identification": q("Agent", ["agent_type", "type", "category", "agent_category"], "Agents by identification pathway"),
	"c311-score": q("Supplier Rating", ["rating", "overall_rating", "score", "total_score"], "Selection score distribution", order="label asc"),
	"c321-evaluation": q("Agent Annual Performance Review", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Annual performance reviews by status"),
	"c321-complaints": q("Quality Action", ["finding_type", "custom_finding_type", "type", "category"], "Agent complaints and breaches by finding type"),
	"c3-overview-policy": q("Non Disclosure Agreement", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "NDA coverage by status"),
	"c3-overview-renewal": q("Agent Contract", ["expiry_date", "end_date", "contract_end_date", "valid_upto"], "Contract renewals by expiry", order="label asc"),
	"c3-overview-exceptions": composite(COMPOSITE_EXCEPTIONS),
	"c3-overview-health": composite(COMPOSITE_READINESS),
	"c3-overview-lifecycle": composite(COMPOSITE_LIFECYCLE),
	"c311-approval": composite(COMPOSITE_LIFECYCLE),
	"c311-contract": composite(COMPOSITE_READINESS),
	"c311-screening": composite(COMPOSITE_LIFECYCLE),
	"c311-weighting": composite(COMPOSITE_READINESS),
	"c321-offboarding": composite(COMPOSITE_LIFECYCLE),
	"c321-onboarding": composite(COMPOSITE_LIFECYCLE),
	"c321-renewal": composite(COMPOSITE_LIFECYCLE),
	"c321-service": composite(COMPOSITE_READINESS),
	"c321-training": composite(COMPOSITE_READINESS),
}

# ===========================================================================
# CRITERION 4 -- handled by admission_intelligence_embed (6 REAL charts).
# Criterion 4's other ~40 metrics were never ported (criterion_4.py's own
# docstring), so it contributes no section charts here.
# ===========================================================================
CRITERION_4 = {}

# ===========================================================================
# CRITERION 5 -- Academic Systems and Processes           7 authored / 32
# ===========================================================================
CRITERION_5 = {
	"c5-511-status": q("Course Proposal", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Course design proposals by status"),
	"c5-512-status": q("Course Review", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Course reviews by status"),
	"c5-521-status": q("Course Schedule", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Course planning schedules by status"),
	"c5-522-status": q("Student Group", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Course delivery groups by status"),
	"c5-531-status": q("Partnerships Agreement Management", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Partnership agreements by status"),
	"c5-54-status": q("Student Log", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Student feedback logs by status"),
	"c5-55-status": q("Assessment Plan", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Assessment plans by status"),
	"c5-511-coverage": composite(COMPOSITE_COVERAGE),
	"c5-512-coverage": composite(COMPOSITE_COVERAGE),
	"c5-521-coverage": composite(COMPOSITE_COVERAGE),
	"c5-522-coverage": composite(COMPOSITE_COVERAGE),
	"c5-531-coverage": composite(COMPOSITE_COVERAGE),
	"c5-54-coverage": composite(COMPOSITE_COVERAGE),
	"c5-55-coverage": composite(COMPOSITE_COVERAGE),
	"c5-overview-availability": composite(COMPOSITE_AVAILABILITY),
	"c5-overview-readiness": composite(COMPOSITE_READINESS),
	"c5-overview-health": composite(COMPOSITE_READINESS),
	"c5-overview-exceptions": composite(COMPOSITE_EXCEPTIONS),
	"c5-511-gaps": composite(COMPOSITE_EXCEPTIONS),
	"c5-511-readiness": composite(COMPOSITE_READINESS),
	"c5-512-cycle": composite(COMPOSITE_LIFECYCLE),
	"c5-512-gaps": composite(COMPOSITE_EXCEPTIONS),
	"c5-521-flow": composite(COMPOSITE_LIFECYCLE),
	"c5-521-gaps": composite(COMPOSITE_EXCEPTIONS),
	"c5-522-gaps": composite(COMPOSITE_EXCEPTIONS),
	"c5-522-readiness": composite(COMPOSITE_READINESS),
	"c5-531-readiness": composite(COMPOSITE_READINESS),
	"c5-531-risk": composite(COMPOSITE_EXCEPTIONS),
	"c5-54-gaps": composite(COMPOSITE_EXCEPTIONS),
	"c5-54-readiness": composite(COMPOSITE_READINESS),
	"c5-55-gaps": composite(COMPOSITE_EXCEPTIONS),
	"c5-55-readiness": composite(COMPOSITE_READINESS),
}

# ===========================================================================
# CRITERION 6 -- Quality Assurance and Improvement       9 authored / 36
# The largest set. Chart ids are opaque (c611-*, c653-*), so each was matched
# to its DocType by reading its TITLE against criterion_6.SOURCE_CANDIDATES.
# ===========================================================================
CRITERION_6 = {
	"c6-overview-actions": q("Quality Action", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Quality Actions by status"),
	"c6-overview-policy": q("Oversight Framework", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Policy evidence by status"),
	"c611-findings": q("Non Conformance", ["severity", "priority", "status", "nc_type"], "Audit findings by severity"),
	"c611-programme": q("Quality Inspection", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Annual audit programme by status"),
	"c621-outputs": q("Management Review", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Management review outputs by status"),
	"c631-types": q("Operational Outcomes Cost Time Saving", ["type", "category", "outcome_type", "status"], "Innovation type mix"),
	"c641-outcomes": q("Supplier Rating", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Provider evaluation outcomes by status"),
	"c641-tier": q("Supplier", ["supplier_group", "supplier_type", "tier"], "Provider tier profile"),
	"c653-levels": q("Risk Register and Mitigation Plans", ["risk_level", "risk_rating", "severity", "level"], "Risk level distribution"),
	# --- composite ---------------------------------------------------------
	"c6-overview-calendar": composite(COMPOSITE_LIFECYCLE),
	"c6-overview-cycle": composite(COMPOSITE_LIFECYCLE),
	"c6-overview-health": composite(COMPOSITE_READINESS),
	"c6-overview-readiness": composite(COMPOSITE_AVAILABILITY),
	"c611-auditors": composite(COMPOSITE_READINESS),
	"c611-cap": composite(COMPOSITE_EXCEPTIONS),
	"c611-lifecycle": composite(COMPOSITE_LIFECYCLE),
	"c611-scope": composite(COMPOSITE_READINESS),
	"c621-ageing": composite(COMPOSITE_EXCEPTIONS),
	"c621-effectiveness": composite(COMPOSITE_EXCEPTIONS),
	"c621-inputs": composite(COMPOSITE_READINESS),
	"c621-preparation": composite(COMPOSITE_LIFECYCLE),
	"c621-thesis": composite(COMPOSITE_READINESS),
	"c631-impact": composite(COMPOSITE_READINESS),
	"c631-investment": composite(COMPOSITE_READINESS),
	"c631-lifecycle": composite(COMPOSITE_LIFECYCLE),
	"c631-qipi": composite(COMPOSITE_EXCEPTIONS),
	"c631-status": composite(COMPOSITE_COVERAGE),
	"c641-delivery": composite(COMPOSITE_LIFECYCLE),
	"c641-package": composite(COMPOSITE_READINESS),
	"c641-rating": composite(COMPOSITE_READINESS),
	"c641-screening": composite(COMPOSITE_LIFECYCLE),
	"c653-bcdr": composite(COMPOSITE_READINESS),
	"c653-matrix": composite(COMPOSITE_READINESS),
	"c653-reporting": composite(COMPOSITE_LIFECYCLE),
	"c653-residual": composite(COMPOSITE_EXCEPTIONS),
	"c653-treatment": composite(COMPOSITE_LIFECYCLE),
}

# CRITERION 7 -- Performance Outcomes                     2 authored / 4
# ===========================================================================
CRITERION_7 = {
	"criterion_7-71-status": q("Quality Performance Outcomes", ["status", "workflow_state", "docstatus", "review_status", "boarding_status", "agreement_status"], "Performance outcomes by status"),
	"criterion_7-71-coverage": composite(COMPOSITE_COVERAGE),
	"criterion_7-overview-sources": composite(COMPOSITE_AVAILABILITY),
	"criterion_7-overview-targets": composite(COMPOSITE_TARGETS),
}


def _merge():
	merged = {}
	for group in (CRITERION_1, CRITERION_2, CRITERION_3, CRITERION_4, CRITERION_5, CRITERION_6, CRITERION_7):
		merged.update(group)
	return merged


DEFINITIONS = _merge()


def spec_for(chart_id, chart_title="", chart_type=""):
	"""The authored spec for a chart, or None.

	Every chart in the platform is enumerated by id above -- no title matching
	and no guessing. A chart with no entry has no spec and stays placeholder;
	it is never given a spec that might be wrong.
	"""
	if chart_id in DEFINITIONS:
		return DEFINITIONS[chart_id]
	return None


def summary():
	"""Authored-vs-composite counts, for the progress report and the Settings
	page. Composite charts are counted separately from "not reached yet"
	because they are a different problem: one needs authoring time, the other
	needs a decision."""
	authored = composites = 0
	for spec in DEFINITIONS.values():
		if spec.get("composite"):
			composites += 1
		else:
			authored += 1
	return {
		"authored": authored,
		"composite": composites,
		"composite_reasons": sorted({s["reason"].split(":")[0] for s in DEFINITIONS.values() if s.get("composite")}),
	}
