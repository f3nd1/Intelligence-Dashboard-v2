"""Shared analytics response/error contract.

Deduped from `standardise_response_contract` and `is_permission_error`,
verified byte-identical (the former) or near-identical (the latter) across
all seven `server-scripts/UCC Analytics - Criterion *.py` files this
session (hash-compared, not assumed from the earlier investigation
reports). Not wired to any criterion script yet -- Phase 4 migrates those
one at a time and calls into this module as it does. Written now so Phase 4
has a stable, tested contract to build against instead of re-deriving it
per criterion.

`is_permission_error` includes the substring check for "403" that, in the
legacy scripts, only Criterion 7 had. Applied universally here per the
Phase 2 plan's recommendation: a broader match only produces more correct
`permission_denied` classifications, and no other criterion's error text
was found to trigger a false positive from it.
"""

CONTRACT_VERSION = "2.1.0"

ARRAY_KEYS = [
	"resolved_filters", "unresolved_filters", "sources", "source_mapping",
	"metrics", "supporting_metrics", "questions", "requirements",
	"exceptions", "evidence_gaps", "data_quality", "warnings",
]

MIRROR_KEYS = [
	"sources", "source_mapping", "metrics", "supporting_metrics", "questions",
	"requirements", "exceptions", "evidence_gaps", "data_quality", "readiness",
]


def _clean_text(value):
	if value is None:
		return ""
	return str(value).strip()


def is_permission_error(error):
	text = _clean_text(error).lower()
	return (
		"permission" in text
		or "not permitted" in text
		or "not allowed" in text
		or "403" in text
	)


def standardise_response_contract(result, criterion_name, api_method, action_name, subcriterion_name, row_limit_value):
	"""Normalise a criterion API response onto the shared frontend contract."""
	if not isinstance(result, dict):
		result = {}

	result["ok"] = bool(result.get("ok", True))

	meta = result.get("meta")
	if not isinstance(meta, dict):
		meta = {}
	meta["api_method"] = api_method
	meta["criterion"] = criterion_name
	meta["contract_version"] = CONTRACT_VERSION
	meta["action"] = action_name
	meta["subcriterion"] = subcriterion_name
	meta["row_limit"] = row_limit_value
	result["meta"] = meta

	filter_values = result.get("filters")
	if not isinstance(filter_values, dict):
		filter_values = {}
	result["filters"] = filter_values

	for key in ARRAY_KEYS:
		value = result.get(key)
		if not isinstance(value, list):
			result[key] = []

	if not result.get("requirements"):
		requirement_evidence = result.get("requirement_evidence")
		if isinstance(requirement_evidence, list):
			result["requirements"] = requirement_evidence

	if not result.get("supporting_metrics"):
		supporting = []
		for metric in result.get("metrics") or []:
			if isinstance(metric, dict) and metric.get("category") == "supporting":
				supporting.append(metric)
		result["supporting_metrics"] = supporting

	if not result.get("source_mapping"):
		mappings = []
		for source in result.get("sources") or []:
			if not isinstance(source, dict):
				continue
			display_name = (
				source.get("display_doctype") or source.get("display_name")
				or source.get("doctype") or source.get("key") or ""
			)
			mappings.append({
				"key": source.get("key"),
				"doctype": source.get("doctype"),
				"display_doctype": display_name,
				"status": source.get("status") or "unavailable",
				"count": source.get("count"),
				"count_is_sample": bool(source.get("count_is_sample")),
				"truncated": bool(source.get("truncated")),
				"candidates": source.get("candidates") or [],
				"resolution_attempts": source.get("resolution_attempts") or [],
			})
		result["source_mapping"] = mappings

	metric_lookup = {}
	for metric in result.get("metrics") or []:
		if isinstance(metric, dict) and metric.get("id"):
			metric_lookup[metric.get("id")] = metric

	normalised_questions = []
	for question in result.get("questions") or []:
		if not isinstance(question, dict):
			continue
		primary_metric = {}
		primary_metric_id = question.get("metric_id")
		if not primary_metric_id:
			metric_ids = question.get("metric_ids") or []
			if metric_ids:
				primary_metric_id = metric_ids[0]
		if primary_metric_id:
			primary_metric = metric_lookup.get(primary_metric_id) or {}
		if question.get("metric_id") is None:
			question["metric_id"] = primary_metric_id
		if question.get("source") is None:
			question["source"] = primary_metric.get("source")
		if question.get("doctype") is None:
			question["doctype"] = primary_metric.get("doctype")
		if not isinstance(question.get("resolved_fields"), list):
			question["resolved_fields"] = primary_metric.get("resolved_fields") or []
		if question.get("record_count") is None:
			question["record_count"] = primary_metric.get("record_count")
		if question.get("unit") is None:
			question["unit"] = primary_metric.get("unit")
		if not question.get("status"):
			question["status"] = primary_metric.get("status") or "unsupported"
		if not question.get("confidence"):
			if question.get("status") == "available":
				question["confidence"] = "Live"
			elif question.get("status") in ["partial", "partial_truncated"]:
				question["confidence"] = "Partial"
			else:
				question["confidence"] = "Unavailable"
		if not question.get("applicable_population"):
			question["applicable_population"] = primary_metric.get("applicable_population") or "Records within the applied filters."
		if not question.get("reporting_period"):
			question["reporting_period"] = primary_metric.get("reporting_period") or "Applied dashboard period, subject to source-field support."
		if not question.get("calculation_note"):
			question["calculation_note"] = primary_metric.get("calculation_note") or primary_metric.get("label") or "Configured management-answer rule."
		normalised_questions.append(question)
	result["questions"] = normalised_questions

	sources = result.get("sources") or []
	metrics = result.get("metrics") or []
	questions = result.get("questions") or []

	source_available = 0
	source_issues = 0
	source_truncated = 0
	for source in sources:
		if not isinstance(source, dict):
			continue
		if source.get("status") == "available":
			source_available = source_available + 1
		else:
			source_issues = source_issues + 1
		if source.get("truncated"):
			source_truncated = source_truncated + 1

	metric_available = 0
	metric_partial = 0
	metric_issues = 0
	for metric in metrics:
		if not isinstance(metric, dict):
			continue
		status = metric.get("status")
		if status == "available":
			metric_available = metric_available + 1
		elif status in ["partial", "partial_truncated"]:
			metric_partial = metric_partial + 1
		else:
			metric_issues = metric_issues + 1

	question_available = 0
	question_partial = 0
	question_issues = 0
	for question in questions:
		if not isinstance(question, dict):
			continue
		status = question.get("status")
		if status == "available":
			question_available = question_available + 1
		elif status in ["partial", "partial_truncated"]:
			question_partial = question_partial + 1
		else:
			question_issues = question_issues + 1

	result["source_summary"] = {
		"total": len(sources), "available": source_available,
		"issues": source_issues, "truncated": source_truncated,
	}
	result["metric_summary"] = {
		"total": len(metrics), "available": metric_available,
		"partial": metric_partial, "issues": metric_issues,
	}
	result["question_summary"] = {
		"total": len(questions), "available": question_available,
		"partial": question_partial, "issues": question_issues,
	}

	readiness = result.get("readiness")
	if not isinstance(readiness, dict):
		readiness = {}
	readiness["status"] = "active_with_limitations" if (
		source_issues or source_truncated or metric_partial or metric_issues
		or question_partial or question_issues or result.get("data_quality")
		or result.get("evidence_gaps")
	) else "active"
	readiness["source_total"] = len(sources)
	readiness["source_available"] = source_available
	readiness["source_truncated"] = source_truncated
	readiness["metric_total"] = len(metrics)
	readiness["metric_available"] = metric_available
	readiness["metric_partial"] = metric_partial
	readiness["question_total"] = len(questions)
	readiness["question_available"] = question_available
	readiness["question_partial"] = question_partial
	readiness["items_need_review"] = len(result.get("data_quality") or []) + len(result.get("evidence_gaps") or [])
	result["readiness"] = readiness

	data = result.get("data")
	if not isinstance(data, dict):
		data = {}
	for key in MIRROR_KEYS:
		data[key] = result.get(key)
	result["data"] = data

	return result
