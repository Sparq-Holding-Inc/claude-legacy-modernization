# 03 Waves

Target state: **refactor** (given as a flag). Risk scores come from `risks.json`, written first and used to order the work.

## The plan is one wave

The tree is two single step jobs, two programs, one shared copybook and one dataset. There is no second cluster to separate, no cycle, no god module and no computed call. I am not inventing a second wave. The only seam in the system is the dataset that PGMW writes and PGMR reads (`app/jcl/WRITEJOB.jcl:3`, `app/jcl/READJOB.jcl:3`), and cutting there would put the byte level contract on the wave boundary with no benefit at this size.

| Wave | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|
| 1. Master file writer and reader pair | `PGMR`, `PGMW`, `job:READJOB`, `job:WRITEJOB` | medium | medium | `app/cbl/PGMW.cbl:11`, `app/cbl/PGMR.cbl:11`, `app/jcl/WRITEJOB.jcl:3`, `app/jcl/READJOB.jcl:3` |

The copybook `cpy:LAYOUTX` and the dataset `ds:SPARQ.TEST.MASTER` move with their owners. They are not listed as units.

## Does wave 1 meet the four tests

| Test | Answer | Confidence | Evidence |
|---|---|---|---|
| Deployed independently, behind a flag or facade | Yes. Run the new writer beside the old one against a separate dataset name, and switch the job that names the dataset. | medium | `app/jcl/WRITEJOB.jcl:3` |
| Rolled back independently | Yes, if the new writer's output is byte identical. The old reader can then still read it. | medium | inference |
| A testable boundary | Yes. The dataset is the boundary, and its bytes can be compared. It is also the articulation point in the graph. | high | `app/cbl/PGMW.cbl:13`, `app/cbl/PGMR.cbl:13` |
| Delivers something a stakeholder can name | Unproven. Nothing in the tree says what business function PGMR, PGMW or the dataset serve. The names are generic and the dataset name contains TEST. | low | inference |

The fourth test is a gap in what I was given, not a pass. It is the first open question for the client.

## Order inside the wave

The scores order the work (`risks.json`).

1. `job:READJOB` and `PGMR` (low-low). This proves the toolchain on a consumer that writes nothing. Its test input is a copy of a legacy-written file.
2. `job:WRITEJOB` and `PGMW` (low-high). The port is easy. Verification is the work: the new output must match the legacy file byte for byte, including the packed amount, padding and record length. Do this only after the harness has proven itself on step 1.

## What I would cut if it were ten times larger

- Cut at datasets that have one writer and few readers. Each dataset boundary is a wave boundary and a test boundary.
- Move consumer-only, loud-failure jobs first (low-low). Move producers of shared datasets after the harness is proven (low-high). Move anything high on both axes last, behind a facade.
- Never split a writer from its readers across waves unless the new side reproduces the legacy byte layout exactly. That is the same constraint that applies here.
- Take the order between jobs from the scheduler export, not from guesswork. It is missing from this tree.

## What each wave unblocks

Wave 1 delivers a byte level definition of the SPARQ.TEST.MASTER record and a working equivalence harness. Those are what later jobs of the nightly cycle, outside this tree, would reuse (inference).
