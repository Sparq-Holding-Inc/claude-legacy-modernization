# 00 Summary

Scope: the whole work folder (`.`). Files read: 3 COBOL programs, 1 copybook, 1 JCL job. Nothing was skipped (analysis: `unparsed` is empty). No git dates, no scheduler artifact, no cloc.

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | `--target refactor` |
| What must not break | the nightly batch cycle | `--must-not-break "the nightly batch cycle"` |
| Runtime telemetry | none | `--telemetry none` |

All three came as flags: **no defaults applied.** Nobody was asked anything.

Telemetry is `none`, so every dead-code claim in this assessment is provisional.

## Headline

- **Wave count: 1.** `job:MAINJOB`, `PGMMAIN` and `PGMLIVE` move together (`modernization-assessment/waves.json:2`). No cycle, no data hub, no god module, no deviation from the extractor's seed.
- **Dead code: 2 unreachable candidates, 0 dormant (not measured), 0 unknown.** `PGMDEAD` and `cpy:UNUSED`. PGMDEAD calls a live program, but nothing calls PGMDEAD, and deleting it leaves the live path whole (`app/cbl/PGMDEAD.cbl:4`, `app/cbl/PGMMAIN.cbl:4`).
- **Effort: 3.5 to 9 person-days, low confidence** (`04-estimate.md`). The harness is most of it, not the port.

## Largest risk

**The one thing that must not break, the nightly batch cycle, cannot be traced in this tree.** The only job is `job:MAINJOB`. No scheduler artifact was parsed. The tree has no dataset, no archived output and no telemetry (analysis: `warnings`). The programs hold no logic (`app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMLIVE.cbl:4`). So the port is easy, but nothing on file can prove the ported job is correct, and nothing shows that this job is the whole cycle. The job scores low-high in `modernization-assessment/risks.json:24`. The work is verification. That is inference.

## Findings

| Finding | Confidence | Evidence |
|---|---|---|
| One entry point, one linear chain: job, step S1, PGMMAIN, PGMLIVE | high | `app/jcl/MAINJOB.jcl:2` |
| PGMDEAD is unreachable and cpy:UNUSED is unreferenced | medium | `app/cbl/PGMDEAD.cbl:4` |
| PGMLIVE has fan-in 1 over reachable programs, and 2 raw callers | high | analysis: `fan_in` |
| No data, contract or temporal edge exists, which is a gap, not proof of independence | medium | analysis: `edge_counts` |
| Cross-job order is unknown | high | analysis: `warnings` |

## Open questions for the client's engineers

1. **Is `job:MAINJOB` the nightly batch cycle, or one job in it?** Where is the scheduler export (Control-M, CA-7, or a wrapper script) that defines the cycle, with its predecessors and successors? The tree has none (analysis: `warnings`). Without it the must-not-break item cannot be tied to units.
2. **Is this tree the whole system, or an extract?** PGMMAIN only calls PGMLIVE, and PGMLIVE only returns (`app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMLIVE.cbl:4`). Where is the business logic? Are there other JCL libraries, PROCs, CICS definitions or programs outside this folder?
3. **Can you supply 12 months of job history or SMF records** for `job:MAINJOB`, PGMMAIN, PGMLIVE and PGMDEAD? That turns the dead-code register from provisional into evidence, and it is also the first oracle for the harness.
4. **Does anything outside this tree run PGMDEAD or COPY `cpy:UNUSED`?** A submit from another job, an internal reader, or a scheduler entry would move PGMDEAD out of the unreachable bucket (`app/cbl/PGMDEAD.cbl:1`, `app/cpy/UNUSED.cpy:1`).
5. **What does the production `job:MAINJOB` read and write?** Its step has no DD statement (`app/jcl/MAINJOB.jcl:2`). Which datasets, GDGs, reports and partner extracts does the real job produce? These are the golden masters.
6. **Can you supply last-modified dates?** The tree is not under git, so the dormant bucket was not computed (analysis: `warnings`). Source-control history or member timestamps would let it be measured.
7. **Does the nightly cycle have `IF/THEN/ELSE` or `COND=` logic, restart points, or run different steps at month-end and year-end?** The extractor does not model them, and step order is taken as file order (`app/jcl/MAINJOB.jcl:2`).
8. **Who on the team can read COBOL and JCL, and can a parallel run of the legacy and ported job be scheduled on production input?** This decides the oracle for wave 1 and the harness cost (`06-test-strategy.md`).

## Not parsed

Nothing. The extractor listed no unparsed file (analysis: `unparsed` is empty).

## Extractor limits that touch this system

The extractor lists 12 limits (`meta.limits` in `graph.json`). These touch this system.

| Limit | How it touches this system | Confidence | Evidence |
|---|---|---|---|
| Only Control-M XML and shell wrappers that name JCL files are read as schedulers | No scheduler was parsed, so cross-job order and the nightly cycle are unknown | high | analysis: `warnings` |
| `IF/THEN/ELSE` and `COND=` in JCL are not modeled. Step order is file order | This job has neither, but the real cycle may | medium | `app/jcl/MAINJOB.jcl:2` |
| DCB, LRECL and RECFM are not read | The step has no DD, so no record length was compared with a layout | medium | `app/jcl/MAINJOB.jcl:2` |
| `EXEC CICS RETURN TRANSID`, `START` and `SEND MAP` are not edges | No CICS call appears in the tree. Online chains outside it are invisible | low | inference |
| A called subprogram gets no DDs from its caller's JCL step | PGMLIVE is called by PGMMAIN and has no file of its own | medium | `app/cbl/PGMMAIN.cbl:4` |
| A variable call target resolves only from VALUE clauses and literal MOVEs | Every call in the tree is a literal, so nothing was left to resolve | medium | `app/cbl/PGMMAIN.cbl:4` |

The rest (COPY REPLACING, IDCAMS and SORT control cards, nested PROC calls, JCL text inside a COBOL literal, the high-versus-proven contract note, LINK and XCTL as one edge kind) do not apply, since the tree has no COPY, no utility step, no PROC, no contract edge and no CICS.
