# Phase 9 and Phase 11 groundwork

What was built, what was deliberately not built, and which CLAUDE.md §19
decisions are blocking the rest.

---

## Phase 11 — Monitoring (CLAUDE.md §9 Phase 11)

### Built

| Piece | File |
|---|---|
| Rule definitions (pure evaluators) | `monitoring/rule_registry.py` |
| Run/dedup/resolve engine | `monitoring/engine.py` |
| `UCC Monitoring Rule` | `sophia/doctype/ucc_monitoring_rule/` |
| `UCC Monitoring Run` | `sophia/doctype/ucc_monitoring_run/` |
| `UCC Monitoring Finding` | `sophia/doctype/ucc_monitoring_finding/` |
| `run_monitoring`, `get_monitoring_findings` | `api.py` |
| 82 checks incl. 6 mutation-verified | `tools/test_ucc_intelligence_monitoring.py` |

Three rules, from CLAUDE.md §11's own use-case list:

1. `student_log_background_required` — use case 1. A log may only be
   completed or closed once the student background is filled.
2. `student_log_dummy_text` — use case 2. Template placeholder text left in
   a live record.
3. `quality_action_closure_evidence` — use case 4. A closure must carry an
   owner, a target date, a resolution and an action taken.

### Design decisions

**Rules are Python, not database rows.** CLAUDE.md §11 requires the
pass/fail decision to be deterministic and §5 wants configuration
reviewable. An evaluator stored as a record is neither diffable nor
testable. The DocType carries only what an administrator legitimately
changes without a deploy: enabled, severity, responsible role, effective
date, remediation text.

**Idempotence is the engine's real contract.** A scheduled rule runs daily
over mostly-unchanged records. Findings are keyed `rule_id::doctype::record`:
still failing → touch; fixed → resolve (never delete); regressed → reopen
the same row; suppressed → left alone. The test runs a rule seven times and
asserts one finding, then walks fix → resolve → regress → reopen →
suppress → rerun.

**Monitoring defaults OFF when settings are unreadable.** It reads every
record in its target DocType, so a settings fault must not start a scan.
(Conversation persistence defaults the other way, because there the safe
default is preserving existing behaviour.)

**`ignore_permissions` on the counting, never on the disclosure.** A run
must see every record in scope or its counts are silently wrong. What it
produces — a `UCC Monitoring Finding` naming a DocType and a record id — is
permission-gated normally, and opening the record still goes through that
record's own permissions.

### Not built, and why

CLAUDE.md §11 use cases 5–8 (course review evidence, expiring contracts,
the QA calendar, departmental housekeeping summaries) need field-level
facts about DocTypes this migration has not inspected. Guessing field names
produces rules that silently never fire, which is worse than not shipping
them. They need a field-mapping pass first.

### Bench steps required

```bash
bench --site <site> migrate          # creates the three DocTypes
bench --site <site> console
>>> frappe.call("ucc_intelligence.api.run_monitoring", rule="student_log_dummy_text")
```

Scheduler wiring is a `hooks.py` entry, and `hooks.py` is bench-generated
and deliberately not in this repo (CLAUDE.md §7). Add:

```python
scheduler_events = {
    "daily": ["ucc_intelligence.monitoring.engine.scheduled_run"],
}
```

`scheduled_run()` is already gated on `enable_monitoring`, so adding the
hook does not start anything until the toggle is switched on.

---

## Phase 9 — Document knowledge (CLAUDE.md §9 Phase 9)

### Built

| Piece | File |
|---|---|
| Chunking, indexing, stale detection, retrieval | `knowledge/retrieval.py` |
| `UCC Knowledge Source` | `sophia/doctype/ucc_knowledge_source/` |
| `UCC Knowledge Chunk` | `sophia/doctype/ucc_knowledge_chunk/` |
| `search_knowledge` | `api.py` |
| 40 checks incl. 5 mutation-verified | `tools/test_ucc_intelligence_knowledge.py` |

Against CLAUDE.md §9's "minimum knowledge features":

| Feature | Status |
|---|---|
| Source registration | Done |
| Version handling | Done (`document_version`) |
| Effective and superseded dates | Done, enforced structurally |
| Section-level retrieval | Done (headings, then paragraph packing) |
| Permission filtering | Done (per-source role + DocType permissions) |
| Citations | Done (document · version · section) |
| Sync status | Done |
| Stale-index detection | Done (content checksum) |
| Deletion and re-indexing | Done (chunks replaced wholesale) |
| Test queries with expected sources | Done |

**Source priority is structural, not scored.** A superseded, inactive or
not-yet-effective document is not a candidate at all — it cannot be
returned however well its wording matches. An answer citing a retired
policy is worse than no answer, so this is enforced by exclusion rather
than ranking, and the test asserts absence.

### Deliberately NOT built — retrieval is keyword, not semantic

There is no embeddings provider, and that is a decision rather than an
omission. Embeddings mean sending UCC policy and course content to an
external service, which is a **CLAUDE.md §19 blocking item** on two counts:
the approved provider account, and whether institutional data may leave the
estate. Neither has been decided.

**Safest reversible default applied:** keyword retrieval with heading
weighting. No external account, no new data-sharing agreement, no vector
store, and no document content leaves the site — the test asserts
`retrieval.py` contains no HTTP call of any kind. `search()`'s contract (a
ranked list of sections with citations) does not change when a semantic
scorer is added behind it, so this is reversible rather than a fork.

### Other §19 items reached, and the defaults applied

| §19 item | Default applied | Reversible? |
|---|---|---|
| Approved AI provider account | `ai_provider` Select offers **OpenAI only** — the only one implemented. No other provider invented. | Yes — add an option when one is approved |
| Whether student/policy data may go to an external provider | Knowledge retrieval stays entirely local; no document content is sent anywhere | Yes |
| Document repository of record | Frappe `File` attachments only. Google Drive is **not** wired up | Yes — `attached_file` becomes one source type among several |
| PDF/DOCX extraction | Not implemented — ingestion takes text that is already text. A new dependency is a separate decision | Yes |

None of these were guessed at. Each is flagged here rather than answered.

### Bench steps required

```bash
bench --site <site> migrate          # creates the two DocTypes
```

Then enable **Document Knowledge** on UCC Intelligence Settings (it is off
by default, and `search_knowledge` returns an empty result with a note
while it is off, rather than querying an empty index).

Registering and indexing a document, until an ingestion UI exists:

```python
source = frappe.get_doc({
    "doctype": "UCC Knowledge Source",
    "title": "Refund Policy",
    "source_type": "Policy",
    "document_version": "3",
    "effective_date": "2026-01-01",
    "classification": "Internal",
}).insert()

from ucc_intelligence.knowledge import retrieval
retrieval.index_source(source.name, open("/path/to/policy.md").read())
```
