# 04 Estimate

Basis: the delivery mode was not given (`--delivery` missing), so both cases are shown. This plugin carries no calibrated productivity data. Every rate below is a planning assumption, not a benchmark. Replace it with measured velocity.

The supplied code is 14 lines of COBOL and JCL in three live units (`app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMLIVE.cbl:4`, `app/jcl/MAINJOB.jcl:2`). The estimate is for this tree only. If the real nightly cycle is larger, it is void.

| Wave 1 term | Conventional | AI-assisted | Does AI shrink it? | Evidence |
|---|---|---|---|---|
| Understanding | 0 | 0 | Done by this assessment | inference |
| Port (3 units) | 0.5 to 1 week | 0.5 week | Barely. The code is trivial. | inference |
| Boundary work | 0.5 week | 0.5 week | Deciding the boundary is human work | inference |
| Equivalence harness | 1 to 2 weeks | 1 week | Harness code is quick. Getting job output is not. | inference |
| Cutover and rehearsal | 1 week | 1 week | No. Windows and approvals do not shrink. | inference |
| **Total** | **3 to 4.5 weeks** | **2.5 to 3 weeks** | | inference |

## Sensitive assumptions

1. Assumes the supplied programs are the whole cycle. If the real programs hold logic, the port term grows in proportion to the lines and the AI-assisted case depends on the review rate (assumed: review takes a quarter of the authoring time it replaces).
2. Assumes archived job output exists for the oracle. If it does not, the harness term roughly doubles.
3. Assumes one cutover window is available. If the cycle must run in parallel for a full month-end, add at least one month elapsed.

## Where the agent helps

Strong at transliterating `PGMMAIN` and `PGMLIVE` once a harness exists. Weak at intent. No business rule is visible here to infer.
