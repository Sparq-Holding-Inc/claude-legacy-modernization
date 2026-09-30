# 04 Estimate

## Method

The plugin estimates per wave and never gives a single number. There are no waves (`modernization-assessment/03-waves.md`), so no per-wave estimate can be made. What follows is a range for the only thing the tree contains, the two programs and the copybook, labeled inference. It says nothing about "the nightly batch cycle", which is not in the tree.

| Scope | Range | Confidence | Evidence |
|---|---|---|---|
| Port PROGA, PROGB and SHARED01 to the refactor target, including a decimal type for the balance field | 1 to 3 engineer days | low | inference |
| Stand up an equivalence harness for those units (see `modernization-assessment/06-test-strategy.md`) | 2 to 10 engineer days, and the range is wide because no oracle is yet known | low | inference |
| Estimate for the nightly batch cycle | cannot be estimated. No JCL, scheduler, dataset or other program of the cycle is in the tree | high | analysis (field `entry_points`) |

The port is small (8 lines per program, 3 lines in the copybook: `app/cbl/PROGA.cbl:8`, `app/cbl/PROGB.cbl:8`, `app/cpy/SHARED01.cpy:3`). The harness is the work, as it is for any low-high or low-low unit whose real behavior is unobserved.

## What the range is most sensitive to

1. **The tree is the whole nightly cycle.** If the tree is an excerpt, as two 8-line programs with no file access suggest, the estimate for the cycle is not "small". It is unknown. If the cycle holds more programs and jobs than these two, this file's numbers do not apply to it.
2. **A production oracle exists.** If archived outputs or job logs for the cycle can be had, the harness is at the low end of its range. If the only oracle is characterization tests generated from source, the harness is weak and the coverage is provisional, since these programs produce no output to characterize (`app/cbl/PROGA.cbl:7`).
3. **No program outside the tree writes or reads a record laid out by SHARED01.** If one does, the layout is an undocumented API to that dataset, the packed decimal field at `app/cpy/SHARED01.cpy:3` becomes a live risk, and the port range roughly doubles, because every writer and reader of the record must move or be checked.

## Where Claude Code can do the port and where it cannot

| Part | Claude Code | Confidence | Evidence |
|---|---|---|---|
| Transliterate the two programs and the copybook | Strong. The programs move a literal and return, and the copybook has two fields | high | `app/cbl/PROGA.cbl:7`, `app/cpy/SHARED01.cpy:2` |
| Choose the target type for `SH-BALANCE` | Can propose a decimal type. A human must sign it off | medium | `app/cpy/SHARED01.cpy:3` |
| Say what the literals `1` and `2` mean | Cannot. They look like hard coded customer ids and nothing in the source explains them | high | `app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7` |
| Say how the programs sit in the nightly cycle | Cannot. It needs the client's JCL and scheduler | high | inference |

## Other estimate drivers, checked against this tree

- Coupling edges crossing a wave boundary: no wave, and only 2 include edges (`analysis` field `edge_counts`).
- God modules: none (`analysis` field `god_modules`).
- Business logic in the database: not visible. No SQL in either program.
- Anyone who can read COBOL on the client's team: not known. Ask.
