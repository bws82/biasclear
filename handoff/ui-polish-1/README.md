# UI polish, first pass (for Jarvis's review)

- Base: biasclear/biasclear main `2b39303652d54607ee6837743f9801e3aecf5ce4`
- Branch (local, Claude's cloud session): `ui-polish`, HEAD `d0f97c10ac16897e11cb227a8a646b4858aa21c2`
- Diff: `ui-polish-1.patch` (one commit, `git am`-ready), sha256 `d0a29b348caf111f956862050db1b8797094221d8d3a1820673cf8ff7a73ed00`
- Not pushed to biasclear/biasclear, not merged, not deployed.

## Files

| File | Change |
|---|---|
| `site/pages/index.html` | "Check your own text" moves first in the sample row (DOM and tab order), plus a zero-height row break after it |
| `site/css/checker.css` | Filled ink button, outlined once pressed; full-width row on phones; 44px touch targets on coarse pointers; Cancel border ink-3; forced-colors border 2px |
| `site/css/site.css` | Touch only: menu links and the Paper/Ink buttons are at least 44px tall |

No content, rule, engine, guard, script, workflow, DNS or settings change.

## What changed and why

1. **Obvious first action.** Before, "Check your own text" was a small outline button at the right end of the row. It came after the four samples in the tab order, and on mobile it measured 166x36. Now it's filled and first: on desktop 190x44, on mobile a full-width 356x47. In the tab order it now comes right after the Paper/Ink switch.
2. **Touch.** On `(hover:none) and (pointer:coarse)`, these are all at least 44px tall: the sample chips, the highlight switch, the edit links, the editor buttons, the menu links and the Paper/Ink buttons.
3. **Contrast.** All text tokens already pass AA: ink-3 is 5.42:1 on light and 6.28:1 on dark, and focus is 5.85 and 8.92. The Cancel button's border was 1.5:1. It now uses ink-3.
4. Focus rings, the loupe, light/dark tokens and all copy are unchanged.

## Checks (run on HEAD d0f97c1)

- `node --test site/test/site.test.mjs`: 27 passed, 0 failed
- `NODE_PATH=$(npm root -g) node --test site/test/browser.test.mjs` (Chromium): 16 passed, 0 failed
- Build: 6 pages, rules 2.0.0a5
- Own-text flow, desktop and mobile: the click opens the editor and focus lands in `TEXTAREA#own`. Filled text goes under the loupe.
- No horizontal scroll at 1366, 1280, 390 or 360 px.

## Trade-off to judge

The sample text sits lower on first load:

| Viewport | Before | After | Change |
|---|---|---|---|
| 1366x768 | 500 px | 512 px | +12 px; still fully on the first screen |
| 390x844 phone | 564 px | 651 px | +87 px |

Most of the phone shift comes from the 44px sample rows (two rows) and the new full-width button. The fix would be a single scrolling row of samples on phones. I left that out of this pass on purpose: it hides options, and it changes the loupe's first screen. Your call.

## Not changed, noted

- While the loupe is still reading, "2 MOVES / 43 WORDS" counts up and can differ from the chip's total ("An ad · 6"). That is checker.js behaviour, so I left it alone.
- On screens 900 px and narrower, GitHub is in the footer only. That's on purpose; a comment in site.css says so.

## Screenshots

`before/` and `after/` hold the same set of views in JPEG. The desktop views are 1280x860, scaled to 2/3. The mobile views are 390x844 at 2x, with touch emulated.
- `home-*`: the home page.
- `own-*-1`: the page after clicking "Check your own text".
- `focus-desktop`: the keyboard focus after 14 presses of Tab.
