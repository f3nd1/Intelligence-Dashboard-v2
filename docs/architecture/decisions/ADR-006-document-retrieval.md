# ADR-006: Document retrieval technology

## Status
Accepted (2026-07-31) — narrow scope, deliberately reversible

## Context
CLAUDE.md Phase 9 requires permission-aware, version-aware document
retrieval with citations. Semantic retrieval would mean sending UCC policy
and course content to an external embeddings provider.

## Options considered
1. External embeddings + vector store.
2. Keyword retrieval over locally-stored chunks.
3. No retrieval until a provider is approved.

## Decision
Option 2. Section-level keyword retrieval with heading weighting, entirely
inside the Frappe site.

## Rationale
Option 1 is a CLAUDE.md §19 blocking item on two counts — the approved
provider account, and whether institutional data may leave the estate —
neither decided. Option 3 leaves a required capability unbuilt while waiting
on a decision that is not ours. Option 2 delivers every one of §9's minimum
features with no external account and no new data-sharing agreement.

## Consequences
- Retrieval matches wording, not meaning. A question phrased differently
  from the policy may miss.
- `search()`'s contract — ranked sections with citations — does not change
  when a semantic scorer is added behind it, so this is reversible rather
  than a fork.
- No document content leaves the site. The test asserts `retrieval.py`
  contains no HTTP call of any kind.

## Revisit triggers
An approved embeddings provider, or evidence that keyword recall is missing
answers staff need.
