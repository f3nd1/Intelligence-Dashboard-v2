# Environment Discovery Template

Blank template. **Nothing here is filled in** — no environment facts have been confirmed for this
migration, and none may be guessed. Fill this in against the real bench/site and commit it before
Phase 1 scaffolding is installed anywhere.

> **Format caveat.** Structure is unverified against the intended `CLAUDE.md` §20; the 13-phase spec
> is not present in this repository. See `migration/phase-1-plan.md` §7.

Rules for filling this in:

- Record the **command used** and its **actual output**, not a recollection.
- `UNKNOWN` is a valid and preferred answer. A guessed version is worse than a blank.
- No real student or staff data in this file — record counts and DocType names only, never rows.

---

## 1. Bench and platform

| Fact | Value | How obtained |
|---|---|---|
| Frappe version | | `bench version` |
| ERPNext version | | `bench version` |
| Other installed apps + versions | | `bench version` |
| Bench path | | |
| Python version | | `bench --site <site> console` → `sys.version` |
| Node version | | `node -v` |
| Database engine + version | | MariaDB / Postgres |
| Redis present | | |
| `developer_mode` enabled on the dev site | | `bench --site <site> get-config developer_mode` |

## 2. Sites

| Site | Purpose | Safe to install onto? | Notes |
|---|---|---|---|
| | production | **NO** | |
| | staging | | |
| | development | | |

## 3. Access

| Fact | Value |
|---|---|
| Access method (SSH / bench console / Frappe Cloud / Docker) | |
| Who can run `bench install-app` | |
| Who can create Server Scripts | |
| Can this agent run bench commands directly, or must a human execute them? | |
| Hosting model (self-hosted / Frappe Cloud / other managed) | |
| Deploy path for app code (git remote, branch, release process) | |

## 4. Current deployed state

| Fact | Value | How obtained |
|---|---|---|
| Custom HTML Block name/id hosting the platform | | |
| Custom HTML Block last-modified timestamp | | |
| Does the deployed JS match `custom-html-block/JAVASCRIPT.js` in this repo? | | sha256 of the field vs the file |
| Server Scripts present on the site (name → API method → enabled → Allow Guest) | | Server Script list view |
| Any Server Script on the site **not** in this repo | | |
| Any Server Script in this repo **not** on the site | | |
| `UCC Dashboard Access` DocType exists on site | | |
| `UCC Dashboard Access` row count and configured roles | | counts only, no data |

## 5. DocType availability

The seven criterion scripts reference **101 distinct candidate DocTypes**. Per-DocType availability
determines which metrics can ever be `available`.

| DocType | Installed? | Readable by the test user? | Row count (approx) | Notes |
|---|---|---|---|---|
| | | | | |

Fastest route: run `ucc_shared_diagnostics` per criterion and attach its output, rather than
enumerating by hand.

Confirmed mappings to re-verify explicitly (these are enforced by
`tools/validate_package.py` and must not regress):

| Purpose | Expected DocType | Present? |
|---|---|---|
| Staff goal analytics | `Goal` | |
| Training needs | `Training Needs Analysis` | |
| Communication material approval | `Material Vetting Form` | |
| Provider evaluation | `Provider Rating` | |
| Provider evaluation fallback (Criteria 3 and 6 only) | `Supplier Rating` | |

## 6. Roles and permissions

| Fact | Value |
|---|---|
| Roles that must see the platform | |
| Role intended to gate the Phase 1 workspace | |
| Test user WITH that role (non-production account) | |
| Test user WITHOUT that role (non-production account) | |
| Is there an approved role matrix document? Where? | |
| Does any UCC role rely on User Permissions / permission queries? | |

## 7. External services

| Service | Needed for | Account confirmed? | Credential location | PDPA/approval status |
|---|---|---|---|---|
| Zep (GetZep) | memory provider (selected, **not wired**) | | | |
| OpenAI | Ask UCC optional AI routing | | currently browser-supplied — must move | |
| Moodle | future | | | |
| Jira | future | | | |
| Google Drive | future | | | |

## 8. Data protection

| Fact | Value |
|---|---|
| PDPA approval obtained for sending UCC data to any external service? | |
| Retention period for conversation/memory data | |
| Retention period for diagnostic logs | |
| Approved data-residency constraints | |
| Who signs off on external data flows | |

## 9. Verification run at discovery time

Record the actual output of each, on the real site:

| Check | Command | Result |
|---|---|---|
| Static package validation | `python3 tools/validate_package.py` | expected baseline: 94/101, 7 known failures |
| Dashboard access self-check | `python3 tools/test_dashboard_access.py` | |
| Permission notice self-check | `node tools/test_permission_notice.js` | |
| Roll fallback self-check | `node tools/test_roll_fallback.js` | |
| Platform loads without console errors | manual | |
| All seven criteria selectable | manual | |
