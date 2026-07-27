# Frappe Insights single-chart pilot — findings

**Status as of 2026-07-27: pilot code shipped, live bench verification pending.**
This is a feasibility spike, not a migration. Nothing here removes or replaces an
existing renderer, and nothing here decides the long-term rendering direction —
that call is Felix's, at the end of this doc.

I have no live access to `ucc-sms.orb.local` / `ucc.local` in this session, same
as every other phase this migration has gone through. Everything that requires
running a bench command, clicking through the Insights UI, or logging in as a
different user is written up as a precise procedure below, not a result — I'm
not going to fabricate a pass/fail for anything I can't actually observe.

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

**Result**: _pending_.

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

**Result**: _pending — this is the one finding that should most directly
drive the go/no-go decision below._

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
`gauge`) are a genuine unknown** — I don't know Insights v2.2.3's actual
supported chart type list without seeing the live UI, so I'm not going to
guess whether they map cleanly or would need custom work; that's a question
for a second, separate pilot if this one goes well, not something this
single-chart spike answers.
- Each plain-aggregate chart's data isn't a raw table scan — most go through
  the same kind of derived-grouping logic `build_admission_intelligence()`
  does (status filtering, field-candidate resolution across DocTypes that
  may or may not have the expected fieldname, multi-source joins in some
  criteria). Each one is its own small migration, not a bulk copy-paste.
- **If** filters need "separate wiring" per §4(a)'s likely answer, that's a
  second per-chart integration cost on top of the query itself — not a
  one-time platform cost.
- Net: full adoption is not a weekend project. A realistic estimate is
  low-to-mid tens of engineer-hours across query-building, filter wiring
  investigation, and permission-model reconciliation, before any visual
  polish — and that estimate could move substantially once §4(b)'s actual
  result is in, since a hard "no" on permissions could mean waiting on an
  Insights feature (or building a permission-aware proxy in front of it)
  before charts 2 through 35 are worth starting.

---

## 6. Recommendation, not a decision

This is Felix's call. What I'd weigh, once §1 and §4 have real answers:

- If §4(b) comes back with silent data exposure or a public-link bypass,
  that's a hard stop on wider adoption until Insights is reconfigured with
  real row-level security tied to the signed-in user, or embeds are served
  through a permission-checking proxy of our own — not something to work
  around chart-by-chart.
- If §4(b) comes back genuinely permission-safe and §4(a) shows filters need
  real but boundable wiring effort, the ~35 plain-aggregate charts become a
  legitimate incremental-migration candidate, most naturally folded into
  Phase 4 (since those charts' data already needs to move off the Server
  Scripts into real app code anyway).
- The ~20 bespoke chart types stay hand-rolled regardless — nothing here
  changes that.

I'd hold off recommending anything firmer than that until the two pending
results in §4 are in.
