# Phase 3 Plan — Migrate Analytics frontend shell

**Status: code written (2026-07-26), self-verified without a bench — see §11. Not yet run on the real
site.** Per CLAUDE.md §9 Phase 3 goal: "Replace the Custom HTML Block shell with a Frappe Desk Page
while preserving the visual and navigation behaviour." Proceeded on the stated defaults (Decision A:
Analytics only; Decision B: Explore deferred) — Felix said "go ahead" without objecting to either.

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

---

## 11. What was built (2026-07-26)

Route came back as `sophia-analytics` (Felix's real bench output), folder `sophia_analytics` — same
hyphen/underscore split as the Phase 2 DocType. No `.py` controller was generated (confirmed: this
Frappe version doesn't require one for a standard client-side Page).

**Files, all at the confirmed real path**
`ucc_intelligence/ucc_intelligence/sophia/page/sophia_analytics/`:

- `sophia_analytics.json`, `__init__.py` (×2, one per new folder level) — the real bench-generated
  files, reproduced here so this repo's copy is complete, same reasoning as Phase 2's DocType.
- `sophia_analytics.js` — the actual port.
- `sophia_analytics.css` — byte-identical copy of `custom-html-block/CSS.css`.

**How the port was done, not just described**: manual retyping of ~1,300 dense lines risks silent
transcription errors, so this wasn't hand-copied through the chat interface. The platform-shell
(`custom-html-block/JAVASCRIPT.js:266-435`) and unified-engine (`:2144-2703`) modules were extracted
programmatically by exact line range, and exactly two mechanical substitutions were applied via
scripted string replacement with an assertion that the *pre-change* text matched the live source
verbatim before any substitution ran (so a silent drift in the legacy file would have raised an error,
not produced a wrong port):

1. `root_element` / document-wide `#uccIntelligencePlatform` lookup → the Page's own wrapper-derived
   element, turning each top-level IIFE into a named function (`initPlatformShell(root)`,
   `initAnalyticsEngine(platform)`) called once from `on_page_load`.
2. `method:"ucc_dashboard_access"` → `method:"ucc_intelligence.api.get_dashboard_access"` — the one
   deliberate behavioural change, wiring this page to Phase 2's ported access-check instead of the
   legacy Server Script, which is exactly what Phase 2 built it for.

Diffing the pre/post transformation confirmed **no other line changed** — not chart renderers, not
`metricRows`, not `callApi`, not the failure-ladder in `chartForLive`, none of it. This matches the
finding in §2 of this plan: once the DOM shape is reproduced identically, the vast majority of the
engine needed zero changes because it already addresses everything through `platform.querySelector`,
not `document`.

**HTML shell**: rebuilt from `HTML.html`'s actual Analytics section (verified against the live file,
not from memory), with exactly the two Decision-A/B trims applied — the changelog/version button
dropped (no changelog system ported) and the Explore/Ask workspace nav buttons dropped (those
workspaces don't exist on this page; a button that shows a blank panel is worse than not having it).
Everything else — brand copy, all seven criterion mount divs, the dashboard `<select>`, the
shell-collapse toggle — is unchanged from the deployed markup.

**`sophia_analytics.css`**: page-scoped by file-colocation convention (same basename as the page,
same folder), not `app_include_css` — this is what neutralises the 222-unscoped-selector finding from
§4 without renaming a single selector.

## 12. Verification performed without a bench

`tools/test_sophia_analytics_page.py` (14 checks, all passing) — re-extracts the same exact ranges
from the live `custom-html-block/JAVASCRIPT.js` and `HTML.html`, re-applies the same two
transformations, and diffs the result against the committed page files. This is a permanent,
re-runnable check: if the legacy source or the ported file drifts later, this catches it — the same
discipline as Phase 2's contract-parity test. Also: `node --check` on the assembled JS, a JSON
round-trip check confirming the embedded shell HTML matches the intended trimmed markup exactly, and
a byte-diff confirming the CSS copy is identical. Full existing regression suite re-run, baseline
unchanged (94/101).

**Not verified — needs the real bench**: everything in CLAUDE.md §9 Phase 3's actual exit criteria
(§8) requires a rendered page — all seven criteria selectable and switching correctly, filters,
loading states, readiness banners, diagnostics modal, responsive behaviour at real widths, and
specifically whether `frappe.require("/assets/ucc_intelligence/js/shared.js", boot)` resolves to the
right built asset path in this Frappe version (the one part of this port with no legacy precedent to
extract from, since the Custom HTML Block never needed to load a separate script this way).

## 13. What's needed from you now

1. `bench build --app ucc_intelligence` (this page's CSS/JS are new files; a new/changed page's assets
   need a build before they'll serve).
2. `bench --site ucc-sms.orb.local migrate` (picks up the Page record if it isn't already active from
   the Desk UI creation — likely a no-op, worth confirming).
3. Visit `/app/sophia-analytics` and report: does it render at all, does `shared.js` load correctly
   (check the browser console for a 404 on the `frappe.require` path), do the seven criteria switch
   correctly, does the KPI/chart/table layout match the live Custom HTML Block side by side.
4. If `frappe.require`'s asset path is wrong, tell me what the browser console actually shows and I'll
   correct it — that's the one line in this port with no exact precedent in the legacy file to verify
   against.

## 14. Fix: `shared.js` 404 — wrong source-tree nesting level (2026-07-26)

Felix reported a fresh (non-cached) page load 404ing on `GET /assets/ucc_intelligence/js/shared.js`,
breaking `frappe.require`'s callback chain (the 404 HTML page gets `eval`'d as JS, throwing
`Unexpected token '<'`).

**Root cause**: Phase 2 placed `shared.js` at `ucc_intelligence/public/js/shared.js` — the outer
app-repo level, sibling to the inner `ucc_intelligence/ucc_intelligence/` package. That matches
CLAUDE.md §7's illustrative tree, which shows `public/` as a sibling of the inner package — but §7
itself warns "the exact scaffold should be generated by the installed Frappe version... not a
licence to manually create an incompatible scaffold." Felix confirmed via real `bench build` output
("Linking `.../ucc_intelligence/ucc_intelligence/public` to `./assets/ucc_intelligence`") that the
actual convention links the **inner** package's `public/` folder to assets, not the outer one. A file
placed one level too high is never linked, hence the 404.

**Fix**: `git mv ucc_intelligence/public ucc_intelligence/ucc_intelligence/public`. No content change —
`shared.js` itself is untouched. The served URL (`/assets/ucc_intelligence/js/shared.js`, used by both
`frappe.require` in `sophia_analytics.js` and the Phase 2 smoke test) does not change, since it was
already written against the correct *served* path — only the *source-tree* path was wrong.

Corrected the stale path in `docs/migration/phase-2-plan.md` and `docs/migration/parity-matrix.md`
(both said `ucc_intelligence/public/js/shared.js`).

**Needed from you**: `bench build --app ucc_intelligence` again, then a hard-refreshed page load —
confirm `shared.js` now serves (200, not 404) and the platform shell/engine boot without the
`Unexpected token '<'` error.
