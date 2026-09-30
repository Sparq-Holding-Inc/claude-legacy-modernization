# 00 Summary

Assessment of the tree in `.` (the work folder). It holds two CICS COBOL programs (PROGR, PROGW), one copybook (ACCTREC), and one CSD file (DEMO.CSD). It has no JCL, no procs, no scheduler definitions, and no batch programs.

## Scoping answers

| Question | Answer | Source | Evidence |
|---|---|---|---|
| Target state | refactor | flag `--target refactor` | inference (from the command arguments) |
| Must not break | "the nightly batch cycle" | flag `--must-not-break` | inference (from the command arguments) |
| Runtime telemetry | none | flag `--telemetry none` | inference (from the command arguments) |

All three came as flags: no defaults applied.

Telemetry is `none`, so every dead-code claim is provisional.

## Result

| Item | Finding | Confidence | Evidence |
|---|---|---|---|
| Waves | 2. Wave 1 is PROGR (read only). Wave 2 is PROGW (writes the shared file). No deviations from the seed. | medium | `modernization-assessment/waves.json:2` |
| Coupling | One KSDS, one writer, one reader, one shared layout copybook. No calls, no cycles, no god modules. | high | `app/cbl/PROGW.cbl:7`, `app/cbl/PROGR.cbl:7`, `app/cpy/ACCTREC.cpy:3` |
| Dead code | None found. Dormancy was not measured, because the tree has no git dates. | low | analysis field `warnings` |
| Estimate | 13 to 34 person-days for both waves, without the nightly batch cycle. | low | inference |
| Oracle | No files in the tree. Parallel run for wave 1, replay against a file copy for wave 2. | medium | inference |

## The single largest risk

The nightly batch cycle, the one thing the client says must not break, is not in the tree, and the only shared state that is in the tree is an account file (ACCTDAT KSDS) whose balance is a packed decimal field. A nightly cycle is exactly the kind of process that reads or updates an account master. If it does, then a port of PROGW that changes one byte of the record layout, the sign nibble, or the key order breaks the batch cycle silently, and nothing in the tree lets us test that. The assessment cannot rule this out and cannot measure it. Evidence: `app/cpy/ACCTREC.cpy:2-3`, `app/cbl/PROGW.cbl:7`, analysis field `meta.files_seen`, inference.

## Open Questions

Addressed to the client's own engineers.

1. **Where is the nightly batch cycle?** We need its JCL, procs, batch programs and scheduler definitions. Does any of it read or write `SPARQ.TEST.ACCTDAT.KSDS`, or a copy of it? The tree has none of these, so the data hub count of one writer and one reader is a lower bound. Evidence: analysis field `meta.files_seen`, `app/csd/DEMO.CSD:2`.
2. **Is this the production file?** The dataset name contains TEST. What is the production name, and does production use this CSD group (there is no `DEFINE LIST` here, so we cannot see whether group DEMO is installed)? Evidence: `app/csd/DEMO.CSD:1-9`.
3. **Where does the key come from?** Neither program sets `ACCT-ID`, and neither has a COMMAREA, a LINKAGE SECTION or a RECEIVE. Is the source shown complete, and is it the deployed version? Evidence: `app/cbl/PROGR.cbl:4-9`, `app/cbl/PROGW.cbl:4-9`.
4. **What should a missing or duplicate key do?** Neither EXEC CICS call has a RESP option or a HANDLE CONDITION. Does a region-level handler (a program error program, or a global exit) catch these, or does the task abend, and does any caller depend on that? Evidence: `app/cbl/PROGR.cbl:7-10`, `app/cbl/PROGW.cbl:7-10`.
5. **What does the VSAM cluster define, and what do the installed FILE attributes allow?** We need the key offset and length, the record size, share options and recovery attributes. The FILE definition sets no ADD, READ or UPDATE attribute, and PROGW uses WRITE. The extractor does not read DCB, LRECL or RECFM, so a record length is never compared with the copybook, which comes to 17 bytes by hand count. Evidence: `app/csd/DEMO.CSD:1-3`, `app/cpy/ACCTREC.cpy:1-3`, meta limit "DCB, LRECL and RECFM are not read".
6. **Which other transactions, programs or regions touch ACCTDAT?** Other CSD groups, other CICS regions, DB2 or MQ users would all be edges the extractor could not see. Evidence: `app/csd/DEMO.CSD:1`, inference.
7. **Do all existing balances hold valid packed decimal?** Records with a bad sign nibble or non-digit key byte behave in ways nobody planned, and a port has to reproduce them. Evidence: `app/cpy/ACCTREC.cpy:2-3`, inference.
8. **How many times did TRNR and TRNW run in the last 12 months?** Without it the dead-code register is provisional, and dormancy is not measured because the tree is not in git. Evidence: analysis field `warnings`.
9. **Which scheduler runs the nightly cycle?** The extractor reads only Control-M XML and shell wrappers that name JCL files. If the client uses CA-7, TWS or another scheduler, its definitions are outside anything this tool parses. Evidence: meta limit "Only Control-M XML and shell wrappers that name JCL files are read as schedulers".
10. **Is a shared layout a proven layout?** The contract edge from PROGW to PROGR is `high`, which means both COPY ACCTREC. It does not prove either program reads the record through a private layout. Confirm with the file's real users. Evidence: meta limit "A contract edge is high when both sides COPY the same layout", `app/cbl/PROGR.cbl:5`, `app/cbl/PROGW.cbl:5`.

Not parsed: the extractor listed nothing as not parsed. The tree holds no free format COBOL, no COPY REPLACING, no called subprograms and no JCL, so the extractor limits on those do not touch this system. Evidence: analysis field `unparsed`.

## Other artifacts

`01-inventory.md`, `02a-edge-tables.md`, `03a-wave-seed.md`, `03a-waves-draft.json` and `05a-dead-code-candidates.md` are generated by the scripts. `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md` and `06-test-strategy.md` are written by hand. The JSON outputs are `graph.json`, `waves.json`, `dead-code.json` and `risks.json`. The `dependency-cartographer` work was not needed, because the graph has no unresolved or medium or low confidence edge. The `migration-risk-assessor` work was done inline and wrote `risks.json`.
