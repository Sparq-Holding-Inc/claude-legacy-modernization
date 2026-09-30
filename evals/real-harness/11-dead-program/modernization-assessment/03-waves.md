# 03. Waves

Target state: **refactor** (`modernization-assessment/waves.json:2`). Same behaviour, restructured
code, in the same or a new language.

The machine-cut seed is in `03a-wave-seed.md` and `03a-waves-draft.json`. The final plan is
`waves.json`. **One wave. No deviations.**

## The plan

| Wave | Family | Name | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | batch-readonly | The MAINJOB chain | `PGMLIVE`, `PGMMAIN`, `job:MAINJOB` | low | medium | `app/jcl/MAINJOB.jcl:1`, `app/cbl/PGMMAIN.cbl:4` |
| — | — | not placed | `PGMDEAD` | — | — | `app/cbl/PGMDEAD.cbl:2` |

`cpy:UNUSED` is a copybook and `step:MAINJOB.S1` is a step, so neither is a unit; they move with
their owner, or in the copybook's case with nothing, because nothing includes it
(`app/cpy/UNUSED.cpy:1`).

## Wave 1 — The MAINJOB chain

**Units:** `PGMLIVE`, `PGMMAIN`, `job:MAINJOB`

**Why this is a sound wave.** Test it against the four conditions.

| Condition | Holds? | Why | Evidence | Confidence |
|---|---|---|---|---|
| Deployable independently | yes | It is the only deployable thing in the tree. One job, one step, two programs, no shared dataset to coordinate with anyone. | `app/jcl/MAINJOB.jcl:2` | high |
| Rollback independently | yes | The job writes nothing (`analysis.data_hubs` is empty; there are no `ds:` nodes), so rollback is re-pointing the step's PGM back at the old load module. There is no data change to unwind. | `analysis` | high |
| Testable boundary | weak but real | The boundary is the job's return code and its SYSOUT. Nothing richer exists, because no program has a FILE SECTION (`app/cbl/PGMMAIN.cbl:3` goes straight to PROCEDURE DIVISION). See `06-test-strategy.md`. | `app/cbl/PGMMAIN.cbl:3`, `app/cbl/PGMLIVE.cbl:3` | high |
| Names something a stakeholder recognises | **no** | This is the honest answer. `PGMLIVE`'s entire procedure division is `GOBACK` (`app/cbl/PGMLIVE.cbl:4`) and `PGMMAIN`'s is a CALL and a GOBACK (`app/cbl/PGMMAIN.cbl:4-5`). No business outcome is attached to porting them. | `app/cbl/PGMLIVE.cbl:4`, `app/cbl/PGMMAIN.cbl:4` | high |

Three of four hold. The fourth does not, and that is the point of this section: **wave 1 delivers
no business value and unblocks nothing inside this tree.** By the skill's own test, a wave that
unblocks nothing is a chore. This one is a chore.

It is still worth running, for one reason and only one: it is a zero-blast-radius rehearsal of the
build, deploy, feature-flag and rollback path for COBOL batch on the target runtime. Do it in the
week the tooling is being stood up, and count it as tooling work, not migration work.

**Why confidence is medium and not high.** There are no computed calls anywhere in the tree
(`analysis.unresolved_dynamic` is empty), so the usual reason to withhold confidence does not
apply — the reachability result is solid. Confidence is held at medium for a different reason:
the must-not-break item the client named, "the nightly batch cycle", cannot be shown to
correspond to `job:MAINJOB`. No scheduler artifact was parsed
(`analysis.warnings`), so nothing in the tree says this job runs nightly, and a single-step job
calling two no-op programs is not a batch *cycle*. The plan is high-confidence about the code on
disk and low-confidence about whether that code is the thing being asked about.

**Risk scoring.** `risks.json` puts every unit at port difficulty 1. `job:MAINJOB` scores blast
radius 3 (`low-high`) because it is the entry point for the named must-not-break item; the three
programs score `low-low`. No unit lands in the high-high quadrant, so deviation reason 4 does not
fire.

## Not placed: `PGMDEAD`

`PGMDEAD` is not in any wave because no entry point reaches it (`analysis.dead_code_candidates.unreachable`).
It is not a sequencing problem; it is a dead-code decision, and it is handled in `05-dead-code.md`.

Do not port it. But do resolve it **before** wave 1 touches `PGMLIVE`, because `PGMDEAD` contains
a second `CALL 'PGMLIVE'` (`app/cbl/PGMDEAD.cbl:4`). A developer grepping for `PGMLIVE`'s callers
during the port will find two call sites and one of them is a ghost. That is a half-hour of
confusion at best and a needlessly ported program at worst.

## Deviations

**None.** The seed's single wave survives every test that could have moved a unit:

| Deviation reason | Fired? | Why not | Evidence |
|---|---|---|---|
| 1. Must-not-break item, SCC or facade forces a move | no | `analysis.sccs` is empty; there is one wave, so there is nowhere to move to. | `analysis` |
| 2. Wave over ~25 units | no | Three units. | `modernization-assessment/waves.json:9` |
| 3. Something the extractor could not see | no | `unresolved_dynamic`, `embedded_jcl`, `runtime_named` and `unparsed` are all empty. | `analysis` |
| 4. `risks.json` high-high placed early | no | No unit scores high on both axes. | `modernization-assessment/risks.json:1` |

A plan with no deviations is the correct answer for a tree with four edges.

## What this plan is not

It is not a migration plan for a nightly batch cycle. It is a migration plan for five files that
appear to be a fragment, a test fixture, or the first commit of a repository whose real contents
have not been supplied. If the client expected more waves, the gap is in the inputs, not in the
sequencing. The questions to put to their engineers are in `00-summary.md`.
