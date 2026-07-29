# Frappe Insights single-chart pilot — findings

**Status as of 2026-07-28: pilot complete.** Query, Chart, and Dashboard all
built and verified against real live data on `ucc-sms-v2.orb.local`. §4(b)
(permissions) has a definitive, tested result — see §6 for the recommendation.
§4(a) (filters) was never actually run — flagged explicitly in that section
rather than left ambiguous. §7 (full 106-chart classification) is repo-only
work, done and complete.

This is a feasibility spike, not a migration. Nothing here removes or
replaces an existing renderer, and nothing here decides the long-term
rendering direction — that call is Felix's, per §6.

I had no live bench/browser access in this session throughout — every result
in §§1-4 that needed one came from Felix running commands and reporting back
verbatim, not from anything fabricated here. §3's build log is long because
getting to a working pilot took real, sequential debugging (six distinct
issues found and fixed, one symptom resolved without a fully confirmed root
cause — see §6's reliability caveat) rather than working on the first try;
left in full rather than cleaned up after the fact, since the debugging path
itself is part of what this pilot demonstrates about working with Insights
v3.

---

## 1. The `ibis` error — diagnosis, not yet fixed

**Symptom reported:** `bench build --app insights` → `ModuleNotFoundError: No
module named 'ibis'`.

**Why a *build* step hits a *backend* Python import**: `bench build` has to
import each installed app's Python package to read its `hooks.py` (asset
manifests, `app_include_js`/`css`, build config) even when it's only bundling
frontend assets. If Insights' package (or something it imports at module load
time) does `import ibis` at the top level, a missing `ibis` install fails
*any* bench operation that touches the app, not just runtime requests — which
is consistent with this failing at `build` rather than only when a chart
actually runs a query.

**Most likely root cause, given this session's own history**: earlier this
session, `ucc_intelligence` itself was found sitting in a bench-side git repo
that had never been through the normal `bench get-app` flow (it was manually
copied in). `bench get-app` runs `bench setup requirements` as part of adding
an app, which installs everything in that app's `pyproject.toml`/
`requirements.txt` into the bench's Python virtualenv. If Insights was added
by any path that skipped that step — manual clone, a partial/interrupted
`get-app`, or a requirements install that ran before Insights added `ibis` as
a dependency — its Python deps, including `ibis-framework`, would simply never
have been installed. This is a normal, non-destructive, "someone re-run the
requirements installer" situation, not a version incompatibility, until
proven otherwise.

**Diagnostic commands — read-only, run from the bench root
(`~/frappe-bench` or wherever yours lives), report the raw output:**

```bash
# 1. Confirm the installed Insights version/commit
bench version
git -C apps/insights log -1 --oneline
git -C apps/insights remote -v

# 2. Confirm ibis is/isn't in the bench's Python env
./env/bin/pip show ibis-framework
./env/bin/python -c "import ibis; print(ibis.__version__)"

# 3. Confirm what Insights itself declares it needs
cat apps/insights/pyproject.toml 2>/dev/null | grep -i -A2 ibis
cat apps/insights/requirements.txt 2>/dev/null | grep -i ibis

# 4. Sanity check: is this isolated to ibis, or did requirements never run at all?
./env/bin/pip show pandas 2>&1 | head -3
```

**Fix to try first (safe, standard, non-destructive)**:

```bash
bench setup requirements
bench build --app insights
```

`bench setup requirements` re-syncs pip installs for *every* installed app
against each app's own pinned requirements file — it's the normal bench
operation for exactly this situation, not a workaround. If step 1's `pyproject.toml`/`requirements.txt`
grep confirms `ibis-framework` (or `ibis-framework[duckdb]`/`[mysql]`, depending on
the site's DB backend) is genuinely listed as a dependency, this should resolve it.

**If that doesn't fix it**: report back the exact output of the four
diagnostic commands above, in particular whether `pip show ibis-framework`
still comes back empty after `bench setup requirements`, and what Frappe
version `bench version` reports next to Insights' own version. That would
point to a real version mismatch (Insights 2.2.3 requiring a newer Frappe/
Python than this bench runs), which is outside a normal pip install and is
exactly the "stop and report" case CLAUDE.md and this task both call for —
I will not suggest a bench downgrade or a manual pinned pip install to paper
over a real incompatibility.

**Open**: unresolved until you run the above and report back. Steps 2-4
below therefore also can't be exercised live yet; they're specified precisely
so they're ready to run the moment Insights builds.

---

## 2. Pilot chart pick

**Picked**: *"No. of Student Applicants per Year"* — Criterion 4, subcriterion
4.1.1, chart id `c411-applicants-year`.

**Why this one, checked against the real source, not guessed**:

- Its `LIVE_VISUAL_EXPANSION` definition (`custom-html-block/JAVASCRIPT.js`)
  says exactly what it is: `"description": "Counts all Student Applicant
  records grouped by academic year."` — a single-DocType `COUNT(*) GROUP BY`
  aggregate. No joins, no derived business logic, no multi-source
  reconciliation.
- Its `type` is `admission-line`, rendered by `renderAdmissionLine()`
  (`JAVASCRIPT.js:2282`). I read that function: it takes `rows` as plain
  `[label, value]` pairs and draws an SVG line with axis gridlines — the same
  shape as the generic `trend`/`bar` renderers, just under a different name
  with admission-specific SVG dimensions/CSS classes. It is **not** one of
  the bespoke types (`decision`, `network`, `reconciliation`, `ladder`,
  `risk-matrix`) that have no sane Insights equivalent — those have
  structurally different data shapes (root+branches, centre+nodes, paired
  reconciliation rows, ranked steps) that a generic BI chart can't reproduce
  without inventing a new visualisation, which is explicitly out of scope.
- I traced its actual data source in `server-scripts/UCC Analytics -
  Criterion 4.py:2397`:
  `applicants_by_year = sort_group_rows(group_count_rows(applicant_rows,
  "academic_year"), True)`, where `applicant_rows` comes from
  `fetch_rows("applicant", applicant_source, [...])` →
  `frappe.get_list("Student Applicant", filters=active_filters,
  limit_page_length=row_limit+1, order_by="modified desc")`. This is
  literally `SELECT academic_year, COUNT(*) FROM \`tabStudent Applicant\`
  GROUP BY academic_year ORDER BY academic_year`, filtered by whatever the
  frontend's filter strip currently has set. Exactly the kind of query
  Insights is built for.
- It's the same chart CLAUDE.md's own Phase 4 discussion pointed at, so this
  pilot's findings will be directly reusable when Phase 4 actually migrates
  Criterion 4's API.

---

## 3. Pilot build — what's shipped, what Felix still has to do live

**What I built and committed** (additive, reversible as one block — see the
`INSIGHTS PILOT` comment header in the source):

- `ucc_intelligence/ucc_intelligence/sophia/page/sophia_analytics/sophia_analytics.js`:
  a `watchForInsightsPilotTarget(root)` function, called once from `boot()`
  alongside the existing `initPlatformShell`/`initAnalyticsEngine` calls.
  It uses a `MutationObserver` to wait for `[data-demo-card="c411-applicants-year"]`
  to appear (that card is mounted lazily, only once the user opens the 4.1.1
  tab — see `ensureLiveSectionCards` in the legacy engine — so it can't
  assume the target exists at boot), then inserts one sibling card labelled
  "Insights pilot" right after it, containing either an iframe (once
  `INSIGHTS_PILOT_EMBED_URL` is set) or a "not yet wired up" placeholder.
  It never touches `CHART_PLUGINS`, `registerChartPlugin`, or `renderChart`
  — regression-guarded by three new checks in
  `tools/test_sophia_analytics_page.py` (21/21 passing, including the
  pre-existing 17 from Phase 3).
- A tiny injected `<style>` block (not a change to `sophia_analytics.css`,
  which stays byte-identical to the legacy `CSS.css` — that identity is
  itself regression-guarded, so pilot styling goes through JS instead).

**What still needs the real bench + Insights UI (can't be done from this
repo)**:

1. Once `bench build --app insights` succeeds (§1), create in the Insights
   UI:
   - **Data Source**: the site's own database (Insights supports adding the
     current Frappe site as a queryable source directly — no new credentials
     needed).
   - **Query**: `SELECT academic_year, COUNT(*) AS applicant_count FROM
     \`tabStudent Applicant\` GROUP BY academic_year ORDER BY academic_year`
     — matching `applicants_by_year`'s actual computation above. Note: the
     legacy engine caps at `row_limit` (default 2000, see
     `server-scripts/UCC Analytics - Criterion 4.py:41`) records fetched
     *before* grouping, not 2000 groups — for a "records per year" grouping
     this cap is very unlikely to bite (2000 rows is a small slice of a
     multi-year applicant table only if the college is far larger than
     expected), but it means the two charts aren't guaranteed
     byte-identical on a very large dataset. Worth a spot-check, not a
     blocker.
   - **Chart**: line chart, x = `academic_year`, y = `applicant_count`.
2. Get the chart's embeddable URL (Insights' public/shared link, or whatever
   v2.2.3 actually exposes — I don't know its exact route without seeing it
   live) and set `INSIGHTS_PILOT_EMBED_URL` in `sophia_analytics.js` to it.
   Tell me the value (or the pattern) and I'll wire it in and push.
3. `bench build --app ucc_intelligence` + hard refresh, confirm the second
   card appears next to the existing "No. of Student Applicants per Year"
   card on the 4.1.1 tab, and that the original chart is completely
   unaffected.

**Update, 2026-07-28 — environment changed, §1's `ibis` blocker is resolved**:
`ucc.local` was deleted and rebuilt as `ucc-sms-v2`; Insights is now v3.12.2
(not v2.2.3 above) and `bench build --app insights` completes clean on the
new site. Manual click-through in the Insights Query Builder proved
unreliable via browser automation, so Data Source/Query/Chart creation moved
to a script instead: **`docs/migration/scripts/create_insights_pilot.py`**
— paste into `bench --site ucc-sms-v2 console`. It does NOT hardcode
Insights' internal schema (v3 is enough of a rewrite from v2 that guessing
field names from older docs isn't safe) — it discovers the real DocType/field
structure first and prints it, and separately verified two things from the
repo alone that the original bullet list above got slightly wrong assuming
parity with the legacy JS variable names:

- `academic_year` is used as a **hardcoded literal** in
  `server-scripts/UCC Analytics - Criterion 4.py:2397`, never verified to
  exist the way `nationality`/`program`/`agent` are (those go through
  `resolve_field()` with a candidate list first). If it's not a real field on
  `Student Applicant`, `group_count_rows()` silently buckets every row under
  `"Not specified"` rather than erroring — the script's Stage 0 checks this
  against the live schema before anything else runs.
- The base query (no filters selected) has **no WHERE clause at all** —
  `applied_filters()` only populates once a real request payload sets a
  filter, confirmed by reading the function directly, not assumed.

Script isn't run yet (still no bench access in this session) — waiting on
its Stage 0/1 discovery output before writing the actual creation call, same
round-trip as every other bench-dependent step in this doc.

**Update, 2026-07-28 (later) — real schema confirmed from the local bench
session's Stage 0/1/1b run**: `Student Applicant.academic_year` is a real
Link field (62 rows, 0 blank, sample values 2021–2025), and the existing
`"Site DB"` Data Source should be reused, not duplicated. The local session
also found this Insights install has both old and v3 schemas side by side,
and asked for the exact `Insights Query v3`/`Insights Chart v3` creation
script. Rather than write that from memory of Insights' v2 API (a materially
different, ibis-based rewrite in v3), I read the actual v3.12.2 source on
GitHub directly (`frappe/insights`, tag `v3.12.2` — Python controllers +
frontend TypeScript operation/chart-config types, cited by file:line in the
script) and found two things the task's own assumptions got wrong:

- **`Insights Query v3.operations`** is a JSON list of typed steps, not a
  flat DocField structure. A `source` step's `table.table_name` must be the
  **raw SQL table name with the `tab` prefix** (`"tabStudent Applicant"`,
  confirmed via `insights_table_v3.py`'s `get_table_name`/`bulk_create`) —
  not the DocType name. A `summarize` step's count measure needs the special
  sentinel `column_name: "count"` + `aggregation: "count"`
  (`ibis_utils.py`'s `translate_measure`) to get a real `COUNT(*)`-equivalent
  row count, rather than counting an arbitrary named column.
- **`Insights Chart v3` has no `public_key` field, and its `is_public` field
  (which does exist) is never read anywhere in its controller** — dead for
  sharing purposes. The real public-link mechanism lives on **`Insights
  Dashboard v3`** (`is_public` + `share_link`, served at
  `/insights/shared/dashboard/<name>` — confirmed via that doctype's own
  preview-generation code, which builds that exact URL). Getting an
  embeddable link therefore requires wrapping the chart in a minimal
  dashboard and publishing *that*, not the chart directly.
- Also worth flagging early, ahead of §4(b)'s actual test:
  `Insights Dashboard v3.get_distinct_column_values` explicitly allows Guest
  (unauthenticated) access once `is_public=1` — a public dashboard is
  visible to anyone with the link, logged in or not, by design.

`docs/migration/scripts/create_insights_pilot.py` now has real Stage 2
creation logic (Query → Chart → Dashboard → publish) built from this
verified schema, plus a note on the chart-type mismatch: the task asked for
`chart_type = bar`, but the actual legacy chart being piloted
(`c411-applicants-year`) is type `admission-line` — an actual line chart,
not a bar chart (`server-scripts/UCC Analytics - Criterion 4.py:2397` via
`renderAdmissionLine()`). Defaulted to `CHART_TYPE = "Line"` as the closer
visual match, flagged the discrepancy rather than silently picking either,
and made it a one-constant change either way. Not run yet — same round-trip,
waiting on the local session to execute it and report the created record
names + the actual public URL.

**Update, 2026-07-28 (later) — zero-rows bug found and fixed**: running the
script surfaced `Insights Table v3` for `tabStudent Applicant` at
`stored=0, sync_mode="Full", last_synced_on=None` — never synced, hence the
query returning zero rows. Read `insights_table_v3.py` and
`insights_data_source_v3.py` in full rather than guessing at a fix:
`InsightsTablev3.get_ibis_table()` (`:136-155`) routes through a DuckDB
warehouse copy that needs importing *unless* `use_live_connection=True`, in
which case it calls `InsightsDataSourcev3.get_ibis_table()` (`:441-447`)
directly — for a MariaDB/Site-DB source that's just
`remote_db.table(table_name)`, a live handle on the site's own DB connection,
no sync required. Set `query.use_live_connection = 1` in the script instead
of building a sync/wait-for-background-job path — simpler, and it matches
the legacy engine's own per-request-live-query behaviour more faithfully
than a periodically-synced copy would anyway. The reuse-existing-query branch
now self-heals a query left over from before this fix rather than silently
reusing one still pointed at the empty warehouse copy.

One more finding along the way, worth having on record before §4(b) actually
runs: `apply_user_permissions()` (`insights_table_v3.py:287-289`) opens with
`if frappe.flags.get("insights_for_public_access"): return t` — row/column
permission filtering is **unconditionally skipped** for requests served
through the public-dashboard flag, live or warehouse mode doesn't matter.
That's no longer a risk to test for, that's read directly from the code.
Separately, even for non-public requests, filtering is gated by
`Insights Settings.apply_user_permissions` (Insights' own default is 1, but
the script now checks the real value on this install) — and even when on,
it enforces plain Frappe DocType read permission, a different and usually
broader question than `ucc_dashboard_access`'s criterion-level gating.
Neither finding changes §4(b)'s status to answered — the actual
logged-out/restricted-user test is still what's needed — but it does mean
the likely outcome is no longer purely speculative.

**Update, 2026-07-28 (later still) — dashboard wiring bug found and fixed**:
Felix ran a genuine zero-cookie permission test against the real bench and
found a partial, informative result: `insights.api.shared.get_dashboard_name`
returned 200 fully anonymous (confirms the earlier finding — some
public-dashboard paths skip permission checks entirely by design), but
`insights.api.get_doc` for the pilot Chart record itself returned **404**
(not 403) both logged out *and* as Administrator — meaning the record
genuinely couldn't be resolved by name, not merely permission-blocked.

Root cause, found by reading the real frontend source rather than continuing
to guess (the previous script version had flagged this exact uncertainty):
`frontend/src2/dashboard/dashboard.ts:62-71` and
`frontend/src2/types/workbook.types.ts:131-142` show the actual
`WorkbookDashboardChart` shape is `{"type": "chart", "chart": <name>,
"layout": {"i": <unique string>, "x", "y", "w", "h"}}` — layout fields
**nested under a `layout` key**, named `w`/`h` (not `width`/`height`), plus a
**required unique `i`** (widget instance id, consumed by the grid layout
library) that the script omitted entirely. The previous version wrote flat
`x/y/width/height` with no `layout` wrapper and no `i` — malformed enough
that the frontend's chart-resolution logic broke, consistent with the 404.

Fixed with the verified shape, and added two things that would have caught
this before it reached the browser: (1) after wiring, the script now fetches
the chart via `frappe.get_doc()` server-side the same way
`insights.api.get_doc`'s direct-fetch path does, and stops with a clear
message if that fails: "This would 404 for every viewer, admin included";
(2) it separately checks `Dashboard.linked_charts` (the `Insights Dashboard
Chart v3` child table, auto-derived from `items` by
`set_linked_charts()` — confirmed this is literally what
`insights/api/shared.py`'s `get_public_charts()` queries to decide guest
access to an individual chart record) actually contains the chart, since
`items` looking right doesn't guarantee the derived child table does too.
The reuse-existing-dashboard branch now also self-heals: it recomputes
`items` from the current chart every run and corrects it if the stored value
differs, rather than trusting a possibly-still-wrong prior write.

Net effect on the permission question so far: still open, same as before,
but the reason it couldn't be answered completely (the chart never actually
rendered) should now be fixed. Waiting on Felix's re-test of the full
picture — does the chart render at all now, and does the earlier
`insights_for_public_access`-skips-filtering finding actually manifest as
unfiltered real data for a genuinely logged-out viewer.

**Update, 2026-07-28 (later still) — the real bug, found and fixed**: the
`items`-shape fix above wasn't it. Felix reran with a fresh Dashboard
(`qinmiinfrs`) and Chart (`qinaqei0rn`), and both 404'd — not just the chart,
the *dashboard itself*, moments after the console script printed it as
created, both logged out and as Administrator, using the exact names the
script had just printed. That ruled out a naming/lookup-signature issue (a
malformed reference would break the chart lookup specifically, not the
dashboard record itself) and pointed at something session-scoped instead.

Confirmed in Frappe's own core source, not Insights': `bench console`'s exit
handler (`frappe/commands/utils.py:_console_cleanup`, registered via
`atexit`) calls `frappe.db.rollback()` explicitly, by design, whenever a
console session closes. The script never called `frappe.db.commit()`
anywhere. Every record it created lived only inside that console session's
own open MariaDB transaction — invisible to any other connection (a real
browser request hits a completely separate web-worker connection) until
committed, and explicitly discarded the moment the session ended. This
explains both mysteries from the previous round at once: the script's own
in-session verification checks (`frappe.get_doc()` calls right after
`insert()`) passed because they read within the *same* transaction, and a
separately-issued request moments later couldn't find anything because
nothing had actually been durably written.

Fixed by adding `frappe.db.commit()` at four milestones (after Query
creation+verification, after Chart creation, after Dashboard+items are
wired, after `is_public` is set) rather than one commit at the very end —
so a script that stops early on one of its own `STOP` checks still preserves
whatever succeeded up to that point instead of losing all of it to the same
rollback. None of this touches the `items`/`layout` fix from the previous
update, which was still a real, worth-fixing bug — it just wasn't the one
actually causing the 404s reported this round.

**Update, 2026-07-28 (yet later) — the commit fix alone didn't resolve it
either**: rerun with fresh records (`ionf4ct5je`/`ionlk6l8mn`), script
completed cleanly with a fully-populated `RESULT`, and both records still
404'd via an authenticated `insights.api.get_doc` call moments later. Before
guessing at a third fix, verified rather than assumed: read Frappe's actual
`commit()` (`frappe/database/database.py:1173-1184`) — it's a real
`self.sql("commit")` followed by `self.begin()` to open a fresh transaction,
the same code path a web worker uses, no console-specific interception.
Since the script's `RESULT` dict was fully populated (meaning execution
reached the final `return`, after all four `commit()` calls), the commits
almost certainly fired. That rules out "commit is a no-op in console" but
doesn't by itself prove the records are visible to a completely different
process — so rather than a third blind fix, added
`stage_3_diagnose_persistence()` to the script: prints this session's
`frappe.local.site`/`db_name`/actual connected database, checks
`frappe.db.exists()` for both records in the *same* session (Felix's own
suggested first test), and gives the exact `bench --site ucc-sms-v2 execute
frappe.db.exists --args '[...]'` command — a genuinely separate process,
the same way `bench execute` inits a fresh site connection per invocation —
as the decisive cross-process test. If that returns `True`, the problem is
in the web/API layer, not the database, and worth digging into
`insights.api.get_doc` specifically or site-routing for whatever domain the
browser is actually pointed at. If it also returns `False`, still a
persistence problem, and the site name printed by the diagnostic is the
next thing to cross-check against the browser's actual site.

**Update, 2026-07-28 (yet later still) — decisive: the row never reaches the
table at all, even via raw SQL**. Felix ran `bench --site ucc-sms-v2
mariadb` (a genuinely separate process, real `mysql` client, zero Frappe
Python/ORM involved) and checked directly: `is_virtual`/`istable` both `0`
for both DocTypes (ruling out a virtual-doctype explanation I'd floated and
checked against the vanilla v3.12.2 source first), the specific row —
empty set, and `SELECT COUNT(*) FROM \`tabInsights Dashboard v3\`` — **0**.
Not just this run's row missing: the entire table is empty, across every
attempt so far, despite the script printing "Created Dashboard: ..." each
time with no errors.

Added `raw_sql_row_exists()` to the script: shells out to a genuinely
separate `mysql`/`mariadb` CLI process (mirroring `bench mariadb`'s own
connection resolution, `frappe/database/__init__.py:96-136`) via
`subprocess`, using `MYSQL_PWD` rather than a `--password=` arg so the
credential never shows in `ps aux`. Now called immediately after each of
the four `frappe.db.commit()` calls, checking every record's row count via
a completely independent OS process and DB connection *during* the same
script run — not a manual follow-up check afterward, and not
same-transaction visibility via `frappe.get_doc()`. This should pinpoint
precisely which commit (if any) a row fails to survive, or confirm the more
unusual possibility flagged in the script itself: that `frappe.db.commit()`
genuinely isn't persisting `Document.insert()` writes on this install at
all, which would point at something install-specific (a customised hook, a
patched `db_insert`, a non-standard commit/connection setup) rather than
anything explainable from the vanilla Frappe/Insights source alone. Waiting
on this round's output.

**Update, 2026-07-28 (final for this thread so far) — persistence confirmed,
root cause has moved to the site name itself**: `bench --site
ucc-sms-v2.orb.local execute frappe.db.exists --args [...]` (a genuinely
separate process from any console session) found both records. Persistence
is not the problem — `frappe.db.commit()` works exactly as it should.

What jumped out immediately: that command used `--site
ucc-sms-v2.orb.local`. Every instruction up to this point — mine included,
in this very script's own docstring and usage line — said bare `--site
ucc-sms-v2`. If this bench has two separate site folders under `sites/`
(`ucc-sms-v2` and `ucc-sms-v2.orb.local`), every prior run of this script
(pasted into a console opened against bare `ucc-sms-v2`, per my own
instructions) would have written real, committed rows into the *empty*
`ucc-sms-v2` site, while the browser — almost certainly resolving whatever
`*.orb.local` hostname it's actually being accessed through — reads from
`ucc-sms-v2.orb.local` instead. That would account for every symptom in
this entire thread without anything being wrong in `insights.api.get_doc`
or the web layer at all: commits genuinely work, rows genuinely persist,
they've just been landing in the wrong site's database the whole time.

Removed every hardcoded `ucc-sms-v2` from the script's runnable output —
`stage_3_diagnose_persistence()`'s example `bench execute` commands and
`raw_sql_row_exists()` now derive everything from `frappe.local.site` (the
live, unambiguous truth for whatever session is actually running), and the
docstring's usage line now says to confirm the real site name via `ls
sites/` rather than assuming one. Asked Felix to confirm that listing and
re-run the full creation script explicitly against `ucc-sms-v2.orb.local`
(matching what his decisive check used) as the next concrete test — not
another blind fix, this one has real evidence behind it.

**Update, 2026-07-28 (later again) — two-site theory ruled out cleanly**:
`ls sites/` shows exactly one folder, `ucc-sms-v2.orb.local`, and Felix
confirmed every console invocation tonight — including the one that made the
records `bench execute` proved exist — used the full `ucc-sms-v2.orb.local`
name throughout. No site mismatch anywhere. Persistence is fully proven
(raw `mysql` CLI, `bench execute`, fresh console all agree the records are
real), and the site-name theory doesn't hold up either. This genuinely is
the web/API layer, as Felix suspected from the start.

Traced the full call chain rather than guessing further: `insights.api.
get_doc` → `frappe.client.get` (`frappe/client.py:93-112`) → `frappe.get_doc()`
+ `frappe.connect()` (`frappe/__init__.py:274-299`, `frappe/app.py:177-209`
`init_request`). Every step is ordinary, correct code — `frappe.connect()`
runs at the top of every single request. Nothing in the code itself explains
a request failing to see data that provably exists.

Given every *freshly-started, short-lived* process tonight (console,
`bench execute`, raw `mysql`) succeeded, and only the *long-running web
worker* process serving the actual browser fails, the leading hypothesis has
shifted from "bug in Insights or the script" to "stale long-lived worker
state" — a connection or process-level cache from before tonight's records
(or possibly before Insights itself was fully fixed and built) existed.
Recommended two things: a cheap check of `maintenance_mode` in
`site_config.json` (a real conditional branch found directly in
`app.py:212` `setup_read_only_mode`, unlikely by itself but free to rule
out), and the actual test worth trying — `bench restart` (or the local
equivalent) followed by a re-test. If that fixes it, there was never a code
bug to find in Insights or this script; if it doesn't, the staleness is
somewhere less obvious and worth another round with that ruled out too.

**Update, 2026-07-28 (still later) — worker restart ruled out too; traced
the permission layer and ruled that out as well**: no `maintenance_mode`
flag, and a full `bench restart` followed by a genuinely fresh page reload
still produced the identical `DoesNotExistError`. That rules out stale
worker state as cleanly as raw SQL ruled out non-persistence.

Felix's sharpest remaining question was whether Insights' own permission
layer raises `DoesNotExistError` as a deliberate obscurity measure instead
of `PermissionError` — a real pattern some apps use. Checked
`insights/hooks.py` and found real `has_permission`/
`permission_query_conditions` registrations for both doctypes
(`insights.permissions.has_doc_permission` /
`get_permission_query_conditions`), so this was a genuinely live
possibility, not a dead end to wave off. Read `insights/permissions.py` in
full: `has_doc_permission` short-circuits `return True` immediately for
`self.is_admin` — consistent with Administrator access — and even when it
doesn't, a failure there surfaces as `frappe.PermissionError`, which
`insights.api.get_doc` explicitly catches and checks `is_public(...)` for
before ever re-raising. That's a different, distinguishable exception from
`DoesNotExistError`.

More decisively: read `frappe.db.get_value()`/`get_values()`
(`frappe/database/database.py:469-650`, which `Document.load_from_db()`
actually calls) and confirmed neither ever references
`permission_query_conditions` or `has_permission` anywhere — those hooks
are a `get_list`/report-view mechanism only, never consulted for a
single-document fetch by name. The exact error text Felix reported
(`"Insights Chart v3 qinaqei0rn not found"`) matches
`frappe/model/document.py:179-182`'s `DoesNotExistError` message format
verbatim, confirming `load_from_db()`'s raw `frappe.db.get_value(doctype,
name, "*")` call is itself coming back empty inside the web request — a
permission-masquerade theory doesn't fit that mechanism.

So: two different Frappe DB calls against the identical row — `frappe.db.
exists()` (succeeds, proven via `bench execute`) and `frappe.db.get_value(
..., "*")` inside `frappe.get_doc()` (fails, inside the real web request) —
disagree, and every layer of business logic in between has now checked out
clean. The next test isolates whether this is really about the *web request
context* specifically, by calling the exact same public method the browser
calls, but from a known-clean process:

```bash
bench --site ucc-sms-v2.orb.local execute insights.api.get_doc --args '["Insights Chart v3", "<chart_name>"]'
bench --site ucc-sms-v2.orb.local execute insights.api.get_doc --args '["Insights Dashboard v3", "<dashboard_name>"]'
```

If that succeeds, the bug is conclusively specific to the real HTTP request
path (something about session/auth context or request parsing that
`bench execute` doesn't reproduce) — not the business logic, which is now
fully verified. If it fails identically even here, that's even more
telling: the exact same `frappe.get_doc()` call fails the same way outside
a browser entirely, which would point at something narrower — worth then
running `DESCRIBE \`tabInsights Chart v3\`;` via `bench mariadb` to check
for a schema anomaly specifically affecting `SELECT *` (as opposed to the
`SELECT name`-style query `frappe.db.exists()` runs).

---

## 4. Filter and permission tests — procedures, results pending

Neither of these can be answered from the repo. Both need you, live, on the
real bench, once §3 is wired up.

### 4(a) Filters

The existing chart is filter-aware **server-side**: the frontend's filter
strip sends `payload.filters.academic_year` (etc.) to
`ucc_analytics_criterion_4`, which maps it through `FILTER_FIELD_CANDIDATES`
into a real `frappe.get_list` filter before grouping
(`server-scripts/UCC Analytics - Criterion 4.py:1540-1562`). There is no
client-side filtering of a pre-fetched dataset to compare against — the
query itself changes.

**Test**:
1. Open Criterion 4 → 4.1.1. Note the existing chart's values (or open dev
   tools → Network → find the `ucc_analytics_criterion_4` response → read
   `admission_intelligence.charts.applicants_by_year` directly).
2. Change the Academic Year filter to a specific year.
3. Confirm the *existing* chart updates (expected: yes — this just confirms
   the baseline still works, not new information).
4. Look at the **Insights pilot card**. Does it change too, or stay frozen?
   My expectation, to be proven or disproven: it stays frozen, because the
   iframe embed has no mechanism today to receive this page's filter state —
   Insights charts take their own "Query Variables"/dashboard filters
   (v2.2.3 may or may not support driving those from an iframe's URL query
   string; genuinely don't know without seeing the live UI). Report exactly
   what you see, including whether Insights' own chart/query editor exposes
   any variable/parameter option at all.

**Result**: _still pending — never actually run_. The multi-day persistence
debugging saga in §3's updates consumed the pilot's live-testing time before
this test was reached. The reasoning above (no mechanism today for this
page's filter strip to reach an embedded Insights chart without deliberate
wiring) stands as an educated expectation, not a tested result — flagging
that distinction explicitly rather than letting it read as answered. Whoever
picks this up next should actually run the 4-step test above before treating
filter behaviour as known.

### 4(b) Permissions — the important one

The existing engine's blocked-source behaviour is precise: if the
`Student Applicant` source resolves to `permission_denied` for the signed-in
user, `build_admission_intelligence()` returns `charts: {}` (no
`applicants_by_year` key at all), the frontend's `metricRows()` finds nothing
under `chart.dataKey`, `chartForLive()` sees zero rows, checks
`result.sources` for a `permission_denied` entry, and renders
`UCCShared.permissionNoticeHtml(...)` — the same amber blocked-source card
used everywhere else, tested in the Phase 2/3 regression suite.

Insights has its own, separate permission model (Insights Team membership,
and optionally per-data-source row-level rules if someone configures them) —
it does **not** know about `ucc_dashboard_access`, and a public/shared chart
link in particular is often designed to work for anyone with the link,
logged in or not. That's a real risk, not a hypothetical one, which is why
the task calls this the single most important thing to answer here.

**Test**:
1. Identify or create a test user who does *not* have read permission on
   `Student Applicant` (or is excluded from Criterion 4 entirely via
   `UCC Dashboard Access`).
2. As that user, confirm the *existing* chart shows the blocked-source
   notice (expected — this is the known-good baseline to compare against).
3. As that same user, look at the **Insights pilot card**. Record exactly
   what it shows:
   - Does it silently render the real `academic_year`/count data anyway?
     (Worst outcome — a permission bypass.)
   - Does it show an Insights-native permission error? (Better, but still
     not the same UX as the rest of the page, and worth knowing what that
     error actually says.)
   - Does it fail to load / 404? (Also acceptable-ish, but confirm it fails
     *closed*, not open.)
4. If the pilot uses a public/shared link (no login required to view), also
   check it from a logged-out / different-browser session — a public link
   bypasses the "log in as a restricted user" test entirely and would need
   to be flagged as unacceptable regardless of what the restricted-user test
   shows.

**Result**: **Confirmed — the worst outcome, and it's Insights' actual
design, not a bug.** Felix ran the real test with genuinely zero-cookie
requests (`credentials: "omit"`, no session at all) against both records:

```
insights.api.get_doc(Insights Dashboard v3, tt5b9kk0bn) -> 200, full record
insights.api.get_doc(Insights Chart v3, tt51l7mma3)     -> 200, full record + query config
```

A completely unauthenticated visitor with nothing but the link gets full
read access — not just the rendered chart, the underlying query
configuration too. This matches, and now empirically confirms, the code
finding from §3's updates: `apply_user_permissions()`
(`insights_table_v3.py:287-289`) explicitly skips row/column permission
filtering entirely whenever a request is served through the public-dashboard
flag. There is no partial protection, no per-user scoping, nothing
equivalent to `ucc_dashboard_access`'s blocked-source behaviour once a
dashboard is marked public — "public" in Insights means genuinely,
unconditionally public.

This is the answer the whole pilot existed to get, and it's a hard
constraint, not a tuning knob: **anything published as a public Insights
dashboard is visible to anyone with the URL, permanently, regardless of the
underlying data's sensitivity or `ucc_dashboard_access`'s role gating.**

**Update, 2026-07-29 — new direction (Option B: embed live Insights charts
directly, not copy logic out) requires testing the *private* path, which
this pilot never touched.** Read the real, unabridged Insights v3.12.2
source rather than assuming from the public-link findings above
(`insights/permissions.py`, `insights/api/__init__.py`,
`insights_table_v3.py`'s `apply_user_permissions`, `insights_query_v3.py`'s
`execute`). Two genuinely independent permission layers exist:

- **Layer 1 (document access)** — can the user open the Chart/Dashboard/
  Query record at all? Governed entirely by `InsightsPermissions`
  (ownership, `DocShare`, Workbook access, Team-based resource grants) —
  has nothing to do with the underlying data's DocType permission. Testing
  only `insights.api.get_doc` (as originally scoped for this check) mostly
  tests this layer, which mainly answers "did someone remember to share
  this chart," not the thing that actually matters for a safe embed.
- **Layer 2 (row/column data filtering on query execution)** — when
  `Insights Query v3.execute()` runs (the real `insights.api.run_doc_method`
  entry point, not a direct Python call), every table it reads goes
  through `apply_user_permissions()`, which applies
  `frappe.has_permission(doctype, "read")` and the same
  `permission_query_conditions` machinery `frappe.get_list` uses — a real
  implementation (`t.filter(False)` when the user can't read the DocType),
  not a stub. Gated by `Insights Settings.apply_user_permissions` (ships
  default `1`, needs confirming on the real site) and skipped only via
  `frappe.flags.insights_for_public_access`, which is set only on the
  public path this pilot already ruled out — not relevant to the private
  path.

Go/no-go test script, testing both layers separately (isolating Layer 2
requires explicitly sharing the chart with the restricted test user first,
otherwise a Layer-1 failure masks whatever Layer 2 does), with a positive
control (grant real `Student Applicant` access, confirm real rows come
back, so a zero-row result is provably permission-driven and not "broken
for everyone"):
**`docs/migration/scripts/test_insights_private_permissions.py`** — not
run yet, same round-trip as every other bench-dependent step in this doc.

---

## 5. Cost estimate for full Analytics-wide adoption (informed by this pilot's scope, not yet by its results)

Rough, and explicitly conditional on §4(b) coming back acceptable — if
permissions don't hold, the rest of this estimate is moot until Insights is
reconfigured with real row-level security or the embed model changes
entirely.

I counted the actual `LIVE_VISUAL_EXPANSION` inventory programmatically
rather than eyeballing it (209 chart definitions total, across all seven
criteria):

| Type | Count | Insights fit |
|---|---:|---|
| `donut` | 38 | plain aggregate — likely candidate |
| `bar` | 35 | plain aggregate — likely candidate |
| `lifecycle` | 31 | generic-ish (stage funnel) — **unverified**, depends on Insights' actual chart type list |
| `funnel` | 28 | generic-ish — **unverified** |
| `matrix` | 23 | generic-ish (heatmap-like) — **unverified** |
| `radar` | 15 | generic-ish (spider/radar) — **unverified** |
| `trend` | 14 | plain aggregate — likely candidate |
| `gauge` | 9 | generic-ish — **unverified** |
| `ladder` | 7 | bespoke, no equivalent |
| `admission-line` | 3 | plain aggregate — likely candidate (pilot's own type) |
| `decision` | 2 | bespoke, no equivalent |
| `admission-column` | 2 | plain aggregate — likely candidate |
| `reconciliation` | 1 | bespoke, no equivalent |
| `network` | 1 | bespoke, no equivalent |
| `risk-matrix` | 0 (registered, unused) | bespoke, no equivalent |

So: **11 charts (`decision`+`network`+`reconciliation`+`ladder`+`risk-matrix`)
are firmly out of scope**, matching the task's own framing exactly. **92
(`bar`+`donut`+`trend`+`admission-line`+`admission-column`) are plain
aggregates like the pilot chart** — the closest thing to a "known-good"
adoption pool. The remaining **106 (`lifecycle`/`funnel`/`matrix`/`radar`/
`gauge`) were originally left as a genuine unknown** in this doc's first
version — **§7 below now classifies all 106 individually**, resolving that
gap. Short version: 55 more turn out to be plain-aggregate candidates (total
candidate pool 147/209), 37 turn out to have no Insights equivalent at all
regardless of visual complexity (total non-candidates 48/209), and 14
genuinely need a closer look before anyone decides (down from 106).
- Each plain-aggregate chart's data isn't a raw table scan — most go through
  the same kind of derived-grouping logic `build_admission_intelligence()`
  does (status filtering, field-candidate resolution across DocTypes that
  may or may not have the expected fieldname, multi-source joins in some
  criteria). Each one is its own small migration, not a bulk copy-paste.
- **If** filters need "separate wiring" per §4(a)'s likely answer, that's a
  second per-chart integration cost on top of the query itself — not a
  one-time platform cost.
- §7's classification adds a cost dimension the type-name table above
  couldn't show: 37 of the 106 "unknown" charts aren't reading from a
  DocType at all — they're rendering request-time permission/availability
  counts (available vs. unavailable sources/metrics), which live nowhere an
  Insights SQL query can reach. Migrating those isn't "write a different
  query," it's "these charts don't have an underlying table, full stop."
  Separately, dozens of the remaining charts (the generic-fallback ones,
  bucket D in §7) show whichever metric happens to land in a rotating
  window keyed to the chart's position, not a metric chosen to match its
  own title — so even a perfect Insights port of *today's* behaviour would
  faithfully reproduce a title/data mismatch that arguably shouldn't be
  preserved. Full adoption of these 106 is as much an information-design
  decision (what should each card actually show) as an Insights migration.
- Net: full adoption is not a weekend project. A realistic estimate is
  low-to-mid tens of engineer-hours across query-building, filter wiring
  investigation, and permission-model reconciliation, before any visual
  polish — and that estimate could move substantially once §4(b)'s actual
  result is in, since a hard "no" on permissions could mean waiting on an
  Insights feature (or building a permission-aware proxy in front of it)
  before charts 2 through 35 are worth starting.

---

## 6. Recommendation, not a decision

The pilot is functionally complete: query, chart, and dashboard all work
against real live data, and §4(b) — the question this whole spike existed to
answer — has a definitive, tested result. This is Felix's call to make, not
mine; here's the honest tradeoff as it actually stands, not as it was hoped
to stand going in.

### What Insights is good at, confirmed tonight

Once the environment issues were actually understood (§1's `ibis` fix, §3's
`use_live_connection` fix, the dashboard `items`/`layout` shape, the
persistence saga below), building the pilot chart itself was genuinely
straightforward — a Query with a `summarize` step and a Chart pointed at it,
versus the hand-rolled SVG renderer this replaces. For the 147 plain-
aggregate charts identified across §5/§7, Insights would very likely be
**less code to build and maintain** than the current `renderBars`/
`renderTrend`/etc. string-building functions, once someone knows the real
`operations`/`layout` schemas (now documented in
`docs/migration/scripts/create_insights_pilot.py`, verified against the real
v3.12.2 source rather than guessed).

### What Insights is missing, confirmed tonight — the actual blocker

**A public Insights dashboard has no row- or column-level access control at
all.** §4(b)'s test was unambiguous: a genuinely unauthenticated request
(zero cookies) against a public dashboard's chart returned the full record,
including the underlying query configuration — not a degraded or partial
view, the same thing an authenticated user sees. `apply_user_permissions()`
skips entirely for public-dashboard requests, by Insights' own design, not
by misconfiguration. There is nothing here equivalent to
`ucc_dashboard_access`'s blocked-source notice, no partial redaction, no
"public but still scoped" middle ground — public means public, permanently,
to anyone who has or guesses the URL.

That is a hard constraint on how Insights can be used for anything backed by
data `ucc_dashboard_access` currently gates: **any chart published as a
public Insights dashboard is exactly as exposed as if that data were posted
on a public webpage**, regardless of which roles can see it in Sophia today.
Non-public Insights sharing (team membership, `DocShare`-based per-user
sharing — both real mechanisms found in `insights/permissions.py`) stays
inside Frappe's login wall, but that's a fundamentally different product
shape from "embed a chart in the existing Analytics page," which is what
this pilot actually spiked.

### An honest caveat on tonight's own reliability

Worth stating plainly: the multi-hour persistence debugging (§3's updates)
never landed on a single, fully-confirmed root cause. Every specific
hypothesis chased — console rollback, dashboard `items` shape, site-name
mismatch, stale worker processes, a permission-layer 404-as-obscurity
pattern — was each individually verified true or false against real evidence,
and each real bug found along the way (`items`/`layout` shape,
`use_live_connection`, missing commits) is now fixed and documented. But the
very last symptom — `insights.api.get_doc` 404ing on records proven to exist
by three independent methods, then working again after a `bench restart` and
some elapsed time, with no single mechanism ever pinned to explain the
"working again" part — resolved without full understanding of why. That's
not nothing: if this recurs on a differently-timed future attempt, it's
worth knowing tonight's fix was empirical, not root-caused, before assuming
Insights is now simply reliable to build on.

### Recommendation

- Given §4(b)'s result, publishing individual analytics charts as public
  Insights dashboards is **not viable as-is** for anything currently gated
  by `ucc_dashboard_access` — this would need either Insights reconfigured
  with real per-user row-level security (a real, documented mechanism in
  `insights/permissions.py`, but it requires being logged in — it does not
  extend to public/guest links), or charts served through a
  permission-checking proxy of Sophia's own, not something to work around
  chart-by-chart.
- That constraint is about the **public-sharing mechanism**, not Insights as
  a query/chart-building tool. If a future direction only ever shows
  Insights charts to logged-in, permission-checked Sophia users (e.g.
  server-side, proxied through `ucc_intelligence`'s own API rather than a
  public dashboard URL), tonight's finding doesn't rule that out — it just
  wasn't what this pilot tested, since the pilot specifically spiked the
  public-embed path.
- §4(a) (filters) is still genuinely untested — don't treat the "likely
  stays frozen" reasoning in that section as a result.
- The 147 plain-aggregate charts (92 original + 55 from §7) remain the
  right adoption pool *if* a permission-safe embedding path is found later.
  The 48 bespoke charts (11 uniquely-shaped + 37 not table-backed, per §7)
  stay hand-rolled regardless. The 14 "needs a closer look" charts are small
  enough to decide individually whenever Phase 4 reaches their criterion.

---

## 7. Full classification of the 106 "unknown" charts

Repo-only work, done while bench access is being sorted out on `ucc-sms-v2`.
Same method as the pilot chart in §2: read the real source, don't infer from
titles. Dispatched one read-only investigation per criterion (7 in total)
against the actual Server Scripts, then combined the results below.

### The mechanism (verified, not assumed)

None of these 106 charts (`lifecycle`/`funnel`/`matrix`/`radar`/`gauge`) have
a dedicated per-chart data mapping the way the pilot chart's `dataKey` does.
`admission_intelligence` (used by §2's pilot chart and its siblings) is the
**only** such dedicated block in the entire engine — confirmed by grep, one
match in `JAVASCRIPT.js`. Every other chart, including all 106 here, goes
through one shared fallback, `metricRows(result, chartIndex, chart)`
(`JAVASCRIPT.js:2399-2432`), which buckets by matching the chart's **title
text** against three regexes, in order, before falling through to a generic
default:

| Bucket | Title regex | What actually renders |
|---|---|---|
| A | `source availability\|evidence readiness\|source readiness` | 4 fixed rows built from `result.source_summary`/`result.metric_summary` — counts of how many of the criterion's declared sources/metrics resolved successfully for this user, this request |
| B | `status distribution\|system health\|control health\|readiness` | 4 fixed rows: Available / Unavailable / Sources / Exceptions counts, again about the response itself |
| C | `exception\|gap\|risk profile` | top 5 of `result.exceptions` (real per-criterion flagged-record counts) |
| D | *(no match — the default)* | a **rotating window** of up to 5 items from `result.metrics`, chosen by the chart's position index within its section, **not by any match to the chart's own title** |

### Two findings that apply across all seven criteria, verified independent of any one criterion's business logic

1. **Buckets A and B (37 charts) are not reading from a database table at
   all.** `source_summary`/`metric_summary` are meta-counts about which of
   the criterion's *other* declared metrics/sources resolved this request —
   computed at runtime from permission/connectivity outcomes, not stored
   anywhere queryable. An Insights SQL query has nothing to point at here
   regardless of how the chart is visually labelled ("Evidence Readiness
   Matrix" sounds like a heatmap over real records; it's actually 4 numbers
   about API response health). These are out of scope the same way
   `decision`/`network`/`ladder` are, just for a different reason — not
   because the visual shape is bespoke, but because there's no table behind
   it to query.
2. **Bucket D (58 charts) shows data chosen by position, not by meaning.**
   A chart titled "Governance Evidence Matrix" doesn't necessarily show
   governance-evidence data — it shows whichever metrics land in a
   `(chartIndex * 5) % metrics.length` window for that criterion. This means
   a byte-for-byte faithful Insights port of *today's* rendered content
   would often reproduce a title that doesn't match its own data — worth
   flagging as an information-design question distinct from the Insights
   feasibility question.

Given this, classification below is done **per criterion × bucket**, not
per individual chart title — charts sharing a criterion and bucket share
identical data provenance, so a single verified answer applies to all of
them. Each criterion section states its underlying metrics/exceptions pool
composition (with file:line) once, then classifies every chart in that
pool.


#### Criterion 1 -- Governance & Strategy

**Metrics pool: 51 total, 39 ever `available`** (17 plain count + 20 plain filtered-count + 2 composite `field_compare` + 12 static `unsupported`, excluded once unavailable). Available pool is 95% plain (37/39). **Exceptions**: not used by any Criterion 1 chart in this set. Source: `server-scripts/UCC Analytics - Criterion 1.py:1161-1279`.

| Chart id | Title | Type | Bucket | Classification |
|---|---|---|---|---|
| `v190-c1-overview-06` | Evidence Readiness Matrix | `matrix` | A | Bespoke — not table-backed |
| `v190-c1-overview-20` | Evidence Completeness | `lifecycle` | D | Plain aggregate |
| `v190-c1-overview-27` | Target Achievement Gauge | `funnel` | D | Plain aggregate |
| `v190-c1-overview-28` | Overall Criterion Readiness | `lifecycle` | B | Bespoke — not table-backed |
| `v190-c1-111-03` | Leadership and Role Readiness | `funnel` | B | Bespoke — not table-backed |
| `v190-c1-111-04` | Policy and Review Lifecycle | `lifecycle` | D | Plain aggregate |
| `v190-c1-111-05` | Governance Evidence Matrix | `radar` | D | Plain aggregate |
| `v190-c1-111-06` | Governance Action Completion | `matrix` | D | Plain aggregate |
| `v190-c1-111-15` | Policy Approval Status | `gauge` | D | Plain aggregate |
| `v190-c1-111-19` | Conflict and Independence Controls | `funnel` | D | Plain aggregate |
| `v190-c1-111-22` | Governance Records Readiness | `matrix` | B | Bespoke — not table-backed |
| `v190-c1-111-27` | Governance Source Readiness | `funnel` | A | Bespoke — not table-backed |
| `v190-c1-111-28` | Governance Metric Readiness | `lifecycle` | B | Bespoke — not table-backed |
| `v190-c1-121-03` | Strategic Target Readiness | `funnel` | B | Bespoke — not table-backed |
| `v190-c1-121-04` | Plan-to-Review Lifecycle | `lifecycle` | D | Plain aggregate |
| `v190-c1-121-06` | Strategic Action Completion | `matrix` | D | Plain aggregate |
| `v190-c1-121-22` | Objective Ownership Coverage | `matrix` | D | Plain aggregate |
| `v190-c1-121-27` | Strategy Source Readiness | `funnel` | A | Bespoke — not table-backed |
| `v190-c1-121-28` | Strategy Metric Readiness | `lifecycle` | B | Bespoke — not table-backed |

#### Criterion 2 -- Corporate Administration

**Metrics pool: 79 total, 72 ever `available`** (72 plain count/sum/avg, 0 composite, 7 static `unsupported`). Available pool is 100% plain -- this criterion has zero composite/ratio metrics anywhere. **Exceptions (8 available of 15 defined)**: also 100% plain single-DocType filtered counts. Source: `server-scripts/UCC Analytics - Criterion 2.py:1351-1543`.

| Chart id | Title | Type | Bucket | Classification |
|---|---|---|---|---|
| `v190-c2-overview-03` | Administration System Health | `funnel` | B | Bespoke — not table-backed |
| `v190-c2-overview-04` | People-to-Feedback Lifecycle | `lifecycle` | D | Plain aggregate |
| `v190-c2-overview-05` | Corporate Exception Funnel | `radar` | C | Plain aggregate |
| `v190-c2-overview-06` | Evidence Readiness Matrix | `matrix` | A | Bespoke — not table-backed |
| `v190-c2-211-04` | Workforce Control Readiness | `lifecycle` | B | Bespoke — not table-backed |
| `v190-c2-212-11` | Development Action Completion | `funnel` | D | Plain aggregate |
| `v190-c2-221-11` | Communication Record Completeness | `funnel` | D | Plain aggregate |
| `v190-c2-231-04` | Data Quality Readiness | `lifecycle` | B | Bespoke — not table-backed |
| `v190-c2-232-04` | Knowledge Repository Readiness | `lifecycle` | B | Bespoke — not table-backed |
| `v190-c2-241-11` | Improvement Action Linkage | `funnel` | D | Plain aggregate |
| `v190-c2-242-04` | Student Satisfaction Readiness | `lifecycle` | B | Bespoke — not table-backed |
| `v190-c2-243-04` | Staff Satisfaction Readiness | `lifecycle` | B | Bespoke — not table-backed |

#### Criterion 3 -- Agent Management

**Metrics pool: 56 total, 41 ever `available`** (35 plain + 6 composite `derived_sum`/`derived_percent`, which combine OTHER metrics' values rather than querying rows directly + 15 static `unsupported`). Available pool is 85% plain, 15% composite. **Exceptions (9 total)**: 7 plain + 2 composite (`ov-known-attention-total`, `c321-known-live-exceptions` -- both sums of other metrics, so a chart drawing on them can double-count). Source: `server-scripts/UCC Analytics - Criterion 3.py:1500-1820`.

| Chart id | Title | Type | Bucket | Classification |
|---|---|---|---|---|
| `v190-c3-overview-05` | Open Exception Profile | `radar` | C | Needs a closer look |
| `v190-c3-overview-06` | Source Readiness | `matrix` | A | Bespoke — not table-backed |
| `v190-c3-overview-07` | Agent Portfolio Status | `gauge` | D | Plain aggregate |
| `v190-c3-overview-20` | Agent Evidence Completeness | `lifecycle` | D | Plain aggregate |
| `v190-c3-overview-28` | Agent Target Achievement | `lifecycle` | D | Plain aggregate |
| `v190-c3-311-05` | Approval and Background Check | `radar` | D | Plain aggregate |
| `v190-c3-311-06` | Contract and NDA Readiness | `matrix` | B | Bespoke — not table-backed |
| `v190-c3-311-07` | Agent Listing and Status | `gauge` | D | Plain aggregate |
| `v190-c3-311-12` | Due-Diligence Evidence | `lifecycle` | D | Plain aggregate |
| `v190-c3-311-15` | Selection Rating Completeness | `gauge` | D | Plain aggregate |
| `v190-c3-311-20` | Contract Signature Coverage | `lifecycle` | D | Plain aggregate |
| `v190-c3-311-22` | NDA Completion Status | `matrix` | D | Plain aggregate |
| `v190-c3-311-27` | Selection Source Readiness | `funnel` | A | Bespoke — not table-backed |
| `v190-c3-311-28` | Selection Metric Readiness | `lifecycle` | B | Bespoke — not table-backed |
| `v190-c3-321-03` | Service Delivery Controls | `funnel` | D | Plain aggregate |
| `v190-c3-321-04` | Performance Evaluation Distribution | `lifecycle` | D | Plain aggregate |
| `v190-c3-321-06` | Complaints and Breaches | `matrix` | D | Plain aggregate |
| `v190-c3-321-15` | Contract Renewal Coverage | `gauge` | D | Plain aggregate |
| `v190-c3-321-22` | Monitoring Record Coverage | `matrix` | D | Plain aggregate |
| `v190-c3-321-27` | Evaluation Source Readiness | `funnel` | A | Bespoke — not table-backed |
| `v190-c3-321-28` | Evaluation Metric Readiness | `lifecycle` | B | Bespoke — not table-backed |

#### Criterion 4 -- Student Protection (non-admission charts only)

**Metrics pool (5 relevant sections): 44 total, 18 ever `available`** (18 plain, 0 composite, 26 static `unsupported` -- refund/movement workflows are largely unmapped). Available pool is 100% plain but *thin*: `c4-441-outcomes` in particular has only 1 of 9 metrics ever computed, so it renders near-empty regardless of backend. **Exceptions (4.6.1 only)**: 2 of 8 tagged ids ever surface after the availability filter, both plain. Source: `server-scripts/UCC Analytics - Criterion 4.py:1743-2323` (top-level `metrics`/`exceptions`, distinct from the separate `admission_intelligence` block the pilot chart uses).

| Chart id | Title | Type | Bucket | Classification |
|---|---|---|---|---|
| `c4-overview-flow` | Student Protection Control Flow | `lifecycle` | D | Plain aggregate |
| `c4-overview-readiness` | Student Control Readiness | `radar` | B | Bespoke — not table-backed |
| `c4-421-contract` | Student Contract Lifecycle | `lifecycle` | D | Plain aggregate |
| `c4-421-readiness` | Student Contract Readiness | `radar` | B | Bespoke — not table-backed |
| `c4-422-flow` | Fee and FPS Processing Flow | `lifecycle` | D | Plain aggregate |
| `c4-441-outcomes` | Refund Request Outcomes | `funnel` | D | Plain aggregate |
| `c4-461-lifecycle` | Attendance Intervention Lifecycle | `lifecycle` | D | Plain aggregate |
| `c4-461-risk` | Attendance Risk Profile | `radar` | C | Plain aggregate |

#### Criterion 5 -- Academic Quality

**Metrics pool: ~78 total, ~57 ever `available`** (~55 plain + 2 composite `attention_count`/`requirement_gap_count`, overview section only + ~21 static `unsupported`). Available pool is 96% plain. **Exceptions (8 fixed ids, `operational_exception_ids`)**: 100% plain single-DocType filtered counts, one `frappe.get_list` call each. Source: `server-scripts/UCC Analytics - Criterion 5.py:2475-3049`.

| Chart id | Title | Type | Bucket | Classification |
|---|---|---|---|---|
| `c5-overview-health` | Criterion 5 System Health | `matrix` | B | Bespoke — not table-backed |
| `c5-overview-exceptions` | Criterion 5 Exception Profile | `funnel` | C | Plain aggregate |
| `c5-511-readiness` | Course Design Evidence Readiness | `radar` | A | Bespoke — not table-backed |
| `c5-511-gaps` | Course Design Gap Profile | `funnel` | C | Plain aggregate |
| `c5-512-cycle` | Course Review Lifecycle | `lifecycle` | D | Plain aggregate |
| `c5-512-gaps` | Review Exception Profile | `funnel` | C | Plain aggregate |
| `c5-521-flow` | Planning Readiness Flow | `lifecycle` | B | Bespoke — not table-backed |
| `c5-521-gaps` | Planning Exception Profile | `funnel` | C | Plain aggregate |
| `c5-522-readiness` | Delivery Evidence Readiness | `radar` | A | Bespoke — not table-backed |
| `c5-522-gaps` | Delivery Exception Profile | `funnel` | C | Plain aggregate |
| `c5-531-risk` | Partnership Risk Profile | `funnel` | C | Plain aggregate |
| `c5-531-readiness` | Partnership Evidence Readiness | `matrix` | A | Bespoke — not table-backed |
| `c5-54-readiness` | Feedback Evidence Readiness | `radar` | A | Bespoke — not table-backed |
| `c5-54-gaps` | Feedback Exception Profile | `funnel` | C | Plain aggregate |
| `c5-55-readiness` | Assessment Evidence Readiness | `radar` | A | Bespoke — not table-backed |
| `c5-55-gaps` | Assessment Exception Profile | `funnel` | C | Plain aggregate |

#### Criterion 6 -- Quality Assurance

**Metrics pool: 53 total, 53 ever `available`** (41 plain flat count/sum/avg + 12 child-table traversal, walking a child table per parent record via `frappe.get_doc` -- single logical source but needs a parent/child join, not a flat `COUNT`; 0 composite/ratio, 0 unsupported). Source: `server-scripts/UCC Analytics - Criterion 6.py:1502-1700`.

| Chart id | Title | Type | Bucket | Classification |
|---|---|---|---|---|
| `v190-c6-overview-04` | Quality Calendar Completion | `lifecycle` | D | Plain aggregate (mostly) |
| `v190-c6-overview-06` | Source Readiness | `matrix` | A | Bespoke — not table-backed |
| `v190-c6-overview-14` | Quality Evidence Completeness | `matrix` | D | Plain aggregate (mostly) |
| `v190-c6-611-05` | Audit Findings by Severity | `radar` | D | Plain aggregate (mostly) |
| `v190-c6-611-06` | Corrective Action Closure | `matrix` | D | Plain aggregate (mostly) |
| `v190-c6-621-03` | Review Input Completeness | `funnel` | D | Plain aggregate (mostly) |
| `v190-c6-621-04` | Review Outputs | `lifecycle` | D | Plain aggregate (mostly) |
| `v190-c6-621-07` | Review Status Distribution | `gauge` | B | Bespoke — not table-backed |
| `v190-c6-631-06` | Improvement Action Status | `matrix` | D | Plain aggregate (mostly) |
| `v190-c6-641-06` | Provider Evaluation Outcomes | `matrix` | D | Plain aggregate (mostly) |
| `v190-c6-641-11` | Rating Completeness | `funnel` | D | Plain aggregate (mostly) |
| `v190-c6-653-03` | 5×5 Risk Matrix | `funnel` | D | Plain aggregate (mostly) |
| `v190-c6-653-07` | Risk Assessment Coverage | `gauge` | D | Plain aggregate (mostly) |

#### Criterion 7 -- Outcomes

**Metrics pool: 50 total, only 17 ever `available`** (15 plain + 1 plain-with-multi-field-AND + 1 composite coverage-rate + **33 (66%) static `unsupported`**). This is the sparsest criterion by far -- most cards drawing from this pool will show few or no real data points no matter what renders them. Source: `server-scripts/UCC Analytics - Criterion 7.py:1476-1600`.

| Chart id | Title | Type | Bucket | Classification |
|---|---|---|---|---|
| `v190-c7-overview-06` | Outcome Evidence Readiness | `matrix` | A | Bespoke — not table-backed |
| `v190-c7-overview-11` | Target Variance | `funnel` | D | Needs closer look (sparse) |
| `v190-c7-overview-14` | Outcome Review Status | `matrix` | D | Needs closer look (sparse) |
| `v190-c7-overview-28` | Underperforming Indicators | `lifecycle` | D | Needs closer look (sparse) |
| `v190-c7-overview-29` | Missing Measurements | `radar` | D | Needs closer look (sparse) |
| `v190-c7-overview-35` | Outcome Source Readiness | `funnel` | A | Bespoke — not table-backed |
| `v190-c7-711-03` | Indicator Definition Coverage | `funnel` | D | Needs closer look (sparse) |
| `v190-c7-711-04` | Indicator Ownership Coverage | `lifecycle` | D | Needs closer look (sparse) |
| `v190-c7-711-05` | Target Definition Coverage | `radar` | D | Needs closer look (sparse) |
| `v190-c7-711-06` | Actual Result Coverage | `matrix` | D | Needs closer look (sparse) |
| `v190-c7-711-12` | Benchmark Readiness | `lifecycle` | B | Bespoke — not table-backed |
| `v190-c7-711-14` | Underperformance Profile | `matrix` | D | Needs closer look (sparse) |
| `v190-c7-711-15` | Missing Result Profile | `gauge` | D | Needs closer look (sparse) |
| `v190-c7-711-31` | Measurement Source Readiness | `gauge` | A | Bespoke — not table-backed |
| `v190-c7-711-36` | Outcome Action Closure | `lifecycle` | D | Needs closer look (sparse) |
| `v190-c7-711-37` | Evidence Completeness | `radar` | D | Needs closer look (sparse) |
| `v190-c7-711-38` | Data Quality Profile | `matrix` | D | Needs closer look (sparse) |

#### Totals across all 106

- Plain aggregate: 44
- Bespoke — not table-backed: 37
- Needs closer look (sparse): 13
- Plain aggregate (mostly): 11
- Needs a closer look: 1
- **Total: 106**
