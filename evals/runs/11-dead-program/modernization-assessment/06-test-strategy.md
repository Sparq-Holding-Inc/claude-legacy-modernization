# 06 Test strategy

Skill applied: `behavioral-equivalence`. "Correct" for this system means: for the inputs the nightly batch cycle really sees, the refactored cycle produces the same outputs as MAINJOB, and any difference was decided on purpose and written down.

## The problem with this tree

The tree holds no dataset. MAINJOB has no DD statement (`app/jcl/MAINJOB.jcl:2`). Neither live program opens a file (`app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMLIVE.cbl:4`). The extractor found no data edge (`modernization-assessment/graph.json:184`). So there is no output to diff, and the oracle has to come from outside the tree: job output, logs and reports. The plan below says what to ask the client to supply.

The anchor is "the nightly batch cycle". That MAINJOB is that cycle is inference. Nothing in the tree links them (`app/jcl/MAINJOB.jcl:1`).

## Oracle for wave 1

In descending order of strength. Different waves may use different oracles. This system has one wave.

| Rank | Oracle | Use for wave 1? | Evidence |
|---|---|---|---|
| 1 | Parallel run. Run MAINJOB and the refactored job on the same nightly inputs and diff the outputs. | Preferred. Ask whether it is possible before settling for less. A batch job that writes nothing irreversible is the easiest case for it. Whether it writes anything irreversible is unknown (inference). | inference |
| 2 | Replay of captured production inputs. | Only if the client can supply inputs. The tree shows none. The capture window must include month-end and, for anything financial, fiscal year-end. | `app/jcl/MAINJOB.jcl:2` |
| 3 | Golden master from archived outputs: job logs and SYSOUT, GDG generations, report archives, extracts sent to partners. | The likely fallback. Each archived run is a dated test case. | inference |
| 4 | Characterization tests generated from the source. | Provisional only. The source says the chain returns and does nothing else, so the test asserts a return code. That encodes what the code says, not what the cycle does. | `app/cbl/PGMLIVE.cbl:4` |

## What to ask the client to supply

1. The scheduler export for the nightly cycle, and confirmation of which job or jobs make it up.
2. Job logs and SYSOUT for at least 12 months, including a month-end and a fiscal year-end run.
3. Every file, report or extract the cycle produces or sends out, with archived generations.
4. The return code and job completion condition that operations treat as success.
5. Confirmation that PGMMAIN and PGMLIVE here are the production source, not stubs.

## Normalization spec (draft, needs a human sign-off)

Each line is a claim that a difference does not matter. Keep the list short.

| Item | Rule | Evidence |
|---|---|---|
| Job number, run id, timestamps, elapsed time, page numbers in SYSOUT | Mask before diffing | inference |
| Return code | Compare exactly. No tolerance. | `app/jcl/MAINJOB.jcl:2` |
| Numeric fields | None seen in the live tree. If outputs carry money, compare in a decimal type with zero tolerance. Never use floats. | inference |
| Record order | Treat as significant until a downstream consumer is shown not to depend on it | inference |
| Padding and low values in fixed-width records | Decide per output file once one is supplied | inference |

## Mainframe traps

None of the listed traps is exercised by the live tree. The unreachable copybook holds a 10 byte alphanumeric field (`app/cpy/UNUSED.cpy:1`), and nothing includes it. There is no packed decimal, no `REDEFINES`, no sort and no keyed file in the live source. Job order: the graph holds no ordering edge across jobs, and no scheduler was parsed (`modernization-assessment/graph.json:197`). These traps could all appear in the production versions of the source if it is not what the tree shows. Re-check when the real source arrives.

## Targeted cases

Production replay covers the common path well and the dangerous paths badly. Add cases for these, once a real input exists:

- month end, quarter end, fiscal year end, leap day and a DST change
- a zero-record run, and a run at the largest volume the legacy cycle ever handled
- bad data already present in the inputs, where the legacy behavior is often neither an error nor a sane result
- any path that runs only at fiscal close. The tree shows no date logic in the three live units (`app/cbl/PGMMAIN.cbl:4`), so any such path lives outside it. Ask.

## Deviation Register

Nothing may differ without a row here. It is empty at the start.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|

## Exit bar for wave 1

Wave 1 is done when all of these hold:

- the replay or parallel-run diff is clean, modulo the normalization spec and the deviation register
- every targeted boundary case passes
- the harness is under version control and runs in CI
- the deviation register is signed by someone with the authority to sign it

Not when the port compiles, and not when it passes tests written beside the port.

## Rollback

Keep MAINJOB as the fallback entry in the scheduler through the shadow period. Rollback is a scheduler switch (inference). It is only safe if the refactored job has not written anything the legacy cycle would then repeat or skip, so confirm what the cycle writes first.

## After cutover

Keep the harness. It becomes the regression suite for the refactored cycle, and it is the only executable specification this system will have.
