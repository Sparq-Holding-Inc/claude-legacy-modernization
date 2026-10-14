# 04 Estimate

**Basis.** `--delivery` was not given, so every figure shows both cases: conventional (no AI coding assistance) and AI-assisted (engineers using an AI coding agent, with human review). This plugin carries no calibrated productivity data. Every rate below is a planning assumption, not a benchmark. Replace it with measured velocity after wave 1.

The tree is 12 lines of COBOL and 5 lines of JCL (`app/cbl/PGMA.cbl:4`, `app/jcl/SEQJOB.jcl:5`). The estimate is for what the tree shows. If the real system is larger, the estimate is void. `inference`

## Wave 1

| Term | Conventional | AI-assisted | Does AI shrink it? | Evidence |
|---|---|---|---|---|
| Understanding the code | 0 weeks | 0 weeks | Already done by this run | `app/cbl/PGMA.cbl:4` |
| Port of three stubs | 0.2 to 0.5 weeks | 0.1 to 0.3 weeks | Yes, if a harness exists. Assumes review takes a quarter of the authoring time it replaces. | `app/cbl/PGMB.cbl:4` |
| Boundary work (step order, return codes) | 0.5 to 1 week | 0.4 to 0.8 weeks | Little. Choosing the boundary is the hard part. | `app/jcl/SEQJOB.jcl:2` |
| Equivalence harness | 1 to 2 weeks | 0.7 to 1.5 weeks | Partly. Code is quick, the oracle is not. | inference |
| Cutover, rehearsal, approvals | 1 to 2 weeks | 1 to 2 weeks | No | inference |
| **Total** | **2.7 to 5.5 weeks** | **2.2 to 4.6 weeks** | | inference |

## Assumptions the range is most sensitive to

1. Assumes the duplicate STEP2 (`app/jcl/SEQJOB.jcl:5`) is a copy error in this extract and the real job has four distinctly named steps. If the real job depends on the repeated name, the boundary work roughly doubles.
2. Assumes the real programs are as small as these stubs. If they are not, the port term grows with their size, and this estimate no longer applies.
3. Assumes the client can supply job logs or archived output for the oracle. If they cannot, the harness term roughly doubles, because the oracle must be built by hand.

## Where AI can and cannot help

- Strong: transliterating the stubs once a comparison harness exists.
- Weak: deciding what the repeated step name means, and what "nightly" means for this job. Those are questions for people.
