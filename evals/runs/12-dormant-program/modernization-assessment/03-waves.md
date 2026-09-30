# 03 Waves

Target state: `refactor` (given as a flag). Ordering rule: the earliest wave maximizes learning per unit of blast radius, not business value. Risk scores are in `risks.json`.

## Decision: one wave

The system is one job, one step and three programs, 16 lines in all (`app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:6`). A system that is one job and a handful of programs is one wave. The alternatives all fail the four tests:

- A wave for OLDPGM and NEWPGM, then a wave for PGMMAIN and MAINJOB, would make a first wave that delivers nothing a stakeholder can name. Each subprogram is a `GOBACK` and nothing else (`app/cbl/OLDPGM.cbl:4`, `app/cbl/NEWPGM.cbl:4`). It also has no boundary of its own to test, since neither reads or writes any data.
- Rollback of the subprograms is not independent of PGMMAIN, which calls both (`app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMMAIN.cbl:5`).

## Wave table

| Wave | Units | Quadrants (port difficulty first) | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|---|
| 1 | `job:MAINJOB`, `PGMMAIN`, `OLDPGM`, `NEWPGM` | low-high, low-high, low-low, low-low | medium | medium | The toolchain and the test harness, on a system with no data coupling. It also settles whether OLDPGM is live. | `app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMMAIN.cbl:5` |

The wave passes the four tests:

1. Independent deploy: swap the one step behind a flag or a facade (`app/jcl/MAINJOB.jcl:2`).
2. Independent rollback: point the step back at the legacy load module.
3. Testable boundary: the step's return code and its job log, since it has no datasets. Weak, and covered in `06-test-strategy.md`.
4. Nameable delivery: a modernized MAINJOB in the nightly cycle. This depends on MAINJOB being part of that cycle, which is inference until a scheduler export arrives.

Two units score `low-high` because their port is trivial but a wrong step in the nightly cycle stops it. The quadrant guide says a `low-high` unit is safe early only once the equivalence harness is proven. With one wave, the harness has to be built first inside the wave. Nothing here is `high-high`.

## What I would cut if this were ten times larger

Inference. I would put the leaf subprograms with no data coupling and no dormant history in the first wave, because they are the `low-low` set. I would leave the caller that makes the articulation point (PGMMAIN here) for a later wave, behind a facade. I would keep any strongly connected component whole. And I would order jobs by the scheduler's before and after edges, which the tree does not give us today.

## Unassigned

None. Every reachable unit is in wave 1.
