# 06 Test strategy

The bar: for the inputs MAINJOB actually receives, the new dispatcher produces the same outputs and
return code as the old one, and every difference is written down on purpose. "It passes the tests"
is not the bar.

## The tree holds no datasets

The extractor found no dataset, VSAM file or DB2 table (`analysis`, field `data_hubs`, and no `ds:`
node in the graph). So the oracle cannot come from file layouts in the tree. It has to come from job
output, logs and reports. This is what to ask the client to supply:

| Ask | Why | Evidence |
|---|---|---|
| The SYSIN or the proc that feeds the ACCEPT, and 12 months of MAINJOB job logs | These are the replay inputs. The job defines no input itself. | `app/jcl/MAINJOB.jcl:2` |
| Return codes and run times per program name dispatched | Shows which programs ran. Doubles as the telemetry that settles HIDDEN01. | `app/cbl/PGMMAIN.cbl:9` |
| Archived SYSOUT, reports and GDG generations from the nightly cycle | Free golden masters with dates on them. | inference |
| The scheduler export for the nightly batch cycle | The order the cycle runs in is the must-not-break item and nothing in the tree records it. | `analysis` |
| The load library member list | It bounds what a CALL by name can reach. | `app/cbl/PGMMAIN.cbl:9` |

## Oracle per wave

| Wave | Preferred oracle | Fallback | Evidence |
|---|---|---|---|
| 1 | Parallel run: the old and the new dispatcher take the same production input on the same night, and the outputs of every dispatched program are diffed. | Replay of captured SYSIN values and archived outputs. Last: characterization tests from source, labeled provisional. | inference |

Ask first whether a parallel run is possible for the nightly cycle. Teams assume it is not and are
often wrong.

## Normalize before you diff

Agree these in writing and have a human sign them off. Each entry is a claim that a difference does
not matter.

- run dates, job numbers and timestamps in SYSOUT and log headers
- page numbers and run ids in any report the dispatched programs print
- trailing spaces: the target name is a fixed 8 character field (`app/cbl/PGMMAIN.cbl:5`), so a
  name shorter than 8 characters is padded, and the port must treat padded and trimmed names as one
- money fields: compare in a decimal type with zero tolerance. The tree holds no packed decimal or
  REDEFINES (the whole source is `app/cbl/PGMMAIN.cbl:1` to line 10 and `app/cbl/HIDDEN01.cbl:1` to
  line 4), but the dispatched programs are unknown, so this cannot be waived.
- record order and collating sequence: unknown until the dispatched programs and their files are known

## Cover the input space deliberately

- **Dispatch input cases.** A name of a program that exists. A blank name. A name with no member in
  the load library. CALL has no ON EXCEPTION clause (`app/cbl/PGMMAIN.cbl:9`), so a missing program
  abends the run. Decide whether the port reproduces the abend, and record the choice in the
  register.
- **HIDDEN01 as target.** Run the dispatcher with its name and assert a clean return
  (`app/cbl/HIDDEN01.cbl:4`).
- **Boundary dates.** Month end, quarter end, fiscal year end, leap day. The ACCEPT input may
  differ on those dates, so the capture window must include them. This is inference.
- **Empty input.** No SYSIN at all, which is what the job as written provides
  (`app/jcl/MAINJOB.jcl:2`).
- **The paths that run only at close.** Whatever program name arrives only at fiscal close is the
  most likely to be missing from a sample.

## Job order

The graph holds no temporal edge (`analysis`, field `edge_counts`) and no scheduler was parsed. The
order of the nightly cycle is therefore unknown, and it is the thing the client said must not break.
The harness has to keep whatever order the scheduler export shows.

## Deviation register

Every intentional difference gets a row. None yet.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|

## Exit bar for wave 1

- the replay diff is clean, modulo the normalization spec and the register
- every case above passes, including the missing program case
- the harness is under version control and runs in CI
- the register is signed by someone with the authority to sign it

Keep the harness after cutover. It becomes the regression suite for the new dispatcher.
