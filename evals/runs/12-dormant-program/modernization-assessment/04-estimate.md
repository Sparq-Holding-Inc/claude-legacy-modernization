# 04 Estimate

## Method

An estimate per wave, built from the things that move it, in order of weight: coupling edges that cross the wave boundary, a behavioral oracle, god modules, logic in the database, and whether the team can read COBOL. It is not built from line count. The figures below are judgment, not measurement, and the range is deliberately wide.

| Driver | Value for wave 1 | Evidence |
|---|---|---|
| Coupling edges crossing the wave boundary | 0 inside the tree. The whole system is in the wave. Cross-job edges are unknown. | inference |
| Behavioral oracle | None in the tree. No datasets. It would have to come from job logs and return codes | `app/jcl/MAINJOB.jcl:2` |
| God modules | None | `app/cbl/PGMMAIN.cbl:6` |
| Logic in the database | None visible. No SQL in the tree | inference |
| Size | 16 lines across 4 units | `app/cbl/PGMMAIN.cbl:6` |

## Wave 1

| Item | Range | Confidence | Evidence |
|---|---|---|---|
| Toolchain and pipeline setup for the target | 2 to 4 person-days | low | inference |
| Port of PGMMAIN, OLDPGM, NEWPGM and MAINJOB | 0.5 to 1 person-day | medium | `app/cbl/PGMMAIN.cbl:4` |
| Oracle capture and the diff harness | 1 to 3 person-days | low | inference |
| Instrumenting OLDPGM to settle its status | 0.5 to 1 person-day | medium | `app/cbl/OLDPGM.cbl:4` |
| Parallel run and cutover | 1 to 3 person-days | low | inference |
| **Total** | **5 to 12 person-days** | low | inference |

The code is the small part. The time goes on getting a build environment, getting the logs, and agreeing what "the same" means for a job with no output files.

## The assumptions the range depends on

1. Assumes the deployed load modules for OLDPGM and NEWPGM are built from the four line sources in the tree (`app/cbl/OLDPGM.cbl:4`, `app/cbl/NEWPGM.cbl:4`). If either carries logic that is not in this tree, wave 1 grows by roughly an order of magnitude, because the port and the oracle would have to come from the load module and its job output.
2. Assumes MAINJOB is the whole nightly batch cycle (inference, no scheduler export). If the scheduler shows more jobs chained to it, each is a temporal edge across the wave boundary and the plan needs another wave and a new estimate.
3. Assumes 12 months of job logs and return codes for MAINJOB can be obtained in the first week. If they cannot, the harness falls back to characterization tests, which are provisional, and the exit bar in `06-test-strategy.md` cannot be met.

## Where Claude Code helps and where it does not

- Strong: transliterating four small units once a harness exists. There is no arithmetic, no packed decimal and no file handling in them (`app/cbl/PGMMAIN.cbl:4`).
- Weak: saying why PGMMAIN calls both OLDPGM and NEWPGM. Nothing in the source states the intent. The names suggest an old and a new implementation of the same job, but that is inference and someone who knows the system has to confirm it.
