# 04 Estimate

Method: per wave, as a range, with the assumptions it is most sensitive to. The count of edges crossing the wave boundary drives it, not lines of code. Here the boundary edges are: none call, none data, none temporal (`analysis`, field `edge_counts` holds only `include`). The estimate is judgment. It is labeled inference.

## Wave 1: PROGA and PROGB (provisional)

| Part | Range | Confidence | Evidence |
|---|---|---|---|
| Port both programs and the copybook to the target, with a decimal type for the balance | 1 to 3 engineer-days | low | inference |
| Build the equivalence harness for the wave | not estimable until the client supplies the batch cycle output | low | inference |

The programs hold 8 lines each and one MOVE each (`app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7`). The port is close to nothing. The real cost sits in the harness and in whatever the missing JCL adds. A number for the whole wave would suggest rigor the tree cannot support.

### Assumptions the range is most sensitive to

1. Assumes this tree is the whole of what PROGA and PROGB do. If the missing JCL runs them against files that use the SHARED01 layout, the wave gains a contract edge and a harness on that file. The range roughly doubles or more.
2. Assumes nobody reads SH-BALANCE outside the tree. If a report or partner extract reads it by offset, the packed decimal layout must be reproduced byte for byte, and the wave needs a decimal type with zero tolerance.
3. Assumes the two programs are live. If no job runs them, the right cost is a deletion review, not a port. See `05-dead-code.md`.

## Where Claude Code can do the port, and where it cannot

- Strong: the transliteration of both programs and the copybook. It is mechanical, given a test harness.
- Weak: intent. Nothing says why PROGA moves 1 and PROGB moves 2 into SH-CUST-ID. The source has no comment and no calling context. A person who knows the nightly cycle must say whether these values are real.

## What was not estimated

The nightly batch cycle. It is not in the tree, so nothing about it can be sized.
