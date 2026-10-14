# 04 Estimate

**Basis: no `--delivery` flag was given, so both cases are shown: conventional (no AI coding assistance) and AI-assisted (engineers with an AI coding agent, human review).** This plugin carries no calibrated productivity data. Every rate below is a planning assumption, not a benchmark. Measured team velocity replaces it.

## Per-wave estimate

There are no waves (`modernization-assessment/waves.json:2`), so there is no per-wave figure. A number for the nightly batch cycle would be invented: the JCL, scheduler and datasets that define it are not in the tree.

## What can be sized

The only code is two 8-line programs and a 3-line copybook (`modernization-assessment/graph.json:41`, `modernization-assessment/graph.json:49`, `modernization-assessment/graph.json:59`).

| Term | Conventional | AI-assisted | Does AI shrink it? | Evidence |
|---|---|---|---|---|
| Port PROGA and PROGB, refactor target | under 1 engineer-week | under 1 engineer-week | Little. The code is trivial. | `app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7` |
| Layout port of `SHARED01` to a decimal type | 1 to 2 days | 1 to 2 days | No. The choice of decimal type and the zero tolerance on money is a decision. | `app/cpy/SHARED01.cpy:3` |
| Equivalence harness, oracle, approvals, cutover | unknown | unknown | No. | inference |

Confidence: low. These cover two toy programs. They say nothing about the real system.

## Assumptions the range is most sensitive to

1. Assumes this tree is the whole system. It is almost certainly not: no JCL exists for "the nightly batch cycle". If the real cycle has dozens of jobs, any figure here is meaningless.
2. Assumes `SHARED01` is used only by these two programs. If other programs outside this tree copy it, the layout change spreads to them (`app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5`).
3. Assumes review takes a quarter of the authoring time it replaces, for an AI-assisted port. Falsifiable once wave 1 is measured.

## Where Claude Code helps and where it does not

- Strong: transliterating these two programs once a comparison harness exists.
- Weak: choosing the target decimal type for the packed field, and knowing what the nightly cycle does with `SH-BALANCE` (`app/cpy/SHARED01.cpy:3`). Neither is in the source.
