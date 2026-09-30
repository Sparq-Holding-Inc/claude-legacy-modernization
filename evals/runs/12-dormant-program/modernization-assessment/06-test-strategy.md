# 06 Test strategy

Skill used: `behavioral-equivalence`. The bar is not that the port compiles or passes tests written
beside it. The bar is that the new job produces the same output as the old one on the inputs the system
really sees, and that any difference is recorded on purpose.

## The oracle problem in this tree

The tree holds no dataset, no copybook and no DD statement (`app/jcl/MAINJOB.jcl:2`, analysis field
`data_hubs`). Two of the three programs do nothing but `GOBACK` (`app/cbl/OLDPGM.cbl:4`,
`app/cbl/NEWPGM.cbl:4`). So no oracle can be built from the source. It has to come from job output, job
logs and reports the client holds. What to ask the client to supply:

1. The JES job log and SYSOUT for `MAINJOB`, at least 12 months of runs, with return codes. They show
   each run and the step return code, and they are the telemetry that firms up the dead-code register.
2. SMF or job accounting records showing whether `OLDPGM` and `NEWPGM` were loaded and ran.
3. The full production JCL, with its DD statements, and the input and output datasets of `MAINJOB`. The
   JCL in the tree has none (`app/jcl/MAINJOB.jcl:2`).
4. Archived generations (GDG) of every report, extract and posting file the job writes. Each generation
   is a dated golden master.
5. Whatever the cycle sends to partners or downstream systems (extracts, feeds, printed reports).
6. The scheduler export that runs `MAINJOB`. It shows its predecessors and successors.

## Oracle for wave 1

| Wave | Oracle, strongest first | Provisional? | Evidence |
|---|---|---|---|
| 1 | Parallel run of legacy and new `MAINJOB` on the same production inputs over a window that includes a month-end. The legacy job can stay up, and the tree shows no reason it cannot. | No | inference |
| 1 | Fallback: replay captured production input, then golden master from archived outputs. | No, if the window covers month-end and, for anything financial, year-end | inference |
| 1 | Last resort: characterization tests from source. Here they would assert that `PGMMAIN` calls `OLDPGM` then `NEWPGM` and returns, which says almost nothing. | Yes | `app/cbl/PGMMAIN.cbl:4-5` |

## Normalization spec (each line is an assertion that a difference does not matter, needs human sign-off)

| Item | Rule | Evidence |
|---|---|---|
| Timestamps, run and job numbers, page numbers | Masked before the diff | inference |
| Monetary and packed-decimal fields | Compare in a decimal type with zero tolerance. None are visible in this tree, but `OLDPGM` and `NEWPGM` may hold arithmetic elsewhere. | inference |
| Record order | Treat as significant until a consumer is shown not to depend on it. Sorting in ASCII changes the order EBCDIC gives. | inference |
| Padding, low values, trailing blanks | Decide per output file once the layouts are known | inference |
| Step order | Keep `OLDPGM` before `NEWPGM`. This is the only ordering in the tree. | `app/cbl/PGMMAIN.cbl:4-5` |
| REDEFINES | Test both branches of any redefined record once layouts are supplied. None are in the tree. | inference |

## Input space to add on top of replay

- Month-end, quarter-end, fiscal year-end, leap day and daylight-saving change nights. Anything that
  runs only at close is the classic failure found six months after cutover. The tree shows no
  conditional path, so this cannot be located from the source. Ask the client.
- A zero-record run and the largest run the job has ever handled.
- The bad data already in the client's files. The new job must reproduce the legacy behavior on it.
- `OLDPGM` in isolation. Capture a run where it was called and record its side effects, so a decision to
  retire it rests on evidence and not on the 2011 date (`app/cbl/OLDPGM.cbl:1`).

## Deviation register

Nothing may differ without a row. One row is already open, because the tree raises a real question.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-1 (open, undecided) | `PGMMAIN` calls `OLDPGM` and then `NEWPGM` on every run | Not decided. Keep both, or retire `OLDPGM`. | Only if the client confirms `NEWPGM` replaced it | Not yet | Unknown. Needs the job output that `OLDPGM` affects | `app/cbl/PGMMAIN.cbl:4` |

## Exit bar for wave 1

- The replay or parallel diff is clean, modulo the normalization spec and the deviation register.
- Every boundary case above passes.
- The harness is under version control and runs in CI.
- The deviation register is signed by someone with authority, including the `OLDPGM` decision.

## After cutover

Keep the harness. It is the only executable specification this job has. Budget to maintain it.
