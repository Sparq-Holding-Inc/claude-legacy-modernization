# 03 Waves

**One wave.** The tree is one JCL job and three programs. Splitting it would cut a temporal chain,
and step order is the only behavior it holds. I did not invent more waves.

Target state is `refactor`, given as a flag. See `00-summary.md`.

## Wave 1: SEQJOB step chain

| Field | Value | Confidence | Evidence |
|---|---|---|---|
| Units | `job:SEQJOB`, `PGMA`, `PGMB`, `PGMC` | high | `app/jcl/SEQJOB.jcl:1`, `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4` |
| Moves with the job, not listed | the four steps, including the second STEP2 that runs IEFBR14 | high | `app/jcl/SEQJOB.jcl:5` |
| Blast radius | medium. SEQJOB is the only job, so it is very likely the nightly batch cycle the client named. That is inference. | low | inference |
| Unblocks | the toolchain, the comparison harness and the scheduler translation for anything larger | low | inference |
| Order inside the wave | step order as written: PGMA, PGMB, PGMC, then IEFBR14 | high | `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`, `app/jcl/SEQJOB.jcl:5` |

## Why it is valid

Each test from the skill, in turn.

| Test | Holds because | Confidence | Evidence |
|---|---|---|---|
| Deploys independently | The job is the only entry point. It can go behind one scheduler entry or one facade. | medium | `app/jcl/SEQJOB.jcl:1` |
| Rolls back independently | Nothing else in the tree reads or writes what it touches. Switch the scheduler entry back to the legacy job. | medium | inference |
| Testable boundary | Job-level: the sequence of programs that ran and each return code. No dataset is named, so there is no file boundary to diff. | medium | `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4` |
| Business stakeholder can name it | "The nightly batch cycle", if SEQJOB is that. Not confirmed. | low | inference |

## Where the risk scores put it

| Unit | Port difficulty | Blast radius | Quadrant | Evidence |
|---|---|---|---|---|
| PGMA | 1 | 2 | low-low | `app/cbl/PGMA.cbl:4` |
| PGMB | 1 | 2 | low-low | `app/cbl/PGMB.cbl:4` |
| PGMC | 1 | 2 | low-low | `app/cbl/PGMC.cbl:4` |
| job:SEQJOB | 2 | 3 | low-high | `app/jcl/SEQJOB.jcl:1` |

The job is `low-high`. The skill says that means the verification is the work and the harness must
be proven first. Here that is right. The port is trivial. Proving the order survived is the wave. No
unit is `high-high`, so nothing needs a facade for difficulty reasons.

## Unassigned

| Item | Reason | Evidence |
|---|---|---|
| `step:SEQJOB.STEP2#2` | Runs IEFBR14, a null program, with no DDs, and shares the name STEP2 with line 3. It moves with SEQJOB or is dropped after the client confirms nothing names it. | `app/jcl/SEQJOB.jcl:5` |

## If the system were ten times larger

Cut by job. A job and the programs its steps run form one unit, because step order binds them. Then
order the jobs by two constraints from `graph.json`: the `temporal` edges a scheduler enforces
between jobs, and the `data_hubs`, where every writer runs before its readers. Any strongly
connected component moves whole. Any `god_modules` entry is strangled behind a facade rather than
ported. Any `high-high` unit goes last. Wave 1 would be the `low-low` job with the fewest crossing
edges, chosen to prove the toolchain and the harness. Inference.
