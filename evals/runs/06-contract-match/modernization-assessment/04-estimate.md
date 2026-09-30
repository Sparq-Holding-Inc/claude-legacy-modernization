# 04 Estimate

Method: bottom-up by task, in person-days, for a team that can read COBOL and JCL. It is not derived from LOC. The whole tree is 16 lines per program (`app/cbl/PGMR.cbl:16`, `app/cbl/PGMW.cbl:16`), so LOC would say almost nothing. Every number here is inference. There is no history, telemetry or velocity data in the tree to calibrate against.

## Wave 1: master file writer and reader pair

| Task | Range (person-days) | Confidence | Evidence |
|---|---|---|---|
| Discovery: get the scheduler export, the real dataset listing and the list of consumers | 2 to 5 | low | inference |
| Port PGMR and job:READJOB | 1 to 2 | medium | `app/cbl/PGMR.cbl:14` |
| Port PGMW and job:WRITEJOB, including byte exact packed decimal output | 2 to 4 | medium | `app/cbl/PGMW.cbl:14`, `app/jcl/WRITEJOB.jcl:4` |
| Equivalence harness: byte compare, normalization spec, boundary cases | 3 to 6 | medium | `app/cpy/LAYOUTX.cpy:3` |
| Deviation register, sign off, cutover and rollback rehearsal | 1 to 3 | low | inference |
| **Total** | **9 to 20** | low | inference |

The range is wide on purpose. Most of the width sits in discovery and the harness, not in the port.

## The assumptions the range is most sensitive to

1. **Assumes SPARQ.TEST.MASTER has no consumer other than PGMR.** If other programs, sort steps or partner extracts read it, the harness scope and the blast radius grow, and the total roughly doubles. Nothing in the tree shows other readers, but the extractor cannot see outside the tree (inference).
2. **Assumes a real copy of the dataset, or an archived generation of it, can be obtained.** If none exists, the oracle is characterization tests built from source, which are provisional, and add about 3 to 5 days to build test data (inference).
3. **Assumes the 15 byte logical record and the LRECL=80 on the DD are reconcilable in a day.** If the real file on disk is 80 byte padded records and a downstream reader depends on that, the porting rules for record padding become a decision with a sign off. If the real file is 15 byte records, the DD is misleading and the physical format must come from the catalog. Either answer is fast to find, but an unexpected answer adds a deviation register entry (`app/jcl/WRITEJOB.jcl:4`, `app/cpy/LAYOUTX.cpy:3`).
4. **Assumes the tree is the whole nightly cycle.** If the cycle has jobs outside the tree, this estimate covers a fragment only, and the fragment's place in the sequence is unknown (inference).

## What moves this estimate

- **Coupling edges crossing the boundary.** One: the contract edge on the dataset (`02a-edge-tables.md`). This keeps the estimate low.
- **Behavioral oracle.** None is in the tree. It is the largest swing factor, in assumption 2.
- **God modules.** None.
- **Business logic in the database.** No SQL or DB2 in the tree (`graph.json` has no db2 datasets), so none is visible.
- **Language skills.** Assumed present. If not, add discovery time for every task.

## Where Claude Code helps and where it does not

- **Strong here.** Transliterating PGMR and PGMW is a mechanical port of two 16 line programs. Generating the byte level comparison harness and boundary cases for the 15 byte record is also well suited to it, once the oracle exists.
- **Weak here.** Deciding intent. PGMW never sets a field before it writes (`app/cbl/PGMW.cbl:14`), and PGMR reads only one record (`app/cbl/PGMR.cbl:14`). Whether that is a stub, a test fixture, or a real behavior to preserve is a business question. It cannot be settled from source. Neither can what the nightly cycle is.
