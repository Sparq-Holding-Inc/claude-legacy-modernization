# Estimate

**Basis:** `--delivery` was not given, so both cases are shown: conventional (no AI coding assistance) and
AI-assisted (engineers using an AI coding agent, with human review). This plugin carries no calibrated
productivity data. Every rate below is a planning assumption, not a benchmark. Measured velocity from the first
wave replaces it.

Size: 16 lines of COBOL and JCL in four units (app/cbl/PGMMAIN.cbl:1, app/jcl/MAINJOB.jcl:1). The port is
trivial. The estimate is dominated by the terms that do not shrink with tooling.

## Wave 1: MAINJOB batch chain

| Term | Conventional | AI-assisted | Does AI shrink it? | Evidence |
|---|---|---|---|---|
| Port (3 programs, 14 lines, no logic) | 0.5 to 1 engineer-week | 0.5 engineer-week | Barely. The work is setup and tooling for the target. | app/cbl/PGMMAIN.cbl:4 |
| Boundary work (job entry, flag, facade) | 0.5 to 1 engineer-week | 0.5 to 1 engineer-week | Partly. Choosing the boundary is the work. | inference |
| Equivalence harness | 1 to 2 engineer-weeks | 1 to 1.5 engineer-weeks | Partly. Code is quick. The oracle and normalization sign-off are not. | inference |
| Cutover and rehearsals | 1 to 2 engineer-weeks | 1 to 2 engineer-weeks | No. Windows, approvals, client availability. | inference |
| **Total** | **3 to 6 engineer-weeks** | **3 to 5 engineer-weeks** | | inference |

Confidence: low. The range comes from what the tree does not show.

## Sensitive assumptions

1. Assumes the tree is the whole nightly batch cycle. If the cycle is many more jobs (the scheduler export is
   missing), this estimate covers only a fragment and the real figure is unknown.
2. Assumes an oracle exists (archived job output or reports). With none, the harness term roughly doubles.
3. Assumes review takes about a quarter of the authoring time it replaces. For 14 lines this is noise.

## Where an AI agent helps and where it does not

- Strong: transliterating the three programs when a comparison harness exists.
- Weak: inferring intent. The programs hold no intent to infer (app/cbl/OLDPGM.cbl:4). Whether `OLDPGM` is a
  stub or a placeholder for real logic is a question for the client's engineers.
