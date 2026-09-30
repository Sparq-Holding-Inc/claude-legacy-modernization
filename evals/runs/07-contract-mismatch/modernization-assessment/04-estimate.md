# 04 Estimate

Target state: refactor. These are ranges in person-days for one engineer working with Claude Code. They are
inference, built from the drivers below. They are not measured, and there is no team velocity yet. The tree is 32
lines of COBOL and 9 lines of JCL, so lines of code are not what moves the number. Evidence: `01-inventory.md`
counts, and `app/cbl/PGMR.cbl:1`, `app/cbl/PGMW.cbl:1`.

| Wave | Range (person-days) | What is in it | Confidence | Evidence |
|---|---|---|---|---|
| 1. Reader side | 3 to 6 | Toolchain and CI set up for the first time. A packed decimal decoder. A ported reader. Golden input files (good, short, bad). The shared schema for the file. | medium | `app/cbl/PGMR.cbl:14`, `app/cpy/LAYOUTY.cpy:3` |
| 2. Writer side | 5 to 10 | A ported writer. A decision on record length and on the undefined record content. A parallel run or replay against the legacy job. The retirement of the duplicate copybook. | low | `app/cbl/PGMW.cbl:14`, `app/jcl/WRITEJOB.jcl:4`, `app/cpy/LAYOUTX.cpy:3` |
| Total | 8 to 16 | Both waves. Excludes client review time and the scheduler work for the nightly cycle, which cannot be sized without the scheduler export. | low | analysis: `warnings` in `modernization-assessment/graph.json` |

## Method

The number was built from these drivers, in order of weight. It was not built from lines of code.

| Driver | What the tree shows | Effect on the range | Evidence |
|---|---|---|---|
| Coupling edges crossing the wave boundary | One contract edge, medium confidence, through the dataset | Sets the size of wave 2. It needs a contract test and a decision about the two copybooks | `app/cbl/PGMW.cbl:11`, `app/cbl/PGMR.cbl:11` |
| Behavioral oracle | None in the tree. No archived output, no data file | Pushes both waves to the weak end of the oracle ladder until the client supplies one (see `06-test-strategy.md`) | analysis: `node_counts` in `modernization-assessment/graph.json` |
| God modules | None | No facade work | analysis: `god_modules` in `modernization-assessment/graph.json` |
| Logic in the database | No SQL, no DB2 in the tree | None | inference: `app/cbl/PGMR.cbl:12`, `app/cbl/PGMW.cbl:12` |
| Someone who can read COBOL and JCL | Not known | The code is so small that a reviewer can cover it in an hour. Not a driver here. Inference | `app/cbl/PGMR.cbl:16` |

## The assumptions the range is most sensitive to

Each is a claim that can be checked.

1. **The catalogued file really holds 15 byte records, or the extra bytes hold nothing.** WRITEJOB asks for
   LRECL=80 but the layout is 15 bytes. If the real dataset has meaningful data beyond byte 15, the two
   copybooks describe a fraction of the file, and both waves roughly grow by half, because the reader and the
   writer both have to model the rest. Evidence: `app/jcl/WRITEJOB.jcl:4`, `app/cpy/LAYOUTX.cpy:3`.
2. **No program outside this tree reads or writes `SPARQ.TEST.MASTER`.** If there is a third reader, wave 2
   gains roughly one wave 1 reader's worth of work per extra reader, because each needs the contract test.
   Inference. Evidence: `app/jcl/READJOB.jcl:3`.
3. **The legacy output of PGMW can be repeated byte for byte, or the varying bytes can be masked.** PGMW moves
   nothing into its record before writing it. If the content changes from run to run, the diff needs a mask
   for those bytes and the oracle gets weaker, which adds about two to three days to wave 2. Inference.
   Evidence: `app/cbl/PGMW.cbl:14`.

## Where Claude Code helps and where it does not

| Work | Claude Code | Why | Evidence |
|---|---|---|---|
| Transliterating open, read, write and close in both programs | Strong | Sixteen lines each, no branches, no computed calls | `app/cbl/PGMR.cbl:13`, `app/cbl/PGMW.cbl:13` |
| A packed decimal codec for `S9(7)V99` in the target, with a decimal type and zero tolerance | Strong, with a test harness | A well-defined format, and the same field in both copybooks | `app/cpy/LAYOUTX.cpy:3`, `app/cpy/LAYOUTY.cpy:3` |
| Turning the two JCL jobs into orchestrator definitions | Strong for the shape, weak for the intent | It cannot know the intended record length or the rerun rule | `app/jcl/WRITEJOB.jcl:3`, `app/jcl/WRITEJOB.jcl:4` |
| Deciding what PGMW is meant to write, and whether `LR-AMT` and `LY-VALUE` mean the same thing | Cannot | The source has no rule to read. Someone has to say. Inference | `app/cbl/PGMW.cbl:14`, `app/cpy/LAYOUTY.cpy:3` |
| Placing the two jobs in the nightly cycle | Cannot | The scheduler was not supplied | analysis: `warnings` in `modernization-assessment/graph.json` |

## How to read this

Wave 1 is a low value chore that proves the toolchain and produces the shared schema. Most of the money is in
wave 2, and most of wave 2 is the verification of the file, not the port. Inference. Evidence:
`app/cbl/PGMR.cbl:14`, `app/jcl/WRITEJOB.jcl:4`.
