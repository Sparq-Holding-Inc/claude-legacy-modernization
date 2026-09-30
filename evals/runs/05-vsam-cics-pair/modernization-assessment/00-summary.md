# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Scope | `.` (the work folder) | argument default |
| Target state | refactor | `--target refactor` |
| Must not break | "the nightly batch cycle" | `--must-not-break` |
| Telemetry | none, so every dead-code claim is provisional | `--telemetry none` |

All three answers came as flags, so **no defaults applied**. This was a non-interactive run and no question was asked.

## What was found

The tree is two CICS programs, one copybook and one CSD file. The extractor read 4 nodes and 5 edges and skipped nothing (`modernization-assessment/graph.json:169`). PROGW writes the account balance file and PROGR reads it, and both use the layout copybook ACCTREC (`app/cbl/PROGW.cbl:7`, `app/cbl/PROGR.cbl:7`, `app/cbl/PROGR.cbl:5`). The CSD maps the file to SPARQ.TEST.ACCTDAT.KSDS (`app/csd/DEMO.CSD:2`). The record is an 11 digit key and a packed decimal balance (`app/cpy/ACCTREC.cpy:2-3`).

- **Waves: 2.** Wave 1 is the read transaction TRNR (PROGR). Wave 2 is the write transaction TRNW (PROGW). No deviations from the seed (`modernization-assessment/waves.json:2`). See `03-waves.md`.
- **Estimate.** 13 to 30 person-days for the two waves, not counting the batch cycle, the data move or the target runtime. Inference, see `04-estimate.md`.
- **Dead code.** None found in any bucket. The dormant bucket was not measured because the tree has no dates, and with no telemetry all of it is provisional (`modernization-assessment/graph.json:260`). See `05-dead-code.md`.
- **Test strategy.** See `06-test-strategy.md`.

## The single largest risk

The item that must not break, the nightly batch cycle, maps to no unit in the tree. No JCL, scheduler or batch program was seen (`modernization-assessment/graph.json:30`). Meanwhile PROGW writes the account balance file, a system of record, and a write cannot be undone by rerouting the transaction (`app/cbl/PROGW.cbl:7`). If the batch reads or writes that file through a layout other than ACCTREC, a port breaks it silently. This is inference, and it is why wave 2 has low confidence. No unit is mapped to the must-not-break item and none was invented.

## Extractor limits that touch this system

- A `high` contract edge means shared layout, not proven equal (`modernization-assessment/graph.json:21`).
- Record length is not compared with the copybook, and no file definition is in the tree (`modernization-assessment/graph.json:20`).
- Only Control-M XML and shell wrappers are read as schedulers. A scheduler in another product would not be read (`modernization-assessment/graph.json:19`).
- RETURN TRANSID, START and SEND MAP are not edges, so a transaction chain from a program outside the tree would not show (`modernization-assessment/graph.json:18`).
- Dormancy was not computed (`modernization-assessment/graph.json:260`).

## Open Questions

For the client's engineers. Nothing was in the tree for the first, so we did not guess.

1. **Where is the nightly batch cycle?** Send its JCL, PROCs, scheduler export and programs. Does it read or write the ACCTDAT file, and through which layout? The tree has none of it (`modernization-assessment/graph.json:30`). Nothing about batch can be sequenced until it arrives.
2. **Is this the production definition?** The file's dataset name contains TEST and the group is DEMO (`app/csd/DEMO.CSD:1-2`). What is the production dataset, and is this group installed there?
3. **Where do the key and the record come from?** Neither program moves a value into ACCT-ID or ACCT-REC before its file call (`app/cbl/PROGR.cbl:6-11`, `app/cbl/PROGW.cbl:6-11`). Is the source a stub, or is a front-end program, map or COMMAREA missing? No BMS map was seen (`modernization-assessment/graph.json:25`).
4. **What are the key and record length of the file?** Send the IDCAMS DEFINE CLUSTER or the catalog entry. We computed 17 bytes from the layout, which is inference (`app/cpy/ACCTREC.cpy:2-3`).
5. **Does the file definition allow adds?** The FILE entry sets no attributes (`app/csd/DEMO.CSD:1-3`). Inference says the CICS default for adds is off, which would make PROGW's write fail. Check the installed definition.
6. **Which of TRNR and TRNW ran in the last 12 months?** Send SMF or CICS statistics. Without them nothing here can leave provisional (`05-dead-code.md`).
7. **What happens on a missing key or a duplicate key?** Neither program tests a response (`app/cbl/PROGR.cbl:7-10`, `app/cbl/PROGW.cbl:7-10`). What does the old system do in production?
8. **What oracle exists?** Journals, unloads of the file, and archived batch outputs, per `06-test-strategy.md`. Can the old system stay up for a parallel run?
9. **Who on the team reads COBOL and CICS, and what is the target runtime for the refactor?** Neither is in the tree or the arguments.

Files the extractor listed as not parsed: none (`modernization-assessment/graph.json:169`).

## Files written

`graph.json`, `01-inventory.md`, `02a-edge-tables.md`, `02-coupling.md`, `03a-wave-seed.md`, `03a-waves-draft.json`, `03-waves.md`, `waves.json`, `04-estimate.md`, `05a-dead-code-candidates.md`, `05-dead-code.md`, `dead-code.json`, `risks.json`, `06-test-strategy.md`.
