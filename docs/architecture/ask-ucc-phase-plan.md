# Ask UCC / Memory / Knowledge / Monitoring / Actions — Phase Groundwork

**Status: planning only, not yet approved for implementation.** No code changes accompany this
document. Per every prior phase's practice, this is presented for review; nothing gets built until
Felix confirms the direction, same as the Insights pilot, the Criterion 4 architecture change, and
every phase before them.

**Scope of this document**: CLAUDE.md's Phases 6 through 12 (Ask UCC, application DocTypes, secure
AI integration, institutional knowledge, memory, monitoring, controlled actions) are all still
unstarted — everything built so far (all 7 Analytics criteria, the Insights embed work) is Phase
0-6's *Analytics* track only. This document covers the *next* track: Ask UCC and everything CLAUDE.md
hangs off it.

---

## 1. Legacy Ask UCC, grounded — read before trusting the architecture below

Same discipline as every Analytics criterion: inspect the deployed source before designing its
replacement, not assumptions. The three legacy Server Scripts are in-repo and were read in full —
`server-scripts/UCC Ask - Student Journey.py` (4208 lines), `- Recruitment Agent.py` (2153 lines),
`- Quality Action.py` (911 lines) — plus the frontend call sites in `custom-html-block/JAVASCRIPT.js`.
Several findings change what Section 2 below should actually propose, rather than just confirming it.

### 1.1 The current system is almost entirely deterministic — "AI" barely exists today

`answer` in all three modules' response shape is **always** template text built from ERPNext facts —
never AI-generated prose. Only Student Journey ever calls OpenAI at all, and only to classify
question *intent* and canonicalize the question text (a structured-output routing call) — not to
generate the answer. `ai_used` in the response only reflects whether that routing call ran, and the
frontend's "OpenAI interpreted the question, ERPNext supplied the facts" note (`JAVASCRIPT.js:1163`)
can currently only ever fire from that one module.

Concretely, of the three modules:

- **Recruitment Agent and Quality Action have zero OpenAI/LLM code anywhere** (confirmed by grep —
  zero matches for "openai"/"api_key" in either file). Intent detection is pure keyword/regex matching
  over the question text. The frontend sends `conversation` and `openai_api_key` to these modules
  anyway; both parameters are silently ignored server-side.
- **Student Journey** reads an optional `openai_api_key` from the request, calls
  `https://api.openai.com/v1/responses` server-side for intent routing only, and falls back to fully
  deterministic behaviour if no key is supplied (or a placeholder key) — genuine progressive
  enhancement, already matching CLAUDE.md §8.5's principle even in the legacy code.
- **A live bug, worth confirming before assuming this path ever worked**: Student Journey's OpenAI
  call builds `payload["model"]` from a module-level `OPENAI_MODEL` constant that is **never defined
  anywhere in this 4208-line file** — and the reference sits *outside* the `try/except` wrapping the
  actual HTTP call, so supplying a real key would raise an uncaught `NameError`, not a handled
  fallback. This repo's copy of the script may not be byte-identical to whatever's actually deployed
  (the same src-vs-deployed gap CLAUDE.md flags for Analytics) — worth a direct check against the live
  Server Script text before concluding the AI path has *never* worked in production, but on the code
  as committed here, it can't.

**Why this matters for planning**: CLAUDE.md's Phase 8 vision (real AI explanation of retrieved facts,
§2.1 steps 6-8 below) is not an incremental refinement of what exists today — it's a genuinely new
capability. The current system's "AI" is closer to "sometimes-broken query classification" than
"answers questions." Framing the new build as "adding proper AI on top of what's there" undersells
the actual scope; it's closer to building the AI-explanation layer for the first time; while replacing
already-working deterministic retrieval, which should be preserved and reused, not the AI part.

### 1.2 Real per-module facts and request shapes — grounding Section 2's tool allowlists

| Module | API method | Request fields read server-side | DocTypes actually read |
|---|---|---|---|
| Student Journey | `ucc_ask_student_journey` | `question`, `student_applicant`, `conversation` (JSON, used for routing only), `openai_api_key`, `student_roll_rows` | Student Applicant, Student, Student Admission UCC, Student Group, Assessment Result, Student Attendance, Student Leave Application, Course Schedule, Sales Invoice, File |
| Recruitment Agent | `ucc_ask_recruitment_agent` | `question`, `agent_contract` | Agent Contract, Agent, Supplier Rating, Sales Invoice |
| Quality Action | `ucc_ask_quality_action` | `question`, `quality_action` | Quality Action |

This is the real starting point for Section 2's per-module tool allowlists — e.g. Student Journey's
tools are concretely `get_admission_record`, `get_attendance_summary`, `get_assessment_results`,
`get_leave_records`, `get_group_and_schedule`, `get_fee_status` (from Sales Invoice), each scoped to
exactly the DocType(s) shown above, not a broader guess.

### 1.3 Conversation history: client-maintained today, and only one module ever reads it

The frontend keeps `state.history` in memory, truncates to the last 20 turns, and resends the whole
thing as a JSON string on *every* request to *all three* modules (`JAVASCRIPT.js:1404-1479`) — nothing
is persisted server-side anywhere in the three Python files (no history doctype, no child table
writes). Only Student Journey's Python actually reads `conversation`, and only for its routing call
(further capped to 10 messages × 1200 chars). This confirms Section 3's memory recommendation from a
different angle: there is no existing server-side conversation persistence to migrate *away from* —
`UCC AI Conversation`/`UCC AI Message` is new work, not a replacement for something already there, and
the local-only recommendation isn't a downgrade from current behaviour, since current behaviour has no
durable memory at all (the browser losing its tab loses the whole conversation today).

### 1.4 The OpenAI key: exactly the weakness CLAUDE.md already names, confirmed precisely

Client-side only, `sessionStorage` key `"uccAiOpenAIKey"`, entered via a modal the first time a
free-form question needs it, skippable by the user (falls back to deterministic-only). No server-side
key storage anywhere — no Settings doctype, no `frappe.conf` entry, no environment variable read in any
of the three files. The frontend attaches this key to **every module's** request regardless of whether
that module's Python ever reads it (only Student Journey does) — meaning today, two-thirds of Ask
UCC's traffic sends a browser-held API key to the server for absolutely no reason. Migrating this to
Phase 8's server-side `ai/client.py` (one place the key is ever touched, never sent from the browser at
all) isn't just the CLAUDE.md-mandated direction (§1.1.9, Phase 8 exit criteria) — it removes a
pointless request-shape hazard that exists today independent of the security argument.

### 1.5 Permission handling: consistent with everything ported tonight, with one real gap

No `ignore_permissions` anywhere in any of the three files — same `frappe.get_list`/`frappe.get_doc`
pattern used throughout the Analytics ports. But errors (including permission errors) are swallowed by
`safe_db_list`/`get_doc_safe`-style wrappers into empty results or `None`, not classified the way
`analytics.contracts.is_permission_error` distinguishes `permission_denied` from `unavailable` today.
Concretely: the legacy system cannot currently tell a user "you don't have access to this" versus "this
record has no data" — it just shows nothing either way. Section 2's step 5 (source packaging with an
explicit `permission_denied` status, reusing the same blocked-source notice already live in Sophia
Analytics) is a genuine, needed improvement here, not a restatement of something the legacy system
already does.

### 1.6 HR module: confirmed still just a placeholder

`JAVASCRIPT.js`'s module registry has a fourth entry, `hr_assistant`, marked `comingSoon: true` with no
`apiMethod` at all — matches CLAUDE.md §3.4's table exactly ("Not yet implemented"). Nothing to ground
here; noted so it isn't mistaken for a fourth legacy script that was missed.

---

## 2. Ask UCC architecture — the tool-first flow, concretely

CLAUDE.md §8.2 specifies the pattern in the abstract (identity → authoritative tool → structured
facts → optional AI explanation → sources shown). This section makes it concrete, mapped onto
CLAUDE.md §7's own proposed module layout and reusing patterns already proven tonight rather than
inventing new ones.

### 2.1 The nine-step flow

1. **Identity & module-level permission resolution.** Before anything else, resolve whether this
   user's roles allow the "Ask UCC" workspace and the specific module (Student Journey / Recruitment
   Agent / Quality Action) at all. This is interface composition, not data permission — same
   distinction CLAUDE.md §3.3 draws for `ucc_dashboard_access` and the same one
   `ucc_intelligence/ucc_intelligence/permissions/access.py` already implements for Analytics. Ask
   UCC needs its own role mapping here (§3 below), not an inherited copy of the Analytics one —
   nothing says a Student Services role that can see Criterion 4 should automatically be able to ask
   about individual students, or vice versa.

2. **Context resolution.** The user picks a module and a record (a record picker, per CLAUDE.md
   Phase 6) — a Student Applicant, an Agent Contract, a Quality Action — or asks a follow-up that
   references the record already in context ("what about his attendance") via the current
   conversation's own history (§3 below; not cross-session memory).

3. **Approved tool selection.** The question is routed to a **fixed, per-module allowlist of named
   retrieval functions** — never a generic "run this doctype query" capability. Student Journey's
   allowlist (§1.2's real DocTypes, not a guess) would be exactly `get_admission_record`,
   `get_attendance_summary`, `get_assessment_results`, `get_leave_records`,
   `get_group_and_schedule`, `get_fee_status` — the *complete* set of things that module can ever
   look up. This is the direct implementation of Phase 8's "AI must not query arbitrary DocTypes... must not accept a
   user-provided method path" — the model picks a tool *name* from an enum, it never constructs or
   supplies a query itself.

4. **Live data retrieval.** Each tool function is structurally the same shape as every criterion
   module built tonight: plain `frappe.get_list`/`frappe.get_doc` calls, no `ignore_permissions=True`,
   returning `{status: available|permission_denied|unavailable, ...}` via the same
   `analytics.contracts.is_permission_error` classification already shared across Criteria 1-7 and
   `admission_intelligence_embed.py`. A blocked source is a normal, expected outcome here too, not a
   special case to invent new handling for.

5. **Source packaging.** Every fact carries `{doctype, record, fields_used, url}` — the same shape
   `sources`/`blockedSourceNames` already consume in `sophia_analytics.js` and
   `analytics.contracts.ARRAY_KEYS`, so a blocked source in Ask UCC renders through the *same*
   `UCCShared.permissionNoticeHtml` component already live for Analytics, not a new one.

6. **Model explanation — only after steps 3-5 return real facts.** The AI client (Phase 8's
   `ai/client.py`) receives the question plus the *already-permission-filtered* facts as context.
   System prompt instruction, non-negotiable: state nothing not present in the supplied facts; every
   claim must cite a fact id from what was actually supplied. This is the literal implementation of
   CLAUDE.md §1.1.11 ("the language model must not become the source of truth") and the "AI must not
   fabricate source links" line in Phase 8.

7. **Output validation.** Before rendering, a small validator (`ai/guardrails.py`) confirms every
   record reference in the model's answer text actually appears in the facts payload passed to it.
   Anything the model mentions that wasn't in the supplied facts is either stripped or the whole
   response is flagged unverified and re-generated once — never silently trusted.

8. **Rendering, source-labeled per §8.4.** Three visually distinct zones: the AI's `answer` text
   (labeled "AI interpretation"), the `facts` grid (labeled by source, e.g. "from Student Applicant,
   live"), and the `sources` list (blocked entries via the existing notice component). This mirrors
   how Sophia Analytics already separates "chart data" from "the page around it" — Ask UCC doesn't
   need a new visual language, just the chat-shaped version of the same one.

9. **Audit.** One `UCC AI Usage Log` row per request — user, module, tools actually called, source
   ids, model, token/cost, latency. No full prompt or PII by default (§12.4, Phase 8) — metadata, not
   content, unless a specific investigation need is documented.

### 2.2 Progressive enhancement is not optional here

§8.5: "the application must still provide useful deterministic analytics if the OpenAI service... is
unavailable." Concretely for Ask UCC: steps 1-5 (record picker → tool call → facts + sources) must
render as a *useful, standalone feature* — a permission-aware record lookup — even with `answer` set
to `null` and an "AI interpretation unavailable" notice in its place. This is not a fallback bolted on
later; it's the same shape Sophia Analytics already has today (raw facts render whether or not any AI
layer exists), so building it this way from day one costs nothing extra and avoids a Phase 8-shaped
retrofit.

### 2.3 Where this lives (filling in CLAUDE.md §7's own scaffold, not inventing a new one)

```
ucc_intelligence/ucc_intelligence/
  ask_ucc/
    contracts.py       # the response shape in §1.4 below, same spirit as analytics/contracts.py
    router.py           # module → allowlisted tool dispatch (step 3)
    student_journey.py  # step-4 tool functions for this module
    recruitment_agent.py
    quality_action.py
  ai/
    client.py           # the ONE place an LLM API key is ever touched (server-side only)
    orchestration.py    # steps 6-7: assemble context, call client, validate output
    prompts.py
    tools.py             # the allowlist registry step 3 dispatches against
    guardrails.py        # step 7's citation-validator
    usage.py              # step 9
```

### 2.4 Proposed response contract (new shape — the Analytics contract doesn't fit a chat turn)

```json
{
  "ok": true,
  "conversation_id": "...",
  "message_id": "...",
  "ai_status": "available | unavailable | disabled | error",
  "answer": {"text": "...", "model": "...", "generated_at": "..."} ,
  "facts": [{"tool": "get_admission_record", "doctype": "Student Applicant", "record": "...", "fields": {}, "retrieved_at": "..."}],
  "sources": [{"doctype": "...", "record": "...", "url": "...", "status": "available | permission_denied"}],
  "warnings": []
}
```

`answer` is `null`, not omitted, when AI is unavailable — the frontend renders the "AI interpretation
unavailable, here are the facts" state explicitly rather than inferring it from a missing key.

---

## 3. Memory: local-only for this phase — a real recommendation, not a menu

**Recommendation: implement local, per-conversation storage only (`UCC AI Conversation` +
`UCC AI Message`, per CLAUDE.md §7.2-7.3) for this round. Formally defer the Zep-vs-Graphiti decision
— not as a placeholder-for-later-Zep, but because CLAUDE.md's own decision rule says not to build it
yet.**

This isn't a coin flip between three options. CLAUDE.md §10 states the rule directly: *"Do not add Zep
or Graphiti merely because it is interesting. Add it only when a concrete use case cannot be handled
adequately by local conversation storage and document retrieval."* Right now:

- **No concrete use case exists yet** — Ask UCC hasn't been built, so there's no real usage pattern
  demonstrating that per-conversation local storage is insufficient. Building toward Zep/Graphiti now
  would be designing for a gap that hasn't been observed, the opposite of what §10 asks for.
- **Zep's approval and plan are an open §19 item** ("whether Zep is approved and which plan is
  available") — building against it now would mean building against an unconfirmed dependency.
- **Graphiti's infrastructure maintainability is the same kind of open §19 item** ("whether Graphiti
  infrastructure can be maintained") — a self-hosted temporal graph is a real ongoing operational
  commitment, not a checkbox.
- §8.6 reinforces this directly: "avoid elaborate abstractions that have no current use... implement
  only the approved provider" — there is no approved memory provider yet.

**What "local-only" concretely means**, per Phase 10's own "suitable memory content" list: the current
conversation's subject, references to official source records, and prior turns *within the same
conversation* — nothing that claims cross-session continuity ("remember what we discussed last
month"). That class of feature is exactly what Zep/Graphiti would be for, and is explicitly the thing
to defer.

**One small, deliberate exception to "just local, no abstraction"**: define `memory/service.py` as a
thin interface now, with `local_store.py` as its only real implementation. This is not the
"elaborate abstraction with no current use" §8.6 warns against — the interface has exactly one
consumer today (Ask UCC's orchestration layer) and one implementation; it just avoids hard-coding
"local storage" into every call site, so a future Zep or Graphiti adapter is a new file implementing
the same interface, not a rewrite of everything that calls memory today.

**Revisit trigger** (an ADR will want this explicitly, per §18's template): once Ask UCC has real
usage and staff repeatedly need continuity local per-conversation storage genuinely can't provide —
not before. Revisit informed by that evidence, not in advance of it.

---

## 4. Blocking decisions this phase would hit — surfaced now, per CLAUDE.md §19

Scanning §19's full list against what this phase actually needs. Marked **BLOCKING** where nothing
meaningful can be built without an answer, **BLOCKING LATER** where it's deferred by design (§2
above) but will need answering before that later phase starts for real, and **already addressed /
not this phase's concern** where it doesn't apply here.

| §19 item | Status this phase | Why |
|---|---|---|
| **Approved AI provider account** | **BLOCKING** | `ai/client.py` cannot be built against a real provider without one. This is the single most load-bearing open item for Phase 8. |
| **Whether student personal data may be sent to an external provider** | **BLOCKING** | Ask UCC's entire premise (Student Journey) is discussing student records. This needs an explicit yes before step 6 of §2.1 sends ANY student data to a model, external or not. |
| **UCC role matrix** | **BLOCKING** | Step 1 of §2.1 needs real roles to build Ask UCC's own module-level gate — this does not automatically inherit from Analytics' role matrix, and guessing it risks either over- or under-exposing modules. |
| **Retention periods** | **BLOCKING** | `UCC AI Conversation`/`Message`/`Usage Log` (§7.2-7.3) have a `retention_category` field in CLAUDE.md's own spec — needs a real value to design correctly from the first migration, not bolted on after data already exists without one. |
| **Document repository of record** | **BLOCKING for Phase 9 specifically** | Can't design ingestion (`knowledge/ingestion.py`) without knowing whether the source is Google Drive, SharePoint, or Frappe file uploads — not needed for Ask UCC itself, but this phase's document-search piece can't start without it. |
| **Moodle authentication method** | **BLOCKING the moment any module needs it** | CLAUDE.md's own §8.2 worked example ("What are his latest results?") uses Moodle grades. If Student Journey's tool set includes assessment results, this blocks that specific tool — the rest of the module doesn't need to wait on it. |
| **Approval level for automatic actions** | **BLOCKING for Phase 12 specifically** | Determines which of Levels 0-4 (read-only through prohibited) are even attempted first. Not needed for Ask UCC or memory, but blocks starting controlled actions. |
| **Jira integration credentials and permission scope** | **BLOCKING LATER** | Only matters if Phase 12's example action (create a Jira ticket) is in scope for a first version — Level 1 (draft-only) actions don't need it at all, so this can be deferred past Jira entirely for a first cut. |
| **Whether Zep is approved and which plan is available** | **BLOCKING LATER** | Deferred by §2's recommendation — not blocking now, but will block Phase 10 the moment it actually starts. |
| **Whether Graphiti infrastructure can be maintained** | **BLOCKING LATER** | Same as above — deferred alongside Zep, not currently blocking. |
| Installed Frappe/ERPNext version, hosting/deployment access | Not new to this phase | Environment-discovery items from Phase 1 — confirm these are already captured in `docs/environment-discovery.md`; if so, this phase inherits that answer rather than needing a fresh one. |
| Exact target repository name | Not this phase's concern | Resolved earlier in the migration (Phase 0/Epic A). |
| Which current Server Scripts are actually deployed | **Partially open** | Resolved for Analytics (all 7 criteria inventoried and ported). The three legacy Ask UCC scripts (`server-scripts/UCC Ask - Student Journey.py`, `- Recruitment Agent.py`, `- Quality Action.py`) exist in-repo and are readable without bench access — worth a proportionate inspection pass before finalizing §1's tool allowlists, the same "inspect deployed source before designing" discipline used for every Analytics criterion. Not a blocking *decision* so much as unstarted *inspection*. |
| Whether existing custom DocTypes may be converted into app-managed DocTypes | Not yet triggered | Only becomes relevant once `UCC AI Conversation` etc. are actually being created — no existing DocType obviously overlaps with them the way `ucc_dashboard_access` did for Analytics. |
| Whether external student/agent portals are in initial scope | Not this phase's concern | A scope question for a later expansion, not for building Ask UCC inside Desk. |

**Net read**: four items are genuinely blocking *right now* for any real Ask UCC build — AI provider
account, external-provider data policy, the Ask-UCC-specific role matrix, and retention periods.
Everything else either blocks a narrower slice (a specific tool, a specific action type) or is
correctly deferred by the memory recommendation above.
