# 04 Estimate

Target state: refactor. One wave, so one estimate.

## Method

This is a bottom-up range in person-days, built from the things that move an estimate and not from
line counts. The tree has 32 lines of COBOL and 9 lines of JCL. Lines would give a number too small
to believe. What costs effort here is the boundary and the proof, so I priced those.

| What moves the estimate | What this tree shows | Evidence |
|---|---|---|
| Coupling edges crossing the wave boundary | None cross it. The one contract edge, writer to reader, sits inside the wave | `app/cbl/PGMW.cbl:13`, `app/cbl/PGMR.cbl:13` |
| A behavioral oracle | None in the tree. No archived generations or output files were supplied | inference: nothing beyond source was given |
| God modules in the wave | None | inference: `analysis.god_modules` in `graph.json` is empty |
| Business logic held in the database | None seen. Neither program has SQL | `app/cbl/PGMW.cbl:12-16`, `app/cbl/PGMR.cbl:12-16` |
| Whether the team can read the source language | Not stated | inference: the brief did not say |

## Wave 1 range

**About 20 to 45 person-days. Confidence: low.** Elapsed time is roughly 4 to 7 weeks for two
engineers, and most of the slack is waiting for the client to supply the oracle (inference).

| Activity | Low | High | Evidence |
|---|---|---|---|
| Target runtime, build and CI set up | 4 | 10 | inference: the target platform was not named |
| Get the oracle from the client: archived files, job logs, catalog entry | 3 | 8 | inference: nothing in the tree supplies one |
| One shared copybook, with proof the bytes are unchanged | 1 | 2 | `app/cpy/LAYOUTX.cpy:2`, `app/cpy/LAYOUTY.cpy:2` |
| Harness: normalization, decimal compare, order check, boundary cases | 6 | 12 | `app/cpy/LAYOUTX.cpy:3` |
| Port two programs and two jobs | 3 | 6 | `app/cbl/PGMW.cbl:14`, `app/jcl/WRITEJOB.jcl:3` |
| Replay, parallel run, deviation register sign-off | 4 | 8 | inference: sign-off time depends on who the client names |
| **Total** | **21** | **46** | inference: the sum of the rows above |

## The assumptions this range is most sensitive to

1. **Assumes `SPARQ.TEST.MASTER` has exactly one writer and one reader.** If another job, a partner
   extract or a utility step also reads it, each one adds a contract to verify, roughly 3 to 5
   person-days apiece. The tree cannot show readers that live outside it.
   Evidence: `app/jcl/READJOB.jcl:3`.
2. **Assumes the two programs are the whole story, at 16 lines each.** If the real writer fills the
   amount by calculation, the rounding and accumulation rules become the work, and the port and the
   harness roughly double. `PGMW` today never sets a field. Evidence: `app/cbl/PGMW.cbl:14`.
3. **Assumes a legacy environment can run the old jobs to produce the oracle.** If it cannot, the
   oracle falls back to tests written from the source, coverage is provisional, and the harness line
   rises by about half. Evidence: inference, no runtime was described.
4. **Assumes `LRECL=80` against a 15 byte record is a padding question and not an open failure.**
   If it is padding, add 1 to 2 days for a normalization rule. If the real JCL differs from this
   copy, the range should be redone once the real catalog entry is in hand.
   Evidence: `app/jcl/WRITEJOB.jcl:4`.

## Where Claude Code helps, and where it does not

| Work | Claude Code | Why | Evidence |
|---|---|---|---|
| Moving `PGMW` and `PGMR` to the target language | Strong, with the harness in place | Plain file I/O and one packed decimal record. Transliteration with a good test harness is its strength | `app/cbl/PGMW.cbl:13`, `app/cbl/PGMR.cbl:13` |
| Building the one shared record definition | Strong | Two copybooks that are identical except for names | `app/cpy/LAYOUTX.cpy:1`, `app/cpy/LAYOUTY.cpy:1` |
| Writing the harness code | Strong | Byte and decimal comparison is mechanical once the normalization spec is signed | `app/cpy/LAYOUTX.cpy:3` |
| Saying what `LR-AMT` and `LR-KEY` mean | Cannot | The names say nothing, and the code never uses them. That is a question for the client | `app/cpy/LAYOUTX.cpy:2` |
| Saying whether the run order and the `LRECL=80` are correct | Cannot | They live in a scheduler and a catalog that were not supplied | `app/jcl/WRITEJOB.jcl:4` |
| Deciding which differences are intended | Cannot | That is the deviation register. A named person with authority signs it | inference: it needs a human owner |

## What is not in this estimate

The move of the two jobs onto a new scheduler is priced only as far as porting the two JCL members.
The cost of the scheduler itself is not in the tree, because no scheduler export was supplied.
Evidence: `app/jcl/READJOB.jcl:1`.
