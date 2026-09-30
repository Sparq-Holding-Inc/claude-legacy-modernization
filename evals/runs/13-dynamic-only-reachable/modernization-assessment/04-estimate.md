# 04 Estimate

Target state: refactor. There is one wave, so there is one estimate. Every figure below is
inference. It comes from the size of the tree and from how much of the work depends on facts the tree
does not hold. It is not measured, and no oracle for it exists yet.

## Method

I did not size this by lines of code. The tree has 14 lines of COBOL and 2 lines of JCL
(`app/cbl/PGMMAIN.cbl:10`, `app/cbl/HIDDEN01.cbl:4`, `app/jcl/MAINJOB.jcl:2`), and that number
predicts nothing. I sized it by what moves the cost, in the order the skill gives:

| Driver | State in this tree | Evidence |
|---|---|---|
| Coupling edges crossing the wave boundary | None visible. One unresolved computed call leaves the boundary open | `app/cbl/PGMMAIN.cbl:9` |
| Behavioral oracle available | None in the tree. No datasets, no archived output, no captured input | inference |
| God modules in the wave | None | inference |
| Business logic in the database | Unknown. No DB2 access is visible in the two programs | `app/cbl/PGMMAIN.cbl:1-10` |
| Someone who can read the source language | Unknown. Ask the client | inference |

## Range for wave 1

Person-days of one engineer who can read COBOL. These are rough ranges.

| Work item | Low | High | Depends on | Evidence |
|---|---|---|---|---|
| Mechanical port of the two programs and the job step | 0.5 | 1.5 | Nothing outside the tree | inference |
| Find the set of names `PGMMAIN` is given, from job logs and `SYSIN` history | 3 | 10 | Whether the client keeps run history | `app/cbl/PGMMAIN.cbl:8` |
| Port or wrap each program in that set | 0 | not bounded | How many targets are outside the tree | `app/cbl/PGMMAIN.cbl:9` |
| Build the comparison harness and gather the oracle, including a month-end and a year-end run | 5 | 15 | Whether archived job output exists | inference |
| Facade, cutover and rollback rehearsal | 2 | 4 | The scheduler export | inference |

For the items that are bounded, the total is about 10 to 30 person-days. That is two to six weeks for
one engineer. The upper bound is not real. The third row has no upper limit, and the total is only as
good as the assumption that the target set is small and in the tree.

## The assumptions this range is most sensitive to

Each one is a claim that can be checked.

1. **The names given to `PGMMAIN` over the last 12 months can be recovered from job logs, and they
   all name programs in this tree.** If they do, the range holds. If even a few name programs that are
   not in the tree, each one adds a full port and equivalence effort, and wave 1 grows by an amount
   this assessment cannot give. The assessment would then be under-scoped.
2. **`HIDDEN01`, which only returns, is the only program the tree holds that `PGMMAIN` could call.**
   This is the reason for the 0 to "not bounded" range in the third row (inference,
   `app/cbl/HIDDEN01.cbl:4`).
3. **`job:MAINJOB` has no hidden inputs.** The JCL as delivered has no DD statements
   (`app/jcl/MAINJOB.jcl:2`). If the real job has a `SYSIN`, a proc or overrides that were not copied,
   the harness cost moves to the top of its range or beyond it, because dataset coupling would appear
   that this graph does not show.

## Where Claude Code helps and where it does not

| Part | Claude Code | Evidence |
|---|---|---|
| Transliterate `PGMMAIN` and `HIDDEN01` to the target language, with a test harness | Strong. The code is ten and four lines | `app/cbl/PGMMAIN.cbl:1-10` |
| Replace the free `CALL` with an explicit registry of targets | Strong, once the target set is given | `app/cbl/PGMMAIN.cbl:9` |
| Work out which names the job was ever given | Cannot do it from the source. It needs job logs and someone who knows the run | `app/cbl/PGMMAIN.cbl:8` |
| Decide what a blank, unknown or self-referencing name should do | Cannot infer intent from undocumented behavior. The source has no `ON EXCEPTION` clause, so there is no stated rule to copy | `app/cbl/PGMMAIN.cbl:9` |
| Confirm which jobs make up the nightly batch cycle | Cannot do it from this tree. Needs the scheduler export | inference |
