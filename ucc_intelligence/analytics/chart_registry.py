"""One registry of every chart in the platform, and where its definition
lives (CLAUDE.md Phase 5 -- "a chart can be added without editing unrelated
rendering code").

WHY THIS EXISTS
Chart definitions were spread through sophia_analytics.js's CONFIG blob and
answered by hand-written SVG renderers. This makes Frappe Insights the
definition source for the chart layer: every chart has an entry here naming
the Insights query that should answer it, and a `status` saying whether that
query is real yet.

STATUS VALUES -- and read this before trusting a chart
  "real"         An Insights Query v3 record exists, was authored against
                 live data, and is executed server-side per request with
                 ordinary Frappe permissions applied.
  "placeholder"  NO Insights query has been authored yet. The registry entry
                 reserves the name and records the intent; the card renders
                 from the criterion API's own (real, permission-checked)
                 numbers and is BADGED in the UI as awaiting its Insights
                 definition.

  A "placeholder" entry never fabricates data. It means "the Insights
  definition for this chart is not written yet", not "here is made-up
  output". The distinction matters: the numbers on a placeholder card are
  real, only the Insights migration of that chart is outstanding.

PERMISSION MODEL -- unchanged, deliberately
Real charts execute through the same path admission_intelligence proved
safe on the bench: `Insights Query v3.execute()` server-side, permission
checked, with `Insights Settings.apply_user_permissions` ON. Insights'
public-dashboard / is_public mechanism is NOT used anywhere and must never
be -- the pilot proved it applies no row or column permissions at all
(docs/migration/insights-pilot-findings.md §4b).

ADDING A REAL DEFINITION
  1. Author and verify the query in the Insights UI against live data.
  2. Save it with the title in `insights_query_title`.
  3. Flip `status` to "real".
Nothing else changes -- the runtime resolves by title.
"""

from ucc_intelligence.analytics.admission_intelligence_embed import CHART_TITLES as _ADMISSION_TITLES

# The six admission_intelligence series are the only charts with real,
# bench-verified Insights queries today. They are registered from
# admission_intelligence_embed's own titles rather than copied, so the two
# cannot drift.
REAL_ADMISSION_CHARTS = {
	"criterion_4-admission-%s" % data_key: {
		"criterion": "criterion_4",
		"type": "bar",
		"title": title.replace("Sophia AI - ", "").replace("Sophia Pilot - ", ""),
		"insights_query_title": title,
		"status": "real",
	}
	for data_key, title in _ADMISSION_TITLES.items()
}

# Every other chart in the platform, generated from the shipped CONFIG so
# none is missed. All placeholder until its query is authored.
PLACEHOLDER_CHARTS = {
	'criterion_1-overview-targets': {
		"criterion": 'criterion_1',
		"type": 'bar',
		"title": 'Target Gap Summary',
		"insights_query_title": 'UCC PLACEHOLDER - Target Gap Summary',
		"status": "placeholder",
	},
	'criterion_1-overview-sources': {
		"criterion": 'criterion_1',
		"type": 'donut',
		"title": 'Source Availability',
		"insights_query_title": 'UCC PLACEHOLDER - Source Availability',
		"status": "placeholder",
	},
	'criterion_1-11-coverage': {
		"criterion": 'criterion_1',
		"type": 'bar',
		"title": 'Leadership and Corporate Governance Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Leadership and Corporate Governance Control Coverage',
		"status": "placeholder",
	},
	'criterion_1-11-status': {
		"criterion": 'criterion_1',
		"type": 'donut',
		"title": 'Leadership and Corporate Governance Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Leadership and Corporate Governance Status Distribution',
		"status": "placeholder",
	},
	'criterion_1-12-coverage': {
		"criterion": 'criterion_1',
		"type": 'bar',
		"title": 'Strategic Planning Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Strategic Planning Control Coverage',
		"status": "placeholder",
	},
	'criterion_1-12-status': {
		"criterion": 'criterion_1',
		"type": 'donut',
		"title": 'Strategic Planning Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Strategic Planning Status Distribution',
		"status": "placeholder",
	},
	'criterion_2-overview-targets': {
		"criterion": 'criterion_2',
		"type": 'bar',
		"title": 'Target Gap Summary',
		"insights_query_title": 'UCC PLACEHOLDER - Target Gap Summary',
		"status": "placeholder",
	},
	'criterion_2-overview-sources': {
		"criterion": 'criterion_2',
		"type": 'donut',
		"title": 'Source Availability',
		"insights_query_title": 'UCC PLACEHOLDER - Source Availability',
		"status": "placeholder",
	},
	'criterion_2-21-coverage': {
		"criterion": 'criterion_2',
		"type": 'bar',
		"title": 'Human Resource Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Human Resource Control Coverage',
		"status": "placeholder",
	},
	'criterion_2-21-status': {
		"criterion": 'criterion_2',
		"type": 'donut',
		"title": 'Human Resource Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Human Resource Status Distribution',
		"status": "placeholder",
	},
	'criterion_2-22-coverage': {
		"criterion": 'criterion_2',
		"type": 'bar',
		"title": 'Communication Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Communication Control Coverage',
		"status": "placeholder",
	},
	'criterion_2-22-status': {
		"criterion": 'criterion_2',
		"type": 'donut',
		"title": 'Communication Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Communication Status Distribution',
		"status": "placeholder",
	},
	'criterion_2-23-coverage': {
		"criterion": 'criterion_2',
		"type": 'bar',
		"title": 'Data, Information and Knowledge Management Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Data, Information and Knowledge Management Control Coverage',
		"status": "placeholder",
	},
	'criterion_2-23-status': {
		"criterion": 'criterion_2',
		"type": 'donut',
		"title": 'Data, Information and Knowledge Management Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Data, Information and Knowledge Management Status Distribution',
		"status": "placeholder",
	},
	'criterion_2-24-coverage': {
		"criterion": 'criterion_2',
		"type": 'bar',
		"title": 'Feedback Management Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Feedback Management Control Coverage',
		"status": "placeholder",
	},
	'criterion_2-24-status': {
		"criterion": 'criterion_2',
		"type": 'donut',
		"title": 'Feedback Management Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Feedback Management Status Distribution',
		"status": "placeholder",
	},
	'c3-overview-lifecycle': {
		"criterion": 'criterion_3',
		"type": 'lifecycle',
		"title": 'Agent Lifecycle Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Agent Lifecycle Coverage',
		"status": "placeholder",
	},
	'c3-overview-policy': {
		"criterion": 'criterion_3',
		"type": 'donut',
		"title": 'Policy Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Policy Control Coverage',
		"status": "placeholder",
	},
	'c3-overview-health': {
		"criterion": 'criterion_3',
		"type": 'radar',
		"title": 'Agent Control Health',
		"insights_query_title": 'UCC PLACEHOLDER - Agent Control Health',
		"status": "placeholder",
	},
	'c3-overview-renewal': {
		"criterion": 'criterion_3',
		"type": 'trend',
		"title": 'Renewal and Evaluation Trend',
		"insights_query_title": 'UCC PLACEHOLDER - Renewal and Evaluation Trend',
		"status": "placeholder",
	},
	'c3-overview-exceptions': {
		"criterion": 'criterion_3',
		"type": 'bar',
		"title": 'Open Exception Profile',
		"insights_query_title": 'UCC PLACEHOLDER - Open Exception Profile',
		"status": "placeholder",
	},
	'c311-identification': {
		"criterion": 'criterion_3',
		"type": 'donut',
		"title": 'Identification Pathways',
		"insights_query_title": 'UCC PLACEHOLDER - Identification Pathways',
		"status": "placeholder",
	},
	'c311-screening': {
		"criterion": 'criterion_3',
		"type": 'funnel',
		"title": 'Selection and Screening Funnel',
		"insights_query_title": 'UCC PLACEHOLDER - Selection and Screening Funnel',
		"status": "placeholder",
	},
	'c311-weighting': {
		"criterion": 'criterion_3',
		"type": 'radar',
		"title": 'Selection Criteria Weighting',
		"insights_query_title": 'UCC PLACEHOLDER - Selection Criteria Weighting',
		"status": "placeholder",
	},
	'c311-score': {
		"criterion": 'criterion_3',
		"type": 'bar',
		"title": 'Selection Score Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Selection Score Distribution',
		"status": "placeholder",
	},
	'c311-approval': {
		"criterion": 'criterion_3',
		"type": 'lifecycle',
		"title": 'Approval and Background Check',
		"insights_query_title": 'UCC PLACEHOLDER - Approval and Background Check',
		"status": "placeholder",
	},
	'c311-contract': {
		"criterion": 'criterion_3',
		"type": 'matrix',
		"title": 'Contract and NDA Readiness',
		"insights_query_title": 'UCC PLACEHOLDER - Contract and NDA Readiness',
		"status": "placeholder",
	},
	'c311-listing': {
		"criterion": 'criterion_3',
		"type": 'donut',
		"title": 'Agent Listing and Status',
		"insights_query_title": 'UCC PLACEHOLDER - Agent Listing and Status',
		"status": "placeholder",
	},
	'c321-onboarding': {
		"criterion": 'criterion_3',
		"type": 'funnel',
		"title": 'Agent Onboarding Funnel',
		"insights_query_title": 'UCC PLACEHOLDER - Agent Onboarding Funnel',
		"status": "placeholder",
	},
	'c321-training': {
		"criterion": 'criterion_3',
		"type": 'radar',
		"title": 'Training Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Training Coverage',
		"status": "placeholder",
	},
	'c321-service': {
		"criterion": 'criterion_3',
		"type": 'matrix',
		"title": 'Service Delivery Controls',
		"insights_query_title": 'UCC PLACEHOLDER - Service Delivery Controls',
		"status": "placeholder",
	},
	'c321-evaluation': {
		"criterion": 'criterion_3',
		"type": 'bar',
		"title": 'Performance Evaluation Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Performance Evaluation Distribution',
		"status": "placeholder",
	},
	'c321-renewal': {
		"criterion": 'criterion_3',
		"type": 'lifecycle',
		"title": 'Renewal Checkpoint Flow',
		"insights_query_title": 'UCC PLACEHOLDER - Renewal Checkpoint Flow',
		"status": "placeholder",
	},
	'c321-complaints': {
		"criterion": 'criterion_3',
		"type": 'donut',
		"title": 'Complaints and Breaches',
		"insights_query_title": 'UCC PLACEHOLDER - Complaints and Breaches',
		"status": "placeholder",
	},
	'c321-offboarding': {
		"criterion": 'criterion_3',
		"type": 'flow',
		"title": 'Offboarding and Exit Security',
		"insights_query_title": 'UCC PLACEHOLDER - Offboarding and Exit Security',
		"status": "placeholder",
	},
	'c5-overview-readiness': {
		"criterion": 'criterion_5',
		"type": 'bar',
		"title": 'Academic System Readiness',
		"insights_query_title": 'UCC PLACEHOLDER - Academic System Readiness',
		"status": "placeholder",
	},
	'c5-overview-availability': {
		"criterion": 'criterion_5',
		"type": 'donut',
		"title": 'Source Availability',
		"insights_query_title": 'UCC PLACEHOLDER - Source Availability',
		"status": "placeholder",
	},
	'c5-overview-health': {
		"criterion": 'criterion_5',
		"type": 'matrix',
		"title": 'Criterion 5 System Health',
		"insights_query_title": 'UCC PLACEHOLDER - Criterion 5 System Health',
		"status": "placeholder",
	},
	'c5-overview-exceptions': {
		"criterion": 'criterion_5',
		"type": 'funnel',
		"title": 'Criterion 5 Exception Profile',
		"insights_query_title": 'UCC PLACEHOLDER - Criterion 5 Exception Profile',
		"status": "placeholder",
	},
	'c5-511-coverage': {
		"criterion": 'criterion_5',
		"type": 'bar',
		"title": 'Course Design Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Course Design Control Coverage',
		"status": "placeholder",
	},
	'c5-511-status': {
		"criterion": 'criterion_5',
		"type": 'donut',
		"title": 'Course Design Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Course Design Status Distribution',
		"status": "placeholder",
	},
	'c5-511-readiness': {
		"criterion": 'criterion_5',
		"type": 'radar',
		"title": 'Course Design Evidence Readiness',
		"insights_query_title": 'UCC PLACEHOLDER - Course Design Evidence Readiness',
		"status": "placeholder",
	},
	'c5-511-gaps': {
		"criterion": 'criterion_5',
		"type": 'funnel',
		"title": 'Course Design Gap Profile',
		"insights_query_title": 'UCC PLACEHOLDER - Course Design Gap Profile',
		"status": "placeholder",
	},
	'c5-512-coverage': {
		"criterion": 'criterion_5',
		"type": 'bar',
		"title": 'Course Review Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Course Review Control Coverage',
		"status": "placeholder",
	},
	'c5-512-status': {
		"criterion": 'criterion_5',
		"type": 'donut',
		"title": 'Course Review Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Course Review Status Distribution',
		"status": "placeholder",
	},
	'c5-512-cycle': {
		"criterion": 'criterion_5',
		"type": 'lifecycle',
		"title": 'Course Review Lifecycle',
		"insights_query_title": 'UCC PLACEHOLDER - Course Review Lifecycle',
		"status": "placeholder",
	},
	'c5-512-gaps': {
		"criterion": 'criterion_5',
		"type": 'funnel',
		"title": 'Review Exception Profile',
		"insights_query_title": 'UCC PLACEHOLDER - Review Exception Profile',
		"status": "placeholder",
	},
	'c5-521-coverage': {
		"criterion": 'criterion_5',
		"type": 'bar',
		"title": 'Course Planning Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Course Planning Control Coverage',
		"status": "placeholder",
	},
	'c5-521-status': {
		"criterion": 'criterion_5',
		"type": 'donut',
		"title": 'Course Planning Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Course Planning Status Distribution',
		"status": "placeholder",
	},
	'c5-521-flow': {
		"criterion": 'criterion_5',
		"type": 'lifecycle',
		"title": 'Planning Readiness Flow',
		"insights_query_title": 'UCC PLACEHOLDER - Planning Readiness Flow',
		"status": "placeholder",
	},
	'c5-521-gaps': {
		"criterion": 'criterion_5',
		"type": 'funnel',
		"title": 'Planning Exception Profile',
		"insights_query_title": 'UCC PLACEHOLDER - Planning Exception Profile',
		"status": "placeholder",
	},
	'c5-522-coverage': {
		"criterion": 'criterion_5',
		"type": 'bar',
		"title": 'Course Delivery Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Course Delivery Control Coverage',
		"status": "placeholder",
	},
	'c5-522-status': {
		"criterion": 'criterion_5',
		"type": 'donut',
		"title": 'Course Delivery Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Course Delivery Status Distribution',
		"status": "placeholder",
	},
	'c5-522-readiness': {
		"criterion": 'criterion_5',
		"type": 'radar',
		"title": 'Delivery Evidence Readiness',
		"insights_query_title": 'UCC PLACEHOLDER - Delivery Evidence Readiness',
		"status": "placeholder",
	},
	'c5-522-gaps': {
		"criterion": 'criterion_5',
		"type": 'funnel',
		"title": 'Delivery Exception Profile',
		"insights_query_title": 'UCC PLACEHOLDER - Delivery Exception Profile',
		"status": "placeholder",
	},
	'c5-531-coverage': {
		"criterion": 'criterion_5',
		"type": 'bar',
		"title": 'Partnership Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Partnership Control Coverage',
		"status": "placeholder",
	},
	'c5-531-status': {
		"criterion": 'criterion_5',
		"type": 'donut',
		"title": 'Partnership Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Partnership Status Distribution',
		"status": "placeholder",
	},
	'c5-531-risk': {
		"criterion": 'criterion_5',
		"type": 'funnel',
		"title": 'Partnership Risk Profile',
		"insights_query_title": 'UCC PLACEHOLDER - Partnership Risk Profile',
		"status": "placeholder",
	},
	'c5-531-readiness': {
		"criterion": 'criterion_5',
		"type": 'matrix',
		"title": 'Partnership Evidence Readiness',
		"insights_query_title": 'UCC PLACEHOLDER - Partnership Evidence Readiness',
		"status": "placeholder",
	},
	'c5-54-coverage': {
		"criterion": 'criterion_5',
		"type": 'bar',
		"title": 'Student Feedback Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Student Feedback Control Coverage',
		"status": "placeholder",
	},
	'c5-54-status': {
		"criterion": 'criterion_5',
		"type": 'donut',
		"title": 'Student Feedback Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Student Feedback Status Distribution',
		"status": "placeholder",
	},
	'c5-54-readiness': {
		"criterion": 'criterion_5',
		"type": 'radar',
		"title": 'Feedback Evidence Readiness',
		"insights_query_title": 'UCC PLACEHOLDER - Feedback Evidence Readiness',
		"status": "placeholder",
	},
	'c5-54-gaps': {
		"criterion": 'criterion_5',
		"type": 'funnel',
		"title": 'Feedback Exception Profile',
		"insights_query_title": 'UCC PLACEHOLDER - Feedback Exception Profile',
		"status": "placeholder",
	},
	'c5-55-coverage': {
		"criterion": 'criterion_5',
		"type": 'bar',
		"title": 'Assessment Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Assessment Control Coverage',
		"status": "placeholder",
	},
	'c5-55-status': {
		"criterion": 'criterion_5',
		"type": 'donut',
		"title": 'Assessment Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Assessment Status Distribution',
		"status": "placeholder",
	},
	'c5-55-readiness': {
		"criterion": 'criterion_5',
		"type": 'radar',
		"title": 'Assessment Evidence Readiness',
		"insights_query_title": 'UCC PLACEHOLDER - Assessment Evidence Readiness',
		"status": "placeholder",
	},
	'c5-55-gaps': {
		"criterion": 'criterion_5',
		"type": 'funnel',
		"title": 'Assessment Exception Profile',
		"insights_query_title": 'UCC PLACEHOLDER - Assessment Exception Profile',
		"status": "placeholder",
	},
	'c6-overview-cycle': {
		"criterion": 'criterion_6',
		"type": 'lifecycle',
		"title": 'Quality Management Cycle',
		"insights_query_title": 'UCC PLACEHOLDER - Quality Management Cycle',
		"status": "placeholder",
	},
	'c6-overview-policy': {
		"criterion": 'criterion_6',
		"type": 'donut',
		"title": 'Policy Evidence Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Policy Evidence Coverage',
		"status": "placeholder",
	},
	'c6-overview-health': {
		"criterion": 'criterion_6',
		"type": 'radar',
		"title": 'Quality System Health',
		"insights_query_title": 'UCC PLACEHOLDER - Quality System Health',
		"status": "placeholder",
	},
	'c6-overview-calendar': {
		"criterion": 'criterion_6',
		"type": 'trend',
		"title": 'Quality Calendar Completion',
		"insights_query_title": 'UCC PLACEHOLDER - Quality Calendar Completion',
		"status": "placeholder",
	},
	'c6-overview-actions': {
		"criterion": 'criterion_6',
		"type": 'bar',
		"title": 'Action Status',
		"insights_query_title": 'UCC PLACEHOLDER - Action Status',
		"status": "placeholder",
	},
	'c6-overview-readiness': {
		"criterion": 'criterion_6',
		"type": 'matrix',
		"title": 'Source Readiness',
		"insights_query_title": 'UCC PLACEHOLDER - Source Readiness',
		"status": "placeholder",
	},
	'c611-programme': {
		"criterion": 'criterion_6',
		"type": 'donut',
		"title": 'Annual Audit Programme',
		"insights_query_title": 'UCC PLACEHOLDER - Annual Audit Programme',
		"status": "placeholder",
	},
	'c611-scope': {
		"criterion": 'criterion_6',
		"type": 'radar',
		"title": 'Audit Scope Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Audit Scope Coverage',
		"status": "placeholder",
	},
	'c611-lifecycle': {
		"criterion": 'criterion_6',
		"type": 'funnel',
		"title": 'Audit Lifecycle',
		"insights_query_title": 'UCC PLACEHOLDER - Audit Lifecycle',
		"status": "placeholder",
	},
	'c611-auditors': {
		"criterion": 'criterion_6',
		"type": 'matrix',
		"title": 'Auditor Qualification and Independence',
		"insights_query_title": 'UCC PLACEHOLDER - Auditor Qualification and Independence',
		"status": "placeholder",
	},
	'c611-findings': {
		"criterion": 'criterion_6',
		"type": 'bar',
		"title": 'Audit Findings by Severity',
		"insights_query_title": 'UCC PLACEHOLDER - Audit Findings by Severity',
		"status": "placeholder",
	},
	'c611-cap': {
		"criterion": 'criterion_6',
		"type": 'trend',
		"title": 'Corrective Action Closure',
		"insights_query_title": 'UCC PLACEHOLDER - Corrective Action Closure',
		"status": "placeholder",
	},
	'c621-thesis': {
		"criterion": 'criterion_6',
		"type": 'radar',
		"title": 'THESIS Review Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - THESIS Review Coverage',
		"status": "placeholder",
	},
	'c621-preparation': {
		"criterion": 'criterion_6',
		"type": 'funnel',
		"title": 'Management Review Preparation',
		"insights_query_title": 'UCC PLACEHOLDER - Management Review Preparation',
		"status": "placeholder",
	},
	'c621-inputs': {
		"criterion": 'criterion_6',
		"type": 'matrix',
		"title": 'Review Input Completeness',
		"insights_query_title": 'UCC PLACEHOLDER - Review Input Completeness',
		"status": "placeholder",
	},
	'c621-outputs': {
		"criterion": 'criterion_6',
		"type": 'donut',
		"title": 'Review Outputs',
		"insights_query_title": 'UCC PLACEHOLDER - Review Outputs',
		"status": "placeholder",
	},
	'c621-ageing': {
		"criterion": 'criterion_6',
		"type": 'bar',
		"title": 'Action Ageing',
		"insights_query_title": 'UCC PLACEHOLDER - Action Ageing',
		"status": "placeholder",
	},
	'c621-effectiveness': {
		"criterion": 'criterion_6',
		"type": 'trend',
		"title": 'Action Effectiveness',
		"insights_query_title": 'UCC PLACEHOLDER - Action Effectiveness',
		"status": "placeholder",
	},
	'c631-types': {
		"criterion": 'criterion_6',
		"type": 'donut',
		"title": 'Innovation Type Mix',
		"insights_query_title": 'UCC PLACEHOLDER - Innovation Type Mix',
		"status": "placeholder",
	},
	'c631-lifecycle': {
		"criterion": 'criterion_6',
		"type": 'funnel',
		"title": 'Improvement Initiative Lifecycle',
		"insights_query_title": 'UCC PLACEHOLDER - Improvement Initiative Lifecycle',
		"status": "placeholder",
	},
	'c631-investment': {
		"criterion": 'criterion_6',
		"type": 'radar',
		"title": 'Innovation Performance Categories',
		"insights_query_title": 'UCC PLACEHOLDER - Innovation Performance Categories',
		"status": "placeholder",
	},
	'c631-qipi': {
		"criterion": 'criterion_6',
		"type": 'trend',
		"title": 'QIPI Outcome Trend',
		"insights_query_title": 'UCC PLACEHOLDER - QIPI Outcome Trend',
		"status": "placeholder",
	},
	'c631-impact': {
		"criterion": 'criterion_6',
		"type": 'gauge',
		"title": 'Before and After Impact',
		"insights_query_title": 'UCC PLACEHOLDER - Before and After Impact',
		"status": "placeholder",
	},
	'c631-status': {
		"criterion": 'criterion_6',
		"type": 'matrix',
		"title": 'Improvement Action Status',
		"insights_query_title": 'UCC PLACEHOLDER - Improvement Action Status',
		"status": "placeholder",
	},
	'c641-tier': {
		"criterion": 'criterion_6',
		"type": 'donut',
		"title": 'Provider Tier Profile',
		"insights_query_title": 'UCC PLACEHOLDER - Provider Tier Profile',
		"status": "placeholder",
	},
	'c641-screening': {
		"criterion": 'criterion_6',
		"type": 'funnel',
		"title": 'Provider Accreditation Funnel',
		"insights_query_title": 'UCC PLACEHOLDER - Provider Accreditation Funnel',
		"status": "placeholder",
	},
	'c641-package': {
		"criterion": 'criterion_6',
		"type": 'matrix',
		"title": 'Compliance Package',
		"insights_query_title": 'UCC PLACEHOLDER - Compliance Package',
		"status": "placeholder",
	},
	'c641-delivery': {
		"criterion": 'criterion_6',
		"type": 'lifecycle',
		"title": 'Service Delivery and Purchase Controls',
		"insights_query_title": 'UCC PLACEHOLDER - Service Delivery and Purchase Controls',
		"status": "placeholder",
	},
	'c641-rating': {
		"criterion": 'criterion_6',
		"type": 'radar',
		"title": 'Provider Rating Weighting',
		"insights_query_title": 'UCC PLACEHOLDER - Provider Rating Weighting',
		"status": "placeholder",
	},
	'c641-outcomes': {
		"criterion": 'criterion_6',
		"type": 'donut',
		"title": 'Provider Evaluation Outcomes',
		"insights_query_title": 'UCC PLACEHOLDER - Provider Evaluation Outcomes',
		"status": "placeholder",
	},
	'c653-reporting': {
		"criterion": 'criterion_6',
		"type": 'funnel',
		"title": 'Hazard Reporting Funnel',
		"insights_query_title": 'UCC PLACEHOLDER - Hazard Reporting Funnel',
		"status": "placeholder",
	},
	'c653-levels': {
		"criterion": 'criterion_6',
		"type": 'donut',
		"title": 'Risk Level Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Risk Level Distribution',
		"status": "placeholder",
	},
	'c653-matrix': {
		"criterion": 'criterion_6',
		"type": 'risk-matrix',
		"title": '5×5 Risk Matrix',
		"insights_query_title": 'UCC PLACEHOLDER - 5×5 Risk Matrix',
		"status": "placeholder",
	},
	'c653-treatment': {
		"criterion": 'criterion_6',
		"type": 'lifecycle',
		"title": 'Risk Treatment Lifecycle',
		"insights_query_title": 'UCC PLACEHOLDER - Risk Treatment Lifecycle',
		"status": "placeholder",
	},
	'c653-residual': {
		"criterion": 'criterion_6',
		"type": 'trend',
		"title": 'Residual Risk Trend',
		"insights_query_title": 'UCC PLACEHOLDER - Residual Risk Trend',
		"status": "placeholder",
	},
	'c653-bcdr': {
		"criterion": 'criterion_6',
		"type": 'radar',
		"title": 'Business Continuity Readiness',
		"insights_query_title": 'UCC PLACEHOLDER - Business Continuity Readiness',
		"status": "placeholder",
	},
	'criterion_7-overview-targets': {
		"criterion": 'criterion_7',
		"type": 'bar',
		"title": 'Target Gap Summary',
		"insights_query_title": 'UCC PLACEHOLDER - Target Gap Summary',
		"status": "placeholder",
	},
	'criterion_7-overview-sources': {
		"criterion": 'criterion_7',
		"type": 'donut',
		"title": 'Source Availability',
		"insights_query_title": 'UCC PLACEHOLDER - Source Availability',
		"status": "placeholder",
	},
	'criterion_7-71-coverage': {
		"criterion": 'criterion_7',
		"type": 'bar',
		"title": 'Measurement of Outcomes Control Coverage',
		"insights_query_title": 'UCC PLACEHOLDER - Measurement of Outcomes Control Coverage',
		"status": "placeholder",
	},
	'criterion_7-71-status': {
		"criterion": 'criterion_7',
		"type": 'donut',
		"title": 'Measurement of Outcomes Status Distribution',
		"insights_query_title": 'UCC PLACEHOLDER - Measurement of Outcomes Status Distribution',
		"status": "placeholder",
	},}

CHARTS = dict(PLACEHOLDER_CHARTS)
CHARTS.update(REAL_ADMISSION_CHARTS)


def get(chart_id):
	return CHARTS.get(chart_id)


def for_criterion(criterion_key):
	return {cid: spec for cid, spec in CHARTS.items() if spec["criterion"] == criterion_key}


def counts():
	"""How much of the chart layer is genuinely on Insights. Surfaced on the
	Settings status page so the migration's real progress is visible rather
	than asserted."""
	real = sum(1 for spec in CHARTS.values() if spec["status"] == "real")
	return {
		"total": len(CHARTS),
		"real": real,
		"placeholder": len(CHARTS) - real,
	}
