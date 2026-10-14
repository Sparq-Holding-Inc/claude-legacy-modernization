# 06 Test strategy

The tree holds no datasets (`02-coupling.md`), so the oracle has to come from job output, logs and reports. `MAINJOB` has no DD statements (`app/jcl/MAINJOB.jcl:2`), and the supplied programs produce no output (`app/cbl/PGMLIVE.cbl:4`). That is the main finding of this section: today the nightly batch cycle has nothing to compare.

## Oracle for wave 1

| Wave | Oracle | Why | Evidence |
|---|---|---|---|
| 1 | Golden master from archived job output, with a parallel run as the preferred target | Parallel run is cheapest for a single batch job. Fall back to archived SYSOUT and return codes. Characterization tests from source only as a provisional last resort. | `app/jcl/MAINJOB.jcl:1` |

## Ask the client to supply

- 12 months of job logs and return codes for `MAINJOB`, including month-end and year-end.
- Archived output (SYSOUT, GDG generations, reports) of each run.
- Whether a parallel run on the legacy system is possible.
- The real programs, if the supplied ones are stubs.

## Normalization spec (draft, needs human sign-off)

Timestamps, run IDs, job numbers and page numbers. No numeric tolerance is needed until money fields appear. Decimal types with zero tolerance when they do (COMP-3).

## Input coverage

Zero-record and maximum-size runs, boundary dates (month end, year end, leap day), and bad data already present. None of these are visible in the tree. They come from the archive.

## Exit bar

Replay diff clean modulo the normalization spec and the deviation register, boundary cases pass, harness in version control and CI, register signed. Keep the harness after cutover.

## Deviation register

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| none yet | | | | | | inference |
