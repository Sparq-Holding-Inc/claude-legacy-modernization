# CardDemo truth: adjudication log

Status: DRAFT. Every decision here is unconfirmed until Gary reviews it.

Each COBOL partition was labeled twice by independent subagents. The two
passes agreed on 360 of 361 edges. The single disagreement was settled by
reading the source.

| Partition | Only in one pass | Decision | Reason |
|---|---|---|---|
| O1 | second labeler pass: `COACTUPC -> CSUTLDTC` call | include | `COACTUPC.cbl:4232` says `COPY CSUTLDPY`. `CSUTLDPY.cpy:293` holds `CALL 'CSUTLDTC'`. COPY puts that source inside COACTUPC at compile time, so the call belongs to COACTUPC. A scan of every copybook in scope found this is the only executable statement inside a copybook, and only COACTUPC copies that member. |

## Rule this adds

A statement inside a copybook belongs to every program that copies it. The
evidence lists both places: the COPY line and the line inside the copybook.
An extractor that does not expand COPY will miss this edge. That is the
point of keeping it.

## Judgment calls the labelers made, accepted as written

These follow the labeling guide literally. A reviewer may disagree.

1. **Called subprograms inherit no DDs.** `CBSTM03B` is called by
   `CBSTM03A`. No JCL step runs it, so its four file edges point at
   `ds:dd:CBSTM03B.*` and are unresolved. In a real run unit the DDs on the
   `CBSTM03A` step (`CREASTMT.JCL` lines 83 to 86) serve `CBSTM03B`. The
   truth follows the guide. The extractor is graded against that.
2. **Self edge in COCRDLIC.** `MOVE LIT-THISPGM TO CCARD-NEXT-PROG` plus the
   "every literal counts" rule gives `COCRDLIC -> COCRDLIC`. Control flow
   never does this. The rule is flow insensitive on purpose.
3. **Split statements.** `EXEC CICS` on one line and `XCTL PROGRAM(...)` on
   the next: evidence and the `?dynamic:PROGRAM:LINE` id use the first line
   of the statement. Three ids in COADM01C and COBIL00C would shift by one
   under the other reading.
4. **DISP based mode for utilities.** IDCAMS REPRO targets are DISP=SHR or
   OLD, so the guide labels them `read`. They are written. In-stream control
   cards are out of scope in v0.2.
5. **Internal reader.** `INTRDRJ1` submits `INTRDRJ2` through
   `SYSOUT=(A,INTRDR)`. No job to job edge is labeled.
6. **Missing job targets.** Control-M jobs `MNTTRDB2` and `TRANEXTR` point at
   JCL that lives in `app/app-transaction-type-db2`, which is out of scope.
7. **Contract edges are derived.** They come from labeled data edges and
   layout copybooks by rule. They were not labeled by hand.
8. **Source typos kept.** `FTPJCL.JCL` declares job `FTPJCLS`. Dataset names
   in `INTRDRJ1.JCL` and `INTRDRJ2.JCL` read `CARDEMO`. `TRANREPT.prc`
   declares `//REPROC PROC`. The truth uses what the file says, and proc ids
   use the member name (the file stem), as z/OS does.
