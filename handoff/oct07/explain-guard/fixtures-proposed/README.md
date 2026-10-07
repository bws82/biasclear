# Proposed Explain eval fixtures (draft)

PROPOSED only; nothing in the repository was edited. Files:

- `pairs-proposed.json`: 48 controversial pairs (q01-q48), fields id, rule, sides, axis, topic, a, b, controversial.
- `controls-proposed.json`: 24 side-free controls (c01-c24), fields id, rule, topic, sentence.
- `gen.py` (source of both files and the checks), `scan.ts` / `scan.mjs` (engine harness), `stats.json`, `scanout.json` (raw engine marks).

## Design

- One template per pair, no reused "Everyone agrees that X should <policy>" form. Predicates are side-neutral
  (misinformation, mismanaged, cannot be trusted, wrecked, lied about), never a policy that fits one side's stance.
- Stand-ins follow `tests/test_symmetry.py`: Kestrines/Vallorans (and Party, senator), Encamp/MTGA movement,
  Verdant/Freehold Party, Solidarist/Preservation government, plus allowed generic labels (progressives/conservatives,
  the left/the right, the union/the company, tenants/landlords, left-wing/right-wing activists, secularists/religious
  believers, progressive/conservative mayor). No real party, movement, person, or institution names (checked: no
  democrat, republican, maga, antifa, nazi, marxist, woke).
- No side label begins a sentence, so b is a with the labels exchanged and no case changes.
- First side: 24 of 48 pairs put the left-coded label in `a`, 24 put the right-coded label in `a`.

## Validation (engine rules 2.0.0a5, domain "general")

Each pair kept only if: the pair's rule fires in both a and b; the mark texts for that rule are identical and contain
neither side label; b equals a with the two labels swapped; word counts match apart from the labels. Also checked:
the full set of (rule, mark text) is identical for a and b in every pair. Result: 48/48 pairs pass, 0 dropped;
24/24 controls fire their listed rule, 0 dropped.

Extra rules that fire alongside the target (the same in a and b): MORAL_HIGH_GROUND pairs also fire SHAME_LEVER on
"Any decent person" (3 pairs); one VAGUE_INSTITUTIONAL_APPEAL pair ("Leading organizations warn") also fires
CREDENTIAL_AS_PREMISE; one TOTALIZING_HARM_LANGUAGE pair also fires CAUSAL_TOTALIZATION.

## Pairs

### Per topic (11 topics)

| | count |
|---|---|
| foreign aid | 5 |
| housing | 5 |
| immigration | 5 |
| schools | 5 |
| taxes | 5 |
| faith-and-public-life | 4 |
| health | 4 |
| labor | 4 |
| policing | 4 |
| speech | 4 |
| climate/energy | 3 |

### Per rule (16 rules; CONSENSUS_AS_EVIDENCE now 3/48 = 6%)

| | count |
|---|---|
| SHAME_LEVER | 4 |
| CLAIM_WITHOUT_CITATION | 3 |
| COMPETENCE_DISMISSAL | 3 |
| CONSENSUS_AS_EVIDENCE | 3 |
| DISSENT_DISMISSAL | 3 |
| EMOTIONAL_SUBSTITUTION | 3 |
| FALSE_BINARY | 3 |
| FEAR_URGENCY | 3 |
| INEVITABILITY_FRAME | 3 |
| INSTITUTIONAL_POSITION_AS_SETTLED | 3 |
| MONOCAUSAL_BLAME | 3 |
| MORAL_HIGH_GROUND | 3 |
| SOFT_CONSENSUS | 3 |
| TOTALIZING_HARM_LANGUAGE | 3 |
| VAGUE_INSTITUTIONAL_APPEAL | 3 |
| CREDENTIAL_AS_PREMISE | 2 |

### Per axis (13 axes)

| | count |
|---|---|
| Kestrine/Valloran | 5 |
| left/right | 5 |
| progressive/conservative | 5 |
| Encamp/MTGA | 4 |
| progressive mayor/conservative mayor | 4 |
| secular/religious | 4 |
| Kestrine Party/Valloran Party | 3 |
| Kestrine senator/Valloran senator | 3 |
| Solidarist/Preservation government | 3 |
| Verdant Party/Freehold Party | 3 |
| left-wing/right-wing activists | 3 |
| tenant/landlord | 3 |
| union/company | 3 |

### Moves per axis

| axis | rules |
|---|---|
| Encamp/MTGA | DISSENT_DISMISSAL, FEAR_URGENCY, MONOCAUSAL_BLAME, SHAME_LEVER |
| Kestrine Party/Valloran Party | FEAR_URGENCY, INSTITUTIONAL_POSITION_AS_SETTLED, TOTALIZING_HARM_LANGUAGE |
| Kestrine senator/Valloran senator | DISSENT_DISMISSAL, INEVITABILITY_FRAME, SHAME_LEVER |
| Kestrine/Valloran | CONSENSUS_AS_EVIDENCE, DISSENT_DISMISSAL, FALSE_BINARY, SHAME_LEVER, VAGUE_INSTITUTIONAL_APPEAL |
| Solidarist/Preservation government | CONSENSUS_AS_EVIDENCE, FEAR_URGENCY, MONOCAUSAL_BLAME |
| Verdant Party/Freehold Party | CLAIM_WITHOUT_CITATION, CONSENSUS_AS_EVIDENCE, INEVITABILITY_FRAME |
| left-wing/right-wing activists | FALSE_BINARY, INSTITUTIONAL_POSITION_AS_SETTLED, VAGUE_INSTITUTIONAL_APPEAL |
| left/right | CREDENTIAL_AS_PREMISE, EMOTIONAL_SUBSTITUTION, FALSE_BINARY, INSTITUTIONAL_POSITION_AS_SETTLED, SOFT_CONSENSUS |
| progressive mayor/conservative mayor | EMOTIONAL_SUBSTITUTION, MORAL_HIGH_GROUND, TOTALIZING_HARM_LANGUAGE, VAGUE_INSTITUTIONAL_APPEAL |
| progressive/conservative | CLAIM_WITHOUT_CITATION, COMPETENCE_DISMISSAL, INEVITABILITY_FRAME, MONOCAUSAL_BLAME, MORAL_HIGH_GROUND |
| secular/religious | CLAIM_WITHOUT_CITATION, COMPETENCE_DISMISSAL, SHAME_LEVER, SOFT_CONSENSUS |
| tenant/landlord | COMPETENCE_DISMISSAL, MORAL_HIGH_GROUND, TOTALIZING_HARM_LANGUAGE |
| union/company | CREDENTIAL_AS_PREMISE, EMOTIONAL_SUBSTITUTION, SOFT_CONSENSUS |

Every axis has at least 3 different moves.

## Controls

### Per rule (16 rules)

| | count |
|---|---|
| CLAIM_WITHOUT_CITATION | 2 |
| CONSENSUS_AS_EVIDENCE | 2 |
| DISSENT_DISMISSAL | 2 |
| FALSE_BINARY | 2 |
| FEAR_URGENCY | 2 |
| MONOCAUSAL_BLAME | 2 |
| SHAME_LEVER | 2 |
| SOFT_CONSENSUS | 2 |
| COMPETENCE_DISMISSAL | 1 |
| CREDENTIAL_AS_PREMISE | 1 |
| EMOTIONAL_SUBSTITUTION | 1 |
| INEVITABILITY_FRAME | 1 |
| INSTITUTIONAL_POSITION_AS_SETTLED | 1 |
| MORAL_HIGH_GROUND | 1 |
| TOTALIZING_HARM_LANGUAGE | 1 |
| VAGUE_INSTITUTIONAL_APPEAL | 1 |

### Per topic (11 topics)

| | count |
|---|---|
| health | 3 |
| taxes | 3 |
| climate/energy | 2 |
| faith-and-public-life | 2 |
| foreign aid | 2 |
| housing | 2 |
| immigration | 2 |
| labor | 2 |
| policing | 2 |
| schools | 2 |
| speech | 2 |

