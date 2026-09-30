# 04 Estimate

Method: effort is driven by the edges crossing the wave boundary and by whether an oracle exists, not by lines of code. The two programs are 14 lines together (`app/cbl/PROGA.cbl:10`, `app/cbl/PROGB.cbl:4`), so the code is the small part. The unknowns are the size of the callee set and the source of the input. All figures are inference and are low confidence.

## Per wave

| Wave | Range (person-days) | What the range covers | Confidence | Evidence |
|---|---|---|---|---|
| 1 (PROGA, PROGB) | 4 to 12 | Port of the 14 lines: 0.5 to 1. Registry for the dynamic call: 1 to 3. Capture of the input and the called programs' output, and the replay harness: 2.5 to 8. | low | inference. Basis: `app/cbl/PROGA.cbl:9` for the dynamic call, no dataset or JCL in the tree for the oracle. |

This is a range for wave 1 only. It does not cover the programs `PROGA` might call. Those are outside the tree, so they are outside the estimate. The effort to assess and port them is unknown until the callee set is known.

## The assumptions the range is most sensitive to

1. Assumes the `ACCEPT` at `app/cbl/PROGA.cbl:8` takes fewer than about 10 distinct program names over a business cycle. If it takes 50 or more, or free text an operator types, the registry and harness work roughly doubles.
2. Assumes every program `PROGA` can call exists on the load library with source. If any of them is a load module with no source, it cannot be ported in this wave and needs a rehost shim, which adds days per module that cannot be sized here.
3. Assumes the input values can be recovered from job logs or SYSIN archives for a full business cycle. If they cannot, the oracle falls to source-generated characterization tests, which are weaker, and the wave needs a longer parallel run.

## What Claude Code can do and what it cannot

- Strong: transliterating `PROGA` and `PROGB` to the target language, and building the registry and the replay harness once the input capture exists. This is mechanical with a good harness.
- Weak: working out which programs the input names, and what the nightly batch cycle expects of them. Neither is in the source (`app/cbl/PROGA.cbl:9`). This is intent and operational knowledge, and it has to come from the client's engineers.
- Not applicable in this tree: packed decimal, `REDEFINES` and record layouts. None appears in the two programs (inference, from reading both files).

## What moves the estimate, in order

| Factor | State here | Evidence |
|---|---|---|
| Coupling edges crossing the wave boundary | 1, and it is computed | `app/cbl/PROGA.cbl:9` |
| Behavioral oracle | none in the tree | inference |
| God modules in the wave | none | analysis field `god_modules` |
| Business logic in the database | no database access in the two programs | inference |
| Team can read the source language | not known. Asked in Open Questions. | inference |
