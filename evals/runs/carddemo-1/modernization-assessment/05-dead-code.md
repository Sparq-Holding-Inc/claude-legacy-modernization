# 05 Dead code

Telemetry: none. Every claim here is provisional. The candidate list is in `05a-dead-code-candidates.md`.

The dormancy rule found nothing. The extractor measured dormancy as of 2026-10-14 with a 5-year window and the dormant list is empty. That reading comes from git dates, which on a repository assembled from one upload mostly reflect the upload, so an empty list means not measured, not nothing is old.

| Unit | Bucket | Confidence | Reason | Evidence |
|---|---|---|---|---|
| cpy:UNUSED1Y | Unreachable | medium | No program includes it | `app/cpy/UNUSED1Y.cpy:1` |
| CBTRN01C | Unknown | low | No job runs it. No computed call reaches it, but an outside COMMAREA could | `app/cbl/CBTRN01C.cbl:23` |
| proc:TRANREPT | Unknown | high | Reached only by JCL text inside CORPT00C. It is live | `app/cbl/CORPT00C.cbl:94` |

Retirement candidates from the risk pass, not deletions: the sample compile jobs and procs in wave 4, `job:INTRDRJ1` and `job:INTRDRJ2` (`app/jcl/INTRDRJ1.JCL:9`), `job:DEFCUST` (`app/jcl/DEFCUST.jcl:32`). Ask the client whether they run. `job:FTPJCLS` is not dead code, but it holds a host, user id and password in clear text (`app/jcl/FTPJCL.JCL:33`). Rotate that credential whatever happens to the job.

Thirty-five jobs are named by no parsed scheduler (`analysis` field `unscheduled_jobs`). The number is overstated, because the CA-7 listing is not parsed (`app/scheduler/CardDemo.ca7:18`). Read by hand, it schedules POSTTRAN, CLOSEFIL, OPENFIL, READACCT, READCARD, READCUST, READXREF, CREASTMT, TXT2PDF1, PRTCATBL and TCATBALF (`app/scheduler/CardDemo.ca7:70`, `app/scheduler/CardDemo.ca7:340`, `app/scheduler/CardDemo.ca7:468`, `app/scheduler/CardDemo.ca7:537`). That is inference from a listing the extractor could not read.
