# 03 Waves

Target state: refactor. `waves.json` holds the same plan in machine form.

## The plan is one wave

This system is two jobs, two programs and one shared dataset. The skill says a system that small is
one wave, and I agree. Cutting it in two would fail the wave test, for a reason you can point at.

| Wave test | Result if I cut writer and reader apart | Evidence |
|---|---|---|
| Deploys independently, behind a flag or facade | No. The writer's output is the reader's input and both take their layout from copybooks that are different files. Moving one side alone changes what the other side reads | `app/cpy/LAYOUTX.cpy:2`, `app/cpy/LAYOUTY.cpy:2` |
| Rolls back independently | No. Rolling back the writer alone leaves a reader tested against a file the old writer never made | `app/jcl/WRITEJOB.jcl:3`, `app/jcl/READJOB.jcl:3` |
| Testable boundary | The boundary is the dataset. It is testable, but a test of one half needs the other half's real output as its input, so the halves are checked together | `app/cbl/PGMW.cbl:14`, `app/cbl/PGMR.cbl:14` |
| Something a business stakeholder can name | Only the pair, as "the master file hand-off". Neither half delivers it alone | inference: no business owner is named anywhere in the tree |

### Wave 1: Writer, reader and the shared master file

| Field | Value | Evidence |
|---|---|---|
| Units | `job:WRITEJOB`, `PGMW`, `job:READJOB`, `PGMR` | `app/jcl/WRITEJOB.jcl:2`, `app/jcl/READJOB.jcl:2` |
| Moves with them | `step:WRITEJOB.S1`, `step:READJOB.S1`, `cpy:LAYOUTX`, `cpy:LAYOUTY`, `ds:SPARQ.TEST.MASTER` | `app/cbl/PGMW.cbl:11`, `app/cbl/PGMR.cbl:11` |
| Blast radius | medium | inference: the pair is small, but the contract is medium confidence and a break is silent |
| Confidence | medium | inference: the tree holds no scheduler and no telemetry |
| Unblocks | One shared record layout that neither program owns, and a comparison harness for the master file that any later job touching it can reuse | `app/cpy/LAYOUTY.cpy:1` |

**Why this wave leads.** There is only one. It proves the toolchain, the harness and the team's port
velocity on two programs that hold no business logic, which is the right place to learn them.

**Inside the wave, in this order:**

1. Put the layout in one copybook and have both programs include it. Confirm the bytes are unchanged
   with the harness. This is the refactor step that removes the drift risk from
   `02-coupling.md`. It changes nothing a job can see.
2. Build the harness before the port (see `06-test-strategy.md`). Feed it the legacy output first.
3. Port the writer, then the reader. Run each against the other's legacy counterpart, then run the
   new pair together.
4. Cut over the two jobs together, with the scheduler order stated in the new schedule.

**Risk quadrants from `risks.json`.** Three units are low-high: `PGMW`, `PGMR` and `job:WRITEJOB`. The
port is easy. The verification is the work. `job:READJOB` is low-low. No unit is high-high. The
plan does not put a high-high unit in the first half, because there is none.

| Unit | Port difficulty | Blast radius | Quadrant | Evidence |
|---|---|---|---|---|
| `PGMW` | 2 | 3 | low-high | `app/cbl/PGMW.cbl:14` |
| `PGMR` | 1 | 3 | low-high | `app/cbl/PGMR.cbl:14` |
| `job:WRITEJOB` | 2 | 3 | low-high | `app/jcl/WRITEJOB.jcl:3` |
| `job:READJOB` | 1 | 2 | low-low | `app/jcl/READJOB.jcl:3` |

## What I would cut if the system were ten times larger

Cut at the dataset, because it is the articulation point in `graph.json`
(`app/jcl/WRITEJOB.jcl:3`, `app/jcl/READJOB.jcl:3`).

1. Wave 1: shared copybook and the harness, plus every low-low reader of the master file. Readers are
   the safer side, since they change no shared state.
2. Wave 2: the writer, once the harness has been proven on the readers. A writer is the side that can
   corrupt a file every reader trusts.
3. Any program in a call cycle would stay with its cycle. There are none here.

The rule that order comes from is in the skill: earliest waves maximize learning per unit of blast
radius, not business value. This is inference about a hypothetical system, not a finding.

## Unassigned

Nothing. Every node in `graph.json` is either a unit in the wave or moves with one.
