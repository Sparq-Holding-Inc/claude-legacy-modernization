# 05 Dead code

Telemetry: none. Every claim below is provisional. Nobody has said which programs ran in the last 12 months, so a bucket here is a question for the client, not a finding. The extractor's candidates are in `modernization-assessment/05a-dead-code-candidates.md`. The machine-readable register is `modernization-assessment/dead-code.json`.

## The three buckets

Unreachable. No static path from any entry point, and no reachable code makes a computed call that could target it.

| Unit | Type | Reason | Confidence | Evidence |
|---|---|---|---|---|
| cpy:UNUSED1Y | copybook | No program includes it and the name appears in no other file. It describes a user record with a clear-text password field. Safe to propose for deletion, but provisional | high | `app/cpy/UNUSED1Y.cpy:1`, `app/cpy/UNUSED1Y.cpy:5` |

Reachable but dormant. Reachable on paper, not modified for five years, no telemetry. Propose for instrumentation, not deletion.

| Unit | Type | Reason | Confidence | Evidence |
|---|---|---|---|---|
| none | | The extractor's list is empty. See the dormancy note below: an empty list here means not measured | low | analysis field dead_code_candidates |

Unknown. Not reached statically, but something outside the static graph could run it. Do not delete on this evidence.

| Unit | Type | Reason | Confidence | Evidence |
|---|---|---|---|---|
| CBTRN01C | batch program | No JCL step, CSD entry, scheduler or menu table names it, and its six DDs are mapped by no JCL step. The 28 reachable computed calls are CICS transfers, and the two menu tables bound the table-driven ones to 17 online programs, so none can reach a batch program. That points to dead code. It stays in unknown because only telemetry can say it never runs. It reads the daily transaction file and the masters, so it may be an older validation pass ahead of CBTRN02C | medium | `app/cbl/CBTRN01C.cbl:23`, `app/cbl/COMEN01C.cbl:185`, `app/cpy/COMEN02Y.cpy:28`, `app/cpy/COADM02Y.cpy:29` |
| proc:TRANREPT | proc | Named only in JCL text inside CORPT00C, which writes it to the JOBS queue that the CSD maps to the internal reader. It runs whenever a user confirms the report. It is almost certainly live. No graph edge exists, so it is unknown, not unreachable | high | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517`, `app/csd/CARDDEMO.CSD:499` |

I bounded the computed calls by hand (`modernization-assessment/02-coupling.md`). The validator does not let me move CBTRN01C from unknown to unreachable, and I have not tried. The evidence supports it. The rule is right that a static tool should not make that call alone.

## Dormancy was not measured

The dormant list is empty, but that says little. The extractor's last-modified dates come from git, and the tree carries only five distinct dates: 99 files at 2022-09-01, 87 at 2025-08-03, 15 at 2025-10-10, 5 at 2025-10-16 and 1 at 2022-10-12. That is the pattern of bulk imports, not of activity. The newest date of any file is 2025-10-16 (`app/cbl/CBEXPORT.cbl:1`), and nothing is old enough to cross the five-year line as of 2026-09-30. Treat dormancy as not computed for this tree. Real last-change dates need the client's source control history, not this copy.

Dormant does not mean unused. A live program that calls a dormant one unconditionally very likely runs it. Nothing here is proposed for deletion on a date alone.

## Jobs no parser can place

The extractor lists 35 jobs that no parsed scheduler or wrapper names, and warns that the list is overstated because it cannot read the CA-7 listing. I read that listing by hand. All of this is inference.

| Group | Jobs | What names them | Question | Confidence | Evidence |
|---|---|---|---|---|---|
| Named in CA-7 | CBPAUP0J, CREASTMT, PRTCATBL, READACCT, READCARD, READCUST, READXREF, TXT2PDF1 | CA-7 trigger lists | Is CA-7 the production scheduler, and is the listing current? | medium | `app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:340`, `app/scheduler/CardDemo.ca7:468`, `app/scheduler/CardDemo.ca7:495`, `app/scheduler/CardDemo.ca7:537` |
| The transaction report | TRANREPT | Nothing. Not CA-7, not Control-M, not a wrapper. Only CORPT00C submits it, through embedded JCL | Is the batch job ever run by hand, or only as the online-submitted proc? A must-not-break item with no scheduler | high | `app/jcl/TRANREPT.jcl:1`, `app/cbl/CORPT00C.cbl:94` |
| One-off definition jobs | CBADMCDJ, CREADB2, DALYREJS, DEFCUST, DEFGDGB, DEFGDGD, ESDSRRDS, REPTFILE, LOADPADB, DBPAUTP0 | Nothing | Run once at install, or re-run on a schedule the tree does not show? | medium | `app/jcl/DALYREJS.jcl:24`, `app/jcl/DEFGDGB.jcl:25`, `app/jcl/REPTFILE.jcl:25` |
| Migration and utility jobs | CBEXPORT, CBIMPORT, FTPJCLS, INTRDRJ1, INTRDRJ2, LISTFILS, RACFCMDS, UNLDGSAM, UNLDPADB | Nothing | On demand only? | low | `app/jcl/CBEXPORT.jcl:43`, `app/jcl/CBIMPORT.jcl:22` |
| Build and sample jobs | CBLDBMS, CICCMP, CIDBCMP, CNJBATMP, IMSMQCMP, REPRTEST, SORTTEST | Nothing | Confirm they are build tooling. If so they are not application code | low | `samples/jcl/BMSCMP.jcl:38`, `samples/jcl/SORTTEST.jcl:1`, `samples/jcl/REPRTEST.jcl:1` |

CA-7 also names two jobs that have no JCL in the tree: CLOSEFIL1 and CLOSEFIL2 (`app/scheduler/CardDemo.ca7:216`, `app/scheduler/CardDemo.ca7:217`). Either the members are missing or the listing is stale.

## Other findings that look like dead or broken code

Not extractor buckets. Each is a question.

| Finding | Why it may be dead or broken | Confidence | Evidence |
|---|---|---|---|
| job:DEFCUST defines and deletes clusters named AWS.CCDA.CUSTDATA.CLUSTER and AWS.CUSTDATA.CLUSTER | No program or job reads them. The customer file the programs use is defined by CUSTFILE | high | `app/jcl/DEFCUST.jcl:25`, `app/jcl/DEFCUST.jcl:35`, `app/jcl/CUSTFILE.jcl:35` |
| job:CREADB2 carries TYPRUN=SCAN | As shipped it checks the JCL and runs nothing | high | `app/app-transaction-type-db2/jcl/CREADB21.jcl:2` |
| CBIMPORT selects DD CARDOUT, which its JCL never maps | The program cannot open that file as written, so the card branch of the import may never have run | high | `app/cbl/CBIMPORT.cbl:63`, `app/jcl/CBIMPORT.jcl:22` |
| CBACT04C has a fee routine that only exits | Fees are declared and not implemented | high | `app/cbl/CBACT04C.cbl:518` |
| The TRANSACT alternate index is defined by both TRANFILE and TRANIDX | Duplicate definitions. One of them fails or is redundant | high | `app/jcl/TRANFILE.jcl:82`, `app/jcl/TRANIDX.jcl:25` |
| The DB2 table TRANSACTION_TYPE and the VSAM file TRANTYPE hold the same reference data | Two copies. One is fed from the other by TRANEXTR | medium | `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:73`, `app/jcl/TRANTYPE.jcl:57` |
| CREASTMT has a corrupt JCL line | The statement job as shipped may not run | high | `app/jcl/CREASTMT.JCL:90` |
| CICS transaction CDV1 runs a program with no source in the tree | Cannot be assessed | high | `app/csd/CARDDEMO.CSD:390` |

## What would turn these into evidence

Ask the client for twelve months of job and step run records (SMF type 30 or the scheduler's history), CICS transaction statistics by transaction and program, and the catalog's last-referenced date for each dataset. Ask for source-control history that predates the bulk imports. With those, unknown and dormant become findings and the register can be signed.
