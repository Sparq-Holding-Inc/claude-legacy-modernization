# 04 Estimate

Method: judgment, weighted by what moves an estimate (coupling edges across the wave boundary,
oracle availability, god modules, logic held in the database, team skill). It is not derived from
lines of code, which total 16 here (`analysis`, field `node_counts`, and `app/cbl/PGMMAIN.cbl:1`).
Every figure below is inference. Every range is person days for one engineer who can read COBOL and
JCL.

| Wave | Range | Method and drivers | Evidence |
|---|---|---|---|
| 1 | 3 to 6 person days if the dispatch target set is small and in this tree | Zero data edges, zero contract edges, zero god modules. One open computed call. Port two units plus a dispatch registry. Most of the time is the harness and the discovery, not the code. | inference |
| 1, callees outside this tree | Not estimable | Each new program is a new unit with its own edges. Ask for the load library list first. | `app/cbl/PGMMAIN.cbl:9` |
| Discovery before wave 1 | 1 to 3 person days on the client side | Obtain the SYSIN or proc source, 12 months of job logs for MAINJOB, and the scheduler export. | inference |

## The assumptions the range is most sensitive to

1. Assumes the values supplied to the ACCEPT at `app/cbl/PGMMAIN.cbl:8` form a short fixed list,
   under five names, and every one is a program in this tree. If any name belongs to a program
   outside this tree, the range no longer holds and the wave has no upper bound until those programs
   are supplied.
2. Assumes the client holds archived output for MAINJOB runs (job logs, SYSOUT, the files that the
   dispatched programs write). If none exist, the oracle falls back to characterization tests
   generated from source, which are provisional, and the range grows by about two to four days.
3. Assumes someone on the team can read COBOL and JCL and can sign a deviation register. If not, the
   range roughly doubles, because every read of the source needs outside help.

## Where Claude Code helps and where it does not

| Work | Fit | Evidence |
|---|---|---|
| Transliterate PGMMAIN and HIDDEN01 into the target language with a test harness | Strong. Ten lines and a bare GOBACK. | `app/cbl/PGMMAIN.cbl:10`, `app/cbl/HIDDEN01.cbl:4` |
| Express MAINJOB in the target scheduler | Strong. One step, no DDs. | `app/jcl/MAINJOB.jcl:2` |
| Decide what names the ACCEPT supplies in production | Cannot. This is a fact in the client's environment, not in the source. | `app/cbl/PGMMAIN.cbl:8` |
| Infer the business rules of the dispatched programs | Weak, and unknown, because they are not in the tree. | inference |
