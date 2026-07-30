# UCC Intelligence Settings — Plan

**Status: planning only, nothing built yet.** Same pattern as every phase — review and confirm before
any DocType or code lands.

**Base**: CLAUDE.md §7.1's `UCC Intelligence Settings`, "Recommended as a Single DocType." Used as
the base, not reinvented — a Frappe **Single** (one record, no list) is the same pattern already live
in this exact codebase for `Insights Settings` (read all night via `frappe.db.get_singles_dict`), so
it's a proven, native fit, not a new concept being introduced.

**Where it lives**: `ucc_intelligence/ucc_intelligence/sophia/doctype/ucc_intelligence_settings/`
— under the `Sophia` module, matching `UCC Dashboard Access`'s actual location, not CLAUDE.md §7's
abstract path (`.../ucc_intelligence/doctype/...` with no module folder) — CLAUDE.md itself says its
proposed tree is "the intended logical structure, not a licence to manually create an incompatible
scaffold" (§7); matching what's actually there beats matching the doc literally.

**No custom page.** A Single DocType gets a full Desk form for free — fields, sections, save/reload,
permissions — with zero custom frontend code. The one thing that doesn't fall out of a plain form
(item 7, live status) is available through **Frappe's own `frm.dashboard.add_indicator()` API**,
called from the DocType's standard `.js` controller file on `refresh`. That's still native Frappe, not
a hand-rolled page — nothing here needs `sophia_analytics.js`-style custom page machinery. Building a
whole new branded page for what's fundamentally a settings form would be solving a problem Frappe
already solves.

---

## 1. Access control — reuse `UCC Dashboard Access`, don't duplicate it

Checked the existing DocType directly rather than assuming: `UCC Dashboard Access`
(`sophia/doctype/ucc_dashboard_access/ucc_dashboard_access.json`) already stores exactly this — one
row per role, with `show_criterion_1` through `show_criterion_7` (plus `show_analytics`/
`show_explore`/`show_ask_ucc`, `enabled`, `default_when_unconfigured`). It already has a full Desk
List View with create/edit/delete (`System Manager` permission, per its own JSON). There is nothing to
add for the underlying feature — it works today.

**What the Settings page adds is a convenient entry point, not new storage:**

- A read-only summary on the Settings form ("6 roles configured — Admissions Officer, Quality Lead,
  ..."), built from `permissions/access.py`'s existing `load_rows()` — reused as-is, not
  reimplemented, via one new thin whitelisted method (e.g. `get_dashboard_access_summary()`) that just
  reshapes `load_rows()`'s output for display.
- A button — `frm.add_custom_button("Manage Role Access", () => frappe.set_route("List", "UCC Dashboard Access"))`
  — routing straight to the existing list for actual editing. No new edit UI.

This keeps `UCC Dashboard Access` as the single source of truth for who sees what, exactly as asked.

---

## 2. Field-by-field plan, marked genuinely-real vs. placeholder vs. needs-decision

"Real" = the field (or a check derived from it) has a genuine effect or genuine live signal *today*.
"Placeholder" = schema only — correct to define now per CLAUDE.md's own phase ordering (Phase 7's
DocTypes precede Phase 8's AI client etc.), but flipping it does nothing until that later phase's
consumer exists. Being explicit about which is which is the point of this section.

### AI settings

| Field | Type | Status |
|---|---|---|
| `enable_ai` | Check | **Placeholder** — no AI client exists yet to gate. This is the field Phase 8 will read once built. |
| `ai_provider` | Select | **Placeholder**, but worth capturing now — CLAUDE.md §19 already lists "approved AI provider account" as a blocking decision; recording Felix's choice here the moment it's made avoids losing it. |
| `ai_model` | Data | **Placeholder**, same reasoning. |
| `max_output_tokens` | Int | **Placeholder.** |
| `default_temperature` | Float | **Placeholder**, but ships with a real default (`0.2`) — CLAUDE.md §7.1 says "normally low for institutional answers"; encoding that as the shipped default documents the intended policy even before anything enforces it. |
| `ai_request_timeout_seconds` | Int | **Placeholder.** |
| API key / secret | — | **Needs a decision, not a field yet.** CLAUDE.md §7.1 is explicit: "Do not store raw provider secrets in ordinary readable fields... Prefer site configuration or the approved secret manager." Recommendation: **don't add a key field to this DocType in this round at all.** There's no AI client to consume it yet (Phase 8), so a field here would be a secret-shaped placeholder with nowhere safe defined for it to go. When Phase 8 starts, this becomes an explicit ADR (§18 Decision 5 is already reserved for exactly this) — Frappe `Password` fieldtype vs. `site_config.json` vs. an external secret manager — not a default silently picked now. |

### Memory settings

| Field | Type | Status |
|---|---|---|
| `enable_persistent_conversations` | Check | **Placeholder — the most placeholder of all of them.** Not just "no consumer yet": the storage itself (`UCC AI Conversation`/`UCC AI Message`, CLAUDE.md §7.2-7.3) doesn't exist either. This toggle would control literally nothing right now, not even a dormant feature. Worth a real choice: build the field now (schema-first, matches Phase 7 sequencing) or hold it until the Conversation/Message DocTypes exist so nothing on this form is ever a toggle for something that isn't even modeled yet. Leaning toward building it now for consistency with the rest of the form, but flagging this as the one field where "placeholder" is least comfortable — say if you'd rather hold it. |
| `conversation_retention_days` | Int | **Placeholder**, same status as above. |

### Knowledge / document search

| Field | Type | Status |
|---|---|---|
| `enable_document_knowledge` | Check | **Placeholder**, as you already flagged — feature is entirely unbuilt (Phase 9), document repository of record is still an open blocking question (Ask UCC plan §4). Toggle only. |

### Monitoring

| Field | Type | Status |
|---|---|---|
| `enable_monitoring` | Check | **Placeholder**, as flagged — Phase 11 unbuilt. Toggle only. |

### Controlled actions

| Field | Type | Status |
|---|---|---|
| `default_action_approval_level` | Select | **Placeholder**, but the option set matters: only **Read-only (Level 0)**, **Draft-only (Level 1)**, **Confirm-before-execute (Level 2)** are offered — CLAUDE.md's own table marks Level 3 "policy-approved automatic" as not yet approved and Level 4 "prohibited initially." The picker shouldn't offer levels CLAUDE.md itself says aren't available yet. Defaults to **Read-only** — the safest value, so if anything ever reads this setting before real gating exists, the default doesn't grant more than intended. |

---

## 3. Status view (item 7) — what's honestly checkable today

Three tiers, not one "green/red" claim:

**Genuinely live, zero new risk, reusing existing code:**
- **Insights charts**: for each of the 6 `admission_intelligence` chart titles
  (`admission_intelligence_embed.CHART_TITLES`), whether its `Insights Query v3` record exists
  (`frappe.db.get_value(..., "name")` — the exact lookup `run_chart_query()` already does). Shows
  "2/6 built" today, reusing the real mechanism, not a guess.
- **`Insights Settings.apply_user_permissions`**: read directly and flagged red if `0` — this is the
  single site-wide toggle tonight's whole permission model depends on
  (`admission_intelligence_embed.py`'s module docstring already calls this out as the thing that
  silently breaks every embedded chart's permission enforcement at once if switched off). A settings
  page that *doesn't* surface this would be missing the one signal most likely to matter later.
- **Dashboard Access rows configured**: count + list, from `load_rows()` (§1).
- **Basic DB/site reachability**: e.g. `frappe.get_meta("Student Applicant")` resolving without error
  — the same kind of check `resolve_source()` already does in every criterion module, reused, not new.

**Configuration-presence only, explicitly not "verified working":**
- "AI configured" = `ai_provider` and `ai_model` fields are non-empty. This is **not** the same claim
  as "AI works" — there's no client to test-call yet, and the status view should say "configured" or
  "not configured," never "healthy," until Phase 8 exists to make that claim true.

**Not included, because there's nothing to check:** memory, knowledge, monitoring, controlled
actions — no live signal exists for any of these; the status view shows their toggle state only
(on/off), not a health check, since there's no feature behind them yet to be healthy or not.

---

## 4. Permissions on the Settings DocType itself

Recommend `System Manager` only for read/write, matching `UCC Dashboard Access`'s own permission row
exactly (consistency, and it's a real, already-approved pattern in this codebase). CLAUDE.md's own
§19 lists "UCC role matrix" as an open blocking item generally — until that's resolved, defaulting to
the same restrictive role already used elsewhere avoids inventing a new access tier speculatively.

---

## 5. What I'd build first, if this is confirmed

1. `UCC Intelligence Settings` DocType JSON (Single, module Sophia) — all fields from §2, `Select`
   options and the Level-0/1/2-only constraint from §2's controlled-actions row, `default_temperature`
   shipping at `0.2`, `default_action_approval_level` shipping at "Read-only."
2. `get_dashboard_access_summary()` — thin wrapper around the existing `load_rows()`, nothing
   reimplemented.
3. The DocType's `.js` controller — `refresh` handler calling one new whitelisted status method (§3's
   "genuinely live" tier only) and rendering via `frm.dashboard.add_indicator()`; the "Manage Role
   Access" button from §1.
4. A smoke test in the same style as tonight's other self-checks — construct the Settings values,
   confirm the status method's output shape, confirm the approval-level Select genuinely only offers
   0/1/2.

Nothing here touches `criterion_1.py`-through-`criterion_7.py`, `admission_intelligence_embed.py`, or
any existing frontend page — this is new, additive surface only.

---

## Decisions (Felix, 2026-07-30) and what was built

1. **Memory toggle: cut entirely.** `enable_persistent_conversations`/`conversation_retention_days`
   are not on the DocType — no field for storage that doesn't exist yet.
2. **AI provider "configured elsewhere" indicator: added**, as a status check, not a stored field.
   `settings/status.py`'s `get_ai_provider_configured()` reads a conventional site_config key
   (`ucc_intelligence_ai_api_key`) via `frappe.conf.get(...)` and reports presence only — never the
   value, never written from this DocType. Shown as a dashboard indicator on the form.
3. **Controlled-actions default approval level: cut entirely**, same reasoning as the memory toggle —
   no field, no Select, no shipped default. `enable_document_knowledge` and `enable_monitoring` kept
   as planned.

**Built**:

- `sophia/doctype/ucc_intelligence_settings/` — the Single DocType (JSON + `.py` controller with the
  `default_temperature` 0-2 clamp + `.js` controller), module `Sophia`, System Manager read/write only.
- `settings/status.py` — `get_dashboard_access_summary()` (thin reshape of the existing
  `load_rows()`, no duplication), `get_insights_chart_status()`, `get_insights_permission_setting()`,
  `get_ai_provider_configured()`, `get_db_reachable()`, and `get_status_summary()` combining them —
  exactly the "genuinely live" tier from §3, nothing from the other two tiers pretending to be more
  than it is. The "AI provider/model fields filled" indicator (configuration-presence tier) is
  computed client-side from `frm.doc` instead — it only needs the form's own already-loaded fields, no
  server round-trip.
- `api.py`'s `get_settings_status()` — gates on `frappe.only_for("System Manager")` before returning
  anything, since the underlying reads aren't all self-gating (`load_rows()` uses
  `ignore_permissions=True` by its own existing design) and this endpoint returns more than any one
  user should necessarily see.
- `tools/test_ucc_intelligence_settings.py` — 43/43 checks: each status function against a stubbed
  `frappe`, the temperature clamp, the DocType JSON shape (explicitly asserts the three cut fields are
  *absent*, not just unused, and that no field name suggests a stored secret), and the System Manager
  gate firing before data returns.

**Verification**: new test 43/43; full existing regression suite still green (all criteria, access,
contracts, page tests); legacy directories (`custom-html-block/`, `server-scripts/`, `src/`, `dist/`,
`archive/`) confirmed byte-for-byte untouched via `git diff --stat`.

**Not yet done, needs Felix's bench access**: the DocType hasn't been installed/migrated on a real
site, so the form itself (fields, indicators, the Manage Role Access button) hasn't been seen live —
same bench-dependent gap every other phase has had at this stage.
