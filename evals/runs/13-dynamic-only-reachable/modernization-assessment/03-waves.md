# 03 Waves

Target state: refactor. The plan is in `waves.json`. Risk scores are in `risks.json`, written by the
`migration-risk-assessor` steps, which I followed inline.

## One wave, on purpose

The tree is one job, one step and two programs (`app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:9`,
`app/cbl/HIDDEN01.cbl:1`). It has no strongly connected component, no articulation point and no shared
dataset. There is nothing to cut along. I did not invent a second wave to make the plan look
substantial.

If the system were ten times larger, I would cut it this way, in this order. This is inference:

1. The leaf programs with no computed calls and no shared datasets, to prove the toolchain and the
   test harness.
2. The programs that share datasets, cut along the writer to reader contracts, once the harness works.
3. The dispatcher `PGMMAIN` and its targets last, behind a facade. It is high-high, and the risk
   quadrants say that belongs at the end.

## Risk scores that drive the plan

Port difficulty and blast radius are scored separately. They are not added or multiplied.

| Unit | Port difficulty | Blast radius | Quadrant | Confidence | Evidence |
|---|---|---|---|---|---|
| `job:MAINJOB` | 1 | 3 | low-high | low | `app/jcl/MAINJOB.jcl:2` |
| `PGMMAIN` | 3 | 4 | high-high | medium | `app/cbl/PGMMAIN.cbl:9` |
| `HIDDEN01` | 1 | 2 | low-low | low | `app/cbl/HIDDEN01.cbl:4` |

## Wave 1: main job and its dispatcher

| Field | Value | Evidence |
|---|---|---|
| Units | `job:MAINJOB`, `PGMMAIN`, `HIDDEN01` | `app/jcl/MAINJOB.jcl:2` |
| Blast radius | high | `app/cbl/PGMMAIN.cbl:9` |
| Confidence | low | inference |
| Unblocks | Running the main job off the legacy platform, and a bounded list of the programs `PGMMAIN` can dispatch to | inference |

Why `HIDDEN01` is in the wave. It has no static caller, but a computed call in reachable code could
name it (`app/cbl/PGMMAIN.cbl:9`). If the port left it behind and `PGMMAIN` is given its name, the
call fails. It is four lines and only returns (`app/cbl/HIDDEN01.cbl:4`), so carrying it costs almost
nothing. It stays in the unknown bucket in `dead-code.json`. Moving it with the wave is not a claim
that it runs.

The four validity tests:

| Test | Answer | Evidence |
|---|---|---|
| Deployed independently, behind a flag or facade | Yes, if the new dispatcher sits behind a facade that can route to the legacy job. The job has no DDs, so there is no shared file to move | `app/jcl/MAINJOB.jcl:2` |
| Rolled back independently | Yes, by pointing the scheduler back at the legacy job. This assumes nothing the job runs writes to a system of record in a way that cannot be reversed. That is not known | inference |
| Testable boundary | Only after the input values are known. The job's inputs are `ACCEPT` values, and its outputs are whatever the called program produces | `app/cbl/PGMMAIN.cbl:8` |
| Business stakeholder can name it | "The nightly batch cycle moves off the mainframe", if `job:MAINJOB` is part of that cycle. The tree does not show that | inference |

## A high-high unit in the first half

The rule says: if a plan puts a high-high unit in the first half, say so plainly. `PGMMAIN` is
high-high (`risks.json`) and it is in the only wave. The system gives no alternative. So the wave is
planned with three conditions, and it does not start until the first two are met:

1. The set of names `PGMMAIN` has ever been given is known. That comes from job logs and `SYSIN`
   history, not from the source (inference, `app/cbl/PGMMAIN.cbl:8`).
2. Every program in that set is in the tree, or it is added to the scope and this plan is redone
   (inference).
3. The port keeps the dispatch behind a facade, so the legacy job can take the traffic back.

Under a refactor target, the dispatcher becomes an explicit registry of the known targets instead of a
free `CALL` on an input string. That is a behavior change on purpose. Any name that used to be
accepted and is not in the registry goes into the deviation register (see `06-test-strategy.md`).

## What the client asked to protect

The client said the nightly batch cycle must not break. The tree holds one job and no scheduler, so I
cannot say which jobs make up the cycle, what runs before `job:MAINJOB` or what runs after it. The
extractor warned about this (`app/jcl/MAINJOB.jcl:1`). Until the scheduler export arrives, the order
constraint that matters most to that requirement is unknown, and this plan cannot vouch for it.
