# 05 Dead code

Telemetry: none. The client gave no run history, so every claim on this page is provisional. `05a-dead-code-candidates.md` is the extractor's list. `dead-code.json` is the register. I kept every extractor candidate in the bucket the extractor put it in. I did not move anything from unknown to unreachable, and I did not add dormant items. I added nothing to unknown either, because nothing I read gave a reason.

Three buckets: unreachable, dormant, unknown.

## Unreachable

| Unit | Type | Reason | Confidence | Evidence |
|---|---|---|---|---|
| cpy:UNUSED1Y | copybook | No program includes it. The extractor found no static path and no reachable computed call. A search of the source finds its name only in its own file. It is 7 lines, last changed 2022-09-01. Safe to propose for deletion after one confirmation. | high | `app/cpy/UNUSED1Y.cpy:1` |

## Unknown

Do not delete these on this evidence.

| Unit | Type | Reason | Confidence | Evidence |
|---|---|---|---|---|
| CBTRN01C | batch program | No JCL step runs it and no static edge reaches it, so 28 reachable computed calls could in principle target it. I bounded the menu calls: the option tables do not list it, the CSD defines no program for it, and it opens all six of its files INPUT. It repeats CBTRN02C's header ('Post the records from daily transaction file') and posts nothing. Very likely retired, but a hand run or a member outside the tree would not show here. | low | `app/cbl/CBTRN01C.cbl:254`, `app/cpy/COMEN02Y.cpy:28`, `app/csd/CARDDEMO.CSD:173` |
| proc:TRANREPT | proc | Named only in JCL text inside CORPT00C, which writes that text to the JOBS queue. The CSD maps that queue to the internal reader. CORPT00C is menu option 9. So this proc very likely runs whenever a user asks for the transaction report online. It is a must-not-break item, not dead code. | low | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517`, `app/csd/CARDDEMO.CSD:499`, `app/cpy/COMEN02Y.cpy:77` |

What the computed calls could reach, and why that keeps this bucket open: 20 programs make 28 computed XCTL calls. I could bound 11 of them (the two menu tables, the constants in COCRDLIC and COUSR00C, COTRN00C's transfer to the view, and the three authorization calls). The rest return to a caller named in the COMMAREA, so their set is open (`02-coupling.md`). All the targets I found are online programs, and CBTRN01C is a batch program. That lowers the chance and does not remove it.

## Reachable but dormant

None. The extractor computed dormancy with a 5 year threshold as of 2026-09-30, and the earliest git date on any unit is 2022-09-01 (`analysis` field `as_of`, and the last modified column of `01-inventory.md`). The repository's history starts in August 2022, so no unit can be five years old. An empty list here means the rule could not fire. It does not mean nothing is dormant. A unit's real age may be older than its commit date, and the ticket footers in the JCL show 2022-07-19 for the oldest JCL (`app/jcl/POSTTRAN.jcl:44`). Treat dormancy as not measured.

Reachable but old code worth instrumenting instead: the 1,058 run counts in the CA-7 listing look like template values and are not telemetry (`app/scheduler/CardDemo.ca7:24`). Ask for real job logs or SMF records.

## Jobs no parsed scheduler runs

A job that no parsed scheduler names counts as an entry point, so it never shows in a bucket. There are 35. Some of them are scheduled in the CA-7 listing, which the extractor cannot parse. The warning says the list is overstated. Here is what I could see in the listing (inference):

| Job | Where CA-7 names it | Confidence | Evidence |
|---|---|---|---|
| job:READACCT | Triggered after CLOSEFIL | medium | `app/scheduler/CardDemo.ca7:340` |
| job:READCARD | Triggered after READACCT | medium | `app/scheduler/CardDemo.ca7:367` |
| job:READCUST | Triggered after READCARD | medium | `app/scheduler/CardDemo.ca7:394` |
| job:READXREF | Triggered after READCUST | medium | `app/scheduler/CardDemo.ca7:421` |
| job:CREASTMT | Triggered after CLOSEFIL | medium | `app/scheduler/CardDemo.ca7:468` |
| job:TXT2PDF1 | Triggered after CREASTMT | medium | `app/scheduler/CardDemo.ca7:495` |
| job:PRTCATBL | Triggered after a second CLOSEFIL | medium | `app/scheduler/CardDemo.ca7:537` |
| job:CBPAUP0J | Triggered after CLOSEFIL, and it triggers POSTTRAN | medium | `app/scheduler/CardDemo.ca7:43` |

The other 27 stay unscheduled as far as I can see. Ask whether they still run. Three of them the client should confirm first, because they are must-not-break or close to it:

| Job | Why it matters | Confidence | Evidence |
|---|---|---|---|
| job:TRANREPT | The transaction report job. No scheduler names it. It also exists as the proc that CORPT00C submits. Two copies of the same steps. | medium | `app/jcl/TRANREPT.jcl:59`, `app/proc/TRANREPT.prc:57` |
| job:CBEXPORT and job:CBIMPORT | A branch migration path. Not scheduled. The import job cannot run as shipped. | medium | `app/jcl/CBEXPORT.jcl:43`, `app/jcl/CBIMPORT.jcl:33` |
| job:DEFCUST | Deletes a cluster under a different qualifier (AWS.CCDA), so it targets nothing in this system. | medium | `app/jcl/DEFCUST.jcl:25` |

The account and card refresh jobs (ACCTFILE and CARDFILE) are not in the unscheduled list because the wrapper scripts name them. Neither Control-M nor the CA-7 listing runs them, so their cadence is not on record.

## Other things worth asking about

These are not extractor candidates. They are gaps I noticed and I did not put them in a bucket.

| Item | What I saw | Confidence | Evidence |
|---|---|---|---|
| Transaction alternate index | TRANIDX and TRANFILE build an alternate index on the transaction master. No program and no CSD file in the tree reads its path. | medium | `app/jcl/TRANIDX.jcl:43`, `app/jcl/TRANFILE.jcl:100` |
| COCRDSEC | The CSD defines a program and the developer transaction CDV1 for it. There is no source. | high | `app/csd/CARDDEMO.CSD:211`, `app/csd/CARDDEMO.CSD:388` |
| CLOSEFIL1 and CLOSEFIL2 | The CA-7 listing triggers two jobs with no JCL in the tree. | medium | `app/scheduler/CardDemo.ca7:216` |
| The two internal reader demos | INTRDRJ1 feeds INTRDRJ2 to the internal reader. Neither is scheduled. | medium | `app/jcl/INTRDRJ1.JCL:17` |
| FTP job | Holds a clear text address, user and password. Retire and rotate. | high | `app/jcl/FTPJCL.JCL:33` |
