# 06 Test strategy

Produced with the `behavioral-equivalence` skill. The bar: for the inputs this system actually sees,
the refactored PROGR and PROGW produce the same outputs as the legacy ones. Where they differ, someone
decided that on purpose and wrote it down.

## The oracle problem, stated plainly

The tree holds no datasets, no job output, no logs and no reports. `graph.json` shows one dataset
node, and it is a name taken from the CSD (`app/csd/DEMO.CSD:2`), not data. The oracle cannot come
from the tree. It has to come from the client. Every oracle below is `inference` until the client
confirms it exists.

### What I would ask the client to supply

| Ask | Why it matters | Evidence |
|---|---|---|
| A recent image copy or REPRO of the production ACCTDAT KSDS, and the IDCAMS DEFINE CLUSTER for it | Gives real records, the true key offset and length, and the record size. The tree only shows the 17 byte layout by inference. | `app/cpy/ACCTREC.cpy:1-3` |
| CICS journals or transaction logs for TRNR and TRNW covering a full business cycle | Captured inputs for replay. Neither program takes input from a COMMAREA or a map in the tree. | `app/cbl/PROGR.cbl:4-9` (inference) |
| The JCL, the scheduler definitions and archived job output (GDG generations) for the nightly batch cycle | The stated must-not-break item. It is the strongest golden master for what happens to ACCTDAT overnight. | inference |
| Any partner extracts or reports built from ACCTDAT | Whatever left the building is an executable spec of the record format. | inference |
| Confirmation of whether `SPARQ.TEST.ACCTDAT.KSDS` is the production dataset or a test copy | The CSD names a TEST dataset. | `app/csd/DEMO.CSD:2` |

## Oracle for wave 1

In descending strength. Take the strongest that the client can supply.

1. **Parallel run.** TRNR and TRNW are small and stateless in the tree. Run the legacy and the
   refactored transaction against the same keyed file image and diff the file and the responses. Ask
   first whether this is possible. It probably is for an online pair this size. `inference`.
2. **Captured traffic replay.** Replay journal records for both transactions against a restored ACCTDAT
   image. The capture window must include month end and fiscal year end, and one full run of the
   nightly batch cycle.
3. **Golden master from archived outputs.** Use archived batch output that consumed ACCTDAT.
4. **Characterization tests from the source.** Weakest. Use only if 1 to 3 are unavailable, and label
   the coverage provisional. The source here carries no rules to characterize beyond one READ and one
   WRITE (`app/cbl/PROGR.cbl:7-10`, `app/cbl/PROGW.cbl:7-10`).

The nightly batch cycle is the must-not-break anchor. The wave is not done until the batch cycle's
archived output matches with the refactored online pair in place.

## Normalization spec

Every line is a claim that a difference does not matter. Keep it short and have a person sign it.

| Item | Proposed rule | Why | Evidence |
|---|---|---|---|
| Packed decimal balance | Compare as a decimal type with zero tolerance. Never as a float. Decide whether sign nibble C and F are the same for a positive value, and write the decision here. | ACCT-BAL is `S9(9)V99 COMP-3`. Encoders differ in the sign nibble. | `app/cpy/ACCTREC.cpy:3` |
| Key digits | Compare ACCT-ID as 11 digits. Decide the code page (EBCDIC F0 to F9 or ASCII 30 to 39) at the record boundary. | Display numeric field. | `app/cpy/ACCTREC.cpy:2` |
| Collating and key order | Keep ascending key order. For a purely numeric key EBCDIC and ASCII agree on digits. Test for keys that hold spaces, low values or letters, where they do not. | A KSDS returns records in key order and a reader may depend on it. | `app/cpy/ACCTREC.cpy:2` (inference) |
| REDEFINES | None in the copybook. Nothing to normalize. | The copybook has no REDEFINES. | `app/cpy/ACCTREC.cpy:1-3` |
| Padding and low values | Decide whether trailing spaces and binary zeros in the record compare equal. Default: they do not. | Fixed width record. | `app/cpy/ACCTREC.cpy:1-3` (inference) |
| Timestamps, run ids, sequence numbers | None appear in the record or the programs. Do not add any to the spec. | Keeps the spec short. | `app/cbl/PROGW.cbl:7-10` |
| Job order | No temporal edge exists in `graph.json`. The order of online writes against the nightly batch cycle is unknown and must be supplied. | The order the harness must keep is not in the tree. | inference |

## Targeted cases

Add these on top of replay. Each one comes from something the source shows.

- The balance at its limits: 999999999.99, -999999999.99, zero, and negative zero
  (`app/cpy/ACCTREC.cpy:3`).
- A packed field with an invalid sign nibble or invalid digit nibbles. Legacy data often has them. The
  refactor must reproduce the legacy behavior, which is often neither an error nor a sane result.
- A non-numeric ACCT-ID: spaces, low values, letters in the digit field (`app/cpy/ACCTREC.cpy:2`).
- READ of a key that does not exist. Neither program has RESP or HANDLE CONDITION, so the legacy
  behavior is an abend and the refactor must match or the deviation must be recorded
  (`app/cbl/PROGR.cbl:7-10`).
- WRITE of a key that already exists, and WRITE when the file is closed or disabled
  (`app/cbl/PROGW.cbl:7-10`).
- The key value with which PROGR and PROGW start. Both use ACCT-ID as RIDFLD and never set it, and
  PROGR's READ INTO overwrites it (`app/cbl/PROGR.cbl:7-9`, `app/cbl/PROGW.cbl:7-9`). Find out where
  the real key comes from and test that path. `inference`.
- Boundary dates for the nightly batch cycle: month end, quarter end, fiscal year end, leap day.
  `inference`: the tree does not say which paths run only at close.
- An empty file, and a file at its maximum size. `inference`.
- Whether the CSD file definition allows WRITE at all (`app/csd/DEMO.CSD:1-3`). Test the
  refactored PROGW under the real file definition, not a permissive one.

## Deviation register

Nothing differs without a row. It starts empty. The two candidates below are not decided and not
approved. They are here so nobody ships them as a silent fix.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| DEV-001 (candidate) | READ and WRITE have no RESP handling, so a failure abends. | Not decided. | Not decided. | none yet | Unknown. Would change what the nightly batch cycle sees on failure. |
| DEV-002 (candidate) | RIDFLD ACCT-ID is never set in the program. | Not decided. | Not decided. | none yet | Unknown. |

## Exit bar for wave 1

The wave is done when all of these hold:

- The replay diff is clean, modulo the normalization spec and the deviation register.
- Every targeted case above passes.
- The nightly batch cycle output, run with the refactored pair in place, matches the archived output.
- The harness is under version control and runs in CI.
- The deviation register is signed by someone with the authority to sign it.

Not when the port compiles, and not when it passes tests written alongside the port. Keep the harness
after cutover. It becomes the regression suite.
