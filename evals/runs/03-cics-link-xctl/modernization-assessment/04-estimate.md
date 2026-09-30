# 04 Estimate

Every number here is inference. The tree is 38 lines of COBOL in four files and holds no data, no
JCL and no oracle. The method is stated so the client can replace my assumptions with facts. I give
ranges in person-days for one engineer who can read COBOL and CICS. There is no single number.

## Wave 1: PROGA call tree

| Component | Range | Method | Confidence | Evidence |
|---|---|---|---|---|
| Port the four programs, with a facade for the COMMAREA program-name contract | 1 to 3 person-days | Line count (38 lines) and no logic or arithmetic in PROGB, PROGC or PROGD. The cost is the PROGA facade and the LINK and XCTL semantics, not the code volume. | medium | `app/cbl/PROGA.cbl:12-25`, `app/cbl/PROGB.cbl:4`, `app/cbl/PROGC.cbl:4`, `app/cbl/PROGD.cbl:4` |
| Bound the LINK at line 16: find the callers and the COMMAREA values they pass | 5 to 15 person-days | Depends on evidence the client must supply. Not derivable from this tree. | low | `app/cbl/PROGA.cbl:15`, `app/cbl/PROGA.cbl:16` |
| Build the equivalence harness for the routing behavior | 3 to 10 person-days | Depends on the oracle (see `06-test-strategy.md`): cheapest with CICS journals to replay, dearest with characterization tests from source. | low | inference |
| Total for wave 1 | about 9 to 28 person-days | Sum of the three ranges above. | low | inference |

The nightly batch cycle is outside this estimate. No artifact for it is in the tree, so I cannot size
it, and I will not guess (analysis: `meta.files_seen`).

## The assumptions the range is most sensitive to

Stated so they can be shown false.

1. **"The callers of PROGA pass a small, fixed set of program names in the COMMAREA."** If instead the
   COMMAREA carries a name typed or built at run time, the facade needs an allow-list, the dependency
   discovery grows, and the second row roughly doubles or more.
2. **"PROGB, PROGC and PROGD in production are the same bare RETURN programs as in this tree."** If any
   holds real logic in production, the first row no longer holds and the wave has to be re-cut. The
   source I have shows 4 lines each (`app/cbl/PROGB.cbl:4`, `app/cbl/PROGC.cbl:4`, `app/cbl/PROGD.cbl:4`).
3. **"A CICS journal or transaction log covers the COMMAREA values in use."** If it does, the harness
   row sits near 3 days. If the only oracle is the source, it sits near 10 and every result stays
   provisional.

## What moves the estimate, in this tree

- Coupling edges crossing the wave boundary: none can be counted. The boundary is the COMMAREA in, and
  its inputs are unseen.
- Oracle: none in the tree.
- God modules in the wave: none (analysis: `god_modules`).
- Logic in the database: none visible, since the tree holds no dataset and no SQL (analysis:
  `data_hubs`, `edge_counts`).
- Someone who can read the source language: the client's engineers must be asked. This is a hard
  dependency, because the semantics of XCTL are what the port must keep.

## Where Claude Code can do the port and where it cannot

- **Can, with the harness in place:** transliterate the four programs, and write the tests that pin
  the call order (LINK PROGB, then the COMMAREA target, then XCTL PROGC, and never the rest). The code is
  short and has no arithmetic (`app/cbl/PROGA.cbl:12-25`).
- **Cannot:** say what a caller puts in the COMMAREA, what PROGB, PROGC and PROGD are for, or whether
  the unreachable lines 23 to 26 are meant to be there. That is intent, and no source here records it.
  It also cannot judge whether the facade should keep the caller's free choice of target or narrow it to
  an allow-list. That is a business decision for the client.
