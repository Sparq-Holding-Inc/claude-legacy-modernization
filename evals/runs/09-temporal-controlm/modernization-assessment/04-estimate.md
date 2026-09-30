# 04 Estimate

Method: effort per wave as a range in person-days, driven by the factors the skill names, in order of weight. It is not derived from lines of code. There are 4 lines of JCL and 14 lines of scheduler XML, and size is not what moves this estimate. Every number below is `inference`. There is no history of past port velocity to calibrate against.

## Wave 1: Nightly chain JOBA to JOBB

Range: 5 to 12 person-days. `inference`

| Factor | What the tree shows | Effect | Evidence |
|---|---|---|---|
| Coupling edges crossing the wave boundary | Two condition edges reach the edge of the tree: EXTERNAL-FEED in and JOBB-DONE out. No data or call edge crosses it. | Small, but each condition has an unknown owner outside the tree. | `app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:11` |
| Behavioral oracle | None in the tree. No archived output, and the jobs write nothing. The oracle must come from scheduler history. | Most of the effort. Building the ordering trace is the work, not the port. | `app/jcl/JOBA.jcl:2` |
| God modules | None | No effect | `modernization-assessment/graph.json:235` |
| Business logic in the database | Not visible. No SQL, no DB2 table in the tree. | Unknown. `inference` | inference |
| People who can read the source language | Unknown. JCL and Control-M XML are the only languages. | Unknown. `inference` | inference |

Where the time goes (`inference`): about half on the shadow-run harness and the condition trace, a quarter on reproducing the definitions and the delete semantics, a quarter on finding the owners of EXTERNAL-FEED and JOBB-DONE.

### The assumptions this range is most sensitive to

1. **Assumes this tree is the whole nightly cycle.** If JOBB-DONE (`app/scheduler/nightly.xml:11`) is waited on by jobs in other folders, every such job joins wave 1, and the range scales with the number of chains, roughly linearly. If the tree is a fragment, the range is too low.
2. **Assumes the scheduler stays Control-M and the condition names, folder name and ODAT scoping do not change.** That is what refactor normally means. If the cycle moves to another scheduler, the delete of JOBA-DONE (`app/scheduler/nightly.xml:10`) has to be rebuilt and proven, and the range roughly doubles.
3. **Assumes the IEFBR14 steps are the real work.** If they stand in for members not in this tree (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`), the port difficulty scores in `risks.json` are wrong, and the whole estimate has to be redone once those members are supplied.

## Where Claude Code helps and where it does not

| Task | Claude Code | Evidence |
|---|---|---|
| Reading Control-M XML and producing a condition graph, including deletes and external conditions | Strong. This is mechanical. It can also diff the graph before and after a refactor. | `app/scheduler/nightly.xml:10` |
| Building the ordering trace comparer for the shadow run | Strong, once real run history is supplied | inference |
| Copying the JCL and the scheduler definitions into a new layout | Strong. Transliteration with a harness is its best case. | `app/jcl/JOBA.jcl:2` |
| Saying what EXTERNAL-FEED is, who posts it, and who reads JOBB-DONE | Cannot. That knowledge is not in the source. The client's operators must supply it. | `app/scheduler/nightly.xml:5` |
| Knowing when the cycle really runs and what operators do by hand (force OK, manual conditions) | Cannot. The XML holds no schedule and no operator practice. | `app/scheduler/nightly.xml:3` |
| Deciding whether the deletion of JOBA-DONE is intended protection or an accident | Cannot. It is intent, and it is undocumented. | `app/scheduler/nightly.xml:10` |
