# 00 Summary

Assessment of the tree in the current directory: two COBOL programs, two copybooks and two JCL jobs.

## Scoping answers

| Question | Answer | Where it came from |
|---|---|---|
| Target state | refactor | given as `--target refactor` |
| What must not break | the nightly batch cycle | given as `--must-not-break` |
| Runtime telemetry | none | given as `--telemetry none` |

All three came as flags, so no defaults were applied and nothing was assumed. The run was
non-interactive and no one was asked anything. Because telemetry is `none`, every dead-code claim is
provisional.

## The result in five lines

- **Waves: 1.** Two jobs, two programs and one shared dataset are one wave. Cutting it apart would
  fail the independent deploy and rollback tests (`03-waves.md`).
- **Largest risk: the file hand-off between the two jobs.** `PGMW` writes `SPARQ.TEST.MASTER` and
  `PGMR` reads it. Each takes its record layout from a different copybook
  (`app/cbl/PGMW.cbl:11`, `app/cbl/PGMR.cbl:11`). I compared them and they are identical today: ten
  characters and one packed decimal amount (`app/cpy/LAYOUTX.cpy:2-3`, `app/cpy/LAYOUTY.cpy:2-3`).
  Nothing keeps them identical. The extractor marked the link medium confidence for that reason.
- **No scheduler was supplied.** The order `WRITEJOB` then `READJOB` is not written anywhere in the
  tree, and nothing shows either job belongs to the nightly batch cycle.
- **The programs hold no business logic.** Each opens a file, moves one record, and closes it
  (`app/cbl/PGMW.cbl:13-15`, `app/cbl/PGMR.cbl:13-15`). The work is the proof, not the port.
- **Effort: about 20 to 45 person-days, low confidence** (`04-estimate.md`).

## Findings

| Finding | Confidence | Evidence |
|---|---|---|
| Writer and reader share one dataset and no call links them | high | `app/jcl/WRITEJOB.jcl:3`, `app/jcl/READJOB.jcl:3` |
| The two layout copybooks are byte compatible and differ only in field names | high | `app/cpy/LAYOUTX.cpy:2-3`, `app/cpy/LAYOUTY.cpy:2-3` |
| No cycle, no god module, no computed call | high | inference: the extractor's `analysis` block is empty for all three |
| The writer creates the dataset with `DISP=(NEW,CATLG,DELETE)` | high | `app/jcl/WRITEJOB.jcl:3` |
| The DD declares `LRECL=80` and the record is 15 bytes | high for the two facts, low for what happens at run time | `app/jcl/WRITEJOB.jcl:4`, `app/cpy/LAYOUTX.cpy:3` |
| The writer writes a record without setting any field | high | `app/cbl/PGMW.cbl:14` |
| No dead code can be shown, and dormancy cannot be judged at all | low | inference: no dates and no telemetry |

## Open Questions

For the client's own engineers.

1. **Which scheduler runs these two jobs, and are they part of the nightly batch cycle?** No
   scheduler artifact was parsed, so the order across jobs is unknown. The extractor reads only
   Control-M XML and shell wrappers that name JCL files (`meta.limits` in `graph.json`). If yours is
   CA-7, TWS, cron or something else, please send the export in any form. Evidence:
   `app/jcl/READJOB.jcl:3`.
2. **What does the file really look like on disk?** The DD says `RECFM=FB,LRECL=80`
   (`app/jcl/WRITEJOB.jcl:4`) and both copybooks describe 15 bytes (`app/cpy/LAYOUTX.cpy:3`). Send
   the catalog entry. Does the run pad to 80, or does the open fail? The extractor does not read
   DCB parameters at all, so it could not tell (inference).
3. **How does `WRITEJOB` survive its second night?** `DISP=(NEW,CATLG,DELETE)` on a name that already
   exists fails the step (inference). Is something earlier deleting the dataset, is this a
   generation dataset in the real system, or is `SPARQ.TEST.MASTER` a test dataset and the real one
   differs? Evidence: `app/jcl/WRITEJOB.jcl:3`.
4. **Is this the whole system?** The writer sets no field before its write, the reader has no end of
   file handling, and neither has a file status clause (`app/cbl/PGMW.cbl:14`,
   `app/cbl/PGMR.cbl:14`, `app/cbl/PGMR.cbl:6`). If these are stubs, where is the real logic, and which programs use the
   amount? The estimate roughly doubles if the real writer computes it. Evidence: `04-estimate.md`.
5. **Who else reads `SPARQ.TEST.MASTER`?** The layout is copied, not shared, so every other reader
   has its own copy of a 15 byte layout. Include partner extracts and utility steps. The extractor
   does not read IDCAMS or SORT control cards (`meta.limits`). Evidence:
   `app/jcl/READJOB.jcl:3`.
6. **Who owns the layout?** Two files, `LAYOUTX` and `LAYOUTY`, describe one record with different
   names for the same bytes. Which name is right, and who signs a change to it? Evidence:
   `app/cpy/LAYOUTX.cpy:1`, `app/cpy/LAYOUTY.cpy:1`.
7. **Can you send 12 months of job logs or SMF records for both jobs, and file dates for the four
   source members?** The tree is not a git repository, so the extractor read no dates and every unit
   shows "unknown". Without them, the dormant bucket cannot be judged. Evidence: inference, from
   `git_dates` being false in `graph.json`.

## Files the extractor could not parse

None. `unparsed` in `graph.json` is empty. All six source files parsed.

## Limits in `meta.limits` that touch this system

| Limit | Touches this tree | Evidence |
|---|---|---|
| Only Control-M XML and shell wrappers are read as schedulers | Yes. No scheduler was found, so cross-job order is unknown | inference: `analysis.warnings` in `graph.json` |
| IDCAMS, SORT and other in-stream control cards are not read | Only for steps outside this tree. Neither job has a utility step | `app/jcl/WRITEJOB.jcl:2`, `app/jcl/READJOB.jcl:2` |
| IF/THEN/ELSE and COND= in JCL are not modeled | No effect. Neither job uses them | `app/jcl/WRITEJOB.jcl:1-5`, `app/jcl/READJOB.jcl:1-4` |
| Nested PROC calls, INCLUDE members and the internal reader are not followed | No effect. Neither job uses a PROC | `app/jcl/WRITEJOB.jcl:2`, `app/jcl/READJOB.jcl:2` |
| A called subprogram gets no DDs from its caller's step | No effect. Neither program makes a call | `app/cbl/PGMW.cbl:12-16`, `app/cbl/PGMR.cbl:12-16` |
| A variable call target is resolved only from VALUE and literal MOVE | No effect. There are no calls | `app/cbl/PGMW.cbl:12-16`, `app/cbl/PGMR.cbl:12-16` |
| COPY REPLACING is not applied | No effect. Both COPY statements are plain | `app/cbl/PGMW.cbl:11`, `app/cbl/PGMR.cbl:11` |
| COBOL is read as fixed format | No effect. Both programs parsed | `app/cbl/PGMW.cbl:1`, `app/cbl/PGMR.cbl:1` |
| CICS RETURN TRANSID, START and SEND MAP are not edges | No effect. There is no CICS | `app/cbl/PGMW.cbl:12-16`, `app/cbl/PGMR.cbl:12-16` |

One limit is missing from that list: the extractor does not read DCB parameters such as `LRECL`, and
`meta.limits` does not say so. It matters here (question 2).

## Provisional throughout

No telemetry was given. The dead-code register is empty, and its empty dormant list means "cannot
tell". See `05-dead-code.md`.

## What is in this folder

| File | Written by |
|---|---|
| `graph.json`, `01-inventory.md`, `02a-edge-tables.md`, `05a-dead-code-candidates.md` | scripts |
| `02-coupling.md`, `03-waves.md`, `waves.json` | assessment |
| `04-estimate.md`, `05-dead-code.md`, `dead-code.json`, `risks.json` | assessment |
| `06-test-strategy.md` | assessment, following the `behavioral-equivalence` skill |
