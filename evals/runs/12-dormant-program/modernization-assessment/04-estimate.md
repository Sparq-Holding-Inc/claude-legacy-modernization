# 04 Estimate

Method: a range per wave, driven by the count of coupling edges that cross the wave boundary, the
availability of an oracle, god modules and database logic, not by lines of code. Every number here is
inference. The tree holds 14 lines of COBOL and 2 lines of JCL, and no dataset. The estimate holds only
for what the tree shows.

## Wave 1: nightly batch cycle (4 units)

| Driver | Reading | Confidence | Evidence |
|---|---|---|---|
| Coupling edges crossing the wave boundary | 0. No dataset, no second entry point, no scheduler successor is visible. | medium | analysis fields `data_hubs`, `entry_points` |
| Behavioral oracle | None in the tree. It has to be collected from the client (job logs, archived output). | high | analysis field `data_hubs` |
| God modules | None | high | analysis field `god_modules` |
| Business logic in the database | None visible. No EXEC SQL, no DB2 node. | medium | analysis field `node_counts` |
| Team can read COBOL | Unknown | low | inference |

| Item | Range (person-days) |
|---|---|
| Port of 4 units, refactor target | 1 to 2 |
| Collect the oracle and the normalization spec | 2 to 5 |
| Build and run the equivalence harness, including a parallel or replay run over one month-end | 3 to 6 |
| Total for wave 1 | 6 to 13 |

## The assumptions the range is most sensitive to

1. Assumes the tree is the whole nightly cycle. If `OLDPGM` and `NEWPGM` are stubs and the real logic is
   built or linked from elsewhere, the port line roughly multiplies by the size of that code, and the
   range no longer applies. Evidence for the doubt: `app/cbl/OLDPGM.cbl:4`, `app/cbl/NEWPGM.cbl:4`.
2. Assumes the client can supply at least 12 months of job logs or archived output for `MAINJOB`. If
   they cannot, the oracle falls back to characterization tests, and the harness line roughly doubles
   while the result is only provisional.
3. Assumes `OLDPGM` still does something the cycle needs. If it turns out to be retired and its call is
   a leftover, the port drops one unit but a decision to remove it needs a signed row in the deviation
   register. Evidence: `app/cbl/PGMMAIN.cbl:4`.

## What Claude Code can and cannot do here

- Can do: transliterate the two `CALL` statements and the `GOBACK`s to the target, and write a job
  wrapper that keeps the call order. That is mechanical, and with a harness it is safe.
- Cannot do: say what `OLDPGM` and `NEWPGM` are for, or whether their order matters. The tree has no
  intent to infer. That comes from the client's engineers.
