# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | `--target refactor` |
| What must not break | the nightly batch cycle | `--must-not-break` |
| Runtime telemetry | none | `--telemetry none` |

All three came as flags: no defaults applied. Nobody was asked anything.

Telemetry is `none`, so every dead-code claim in this assessment is provisional (`05-dead-code.md`).

## What was assessed

Four COBOL programs, PROGA to PROGD, 38 lines in all, all using EXEC CICS. No copybook, dataset, JCL, PROC, CSD, scheduler or shell file is in the tree (`01-inventory.md`). The extractor skipped nothing.

## Wave count

**0 waves.** No entry point exists in the tree: no CSD transaction, no JCL job, no scheduler job (analysis: `entry_points`, empty). The extractor could not seed a wave and I did not invent one. All four programs are in `unassigned` in `modernization-assessment/waves.json`. Nothing can be sequenced until the client supplies JCL, a CSD or a scheduler export.

## Single largest risk

PROGA links to a program chosen at run time by its caller. It moves its COMMAREA into a variable and uses it as the LINK target (`app/cbl/PROGA.cbl:15`, `app/cbl/PROGA.cbl:16`). Nothing in the tree sets that value, so the set of programs PROGA can reach cannot be bounded from the source. Until someone captures the values, PROGB, PROGC and PROGD cannot be called unreachable, a port cannot fix its dispatch list, and a facade would have to accept any name. PROGA is scored high-high for that reason (`risks.json`).

## What else the source shows

| Finding | Confidence | Evidence |
|---|---|---|
| The XCTL to PROGC at line 20 is unconditional and never returns. The XCTL to PROGD at line 23 and the RETURN at line 26 follow it, so on the normal path they do not run. The graph shows PROGA to PROGD as a high confidence edge, but it is very likely never executed. | medium | `app/cbl/PROGA.cbl:20`, `app/cbl/PROGA.cbl:23`, `app/cbl/PROGA.cbl:26` |
| The extractor lists the XCTL at line 20 both as a medium confidence call to PROGC and as an unresolved computed call. The source shows one statement, and PROGC is the only value WS-NEXT-PGM can hold. | medium | `app/cbl/PROGA.cbl:19`, `app/cbl/PROGA.cbl:20` |
| PROGB, PROGC and PROGD each contain only a RETURN. They may be stubs. | medium | `app/cbl/PROGB.cbl:4`, `app/cbl/PROGC.cbl:4`, `app/cbl/PROGD.cbl:4` |
| The nightly batch cycle maps to no unit in this tree. | high | analysis: `entry_points` empty, `meta.files_seen` shows no JCL, scheduler or CSD |

## Files in this assessment

The write-ups are `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md` and `06-test-strategy.md`. The generated fact tables are `01-inventory.md`, `02a-edge-tables.md`, `03a-wave-seed.md`, `03a-waves-draft.json`, `05a-dead-code-candidates.md`. The data files are `graph.json`, `waves.json`, `dead-code.json` and `risks.json`.

## Not parsed, and limits that touch this system

- **Not parsed:** nothing. All four files were read (`graph.json`, `unparsed`, empty).
- **Dormant not computed.** The tree is not a git repository, so there are no last-modified dates (analysis: `warnings`).
- **No CSD, JCL or scheduler was read.** The extractor reads only COBOL here (`meta.files_seen`). Every entry-point and wave result follows from that.
- **A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program** (`meta.limits`). That is why the COMMAREA-fed LINK is unresolved.
- **LINK and XCTL are both call edges and control flow is not modeled** (`meta.limits`). That is why the dead XCTL at line 23 shows as a high confidence edge.
- **`EXEC CICS RETURN TRANSID`, `START` and `SEND MAP` are not edges** (`meta.limits`). None appears in these four files.
- **A called subprogram gets no DDs from its caller's JCL step** (`meta.limits`). No DD exists in the tree, so this has no effect yet.

## Open Questions

For the client's own engineers.

1. **Where is the nightly batch cycle?** You named it as the thing that must not break. This tree holds no JCL, no scheduler definition, no batch program and no dataset, and all four programs use EXEC CICS (`app/cbl/PROGA.cbl:12`). It maps to no unit here and I have not mapped it to one. Send the JCL, PROCs, the scheduler export (Control-M, CA-7 or other) and the GDG bases for that cycle.
2. **Which transactions start PROGA, and who calls it?** Nothing in the tree calls PROGA (`app/cbl/PROGA.cbl:1`). Send the CSD or RDO listing, or the transaction-to-program table. Without it there is no entry point, so no wave and no reachability.
3. **What program names reach PROGA's COMMAREA?** PROGA links to whatever it holds (`app/cbl/PROGA.cbl:15`, `app/cbl/PROGA.cbl:16`). Give the full list of values production passes, or a year of captured COMMAREAs. Say what should happen when the COMMAREA is empty or shorter than eight bytes, since PROGA checks neither.
4. **Is the code after the XCTL at line 20 meant to run?** The XCTL to PROGD at line 23 and the RETURN at line 26 come after an unconditional transfer (`app/cbl/PROGA.cbl:20`, `app/cbl/PROGA.cbl:23`). Is that a leftover, a fall-back if PROGC is missing, or a bug? Is there any HANDLE CONDITION or RESP handling outside these files?
5. **Are PROGB, PROGC and PROGD stubs?** Each is a single RETURN (`app/cbl/PROGB.cbl:4`, `app/cbl/PROGC.cbl:4`, `app/cbl/PROGD.cbl:4`). Is the real source in another library, in another language such as Assembler or PL/I, or only as a load module?
6. **Can you tell us which of these programs ran in the last twelve months?** CICS monitoring, SMF 110 records or statistics would do. Telemetry is `none`, so the dead-code register is provisional, and PROGD in particular needs a measured answer.
7. **When was each program last changed?** The tree has no version history, so the dormant bucket was not computed. Send the change dates from the source manager.
8. **Is this the whole system or a fragment?** Four programs and 38 lines is unlikely to be a system. If more exists, send it before anyone reads this assessment as a plan.
