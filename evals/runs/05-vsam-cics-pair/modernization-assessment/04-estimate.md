# 04 Estimate

Every number here is `inference`. There is no runtime data, no test suite and no team profile in the
tree. Do not read the range as a commitment. Read the assumptions.

## Method

Not lines of code. I weighted, in this order: coupling edges crossing the wave boundary, whether a
behavioral oracle exists, god modules, logic held in the database, and who can read COBOL.

| Driver | Finding | Evidence |
|---|---|---|
| Edges crossing the boundary | 1 contract edge, 2 data edges, 0 call edges, 0 temporal edges | `app/cbl/PROGR.cbl:7`, `app/cbl/PROGW.cbl:7` |
| Oracle in the tree | None. No datasets, job output, logs or reports. | inference |
| God modules | None | inference |
| Logic in the database | No EXEC SQL in either program | `app/cbl/PROGR.cbl:6-11` |
| Team that can read COBOL | Unknown | inference |

## Wave 1, ACCTDAT online pair

Range: 4 to 12 person-days, all in. Of that, the transliteration of the two programs is under one
day. The rest is the harness, the oracle and the sign-off on the normalization spec.

The range is most sensitive to three assumptions, each stated so it can be proven wrong:

1. **Assumes the nightly batch cycle is the only other consumer of ACCTDAT, and that the client can
   supply its job output.** If the batch cycle has programs that read or write ACCTDAT by offset and
   they are in scope for equivalence, the wave roughly doubles, because the harness must then drive
   those jobs too.
2. **Assumes the KSDS stays in place and the 17 byte ACCTREC layout is preserved** (see
   `app/cpy/ACCTREC.cpy:1-3`). If the refactor moves ACCTDAT to a relational store, add a data
   migration and a key mapping. That roughly doubles the wave.
3. **Assumes archived ACCTDAT images or CICS journals exist to replay.** If not, the oracle falls to
   characterization tests generated from the source, which are provisional, and the range gains 3 to 5
   days for building a synthetic case set.

## Where Claude Code can do the mechanical work

- Strong: transliterating the two programs, and encoding and decoding the ACCTREC record, including
  the COMP-3 balance (`app/cpy/ACCTREC.cpy:3`), when a test harness with real records exists.
- Weak: intent. Neither program sets its key or its record and neither handles a failed READ or WRITE
  (`app/cbl/PROGR.cbl:4-10`, `app/cbl/PROGW.cbl:4-10`). What the transactions are for, and what should
  happen on not found or duplicate key, are not inferable from the source. A person who owns the
  business rule has to say.
