# 04 Estimate

One wave, so one estimate. The ranges are inference. There is no size, velocity or team data in the
tree to compute them from.

## Method

I weighed the factors the skill lists, in its order of weight, against what the graph shows.

| Factor | This wave | Evidence |
|---|---|---|
| Coupling edges crossing the wave boundary | 0 call, 0 data, 0 contract. 1 temporal edge, inside the wave. | analysis (`edge_counts`) |
| Behavioral oracle | None in the tree. It must come from job logs and scheduler history. | inference |
| God modules in the wave | none | analysis (`god_modules`) |
| Business logic in the database | none visible: no DB2 or dataset node | analysis (`node_counts`) |
| Someone who can read the source language | unknown. The source is a 6-line shell script and three 2-line JCL members. | `scripts/nightly.sh:3` |

## Wave 1 range

| Wave | Range | Basis | Evidence |
|---|---|---|---|
| 1 | 3 to 10 person-days, including the equivalence harness | The port is hours. The rest is finding out what `submit` does, collecting job history and building the order check. | inference |

## The assumptions the range is most sensitive to

1. **The jobs in production are the jobs in the tree.** The range assumes each job is a no-op step
   (`jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2`). If production JCL runs application programs, this estimate does
   not apply. It needs a fresh scan, and the cost moves by an order of magnitude.
2. **`submit` returns when the job is submitted, and only the submit order matters.** If JOBB must wait
   for JOBA to end with return code 0, add about 1 to 2 person-days to map the condition into the
   target scheduler, and to test the failure paths. The wrapper does not settle it
   (`scripts/nightly.sh:4`, `scripts/nightly.sh:5`).
3. **The client can supply at least a month of job history.** If not, add about 2 to 3 person-days to
   capture run logs before the harness has anything to compare.

## Where Claude Code helps and where it does not

Claude Code is strong at the mechanical part: re-expressing the two `submit` lines as a dependency
chain in the target scheduler, with a test that asserts the order. It cannot tell what `submit` does,
what JOBA and JOBB are for, or whether JOBC is retired. Those need the client's engineers. Inference.

## Target state

The target is `refactor`. This tree has no application code to restructure, so the refactor label
applies to the wrapper only. Whether `rehost` would describe the real work better is the client's call.
Inference.
