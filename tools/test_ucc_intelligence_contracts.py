#!/usr/bin/env python3
"""Self-check for the deduped analytics response/error contract.

Extracts standardise_response_contract() verbatim from the legacy
server-scripts/UCC Analytics - Criterion 1.py (frappe-independent, pure
Python) and diffs its output against the ported
ucc_intelligence.analytics.contracts version across representative
fixtures, so drift in either copy is caught before Phase 4 wires any
criterion script to the ported one.

    python3 tools/test_ucc_intelligence_contracts.py
"""
import copy
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ucc_intelligence"))

from ucc_intelligence.analytics.contracts import (  # noqa: E402
	is_permission_error as ported_is_permission_error,
	standardise_response_contract as ported_contract,
)


def _load_legacy_contract():
	path = ROOT / "server-scripts" / "UCC Analytics - Criterion 1.py"
	lines = path.read_text(encoding="utf-8").split("\n")
	start = next(i for i, l in enumerate(lines) if l.startswith("def standardise_response_contract("))
	end = start + 1
	while end < len(lines) and (lines[end].strip() == "" or lines[end].startswith((" ", "\t"))):
		end += 1
	namespace = {}
	exec(compile("\n".join(lines[start:end]), "legacy_contract", "exec"), namespace)  # noqa: S102
	return namespace["standardise_response_contract"]


legacy_contract = _load_legacy_contract()

FIXTURES = [
	({}, "Criterion 1", "ucc_analytics_criterion_1", "summary", "1.1.1", 2000),
	({
		"sources": [
			{"key": "a", "doctype": "Goal", "status": "available", "count": 5},
			{"key": "b", "doctype": "X", "status": "unavailable"},
		],
		"metrics": [
			{"id": "m1", "status": "available", "category": "supporting", "source": "Goal", "doctype": "Goal"},
			{"id": "m2", "status": "partial"},
			{"id": "m3", "status": "unsupported"},
		],
		"questions": [{"id": "q1", "metric_id": "m1"}, {"id": "q2"}],
		"data_quality": [{"issue": "stale"}],
		"evidence_gaps": [{"gap": "missing sign-off"}],
	}, "Criterion 5", "ucc_analytics_criterion_5", "summary", "5.1.1", 500),
	(None, "Criterion 3", "ucc_analytics_criterion_3", "drilldown", "3.1.1", 200),
]

for args in FIXTURES:
	expected = legacy_contract(*copy.deepcopy(args))
	actual = ported_contract(*copy.deepcopy(args))
	assert expected == actual, f"contract mismatch for fixture {args[1]}/{args[3]}/{args[4]}:\n{expected}\nvs\n{actual}"

# is_permission_error: verified against the legacy per-criterion behaviour.
# Criteria 1-6 lack the "403" substring check; Criterion 7 alone has it. The
# ported version applies it universally (Phase 2 plan decision) -- assert it
# matches the superset (C7) behaviour, since that's the one deliberate
# difference from six of the seven legacy copies.
CASES = [
	("PermissionError: No permission to read Assessment Result", True),
	("frappe.exceptions.PermissionError: not permitted to access Student Applicant", True),
	("DoesNotExistError: nope", False),
	("InternalServerError: boom", False),
	("HTTP 403 Forbidden", True),  # the deliberate C7-only case, applied everywhere here
	("", False),
	(None, False),
]
for value, expected in CASES:
	actual = ported_is_permission_error(value)
	assert actual == expected, f"is_permission_error({value!r}) = {actual}, expected {expected}"
assert ported_is_permission_error(Exception("not allowed to read Course Schedule")) is True

print(f"PASS: ported analytics.contracts matches legacy standardise_response_contract "
      f"across {len(FIXTURES)} fixtures; is_permission_error matches C7's superset behaviour "
      f"({len(CASES) + 1} cases)")
