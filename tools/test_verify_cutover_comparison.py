#!/usr/bin/env python3
"""Prove verify_cutover.py's comparison tells AI wording apart from a real
Server Script dependency.

WHY THIS EXISTS
The bench run came back 38/40: everything matched with the Server Scripts
disabled except ask_quality_action and ask_student_journey. The proposed
reading was "that's just the language model writing different words". That
is a plausible story, and plausible stories are exactly what should not be
accepted on a security-relevant test -- if a Server Script really were still
being reached, "it's just the AI" is what it would look like.

So the comparison was SPLIT rather than relaxed, and this file proves the
split works: a difference confined to model wording is reported as such,
and a difference that touches facts, sources or ai_status still FAILS.
Loosening the test to make it green would fail the checks below.

    python3 tools/test_verify_cutover_comparison.py
"""
import copy
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "docs" / "migration" / "scripts" / "verify_cutover.py"

checks = []


def report(ok, message, detail=""):
	print(("PASS" if ok else "FAIL") + ": " + message + (("\n        " + detail) if detail and not ok else ""))
	checks.append(bool(ok))
	return bool(ok)


# The script imports frappe at module scope and calls run() at the bottom.
# Load only the definitions above run() -- the comparison logic is what is
# under test, not the bench orchestration.
sys.modules.setdefault("frappe", types.ModuleType("frappe"))
source = SCRIPT.read_text(encoding="utf-8")
namespace = {"__name__": "verify_cutover"}
exec(compile(source.split("\ndef run():")[0], str(SCRIPT), "exec"), namespace)  # noqa: S102

comparable = namespace["comparable"]
first_difference = namespace["first_difference"]


def classify(before, after):
	"""The exact decision verify_cutover makes on the bench."""
	identical = comparable(before) == comparable(after)
	ai_only = comparable(before, drop_ai=True) == comparable(after, drop_ai=True)
	where = first_difference(before, after)
	return {"identical": identical, "ai_only": ai_only, "where": where[0] if where else None}


# A realistic Ask UCC response, shaped like the real contract.
BASE = {
	"ok": True,
	"module": "quality_action",
	"conversation_id": "conv-1",
	"ai_status": "available",
	"answer": {"text": "This Quality Action is open and has two outstanding items.",
		"model": "gpt-4o-mini-2024-07-18", "token_usage": 142},
	"answer_error": None,
	"facts": {"get_quality_action_summary": {
		"status": "available", "quality_action": "QA-0001", "title": "Late fee reconciliation",
		"open_count": 2, "completed_count": 1, "overdue_count": 0}},
	"sources": [{"doctype": "Quality Action", "record": "QA-0001", "status": "available"}],
	"warnings": [],
}


# ============================================================
# 1. AI WORDING ONLY -- the reported case. Must be recognised.
# ============================================================
reworded = copy.deepcopy(BASE)
reworded["answer"]["text"] = "There are two items still outstanding on this Quality Action."
reworded["answer"]["token_usage"] = 151
reworded["conversation_id"] = "conv-2"

verdict = classify(BASE, reworded)
report(not verdict["identical"], "a reworded AI answer does NOT compare identical (this is why the bench saw 38/40)")
report(verdict["ai_only"], "...and IS recognised as AI-wording-only")
report(verdict["where"].startswith(".answer"),
	"...with the difference located inside .answer, not the facts",
	"located at %s" % verdict["where"])

# Model and token count moving too is still AI-only.
model_changed = copy.deepcopy(reworded)
model_changed["answer"]["model"] = "gpt-4o-2024-11-20"
report(classify(BASE, model_changed)["ai_only"],
	"a different model id and token count are still AI-only, not a data difference")


# ============================================================
# 2. THE FALSIFICATION -- differences that must still FAIL.
#
# If the split were a relaxation rather than a split, these would pass.
# ============================================================
fact_changed = copy.deepcopy(BASE)
fact_changed["facts"]["get_quality_action_summary"]["open_count"] = 5
verdict = classify(BASE, fact_changed)
report(not verdict["ai_only"],
	"a changed FACT is NOT excused as AI wording -- this is what a live Server Script dependency looks like")
report(verdict["where"] == ".facts.get_quality_action_summary.open_count",
	"...and is located precisely", "located at %s" % verdict["where"])

fact_missing = copy.deepcopy(BASE)
del fact_missing["facts"]["get_quality_action_summary"]["overdue_count"]
report(not classify(BASE, fact_missing)["ai_only"], "a MISSING fact still fails")

source_changed = copy.deepcopy(BASE)
source_changed["sources"][0]["record"] = "QA-0002"
verdict = classify(BASE, source_changed)
report(not verdict["ai_only"], "a changed SOURCE record still fails")
report(verdict["where"] == ".sources[0].record", "...and is located precisely",
	"located at %s" % verdict["where"])

source_dropped = copy.deepcopy(BASE)
source_dropped["sources"] = []
report(not classify(BASE, source_dropped)["ai_only"], "a DROPPED source still fails")

status_changed = copy.deepcopy(BASE)
status_changed["ai_status"] = "unavailable"
report(not classify(BASE, status_changed)["ai_only"],
	"a changed ai_status still fails -- AI silently stopping running is a real difference")

answer_vanished = copy.deepcopy(BASE)
answer_vanished["answer"] = None
report(not classify(BASE, answer_vanished)["ai_only"],
	"an answer DISAPPEARING is not 'different wording' -- the presence of an answer is compared")

tool_changed = copy.deepcopy(BASE)
tool_changed["facts"]["get_quality_action_summary"]["status"] = "permission_denied"
report(not classify(BASE, tool_changed)["ai_only"], "a fact-level permission change still fails")


# ============================================================
# 3. Deterministic surfaces must be compared with FULL strictness.
#
# A criterion response carries no AI text, so the AI split must not weaken
# it in any way -- otherwise the split WOULD be a relaxation.
# ============================================================
CRITERION = {
	"ok": True,
	"meta": {"criterion": "1", "subcriterion": "1.1.1", "generated_at": "2026-07-31 10:00:00",
		"api_method": "ucc_intelligence.api.get_criterion_1"},
	"metrics": [{"id": "m1", "label": "Policies overdue", "value": 3, "status": "available"}],
	"sources": [{"doctype": "Quality Action", "status": "available"}],
}
same_but_later = copy.deepcopy(CRITERION)
same_but_later["meta"]["generated_at"] = "2026-07-31 10:05:00"
report(classify(CRITERION, same_but_later)["identical"],
	"a criterion response differing ONLY by timestamp compares identical")

metric_moved = copy.deepcopy(CRITERION)
metric_moved["metrics"][0]["value"] = 4
verdict = classify(CRITERION, metric_moved)
report(not verdict["identical"] and not verdict["ai_only"],
	"a criterion METRIC changing fails under both comparisons -- no AI text to hide behind")
report(verdict["where"] == ".metrics[0].value", "...located precisely",
	"located at %s" % verdict["where"])

method_changed = copy.deepcopy(CRITERION)
method_changed["meta"]["api_method"] = "ucc_analytics_criterion_1"
report(not classify(CRITERION, method_changed)["ai_only"],
	"a response reverting to the Server Script method name fails -- exactly the regression this guards")


# ============================================================
# 4. The AI exclusion must be NARROW.
# ============================================================
report(namespace["AI_TEXT_KEYS"] == {"text", "answer_error", "model", "token_usage"},
	"only model-written keys are excluded, and only inside `answer`",
	"excluded: %s" % sorted(namespace["AI_TEXT_KEYS"]))
report("facts" not in namespace["AI_TEXT_KEYS"] and "sources" not in namespace["AI_TEXT_KEYS"],
	"facts and sources are NEVER excluded")
report("facts" not in namespace["VOLATILE_KEYS"] and "sources" not in namespace["VOLATILE_KEYS"],
	"...and are not hidden in the volatile list either")

# A key named `text` OUTSIDE an answer must still be compared -- the
# exclusion is positional, not name-based.
outside = copy.deepcopy(BASE)
outside["facts"]["get_quality_action_summary"]["text"] = "original"
other = copy.deepcopy(outside)
other["facts"]["get_quality_action_summary"]["text"] = "changed"
report(not classify(outside, other)["ai_only"],
	"a field called `text` inside FACTS is still compared -- the exclusion is positional, not by name")

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
