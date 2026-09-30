# 04 Estimate

## Method and its limit

The skill asks for an estimate per wave. There are no waves (`03-waves.md`), so there is no wave estimate. Any number for the whole system would be invented, because the tree holds 38 lines of COBOL in four programs (`01-inventory.md`) and no JCL, CSD, scheduler, dataset or copybook. Line count is not what drives the cost anyway. The drivers, in the skill's order, are set out below.

I give one range, for the four programs as found, and I label it inference. It says nothing about the nightly batch cycle, which is not in the tree.

| Driver | What the tree shows | Effect on the estimate | Confidence | Evidence |
|---|---|---|---|---|
| Coupling edges crossing a wave boundary | Three static calls and two computed calls, all out of PROGA. No data, contract or temporal edge. | Small, except that the computed LINK has no bounded target set. | medium | `app/cbl/PROGA.cbl:12`, `app/cbl/PROGA.cbl:16`, `app/cbl/PROGA.cbl:20` |
| Behavioral oracle | None in the tree. No datasets, no archived output, no captured traffic. | Dominant. Most of the range comes from here. | low | inference |
| God modules | None. | None. | medium | analysis: `god_modules` |
| Logic in the database | No SQL, no dataset access in any program. | None seen. | medium | inference |
| Someone who can read the source language | Not known. | Unknown, not assumed. | low | inference |

## Range for the four programs as found

| Piece of work | Range (engineer-days) | Confidence | Evidence |
|---|---|---|---|
| Port PROGB, PROGC, PROGD (each a bare RETURN) | 0.5 to 1 in total | medium | `app/cbl/PROGB.cbl:4`, `app/cbl/PROGC.cbl:4`, `app/cbl/PROGD.cbl:4` |
| Port PROGA, keeping LINK, XCTL and the computed LINK semantics | 1 to 3 | low | `app/cbl/PROGA.cbl:12-25` |
| Capture the COMMAREA values that reach PROGA and turn them into replay cases | 3 to 10 | low | inference |
| Comparison harness, normalization spec and Deviation Register | 2 to 5 | low | inference |
| **Total for these four programs** | **6.5 to 19** | low | inference |

The range is wide because the third row is unknown until someone says whether CICS traffic, journals or monitoring records exist for PROGA.

## The assumptions the range is most sensitive to

1. **Assumes the values that reach PROGA's COMMAREA form a short, closed list of program names.** If a caller can pass any name, the port needs a router that keeps the dynamic lookup, and the third and fourth rows roughly double. If a list of at most a handful of names exists, the third row falls to the low end.
2. **Assumes PROGB, PROGC and PROGD really are empty.** Each is a bare RETURN. If the real bodies live in another library and these are stubs, the first row is wrong by an order of magnitude, and the tree is not the system.
3. **Assumes no JCL, CSD or scheduler content matters to these programs.** If a CSD names PROGA as the initial program of a transaction with a terminal map, or a batch job drives any of them, the boundary changes and this estimate does not apply.

## Where Claude Code can do the port and where it cannot

- **Strong.** Transliterating PROGB, PROGC and PROGD. Mapping the static LINK at line 12 to a call. Mapping the literal-fed XCTL at line 20 to a transfer to PROGC.
- **Strong with a harness.** Reproducing the LINK-returns and XCTL-never-returns difference, and the fact that the XCTL to PROGD at line 23 does not run.
- **Weak.** Deciding which program names production actually passes in the COMMAREA. The source does not say, and the answer has to come from the client's traffic. Also weak: deciding what a caller with no COMMAREA should do, and whether the bare-RETURN programs are stubs.
- **Cannot do at all from this tree.** Anything about the nightly batch cycle.
