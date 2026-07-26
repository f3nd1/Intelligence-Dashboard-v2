# Phase 3 Plan — Migrate Analytics frontend shell

Plan only. **No code written yet.** Per CLAUDE.md §9 Phase 3 goal: "Replace the Custom HTML Block
shell with a Frappe Desk Page while preserving the visual and navigation behaviour."

## 0. Two scope decisions this plan does not make silently

**Decision A — Analytics only, or the whole three-workspace shell?**

CLAUDE.md's phase is titled "Migrate **Analytics** frontend shell" and its exit criteria only mention
criterion shells. The deployed reality is one Custom HTML Block hosting three workspaces (Analytics,
Explore, Ask UCC) behind one switcher (`custom-html-block/JAVASCRIPT.js:266-437`). You said "just
moving the existing structure into the app properly" — which could mean either "move the Analytics
piece, per the phase's literal scope" or "move the one page as it exists today, all three tabs."

**Recommending Option A — Analytics only** for this phase:
- Matches CLAUDE.md §9 Phase 3's literal title and exit criteria exactly.
- Smaller, more reviewable diff (§1.1.7) — Analytics alone is lines 1-437 + 2144-2703 of the deployed
  JS (~1,000 lines); the full page is 3,343.
- **Nothing changes for real users either way.** The legacy Custom HTML Block stays fully live and
  unmodified regardless of which option is chosen — only a new, separate, not-yet-linked-to-anywhere
  Desk Page is added. "Keep navigation the same" is trivially satisfied for actual users because
  their page doesn't change at all this phase.
- Explore (`:2704-3065`) and Ask UCC (`:438-2114`) get their own migration later — Ask UCC has an
  explicit phase (Phase 6); Explore has no named phase in CLAUDE.md at all, worth flagging separately
  (Decision B below).

If you want the full three-workspace shell moved in one phase instead, say so — it's a larger but
still mechanical port, not a redesign either way.

**Decision B — does Explore ride along?**

CLAUDE.md's phase list has no phase for the Diagram Explorer. It's tightly coupled to Analytics (same
visual catalogue, same `LIVE_VISUAL_EXPANSION` data), but it's a distinct ~1,300-line module
(`custom-html-block/JAVASCRIPT.js:2704-3065`). Recommending **defer it** — same reasoning as Decision
A (smaller diff, nothing live changes), revisit once Analytics is confirmed working. Flagging rather
than assuming, since "no named phase" isn't the same as "in scope now."

**This plan below is written assuming Option A (Analytics only, Explore deferred).** Everything
scales down in a straightforward way if you pick otherwise — say so before I write code.

## 1. What Phase 3 required work actually is (CLAUDE.md §9)

- Create a proper Desk Page for UCC Intelligence.
- Move HTML construction into maintainable templates/components.
- Move CSS into app assets.
- Move JavaScript into app assets and modules.
- Preserve criterion selection, tab navigation, filters, loading states, readiness, diagnostics, and
  lazy loading.
- Preserve responsive behaviour.
- Remove reliance on `root_element`, which is specific to Custom HTML Blocks.
- Use Frappe page lifecycle correctly.
- Avoid global namespace pollution.

## 2. What gets built, mapped to real legacy code (re-verified this session, legacy dirs unchanged)

| # | Required-work bullet | Source (verified) | Built at (proposed) |
|---|---|---|---|
| 1 | Desk Page | Nothing today — Custom HTML Block only | `ucc_intelligence/ucc_intelligence/sophia/page/<page-name>/` — **needs one bench round-trip, §5** |
| 2 | HTML → templates/components | `custom-html-block/HTML.html:1-7` (Analytics section: platform chrome + 7 empty `[data-dashboard-panel]` divs) | Built as a DOM-construction function in the page's JS, mirroring `dashboardShellMarkup`/`mountUnifiedDashboards` (`JAVASCRIPT.js:2181-2194`) — the legacy HTML file itself is nearly empty (all markup is JS-generated), so there's very little static HTML to "templatize"; the real content to port is the JS that builds it |
| 3 | CSS → app assets | `custom-html-block/CSS.css` (2,105 lines). Analytics-relevant families: `.ucc-platform` shell, `.ucc-demo-*`, `.ucc-live-*`, `.ucc-card-*`, `.ucc-readiness-strip`, `.ucc-perm-notice`, `.kpis`, brand tokens `#26345B`/`#CE9E5D`. **Finding this session: 222 of 1,254 selector groups have no `.ucc-`/`.aja-` scoping prefix at all** (e.g. `.badge`, `.chart`, `.error`, `.good`, `.controls`) — see §4. | `ucc_intelligence/public/css/platform.css` — straight copy first, then verify it's loaded page-scoped, not site-wide (§4) |
| 4 | JS → app assets/modules | Platform shell (`:266-437`) + unified dashboard engine (`:2144-2703`), **excluding** Ask UCC (`:438-2114`) and Explore (`:2704-3065`) per Decision A. Shared runtime (`:1-265`) is **already ported** in Phase 2 (`ucc_intelligence/public/js/shared.js`) — reused, not re-copied. | `ucc_intelligence/public/js/analytics/` — split into the same logical pieces the legacy file already has (markup builders, chart plugins, state/API, renderers, orchestration), per the module inventory in `docs/architecture/current-state.md` §2 |
| 5 | Preserve criterion selection/tabs/filters/loading/readiness/diagnostics/lazy-loading | All of `current-state.md` §2.1-§2.4 | Ported logic, behaviour-identical — this is the bulk of the actual work, not new design |
| 6 | Preserve responsive behaviour | CSS media queries within `CSS.css` (not yet inventoried by breakpoint — will be during the port) | Carried over with the CSS |
| 7 | Remove `root_element` reliance | `JAVASCRIPT.js:2147` (`typeof root_element!=="undefined"?...`) and the same pattern in every module | Replaced with the Page's own `wrapper` parameter, scoped queries throughout — the single biggest mechanical change, touches every DOM lookup |
| 8 | Frappe page lifecycle | N/A today | Standard `frappe.pages['<name>'].on_page_load` / `on_page_show` — replaces the "runs immediately on script evaluation" pattern the legacy engine uses (`current-state.md` §2.1), which has no real analogue in a Frappe Page and needs a deliberate re-entry/lifecycle decision (§4) |
| 9 | No global namespace pollution | Legacy already keeps this fairly tight — `window.UCCShared`, `UCCLiveAnalytics`, `UCCChartPlugins`, `UCCLiveVisualDefinitions`, all `UCC`-prefixed | Same small set carried over; no new globals planned |

## 3. Files left untouched

Same standing list: `custom-html-block/` (all files, **fully live and unmodified** — this is the
whole point of Decision A, nothing here changes), `server-scripts/` (all 17, including the 7
criterion scripts — Phase 3 does not touch the API layer, only what calls it), `src/`, `dist/`,
`archive/`, `reference/`, `documentation/`. The new Desk Page calls the **existing**
`ucc_analytics_criterion_N` Server Scripts exactly as the legacy JS does — no request/response shape
changes. That's Phase 4.

## 4. Two technical findings from re-inspecting the legacy files this session

**CSS: don't use site-wide inclusion.** 222 of 1,254 selector groups in `CSS.css` have no
`.ucc-`/`.aja-` scoping class anywhere in the rule (`.badge`, `.chart`, `.controls`, `.error`, `.good`,
`.empty`, and similar generic names). Today this is contained because a Custom HTML Block's CSS field
only affects the one page/workspace hosting it. If the ported CSS were loaded via Frappe's site-wide
`app_include_css` hook, it would apply to **every** Desk page across Felix's bench — including
`erpnext`, `hrms`, `educ_sg`, and every other installed app — a real regression the legacy deployment
doesn't have today. **Plan: load the CSS page-scoped** (bundled with the Page itself, not via
`app_include_css`), so the blast radius stays exactly what it is today. Not renaming the 222
selectors — that's a real fix but it's "redesign," explicitly out of scope this round; page-scoping
neutralises the risk without touching a single selector.

**JS lifecycle: the legacy engine runs on script evaluation, a Frappe Page runs on `on_page_load`.**
The deployed engine has no `DOMContentLoaded` listener — it executes top-to-bottom the moment the
script loads (`current-state.md` §2.1). A Frappe Page's JS file is loaded once per session and
`on_page_load(wrapper)` fires each time the page is navigated to; navigating away and back does
**not** reload the script. This needs a deliberate re-entry guard (the legacy `dataset.xReady==="1"`
pattern still works, just needs to key off the Page's own wrapper instead of a global
`#uccIntelligencePlatform` lookup) and a decision about whether `on_page_show` should re-check
`ucc_dashboard_access` on every visit or only once per session. Proposing **once per session**
(matches the legacy behaviour — it's not designed to be revalidated on every tab switch either), flag
if you want it stricter.

## 5. What's needed from you / your bench (genuinely can't proceed without this)

Same caution as Phase 1's app scaffold and Phase 2's DocType: a Frappe Page's generated files
(`<name>.json` schema, whether a `.py` controller is required in the installed version, exact
JS-loading convention) are version-specific — CLAUDE.md §7 says these must come from the installed
Frappe version, not be hand-authored. **One bench round-trip needed:**

```bash
bench make-page ucc_intelligence_analytics
```

(name is a proposal — open to a different one; it becomes the route). Then paste back:

```bash
find ucc_intelligence/ucc_intelligence/sophia/page -type f    # confirm it landed under sophia/, matching Phase 2's module
cat ucc_intelligence/ucc_intelligence/sophia/page/ucc_intelligence_analytics/*.json
cat ucc_intelligence/ucc_intelligence/sophia/page/ucc_intelligence_analytics/*.py
```

I'll write the actual HTML-construction/engine/CSS port against the real generated shape once I have
it, the same way Phase 2's `api.py`/DocType were completed against your confirmed real paths rather
than guessed ones.

**Also needed, both are proposals not decisions:**
- **Confirm or rename the route**: `ucc_intelligence_analytics` was chosen to be unambiguous; given
  the app's real title is "Sophia" (not "UCC Intelligence" — CLAUDE.md's prose still says "UCC
  Intelligence workspace" throughout, written before the rename), a name like `sophia-analytics`
  might read better to staff. Your call.
- **Whether a Workspace/menu shortcut gets added now.** Phase 1 descoped the role-restricted
  workspace entirely ("out of scope, not worth tracking further"). Without any menu entry, the new
  page is reachable only by typing its route directly — fine for your own testing, but worth deciding
  now rather than rediscovering it later. Proposing: skip it again this phase, you'll use the direct
  URL for now, matching the same "don't build UI navigation infra we're not ready to commit to" call
  from Phase 1.

## 6. Verification plan

**Reused, not reinvented** — `documentation/TESTING_GUIDE.md`'s existing "Platform shell" checklist
already covers exactly this transition's concerns and gets re-run against the new page:

- Dashboard selector shows Criteria 1-7.
- UCC Blue and Gold have readable contrast.
- Mobile layout remains usable.
- (Its "only Criterion 5 selectable" line is stale from an earlier deployment stage — current
  deployed state has all seven live; the check becomes "all seven selectable, matching
  `current-state.md`'s confirmed behaviour.")

**New, specific to this phase:**

- Side-by-side manual check against the live Custom HTML Block: same criteria, same subcriteria per
  criterion, same tab order, same filter controls, same KPI/chart/table layout, at desktop and at
  least one mobile width.
- Every behaviour in CLAUDE.md §9 Phase 3's own exit criteria (§8 below) checked explicitly, not
  assumed from "it looks right."
- The specific fragilities `current-state.md` §6 already flagged must survive the port unchanged
  (not fixed, not silently broken): `panelInsertPoint`'s heading-text DOM anchor, `metricRows`'
  title-regex data-source selection, the C5 5.4/5.5 cache-defeating behaviour. Porting these as-is is
  correct for this phase; "fix" is a future, separate decision.
- Network trace: confirm only the selected criterion fetches on initial load (matches legacy — six of
  seven should show their loading-placeholder state, not fetch).

**What I can verify without a bench, same pattern as Phases 1-2:**

- Any file that's meant to be a straight copy (e.g. CSS before scoping-related edits) gets diffed
  against the legacy source to prove nothing drifted, the same way `shared.js`'s port was diffed
  byte-identical in Phase 2.
- `node --check` / `py_compile` on everything new.
- The existing regression suite (`tools/validate_package.py`, the two `test_dashboard_access.py`
  variants, `test_permission_notice.js`, `test_roll_fallback.js`) stays at its 94/101 baseline,
  proving Phase 3 didn't touch anything Phase 0-2 already covers.
- What I **cannot** verify without the bench: anything requiring a rendered page, a real
  `frappe.call`, or a browser — i.e. most of the actual exit criteria. That verification is yours to
  run and report back, same as Phases 1-2.

## 7. Archive plan

Nothing moves to `archive/`. The Custom HTML Block stays fully live throughout Phase 3 — per Decision
A, real users see zero change. Legacy removal is Phase 13, after all phases and full parity sign-off.

## 8. Exit criteria — copied verbatim from CLAUDE.md §9 Phase 3 (not yet attempted)

- [ ] All seven criterion shells render from the app.
- [ ] No Custom HTML Block is required for the staging version.
- [ ] Navigation and selected criterion persistence work.
- [ ] Hidden criteria are not available through direct UI manipulation.
- [ ] Desktop and supported mobile widths are visually checked.

## 9. Rollback

Nothing here touches `custom-html-block/` or `server-scripts/` — a git revert of the Phase 3 commits
is sufficient on the code side. The new Page is inert until someone navigates to its route; there's no
migration/data step to roll back on the site side (a Page record is trivial to remove via
`bench --site <site> console` → delete the Page doc, or just `bench migrate` after reverting the code,
same as any other doctype/page removal).

---

## 10. What I need from you before writing code

1. **Decision A** (§0): Analytics-only Desk Page this phase (recommended), or the full three-workspace
   shell in one go?
2. **Decision B** (§0): Explore deferred (recommended), or ride along with Analytics?
3. **The `bench make-page` round-trip** (§5) — can't write the actual Page files without it.
4. **Route name** (§5) — `ucc_intelligence_analytics`, `sophia-analytics`, or your preference.
5. **Workspace/menu shortcut** — skip for now (recommended, matches Phase 1), or add one this phase.

Everything else in this plan (page-scoped CSS loading, once-per-session access-check revalidation,
porting fragilities as-is rather than fixing them) has a stated default and doesn't block starting —
say so if any default is wrong.
