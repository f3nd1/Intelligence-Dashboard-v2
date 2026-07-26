# UCC Intelligence Platform
## Master Claude Code Handover and Full Frappe App Migration Specification

**Document purpose:** This file is intended to be placed at the root of the duplicated GitHub repository and used as the primary `CLAUDE.md` instruction file for Claude Code.

**Original repository:** `f3nd1/Intelligence-Dashboard`

**Target repository:** A duplicated repository owned by UCC. Confirm its actual name before changing remote URLs, package names, CI configuration, deployment instructions, or badges.

**Organisation:** United Ceres College Pte Ltd, Singapore

**Target product name:** UCC Intelligence Platform

**Primary target environment:** UCC SMS running on Frappe/ERPNext

**Migration objective:** Replace the current deployment based on Frappe Custom HTML Blocks and Python Server Scripts with a proper installable Frappe app and module. Preserve the useful analytics and user experience, then extend the application into a secure institutional intelligence platform with analytics, Ask UCC, document knowledge, monitoring, and controlled AI-assisted workflows.

**Final-state rule:** The production implementation must not depend on the legacy Custom HTML Block or Server Script records. Legacy code may remain temporarily during migration and parity testing, but it must be removed from the final application branch after cutover. Preserve the original repository or a release tag as the historical fallback rather than shipping two competing implementations.

---

# 1. Instructions to Claude Code

Claude must treat this file as the authoritative project brief unless Felix explicitly overrides a point in the conversation.

## 1.1 Working behaviour

1. Inspect the repository before changing code.
2. Read both existing Analytics investigation reports before designing the migration:
   - `docs/investigation_analytics_report.md`
   - `docs/analytics_workspace_report_2.md`
3. Treat the deployed files as the current behavioural source of truth unless runtime evidence shows otherwise:
   - `custom-html-block/HTML.html`
   - `custom-html-block/CSS.css`
   - `custom-html-block/JAVASCRIPT.js`
   - `server-scripts/UCC Dashboard Access.py`
   - `server-scripts/UCC Analytics - Criterion 1.py` through `UCC Analytics - Criterion 7.py`
   - Ask UCC-related Server Scripts and frontend code found in the repository
4. Do not assume that `src/`, `dist/`, archived builds, prototypes, or old version folders match the deployed Custom HTML Block implementation. Compare them explicitly.
5. Do not begin by rewriting the interface from scratch.
6. Establish behavioural parity first, then improve architecture and features.
7. Make small, reviewable commits grouped by one purpose.
8. Do not perform unrelated formatting, renaming, dependency upgrades, or refactoring.
9. Do not expose OpenAI, Zep, database, Moodle, Jira, Google, or other credentials in browser code, repository files, fixtures, logs, screenshots, test snapshots, or documentation.
10. Do not use `ignore_permissions=True` merely to make a feature work. Permission bypasses require an explicit documented reason and approval.
11. Do not let the language model become the source of truth for grades, attendance, fees, contracts, compliance status, or other official records.
12. Every AI answer that uses institutional data must retain source traceability.
13. Every write action proposed by AI must be permission-checked and, initially, require explicit user confirmation.
14. Where the Frappe or ERPNext version affects implementation, inspect the deployed environment instead of guessing.
15. Before deleting any legacy path, confirm equivalent functionality using tests and an agreed parity checklist.

## 1.2 Required response format during implementation

For each substantial task, report:

1. **What was inspected**
2. **Assumptions made**
3. **Files changed**
4. **Behaviour changed**
5. **Verification performed**
6. **Known limitations or follow-up work**

## 1.3 Definition of a safe change

A change is acceptable only when:

- it is directly tied to an approved migration requirement;
- it preserves or intentionally changes documented behaviour;
- permission checks remain effective;
- test evidence exists;
- deployment and rollback implications are understood;
- no secret is introduced into Git;
- no production data is copied into fixtures or tests.

---

# 2. Product Vision

The UCC Intelligence Platform is not merely a chatbot and not merely a dashboard. It is a Frappe application inside UCC SMS that combines:

1. **Institutional analytics**
   - EduTrust GD4 Criterion 1 to Criterion 7 dashboards
   - data-source readiness
   - KPI and trend visualisations
   - exception and evidence views

2. **Ask UCC**
   - Student Journey assistant
   - Recruitment Agent assistant
   - Quality Action assistant
   - later modules for HR, courses, compliance, operations, and management

3. **Institutional knowledge**
   - policies
   - procedures
   - course documents
   - EduTrust, ISO, DPTM, and other compliance requirements
   - meeting decisions and approved organisational knowledge

4. **Operational monitoring**
   - data completeness checks
   - dummy or guide-text detection
   - missing evidence detection
   - overdue and unclosed records
   - scheduled departmental housekeeping

5. **Controlled agents and workflows**
   - draft a reminder
   - create a Jira or internal task after confirmation
   - prepare a Quality Action draft
   - prepare audit evidence lists
   - generate reports
   - route matters to process owners

6. **Institutional memory**
   - retain conversation context and approved organisational context across sessions
   - preserve relationships and historical decisions
   - never replace the authoritative operational systems

The product should feel like one UCC system even if its backend connects to several services.

---

# 3. Current Repository Baseline

## 3.1 Current deployment model

The current implementation is deployed through:

- one Frappe Custom HTML Block containing separate HTML, CSS, and JavaScript fields;
- Python Server Scripts exposed as Frappe API methods;
- direct `frappe.call` requests from browser JavaScript;
- live queries against ERPNext/Frappe DocTypes and query reports;
- browser state, local storage, and session storage for selected interface state and limited conversation context.

The deployment notes currently require replacing the three Custom HTML Block fields together, clearing cache, hard refreshing the page, and verifying that versions are aligned.

## 3.2 Current functional areas already present

The repository already contains more than data extraction. It includes:

- a multi-workspace shell;
- Criterion 1 to Criterion 7 analytics;
- a configurable chart engine;
- source mapping and diagnostics;
- role-aware interface composition through `ucc_dashboard_access`;
- permission-aware error presentation;
- an Ask UCC interface;
- Student Journey, Recruitment Agent, and Quality Action assistant modules;
- conversation history sent to backend methods;
- optional OpenAI interpretation in parts of the current Ask UCC implementation;
- CSV export, source links, record links, timelines, summaries, and tables.

## 3.3 Current Analytics architecture

The existing technical reports establish the following important facts:

1. The seven criterion dashboard containers are initially empty mount points in `custom-html-block/HTML.html`.
2. Most Analytics markup is generated dynamically by `custom-html-block/JAVASCRIPT.js`.
3. The frontend calls `ucc_dashboard_access` before mounting dashboards.
4. Criteria that the user may not access are removed from the DOM and from frontend configuration before mounting.
5. This interface gating is separate from Frappe data permissions. Backend methods still rely on normal Frappe permission checks.
6. Only the visible criterion is loaded initially. Other criteria are loaded when selected.
7. Each criterion calls its corresponding method, generally named `ucc_analytics_criterion_1` through `ucc_analytics_criterion_7`.
8. Requests are sent as a JSON string in an argument named `payload`.
9. The shared frontend normalises responses and renders KPIs, charts, management questions, source records, readiness information, and data quality.
10. The source-of-truth deployed implementation may differ from files in `src/` or `dist/`.

Claude must preserve these behaviours unless a migration decision explicitly changes them.

## 3.4 Current Ask UCC architecture

The existing frontend defines at least these modules:

| Module | Current API method | Primary record |
|---|---|---|
| Student Journey | `ucc_ask_student_journey` | Student Applicant or related student identity |
| Recruitment Agent | `ucc_ask_recruitment_agent` | Agent Contract |
| Quality Action | `ucc_ask_quality_action` | Quality Action |
| HR | Not yet implemented | Employee |

Current characteristics include:

- a record picker;
- recent records held in browser local storage;
- in-memory conversation history;
- the latest conversation subset sent with each request;
- live record retrieval from Frappe;
- source links back to ERPNext records;
- structured visuals such as summary cards, tables, and timelines;
- optional OpenAI key stored in browser session storage.

The browser API-key model is not acceptable for the final production application and must be replaced by server-side secrets and a controlled AI service layer.

## 3.5 Known current strengths to retain

- clear source visibility;
- direct links to ERPNext records;
- permission-aware behaviour;
- informative blocked-source messages;
- criterion-based navigation;
- dynamic charts and tables;
- lazy loading rather than loading every dashboard at once;
- fallback behaviour when a query report is blocked;
- separation between AI interpretation and ERPNext facts in user messaging;
- export and diagnostic capabilities.

## 3.6 Known weaknesses to remove

- oversized Custom HTML Block JavaScript;
- manual deployment by copy and paste;
- Server Scripts as production application logic;
- duplicated or diverging `src`, `dist`, and deployed files;
- hard-coded configuration mixed with rendering logic;
- browser-stored OpenAI key;
- limited persistent session storage;
- weak automated test coverage;
- difficult code ownership boundaries;
- no formal migration mechanism for application DocTypes and settings;
- no robust background-job architecture;
- no standard CI gate;
- no clean app installation and rollback path.

---

# 4. Target Technical Outcome

Create one installable Frappe app, proposed package name:

```text
ucc_intelligence
```

Proposed title:

```text
UCC Intelligence
```

The app must provide:

- a standard Frappe module;
- one or more Frappe Workspaces;
- proper Desk Pages;
- version-controlled Python APIs;
- app-managed DocTypes;
- app assets built by Frappe;
- scheduler and background-job support;
- fixtures only where appropriate;
- permissions and role controls;
- automated tests;
- migration patches;
- production deployment instructions;
- rollback instructions;
- observability and audit logging.

## 4.1 Final high-level architecture

```text
Users
  |
  +-- Staff through UCC SMS / Frappe Desk
  +-- Management through role-specific dashboards
  +-- Students through a later restricted portal
  +-- Agents through a later restricted portal
  |
UCC Intelligence Frappe App
  |
  +-- Analytics UI
  +-- Ask UCC UI
  +-- Knowledge UI
  +-- Monitoring UI
  +-- Agent and action UI
  |
Application Services
  |
  +-- Analytics services
  +-- Query and source services
  +-- AI orchestration service
  +-- Knowledge retrieval service
  +-- Conversation and memory service
  +-- Monitoring and rules service
  +-- Action approval service
  |
Authoritative Systems
  |
  +-- ERPNext / UCC SMS
  +-- Moodle
  +-- Google Drive or approved document repository
  +-- Jira or internal Frappe tasks
  +-- Gmail and Calendar where explicitly authorised
  |
Optional Context Services
  |
  +-- Zep managed context platform, or
  +-- Graphiti self-hosted temporal graph
```

## 4.2 One product, not one physical database

The user experience should be unified, but data must remain in the correct system of record.

| Information | Authoritative source |
|---|---|
| Student application and admission status | ERPNext/SMS |
| Attendance | ERPNext or Moodle, according to UCC's actual process |
| Assessment results | Moodle or the approved assessment record in ERPNext |
| Fees and payments | ERPNext/Finance records |
| Signed official documents | Approved document repository |
| Quality Actions | ERPNext Quality Action |
| Jira ticket status | Jira |
| Conversation context | UCC Intelligence database and/or approved memory service |
| Document retrieval index | Knowledge service/index |
| AI-generated explanation | Not an authoritative source |

---

# 5. Required Repository Strategy

## 5.1 Duplication approach

Felix will duplicate the original repository because the new product should not overwrite or retain the old implementation as the final production solution.

Recommended sequence:

1. Duplicate or fork `f3nd1/Intelligence-Dashboard` into a new private repository.
2. Protect the original repository as the historical baseline.
3. Create a tag in the duplicated repository before migration, for example:

```text
legacy-custom-html-baseline
```

4. Create a migration branch:

```text
migration/frappe-app
```

5. Place this file at the duplicated repository root as:

```text
CLAUDE.md
```

6. Do not delete the legacy directories immediately.
7. Keep them only until parity testing is complete.
8. Remove them from the final application branch before production cutover.
9. The historical tag and original repository provide rollback reference, so the final branch does not need to carry the legacy implementation.

## 5.2 Proposed branch model

```text
main
  Stable releasable application

develop
  Integrated development, optional if team size justifies it

migration/frappe-app
  Initial migration work

feature/<specific-feature>
  Short-lived focused branches

release/<version>
  Optional release stabilisation branch
```

For a small team, `main` plus short-lived feature branches is sufficient. Avoid process overhead that the team cannot maintain.

## 5.3 Commit standards

Examples:

```text
chore: scaffold ucc_intelligence Frappe app
feat: add role-aware Intelligence workspace
refactor: move criterion 1 API from Server Script
feat: migrate shared analytics renderer
fix: preserve blocked-source notice behaviour
security: move OpenAI key to site configuration
 test: add criterion API contract tests
 docs: add deployment and rollback runbook
```

Each commit should be independently understandable and should avoid mixing migration, redesign, and new AI functionality unless technically inseparable.

---

# 6. Environment Discovery Required Before Implementation

Claude must create an environment discovery report before choosing version-specific patterns.

## 6.1 Required environment facts

Confirm:

- Frappe version;
- ERPNext version;
- Python version;
- Node version;
- database type and version;
- bench topology;
- production hosting model;
- whether Frappe Cloud is used;
- access level available to Felix and the developer;
- whether SSH and bench access exist;
- whether the site is multi-tenant;
- current custom apps;
- current custom fields and fixtures;
- enabled Server Scripts;
- worker and scheduler status;
- current backup process;
- staging-site availability;
- release and rollback process;
- current user roles relevant to Analytics and Ask UCC;
- external network access permitted from workers;
- approved secret-management method.

## 6.2 Suggested discovery commands

Run only in an authorised development or staging environment:

```bash
bench version
bench --site <site> list-apps
bench --site <site> show-config
bench doctor
bench --site <site> scheduler status
node --version
python --version
```

Do not paste secret values from `site_config.json` or environment variables into chat, Git, issues, or this documentation.

## 6.3 Required discovery output

Create:

```text
docs/environment-discovery.md
```

Include:

- confirmed versions;
- available access;
- constraints;
- unresolved questions;
- chosen compatibility target;
- consequences for the app structure and frontend framework.

---

# 7. Target Repository Structure

The exact scaffold should be generated by the installed Frappe version. The following is the intended logical structure, not a licence to manually create an incompatible scaffold.

```text
.
├── CLAUDE.md
├── README.md
├── CHANGELOG.md
├── SECURITY.md
├── CONTRIBUTING.md
├── docs/
│   ├── architecture/
│   │   ├── system-context.md
│   │   ├── application-components.md
│   │   ├── data-flow.md
│   │   ├── permissions.md
│   │   ├── ai-boundaries.md
│   │   └── decisions/
│   ├── migration/
│   │   ├── legacy-inventory.md
│   │   ├── parity-matrix.md
│   │   ├── cutover-runbook.md
│   │   └── rollback-runbook.md
│   ├── api/
│   ├── operations/
│   └── user-guides/
├── ucc_intelligence/
│   ├── hooks.py
│   ├── modules.txt
│   ├── patches.txt
│   ├── public/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── fixtures/
│   ├── patches/
│   ├── templates/
│   ├── www/
│   └── ucc_intelligence/
│       ├── __init__.py
│       ├── api/
│       │   ├── analytics.py
│       │   ├── ask_ucc.py
│       │   ├── knowledge.py
│       │   ├── monitoring.py
│       │   └── actions.py
│       ├── analytics/
│       │   ├── contracts.py
│       │   ├── registry.py
│       │   ├── source_resolver.py
│       │   ├── metric_engine.py
│       │   ├── criterion_1.py
│       │   ├── criterion_2.py
│       │   ├── criterion_3.py
│       │   ├── criterion_4.py
│       │   ├── criterion_5.py
│       │   ├── criterion_6.py
│       │   └── criterion_7.py
│       ├── ask_ucc/
│       │   ├── contracts.py
│       │   ├── router.py
│       │   ├── student_journey.py
│       │   ├── recruitment_agent.py
│       │   ├── quality_action.py
│       │   └── hr.py
│       ├── ai/
│       │   ├── client.py
│       │   ├── orchestration.py
│       │   ├── prompts.py
│       │   ├── tools.py
│       │   ├── guardrails.py
│       │   └── usage.py
│       ├── knowledge/
│       │   ├── ingestion.py
│       │   ├── chunking.py
│       │   ├── retrieval.py
│       │   ├── citations.py
│       │   └── connectors.py
│       ├── memory/
│       │   ├── service.py
│       │   ├── local_store.py
│       │   ├── zep_adapter.py
│       │   └── graphiti_adapter.py
│       ├── monitoring/
│       │   ├── engine.py
│       │   ├── rule_registry.py
│       │   ├── evaluators.py
│       │   ├── scheduler.py
│       │   └── notifications.py
│       ├── integrations/
│       │   ├── moodle.py
│       │   ├── jira.py
│       │   ├── google_drive.py
│       │   └── openai.py
│       ├── permissions/
│       │   ├── access.py
│       │   └── scopes.py
│       ├── logging/
│       │   ├── audit.py
│       │   └── redaction.py
│       ├── doctype/
│       │   ├── ucc_intelligence_settings/
│       │   ├── ucc_ai_conversation/
│       │   ├── ucc_ai_message/
│       │   ├── ucc_knowledge_source/
│       │   ├── ucc_knowledge_sync_run/
│       │   ├── ucc_monitoring_rule/
│       │   ├── ucc_monitoring_run/
│       │   ├── ucc_monitoring_finding/
│       │   ├── ucc_ai_action_request/
│       │   ├── ucc_ai_usage_log/
│       │   └── ucc_dashboard_access/
│       ├── page/
│       │   ├── ucc_intelligence/
│       │   ├── ask_ucc/
│       │   ├── intelligence_knowledge/
│       │   └── intelligence_monitoring/
│       ├── workspace/
│       │   └── ucc_intelligence/
│       └── tests/
│           ├── test_analytics_contracts.py
│           ├── test_permissions.py
│           ├── test_ask_ucc.py
│           ├── test_monitoring.py
│           └── fixtures/
├── package.json
├── pyproject.toml
└── licence.txt
```

Do not create every file on day one. Build the minimum structure required by each migration phase.

---

# 8. Core Design Principles

## 8.1 Frappe-first integration

Use native Frappe capabilities where appropriate:

- module and workspace;
- Desk Page APIs;
- DocTypes;
- role permissions;
- whitelisted Python methods;
- background jobs;
- scheduler events;
- realtime events;
- Error Log and structured application logs;
- migrations and patches;
- fixtures for stable configuration only;
- test utilities.

Official references:

- Frappe app creation: https://docs.frappe.io/framework/user/en/tutorial/create-an-app
- Frappe hooks: https://docs.frappe.io/framework/user/en/python-api/hooks
- Frappe Desk Page API: https://docs.frappe.io/framework/user/en/api/page
- Frappe background jobs: https://docs.frappe.io/framework/user/en/api/background_jobs
- Frappe REST and whitelisted methods: https://docs.frappe.io/framework/user/en/api/rest
- Workspace access: https://docs.frappe.io/framework/user/en/desk/workspace/access

Confirm that each reference applies to the installed version.

## 8.2 Tool-first factual answers

For questions about current institutional records:

1. Resolve the user's identity and permissions.
2. Determine the relevant authoritative tool.
3. Query the authoritative system.
4. Return structured facts.
5. Optionally let the language model explain the facts.
6. Show sources.

Example:

```text
Question: What are his latest results?

Memory/context:
  "his" refers to Jabbary Reda

Authoritative query:
  Approved Moodle or ERPNext results integration

AI role:
  Explain the returned result clearly

Source shown:
  Assessment Result or Moodle grade record
```

The AI must not invent a result from memory.

## 8.3 Permission intersection

The answerable data set is the intersection of:

```text
User's Frappe permissions
AND module access
AND record-level access
AND external-system permissions
AND AI feature policy
```

The model must not broaden access. Retrieval services must execute as the authenticated user where possible, or apply an equivalent explicit permission scope.

## 8.4 Source traceability

Every result should distinguish:

- live ERPNext source;
- live external source;
- indexed document source;
- remembered conversational context;
- AI-generated interpretation;
- inference or uncertainty.

## 8.5 Progressive enhancement

The application must still provide useful deterministic analytics if the OpenAI service, memory service, or document index is unavailable.

Analytics and standard record retrieval must not become unnecessarily dependent on AI availability.

## 8.6 No premature single-provider lock-in

Define interfaces for:

- language model provider;
- embeddings provider;
- memory provider;
- document store;
- ticketing provider.

Initially implement only the approved provider. Avoid elaborate abstractions that have no current use, but keep external calls behind small service boundaries so credentials and vendors are not spread throughout the codebase.

---

# 9. Migration Phases

Each phase has a goal, required work, and exit criteria. Do not progress merely because code compiles. Meet the exit criteria.

## Phase 0: Repository and behavioural inventory

### Goal

Create a verified map of what exists before migration.

### Required work

- Read both existing Analytics technical reports.
- Inventory all files and directories.
- Identify deployed, generated, archived, experimental, and obsolete files.
- List all Server Script API methods.
- List all DocTypes and reports queried.
- List all frontend routes, workspaces, buttons, filters, tabs, and actions.
- List browser storage keys.
- List all role and permission logic.
- List external libraries and CDN dependencies.
- List OpenAI-related paths and current key handling.
- Identify all source contracts returned by server methods.
- Identify current production-specific assumptions.

### Deliverables

```text
docs/migration/legacy-inventory.md
docs/migration/parity-matrix.md
docs/architecture/current-state.md
```

### Exit criteria

- Every production feature has an owner file and test plan.
- Every Server Script has a migration destination.
- Every legacy UI action appears in the parity matrix.
- Unknowns are listed rather than guessed.

## Phase 1: Scaffold the Frappe app

### Goal

Create an installable empty app without changing current production behaviour.

### Required work

- Use `bench new-app ucc_intelligence` in a compatible bench.
- Confirm package metadata.
- Install it only on development or staging first.
- Add a basic module and role-restricted workspace.
- Add a simple health-check method.
- Establish linting and test commands appropriate to the environment.
- Document installation and uninstall procedures.

### Example commands

```bash
bench new-app ucc_intelligence
bench --site <staging-site> install-app ucc_intelligence
bench build --app ucc_intelligence
bench --site <staging-site> migrate
```

### Exit criteria

- App installs on a clean compatible site.
- App uninstalls without corrupting unrelated data.
- Workspace visibility follows roles.
- Health check works.
- CI or documented local checks run.

## Phase 2: Migrate access and shared runtime services

### Goal

Move shared permission and runtime logic before moving dashboards.

### Required work

- Migrate `ucc_dashboard_access` from Server Script to app Python.
- Preserve the current access DocType or replace it with an app-managed equivalent.
- Migrate shared error classification and blocked-source presentation.
- Establish common API response and error contracts.
- Add audit-safe logging and redaction.
- Create tests for role combinations and denied sources.

### Exit criteria

- Existing role behaviour is reproduced.
- Hidden criteria are not mounted or queried.
- Backend permissions remain authoritative.
- Permission errors do not reveal stack traces or sensitive details to ordinary users.
- Administrator diagnostics remain available in a controlled manner.

## Phase 3: Migrate Analytics frontend shell

### Goal

Replace the Custom HTML Block shell with a Frappe Desk Page while preserving the visual and navigation behaviour.

### Required work

- Create a proper Desk Page for UCC Intelligence.
- Move HTML construction into maintainable templates/components.
- Move CSS into app assets.
- Move JavaScript into app assets and modules.
- Preserve criterion selection, tab navigation, filters, loading states, readiness, diagnostics, and lazy loading.
- Preserve responsive behaviour.
- Remove reliance on `root_element`, which is specific to Custom HTML Blocks.
- Use Frappe page lifecycle correctly.
- Avoid global namespace pollution.

### Exit criteria

- All seven criterion shells render from the app.
- No Custom HTML Block is required for the staging version.
- Navigation and selected criterion persistence work.
- Hidden criteria are not available through direct UI manipulation.
- Desktop and supported mobile widths are visually checked.

## Phase 4: Migrate Criterion APIs one at a time

### Goal

Move the seven Analytics Server Scripts into version-controlled Python modules without changing result semantics.

### Migration order

Use the least complex representative criterion first, then proceed incrementally. Do not migrate all seven in one unreviewable change.

Suggested sequence:

1. Criterion 1 pilot
2. Criterion 3
3. Criterion 7
4. Criterion 2
5. Criterion 6
6. Criterion 4
7. Criterion 5

Adjust based on actual complexity discovered.

### Required work per criterion

- copy logic into an app module;
- remove Server Script assumptions such as `frappe.form_dict` where a clearer function signature is possible;
- retain a compatibility API during migration if needed;
- preserve normal Frappe permission enforcement;
- define typed or validated request payloads;
- define a stable response contract;
- add unit and integration tests;
- compare legacy and new responses using the same authorised test data;
- document known intentional differences.

### Proposed request contract

```json
{
  "action": "summary",
  "subcriterion": "5.1.1",
  "filters": {},
  "page_size": 100
}
```

### Proposed response contract

```json
{
  "ok": true,
  "meta": {
    "criterion": "5",
    "subcriterion": "5.1.1",
    "generated_at": "ISO-8601 timestamp",
    "data_version": "optional"
  },
  "metrics": [],
  "sources": [],
  "questions": [],
  "exceptions": [],
  "data_quality": [],
  "source_summary": {},
  "metric_summary": {},
  "warnings": []
}
```

### Exit criteria per criterion

- API contract test passes.
- Legacy-versus-new parity test is signed off.
- Permission tests pass.
- Frontend rendering matches expected behaviour.
- No production-only field name is silently assumed.
- Diagnostics identify missing DocTypes or field mismatches clearly.

## Phase 5: Consolidate Analytics configuration

### Goal

Replace scattered hard-coded registries with one maintainable configuration model without overengineering.

### Required work

Separate:

- criterion metadata;
- subcriterion metadata;
- source definitions;
- metric definitions;
- chart definitions;
- management questions;
- filter definitions;
- permissions.

Prefer version-controlled Python or JSON for stable product configuration. Use DocTypes only where UCC genuinely needs authorised runtime editing.

### Rule

Do not put all configuration into database records merely because Frappe supports DocTypes. Version-controlled configuration is easier to review and test. Use runtime DocTypes for settings that administrators should change without a deployment.

### Exit criteria

- A developer can locate a metric and its source without searching one huge JavaScript file.
- A chart can be added without editing unrelated rendering code.
- Configuration validation catches duplicate IDs and invalid subcriteria.
- Criterion 4 and 5 special cases are explicit and tested.

## Phase 6: Migrate Ask UCC frontend and deterministic retrieval

### Goal

Move Ask UCC into the app while initially preserving its deterministic ERPNext retrieval behaviour.

### Required work

- create a dedicated Desk Page or integrated workspace panel;
- migrate module selector;
- migrate record picker and recent-record behaviour;
- migrate structured response rendering;
- migrate source links;
- migrate CSV export and print support;
- migrate Student Journey API;
- migrate Recruitment Agent API;
- migrate Quality Action API;
- preserve partial-access fallbacks;
- replace browser-only conversation state with an app conversation service;
- keep AI optional until server-side integration is ready.

### Exit criteria

- Each implemented module works without an OpenAI key.
- Facts come from live authorised records.
- Follow-up context works within a conversation.
- Sources open the correct records.
- Blocked sources are explained without leaking data.

## Phase 7: Add application DocTypes and settings

### Goal

Provide durable configuration, conversations, monitoring, and audit records.

### 7.1 `UCC Intelligence Settings`

Recommended as a Single DocType.

Possible fields:

- enable AI;
- approved model provider;
- approved model name;
- maximum model output tokens;
- default temperature, normally low for institutional answers;
- AI request timeout;
- enable persistent conversations;
- enable document knowledge;
- enable monitoring;
- require confirmation for write actions;
- retention periods;
- external integration toggles;
- default source-display policy.

Do not store raw provider secrets in ordinary readable fields unless Frappe's password field and access controls are confirmed suitable. Prefer site configuration or the approved secret manager.

### 7.2 `UCC AI Conversation`

Suggested fields:

- conversation title;
- user;
- module;
- linked DocType;
- linked document name;
- status;
- created time;
- last activity;
- retention category;
- external memory reference, optional;
- archived flag.

### 7.3 `UCC AI Message`

Suggested fields:

- parent conversation;
- role;
- content or protected content reference;
- source summary;
- model name;
- tool calls;
- latency;
- token usage;
- safety status;
- created time.

Consider whether messages should be a child table or independent DocType based on expected volume, query needs, and retention. Do not choose silently.

### 7.4 `UCC Knowledge Source`

Suggested fields:

- title;
- source type;
- source URL or File reference;
- owner department;
- document classification;
- effective date;
- review date;
- current version;
- active status;
- permission scope;
- checksum;
- sync status;
- last indexed time;
- superseded-by reference.

### 7.5 Monitoring DocTypes

- `UCC Monitoring Rule`
- `UCC Monitoring Run`
- `UCC Monitoring Finding`

### 7.6 Action DocType

`UCC AI Action Request` should capture:

- proposed action;
- target system;
- target record;
- proposed payload;
- reason;
- sources;
- requested by;
- approval status;
- approved by;
- execution status;
- execution result;
- rollback information;
- audit timestamps.

### Exit criteria

- DocTypes install and migrate cleanly.
- permissions are tested;
- sensitive fields are protected;
- records have retention rules;
- no operational data is duplicated without a clear purpose.

## Phase 8: Secure server-side OpenAI integration

### Goal

Add AI interpretation without exposing credentials or weakening factual controls.

### Required work

- remove browser OpenAI-key entry from production UI;
- store credentials in an approved server-side secret location;
- create one AI client service;
- set timeouts and retry limits;
- log request metadata without logging sensitive full prompts by default;
- add usage and cost controls;
- allow AI to call only approved internal tools;
- validate structured model outputs;
- protect against prompt injection from documents and user input;
- clearly label AI-generated explanations;
- provide deterministic fallback when AI is unavailable.

### Required AI flow

```text
User question
  -> permission and module scope
  -> context resolution
  -> approved tool selection
  -> live data retrieval
  -> source packaging
  -> model explanation
  -> output validation
  -> source rendering
  -> audit metadata
```

### AI must not

- query arbitrary DocTypes supplied by the user;
- execute arbitrary SQL;
- accept a user-provided method path;
- reveal hidden fields;
- fabricate source links;
- change records without approval;
- place private data into external memory without policy approval;
- use document instructions as system instructions.

### Exit criteria

- no API key appears in browser storage or network request arguments from the client;
- tool permissions are tested;
- model outage fallback is tested;
- prompt injection tests exist;
- source attribution is present;
- usage logs exist without exposing unnecessary personal data.

## Phase 9: Institutional knowledge and document retrieval

### Goal

Add trusted document retrieval for policies, SOPs, courses, EduTrust, ISO, DPTM, meeting decisions, and approved institutional documents.

### Architectural decision

Do not automatically assume Zep or Graphiti should replace conventional document retrieval. Document retrieval needs exact source segments, document versions, metadata, and citations. Memory and temporal graphs solve related but different problems.

Recommended logical services:

```text
Knowledge ingestion
  -> extract text
  -> identify document and version
  -> split by meaningful section
  -> retain page/heading/source metadata
  -> index for retrieval
  -> optionally add entities/relationships to context graph
```

### Minimum knowledge features

- source registration;
- version handling;
- effective and superseded dates;
- section-level retrieval;
- permission filtering;
- citations;
- sync status;
- stale-index detection;
- deletion and re-indexing;
- test queries with expected sources.

### Source priority

For compliance or policy answers, prefer:

1. current approved UCC document;
2. current official regulatory source if integrated;
3. current approved procedure;
4. historical version only when explicitly requested.

### Exit criteria

- answers show the source document and section;
- superseded documents are not presented as current;
- restricted documents are not retrieved for unauthorised users;
- document deletion and replacement propagate to the index;
- evaluation set meets agreed retrieval quality.

## Phase 10: Memory and temporal context

### Goal

Add long-term context where it improves continuity, without treating memory as the official record.

### Provider decision

Support one of the following after a documented decision:

- Zep as a managed context platform;
- Graphiti as a self-hosted temporal graph framework;
- local Frappe conversation storage for the initial version.

Do not add Zep or Graphiti merely because it is interesting. Add it only when a concrete use case cannot be handled adequately by local conversation storage and document retrieval.

### Suitable memory content

- current conversation subject;
- user preferences relevant to interface behaviour;
- previous approved decisions;
- relationships between projects, roles, and records;
- historical organisational context;
- references to official source records.

### Unsuitable memory as authoritative fact

- latest grades;
- latest attendance;
- account balances;
- current fees;
- current contract status;
- current regulatory status;
- current task status.

Those must be re-queried.

### Required controls

- user-scoped and shared institutional memory separation;
- permission-aware retrieval;
- retention and deletion;
- source references;
- valid-time and recorded-time handling if temporal graphs are used;
- no silent cross-user leakage;
- provider outage fallback;
- clear sync boundaries.

### Exit criteria

- follow-up pronouns and references work across approved sessions;
- memory cannot override a current official record;
- deletion requests can be fulfilled;
- cross-user isolation is tested;
- external provider data handling is approved.

## Phase 11: Monitoring and housekeeping

### Goal

Implement scheduled, deterministic monitoring before allowing autonomous AI actions.

### Initial monitoring use cases

1. Student Log can be completed or closed only when student background is filled.
2. Student Log content must not contain guide or dummy text.
3. Required approval fields must be present before closure.
4. Quality Actions must have owners, due dates, actions, evidence, and closure verification.
5. Course review and development records must contain required evidence.
6. Expiring contracts and documents must be flagged.
7. Records required by the QA calendar must be checked quarterly.
8. Departmental housekeeping summaries must be generated.

### Monitoring design

A monitoring rule must define:

- rule ID;
- title;
- purpose;
- target DocType;
- target population filter;
- fields required;
- evaluation function;
- severity;
- responsible role or owner resolver;
- schedule;
- suppression or exception policy;
- evidence output;
- remediation guidance;
- effective date;
- version.

### Execution flow

```text
Scheduler
  -> enqueue monitoring run
  -> resolve active rules
  -> query authorised target records
  -> evaluate deterministic rules
  -> store findings
  -> deduplicate open findings
  -> prepare department summary
  -> notify or propose actions
```

AI may summarise findings, but the pass/fail decision should remain deterministic where possible.

### Exit criteria

- rerunning a rule is idempotent;
- duplicate findings are controlled;
- false-positive suppression is auditable;
- rule versions are traceable;
- scheduled jobs do not block web workers;
- department permissions are honoured;
- management summary links to exact records.

## Phase 12: Controlled actions and agents

### Goal

Allow the platform to propose and execute tightly controlled actions.

### Initial action levels

| Level | Behaviour | Example |
|---|---|---|
| 0 | Read only | Explain missing evidence |
| 1 | Draft only | Draft reminder text |
| 2 | Confirm before execution | Create Jira ticket after user confirms |
| 3 | Policy-approved automatic action | Send scheduled low-risk reminder |
| 4 | Prohibited initially | Automatically change grades or financial records |

### Required controls

- action allowlist;
- permission recheck at execution time;
- confirmation for Level 2;
- audit record;
- idempotency key;
- result capture;
- failure handling;
- retry policy;
- rollback or compensating action where possible;
- no hidden background write initiated only from model prose.

### Exit criteria

- unapproved action cannot execute;
- repeated clicks do not create duplicate tickets;
- executed action records who approved it;
- failure is visible and recoverable;
- action scope is tested against roles.

## Phase 13: Cutover and legacy removal

### Goal

Make the Frappe app the sole production implementation.

### Required work

- complete the parity matrix;
- run staging user acceptance tests;
- back up the site and code;
- tag the last pre-cutover app release;
- install and migrate the app in production;
- switch navigation to the app workspace;
- disable the legacy Custom HTML Block;
- disable legacy Server Scripts;
- monitor logs and user reports;
- remove legacy directories from the final branch after the agreed stabilisation period;
- retain historical tags and original repository for reference;
- update operating documentation.

### Exit criteria

- no live page references the legacy Custom HTML Block;
- no browser call invokes a legacy Server Script method;
- app installation is documented;
- rollback is tested or rehearsed;
- production monitoring is active;
- legacy code is absent from the final main branch, except documented migration records where necessary.

---

# 10. UI and Information Architecture

## 10.1 Main workspace

Proposed navigation:

```text
UCC Intelligence
├── Overview
├── Analytics
│   ├── Criterion 1
│   ├── Criterion 2
│   ├── Criterion 3
│   ├── Criterion 4
│   ├── Criterion 5
│   ├── Criterion 6
│   └── Criterion 7
├── Ask UCC
├── Student Journey
├── Recruitment Agents
├── Quality Actions
├── Knowledge
├── Monitoring
├── Findings and Alerts
├── Action Requests
├── Reports
└── Administration
```

Role visibility must control what is shown. Hiding navigation is not a substitute for data permission checks.

## 10.2 Overview screen

The overview should combine:

- priority alerts;
- pending actions;
- compliance readiness;
- student risks, if the user may see them;
- recent monitoring runs;
- failed integrations;
- AI service health;
- recent activity;
- shortcuts to Ask UCC and Analytics.

Do not overload the initial release. Use existing dashboard design language and add only verified, actionable cards.

## 10.3 Ask UCC screen

Required interface elements:

- module selector;
- record context picker;
- current context badge;
- guided questions;
- free-text question box;
- response area;
- source links;
- confidence or limitation note where meaningful;
- warnings;
- action buttons only when authorised;
- conversation history;
- reset context;
- export and print where appropriate.

## 10.4 Contextual assistant on records

Later, add a side panel or action menu on selected DocTypes, for example:

- Student Applicant;
- Student;
- Quality Action;
- Agent Contract;
- Course Review;
- Monitoring Finding.

The panel should receive the open record as context rather than requiring the user to search again.

## 10.5 Accessibility and usability

- keyboard navigation;
- visible focus states;
- semantic buttons and labels;
- adequate contrast;
- table alternatives for charts;
- loading and error announcements;
- no reliance on colour alone;
- responsive design;
- supported browser policy documented.

---

# 11. API and Contract Standards

## 11.1 Whitelisted methods

Use a small public API surface. Public means callable by authorised logged-in clients, not anonymous.

Suggested endpoints:

```text
ucc_intelligence.api.analytics.get_dashboard_access
ucc_intelligence.api.analytics.get_criterion_summary
ucc_intelligence.api.ask_ucc.ask
ucc_intelligence.api.ask_ucc.get_modules
ucc_intelligence.api.ask_ucc.search_context_records
ucc_intelligence.api.knowledge.search
ucc_intelligence.api.monitoring.run_rule
ucc_intelligence.api.monitoring.get_findings
ucc_intelligence.api.actions.propose
ucc_intelligence.api.actions.approve
ucc_intelligence.api.actions.execute
```

Do not expose one method per internal helper. Keep internal functions internal.

## 11.2 Input validation

Validate:

- allowed module;
- allowed criterion;
- allowed subcriterion;
- filter keys;
- filter value types;
- page sizes and maximums;
- linked DocType allowlist;
- linked document access;
- question length;
- attachment type and size;
- action type;
- target record;
- idempotency key.

## 11.3 Error contract

Return safe user-facing errors with a diagnostic reference.

Example:

```json
{
  "ok": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "This source is not available to your account.",
    "source": "Assessment Result",
    "diagnostic_id": "UCC-ERR-..."
  }
}
```

Do not expose stack traces to ordinary users.

## 11.4 Pagination

Any API returning records must enforce a maximum page size and stable ordering. Do not return thousands of records to the browser merely because the existing prototype did so.

## 11.5 Caching

Cache only where correctness is preserved.

Potential cache keys:

- user;
- role set or permission scope;
- criterion;
- subcriterion;
- filters;
- data version;
- configuration version.

Never share a cache entry across users if row-level permissions could differ.

---

# 12. Security and Data Protection Requirements

UCC handles student, staff, agent, academic, and operational data. Treat this as sensitive institutional information.

## 12.1 Secrets

- no secrets in Git;
- no secrets in frontend JavaScript;
- no secrets in query parameters;
- no secrets in screenshots;
- no secrets in fixtures;
- rotate any key that was previously exposed;
- document the approved storage and rotation process.

## 12.2 Personal data minimisation

Send only the information required for the current task to an external model or memory service.

Where possible:

- use IDs rather than unnecessary full profiles;
- omit contact information unless required;
- redact government identifiers;
- avoid sending entire records when selected fields suffice;
- apply retention controls;
- log metadata rather than full content.

## 12.3 Prompt injection controls

Treat retrieved documents, emails, notes, and user-entered text as untrusted data.

- separate system instructions from retrieved content;
- mark retrieved content as data;
- ignore instructions found inside documents;
- restrict tools by allowlist;
- validate model-proposed tool arguments;
- require permissions independently of the model;
- test malicious document content.

## 12.4 Audit trail

Log at minimum:

- user;
- feature/module;
- time;
- linked record context;
- tools called;
- source IDs;
- model/provider;
- action proposed;
- approval;
- execution result;
- error reference.

Balance audit needs with data minimisation. Do not log full sensitive payloads by default.

## 12.5 Data residency and provider review

Before sending personal or regulated information to OpenAI, Zep, or any other provider, UCC must confirm the approved account, contractual terms, retention settings, data-processing terms, and internal PDPA requirements.

Claude should implement technical controls but must not claim that provider use is legally approved unless UCC has confirmed it.

---

# 13. Testing Strategy

## 13.1 Test layers

1. **Pure unit tests**
   - payload validation;
   - metric calculations;
   - rule evaluators;
   - response adaptation;
   - source mapping;
   - redaction.

2. **Frappe integration tests**
   - DocType queries;
   - role permissions;
   - whitelisted methods;
   - background jobs;
   - patches and fixtures.

3. **Contract tests**
   - old versus new Analytics responses;
   - Ask UCC structured result shape;
   - source-link format;
   - external connector adapters.

4. **Frontend tests**
   - navigation;
   - lazy loading;
   - chart/table toggle;
   - denied-source state;
   - record context;
   - source rendering;
   - action confirmation.

5. **Security tests**
   - cross-role access;
   - direct endpoint access;
   - prompt injection;
   - invalid DocType or field request;
   - oversized payload;
   - duplicate action execution;
   - secret leakage.

6. **User acceptance tests**
   - Principal/Management;
   - Quality;
   - Academic;
   - Student Services;
   - restricted user;
   - administrator.

## 13.2 Parity testing

For each legacy function, document:

| Feature | Legacy result | App result | Status | Approved difference |
|---|---|---|---|---|
| Criterion 1 initial load | | | | |
| Criterion access by role | | | | |
| Source link | | | | |
| Blocked source | | | | |
| Student search | | | | |
| Journey timeline | | | | |
| Quality Action answer | | | | |

## 13.3 Test data rules

- use synthetic or approved anonymised data;
- never commit production exports;
- avoid real names, emails, phone numbers, IDs, grades, or financial data;
- document how staging test data is produced.

## 13.4 Performance targets

Agree actual targets after measuring the current system. Initial suggested targets:

- initial workspace shell: interactive within 2 seconds on normal UCC office connectivity, excluding slow external dependencies;
- criterion API: target under 3 seconds for normal requests;
- record search: target under 1.5 seconds;
- AI response: progressive loading state, with deterministic facts retrieved before explanation where feasible;
- monitoring jobs: run in workers, never block web requests;
- no page should load all seven full criterion data sets on initial entry.

These are starting targets, not guaranteed commitments. Record baseline measurements first.

---

# 14. Observability and Operations

## 14.1 Health checks

Track:

- app version;
- database connectivity;
- scheduler enabled;
- worker availability;
- OpenAI configuration, without exposing the key;
- knowledge index status;
- memory-provider status;
- Moodle/Jira/Drive connector status;
- last successful monitoring run;
- failed job count.

## 14.2 Logging

Use structured logs where possible. Include a request or diagnostic ID.

Log levels:

- DEBUG: development detail, disabled or reduced in production;
- INFO: successful high-level operations;
- WARNING: degraded but recoverable behaviour;
- ERROR: failed requests or jobs;
- SECURITY: denied actions, suspicious tool requests, or repeated invalid access.

## 14.3 Failure behaviour

| Failure | Required behaviour |
|---|---|
| OpenAI unavailable | Show deterministic data and state that interpretation is unavailable |
| Memory provider unavailable | Continue current-session conversation where possible |
| Knowledge index unavailable | Do not invent a policy answer, show source search unavailable |
| Moodle unavailable | State that current results cannot be confirmed |
| One criterion source blocked | Show blocked-source notice and any authorised partial data |
| Background job fails | Store run failure and alert administrator/process owner |
| Chart fails | Show table or error state, not a blank card |

---

# 15. Deployment and Release

## 15.1 Development

Use a dedicated bench and site. Do not develop directly on production.

Typical workflow:

```bash
bench start
bench watch
bench --site <dev-site> migrate
bench --site <dev-site> run-tests --app ucc_intelligence
```

Confirm exact commands for the installed Frappe version.

## 15.2 Staging

Staging must contain:

- representative configuration;
- synthetic or approved masked data;
- representative roles;
- workers and scheduler;
- the same external integration restrictions as production where possible.

## 15.3 Production deployment outline

```bash
cd <bench>
git status
bench --site <site> backup
bench get-app <repository-url> --branch <release-branch>   # first installation only
bench --site <site> install-app ucc_intelligence          # first installation only
bench setup requirements
bench build --app ucc_intelligence
bench --site <site> migrate
bench restart
bench doctor
```

The hosting environment may use a different deployment mechanism. Document the actual runbook after environment discovery.

## 15.4 Rollback

Rollback planning must cover:

- code rollback to prior release tag;
- database migration consequences;
- disabling new workspace routes;
- re-enabling legacy implementation temporarily if still within migration window;
- restoring backup when necessary;
- external action reconciliation;
- knowledge-index compatibility.

Never promise that a Git revert alone can reverse a database migration.

## 15.5 Versioning

Use semantic versioning where practical:

```text
0.x  Migration and pre-production
1.0  Full app parity and production cutover
1.1  Secure AI interpretation
1.2  Institutional knowledge
1.3  Monitoring
1.4  Controlled actions
```

Actual releases should be based on completed functionality, not the example numbering.

---

# 16. Legacy Removal Checklist

Before deleting `custom-html-block/` and `server-scripts/` from the final branch, confirm:

- [ ] UCC Intelligence workspace exists.
- [ ] all seven criteria render.
- [ ] access gating matches approved roles.
- [ ] all seven criterion APIs have migrated.
- [ ] source links work.
- [ ] blocked-source states work.
- [ ] diagnostics work.
- [ ] Ask UCC Student Journey works.
- [ ] Ask UCC Recruitment Agent works.
- [ ] Ask UCC Quality Action works.
- [ ] browser OpenAI-key entry is removed.
- [ ] app settings and secrets are configured.
- [ ] background jobs are operational.
- [ ] automated tests pass.
- [ ] UAT is signed off.
- [ ] cutover and rollback runbooks are approved.
- [ ] production backup exists.
- [ ] original repository or legacy tag remains available.
- [ ] no active route or workspace references the Custom HTML Block.
- [ ] no frontend call invokes legacy Server Script methods.
- [ ] legacy Server Script records are disabled or removed from production.

Only then remove legacy code from the final branch.

---

# 17. Initial Backlog

## Epic A: Foundation

- A1 Duplicate repository and tag baseline
- A2 Add `CLAUDE.md`
- A3 Complete environment discovery
- A4 Complete legacy inventory
- A5 Create parity matrix
- A6 Scaffold Frappe app
- A7 Add CI and test commands

## Epic B: Security and access

- B1 Migrate dashboard access API
- B2 Define app roles
- B3 Test role combinations
- B4 Add safe error contract
- B5 Add audit-safe logging
- B6 Remove client-side secret handling

## Epic C: Analytics migration

- C1 Migrate Desk shell
- C2 Migrate shared chart engine
- C3 Migrate Criterion 1
- C4 Migrate Criterion 2
- C5 Migrate Criterion 3
- C6 Migrate Criterion 4
- C7 Migrate Criterion 5
- C8 Migrate Criterion 6
- C9 Migrate Criterion 7
- C10 Complete parity tests

## Epic D: Ask UCC migration

- D1 Migrate conversation interface
- D2 Migrate context picker
- D3 Migrate Student Journey
- D4 Migrate Recruitment Agent
- D5 Migrate Quality Action
- D6 Add persistent conversations
- D7 Add HR module only after requirements are defined

## Epic E: AI

- E1 Add server-side provider settings
- E2 Implement OpenAI client
- E3 Implement tool router
- E4 Add structured output validation
- E5 Add citations and sources
- E6 Add usage logging
- E7 Add prompt-injection tests
- E8 Add deterministic fallback

## Epic F: Knowledge

- F1 Define approved source types
- F2 Create Knowledge Source DocType
- F3 Implement extraction and chunking
- F4 Implement permissions and versioning
- F5 Implement retrieval
- F6 Implement source citations
- F7 Build evaluation set

## Epic G: Memory

- G1 Define memory use cases
- G2 Decide local, Zep, or Graphiti
- G3 Implement provider interface
- G4 Add user and institutional memory separation
- G5 Add retention and deletion
- G6 Test cross-user isolation

## Epic H: Monitoring

- H1 Create monitoring DocTypes
- H2 Implement rule engine
- H3 Implement Student Log completeness rules
- H4 Implement dummy-text rules
- H5 Implement Quality Action closure rules
- H6 Add scheduled runs
- H7 Add departmental summaries
- H8 Add deduplication and suppression

## Epic I: Controlled actions

- I1 Create Action Request DocType
- I2 Implement draft-only actions
- I3 Add confirmation workflow
- I4 Add Jira integration
- I5 Add reminders
- I6 Add idempotency and audit

## Epic J: Cutover

- J1 Staging UAT
- J2 Performance testing
- J3 Security review
- J4 Production backup
- J5 Production installation
- J6 Disable legacy deployment
- J7 Stabilisation monitoring
- J8 Remove legacy directories from final branch
- J9 Release 1.0 documentation

---

# 18. Decisions That Must Be Recorded

Create Architecture Decision Records under:

```text
docs/architecture/decisions/
```

Minimum decisions:

1. Supported Frappe and ERPNext version
2. Frontend approach for Desk Pages
3. Analytics configuration storage
4. Conversation storage design
5. OpenAI secret storage
6. Document retrieval technology
7. Zep versus Graphiti versus local memory
8. Moodle integration method
9. Jira versus internal Frappe tasking
10. Logging and retention policy
11. Deployment and rollback model
12. Legacy cutover date and removal criteria

ADR template:

```markdown
# ADR-NNN: Decision title

## Status
Proposed / Accepted / Superseded

## Context
What problem requires a decision?

## Options considered
1. Option A
2. Option B
3. Option C

## Decision
What was selected?

## Rationale
Why was it selected?

## Consequences
Positive, negative, operational, security, and migration effects.

## Revisit triggers
What future event would justify reconsidering it?
```

---

# 19. Questions Claude Must Not Decide Silently

Claude should surface these when they become material, but continue other non-blocked work:

- exact target repository name;
- installed Frappe and ERPNext version;
- hosting and deployment access;
- approved AI provider account;
- whether student personal data may be sent to an external provider;
- whether Zep is approved and which plan is available;
- whether Graphiti infrastructure can be maintained;
- document repository of record;
- Moodle authentication method;
- Jira integration credentials and permission scope;
- retention periods;
- UCC role matrix;
- approval level for automatic actions;
- which current Server Scripts are actually deployed;
- whether existing custom DocTypes may be converted into app-managed DocTypes;
- whether external student and agent portals are in the initial scope.

For minor ambiguities, choose the safest reversible option and document it.

---

# 20. Immediate First Task for Claude Code

When Claude first opens the duplicated repository, it should not immediately scaffold or delete files. It should perform this sequence:

## Step 1: Confirm repository state

```bash
git status
git branch --show-current
git log -5 --oneline
find . -maxdepth 3 -type f | sort
```

## Step 2: Read the technical baseline

Read:

```text
CLAUDE.md
README.md
custom-html-block/DEPLOYMENT_NOTES.md
custom-html-block/HTML.html
custom-html-block/CSS.css
custom-html-block/JAVASCRIPT.js
docs/investigation_analytics_report.md
docs/analytics_workspace_report_2.md
server-scripts/UCC Dashboard Access.py
server-scripts/UCC Analytics - Criterion 1.py
...
server-scripts/UCC Analytics - Criterion 7.py
```

Then locate and read all Ask UCC Server Scripts.

## Step 3: Produce, but do not yet execute, the first implementation plan

Create:

```text
docs/migration/legacy-inventory.md
docs/migration/parity-matrix.md
docs/environment-discovery-template.md
docs/migration/phase-1-plan.md
```

The Phase 1 plan must identify:

- exact files to add;
- exact files to leave untouched;
- bench commands required;
- environment information still missing;
- tests to run;
- rollback for the phase;
- acceptance criteria.

## Step 4: Wait only for genuinely blocking environment input

Do not ask Felix to restate information already present in the repository or this file. Continue all repository-only analysis while environment access is being arranged.

---

# 21. Suggested First Claude Prompt

Felix may use the following prompt after placing this file in the duplicated repository:

```text
Read CLAUDE.md in full, then inspect the entire repository without changing any code.

Start with the two Analytics technical reports and verify their key claims against the deployed source-of-truth files in custom-html-block/ and server-scripts/. Also identify every Ask UCC Server Script and frontend entry point.

Create the Phase 0 deliverables required by CLAUDE.md:
1. docs/migration/legacy-inventory.md
2. docs/migration/parity-matrix.md
3. docs/architecture/current-state.md
4. docs/environment-discovery-template.md

Do not scaffold the Frappe app and do not delete or refactor the legacy implementation yet. Where the reports disagree, inspect the current files and document the verified result. Finish with the smallest safe Phase 1 implementation plan and list only genuinely blocking environment information.
```

---

# 22. Completion Definition for the Overall Programme

The migration is complete when:

1. UCC Intelligence is installed as a proper Frappe app.
2. Staff access it through a role-aware UCC Intelligence workspace inside SMS.
3. Criterion 1 to Criterion 7 Analytics are migrated and validated.
4. Existing useful charts, tables, filters, source links, readiness views, and diagnostics are preserved or deliberately improved.
5. Ask UCC Student Journey, Recruitment Agent, and Quality Action modules operate from app code.
6. OpenAI credentials are entirely server-side.
7. AI uses approved tools and displays sources.
8. Deterministic features continue to work when AI is unavailable.
9. Institutional document retrieval is permission-aware and version-aware.
10. Any memory service is subordinate to official data sources.
11. Monitoring jobs run through workers and produce auditable findings.
12. Write actions are controlled, confirmed, permission-checked, and logged.
13. Automated tests cover contracts, permissions, and critical flows.
14. Deployment, rollback, and operations are documented.
15. The production site no longer depends on Custom HTML Blocks or Server Scripts for this product.
16. The final main branch no longer contains the legacy implementation, apart from migration documentation where useful.
17. The original repository or a legacy tag preserves the historical baseline.

---

# 23. Final Direction

Build the new UCC Intelligence Platform as an evolution of the proven dashboard behaviour, not as an unrelated greenfield design.

The migration priority is:

```text
Understand
  -> preserve behaviour
  -> move into a proper Frappe app
  -> secure permissions and secrets
  -> validate parity
  -> add AI interpretation
  -> add institutional knowledge
  -> add memory where justified
  -> add deterministic monitoring
  -> add controlled actions
  -> remove the legacy implementation
```

Do not reverse this order by adding an impressive AI layer on top of unstable, untested, or insecure data access.
