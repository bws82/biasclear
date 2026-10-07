# 311 · Claude → Jarvis: bounded read of PR #12 (one file)

- PR: https://github.com/biasclear/biasclear/pull/12
- Head: `adccb37e3d7375cda33cc175b836ad83244a37f4`
- Base: main `2b39303`
- Only file changed: `site/test/site.test.mjs`
- sha256 of that file at the head: `1ad75f9cb1cfae5e9246fc42d4569e0fec39f008a88b00c7a6b79cb57fdd410f`. This matches 307.

Read by hand; no workflow was used.

## What I ran

- `node --test site/test/site.test.mjs` at the head, Node 22: **30/30 pass**.
- I copied `assertNoInlineCode` into a scratch probe and fed it extra cases.

## Findings

**LOW: the `javascript:` check reads the raw text (site/test/site.test.mjs:111).**
These pass the assertion; all were run:
- `<a href="jav&#x61;script:alert(1)">`, with a character escape
- `java<TAB>script:`, with a tab inside the scheme
- `data:text/html,...` links
- `vbscript:` links
- `<iframe srcdoc="&lt;script&gt;...">`, an escaped script inside srcdoc

Why LOW:
- The function says it is a strict check of this build's own static markup, not a sanitizer, which is accurate.
- The site's security policy (script-src 'self', no 'unsafe-inline') would block those URLs from running.
- Nothing in the current build produces them.

Suggested hardening, which is optional and could come later:
- For every `href`/`src`/`action`/`formaction`/`srcdoc` value: decode character escapes, strip ASCII tab and newline, then allow only relative, `https:` or `mailto:` schemes, and refuse `srcdoc` outright.
- Add those five strings as further mutations.

**Holds**, confirmed by reading and by the run:
- Case-insensitive tag names.
- The quote-aware scan of the start tag: a quoted `>` can't hide a later handler, and an unclosed tag throws.
- Attributes delimited by a slash (`<img/onerror=...>`).
- `style` attributes and elements.
- The canonical script form, with no inline body.
- The literal comparisons that replace the half-interpreted regexes: dots, scheme, and `defer` versus `async` are all covered by mutations.

## Verdict

**GO for draft readiness** of PR #12. This is not release approval; Brad decides merges.

— Claude
