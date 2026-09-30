---
name: behavioral-equivalence
description: Design a test harness that proves a ported or rewritten COBOL, CICS or JCL component behaves identically to the legacy one. Use when the user asks how to verify a migration, how to prove a rewrite is correct, how to test a port, what "done" means for a modernization wave, or asks about characterization tests, golden-master testing, parallel run, or shadow traffic. Also use after a modernization assessment, to define the acceptance bar for each wave.
---

# Behavioral equivalence

"It passes the tests" is not the bar. The legacy system has no tests. The bar is: **for the
inputs this system actually sees, the new implementation produces the same outputs as the
old one, and where it does not, someone decided that on purpose and wrote it down.**

## Pick the oracle first

Everything downstream depends on what you can compare against. In descending order of
strength:

1. **Parallel run.** Both systems process the same production inputs; outputs are diffed.
   The gold standard. Expensive, and needs the old system to stay up. Always ask whether
   this is possible before settling for anything weaker. Teams assume it is not and are
   often wrong.
2. **Captured production traffic replay.** Record real inputs and outputs over a period that
   covers the business cycle, replay against the new system. Nearly as good as parallel run
   and much cheaper. The capture window must include month-end and, for anything financial,
   fiscal year-end.
3. **Golden master from archived outputs.** The client almost certainly has years of archived
   reports, extracts, and statements. These are free test cases nobody thinks to use.
4. **Characterization tests generated from the legacy source.** Weakest, because it encodes
   what the code says rather than what it does. Use only where 1–3 are unavailable, and label
   the resulting coverage as provisional.

State the chosen oracle per wave. Different waves legitimately use different oracles.

## Normalize before you diff

A naive diff of two outputs will be 100% failures for reasons that don't matter. Before
comparing, agree a normalization spec and write it down:

- timestamps, run IDs, sequence numbers, page numbers
- floating-point tolerance. Be careful here. Legacy financial systems typically use
  packed decimal / fixed-point arithmetic. Porting to IEEE 754 floats introduces rounding
  differences that are *real defects*, not noise. Choose a decimal type in the target and
  set tolerance to zero for monetary fields.
- record ordering where the legacy system's order was incidental (and confirm it *was*
  incidental. Downstream consumers sometimes depend on it)
- trailing whitespace and fixed-width padding

Every entry in the normalization spec is a small assertion that a difference doesn't matter.
Each one is a place a real bug can hide. Keep the list short and have a human sign off on it.

## Cover the input space deliberately

Production replay covers the common path well and the dangerous paths badly. Add targeted
cases for:

- **boundary dates**: month end, quarter end, fiscal year end, leap day, DST transitions
- **the empty and the enormous**: zero-record batches, files at the maximum the old system
  could handle
- **the bad data that is already in there**: legacy systems accumulate records that violate
  their own rules. The new system must reproduce the legacy behavior on them, which is often
  neither an error nor a sane result.
- **the paths that only run at fiscal close**: the single most common source of a
  modernization failure discovered six months after cutover

## Where the oracle comes from in a mainframe shop

Look here before you accept that no oracle exists.

- **Archived generations.** GDG datasets keep prior runs of every report, extract and posting file.
  Each generation is a golden master with a date on it.
- **Job logs and SMF records.** They show which programs ran, with which return codes, and how long
  they took. They are also your telemetry for the dead-code register.
- **Extract files sent to partners.** Whatever left the building is already an executable
  specification of the format.
- **CICS journals and transaction logs.** They hold captured inputs for replay.
- **Report archives.** Statements, regulatory filings, and printed reports the business kept.

## Mainframe traps to put in the normalization spec

- **Packed decimal.** `COMP-3` and `COMP` fields round and truncate in ways IEEE floats do not.
  Compare in a decimal type with zero tolerance on money.
- **Collating sequence.** EBCDIC sorts letters and digits differently from ASCII. A KSDS returns
  records in key order, and downstream programs may depend on it. A port that sorts in ASCII
  changes the order silently.
- **`REDEFINES`.** Two layouts over the same bytes. Test every branch that reads either one.
- **Record padding and low values.** Fixed width records pad with spaces or binary zeros. Decide
  which differences matter and write it down.
- **Job order.** A step that reads a file another job writes is correct only in that order. The
  temporal edges in `graph.json` are the list of orders the harness must keep.

## Record the intentional differences

There will be behavior in the legacy system that is simply wrong, and that the client does
not want reproduced. Every one of these gets an entry in a **Deviation Register**:

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|

Nothing gets to differ without a row here. This register is the single most useful artifact
of the whole migration. It is what you hand the auditor, and it is what stops a defect from
being relitigated as a feature six months later.

## Define the exit bar per wave

A wave is done when:

- replay diff is clean, modulo the normalization spec and the deviation register
- every targeted boundary case passes
- the harness itself is under version control and runs in CI
- the deviation register is signed by someone with the authority to sign it

Not when the port compiles. Not when it passes the tests someone wrote alongside the port .
those tests encode the porter's understanding, which is the very thing under test.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the modernized system. Budget for
maintaining it. Teams routinely throw it away at cutover and lose the only executable
specification the system ever had.
