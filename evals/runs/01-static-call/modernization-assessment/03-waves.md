# 03 Waves

Target state: refactor. The scoping answer was given as a flag (`--target refactor`). The plan is in
`waves.json`. Risk scores are in `risks.json`.

## One wave

The tree is one batch driver and the one subprogram it calls (`app/cbl/PROGA.cbl:6`). There is no shared
dataset, no cycle, no articulation point and no god module (`02-coupling.md`). Cutting this into more
than one wave would invent a boundary that carries no data and no parameters. So the plan is a single wave.

| Wave | Units | Blast radius | Unblocks | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | PROGA, PROGB | low | The toolchain, the harness and the CALL boundary are proven end to end. Once the missing JCL and scheduler arrive, it is the first cut of the nightly batch cycle. | low | `app/cbl/PROGA.cbl:6`, `app/cbl/PROGB.cbl:4` |

Both units score 1 on port difficulty and 2 on blast radius, which is `low-low`, the wave one quadrant
(`risks.json`). Confidence is low for two reasons. First, the tree has no JCL or scheduler, so nothing
ties these programs to the nightly batch cycle the client named. That link is inference. Second, PROGB
is a bare `GOBACK` (`app/cbl/PROGB.cbl:4`). The source in the tree may not match the load module
that runs in production.

## Why the order rule does not bite

The rule is that early waves maximize learning per unit of blast radius. With one wave, that is trivially
satisfied. The wave is also the whole system, so it is "wave one" and "the last wave" at once. A wave
that proves the toolchain on the whole system carries a real risk: there is no easier place to learn
first. If the nightly cycle turns out to be much larger than this tree, this wave becomes the pilot.

## What I would cut if the system were ten times larger

Inference, since nothing in this tree shows it. I would cut along dataset seams first, then along
scheduler order.

1. Wave 1: the programs with no shared datasets and low fan-in. They prove the toolchain and the harness.
2. Wave 2: programs that write a dataset only one other program reads, where both sides share a layout
   copybook (`high` contract edges).
3. Later waves: the programs on the datasets with the most readers (data hubs), and anything with
   `medium` contract edges. Those go last, behind a facade.
4. Strongly connected components move as one unit. God modules are strangled, not ported.

## Assumptions the wave plan depends on

| Assumption | If it is false | Evidence |
|---|---|---|
| PROGA is started by something outside the tree, and PROGB is not called from elsewhere. | If another job also calls PROGB, or runs PROGA in a different order, the wave gains temporal edges and may need splitting. | inference |
| The source in the tree is the source of the load modules that run. | If PROGB in production is larger than four lines, the risk scores are wrong. | `app/cbl/PROGB.cbl:4` |
