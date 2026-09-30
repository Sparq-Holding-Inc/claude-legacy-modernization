# 03 Waves

Target state: refactor (given as a flag). Machine-readable plan: `waves.json`. Risk scores: `risks.json`, written by the migration-risk-assessor step, done inline.

## The plan is one wave

The live system is one wrapper and two jobs, with no program, dataset or copybook coupling to cut along (`02-coupling.md`). The one constraint the tree enforces is the JOBA-before-JOBB order (`scripts/nightly.sh:4`, `scripts/nightly.sh:5`). Putting JOBA and JOBB in different waves would split that constraint across two deployments, so one wave is the honest answer. Inventing a second wave would be padding.

| Wave | Units | Unblocks | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1. Nightly chain | `sch:scripts/nightly.sh`, `job:JOBA`, `job:JOBB` | The order and return-code harness for the nightly cycle. The decision to delete JOBC. | medium | medium | `scripts/nightly.sh:4`, `scripts/nightly.sh:5`, `jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2` |

Unassigned: `job:JOBC`. It is retired (`scripts/nightly.sh:2`) and its submit is commented out (`scripts/nightly.sh:6`). It is a deletion candidate, not a port unit.

## The four tests for a valid wave

- **Independent deploy behind a flag or facade.** The wrapper is the facade. Run the refactored chain beside the old one on the same trigger, and switch the trigger. Inference, because the trigger is not in the tree.
- **Independent rollback.** Point the trigger back at `scripts/nightly.sh`. The jobs write no data in the tree (`jcl/JOBA.jcl:2`), so no data has to be restored. Inference.
- **Testable boundary.** Job return codes, submit order, and the JES output of each job. See `06-test-strategy.md`.
- **Something a stakeholder can name.** "The nightly batch cycle", which is what the client said must not break.

## Where the risk scores put this wave

All three wave units are `low-high` in `risks.json`: the port is trivial, and the blast radius is high because the wave is the named must-not-break path. The assessor guidance for `low-high` is safe to do relatively early, once the equivalence harness is proven. With one wave there is nothing to order it against. What it teaches is the harness, not the port. No unit is `high-high`, so no strangler facade is needed.

## Order inside the wave

1. Build the harness first: capture return codes, submit order and JES output for the current chain (`06-test-strategy.md`).
2. Port `job:JOBA` and `job:JOBB` as they stand. Each is one IEFBR14 step (`jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2`), so this is mechanical.
3. Replace the wrapper ordering with a dependency the scheduler enforces, only after the client says what `submit` does (see Open Questions in `00-summary.md`). If `submit` is asynchronous, the port must add a completion condition. The wrapper never had one. That is a deviation to record, not a silent fix.
4. Run old and new in parallel on the same trigger. Delete JOBC only after the client confirms nothing else submits it.

## If the system were ten times larger

I would cut along the same lines the extractor already computes, not by team or by business value.

- Wave 1: leaf jobs and programs with no writers of shared datasets and no scheduler successors (`low-low`), to prove the toolchain.
- Wave 2: `high-low` units, to learn the hard patterns (packed decimal, `REDEFINES`) where they cannot hurt.
- Then `low-high` units, only once the harness is proven, in scheduler order so that every writer moves with or before its readers.
- Last, `high-high` units and god modules, strangled behind a facade. Strongly connected components move as one unit. Wave boundaries would fall on articulation points and on the temporal edges between scheduler jobs, because a boundary that cuts a temporal edge needs both sides to keep the order.

None of that applies to this tree, because it has none of those structures.
