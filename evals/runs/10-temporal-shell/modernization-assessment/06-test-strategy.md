# 06 Test strategy

The must-not-break item is "the nightly batch cycle". It maps to `sch:scripts/nightly.sh`, `job:JOBA` and `job:JOBB` (`scripts/nightly.sh:4`, `scripts/nightly.sh:5`). The tree holds no dataset, no program and no archived output, so the oracle has to come from job output, logs and reports. None of those is in the tree. The client must supply them.

## Oracle for wave 1

| Rank | Oracle | Status here | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Parallel run: run old and new wrapper on the same night and diff | Possible if the old chain can stay up. Ask. | low | `scripts/nightly.sh:4` |
| 2 | Replay of captured job logs and return codes | Needs 12 months of logs and SMF job records from the client, including month-end | low | inference |
| 3 | Golden master from archived outputs | None visible. Jobs allocate nothing in the tree. Ask what the real cycle writes. | low | `jcl/JOBA.jcl:2` |
| 4 | Characterization tests from source | The fallback. Provisional. Covers only submit order and stop-on-failure. | low | `scripts/nightly.sh:3` |

Chosen: parallel run if the client allows, otherwise rank 2. If only rank 4 exists, label coverage provisional.

## What the harness asserts

| Assertion | Why | Evidence |
|---|---|---|
| JOBA is submitted before JOBB | The only ordering rule in the tree | `scripts/nightly.sh:4`, `scripts/nightly.sh:5` |
| JOBB is not submitted when JOBA's submit fails | `set -e` | `scripts/nightly.sh:3` |
| JOBC is never submitted | Its line is commented out | `scripts/nightly.sh:6` |
| Each job ends with the same return code as before | IEFBR14 gives a return code and little else | `jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2` |
| Datasets the real cycle writes match, once the client names them | Unknown now | inference |

## Normalization spec (for a human to sign)

- Ignore job numbers, run timestamps and elapsed times.
- Ignore wrapper log wording, but keep exit codes.
- Do not normalize record order or padding on any output until the client names an output. When one is named, decide on collating sequence (EBCDIC against ASCII) and packed decimal (zero tolerance on money) then.

## Targeted cases

- A night where JOBA fails. Does JOBB run?
- A night with month-end and fiscal-year-end dates. Does the cycle change behavior? No evidence either way in the tree (inference).
- A late or empty run: what the cycle does when it starts after its usual window.
- JOBC: confirm that nothing submits it.

## Deviation register

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| D-1 | JOBC exists but is not submitted | JOBC removed | Retired per the wrapper header | pending, client engineer | none expected, unconfirmed | `scripts/nightly.sh:2` |

## Exit bar for wave 1

- Diff clean against the chosen oracle, within the signed normalization spec and the register.
- The failure-order cases pass.
- The harness is in version control and runs in CI.
- The register is signed by someone with authority.

Keep the harness after cutover as the regression suite.
