# 03 Waves

Target state: refactor (`modernization-assessment/waves.json:2`). Refactor means the same behavior in restructured code. Here the
"code" is two do-nothing JCL jobs and a scheduler file, so what gets restructured is the schedule and its conditions.

The plan is the extractor's seed (`03a-wave-seed.md`), kept as it was. The seed cut one wave. I found no reason to change it.

## The plan

| Wave | Family | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | batch-utility | `job:JOBA`, `job:JOBB`, `sch:NIGHTLY/JOBA`, `sch:NIGHTLY/JOBB` | medium | medium | `app/jcl/JOBA.jcl:1`, `app/jcl/JOBB.jcl:1`, `modernization-assessment/waves.json:5` |

There is one wave. No unit is left unplaced (`modernization-assessment/waves.json:24`) and there are no deviations (`modernization-assessment/waves.json:25`).

## Wave 1. Nightly batch cycle: JOBA then JOBB

**Why it is one wave.** The four units have one coupling between them, the JOBA-DONE condition (`app/scheduler/nightly.xml:6`,
`app/scheduler/nightly.xml:9`). It forces JOBA before JOBB. Splitting the pair across waves would put a scheduler order across a wave
boundary, so it stays whole.

**The four wave tests.**

| Test | Answer | Evidence |
|---|---|---|
| Deploys independently, behind a flag or facade | Yes. Nothing outside the folder calls into it and the jobs share no dataset. The switch is which scheduler holds the NIGHTLY folder. | `app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2` |
| Rolls back independently | Yes, by re-enabling the legacy folder. The catch is the conditions: EXTERNAL-FEED must reach one scheduler only, and JOBB-DONE must go to the same consumer as before. | `app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:11` |
| Has a testable boundary | Yes. Assert the order of the two jobs, the conditions each sets and clears, and each return code. There is no data at the boundary. | `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9`, `app/scheduler/nightly.xml:10` |
| Delivers something a stakeholder can name | Yes: the nightly batch cycle, the item the client said must not break. The name match to the folder is inference. | `app/scheduler/nightly.xml:3` |

**What it unblocks.** Nothing else in this tree. It is the only wave, and no program, dataset or copybook depends on it. By
dependency it is a chore. It matters because it is the client's must-not-break item, and because it pins the condition contract
(EXTERNAL-FEED in, JOBB-DONE out) that any later scheduler port has to keep.

**Confidence is medium, not high.** The sequence is not in doubt, because there is only one wave and one internal order. What is in doubt
is whether the tree is the whole cycle (inference). Both jobs run only IEFBR14 (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`), which
does nothing. Either the real work sits in members we were not given, or the cycle is a set of pure scheduling signals. I did not
raise the confidence above medium, and I did not lower it further, because no edge is low confidence and there are no computed calls.

**Blast radius is medium.** The jobs do no work in this tree, so a bad port cannot corrupt data here. What it can do is start the cycle at the wrong time,
run JOBB before JOBA, or fail to set JOBB-DONE, and any of those is silent if nobody watches the folder (inference).

## Risk quadrants and how they were used

Both jobs score low port difficulty and blast radius 3, which the plugin calls low-high (`modernization-assessment/risks.json:13`,
`modernization-assessment/risks.json:42`). A low-high unit is safe to do early, once the equivalence harness is proven. Its wave is the
first and only one, so the quadrant and the family agree and no move was needed (rule 4 of the change reasons does not fire).

| Reason to change the plan | Fired | Evidence |
|---|---|---|
| Must-not-break item, strongly connected component or facade forces a move | No. The must-not-break item maps to this wave already, and there is no strongly connected component | analysis: `sccs` is empty |
| A wave over 25 units needs a cut | No. The wave holds 4 units | `modernization-assessment/waves.json:8` |
| Something the extractor could not see changes what a unit is | No. No computed call, nothing unparsed, no JCL text in a COBOL literal | analysis: `unresolved_dynamic`, `embedded_jcl` and `unparsed` are empty |
| A high-high unit sits in an early family | No. There is no high-high unit | `modernization-assessment/risks.json:13` |

## Not placed

Nothing. Every unit is placed (`modernization-assessment/waves.json:24`).
