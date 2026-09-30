# 03 Waves

Target state: refactor. Given by the `--target` flag.

## The plan is one wave

The tree holds four programs and one call chain. It has no JCL job, no proc, no scheduler job, no dataset
and no copybook. The skill says a system of this size is one wave, so it is one wave. I did not invent a
second one.

| Wave | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|
| 1. CICS routing chain | PROGB, PROGC, PROGD, PROGA | medium | low | `app/cbl/PROGA.cbl:12`, `app/cbl/PROGA.cbl:16`, `app/cbl/PROGA.cbl:20`, `app/cbl/PROGA.cbl:23` |

Why not two waves, the leaves first and PROGA second:

- The computed LINK at `app/cbl/PROGA.cbl:16` can name PROGB, PROGC or PROGD, or any other program in the
  region. No boundary between PROGA and its callees can be proven, so the "testable boundary" test fails
  for a split (inference).
- Splitting the leaves off delivers nothing a stakeholder can name. Each is a bare RETURN
  (`app/cbl/PROGB.cbl:4`). A wave that delivers nothing is a chore, so it merges into its neighbor.

## Quadrants, and one thing to say plainly

The scores are in `risks.json`. PROGB, PROGC and PROGD are low-low. PROGA is high-high, because of the
computed LINK and the one way XCTL (`app/cbl/PROGA.cbl:15-20`).

The rule is that a high-high unit goes last and is strangled behind a facade, not ported. This plan puts a
high-high unit in the first and only wave. That is unavoidable when the system has a single entry program.
The mitigation is the order inside the wave: port PROGB, PROGC and PROGD first, then put PROGA behind a
routing facade that keeps the dispatch on a caller supplied name and keeps the XCTL "does not return"
behavior. Do not port PROGA as a straight transliteration.

The scores for PROGA rest on thin evidence. Its callers and its COMMAREA contract are not in the tree.
Treat 3 and 3 as a floor.

## Wave 1 in detail

| Item | Content | Confidence | Evidence |
|---|---|---|---|
| Units | PROGB, PROGC, PROGD, then PROGA | low | `app/cbl/PROGA.cbl:12-25` |
| Rationale | One chain, nothing to cut. See above | low | inference |
| Unblocks | The toolchain and harness proof for CICS LINK and XCTL dispatch. It does not unblock the nightly batch cycle, which has no artifact in the tree | low | inference |
| Deployable independently | Yes, behind a facade that routes by the COMMAREA name. Needs the CSD to confirm which transactions start PROGA | low | inference |
| Rollback | Route the transaction back to the legacy PROGA. No data is written, so nothing needs reversing | medium | `app/cbl/PROGA.cbl:1-26` |
| Testable boundary | The COMMAREA in, the sequence of programs invoked and the abend or return condition out | medium | inference |
| Stakeholder name | "The routing transaction" (name to be confirmed by the client) | low | inference |

## What I would cut if the system were ten times larger

Forty programs with the same shape would be cut along these lines:

1. Leaf programs that only RETURN or do local work, with no shared dataset, go first. They are low-low.
   They prove the toolchain.
2. Programs that share a dataset or a record layout move together, or the writer moves after its readers
   are covered by the harness. The data hubs and medium confidence contract edges in `graph.json` say
   which.
3. Router programs with computed dispatch, like PROGA, move last. Each is put behind a facade. The
   dispatch table is recovered from the callers first.
4. Any strongly connected component moves as one unit. Any god module is strangled.
5. The nightly batch cycle would be its own set of waves, ordered by the scheduler's temporal edges, and
   would need the JCL and scheduler definitions the tree does not contain.

## The nightly batch cycle

The must-not-break item is not in the tree, so it cannot be assigned to a wave, and no unit here can be
shown to sit on its path. That is not the same as the two being unrelated. See `00-summary.md`, Open
Questions.
