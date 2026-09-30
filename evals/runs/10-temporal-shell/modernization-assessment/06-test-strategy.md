# 06 Test strategy

Skill: `behavioral-equivalence`. The bar is not "it runs". The bar is that the new nightly cycle runs
the same jobs in the same order with the same return codes as the old one, and that any difference
was decided and written down.

## The tree holds no datasets

The graph has no dataset node, so there are no archived generations, no golden master files and no
record layouts to compare (analysis, `node_counts`). The oracle has to come from job output, logs and
reports. The client must supply them.

## What to ask the client for

1. Scheduler or job history for the nightly cycle: start time, end time and return code of JOBA and
   JOBB, for at least a month and including a month end. Inference: this is the executable definition
   of the cycle.
2. The definition of `submit` used at `scripts/nightly.sh:4`. Does it wait for the job to end? What does it
   return on a job abend?
3. SYSOUT and job logs for a sample of runs, and any report or extract the cycle produces.
4. Whether JOBA and JOBB ever ran overlapped in the history. If they did, only submit order holds.
5. Any month-end, quarter-end or holiday variant of the nightly chain. The tree has one wrapper.
6. Confirmation that the production JCL for JOBA, JOBB and JOBC matches the members in the tree
   (`jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2`, `jcl/JOBC.jcl:2`).

## Oracle for wave 1

| Rank | Oracle | Use for wave 1 | Evidence |
|---|---|---|---|
| 1 | Parallel run: old wrapper and new chain fed the same nights, compare job order and return codes | Preferred. The jobs do nothing visible, so a parallel run is cheap and safe. Ask whether it is possible before settling for less. | inference |
| 2 | Captured job history replay | Fallback. Replay the recorded start and end order against the new scheduler's simulation. | inference |
| 3 | Golden master from archived outputs | Only if the client has archived reports or SYSOUT from the cycle. None in the tree. | analysis (no dataset nodes) |
| 4 | Characterization test from source | Weakest. It would assert the order in `scripts/nightly.sh:4` and `scripts/nightly.sh:5`, which is what the code says and not necessarily what runs. Label it provisional. | `scripts/nightly.sh:4` |

## Assertions at the wave boundary

| Assertion | Meaning | Evidence |
|---|---|---|
| JOBB is submitted after JOBA | The weak form. It is what the wrapper states. | `scripts/nightly.sh:4`, `scripts/nightly.sh:5` |
| JOBB starts after JOBA ends with return code 0 | The strong form. Assert it only if the history shows the legacy chain does it. | inference |
| A failed JOBA submit stops the chain | Failure injection. `set -e` implies JOBB is not submitted. | `scripts/nightly.sh:3` |
| A JOBA abend after a good submit | Observe what the legacy chain does with JOBB and copy it, or record a deviation. | inference |
| JOBC is not submitted | The new chain must not run JOBC unless the client says it is live. | `scripts/nightly.sh:6` |

## Normalization spec

Keep it short. Each line is a claim that a difference does not matter, and a human signs it off.

| Ignore | Why | Evidence |
|---|---|---|
| JES job numbers and run IDs | They change every run. | inference |
| Absolute timestamps | Compare order and elapsed spans, not clock times. | inference |
| Trailing whitespace in SYSOUT | Padding only. | inference |

Not ignored: order, return codes and the set of jobs run. Packed decimal, collating sequence and
`REDEFINES` do not apply, because the tree has no data or COBOL. Add them when real data appears.

## Traps for this tree

- **Job order.** The temporal edge JOBA to JOBB is the one order the harness must keep
  (`scripts/nightly.sh:4`, `scripts/nightly.sh:5`). It is medium confidence, so the harness is what
  raises it to high or shows it was never real.
- **Boundary dates.** A nightly chain that crosses a month end, a quarter end, a fiscal year end, a
  leap day or a daylight saving change can order differently. Cover each in the history sample.
  Inference.
- **Empty and enormous runs.** With no datasets, this means a night with no work and a night when JOBA
  is late. Inference.
- **Fiscal close paths.** If a close variant of the chain exists outside this tree, it is not covered
  here. This is the failure that shows up six months after cutover. Ask for it.

## Deviation register

Nothing differs without a row here. One candidate row is seeded.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-1 (candidate) | JOBC exists as JCL but the wrapper does not submit it | JOBC is not deployed | Wrapper comment calls it retired. Unconfirmed. | pending, client owner | none known, none can be seen | `scripts/nightly.sh:2`, `scripts/nightly.sh:6` |

## Exit bar for wave 1

- The order and return code diff against the oracle is clean, modulo the normalization spec and the register.
- Each failure and boundary case above passes.
- The harness is under version control and runs in CI.
- The register is signed by someone with authority to sign it.

Not when the new chain starts. After cutover the harness stays as the regression suite for the cycle.
