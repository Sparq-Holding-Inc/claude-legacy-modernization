# Waves

Target state: refactor. The extractor's seed placed every unit in one family (03a-wave-seed.md). I made no
changes, so `deviations` is empty.

| Wave | Name | Units | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|---|
| 1 | MAINJOB batch chain | job:MAINJOB, PGMMAIN, OLDPGM, NEWPGM | low | medium | Nothing in the tree. It proves the toolchain and the harness. | app/jcl/MAINJOB.jcl:2, app/cbl/PGMMAIN.cbl:4, app/cbl/PGMMAIN.cbl:5 |

## Why one wave

- The four units have one entry point, `job:MAINJOB` (app/jcl/MAINJOB.jcl:1).
- They share no dataset, copybook or DD (meta.files_seen shows no copybooks), so no data or contract edge
  crosses a possible cut.
- Cutting at the articulation point `PGMMAIN` (analysis.articulation_points) would leave a wave with no
  testable boundary. The boundary that exists is the job's output.
- It deploys behind a flag at the job level, rolls back by running the legacy job, and delivers the nightly
  batch cycle the client named (the mapping of that cycle to `job:MAINJOB` is inference).

## Confidence is medium, not high

- No scheduler was parsed (analysis.warnings). The job may be one of many in the nightly cycle (inference).
- The bodies hold no logic (app/cbl/PGMMAIN.cbl:6), so the port is trivial, but the behavior that the real
  system exhibits is not in this tree. Ask the client whether the tree is complete.
- There are no computed calls, so no unit's confidence is lowered for that reason.

## Not placed

None. The validator requires every program and job to be placed or listed, and all four are placed.
