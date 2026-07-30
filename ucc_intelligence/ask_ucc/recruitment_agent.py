"""Recruitment Agent tool functions for Ask UCC -- the fixed, named
allowlist this module may call (CLAUDE.md Phase 8: "AI must not query
arbitrary DocTypes... must not accept a user-provided method path").

Ported from server-scripts/UCC Ask - Recruitment Agent.py after a full
read. That script has zero AI code of its own (`response_base` hardcodes
`ai_used: False`), so there is no AI behaviour to preserve -- only the
deterministic fact-gathering and the two rule ladders below, both carried
over exactly.

Its ~13 keyword-triggered intents collapse into 3 tools, the same way
Quality Action's ~10 collapsed into 2: `handle_profile`/`handle_contract`/
`handle_latest_contract` all read the same contract fields, and
`handle_compliance`/`handle_renewal` consume identical inputs (latest
contract dates/status + latest rating) and are both pure rule ladders.

**Deliberately NOT ported** (documented rather than silently dropped):

- `find_contract()`'s fuzzy fallback -- loads 1000 contracts and
  substring-matches the raw question. Cross-record search, same deferral
  as Quality Action's "all open quality actions".
- `handle_active_count()` -- lists 5000 contracts then `get_doc`s each.
  Cross-record search and a performance hazard.
- `matching_rows_for_agent`/`scan_rows_for_agent` and everything built on
  them (`handle_students`' fallback, `handle_finance`) -- brute-force
  scans of up to 5000 rows per DocType with a fuzzy ≥2-token-overlap
  match. That is schema-discovery scaffolding the original author left in
  to find the real agent link field, not production logic. The legacy
  script's own warning concedes it: "Commission status remains
  unavailable until the exact commission field, child table or
  transaction DocType is mapped."
- `intent == "expiring"` -- dead in the legacy script (no handler).

Permission model: `frappe.get_doc` below runs with no ignore_permissions,
same as the legacy script and every other module tonight. Unlike the
legacy `safe_get_doc`/`safe_db_list` wrappers -- which swallow
PermissionError, DoesNotExistError and genuine faults into an
indistinguishable empty result -- `load_agent_contract()` classifies them,
so a blocked record renders the real blocked-source notice instead of
looking like an empty one.
"""

import frappe

from ucc_intelligence.analytics.contracts import is_permission_error
from ucc_intelligence.analytics.engine import clean_text, lower_text

MINIMUM_RATING_LIKERT = 3.5

# Every candidate list below is quoted from the legacy script's own
# first_value() calls -- this session has never verified Agent Contract's
# real schema, so probing candidates is preserved, not replaced with a
# hardcoded fieldname.
NAME_CANDIDATES = ["party_name", "agent_name", "company_name", "supplier_name"]
START_DATE_CANDIDATES = ["commencement_date", "start_date", "contract_start_date", "posting_date", "effective_date"]
END_DATE_CANDIDATES = ["end_date", "expiry_date", "contract_end_date", "expiration_date", "valid_till"]
STATUS_CANDIDATES = ["status", "workflow_state", "contract_status"]
IDENTIFIER_CANDIDATES = ["personal_id", "uen", "company_id", "registration_number"]

RATING_VALUE_CANDIDATES = {
	"rating": ["rating", "total_rating", "overall_rating", "rating_score", "total_score"],
	"rating_likert": ["rating_likert", "overall_likert", "likert_rating", "average_likert"],
	"evaluation_stage": ["evaluation_stage", "custom_evaluation_stage", "stage"],
	"status": ["status", "workflow_state", "recommendation"],
}

# Tried in order; the first filter returning rows wins (legacy rating_rows()).
RATING_FILTER_CANDIDATES = [
	"supplier_name", "supplier", "provider_name", "party_name", "agent_name", "agent",
]

RATING_ATTENTION_TERMS = [
	"terminate", "reject", "suspend", "not approved", "corrective", "conditional",
]


def first_value(doc, candidates):
	for fieldname in candidates:
		try:
			value = doc.get(fieldname)
		except Exception:
			value = None
		if value not in [None, ""]:
			return value
	return None


def to_number(value):
	try:
		if value in [None, ""]:
			return None
		return float(value)
	except Exception:
		return None


def load_agent_contract(agent_contract_name):
	try:
		return {"status": "available", "doc": frappe.get_doc("Agent Contract", agent_contract_name)}
	except frappe.DoesNotExistError:
		return {"status": "not_found", "message": "No Agent Contract named %r." % agent_contract_name}
	except Exception as error:
		status = "permission_denied" if is_permission_error(error) else "unavailable"
		return {"status": status, "message": clean_text(error)}


def contract_dates(doc):
	return {
		"start": clean_text(first_value(doc, START_DATE_CANDIDATES)),
		"end": clean_text(first_value(doc, END_DATE_CANDIDATES)),
	}


def contract_status(doc):
	"""Legacy contract_status(), ported exactly: dates decide the status
	before any stored status field is consulted."""
	dates = contract_dates(doc)
	today = clean_text(frappe.utils.today())
	if dates.get("end") and dates.get("end") < today:
		return "Expired"
	if dates.get("start") and dates.get("start") > today:
		return "Not started"
	if dates.get("start") or dates.get("end"):
		return "Active"
	return clean_text(first_value(doc, STATUS_CANDIDATES)) or "Not recorded"


def agent_name_of(doc):
	return clean_text(first_value(doc, NAME_CANDIDATES)) or clean_text(doc.get("name"))


def load_rating_rows(agent_name):
	"""Legacy rating_rows(): try each candidate filter in order, stop at the
	first that returns anything."""
	if not agent_name:
		return []
	for fieldname in RATING_FILTER_CANDIDATES:
		try:
			rows = frappe.get_list(
				"Supplier Rating", filters={fieldname: agent_name},
				fields=["name", "modified"], order_by="modified desc", limit_page_length=100,
			) or []
		except Exception:
			continue
		if rows:
			return rows
	return []


def rating_values(doc):
	values = {}
	for key, candidates in RATING_VALUE_CANDIDATES.items():
		values[key] = clean_text(first_value(doc, candidates))
	values["modified"] = clean_text(doc.get("modified"))
	return values


def get_agent_contract_summary(agent_contract_name):
	"""Tool: the contract's own facts -- who the agent is, the computed
	status, the dates, the identifier. Covers the legacy handle_profile,
	handle_contract and handle_latest_contract intents."""
	loaded = load_agent_contract(agent_contract_name)
	if loaded["status"] != "available":
		return loaded
	doc = loaded["doc"]
	dates = contract_dates(doc)
	return {
		"status": "available",
		"agent_contract": agent_contract_name,
		"agent_name": agent_name_of(doc),
		"identifier": clean_text(first_value(doc, IDENTIFIER_CANDIDATES)) or "Not recorded",
		"contract_status": contract_status(doc),
		"commencement_date": dates["start"] or "Not recorded",
		"expiry_date": dates["end"] or "Not recorded",
	}


def get_agent_ratings(agent_contract_name):
	"""Tool: this agent's Supplier Rating history plus the latest values and
	whether it meets the 3.5 minimum. Covers the legacy handle_rating
	intents (both the plain and threshold modes)."""
	loaded = load_agent_contract(agent_contract_name)
	if loaded["status"] != "available":
		return loaded
	doc = loaded["doc"]
	agent_name = agent_name_of(doc)

	ratings = []
	for row in load_rating_rows(agent_name):
		try:
			rating_doc = frappe.get_doc("Supplier Rating", row.get("name"))
		except Exception:
			continue
		values = rating_values(rating_doc)
		values["name"] = clean_text(row.get("name"))
		ratings.append(values)

	latest = ratings[0] if ratings else None
	likert = to_number(latest.get("rating_likert")) if latest else None
	meets_minimum = None
	if likert is not None:
		meets_minimum = likert >= MINIMUM_RATING_LIKERT

	return {
		"status": "available",
		"agent_contract": agent_contract_name,
		"agent_name": agent_name,
		"ratings": ratings,
		"latest": latest,
		"minimum_rating_likert": MINIMUM_RATING_LIKERT,
		"meets_minimum_rating": meets_minimum,
	}


def assess_agent_contract_renewal(agent_contract_name):
	"""Tool: deterministic compliance issues + renewal recommendation. Both
	legacy ladders (handle_compliance's issue list and handle_renewal's
	ordered recommendation) ported exactly -- the AI explains these, it
	does not compute or override them (CLAUDE.md: "the pass/fail decision
	should remain deterministic where possible")."""
	loaded = load_agent_contract(agent_contract_name)
	if loaded["status"] != "available":
		return loaded
	doc = loaded["doc"]

	dates = contract_dates(doc)
	status = contract_status(doc)
	ratings_result = get_agent_ratings(agent_contract_name)
	ratings = ratings_result.get("ratings") or []
	latest = ratings_result.get("latest")
	likert = to_number(latest.get("rating_likert")) if latest else None

	issues = []
	if status in ["Expired", "Not started"]:
		issues.append("Contract status is " + status + ".")
	if not dates.get("start"):
		issues.append("Contract commencement date is missing.")
	if not dates.get("end"):
		issues.append("Contract expiry date is missing.")
	if ratings:
		if likert is not None and likert < MINIMUM_RATING_LIKERT:
			issues.append("Latest rating_likert is below the 3.5 minimum.")
		rating_status = lower_text(latest.get("status"))
		if any(term in rating_status for term in RATING_ATTENTION_TERMS):
			issues.append("Latest rating status requires attention: " + clean_text(latest.get("status")) + ".")
	else:
		issues.append("No linked Supplier Rating was found.")

	warnings = []
	if status == "Expired":
		recommendation = "Do not renew automatically; complete a formal renewal review."
	elif status == "Not started":
		recommendation = "Renewal is not applicable because the latest contract has not started."
	elif not dates.get("end"):
		recommendation = "Hold the renewal decision until the expiry date is recorded."
		warnings.append("The contract expiry date is missing.")
	elif not latest:
		recommendation = "Complete a current Supplier Rating before deciding on renewal."
		warnings.append("No linked Supplier Rating was found.")
	elif likert is None:
		recommendation = "Review manually because the latest rating_likert is missing."
		warnings.append("Latest rating_likert is not recorded.")
	elif likert < MINIMUM_RATING_LIKERT:
		recommendation = "Do not renew without corrective action and management approval."
		warnings.append("Latest rating_likert is below the 3.5 minimum.")
	else:
		recommendation = (
			"Eligible for continuation, subject to management approval and completion "
			"of the formal renewal process."
		)

	return {
		"status": "available",
		"agent_contract": agent_contract_name,
		"agent_name": agent_name_of(doc),
		"contract_status": status,
		"issues": issues,
		"recommendation": recommendation,
		"warnings": warnings,
		"note": "Rule-based assessment. Formal renewal still requires management approval and the documented review process.",
	}


TOOLS = {
	"get_agent_contract_summary": get_agent_contract_summary,
	"get_agent_ratings": get_agent_ratings,
	"assess_agent_contract_renewal": assess_agent_contract_renewal,
}
