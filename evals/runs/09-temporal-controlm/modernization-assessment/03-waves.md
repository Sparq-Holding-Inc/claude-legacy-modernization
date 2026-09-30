# 03 Waves

Target state: `refactor`. Must not break: "the nightly batch cycle". Telemetry: none.

## Decision: one wave

This system is one Control-M folder, two JCL jobs and one ordering condition between them. That is one wave. I did not split it, and I did not invent a second wave to look thorough.

Cutting JOBA from JOBB would put a scheduler condition across a wave boundary. Then the two waves would be tied by a token that JOBB deletes on completion (`app/scheduler/nightly.xml:10`). One wave could not be rolled back without the other. That fails the rule that a wave rolls back independently.

## Wave 1: Nightly chain JOBA to JOBB

| Field | Value | Evidence |
|---|---|---|
| Units | `job:JOBA`, `job:JOBB`, `sch:NIGHTLY/JOBA`, `sch:NIGHTLY/JOBB`. The steps move with their jobs. | `app/scheduler/nightly.xml:4`, `app/scheduler/nightly.xml:8` |
| Deploys independently | Yes, if the condition names JOBA-DONE, JOBB-DONE and EXTERNAL-FEED and the date scoping stay as they are. The deploy is a job and scheduler definition change, behind a shadow folder. `inference` | inference |
| Rolls back independently | Yes. Restore the previous definitions and job members. Nothing in the tree writes a dataset. | `app/jcl/JOBA.jcl:2` |
| Testable boundary | The order and count of job starts per ODAT, and the state of the three conditions at each start. | `app/scheduler/nightly.xml:5` |
| Names a stakeholder | The operations owner of the nightly cycle: the cycle still finishes in the same order. | `app/scheduler/nightly.xml:3` |
| Blast radius | medium. Nothing here writes data. The exposure is silent misordering of a cycle that must not break. | inference |
| Confidence | medium | inference |
| Unblocks | Proof of the shadow-run harness on the smallest possible cycle, and a written list of the cycle's condition names, which any later wave in a bigger tree needs. | inference |

Port order inside the wave, program by program (`inference`):

1. `job:JOBA` with `sch:NIGHTLY/JOBA`, because JOBB depends on its condition.
2. `job:JOBB` with `sch:NIGHTLY/JOBB`, and only after the shadow run shows the delete of JOBA-DONE behaving the same.

The units are listed together in `waves.json` because the test boundary spans both.

## Risk quadrant for each unit

All four units sit in low-high. The port is easy and the verification is the work. Per the quadrant rule, they are safe to do early once the equivalence harness is proven, and that harness is the deliverable of this wave.

| Unit | Port difficulty | Blast radius | Quadrant | Evidence |
|---|---|---|---|---|
| `job:JOBA` | 1 | 3 | low-high | `app/jcl/JOBA.jcl:2` |
| `job:JOBB` | 1 | 3 | low-high | `app/jcl/JOBB.jcl:2` |
| `sch:NIGHTLY/JOBA` | 2 | 4 | low-high | `app/scheduler/nightly.xml:5` |
| `sch:NIGHTLY/JOBB` | 2 | 4 | low-high | `app/scheduler/nightly.xml:10` |

## What I would cut if this were ten times larger

- Build one component per chain of Control-M conditions, by condition name. A chain is a set of jobs joined by a condition one adds and another waits for. A chain never splits across waves.
- Two jobs that both wait on the same condition, or one that deletes what another reads, belong to the same wave. The delete at `app/scheduler/nightly.xml:10` is the pattern to search for.
- Put leaf chains first: chains whose input is an external condition and whose output nobody waits for. This chain is that shape (`app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:11`). It proves the toolchain and the harness at the lowest blast radius.
- Put chains that feed month-end close, regulatory reports or partner extracts last, and only after the harness has run clean through a month-end.
- Once real programs and datasets exist, cut the programs on the data hubs and the contract edges instead, and keep every writer with the readers that share its record layout copybook.
- Business value leads in wave three, not wave one.

All of this is `inference`.
