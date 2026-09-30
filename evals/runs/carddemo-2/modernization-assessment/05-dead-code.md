# 05 Dead code

The candidates come from the extractor and are listed in `05a-dead-code-candidates.md`. This file is my judgment on them. Telemetry is none, so **every claim here is provisional**. Nothing below is safe to delete on this evidence alone, with one exception noted in the first bucket.

## The three buckets

### Unreachable

| Unit | Verdict | Confidence | Evidence |
|---|---|---|---|
| cpy:UNUSED1Y | Propose for deletion after the client confirms. No program includes it and the name appears nowhere else in the tree | high | `app/cpy/UNUSED1Y.cpy:1` |

The extractor also put `proc:TRANREPT` here. I moved it to the unknown bucket, because it is live. See below.

### Reachable but dormant

Empty. The extractor's rule is 5 years without a modification as of 2026-09-30. The oldest file dates in the tree are 2022-09-01, which is 4 years old. Those dates come from the git history of this copy, so they are the date the code was imported and not the date the mainframe source last changed. Dormancy says nothing about this system. Fifteen programs carry the 2022-09-01 date (see `01-inventory.md`), and on 2027-09-01 all of them would flip to dormant with no change in behavior. Do not use date-based dormancy on this tree.

### Unknown

Eleven units. Ten came from the extractor. One I moved in from the unreachable list.

| Unit | What I found | Likely status | Evidence |
|---|---|---|---|
| proc:TRANREPT | CORPT00C writes JCL text containing `EXEC PROC=TRANREPT` to the JOBS TDQ. The extractor does not follow the internal reader. The proc file's first line declares a proc named REPROC, so the name in the JCL library member and the proc name inside it disagree | Live. The online report path depends on it | `app/cbl/CORPT00C.cbl:94`, `app/proc/TRANREPT.prc:1` |
| CBPAUP0C | Run as an IMS BMP by CBPAUP0J through a PARM. The CA-7 listing chains CBPAUP0J ahead of POSTTRAN | Probably live | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/scheduler/CardDemo.ca7:43` |
| CBTRN01C | No runner anywhere in the tree. Reads six files and its header says it posts daily transactions | Cannot tell. Instrument it | `app/cbl/CBTRN01C.cbl:5` |
| COBTUPDT | Run by MNTTRDB2 through a DSN command. MNTTRDB2 is in the Control-M weekly folder | Probably live weekly | `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30`, `app/scheduler/CardDemo.controlm:27` |
| DBUNLDGS | Run by UNLDGSAM through a DL/I PARM. No scheduler names the job | Probably run by hand | `app/app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL:27` |
| PAUDBLOD | Run by LOADPADB as a BMP. No scheduler names the job | Probably a one time load | `app/app-authorization-ims-db2-mq/jcl/LOADPADB.JCL:27` |
| PAUDBUNL | Run by UNLDPADB through a DL/I PARM. No scheduler names the job | Probably run by hand | `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:39` |
| cpy:IMSFUNCS | Included only by three programs that are themselves in this bucket | Follows its includers | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:136`, `app/app-authorization-ims-db2-mq/cbl/PAUDBLOD.CBL:142` |
| cpy:PADFLPCB | Included only by DBUNLDGS | Follows DBUNLDGS | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:156` |
| cpy:PASFLPCB | Included only by DBUNLDGS | Follows DBUNLDGS | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:155` |
| cpy:PAUTBPCB | Included only by DBUNLDGS, PAUDBLOD and PAUDBUNL | Follows its includers | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:154`, `app/app-authorization-ims-db2-mq/cbl/PAUDBLOD.CBL:161` |

**The computed calls are bounded, and that does not change any placement.** The extractor's reason for the unknown bucket is that 28 computed calls in reachable code could target any unreached program. I read them (see `02-coupling.md`). Every one is an `EXEC CICS XCTL` in an online program, and every program name that can reach them is an online program. So none of the batch programs above can be the target of any of them. The rule says to say so and to leave them in unknown, and I did. What keeps them unknown is different: the extractor does not follow the three ways they are actually run, which are the IMS PARM, the DSN command and the internal reader.

## Beyond the extractor's buckets

These are jobs. A job with no caller is an entry point, so the extractor never calls it dead. I list them because the migration should not carry them. None is a deletion proposal on its own, and each needs a client answer.

| Unit | Why it may not be needed | Evidence |
|---|---|---|
| job:DEFCUST | Defines AWS.CUSTDATA.CLUSTER, which no program reads. Its key length of 10 disagrees with CUST-ID PIC 9(09) and with CUSTFILE.jcl | `app/jcl/DEFCUST.jcl:37`, `app/jcl/CUSTFILE.jcl:50` |
| job:ESDSRRDS | Builds ESDS and RRDS copies of the user file that nothing reads | `app/jcl/ESDSRRDS.jcl:26` |
| job:FTPJCLS | FTP demo. The login fields are in the JCL stream, so rotate that credential | `app/jcl/FTPJCL.JCL:34` |
| job:INTRDRJ1 and job:INTRDRJ2 | Internal reader demos | `app/jcl/INTRDRJ1.JCL:14` |
| job:REPRTEST and job:SORTTEST | Test jobs | `samples/jcl/REPRTEST.jcl:1`, `samples/jcl/SORTTEST.jcl:1` |
| job:REPTFILE | Defines the TRANREPT generation group with a limit of 10, and DEFGDGB defines the same group with a limit of 5. One of them is stale | `app/jcl/REPTFILE.jcl:27`, `app/jcl/DEFGDGB.jcl:38` |
| Compile jobs and procs | CBLDBMS, CICCMP, CIDBCMP, CNJBATMP, IMSMQCMP and the four BUILD procs. The new build pipeline replaces them | `samples/jcl/BMSCMP.jcl:1`, `samples/proc/BUILDBAT.prc:1` |

## What telemetry would change

Ask the client for 12 months of SMF type 30 records or job logs for the batch side and CICS transaction statistics for the online side. With them:

- CBPAUP0C, COBTUPDT, DBUNLDGS, PAUDBLOD and PAUDBUNL would move to live or to dormant with evidence.
- CBTRN01C would either get a runner or become a deletion candidate.
- The dormant bucket would become meaningful, because run dates would replace commit dates.
