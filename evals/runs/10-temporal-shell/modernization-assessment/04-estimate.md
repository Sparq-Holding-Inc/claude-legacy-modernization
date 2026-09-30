# 04 Estimate

Method: effort per wave, driven by the factors that move it (coupling edges crossing the wave boundary, oracle availability, god modules, logic in the database, team skills), not by lines of code. The tree has 6 lines of shell and 6 lines of JCL, so lines of code would say nearly nothing.

## Wave 1. Nightly chain

| Item | Estimate | Basis | Evidence |
|---|---|---|---|
| Restate the chain in the target scheduler with an enforced JOBA-then-JOBB dependency | 1 to 2 person-days | Three units, one temporal edge, no data edges | `scripts/nightly.sh:4`, `scripts/nightly.sh:5` |
| Build the order and return-code harness, with normalization spec | 3 to 6 person-days | The oracle has to come from job logs, since the tree has no datasets. Most of the work is collecting and normalizing them | `jcl/JOBA.jcl:2` |
| Parallel run and sign-off | 5 to 10 elapsed business days, 1 to 2 person-days of effort | The cycle is nightly, and the run has to cover a month-end at least | inference |
| Delete JOBC after confirmation | under 1 person-day | One job, retired | `scripts/nightly.sh:6` |

Total for wave 1: roughly 5 to 11 person-days of effort. The range is inference. There are no prior velocity numbers for this team.

## What the range is most sensitive to

1. **Assumes `submit` waits for the job and returns its return code.** If it only queues the job, the harness has to track completion and the port has to add a completion condition, and wave 1 roughly doubles. The tree does not define `submit` (`scripts/nightly.sh:4`).
2. **Assumes IEFBR14 is the whole workload.** All three steps run it (`jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2`, `jcl/JOBC.jcl:2`). If the real jobs run other programs that are outside this tree, this estimate covers only the wrapper and JCL, and the programs are unestimated. That is the largest unknown in this document.
3. **Assumes nothing else submits JOBC or reads the output of JOBA and JOBB.** If a partner or downstream job depends on either, the boundary has coupling this tree cannot show, and harness effort grows by the number of consumers.

## Where Claude Code can do the work, and where it cannot

- **Strong.** Mechanical restatement of the two JCL jobs and the wrapper in the target scheduler's format, and writing the harness code that diffs job logs after normalization. Both are transliteration against a clear check.
- **Weak.** Deciding what `submit` really does, what triggers the wrapper at night, why JOBC was retired, and whether anything downstream relies on the jobs running in that order. Those live in people's heads and in systems outside the tree. It cannot infer them from six lines of shell.

## Estimate confidence

Low. The tree is too thin to estimate a real nightly cycle. Treat the numbers as the cost of moving this wrapper and these jobs, not the cost of modernizing the batch cycle the client cares about.
