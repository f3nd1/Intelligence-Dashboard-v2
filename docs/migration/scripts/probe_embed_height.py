"""What the embed measured, and what the dashboard actually is.

NOT a bench script -- this one runs in the BROWSER. Open a criterion tab with
an embedded dashboard, open Chrome DevTools (View > Developer > JavaScript
Console), paste the block below the line, and press Enter.

It answers the question two deploy rounds could not: was the height wrong
because the arithmetic was wrong, or because the measurement was?

WHAT THE ANSWERS MEAN

  tallestMatch  the dashboard's real content height. This is what the frame
                should be, plus a little padding.
  firstMatch    what querySelector alone would have returned. If this is tiny
                and tallestMatch is large, the two are DIFFERENT elements --
                AppSidebar.vue's link list matches the same selector and comes
                first, which is the bug fixed on 2026-08-04.
  frameHeight   what the frame was actually set to. Should be within ~40px of
                tallestMatch.
  reachable     false means Sophia cannot see into the frame at all. Then the
                height falls back to filling the window and every other number
                here is meaningless -- that would be the real fault.
  scrollsInside true means the dashboard is still taller than its frame.

Copy from here down:
--------------------------------------------------------------------------
(() => {
  const f = document.querySelector("iframe.ucc-embed-frame");
  if (!f) return "No embedded dashboard on this tab.";
  let d; try { d = f.contentDocument } catch (e) { return "blocked: " + e.message }
  if (!d) return { reachable: false };
  const scrollers = [...d.querySelectorAll("#app .overflow-y-auto")];
  const heights = scrollers.map(n => ({
    container: n.className,
    child: n.firstElementChild ? n.firstElementChild.className : "(empty)",
    height: n.firstElementChild
      ? Math.round(n.firstElementChild.getBoundingClientRect().height) : 0,
  }));
  const inner = scrollers.find(n => n.scrollHeight > n.clientHeight + 1);
  return {
    reachable: true,
    candidates: heights,
    firstMatch: heights.length ? heights[0].height : 0,
    tallestMatch: Math.max(0, ...heights.map(h => h.height)),
    frameHeight: f.style.height,
    windowHeight: window.innerHeight,
    scrollsInside: Boolean(inner),
    caption: document.querySelector("[data-embed-scroll]")
      ? (document.querySelector("[data-embed-scroll]").textContent || "(no scroll notice)")
      : "(no caption)",
  };
})()
--------------------------------------------------------------------------

The same numbers also go into the tab's own diagnostics log on every load, as
an `embed_height` line -- this script is for reading them without opening it.
"""
