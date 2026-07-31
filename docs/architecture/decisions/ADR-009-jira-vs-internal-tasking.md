# ADR-009: Jira vs internal Frappe tasking

## Status
Accepted (2026-07-31)

## Context
CLAUDE.md Phase 12 gives "create a Jira ticket after confirmation" as the
worked example of a Level 2 controlled action.

## Options considered
1. Jira via its REST API.
2. Frappe's own ToDo.
3. Neither — draft-only actions.

## Decision
Option 2 now, option 1 later. `create_internal_task` creates a Frappe ToDo.

## Rationale
Jira needs credentials and a permission-scope decision (CLAUDE.md §19), and
is explicitly out of scope. ToDo is already in the site, already
permission-controlled, and exercises the entire propose → approve → execute
path with a real write — which is what needed proving. Option 3 would have
left the level-2 path untested.

## Consequences
- The action registry gains a Jira entry later without changing the service:
  actions are allowlist entries, not new machinery.
- Tasks created today live in Frappe, not Jira. If both end up in use, that
  is a split worth avoiding — hence "later", not "never".

## Revisit triggers
Jira credentials and an agreed permission scope.
