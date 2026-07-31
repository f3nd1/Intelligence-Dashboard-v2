# hooks.py entries this app needs

`hooks.py` is bench-generated and deliberately not in this repository
(CLAUDE.md §7: scaffold files come from the installed Frappe version, not
hand-authored). These are the entries to add to it on the bench.

## Scheduler — monitoring

```python
scheduler_events = {
    "daily": [
        "ucc_intelligence.monitoring.engine.run_daily",
    ],
    "weekly": [
        "ucc_intelligence.monitoring.engine.run_weekly",
    ],
    "monthly": [
        # Frappe has no quarterly cron. run_quarterly() self-limits to the
        # first month of a quarter, so registering it monthly is correct and
        # keeps the cadence visible in one place rather than in a custom
        # scheduler.
        "ucc_intelligence.monitoring.engine.run_quarterly",
    ],
}
```

Every entry is gated on `UCC Intelligence Settings.enable_monitoring`, which
defaults OFF. Adding these hooks starts nothing until monitoring is switched
on deliberately.

Per-rule cadence lives in `monitoring/engine.py`'s `RULE_CADENCE`:

| Rule | Cadence |
|---|---|
| `student_log_background_required` | daily |
| `student_log_dummy_text` | daily |
| `quality_action_closure_evidence` | daily |
| `expiring_contract` | daily |
| `department_housekeeping` | weekly |
| `course_review_evidence` | weekly |
| `qa_calendar_record` | quarterly |

## Fixtures — the approval workflow

```python
fixtures = [
    {"dt": "Workflow", "filters": [["name", "in", ["UCC AI Action Approval"]]]},
    {"dt": "Workflow State", "filters": [["name", "in", [
        "Draft", "Pending Approval", "Approved", "Rejected", "Executed"]]]},
    {"dt": "Workflow Action Master", "filters": [["name", "in", [
        "Submit for Approval", "Approve", "Reject", "Execute"]]]},
]
```

`ucc_intelligence/fixtures/workflow.json` is the workflow itself. Without it
installed, `UCC AI Action Request` records can be created but no transition
is possible — which fails safe: nothing can reach Approved, so nothing can
execute.

## Knowledge re-indexing (optional)

```python
scheduler_events = {
    "daily": [
        "ucc_intelligence.knowledge.ingestion.reindex_stale",
    ],
}
```

Re-indexes any source whose attached file no longer matches its stored
checksum. Only worth enabling once real documents are registered.
