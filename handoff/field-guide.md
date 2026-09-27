# The BiasClear Field Guide

*Rule pack: frozen core v1.2.0 (repository commit ddad685). Every example, honest rewrite and false alarm below was run through the engine and checked.*

## Before you start

**What a move is.** A move is a way of writing that gets a reader to accept a point without being shown why it is true. "Everyone knows," "studies show," "act now," "any reasonable person": each of these asks for agreement and offers something other than evidence in return. A move can sit inside a sentence whose facts are all correct. It is about how the sentence is built, not about whether its claims are true.

**Rules point at structure, not people.** Each BiasClear rule looks for the shape of a move in the words on the page. A flag says "this phrasing has the shape of a move." It does not say the writer is dishonest, biased or wrong, and it says nothing about the writer's side of any question. Good writers use these phrases by accident, and careful writers sometimes use them fairly. That is why every entry below includes a false alarm.

**This guide says what the rules miss.** The rules match fixed wording. They catch the common phrasings and let other phrasings through. Every entry ends with a plain account of what gets past that rule: synonyms, contractions, curly apostrophes, word order, and the same move made without any trigger words. A scan with no flags means none of these phrasings appeared. It does not mean the text is free of persuasion.

**How to read an entry.** Each entry gives the move's plain name and a one-line summary, how it works on a reader, what its tier means, two examples with the flagged words in bold and an honest version that keeps the facts, a false alarm (a fair sentence) with a note on whether the engine flags it, and what the rule misses.

**The three tiers.** Persistent Influence Theory (PIT) sorts moves into three tiers. Tier 1 is ideological: the move sets what feels like common sense. Tier 2 is psychological: the move works through feelings. Tier 3 is institutional: the move borrows the standing of an office or official source. The tier describes how a move works, not how serious it is.

**Coverage.** This guide covers 40 of the 42 rules in core v1.2.0. Two general Tier 3 rules, Credential as Proof and Institutional Neutrality, are not written up yet. No accuracy figures appear here, because none have been measured on independent text.


---

## Tier 1: Ideological

Moves that decide what counts as common sense before any evidence is weighed: agreement, tradition, momentum or a quiet verdict stands in for a reason.


### Tier 1 · General

*These rules run on every scan.*


#### Consensus as proof

Rule `CONSENSUS_AS_EVIDENCE` (Consensus Substituted for Evidence)

*It treats the fact that many people agree as if that agreement proved the claim, and never shows the evidence the agreement should rest on.*

**How it works.** Most of us trust what the people around us believe, and that is usually a sensible shortcut. This move uses that trust. It tells the reader who agrees but not why, so disagreeing feels like standing apart from the group, and the reader never gets anything to check.

**The tier, in plain words.** This is a Tier 1 (Ideological) move because it presents a claim as common sense that everyone already shares, which leaves the reason for believing it out of view.

**Examples.**

1. **Everyone knows** the new phone is worth the upgrade, so there is no reason to wait for reviews.  
   *Honest version:* The new phone's battery lasted about two days in the maker's own test, and its camera is faster than last year's model; whether that is worth the upgrade depends on the phone you have now.

2. Among home builders **it is widely accepted** that a basement dehumidifier prevents mold, so every house on the street needs one.  
   *Honest version:* A basement dehumidifier keeps the air drier, and mold grows less in dry air; if your basement stays damp after rain, one may help.

**False alarm.** In the garden club's vote on the spring plant swap, most people chose Saturday: 41 members voted for Saturday and 9 for Sunday.  
The claim is only about what members prefer, so the vote is the evidence, and the sentence gives the full count. It does not use agreement to prove some other fact.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** The rule looks for a fixed list of phrases, so the same move gets through when it is worded differently. "Any gardener will tell you that tomatoes go in after the last frost" and "Nobody serious disputes that the new bus schedule is better" both lean on agreement alone, and neither is flagged. The rule also skips "the consensus" whenever the next word is "view", so "The consensus view among riders is that the new bus schedule is better" gets through even though it makes the same move.


#### Proof with no source

Rule `CLAIM_WITHOUT_CITATION` (Authoritative Claim Without Citation)

*It states a claim as settled by pointing to studies, data, or experts, but never says which ones.*

**How it works.** Phrases like "studies show" or "data shows" borrow the weight of research without showing any of it. The reader hears that someone checked, so the claim feels settled. With no source named, there is nothing to look up and no way to see what was actually found.

**The tier, in plain words.** This is a Tier 1 (Ideological) move because it makes a claim feel like common sense that everyone already knows is backed by research, so it seems odd to ask for the source.

**Examples.**

1. **Studies show** that tomatoes grow better when you water them at dawn, so the garden club is moving its watering hour.  
   *Honest version:* The garden club is moving its watering hour to dawn. The county extension office's vegetable guide recommends morning watering so leaves dry before evening.

2. **Data shows** the new bus schedule has cut wait times, so riders on the east line should be happier this fall.  
   *Honest version:* The transit office's first monthly report on the new schedule lists the average wait on the east line as nine minutes, down from twelve, so riders should see shorter waits this fall.

**False alarm.** Our backyard rain gauge data shows that two inches of rain fell on Tuesday.  
The sentence names its source (the speaker's own rain gauge) and gives the measured amount, so a reader knows exactly where the number came from. The engine still flags it because it only recognizes formal citation shapes, such as (Author, 2024), [1], or Table 2, and not a source named in plain words.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** Two ways the same move gets past the rule. (1) Other wording. The rule matches a fixed list of phrases, so "Studies have shown...", "A recent study found...", "It has been proven...", and "Scientists found..." are not flagged, though they make the same unsourced appeal. (2) Anything shaped like a citation within about 120 characters turns the rule off, whether or not it points to a real source. A bare "[1]" with no reference list is enough. So is an unrelated phrase like "3 buses at 7", which the citation check mistakes for a legal citation.


#### Dismissing by label

Rule `DISSENT_DISMISSAL` (Dissent Dismissed by Label)

*It waves away an opposing view by giving it a name like "misinformation" or "debunked" instead of showing why it is wrong.*

**How it works.** A label such as "fringe" or "debunked" sounds like a finished verdict, so the reader assumes the checking has already happened somewhere else. The reader gets the conclusion but never sees the reason. It also puts a social cost on the other view, so agreeing with it starts to feel careless.

**The tier, in plain words.** This is Tier 1 (Ideological) because the label decides which views count as reasonable before anyone weighs the evidence.

**Examples.**

1. Riders who say the new Route 9 timetable makes them late are spreading **misinformation**.  
   *Honest version:* Riders say the new Route 9 timetable makes them late, but the transit office's arrival logs show buses reached the downtown stop within two minutes of schedule on 95 of 100 weekday trips last month.

2. Some members think the new compost is making the tomatoes wilt, but that idea **has been thoroughly debunked**.  
   *Honest version:* Some members think the new compost is making the tomatoes wilt, but in the club's test beds this summer, plants with and without the compost wilted at the same rate.

**False alarm.** The rumor that the bake sale was canceled has been debunked: the school calendar, posted Monday, still lists it for Saturday, May 3.  
The word 'debunked' comes with its evidence in the same sentence: a named, checkable source and a specific date. Here the label sums up a rebuttal. It does not replace one.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** The rule matches a fixed word list, so the same move gets through when it uses other labels. "That forecast of a wet spring is a crackpot idea from the usual complainers" is not flagged, and neither are words like "quackery" or "nonsense". The rule also misses plurals of its own phrase. "No serious expert thinks the phone upgrade slows the camera" is flagged, but "No serious experts think..." is not, because the pattern has no "s?" after scientist, researcher, expert or scholar.


#### Inevitability as argument

Rule `INEVITABILITY_FRAME` (Inevitability Framing)

*It says an outcome is bound to happen, so there is no point in weighing it or pushing back.*

**How it works.** It swaps the question "is this a good idea?" for "this is already happening." If the result is coming anyway, checking the evidence feels like wasted effort and objecting feels foolish. The reader gets a sense of momentum in place of a reason.

**The tier, in plain words.** This is a Tier 1 Ideological move because it sets what counts as common sense: the outcome is treated as a settled fact about the future, so questioning it seems out of step instead of reasonable.

**Examples.**

1. Fifteen-minute service on every route is **the inevitable direction** for the city, so the bus board should approve the new schedule tonight.  
   *Honest version:* I think the bus board should approve fifteen-minute service on every route tonight. Ridership counts and the cost of each route would show whether that case holds.

2. Online sign-ups are replacing paper sheets for the school bake sale, and **there is no stopping this**, so the committee should drop the paper list.  
   *Honest version:* Online sign-ups are replacing paper sheets for the school bake sale. I think the committee should drop the paper list, and a count of how many volunteers still use it would show whether that case holds.

**False alarm.** The plumber's report found rust along the seams of our 22-year-old water heater, and she said a leak is the inevitable outcome if we do not replace it this year.  
The inevitability claim names its source (the plumber's report) and gives the physical evidence behind it (a 22-year-old tank rusting at the seams). It also names a condition ("if we do not replace it"), which is the opposite of saying nothing can be done. The engine still flags "the inevitable outcome" because this rule matches the phrase and does not check for a cited source.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) Small wording changes get past it. The rule only accepts the full phrase "there is no". So "there's no stopping this" is not flagged, and neither is "You can't stop this change" (it looks for "can't stopping", which nobody writes). 2) Common phrasings that are not on its lists also pass. "It is only a matter of time before every garden club drops the rose show" and "Folding phones are the inevitable future" both go unflagged. The first has no listed trigger. In the second, "future" is not one of the nouns the rule accepts after "inevitable" (direction, trend, shift, outcome, and so on). The adverb "inevitably" is not covered either.


#### Because we always have

Rule `APPEAL_TO_TRADITION` (Appeal to Tradition / Precedent Inertia)

*It uses the fact that something has long been done one way as the reason to keep doing it.*

**How it works.** A long habit feels safe, so pointing to it makes a choice sound already settled. The sentence says the practice is old, but not why the practice works. The reader gets a feeling of certainty with no evidence behind it.

**The tier, in plain words.** This is a Tier 1 (Ideological) move because it treats the usual way of doing things as common sense that needs no defense.

**Examples.**

1. The garden club should hold the plant sale in May again, because **we've always done it this way**.  
   *Honest version:* The garden club should hold the plant sale in May again: the last three May sales sold out, and most seedlings are ready to plant by then.

2. The bake sale has always been in the school lobby, and **departing from tradition would be unwise**.  
   *Honest version:* The bake sale has always been in the school lobby, and it should stay there: parents walk through the lobby at pickup, and last year's sale raised $600 there.

**False alarm.** Departing from established practice is dangerous here: the breaker must be off before anyone touches the outlet, or the person doing the repair can get a shock.  
The sentence gives its reason right away. The practice is defended by what it prevents, a shock, and not by how old it is. The engine only matches the phrase and cannot tell that a real reason follows.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) Typography: the rule only matches a straight apostrophe. The same sentence with a curly one ("because we’ve always done it this way") is not flagged, and most typeset or word-processed text uses curly apostrophes. It also misses "Longstanding practice dictates..." written as one word, because the rule needs "long-standing" or "long standing". 2) Paraphrase: the rule only knows a few fixed phrases, so the same move in everyday words gets through. Examples: "That's how the bake sale has always been run, so why change it now?", "We always do it this way", "It's always been this way", or "We have held the plant sale in May for twenty years, so it stays in May." None of these were flagged.


#### Splitting the difference

Rule `FALSE_EQUIVALENCE` (False Equivalence)

*It treats a strong case and a weak case as equals, so the weaker one looks just as good.*

**How it works.** Being balanced sounds fair, so readers relax when they hear both sides are equal. The phrase goes in place of comparing the evidence, and the gap between a careful inspection and a quick glance disappears. The reader leaves thinking the question is open when the evidence mostly points one way.

**The tier, in plain words.** It is Tier 1 (Ideological) because it sets a common-sense rule, that fair means the answer lies halfway between the two sides, before anyone weighs the evidence.

**Examples.**

1. One roofer climbed into the attic and found rot in twelve rafters, and the other looked from the driveway, but **both sides make good points** about whether the roof needs work.  
   *Honest version:* One roofer climbed into the attic and found rot in twelve rafters; the other looked only from the driveway. The attic inspection is the stronger evidence, and it says the roof needs work.

2. Riders logged the Route 9 bus arriving late on 40 of 45 mornings, and one driver says it usually runs on time, so **the truth lies somewhere in the middle**.  
   *Honest version:* Riders logged the Route 9 bus arriving late on 40 of 45 mornings. One driver says it usually runs on time, but the 45-morning log is the fuller record, and it shows the bus is usually late.

**False alarm.** Two identical rain gauges in the same yard read 1.1 and 1.3 inches, so the answer is somewhere in the middle, about 1.2 inches.  
The two readings come from the same kind of instrument in the same place, so they deserve equal weight. Taking the midpoint is a sound way to combine them, and the sentence shows both numbers.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) The rule only catches a few fixed phrases. A plain 'opinions differ' gets through even when the facts are lopsided: 'One roofer found rot in twelve rafters and the other looked from the driveway; opinions differ on whether the roof needs work' is not flagged. 2) Small wording changes get past the regex. It wants 'side' or 'sides' and the verbs has, have, make, makes, present, or presents, so past tense or other nouns are missed: '...so both camps made fair points' is not flagged. The rule also cannot see the move when it is built from the layout alone, such as two quotes given equal space with no weighing of the evidence.


#### Vague majority claims

Rule `SOFT_CONSENSUS` (Soft Consensus Manufacturing)

*It says that most people, or a growing pile of evidence, back a claim, but never says who they are or what the evidence is.*

**How it works.** Phrases like "the vast majority agree" or "a growing body of evidence suggests" sound careful and measured, so readers take them as a summary of real findings. No survey, count, or source is given, so the reader cannot check how many people agreed or what the evidence was. The wording lends the claim the weight of agreement without showing the agreement.

**The tier, in plain words.** This is Tier 1 (Ideological) because it presents a claim as something most people already accept, which quietly sets what counts as common sense before any evidence is shown.

**Examples.**

1. **The vast majority of our garden club members agree** that the new compost mix works better than the old one.  
   *Honest version:* At the March meeting, eighteen of the twenty-two garden club members said the new compost mix worked better than the old one.

2. A **growing body of evidence suggests** that sealing the attic saves more on heating than replacing the windows.  
   *Honest version:* Our home energy audit last fall estimated that sealing the attic would cut heating costs by about 15 percent, and new windows by about 5 percent.

**False alarm.** The vast majority of the 40 bake sale volunteers agree on a 9 a.m. start, according to the sign-up sheet they filled out on Monday.  
The sentence gives the group size (40 volunteers) and names where the answer came from (Monday's sign-up sheet), so a reader can check it. The engine still flags it because its citation check only looks for formal citation formats, such as (Table 2), [1], or p. 12. It does not recognize a source named in plain words. A version that cites '(Table 2)' next to the same phrase is not flagged.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) Verbs outside the rule's list get through. "The overwhelming majority of shoppers prefer the new phone over last year's model" is not flagged, because the rule only fires on verbs like agree, support, believe, accept, or endorse. "Prefer" is not on the list, and no other rule catches this sentence either. The rule also stops looking after five words between "majority of" and the verb, so a longer version slips past too: "The vast majority of the people who ride the early bus every single morning agree..." 2) A number that happens to look like a citation switches the rule off. "As of 3 March 2025, the vast majority of riders agree the new bus schedule is easier to follow" is not flagged, because the date "3 March 2025" matches the engine's citation pattern (number, word, number). The same sentence without the date is flagged.


#### Promises in place of results

Rule `ASPIRATIONAL_DEFLECTION` (Aspirational Deflection)

*It offers a goal or a promise where the reader expected a result.*

**How it works.** Phrases like "our goal is to" and "we are committed to" sound like good character, and readers tend to give good intentions the same credit as outcomes. When two or three of these phrases pile up, they fill the space where a number, a date, or a checked result would go. The reader comes away with a warm impression and nothing to check.

**The tier, in plain words.** It is Tier 1 (Ideological) because it quietly treats a stated intention as a result, so the reader starts to take the promise as the record.

**Examples.**

1. **Our goal is to** keep every bus on the new city schedule running on time, and we are committed to reliable service for every rider.  
   *Honest version:* On the new city schedule, 88 of the 100 bus trips we checked last month left on time; we want to reach 95, and we will post next month's count at each stop.

2. With the new phone upgrade, **we strive to deliver** the longest battery life in its class, and we are fully committed to quality.  
   *Honest version:* In our lab test of video playback, the new phone ran 21 hours on one charge, two hours longer than last year's model; we have not tested it against other brands.

**False alarm.** Our goal is to plant 200 trees along Mill Road this year; the garden club has planted 140 so far, and we are committed to finishing the last 60 by November.  
The goal comes with the actual count (140 of 200) and a deadline, so the reader can check progress for themselves. The intention is labeled as an intention, and the result is stated right beside it. The engine still flags it because the rule counts two aspirational phrases and does not look for the evidence next to them.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) One phrase is not enough. The rule only fires when at least two aspirational phrases appear together (min_matches=2), so a single promise gets through. Example: "With the new phone upgrade, we strive to deliver the longest battery life in its class." The engine does not flag it. 2) The rule only knows certain wordings, so contractions and close synonyms slip past it. Example: "We're committed to quality, and our aim is to give you the longest battery life in its class." The engine does not flag it: "We're" does not match "we are", "aim" is not on the rule's list of goal words, and "give" is not on its list of verbs. The same goes for phrasing like "our team is dedicated to" (the rule expects "are", not "is") or "we hope to". Both cases were confirmed on the v1 engine.


### Tier 1 · Media

*These rules run only when a scan is set to the media domain (or auto). In a general scan they never fire.*


#### Opinion dressed as news

Rule `MEDIA_EDITORIAL_AS_NEWS` (Editorializing Disguised as Reporting)

*It slips the writer's verdict into a news description, so a judgment reads as a plain fact.*

**How it works.** One loaded word, such as "misguided" or "so-called", hands the reader a conclusion before any facts arrive. Because it sits inside the description and not in a quote, nobody is named as holding that view, so there is no source to check. The reader absorbs the verdict with the facts and never gets to weigh it.

**The tier, in plain words.** It is Tier 1 (Ideological) because the verdict comes in as part of the basic description, so it quietly becomes the common-sense starting point instead of a claim to be tested.

**Examples.**

1. The transit office announced **the misguided schedule plan** on Monday: weekday buses on Route 9 will run every 20 minutes instead of every 15.  
   *Honest version:* The transit office announced a new schedule plan on Monday: weekday buses on Route 9 will run every 20 minutes instead of every 15. Two riders who spoke at the public hearing said the longer wait would make them late for work.

2. **The so-called upgrade program** lets customers trade in a two-year-old phone for $150 off a new model.  
   *Honest version:* The upgrade program lets customers trade in a two-year-old phone for $150 off a new model. The store's own terms say the credit applies only to phones in working condition.

**False alarm.** After the league moved the final to a Tuesday night, the head coach told reporters it was "a controversial decision" that would keep many families home.  
The judgment is in quotation marks and credited to a named role, the head coach. It reports what a source said instead of giving the writer's own verdict, and the reader can see who holds the view.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** The rule only catches a word from a fixed list, such as "misguided" or "so-called", that comes right after "the", "a" or "an" and is followed, with at most one word in between, by a noun from a short list such as plan, program or decision. A possessive in front gets past it ("the city's misguided schedule plan"). So does a second word before the noun ("the misguided new weekday schedule plan"), or a loaded word or noun that is not on the list ("a baffling new bus timetable"). A judgment carried by verbs and adverbs also goes unflagged, as in "The garden club quietly slipped a fee increase into its spring newsletter." The rule runs only when the media domain (or auto) is selected, so the same sentence checked in the general domain is not flagged.


#### False balance

Rule `MEDIA_FALSE_BALANCE` (False Balance / Both-Sidesism)

*It sets a weak or long-rejected claim next to a well-tested one, as if the two had equal standing.*

**How it works.** A "some say this, experts say that" sentence looks fair, so readers assume both sides carry similar weight. The sentence never says how much evidence stands behind each side. The reader comes away thinking the question is still open when it is not.

**The tier, in plain words.** It is Tier 1 (Ideological) because it changes what readers take as common sense: a settled question starts to feel like an open debate.

**Examples.**

1. **A few insist that caterpillar stripes predict a hard winter, yet scientists who study weather point out** the stripes show no link to snowfall.  
   *Honest version:* Caterpillar stripes do not predict a hard winter; scientists who study weather have compared the stripes with snowfall records and found no link.

2. **Some claim that overnight charging ruins a phone battery in a month, while researchers who test batteries disagree**.  
   *Honest version:* Overnight charging does not ruin a phone battery in a month; battery test labs found that modern phones stop charging once the battery is full.

**False alarm.** Some say the new bus schedule cuts wait times, while researchers who timed 400 trips note the average wait fell by two minutes (Route Study, 2025).  
The researchers back up the claim instead of arguing against it. They give a measurement and name the source, and nobody's weak claim is being raised to equal standing. The rule matches the sentence's shape ("some say ... while researchers ... note") without checking whether the two sides actually disagree or whether one of them is fringe. This rule does not use the engine's citation check, so the cited source does not stop the flag.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) The expert word is not on the rule's short list. "Some say a rainy spring means a dry summer, but most meteorologists disagree." is not flagged, because the rule only knows words like scientists, experts, researchers, doctors, economists and scholars. Words such as meteorologists, forecasters, engineers or mechanics get past it. 2) The move is built from layout rather than one "some say ... while experts ..." sentence. "Do caterpillar stripes predict winter? Folk forecasters read the bands each fall, and weather scientists read ocean data. Both sides make their case below." is not flagged, even though it treats folklore and science as equal sides. The same happens with split headlines, back-to-back quotes or equal paragraph space. The rule also only runs when the domain is "media" or "auto". The same sentences checked as "general" are never flagged. It also misses when the weak claim runs longer than about 80 characters before the "while/but/yet" turn.


#### Scare quotes

Rule `MEDIA_SELECTIVE_QUOTATION` (Scare Quotes / Selective Quotation)

*It puts quotation marks around a single ordinary word to hint that the word is doubtful or silly, without saying why.*

**How it works.** Quotation marks normally mean "someone said this." Around one plain word, they also carry a wink: the writer doubts it, but never says so. The reader picks up the doubt without being shown a fact to weigh, and there is no stated claim to check or dispute.

**The tier, in plain words.** It is a Tier 1 (Ideological) move because it sets what counts as common sense: the quotation marks treat a word as obviously doubtful, so the reader takes the doubt as a given instead of as a claim that needs support.

**Examples.**

1. Monday brings an **"improved"** bus schedule with "shorter" waits between stops.  
   *Honest version:* Monday brings a new bus schedule. The transit office calls it an improvement and says waits between stops will be shorter.

2. The bake sale committee promised **"homemade"** treats, but the "fresh" cookies came in store boxes.  
   *Honest version:* The bake sale committee promised homemade, fresh treats, but the cookies came in store-bought boxes.

**False alarm.** The garden club's planting guide says seed packets marked "hardy" or "perennial" should survive the winter.  
The quotation marks show the exact labels printed on the seed packets. They mark words being named, not words being mocked, and the sentence gives its source (the planting guide).  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) One scare quote gets through. The rule needs at least two quoted words before it fires, so The team's "rebuilding" season ended with four wins and twelve losses. is not flagged, even though the one quoted word does the same job. 2) Some quote shapes fall outside the pattern: multi-word phrases ("fan favorite" flavor, "limited edition" frosting), hyphenated words ("top-rated" roofer, "same-day" repair) and single quotes ('improved' schedule) all went unflagged in testing. The rule only matches one run of letters inside double or curly quotes.


#### Loaded quote verbs

Rule `MEDIA_ASYMMETRIC_ATTRIBUTION` (Asymmetric Source Attribution)

*It reports one side with a plain verb like 'said' and the other with a doubting verb like 'claimed' or 'insisted', so the reader learns whom to trust from the verbs alone.*

**How it works.** 'Said' reads as a simple record of what someone said. 'Claimed', 'alleged' and 'insisted' add a hint of doubt or stubbornness. Readers pick up that hint before they weigh what either side actually said, so one account starts out sounding like fact and the other like an excuse, and no evidence has been offered for either.

**The tier, in plain words.** This is a Tier 1 (Ideological) move. The verbs quietly decide whose account counts as the normal, common-sense version and whose counts as the suspect one.

**Examples.**

1. The parent volunteers said the bake sale raised $400, but the treasurer **claimed** the total was lower and insisted on a recount.  
   *Honest version:* The parent volunteers said the bake sale raised $400. The treasurer said her count came out lower and asked for a recount.

2. The contractor said the roof repair was finished on schedule, while the homeowner **alleged** the gutters still leak and insisted the crew come back.  
   *Honest version:* The contractor said the roof repair was finished on schedule. The homeowner said the gutters still leak and asked the crew to come back.

**False alarm.** The garden club admitted 12 new members this spring, and nine of them claimed a free seed packet at the first meeting.  
Neither verb reports what anyone said. 'Admitted' means let in and 'claimed' means picked up. The sentence treats nobody's account differently from anyone else's.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) One loaded verb is enough to tilt a story, but the rule needs at least two before it fires. The basic form of the move gets through: "The coach said the team trained hard all season, but the rival coach claimed the schedule was unfair." (Not flagged.) 2) The rule only looks for a fixed list of past-tense verbs. Headline-style present tense ("one buyer claims ... and insists ...") and loaded verbs that aren't on the list ("riders complained ... and grumbled ...") pass without a flag. The rule also counts loaded verbs anywhere in the text and never checks whether one side got 'said' and the other did not, so it can't tell an unfair contrast from even-handed wording.


### Tier 1 · Financial

*These rules run only when a scan is set to the financial domain (or auto). In a general scan they never fire.*


#### Counting only the winners

Rule `FIN_SURVIVORSHIP_BIAS` (Survivorship Bias)

*It draws a lesson from the people or things that succeeded and leaves out the ones that failed or dropped away.*

**How it works.** The survivors are easy to see, so a habit they share looks like the reason they survived. The ones that failed are missing from the picture, and they may have had the same habit. The reader sees a pattern but never gets the comparison that would show whether it means anything.

**The tier, in plain words.** It is a Tier 1 (Ideological) move because it makes "look at who made it" feel like common sense, so a sample with the failures left out passes for the whole story.

**Examples.**

1. Of the home repair shops on Main Street, the **top firms all use** same-day callbacks, so same-day callbacks must be what keeps a repair shop in business.  
   *Honest version:* Of the home repair shops still open on Main Street, the busiest three offer same-day callbacks. Two of the four shops that closed in the last five years offered them too, so callbacks alone do not explain which shops lasted.

2. **A $40 investment in a backyard rain barrel would now be worth** $300 in saved water, based on the garden club members who still use theirs.  
   *Honest version:* Garden club members who still use their $40 rain barrels say each one has saved about $300 in water. We did not hear from members whose barrels cracked or who stopped using them, so the typical saving may be lower.

**False alarm.** A survey of all 60 bakeries that opened downtown since 2015, including the 38 that later closed, found that the top firms all use one flour supplier, and so did most of the bakeries that closed (Table 2).  
The survey counts the bakeries that closed as well as the ones that stayed open, and it says the shared habit does not set the winners apart. It also points to its table. That is the opposite of survivorship bias, but it uses the same words, "top firms all use."  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) If the group is named with a noun the rule does not list, it gets through. For example: "The five bakeries still open downtown all bake their own bread, so baking in-house is how a bakery lasts." The rule only knows words like funds, stocks, companies, firms, managers, investors and traders, so "bakeries" is not caught. Neither are shops, teams or schools. 2) In the "top firms all use" form, a past-tense verb gets through. For example: "...the top firms all used same-day callbacks..." That form only accepts present-tense verbs such as use, have and share. It is also a financial-domain rule. It runs only when text is checked as "financial" or "auto", so a check in the general domain never flags either example.


#### Cherry-picked timeframe

Rule `FIN_CHERRY_PICKED_TIMEFRAME` (Cherry-Picked Timeframe)

*It picks the start and end dates that make a result look good, and leaves out what other date ranges would show.*

**How it works.** A number tied to a date range looks exact, so readers tend to trust it. But the writer chose where the range starts and stops, and a different choice could show a flat or opposite result. The date range carries the argument, and the reader never sees the longer record needed to judge it.

**The tier, in plain words.** This is Tier 1 (Ideological) because it quietly sets the frame: the chosen window becomes the normal way to look at the numbers, and no one is asked whether that window is fair.

**Examples.**

1. **Since March, the school bake sale fund has gained 40%**, so the new cookie table is paying off.  
   *Honest version:* The bake sale fund grew 40% from March to May, after a slow winter; across the whole school year it is up about 5%, so it is too early to credit the new cookie table.

2. **In the last two months, the Route 9 bus beat** every other line for on-time arrivals.  
   *Honest version:* Route 9 had the best on-time record of any line in the last two months; over the full year it ranks fourth of seven lines.

**False alarm.** Since 1998, the club's first year, plant sales averaged 4% growth a year; that figure covers every sale on record.  
The range starts at the club's first year and covers the full record, so the writer did not pick the start date to flatter the result. It also says plainly that no years were left out.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) The rule only catches the 'since' / 'over the past' form when a month name, a four-digit year, or a named event (such as 'the dip') follows. A count of years gets past it: "Over the past three years, the garden club's seed fund returned 30%." is not flagged. Week-based windows ("in the last six weeks") and verbs outside its list (won, rose, grew) also get through. 2) Swap the words and the move gets past the rule: "From the March low to today, the phone's resale value is up by a third." uses 'from ... to' instead of 'since' and 'a third' instead of a percent sign, so it is not flagged. The rule also runs only when text is scanned in the financial or auto domain. In the general domain it does not fire at all.


---

## Tier 2: Psychological

Moves that work on feelings (fear, shame, belonging, frustration, hope) so that a reaction takes the place of a reason.


### Tier 2 · General

*These rules run on every scan.*


#### Only two choices

Rule `FALSE_BINARY` (False Binary / False Dilemma)

*It presents a situation as a choice between two options when others exist.*

**How it works.** Once a reader sees two options, their attention goes to picking one, and they stop asking whether there are more. Usually one option is made to look bad, so the other feels like the only sensible choice, even though nothing has been shown to rule out a third path. The frame does the persuading, not the evidence.

**The tier, in plain words.** This is a Tier 2 (Psychological) move because it relies on the pressure of a forced choice, often a fear of the worse option, rather than on reasons.

**Examples.**

1. **Either we raise the bake sale prices this year or** the class trip gets cancelled.  
   *Honest version:* The class trip is short on funds this year. Raising bake sale prices is one way to close the gap; a second sale day or a parent sponsor could also help.

2. When your old phone slows down, there are **only two options**: buy the new model or live with the lag.  
   *Honest version:* Your old phone has slowed down. Buying the new model is one fix; clearing storage or replacing the battery may also help.

**False alarm.** The 12 bus runs on either the weekday schedule or the Sunday schedule; there is no Saturday service.  
The timetable really does have just two schedules, so naming both is an accurate description, not a forced choice. Nothing is left out and nobody is being pushed toward an option.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** The rule looks for set phrases such as "either ... or", "only two options" or "no middle ground". A forced choice written without them gets through, for example "Raise the bake sale prices this year, or the class trip is off." Small changes also slip past: one extra word ("only two real choices"), or a long stretch between "either" and "or", as in "Either we raise the bake sale prices this year for every cookie, brownie, and lemon bar on the table or the class trip gets cancelled."


#### Fear and hurry

Rule `FEAR_URGENCY` (Fear-Based Urgency)

*It pushes the reader to act fast by pointing to disaster or a closing deadline, not by showing what is actually at stake.*

**How it works.** Fear and time pressure narrow attention. When a reader feels something terrible will happen, or that the chance is about to vanish, stopping to check the claim can feel like a risk in itself. The words carry the weight, so the reader never learns how likely the harm is, how big it is, or what waiting would really cost.

**The tier, in plain words.** This is a Tier 2 (Psychological) move because it works on the reader's fear and sense of alarm instead of giving reasons they can weigh.

**Examples.**

1. **Act now**, or you'll be stuck with a slow, outdated phone for years.  
   *Honest version:* Your phone is three years old and runs the newest apps slowly; if that bothers you, the upgrade offer runs through Friday.

2. Leave that small roof leak alone and the damage to your attic will be **irreversible**.  
   *Honest version:* The roofer found one loose shingle over the attic; fixing it costs about $150, and a slow leak left all season can rot the boards underneath.

**False alarm.** The regional weather service forecasts the river will crest at 18 feet on Tuesday and warns that this could bring devastating flooding to low-lying streets (Flood Bulletin No. 2026-09).  
The strong word describes a specific forecast. The sentence names the source, the expected water level, the day, and the streets at risk, so the reader can check the warning and judge it for themselves. Nothing in it tells the reader to act without evidence.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) Curly apostrophes. The rule's phrases are written with a straight apostrophe, so "If we don’t act this week, the school bake sale won’t have enough treats to sell" (typographic ’) gets through. The same sentence with a straight ' is flagged. Word processors and phones often insert curly quotes automatically. 2) Pressure that avoids the listed words. Scarcity and countdown phrasing such as "Only three upgrade slots left, and this price disappears at midnight. Don't wait." raises no flag. Neither does vivid imagery like "Picture your family shivering in a dark, cold house next winter because you put off the furnace check." The rule matches set phrases like "act now", "too late", "irreversible" and "complete collapse", not the pressure itself.


#### Shame as pressure

Rule `SHAME_LEVER` (Shame or Social Pressure as Lever)

*It pushes you to agree by suggesting that only a foolish, careless, or bad person would disagree.*

**How it works.** The sentence swaps a reason for a judgment about the reader. Disagreeing now looks like admitting you are unreasonable or letting people down, so going along feels safer than asking for proof. The claim itself never gets any support. What gets pressed is your wish to be seen as sensible and decent.

**The tier, in plain words.** This is a Tier 2 (Psychological) move because it works through feelings of shame, guilt, and belonging rather than through evidence or through appeals to authority.

**Examples.**

1. **Any reasonable person** would upgrade to the new phone this fall.  
   *Honest version:* The new phone comes out this fall, and its battery lasts about six hours longer than last year's model, so upgrading may make sense if battery life matters to you.

2. **How could anyone possibly** skip the school bake sale after all the work the parents put into planning it?  
   *Honest version:* The parents put a lot of work into planning the school bake sale, which runs Saturday from 9 to noon, and the money raised will pay for new library shelves.

**False alarm.** How could anyone possibly carry the new couch up those stairs? We measured, and the stairwell is two inches too narrow.  
This is a practical question about moving furniture, not a judgment of anyone's character, and the next sentence gives the measurement that answers it. No one is being shamed into agreeing.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** The rule only matches a short list of fixed phrases, so peer pressure written in ordinary words gets through. For example, "Every other family on the street has already signed up for the bake sale, so don't be the one house that lets the kids down" is not flagged. Swapping in a synonym also gets past it: "Any sensible person would upgrade to the new phone this fall" is not flagged, because the "any ___ person" phrase only matches "reasonable", "rational", "intelligent", "educated", and "decent".


#### Emotion instead of evidence

Rule `EMOTIONAL_SUBSTITUTION` (Emotional Appeal Substituted for Argument)

*It uses strong feeling words where the reasons or facts behind a point should be.*

**How it works.** A strong feeling arrives faster than a reason, and once it is there it feels like a reason. Words like "heartbreaking" or "outrageous" tell the reader how to feel about a fact before the fact is shown, and "speaks for itself" skips the showing entirely. The reader comes away with a reaction but not the details they would need to check it.

**The tier, in plain words.** This is a Tier 2 (Psychological) move because it works by pressing on the reader's feelings, such as sorrow, anger or alarm, rather than by setting what counts as common sense or by leaning on an authority.

**Examples.**

1. The new bus schedule is **simply heartbreaking** for everyone who rides Route 4.  
   *Honest version:* The new bus schedule drops the last two evening runs on Route 4, so riders who finish work after 9 p.m. will need another way home.

2. The garden club wants members to chip in for new raised beds after the storm. **The devastation speaks for itself**.  
   *Honest version:* The garden club wants members to chip in for new raised beds after the storm, which split 12 of the 20 beds.

**False alarm.** It was heartbreaking when the late frost hit the garden club's seedlings: 40 of the 60 trays were lost overnight.  
The feeling comes with the fact that explains it. The reader gets the count (40 of 60 trays, lost overnight) and can judge the loss for themselves. The emotion sits next to the evidence and does not replace it.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) The rule only matches set phrases, so a small change in wording gets past it. "It is heartbreaking to see the Route 4 evening runs disappear from the new bus schedule" is not flagged, because "heartbreaking" is caught only when followed by "that," "how" or "when," or when it comes after "simply," "truly," "absolutely" or "utterly." Feeling words that are not on the list also pass: "The new bus schedule is a gut-wrenching blow to everyone who rides Route 4" is not flagged. 2) A vivid scene can do the same job without using any feeling word at all. "Picture a nurse standing alone at a dark bus stop at 10 p.m., waiting for a Route 4 bus that no longer comes" puts one imagined rider where the rider counts should be, and the engine does not flag it.


#### Moral high ground

Rule `MORAL_HIGH_GROUND` (Moral Authority Claim)

*It turns a practical disagreement into a test of character, so that anyone who disagrees looks like a bad person instead of just someone with a different view.*

**How it works.** The sentence does not give a reason for its view. It says that good people already hold it. Most readers want to see themselves as decent, so agreeing starts to feel like the price of staying decent. The question about the facts never gets weighed, because objecting now feels like confessing a flaw.

**The tier, in plain words.** It is a Tier 2 (Psychological) move because it works on the reader's wish to be seen as a good person, and on the shame of seeming otherwise, rather than on any evidence about the question.

**Examples.**

1. **Any caring person would agree** that the bake sale belongs on Saturday, not Friday.  
   *Honest version:* I think the bake sale belongs on Saturday, not Friday: last year's Saturday sale drew twice as many families, and more parent volunteers are free that day.

2. Keeping the late bus on the schedule is not a budget question; **it is simply a matter of basic decency**.  
   *Honest version:* Keeping the late bus on the schedule costs about $300 a week, and I think it is worth it: about 40 riders use it each night, and most have no other ride home after late shifts.

**False alarm.** Any responsible professional should know to shut off the water before replacing a faucet, as the plumbing guide explains on p. 14.  
This sentence states a basic safety step that anyone can check, and it names where to look it up. Nobody on the other side is being cast as a bad person, and no open question is being closed off. 'Responsible' here means competent at the job. It is not a moral verdict on people who disagree.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) Saying it without the stock phrase: "Only someone who doesn't care about their neighbors would vote to cut the late bus" makes the same move, but the rule does not flag it because none of its fixed wordings appear. 2) Small wording changes: "Any caring parent would agree..." gets through because "parent" is not on the rule's list of nouns (person, citizen, professional, and so on). "It's simply a matter of basic decency" also gets through when it is typed with a curly apostrophe (it’s), because the rule only matches a straight one.


#### Questioning the critic's competence

Rule `COMPETENCE_DISMISSAL` (Competence-Based Dismissal)

*It answers a disagreement by saying the people who disagree don't understand the subject, and never gets to what they actually said.*

**How it works.** The reader hears that the critics are out of their depth and stops weighing what they said. No evidence is offered about the question itself. The only claim is about the critics, and it is usually too vague to check.

**The tier, in plain words.** This is Tier 2 (Psychological) because it works through shame and identity: readers back away from a view once they're told that holding it means they don't understand.

**Examples.**

1. **Those who object to the new bus schedule fail to grasp** how the routes actually work.  
   *Honest version:* Some riders object to the new bus schedule because the early run now leaves at 7:40. The transit office says the change cuts the average wait from 14 minutes to 9.

2. Customers who question the phone upgrade **simply don't understand the technical requirements** of the new chip.  
   *Honest version:* Some customers question why the phone upgrade skips older models. The new chip needs 8 GB of memory, and the older models have 4 GB.

**False alarm.** Most first-time gardeners lack the experience to prune fruit trees, so the garden club runs a free class each spring.  
Nobody's view is being dismissed and no argument goes unanswered. The sentence says beginners haven't learned a skill yet and points to a class where they can learn it.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** The rule matches exact verb forms, so the third-person singular slips through: "Anyone who objects to the bake sale prices misunderstands what the ingredients cost." It isn't flagged because "objects" and "misunderstands" don't match the rule's "object" and "misunderstand". The rule also misses any attack on the critic's competence that avoids its fixed phrases, as in "Critics of the new bus schedule have clearly never ridden a bus at rush hour." That sentence makes the same move with none of the understand, grasp or expertise wording.


#### Reframing to dismiss

Rule `DISMISSAL_BY_REFRAMING` (Dismissal by Reframing)

*It restates someone's point as something they did not say, then answers that new version instead of the real one.*

**How it works.** The restatement is presented as a helpful clarification of what the other side really means, so readers tend to accept it as a fair summary. Once the new version stands in for the original, rejecting it feels like rejecting the original, but the original point is never answered. No evidence is offered that the new version is what the person meant.

**The tier, in plain words.** It is a Tier 2 (Psychological) move because it works on how readers feel about the people making the point, often by giving them a hidden or unflattering motive, rather than on facts about the point itself.

**Examples.**

1. Riders asked for one more evening bus on Route 4, but **what they're really asking** for is a private taxi that everyone else pays for.  
   *Honest version:* Riders asked for one more evening bus on Route 4. The transit office says it would add about 40 minutes of driver time each weeknight, so the board will weigh that cost against expected ridership.

2. Parents asked that each item at the bake sale carry an ingredient label, but **that is really just** a way to push out the home bakers.  
   *Honest version:* Parents asked that each item at the bake sale carry an ingredient label so families with allergies can choose safely. Home bakers would need to write out a label for every batch they bring.

**False alarm.** When the transit office asked riders what they're really asking for, 212 of 300 survey replies named a later last bus.  
Nobody's point is recast here. The riders were asked directly, the answer is in their own words, and the sentence gives the count of replies. The engine matches the phrase without checking who is doing the restating.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** The rule only looks for a few set phrases, so the same move gets through when it is worded differently. "In other words, they want the city to run empty buses all night" is not flagged. Neither is "So what you're really asking for is a private taxi," because the phrase check covers only "they," "he" and "she," not "you." A second gap is typography. Published text often uses a curly apostrophe (they’re), and the phrase check expects a straight one ('), so the first example goes unflagged when it is set in curly quotes.


#### One cause for everything

Rule `CAUSAL_TOTALIZATION` (Causal Totalization)

*It blames one person, group, or thing for wrecking a whole life, everything, or a whole system, with no evidence, no mechanism, and no limit on the damage.*

**How it works.** Big harm words like "ruined" and "destroying" land as a feeling before they land as a claim. Pinning all of it on one actor gives the reader a simple story and someone to be angry at. It never says what that actor did, how it caused the harm, or how far the harm really goes, so there is nothing to check.

**The tier, in plain words.** This is a Tier 2 (Psychological) move because it works through frustration and a sense of loss, pointing those feelings at a single target instead of giving the reader facts to weigh.

**Examples.**

1. The city's new bus schedule **is ruining my life**.  
   *Honest version:* Since the new bus schedule moved my morning bus from 8:10 to 8:25, I have been late to work three times this month.

2. The garden club's new president **ruined everything** this spring.  
   *Honest version:* This spring the garden club's new president moved meetings to weekday mornings, and attendance fell from 30 members to 12.

**False alarm.** A burst pipe ruined everything in the basement, including the washer, the dryer, and six boxes of books.  
This is a literal account of physical damage. It names the cause (a burst pipe), limits the damage to one place (the basement), and lists what was lost. Nothing is exaggerated and nothing is hidden. The rule matches only the words "ruined everything" and does not look at the scope that follows, and it has no citation or detail check that could turn it off.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) Contractions get past it. "The new bus schedule's ruining my life." makes the same claim, but the rule needs the full word "is", "are", "has been" or "have been" before a present-tense verb, so "schedule's ruining" is not matched. The v1 engine raises no flags at all on this sentence. 2) Blame without a destruction verb gets past it. "The new coach is the reason our whole season fell apart." puts the whole collapse on one actor, but it uses "is the reason ... fell apart" instead of a listed verb such as ruin, destroy or wreck, so nothing fires. Targets outside the fixed list also get through. "The new bus schedule is ruining the neighborhood." and "The new president ruined our garden club." raise no flags, because "the neighborhood" and "our garden club" are not among the listed targets like "everything" or "my life".


#### Single-cause blame

Rule `MONOCAUSAL_BLAME` (Monocausal Blame Compression)

*It blames a broad outcome on one cause or one actor and leaves out everything else that played a part.*

**How it works.** Most outcomes have several causes, and sorting them out takes work. A single cause gives the reader a tidy story and one clear place to aim their frustration, so it feels like an explanation even when no evidence ties that cause to the whole result. Once readers accept it, they stop asking what else contributed.

**The tier, in plain words.** It is Tier 2 (Psychological) because it works by giving frustration a single target, and that simple, satisfying story takes the place of evidence about what actually happened.

**Examples.**

1. **Because of the new coach everything has gone downhill** this season.  
   *Honest version:* The team has done worse since the new coach arrived, and the coaching change may be one of several reasons.

2. The rain was **the sole reason why** the school bake sale came up short this year.  
   *Honest version:* The school bake sale raised less this year, and rain on the day was one likely reason.

**False alarm.** The plumber's inspection report found that a cracked seal was the main cause for the leak under the sink.  
The claim is narrow (one leak), it names its source (an inspection report), and it points to a physical cause that anyone can check. The engine matches the phrase 'the main cause for' without looking at scope or source, so it flags this fair sentence on the span 'the main cause for'.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** The rule matches only fixed phrases. (1) The same claim with different wording gets through. "Ever since the new coach arrived, nothing has gone right for this team." makes the same one-cause claim but uses none of the trigger phrases, and the engine does not flag it. (2) Small surface changes break the phrases that do exist. "Because of the rain everything has gone wrong." is flagged, but the same sentence with a comma ("Because of the rain, everything has gone wrong.") is not. The cause can be at most three words: "Because of the new schedule everything has gone wrong." is flagged, while "Because of the new bus schedule everything has gone wrong." is not. A possessive ("It's all the coach's fault.") or a curly apostrophe ("It’s all their fault.") also gets through, even though "It's all their fault." with a straight apostrophe is flagged.


### Tier 2 · Legal

*These rules run only when a scan is set to the legal domain (or auto). In a general scan they never fire.*


#### Penalty threat to silence

Rule `LEGAL_SANCTIONS_THREAT` (Sanctions Threat as Silencing Tool)

*It warns that the other side will be punished if it keeps making an argument, so the argument gets dropped instead of answered.*

**How it works.** A penalty warning makes an argument feel dangerous to keep, whether or not it is weak. The reader or the other side feels the risk and starts to doubt the claim, but nobody has shown why it is wrong. The threat stands in for the reasons that would actually settle the point.

**The tier, in plain words.** It is Tier 2 (Psychological) because it works through fear of being punished, not through evidence about the argument itself.

**Examples.**

1. The roofer's claim that the second coat was never paid for is baseless, and **sanctions will be sought** unless it is withdrawn by Friday.  
   *Honest version:* The roofer's claim that the second coat was never paid for is wrong: the bank record from June 3 shows the full payment, and we will file it with our answer.

2. If the garden club keeps pressing its fence-line argument, we will move under **Rule 11** before the spring hearing.  
   *Honest version:* We disagree with the garden club's fence-line argument because the March survey puts the post two feet inside our lot, and we will explain that at the spring hearing.

**False alarm.** The judge's order in the bus-shelter repair case explained that Rule 11 requires every filing to have a factual basis, then declined to impose any penalty.  
It reports what the rule requires and what the court actually decided. It does not threaten anyone or push anyone to drop an argument.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** The rule looks for particular words, such as "Rule 11", "sanctions will be sought", "warrants sanctions", or a referral to a disciplinary board. So the same threat gets past it in two ways. First, it can be hinted at without those words: "You may want to think hard about what judges do to people who waste their time before you file that bake-sale refund claim again." The engine did not flag this. Second, the penalty can be named in plain terms instead of legal ones: "Keep pushing the phone-upgrade fee argument and we will ask the court to make you pay every dollar of our legal fees." The engine did not flag this either. The rule also cannot judge whether the challenged argument is really frivolous. It flags the words, not the purpose behind them.


#### Arguing with a straw man

Rule `LEGAL_STRAW_MAN` (Straw Man Mischaracterization)

*It restates the other side's argument in a bigger or cruder form than they gave it, then knocks down that weaker version.*

**How it works.** The reader usually hears the other side's position only through the writer's summary, so a stretched summary takes the place of the real one. Words like "every," "never," or "essentially arguing" make the stretched version sound extreme, and an extreme claim looks foolish without any proof against it. The reader ends up agreeing that the claim is wrong, but nobody has shown that the claim the other side actually made is wrong.

**The tier, in plain words.** This is a Tier 2 (Psychological) move because it works on how the reader feels about the other side, making them look unreasonable or extreme, and gives no evidence about what they really said.

**Examples.**

1. **Plaintiff claims that every** shingle on the roof was installed wrong, which is hard to square with a roof that has not leaked in two years.  
   *Honest version:* Plaintiff claims that three shingles on the north slope were installed loose; our inspector's report found those three shingles fastened to code, and the roof has not leaked in two years.

2. The garden club **is essentially arguing that we should** never be allowed to use the shared water line again.  
   *Honest version:* The garden club asks that the shared water line be used only on weekday mornings; we ask for evening hours too, because our beds dry out by noon.

**False alarm.** Plaintiff argues that no refund was issued for the returned phone, and attaches the store receipt showing the return date.  
The summary is accurate. The plaintiff's claim really is that no refund was issued, and the sentence points to the receipt as evidence. Here "no" is simply what the claim says, not an overstatement. The rule can't tell the two apart, because it matches the words and never checks them against what the party actually said.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) The rule looks for two fixed wordings. The first is a formal party label (plaintiff, defendant, petitioner, respondent, appellant, appellee, opposing or other party, side, or counsel), then a verb like "argues" or "claims," then an absolute word such as "every," "no," or "never." The second is a reducing frame such as "essentially arguing" or "really asking," followed by "we," "this court," or "the plaintiff" and then "should," "must," or "have to." A loose paraphrase that uses neither wording gets through even when it is just as distorted. For example, "In other words, the homeowner wants the contractor to rebuild the entire porch for free" and "The bake sale committee wants every family to bake four dozen cookies, which no working parent could manage" are not flagged. "Homeowner" and "committee" are not on the party list, "wants" is not on either verb list, and neither sentence uses the reducing frame. 2) The rule is loaded only when the engine runs in the legal domain (or auto). The same sentence, "Plaintiff claims that every shingle on the roof was installed wrong," is not flagged in the default general domain.


### Tier 2 · Media

*These rules run only when a scan is set to the media domain (or auto). In a general scan they never fire.*


#### Vague crowd words

Rule `MEDIA_WEASEL_QUANTIFIERS` (Weasel Words / Vague Quantifiers)

*It says an unnamed and uncounted group agrees, so a claim seems widely held when nobody can check how many people actually hold it.*

**How it works.** Phrases like "many people say" or "it is widely believed" suggest that a crowd already agrees. The reader feels the weight of that crowd but never finds out who is in it, how many there are, or what they based their view on. Since no number or name is given, the claim can't be checked, and it can't be shown to be wrong either.

**The tier, in plain words.** This is a Tier 2 (Psychological) move because it plays on the wish to agree with others, so a reader goes along with the claim because "many" seem to believe it, not because of any evidence.

**Examples.**

1. **Many people** say the garden club's spring plant sale was the best in years, and some experts think sales will double next year.  
   *Honest version:* The garden club's treasurer said spring plant sale receipts were the highest in five years, and she expects sales to double next year based on early pre-orders.

2. **It is widely believed** that the new city bus schedule saves riders time, and there is growing support for adding a Sunday route.  
   *Honest version:* The transit office's ride logs show trips on the new city bus schedule average six minutes shorter, and 140 riders have signed a petition asking for a Sunday route.

**False alarm.** At the garden club meeting, 18 of 24 members voted to hold the plant sale on Saturday; some people wanted Sunday instead, and several people abstained.  
The sentence gives the real count first (18 of 24 in a named vote). "Some" and "several" only split up the six members who were left over. They don't suggest a larger agreement than the tally shows. The engine still flags it, because the rule counts two quantifier phrases and does not look at the numbers around them. A citation doesn't stop it either: this rule has no citation check, and a similar bake-sale sentence with "(Table 2)" was also flagged.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) The rule only fires after two vague phrases. One phrase on its own gets through: "Many experts think the new phone upgrade is worth the price." is not flagged. 2) Any wording outside the rule's fixed word lists also gets through. Contractions do too: the rule looks for "it is" and "it has been", so "it's" is missed. Nothing in "Most fans think this is the team's best season in years, and a lot of folks expect a title." is flagged ("most", "a lot of", "fans" and "folks" are not in the lists). Nothing in "It's widely believed the new phone upgrade fixes the battery problem, and it's generally thought the camera is better too." is flagged either.


#### Feelings before facts

Rule `MEDIA_EMOTIONAL_LEAD` (Emotional Lead / Hook)

*It opens a story with a strong feeling word, so the reader reacts before learning what happened.*

**How it works.** The first words of a story set the mood for everything after them. A word like 'shocking' or 'heartbreaking' tells the reader how to feel before they know the facts, so the facts that follow get read through that feeling. The word carries no evidence of its own. It only reports the writer's reaction, or the reaction the writer wants you to have.

**The tier, in plain words.** It is a Tier 2 (Psychological) move because it works on the reader's feelings, setting a mood of alarm, anger or sorrow before any fact arrives.

**Examples.**

1. **Shocking** changes are coming to the Route 9 bus: starting Monday, buses will run every 20 minutes instead of every 15.  
   *Honest version:* Starting Monday, Route 9 buses will run every 20 minutes instead of every 15, according to the schedule the city transit office posted this week.

2. **Heartbreaking** news from the school bake sale: this year's sale raised $450, down from $600 last year.  
   *Honest version:* This year's school bake sale raised $450, down from $600 last year, according to the parent group's treasurer.

**False alarm.** Damaging winds of up to 60 mph are possible Tuesday evening, the county weather office said in its storm advisory.  
'Damaging winds' is a standard forecast term for wind strong enough to break branches or bring down lines. The sentence gives the speed and names the source, so the word reports a measured risk. It is not there to set a mood. The engine flags it anyway because it matches the word itself and does not look at how the word is used.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** The rule checks a fixed list of words, and only when one starts within about the first 50 characters of the text. (1) A charged word that is not on the list gets through. 'Nightmare commute ahead: starting Monday, Route 9 buses will run every 20 minutes instead of every 15.' is not flagged. (2) A listed word placed a little later also gets through. In 'Riders who count on the Route 9 bus every morning got a shocking surprise this week: ...' the word 'shocking' starts after character 50, so it is not flagged. The same goes for a scene-setting opening with no charged word at all, such as 'The rain had soaked through her coat by the time the Route 9 bus finally came, twenty minutes late.' It still leads with feeling, and the rule does not flag it.


#### Correction at the bottom

Rule `MEDIA_BURIED_QUALIFIER` (Buried Qualifier / Buried Denial)

*It opens with the story people will remember and puts the fact that weakens it, such as a denial, a correction or "no evidence," at the end.*

**How it works.** Readers form their view of a story from its opening lines, and many stop reading before the end. When the correction or denial comes last, it is technically there, but it arrives after the reader has already made up their mind. Nothing false has to be said. The order of the facts does the work that evidence should do.

**The tier, in plain words.** It is a Tier 2 (Psychological) move because it works on how people hold first impressions: the feeling the opening creates stays with the reader even after the correction arrives.

**Examples.**

1. Last night's storm left fallen branches on nearly every street in town, flooded a dozen basements and sent a long line of neighbors to the hardware store, and by breakfast most of them were blaming the old storm drains on Elm Street. **However, the town engineer found no evidence** that the drains failed.  
   *Honest version:* The town engineer found no evidence that the old storm drains on Elm Street failed in last night's storm, though by breakfast most neighbors were blaming them after the storm left fallen branches on nearly every street, flooded a dozen basements and sent a long line of neighbors to the hardware store.

2. Owners who installed this week's phone update flooded the help forums with posts saying their batteries now die before lunch, and the most shared thread, titled "This update ruined my phone," drew thousands of angry replies within a day. In the phone maker's lab tests, **though, the drain was not confirmed** on any model.  
   *Honest version:* The phone maker's lab tests did not confirm a battery drain on any model, though owners who installed this week's update flooded the help forums with posts saying their batteries now die before lunch, and the most shared thread, titled "This update ruined my phone," drew thousands of angry replies within a day.

**False alarm.** Starting Monday, Route 4 buses will run every 15 minutes instead of every 20, Route 9 will add a stop at the public library, and the last evening bus on both routes will leave the depot at 11:10 p.m. instead of 10:40 p.m. However, the start date for the new Sunday service is not confirmed yet.  
The main news is stated plainly and is not changed by the last sentence. The caveat is about a different detail, the Sunday service, and it is said clearly. Nothing earlier in the text sets up an impression that the caveat has to undo, so the order is simply the natural order of importance.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) Wording outside its short list. The rule only fires when a "however / but / though" is followed within about 150 characters by one of a few fixed phrases ("no evidence," "not confirmed," "denied," "could not be confirmed," "remains unclear," and so on). A buried denial worded as "has not been confirmed," "could not confirm," or "did not confirm" goes unflagged. So does one with no transition word, like "The town engineer's report, for its part, found the drains worked as designed." All of these were tested and none was flagged. 2) It counts characters, not reading order. If the frame is set in under 200 characters, as in a headline or a short alert followed right away by the qualifier, the rule stays silent. It also stays silent when the qualifier comes more than about 150 characters after the "however," even though that pushes the qualifier deeper into the text.


#### Guesses dressed as likely

Rule `MEDIA_SPECULATIVE_FRAMING` (Speculation Presented as Likely)

*It uses forecast words like "is expected to" or "could well lead to" to make a guess about the future sound nearly settled, without saying who expects it or why.*

**How it works.** Words like "expected", "poised", "set to", and "signs point to" suggest that someone has weighed the evidence, but they never say who did or what they found. Each phrase is hedged, so none of them can be proven wrong. Stack two or three together and the reader walks away treating the outcome as close to certain.

**The tier, in plain words.** This is a Tier 2 (Psychological) move because it works on what readers hope for or brace for, and that expectation replaces a claim they could check.

**Examples.**

1. The new city bus schedule **is expected to** cut wait times, and it could well lead to fuller buses by spring.  
   *Honest version:* Transit planners estimate the new city bus schedule will cut average waits from 15 minutes to 10, based on a three-month trial. They have not projected how many more riders it will bring.

2. The home team **is poised to** win the title this season, and signs point to a sold-out final.  
   *Honest version:* The home team leads the league by six points with four games left, and 9,000 of the 10,000 seats for the final have been sold.

**False alarm.** The posted timetable says the new city bus schedule is set to start on June 1, and the Route 4 bus is slated to run every 12 minutes.  
This is not a guess. It reports a published plan, names where the plan comes from, and gives exact dates and times that a reader can check. Here "set to" and "slated to" are ordinary scheduling words, not a forecast made to sound certain.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) A single phrase passes. The rule needs at least two matching phrases, so "The new phone upgrade is expected to sell out on the first day." raises no flag, and neither does the same guess followed by a sentence without a listed phrase ("...is expected to sell out. Stores are bracing for long lines."). 2) Wording outside the fixed list passes. "Could face delays" on its own (the rule only catches "could soon/eventually/ultimately/well face"), "will likely", and contractions such as "It's expected to" or "the storm's likely to" do not match. So "The garden club's spring show could face delays, and it will likely draw a smaller crowd." is not flagged. (Also note that the rule runs only when the domain is "media" or "auto". Under "general", the first example is not flagged.)


### Tier 2 · Financial

*These rules run only when a scan is set to the financial domain (or auto). In a general scan they never fire.*


#### Convenient reference point

Rule `FIN_ANCHORING` (Arbitrary Anchoring)

*It measures a number against a hand-picked high or low, so the same figure looks like a bargain or a boom.*

**How it works.** The first number a reader sees becomes the yardstick for the numbers after it. A price "down 45% from the record high" feels cheap because the record high is the comparison, even if that high was unusual and today's price is ordinary. The reader comes away with a sense of value or momentum but never learns whether the reference point was a fair one to pick.

**The tier, in plain words.** It is Tier 2 (Psychological) because it works on the feeling of a bargain or a missed chance, not on evidence about the number itself.

**Examples.**

1. Season tickets are **down 45% from the record high**, so this is the year to finally buy them.  
   *Honest version:* Season tickets cost $330 this year, about the same as last year's $320; three seasons ago they peaked at $600.

2. Last year's phone is now **selling at just 40% of its peak price**, which makes it a steal for anyone ready to upgrade.  
   *Honest version:* Last year's phone now costs $360, down from $900 at launch, while this year's model costs $950.

**False alarm.** The river is down 30% from its record high in April, which the county flood office says is normal for late summer.  
The reference point is dated and relevant to the reader. A source supplies the context, and the sentence says what the drop means instead of using it to push a choice.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) Small changes in wording get past the regex. "Down 45% from their record high" is not flagged because the rule accepts only "its", "the", or no word before the anchor. "Less than half of what they did at the peak" is not flagged because there is no percent figure. 2) The most common retail anchor has no percent and no peak/high wording at all: "Was $900, now only $360" and "40% below the list price" both pass unflagged. The rule also runs only when domain is "financial" or "auto". Under the default "general" domain it flags nothing, even on the examples above.


#### Forecast stated as fact

Rule `FIN_PROJECTION_AS_FACT` (Projection Presented as Fact)

*It states a guess about the future, like a price or a sales total, as if it were already settled.*

**How it works.** A forecast is an estimate, and it can be wrong. Writing "will reach" in place of "is expected to reach" drops the words that tell readers they are looking at an estimate. Readers take in a confident number as a known one and never ask what it rests on.

**The tier, in plain words.** This is Tier 2 (Psychological) because it works on how readers feel about uncertainty: sounding sure gives comfort or urgency where the evidence gives neither.

**Examples.**

1. The school bake sale opens at nine on Saturday, and **sales will reach $600**.  
   *Honest version:* The school bake sale opens at nine on Saturday. Last year it took in $540, so the committee expects sales of about $600.

2. The new phone goes on sale in March, and **the price will fall** by half before summer.  
   *Honest version:* The new phone goes on sale in March. The maker's last two models dropped about 40% within four months, so the price may fall by half before summer.

**False alarm.** On July 1, under the fare change the transit board approved in May, bus ticket prices will reach $2.50.  
This isn't a forecast. The new fare was already voted on and has a start date, so "will" describes a scheduled fact, and the sentence says where it comes from.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** The rule only matches a short list of money words followed by a short list of verbs. So "sales will climb to $600" passes, because "climb" is not on the verb list. "The garden club's plant sale will bring in $900" also passes, because the subject is not on the list. The rule also runs only when the text is checked in the financial (or auto) domain. In the default general domain, the same bake-sale sentence is not flagged at all.


#### Hot streak forever

Rule `FIN_RECENCY_EXTRAPOLATION` (Recency Bias / Trend Extrapolation)

*It takes a short run of good results and treats the run as if it will keep going, without saying why.*

**How it works.** A recent streak is easy to picture, so the reader carries it forward without being asked to. The writer never states or defends the prediction. They only point at the streak, or say nothing suggests it will end. Because the forecast is never spelled out, the reader is never shown the evidence it would need, such as how long the run has lasted, what caused it, or what might change.

**The tier, in plain words.** It is a Tier 2 (Psychological) move because it works on hope and the fear of missing out, not on evidence.

**Examples.**

1. The school bake sale has raised more than the year before for three springs in a row, and **there's no reason to think this will stop**.  
   *Honest version:* The school bake sale has raised more than the year before for three springs in a row. Three years is a short run, and turnout and donated goods change each spring, so we are planning for a total near last year's.

2. After six straight wins, the home team **continues its winning ways**, so fans are already planning the championship parade.  
   *Honest version:* The home team has won six straight games. Half the season is left, and four of the remaining games are against the top teams in the league, so the title is still open.

**False alarm.** The Route 9 bus has consistently delivered on-time arrivals 95 percent of the time over five years of monthly logs, but the schedule changes in January, so that record may not hold.  
It reports a measured past record, names the source and the time span, and says plainly that the record may not continue. It does not extrapolate.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) It only matches a few fixed phrases. A sentence like "The new phone sold out in its first week, and the trend shows no sign of slowing" makes the same move and is not flagged. The regex needs "no sign" to be followed directly by "this/it/the ... will stop/slow", so "no sign of slowing" gets through. The same goes for "keeps winning", "is on a roll", or "has outperformed three years straight" when no word like "consistently" or "always" appears. 2) When the conclusion is left for the reader to draw, as in "The garden club doubled its membership last spring. Imagine how big it will be in five years.", no trigger phrase appears and nothing is flagged. Also, the rule is financial-only: it runs when the domain is "financial" or "auto". In a "general" scan it never fires, even on the exact example text.


---

## Tier 3: Institutional

Moves that borrow the voice or weight of an office, a court or an organization, so that official standing takes the place of a reason.


### Tier 3 · General

*These rules run on every scan.*


#### Hiding behind official jargon

Rule `BUREAUCRATIC_OBSCURITY` (Bureaucratic Language Obscuring Meaning)

*It wraps a simple claim in stiff, official-sounding words, so the claim sounds more settled than it is, or so its real meaning is harder to see.*

**How it works.** Formal legal and office phrases sound like a rule or a procedure is speaking, not a person, so readers tend to accept the sentence rather than question it. The dense wording also slows readers down, and a plain point, often an unwelcome one like a cut, a delay or a cost, can slip past them. No evidence has been added; only the tone has changed.

**The tier, in plain words.** This is a Tier 3 (Institutional) move because it borrows the voice of an office or a legal document, so the claim leans on how official it sounds, not on reasons the reader can check.

**Examples.**

1. **Pursuant to the implementation** of the revised service plan, Route 9 buses will arrive every 20 minutes instead of every 15.  
   *Honest version:* Route 9 buses will now come every 20 minutes instead of every 15. That means a longer wait at each stop.

2. **Notwithstanding the foregoing**, the contractor has determined that the leak under the sink falls outside the scope of the warranty.  
   *Honest version:* Even so, the contractor says the warranty does not cover the leak under the sink.

**False alarm.** It should be noted that the garden club survey covered only 40 households (Table 2), so the result may not hold for the whole town.  
Here the formal phrase points to a real limit in the evidence and says where the numbers are (Table 2). It makes the claim weaker and easier to check, not more official. The rule matches the words "It should be noted that" no matter what follows, and this rule is not switched off when a citation is present, so the engine flags the sentence anyway.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) The rule only catches a fixed list of phrases, so newer office jargon gets through. For example, "To right-size service levels, the transit team will leverage stakeholder alignment across Route 9" hides a service cut in the same way, and the engine does not flag it. 2) The buzzword check needs exactly one word between the buzzword and the noun. "The phone plan will effectuate a streamlined trade-in mechanism for all customers" has two words in between, so it is missed. Long noun phrases with no listed words are also missed, such as "A service frequency optimization initiative has been undertaken for Route 9."


#### Unnamed authorities

Rule `VAGUE_INSTITUTIONAL_APPEAL` (Vague Institutional Appeal)

*It says important organizations back a claim but never says which ones.*

**How it works.** Words like "leading" or "key" make readers picture serious, trusted bodies standing behind the claim. No names are given, so the reader cannot check who said it, what they said, or whether anyone said it. The claim gets the weight of authority without anything a reader can test.

**The tier, in plain words.** This is a Tier 3 (Institutional) move. It borrows the standing of institutions to carry a claim, in place of the evidence those institutions would supply.

**Examples.**

1. **Leading organizations recommend** watering tomatoes at dawn, so the garden club is moving its watering hour.  
   *Honest version:* The garden club is moving its watering hour to dawn. The county extension office's vegetable guide recommends morning watering so the leaves dry before evening.

2. **Industry leaders have long recognized** that a roof should be replaced every twenty years, so we booked a crew for spring.  
   *Honest version:* The label on our shingles lists a twenty-year lifespan, and the roof is now twenty-two years old, so we booked a crew for spring.

**False alarm.** Two key groups support the new bus schedule: the riders' council, which voted for it in June, and the school board, which asked for an earlier first bus.  
The sentence names both groups and says what each one did, so a reader can check it. The engine still flags it. It matches "key groups support" and finds nothing nearby that it counts as a citation, because it does not read the names that come after the colon.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) Small changes in wording get past it. The rule knows only a fixed list of adjectives, nouns and verbs, in one word order, with no more than five words between the group and the verb. None of these are flagged: "Well-known organizations recommend watering tomatoes at dawn" ("well-known" is not on the list), "Watering tomatoes at dawn is recommended by leading organizations" (passive order), and "Top experts back the new watering schedule" ("experts" and "back" are not on the list). 2) Plain numbers near the claim can switch the rule off. "Leading organizations recommend watering tomatoes at dawn, 2 or 3 times a week, so the garden club is moving its watering hour" is not flagged. The citation check treats "2 or 3" as a reference, so it assumes a source was given.


#### Sweeping damage claims

Rule `TOTALIZING_HARM_LANGUAGE` (Totalizing Harm Language)

*It describes harm as total and final, with everything ruined and nothing left, without saying what was actually damaged or how much.*

**How it works.** Phrases like 'completely destroyed' or 'nothing left' give the reader a finished verdict instead of a measurement. A picture of total loss is vivid and hard to argue with, so readers tend to accept the scale without asking what was counted. Because no scope is given, there is nothing to check, and a partial loss can pass as a total one.

**The tier, in plain words.** BiasClear files it under Tier 3, Institutional, because it speaks with the finality of an official damage report and settles the question of scope the way a signed assessment would, but with no assessment behind it.

**Examples.**

1. Last night's hailstorm **completely destroyed** the community garden.  
   *Honest version:* Last night's hailstorm flattened the tomato and squash beds in the community garden; the herb beds and the fruit trees lost leaves but no branches.

2. The basement flooded over the weekend, and **everything is ruined**.  
   *Honest version:* The basement flooded over the weekend with about two inches of water; the carpet and three boxes of books are soaked, but the furnace and the washer are dry and working.

**False alarm.** The backyard shed was completely destroyed in Tuesday's fire, but the house ten feet away had only a scorched fence post.  
The sentence names one object, the shed, says what happened to it, and marks where the damage stopped. That makes 'completely' a checkable fact about a bounded thing, not a sweeping verdict. The engine flags it anyway because the rule matches the words 'completely destroyed' and cannot see that the scope is limited.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) Plain past tense gets through. 'Last night's hailstorm destroyed the whole community garden.' and 'Last night's hailstorm wiped out the whole community garden.' are not flagged. The rule catches 'the whole' or 'the entire' only after -ing verbs like 'destroying'. It catches a past-tense word like 'destroyed' or 'ruined' only right after an intensifier such as 'completely', or right after 'everything' or 'everything is'. 2) A nearby reference mark turns the rule off. 'Last night's hailstorm completely destroyed the community garden [1].' and the same sentence ending in '(see p. 2)' are not flagged. The rule skips a match when a bracketed number, a page number, or a similar reference mark appears within about 120 characters of it. That mark says nothing about whether the whole garden was lost.


### Tier 3 · Legal

*These rules run only when a scan is set to the legal domain (or auto). In a general scan they never fire.*


#### Settled law as shutdown

Rule `LEGAL_SETTLED_DISMISSAL` (Settled Law Dismissal)

*It calls a rule "settled" to end a discussion, without showing how the rule answers the point someone raised.*

**How it works.** The word "settled" tells readers that people with authority answered the question long ago, so asking again feels pointless or rude. The sentence never names the rule, quotes it, or shows how it fits the case at hand. The reader gets a verdict and a closed door, not a reason they can check.

**The tier, in plain words.** This is a Tier 3 (Institutional) move because it uses the weight of past rulings and rulebooks, the authority of the institution, where an argument the reader could test should be.

**Examples.**

1. The garden club's plot rules are **settled law**, so the new member's question about the waiting list needs no answer.  
   *Honest version:* Rule 3 of the garden club's bylaws gives open plots to members in the order they joined; the new member joined in May, so she is fourth on the waiting list.

2. It is **well settled that** a rained-out game counts as a tie, so the coach's request for a makeup game fails.  
   *Honest version:* League rule 7.2 says a rained-out game counts as a tie and is not replayed, so the coach's request for a makeup game does not fit that rule.

**False alarm.** It is well settled that rained-out games count as ties: league rule 7.2 says so on page 4, and the board applied it to three games last season.  
The sentence names the rule, says where to find it, and points to past cases where it was applied, so a reader can check the claim. Here "well settled" sums up evidence that is given instead of standing in for it. The engine still flags it because this rule has no citation check and matches on the phrase alone.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** The rule only looks for a short list of stock phrases: well settled (with or without a hyphen), clearly or plainly established, settled, or erroneous, black-letter law, hornbook law, settled law, principle, precedent or authority, and "controlling authority is clear". Other wording that makes the same move gets through. For example, "That question was answered years ago, so the new member's complaint about the waiting list needs no reply" is not flagged, and neither is "It is firmly established that a rained-out game counts as a tie, so the coach's request fails." The rule also runs only in the legal (or auto) domain. In a general scan, "It is well settled that a rained-out game counts as a tie, so the coach's request for a makeup game fails" raises no flag at all.


#### Dismissed without an answer

Rule `LEGAL_MERIT_DISMISSAL` (Merit Dismissed Without Engagement)

*It calls an argument meritless or frivolous so that nobody has to answer what the argument actually says.*

**How it works.** Words like "plainly meritless" or "wholly without merit" sound like a finished judgment, so the reader assumes someone has already checked the argument. But the sentence gives no fact, rule, or record showing why the argument fails. The strong label does the work that a reason should do.

**The tier, in plain words.** It is Tier 3 (Institutional) because it borrows the tone of a court's final ruling, and that official weight stands in for actually engaging with the argument.

**Examples.**

1. The homeowner's claim that the contractor skipped the second coat of sealant on the deck is **plainly meritless**, and the court should dismiss it.  
   *Honest version:* The homeowner's claim that the contractor skipped the second coat of sealant on the deck should be dismissed: the job log and dated photos from both days show two coats going on.

2. The garden club's challenge to the new plot fees is **wholly without merit** and should be rejected.  
   *Honest version:* The garden club's challenge to the new plot fees should be rejected because the club's own bylaws, in section 3, let the board set fees each spring without a member vote.

**False alarm.** The small-claims judge found the fence claim had no merit because the survey map placed the fence two feet inside the owner's own lot.  
It reports a judge's finding and gives the reason right away: a survey map anyone can check. The reader gets the evidence along with the verdict.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** The rule only knows a fixed list of phrases. Plain synonyms get past it: "baseless," "devoid of merit," "lacks merit" (without "any"), "meritless on its face," "without any merit," and "frivolous" on its own with no "clearly," "obviously," or "patently" in front all go unflagged. The rule also runs only when the text is checked as legal (or auto) writing, so the same sentence checked as general writing is never flagged.


#### Piling on authority

Rule `LEGAL_WEIGHT_STACKING` (Authority Weight Stacking)

*It treats a big, unnamed pile of authority as if its size settled the question, and never shows why the claim is right.*

**How it works.** Hearing that "every court" or "the weight of authority" agrees makes a point feel closed before the reader asks what those sources actually said. The reader gets a sense of size, not a reason: no source is named, nothing is counted, and the reasoning that decided the matter is left out. Checking a whole stack of sources feels like too much work, so most readers just take the summary.

**The tier, in plain words.** This is Tier 3, Institutional, because it leans on the combined standing of courts and other official sources and asks readers to trust that weight instead of judging the argument.

**Examples.**

1. **The weight of authority** is against moving the bake sale outside, so it stays in the gym.  
   *Honest version:* The school's event handbook says food sales must be held indoors, so the bake sale stays in the gym unless the committee changes that rule.

2. **Every court that has addressed** a leaky-gutter dispute sided with the homeowner, so the roofer must redo the job for free.  
   *Honest version:* Two small-claims rulings on the same warranty wording sided with the homeowner because the warranty covers gutter leaks for two years; this leak began at eight months, so the roofer must redo the job for free.

**False alarm.** The weight of authority on gutter warranties is evenly split, four small-claims rulings each way, so this case turns on the wording of the roofer's contract.  
It reports what the authority actually shows, gives the count on each side, says plainly that there is no consensus, and points to the contract wording as the thing that decides the case. It is not using the pile of rulings to win the point.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** Small changes in wording get past it. "Every court to have considered a leaky-gutter dispute sided with the homeowner" is not flagged. The rule accepts "every court to consider" and "every court that has considered", but not "to have considered". A plain list also gets through: "Three past rulings, two consumer guides, a trade handbook and a repair pamphlet all side with the homeowner" stacks up authority without any of the stock phrases the rule watches for. (The rule also runs only when text is checked in legal or auto mode. The same flagged sentences checked in general mode return no flags.)


#### Too late to hear

Rule `LEGAL_PROCEDURAL_GATEKEEPING` (Procedural Gatekeeping to Avoid Substance)

*It turns down a complaint on a procedural point, such as a missed deadline, the wrong person asking, or the wrong step, and never says whether the complaint is right.*

**How it works.** A rule about timing or who may speak sounds fair and neutral, so readers accept the refusal without asking about the actual problem. The procedural point may be true, but it answers a different question. The reader comes away thinking the matter is settled when nobody has checked the facts.

**The tier, in plain words.** This is a Tier 3 (Institutional) move because it uses an institution's own rules and procedures to decide the question, so nobody has to weigh the evidence.

**Examples.**

1. The bake sale committee said the parent **failed to raise** her concern about the prices before the sign-up deadline, so it will not look at whether the cookies cost too much.  
   *Honest version:* The parent raised her concern about the prices after the sign-up deadline. The committee is not reviewing it for that reason, so it has not decided whether the cookies cost too much.

2. Riders who missed the comment period have **waived any objection** to the new bus schedule, so the transit board will not discuss the longer waits on Route 9.  
   *Honest version:* Some riders sent their objections after the comment period closed. The transit board will not discuss them at this meeting, so nobody has yet checked the longer waits on Route 9.

**False alarm.** The league ruled that the coach failed to raise his protest before the final whistle, as the rulebook requires, but it still reviewed the game video and found the goal was clean.  
The sentence gives the procedural point and its source (the rulebook). Then it deals with the substance: the league checked the video and gives its finding. The late protest is not the only reason for the decision.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) Plain wording gets past the rule. The rule matches set phrases like "failed to raise", "waived any objection", "lacks standing to raise" and "procedurally barred". "You brought this up too late, so we won't be looking at the prices at all" makes the same move and is not flagged by this rule. (Another rule, FEAR_URGENCY, catches "too late" in it.) Neither is "That point was not raised in time, and the board considers the matter closed." 2) The rule only matches "before the court", "before this court", "before the tribunal" or "before this tribunal". A sentence that names any other body is missed: "The complaint about the roof repair is not properly before the committee, so we will move on" is not flagged. Also note that the rule only runs when the domain is legal (or auto). The same sentences get no flag in the general domain.


### Tier 3 · Media

*These rules run only when a scan is set to the media domain (or auto). In a general scan they never fire.*


#### Faceless source

Rule `MEDIA_ANONYMOUS_ATTRIBUTION` (Anonymous or Unverifiable Source Attribution)

*It pins a claim on sources the reader cannot name or check, so the claim sounds reported without being shown.*

**How it works.** Phrases like "insiders say" or "people familiar with the matter" suggest that someone close to the facts has spoken. The reader cannot see who they are, how they know, or whether anyone checked. The vague label stands in for the evidence and lends the claim the weight of inside access.

**The tier, in plain words.** This is Tier 3 (Institutional) because the claim borrows authority from an implied position inside an organization instead of from anything the reader can check.

**Examples.**

1. **People familiar with the discussions** say the city will drop the late-night bus route next month.  
   *Honest version:* The transit board voted on Tuesday to drop the late-night bus route starting next month, according to the posted meeting minutes.

2. **Unnamed sources** say the new phone upgrade will cost more than last year's model.  
   *Honest version:* The maker's posted price list shows the new phone upgrade costs $50 more than last year's model.

**False alarm.** Two unnamed staffers at the bus depot, who are not allowed to speak publicly, showed the reporter the repair logs for the broken buses.  
The sentence gives the reason the sources are not named, and it points to evidence the reporter saw with their own eyes (the repair logs). This is careful, legitimate anonymous sourcing, not vagueness standing in for proof.  
*Does the engine flag it?* Yes, the engine flags this sentence. That is a false alarm.

**What it misses.** 1) Wording outside the rule's fixed list gets through. Bare "Sources say the new phone upgrade will cost more than last year's model." is not flagged. The rule counts "sources" only after "unnamed", "anonymous" or "unidentified", or before "close to", "familiar with" or "with knowledge/insight". "Word around the garden club is that the spring plant sale will be canceled." is not flagged either. 2) Numbers near the phrase can switch the rule off. The rule is skipped when something that looks like a citation sits within 120 characters, and a plain time range can look like one. "Unnamed sources say the bus will now run every 15 minutes from 6 to 9." is not flagged, because "6 to 9" matches the number-word-number citation shape. Also note that the rule only runs when the domain is media or auto. In the general domain, "Unnamed sources say..." is not flagged.


---

*Every false alarm in this guide is flagged by the engine. These rules match wording and cannot tell a fair use from an unfair one, so each flag is a prompt to look, not a finding.*
