# 05 Dead code

Telemetry: none. Every claim here is provisional. Candidates are in `05a-dead-code-candidates.md`.

The git dormancy rule ran (git dates are on, five-year window, as of 2026-10-14) and found nothing: the oldest file was last changed in 2022 (`app/cbl/COACTVWC.cbl:1`). An empty dormant list therefore means "nothing is older than five years in git", not "everything is used". Git dates on a sample repository say little about production use.

| Unit | Bucket | Reason | Confidence | Evidence |
|---|---|---|---|---|
| cpy:UNUSED1Y | Unreachable | No program includes it | medium | `app/cpy/UNUSED1Y.cpy:1` |
| CBTRN01C | Unknown | Nothing in the tree names it; no computed call can reach it; an outside scheduler could | low | `app/cbl/CBTRN01C.cbl:1` |
| proc:TRANREPT | Unknown | Named only in JCL text inside `CORPT00C`; on a must-not-break path. Keep | high | `app/cbl/CORPT00C.cbl:94` |

## What to ask

- 35 jobs are named by no parsed scheduler (`analysis` field `unscheduled_jobs`), and the CA-7 listing cannot be parsed. Most of them are compile, setup and test jobs. Ask which still run. One of them matters: `job:TRANREPT` is unscheduled, yet the report is a must-not-break item (`app/jcl/TRANREPT.jcl:23`). `job:POSTTRAN` is also in no Control-M folder and is run only by shell wrappers (`scripts/run_posting.sh:26`).
- `CBTRN01C` has a plausible role (it reads the daily transaction file, as `CBTRN02C` does) but is named nowhere. Ask whether it is a test harness (`app/cbl/CBTRN01C.cbl:1`).
- The risk assessor marked 22 units `do_not_port` (`modernization-assessment/risks.json:1`). Treat that as a proposal, not a decision, until the client confirms with job logs.
