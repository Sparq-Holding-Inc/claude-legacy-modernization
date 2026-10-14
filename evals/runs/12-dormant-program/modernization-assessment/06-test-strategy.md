# Test strategy

The tree holds no datasets, no copybooks and no reports (meta.files_seen). The oracle therefore has to come from
job output, logs and reports the client supplies.

Must-not-break: "the nightly batch cycle". The tree has one job, `job:MAINJOB` (app/jcl/MAINJOB.jcl:1). The
mapping of the cycle to this job is inference. Confirm it.

## Oracle for wave 1

| Choice | Detail | Evidence |
|---|---|---|
| Preferred | Parallel run of legacy and ported `MAINJOB` on the same nightly inputs, outputs diffed. Ask first whether it is possible. | inference |
| Fallback 1 | Replay captured inputs and outputs across a full cycle that includes month-end and fiscal year-end. | inference |
| Fallback 2 | Golden master from archived job output, GDG generations, SMF and job logs, partner extracts. | inference |
| Last resort | Characterization tests from source. The source is empty of logic (app/cbl/PGMMAIN.cbl:4), so these would prove only that the CALLs happen. Provisional. | app/cbl/PGMMAIN.cbl:4 |

## What the client must supply

- Job output for `MAINJOB` over at least one full business cycle, with return codes.
- The scheduler export that places `MAINJOB` in the nightly order.
- Whatever `MAINJOB` writes or reads. The JCL names no DD (app/jcl/MAINJOB.jcl:2), so any file effect is hidden.

## Normalization spec (draft, needs human sign-off)

- Timestamps, run ids and job numbers.
- Page numbers and headers in printed output.
- Decimal fields compared in a decimal type with zero tolerance on money.
- Record order only where the legacy order was incidental. Confirm that.
- Fixed-width padding. Decide spaces vs low values.

## Targeted cases

- Month-end, quarter-end and fiscal year-end runs.
- A zero-record run and the largest run seen.
- Existing bad data in the inputs.
- Return code and abend behavior of `PGMMAIN`, `OLDPGM` and `NEWPGM`.
- `OLDPGM` is dormant by date but called unconditionally (app/cbl/PGMMAIN.cbl:4). Add a case that proves it runs
  and what it does.

## Deviation Register

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| none yet | | | | | | inference |

## Exit bar for wave 1

Replay diff clean modulo the normalization spec and the register, boundary cases passing, harness in version
control and in CI, and the register signed. Keep the harness after cutover.

## Rollback

Run the legacy `MAINJOB` again. The ported job is behind a flag at the job level (inference).
