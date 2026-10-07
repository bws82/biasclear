# Jarvis: independent review of the BiasClear public preview (locked)

From Claude (BiasClear PM), __NOW__ (system clock). The owner is present: he pressed run. No live calls.

**Your read access:** this folder's `CHANNEL-claude-jarvis.md`, this brief, and `__EVID__/` (a clone of the public repository github.com/biasclear/biasclear at the exact commit under review, `__COMMIT__`, pull request #__PR__). Nothing else is needed. You may run local commands that need no network and write nothing outside `__EVID__/` (for example `cd __EVID__/repo && PYTHONPATH=src python3 -m pytest -q` or `PYTHONPATH=src python3 -m biasclear "some text"` if Python 3.10 or newer and pytest are on this Mac). Say what you ran.

**What BiasClear is.** It marks the persuasion moves in a text, names each one, and says which words carry it. It points at wording, never at people or sides. It is not a fact-checker and gives no truth score. One rule pack (`rules/biasclear-rules.json`, 43 rules) drives two engines that are tested to give identical results: Python (`src/biasclear/`) and TypeScript (`packages/engine/`). The website (`site/`) runs the TypeScript engine inside the visitor's browser; nothing typed is sent anywhere. The project's flag is "same rules for everyone": no rule may name, or contain a word built from, a person, party, ideology, faith, country, program, outlet or institution (`AGENTS.md`, "Neutrality"), and a suite of swapped pairs (`tests/test_symmetry.py`) checks that swapping one side's name for the other's gives the same result.

**The step under review.** This pull request is the whole public preview: the rules, both engines, the fairness suite, the website, the README and the project docs. Merging it publishes the site at biasclear.github.io/biasclear, clearly labelled Preview. `__EVID__/diffstat.txt` lists every file against the repository's current main. The owner merges; your verdict informs his call and does not replace it.

**What Claude's own checks already did** is in `__EVID__/repo/CHANGELOG.md` (top section) and `rules/RULE_CHANGES.md`. Please don't take them on trust.

**Please check, in this order:**
1. **Neutrality.** Does any rule, word list or exclusion in `rules/biasclear-rules.json` name, or build on the name of, a person, party, ideology, faith, country, program, outlet or institution, in any form (plural, -ist, -ism, anti-, slur blends)? Does `tests/test_neutrality_lint.py` actually catch that if someone adds one?
2. **Symmetry.** Can the same sentence be marked when it is about one side and not when it is about the other? Give concrete pairs and the rule involved. Try politics (left and right), religion (several faiths and none), nationality, gender, age and profession.
3. **Can a bad case pass?** Pick the three rules you think are weakest. For each, show a text that should be marked and is not, or one that is marked and should not be.
4. **Truth in copy.** Is every claim and number in `README.md`, `site/pages/*.html`, `CHANGELOG.md` and `packages/engine/README.md` true of the code? Flag anything that overclaims ("every", "never", "all", accuracy, privacy promises).
5. **Privacy and security.** Any real person's name outside the paper citation, any personal information, secret, key or token, or any request the site makes to another server? Does the privacy page say exactly what is true? Any regular expression that can be made to run for seconds on a short input?
6. **First impression.** Someone clicks through from a post on X and sees the README top and the site's home page. Is it clear, honest and finished within five seconds? What would make a skeptic close the tab?
7. **GO / NO-GO** for the exact next step: "The owner merges pull request #__PR__ and the Preview goes live."

Answer in `__ANSWER__` with `STATUS: DONE` on line 1, then your verdict line, then HIGH / MEDIUM / LOW findings, each with file:line and, for rules, the exact text you tested. Keep it as short as the findings allow. Your verdict is your own.

— Claude (BiasClear PM)
