# 03 Waves

Target state: refactor. Machine form: `modernization-assessment/waves.json`.

## What the seed gave

The extractor placed no unit in any wave. It found no entry point: no CSD transaction, no JCL job, no
scheduler job and no shell wrapper (analysis: `entry_points`, `wave_seed`; `03a-wave-seed.md`). The seed
groups units by the family of the entry points that use them, so with no entry point it has nothing to
group. All four programs came back "not placed".

## The plan

One wave. It is a placeholder, and I say so plainly. The validator rejects a plan with no wave, and the
four programs cannot honestly be left out of the plan, so they are placed together by deviation. The plan
is not an argument that this is the right sequence. It is the smallest claim the evidence supports: these
four programs move as one call tree.

| Wave | Family | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | none, no entry point found | PROGA, PROGB, PROGC, PROGD | medium | low | `app/cbl/PROGA.cbl:12`, `app/cbl/PROGA.cbl:16`, `app/cbl/PROGA.cbl:20`, `app/cbl/PROGA.cbl:23` |

**Port order inside the wave.** PROGB, PROGC and PROGD first: each is a bare RETURN and scores low-low
(`app/cbl/PROGB.cbl:4`, `app/cbl/PROGC.cbl:4`, `app/cbl/PROGD.cbl:4`). PROGA last: it scores high-high, so it
goes last and behind a facade that keeps the COMMAREA program-name contract
(`app/cbl/PROGA.cbl:15-16`). A high-high unit is a candidate for strangling, not for a straight port.

**Why it is one wave.** PROGA is the only articulation point and the only program with callees
(analysis: `articulation_points`, `fan_out`). The leaves have no caller other than PROGA in the tree, but
the LINK at line 16 can reach any program, so they may have other callers I cannot see. There is no
call cycle to keep whole (analysis: `sccs`).

**Does it meet the four tests?**

| Test | Result | Confidence | Evidence |
|---|---|---|---|
| Deployable independently behind a flag or facade | Yes for the four programs together. The unseen callers of PROGA are the open part. | low | inference |
| Rollbackable independently | Yes in principle: the programs hold no data and write nothing. | medium | `app/cbl/PROGA.cbl:12`, `app/cbl/PROGB.cbl:4` |
| Testable boundary | The boundary is the COMMAREA in and the program sequence out. No oracle is in the tree. See `06-test-strategy.md`. | low | inference |
| Delivers something a stakeholder can name | No. No transaction, map, dataset or business function is visible. | high | analysis: `entry_points`, `node_counts` |

It fails the fourth test. It unblocks nothing that can be named. It is a chore until the client supplies
the CSD, the callers of PROGA and the nightly batch cycle.

## The must-not-break item

The client named "the nightly batch cycle". The tree has no batch program, no JCL and no scheduler
definition (analysis: `node_counts`, `meta.files_seen`). All four programs use EXEC CICS, so they are
online programs (`app/cbl/PROGA.cbl:12`). Nothing here ties them to the batch cycle. The item is not in
the tree at all, so it cannot anchor a wave. If a batch job drives any of these programs (through an
external CICS interface, for example), it would have to be found outside this tree (inference).

## Deviations from the seed

All four are placements of units the seed left unplaced. Each is recorded in `waves.json`.

| Unit | From | To | Reason | Confidence | Evidence |
|---|---|---|---|---|---|
| PROGA | not placed | 1 | No entry point exists. A computed LINK from its COMMAREA means it cannot be shown to sit outside any flow. | low | `app/cbl/PROGA.cbl:16` |
| PROGB | not placed | 1 | Linked from PROGA at its first statement. | medium | `app/cbl/PROGA.cbl:12` |
| PROGC | not placed | 1 | Reached from PROGA through WS-NEXT-PGM, which holds only PROGC. | medium | `app/cbl/PROGA.cbl:19`, `app/cbl/PROGA.cbl:20` |
| PROGD | not placed | 1 | Reached from PROGA by constant, but after an XCTL that never returns, so probably never from there. Kept because the COMMAREA-driven LINK could reach it. | low | inference: `app/cbl/PROGA.cbl:23` |

## What would change the plan

- A CSD or transaction list. It would give PROGA an entry point, and the seed would then place it in a
  family (an online transaction that writes nothing another entry point uses falls in the
  `online-readonly` family).
- The callers of PROGA and the values they put in the COMMAREA. They would bound the LINK at line 16.
- The nightly batch cycle. It would add the temporal edges this plan has none of.
