# 05 Dead code

Telemetry: none. Every claim below is provisional. Nothing here is a reason to delete a unit
until someone shows that it did not run in the last twelve months. The register is
`modernization-assessment/dead-code.json:1` and the extractor's candidates are in
`05a-dead-code-candidates.md`.

## Three buckets

| Bucket | Units | Confidence it is dead | Evidence |
|---|---|---|---|
| Unreachable | `cpy:UNUSED1Y` | medium | `app/cpy/UNUSED1Y.cpy:1` |
| Reachable but dormant | none | not measured | `analysis` (field `dead_code_candidates`, dormant is empty) |
| Unknown | `CBTRN01C`, `proc:TRANREPT` | low | `app/cbl/CBTRN01C.cbl:1`, `app/cbl/CORPT00C.cbl:94` |

I did not move any unit toward or away from a bucket. Every extractor candidate is in the same
bucket the extractor put it in.

## Unreachable

`cpy:UNUSED1Y` is a seven line copybook. No program includes it and no other file in the tree
names it (`app/cpy/UNUSED1Y.cpy:1`). Copybooks cannot run, so this is the safest candidate in the
tree to propose for deletion. It is still provisional: another repository could include it, and I
did not have one.

## Reachable but dormant: the empty list means not measured

The rule is five years without a change, as of 2026-09-30, so the cutoff is 2021-09-30. The oldest
last-modified date in the tree is 2022-09-01, and 99 files carry it (`analysis`, computed from the
node dates). One upload date on that many files looks like a bulk import, not a change history.
So the empty list does not say the code is live. It says the date test could not distinguish
anything. Dormancy here needs the client's own change history or telemetry.

## Unknown

| Unit | Why it stays unknown | Evidence |
|---|---|---|
| `CBTRN01C` | No JCL step runs it, no static call reaches it, and the CSD does not define it. Its header reads the same as the posting program's, and it only reads. My reading of the 28 computed calls (see `02-coupling.md`) finds targets only in the menu tables and the COMMAREA return names, and a batch program cannot be started by an XCTL. So I think it is unreachable in fact. I leave it in unknown because the validator forbids moving it, and because a run by hand would leave no trace in the tree | `app/cbl/CBTRN01C.cbl:154`, `app/cpy/COMEN02Y.cpy:28` |
| `proc:TRANREPT` | Named only in JCL text inside `CORPT00C`. The program writes that text to the JOBS queue at run time. It is live whenever a user asks for a report on the screen | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517` |

The evidence line for `COMEN02Y` is `app/cpy/COMEN02Y.cpy:28`; the table lists eleven programs and
`CBTRN01C` is not among them.

## Jobs that cannot appear in a bucket

The extractor counts a job as an entry point unless a parsed scheduler names it. Thirty-five jobs
are not named by Control-M or a wrapper script (`analysis`, field `unscheduled_jobs`). That list is
overstated, and the dead-code warning says why: the CA-7 listing is not parsed
(`app/scheduler/CardDemo.ca7:1`). Reading the listing by hand (inference), eight of the 35 are in
it: `CBPAUP0J`, `CREASTMT`, `PRTCATBL`, `READACCT`, `READCARD`, `READCUST`, `READXREF` and
`TXT2PDF1` (`app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:340`,
`app/scheduler/CardDemo.ca7:495`, `app/scheduler/CardDemo.ca7:537`).

The other 27 are the ones to ask about. They are the build jobs, the samples, the IMS load and
unload jobs, and a few application jobs. Candidates for instrumentation, not deletion:

| Unit | Why it looks unused | Confidence | Evidence |
| --- | --- | --- | --- |
| `job:DEFCUST` | Deletes one cluster and defines another, and no program reads either | medium | `app/jcl/DEFCUST.jcl:25` |
| `job:ESDSRRDS` | Defines demo ESDS and RRDS files that no program reads | medium | `app/jcl/ESDSRRDS.jcl:63` |
| `job:INTRDRJ1`, `job:INTRDRJ2` | Internal reader demo | medium | `app/jcl/INTRDRJ1.JCL:17` |
| `job:SORTTEST`, `job:REPRTEST` | Sample jobs that write production GDG generations | medium | `samples/jcl/SORTTEST.jcl:35`, `samples/jcl/REPRTEST.jcl:33` |
| `job:REPTFILE` | Defines the report GDG that `DEFGDGB` also defines | medium | `app/jcl/REPTFILE.jcl:26`, `app/jcl/DEFGDGB.jcl:36` |
| `job:CBIMPORT` | Cannot run as shipped: its job has no DD for the card output | medium | `app/cbl/CBIMPORT.cbl:233` |
| Alternate index on the transaction master | No program reads it and no CSD entry defines it (inference from a search of the tree). `TRANIDX` and `TRANFILE` still build it | low | `app/jcl/TRANIDX.jcl:27`, `app/jcl/TRANFILE.jcl:84` |

## What I would ask for

Twelve months of job logs or SMF step records for the 27 jobs above, the CICS transaction statistics
for the 25 transactions in the four CSD files (`app/csd/CARDDEMO.CSD:306`), and a search of the client's other
repositories for `UNUSED1Y`. With those three the dormant and unknown buckets become evidence.
