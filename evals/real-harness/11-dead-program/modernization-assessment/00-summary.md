# 00. Summary

## Scoping

All three scoping answers were supplied as flags on `/modernize-scan`. **No defaults applied.**

| Question | Answer | Source |
|---|---|---|
| Target state | **refactor** — same behaviour, restructured code | `--target refactor` |
| What must not break | **the nightly batch cycle** | `--must-not-break "the nightly batch cycle"` |
| Runtime telemetry | **none** — the client cannot say which programs ran in the last 12 months | `--telemetry none` |

Scope: the current directory. Five files: three COBOL programs, one copybook, one JCL job
(`meta.files_seen`). Seventeen lines of COBOL and copybook plus a two-line job.

## The system, in one table

| Unit | Type | LOC | Reachable? | Wave | Evidence | Confidence |
|---|---|---|---|---|---|---|
| `job:MAINJOB` | JCL job, the only entry point | 2 | entry point | 1 | `app/jcl/MAINJOB.jcl:1` | high |
| `PGMMAIN` | batch program, calls `PGMLIVE` and GOBACKs | 5 | yes | 1 | `app/cbl/PGMMAIN.cbl:4` | high |
| `PGMLIVE` | subprogram, body is `GOBACK` | 4 | yes | 1 | `app/cbl/PGMLIVE.cbl:4` | high |
| `PGMDEAD` | batch program, identical to `PGMMAIN`, nothing runs it | 5 | **no** | not placed | `app/cbl/PGMDEAD.cbl:2` | high |
| `cpy:UNUSED` | copybook, `PIC X(10)`, nothing includes it | 1 | **no** | n/a | `app/cpy/UNUSED.cpy:1` | high |

Four edges, three `call` and one `include` (`analysis.edge_counts`). **No data edges, no contract
edges, no temporal edges, no datasets, no computed calls, no SCCs, no god modules, no articulation
points** (`analysis`).

## Wave count

**One.** `03-waves.md` and `waves.json`. Every reachable unit is in it, because every reachable
unit is on the same two-link call chain. No deviations from the machine-cut seed
(`modernization-assessment/waves.json:39`).

Wave 1 satisfies three of the four validity tests — independently deployable, independently
rollbackable, testable at a boundary — and fails the fourth: it delivers nothing a business
stakeholder can name, because porting two no-op programs achieves nothing anyone will notice
(`app/cbl/PGMLIVE.cbl:4`). By the skill's own test it is a chore. Run it as a toolchain
rehearsal, budget it as tooling, and do not report it as migration progress.

Estimate: **1.5 to 4 engineer-weeks**, of which roughly two thirds is toolchain setup any first
wave would pay once (`04-estimate.md`).

## The single largest risk

**The tree almost certainly is not the system.** The client named "the nightly batch cycle" as the
thing that must not break. What was supplied is one JCL job with one step
(`app/jcl/MAINJOB.jcl:1-2`) invoking a program whose entire procedure division is a CALL and a
GOBACK (`app/cbl/PGMMAIN.cbl:4-5`), which calls a program whose entire procedure division is a
GOBACK (`app/cbl/PGMLIVE.cbl:4`). No program opens a file. No scheduler artifact exists to say
anything runs nightly (`analysis.warnings`). A batch *cycle* is a sequence of jobs that move data;
this is one job that moves nothing.

Everything in this assessment is therefore correct about the five files on disk and unlikely to be
useful about the client's nightly batch cycle. The gap is in the inputs, not in the analysis. The
single highest-value action is not to start wave 1; it is to establish what the nightly cycle
actually consists of and re-run the assessment against it.

The second-order risk this creates is specific and worth naming: an assessment that looks complete
— one wave, no deviations, high-confidence dead code, a clean estimate — is easy to mistake for an
assessment of the real system. It is not one.

## Dead code

Telemetry is **none**, so every claim is provisional
(`modernization-assessment/dead-code.json:2`). With that said, this is an unusually strong static
result: there are no computed calls, no JCL embedded in COBOL literals, no programs named at run
time, and no file the extractor failed to parse (`analysis`). Within the supplied tree the
reachability answer is complete, not merely best-available.

| Bucket | Items | Evidence | Confidence |
|---|---|---|---|
| Unreachable — propose for deletion | `PGMDEAD`, `cpy:UNUSED` | `app/cbl/PGMDEAD.cbl:2`, `app/cpy/UNUSED.cpy:1` | high within scope |
| Reachable but dormant | none — **not measured** | `analysis.warnings` | n/a |
| Unknown | none, and genuinely so | `analysis` | high |

The dormant list is empty because dormancy was never computed: the target is not a git repository
and every node carries `last_modified: null` (`analysis.warnings`). Do not read the empty list as
"nothing is stale."

Note for sequencing: `PGMDEAD` contains a second `CALL 'PGMLIVE'` (`app/cbl/PGMDEAD.cbl:4`).
Resolve it before wave 1 touches `PGMLIVE`, so a developer grepping for callers finds one call
site and not two.

## Test strategy

`06-test-strategy.md`. The oracle cannot come from data because there is no data. It comes from
condition codes, SYSOUT and SMF records, captured by parallel-running the job on both platforms —
which is cheap here precisely because the job has no side effects. The normalization spec is seven
lines and deliberately contains none of the packed-decimal, EBCDIC-collation or `REDEFINES` rules
that a real mainframe port needs, because none of those constructs exists in the tree
(`app/cbl/PGMMAIN.cbl:3`). That spec is not reusable for the real system.

## Open Questions

For the client's engineers. Ordered by how much the answer would change this assessment.

1. **Is this the whole system?** The extractor parsed 3 COBOL files, 1 copybook, 1 JCL job, 0
   procs, 0 CICS CSDs, 0 Control-M definitions, 0 shell wrappers (`meta.files_seen`). If the
   nightly batch cycle is larger than one job, what was supplied is a fragment and every artifact
   here is scoped to the fragment. Evidence: `app/jcl/MAINJOB.jcl:1`.
2. **What is "the nightly batch cycle"?** No scheduler artifact was parsed, so nothing in the tree
   says any job runs nightly, nor what runs before or after it
   (`analysis.warnings`). Supply the Control-M or equivalent export. Until then the
   must-not-break item maps to `job:MAINJOB` only by assumption, and that assumption is in
   `03-waves.md` as the reason wave 1's confidence is medium rather than high.
3. **Were the production load modules compiled from these exact sources?** `PGMLIVE`'s procedure
   division is a single `GOBACK` (`app/cbl/PGMLIVE.cbl:4`). If the running load module does more
   than that, these files are stubs and the port would transliterate the wrong thing.
4. **Does anything outside these five files run `PGMDEAD`?** Static analysis says nothing in the
   tree does, and there is no dynamic dispatch to hide behind (`analysis.unresolved_dynamic` is
   empty). But a job in a library not supplied, or an operator submitting it by hand, would be
   invisible. Search the full JCL and scheduler libraries for the string `PGMDEAD` before
   deleting. Evidence: `app/cbl/PGMDEAD.cbl:2`.
5. **Does anything outside these five files `COPY UNUSED`?** Same question for the copybook. No
   program in the tree has a DATA DIVISION at all, so there is no COPY statement anywhere here
   (`app/cpy/UNUSED.cpy:1`, `app/cbl/PGMMAIN.cbl:3`).
6. **Can the tree be supplied as a git repository, or with dataset last-referenced dates?** The
   dormancy rule was configured for 5 years as of 2026-09-30 and had no dates to apply itself to
   (`analysis.as_of`, `analysis.dormant_years`; `meta.git_dates` is `false`). Without dates there
   is no dormant bucket, only an empty one.
7. **Can SMF type 30 records be supplied for the last 30 days?** This is the cheapest route from
   `--telemetry none` to real telemetry. It would move the dead-code claims from provisional to
   evidenced and supply the elapsed-time ceiling the test strategy needs
   (`06-test-strategy.md`). Evidence: `app/jcl/MAINJOB.jcl:1`.
8. **Is `MAINJOB` still submitted at all?** It is treated as an entry point because it is a JCL
   job (`app/jcl/MAINJOB.jcl:1`), not because any scheduler was found naming it.
   `analysis.unscheduled_jobs` is empty, but that is because no scheduler was parsed to compare
   against, not because a scheduler confirmed it.
9. **Which target runtime?** Nothing in this code constrains the choice, so the platform decision
   dominates the estimate — it is 3 to 10 of the 6.25 to 19.5 engineer-days in `04-estimate.md`.

## Extractor limits that touch this system

From `meta.limits`. Most of the listed limits are inert here because the constructs they concern
do not appear. These three are live:

| Limit | Why it matters here | Confidence |
|---|---|---|
| "IF/THEN/ELSE and COND= in JCL are not modeled. Step order is file order." | Only one step exists (`app/jcl/MAINJOB.jcl:2`), so no order is at stake — but if the real cycle has conditional steps, the wave families are computed from an unconditional reading. | high |
| "Only Control-M XML and shell wrappers that name JCL files are read as schedulers." | If the client's scheduler is CA-7, TWS/OPC, Zeke or anything else, it would not have been parsed and would show as the "no scheduler artifact" warning seen here. The warning may mean *unsupported format*, not *absent*. | medium |
| "A called subprogram gets no DDs from its caller's JCL step." | `PGMLIVE` is called by `PGMMAIN` (`app/cbl/PGMMAIN.cbl:4`) and the step has no DDs to inherit anyway (`app/jcl/MAINJOB.jcl:2`), so this is inert today — but it is the limit that would bite first if DDs were added. | high |

No file was listed as not parsed (`unparsed` is empty), so there is no unread-file question to add
to Open Questions.

## Artifacts

| File | Contents |
|---|---|
| `01-inventory.md` | Generated inventory |
| `02-coupling.md` | Coupling argument |
| `02a-edge-tables.md` | Generated edge tables |
| `03-waves.md`, `waves.json` | Wave plan |
| `03a-wave-seed.md`, `03a-waves-draft.json` | Machine-cut seed |
| `04-estimate.md` | Estimate and assumptions |
| `05-dead-code.md`, `dead-code.json` | Dead-code register |
| `05a-dead-code-candidates.md` | Generated candidates |
| `06-test-strategy.md` | Behavioral equivalence |
| `risks.json` | Port difficulty and blast radius |
| `graph.json` | Facts |
