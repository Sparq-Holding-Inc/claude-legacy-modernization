# 03 Waves

Target state: refactor (given as a flag). The plan is in `modernization-assessment/waves.json`. It has two waves and no deviations from the extractor's seed (`03a-wave-seed.md`). A plan with no deviations is a fine answer for a tree this small.

## The plan

| Wave | Family | Units | Name | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | online-readonly | PROGR | Account file read transaction (TRNR) | low | medium | `app/csd/DEMO.CSD:6-7` |
| 2 | online-writers | PROGW | Account file write transaction (TRNW) | high | low | `app/cbl/PROGW.cbl:7` |

The copybook `cpy:ACCTREC` and the dataset `ds:SPARQ.TEST.ACCTDAT.KSDS` move with their owners and are not listed as units. The copybook belongs to wave 1, the first program that uses it. The dataset moves at wave 2, when its writer moves. Every unit is placed. Nothing is unassigned.

## Why each wave holds up against the four tests

| Test | Wave 1 (PROGR) | Wave 2 (PROGW) | Confidence | Evidence |
|---|---|---|---|---|
| Deploys independently, behind a flag or facade | Yes. Route transaction TRNR to the new program. The file stays in place. | Yes, with more care. Route TRNW to the new program only after a copy of the file has been replayed. | medium | `app/csd/DEMO.CSD:4-7`, inference |
| Rolls back independently | Yes. It writes nothing, so there is no data to repair. | Partly. The programs write records that cannot be undone from the code. Roll back means route back and restore or reconcile the file. | medium | `app/cbl/PROGR.cbl:7`, `app/cbl/PROGW.cbl:7` |
| Has a testable boundary | Yes. The bytes and response code that come back from a READ of a known key. | Yes. The file contents and response code after a WRITE of a known record. | medium | `app/cpy/ACCTREC.cpy:1-3`, inference |
| Delivers something a stakeholder can name | Weak. The program never uses the record it reads. This wave is mostly a chore that proves the toolchain. | Moderate. It moves ownership of the account file. | low | `app/cbl/PROGR.cbl:7-11`, inference |

## What each wave unblocks

Wave 1 unblocks the decimal mapping for ACCTREC and the access path to the KSDS. Both are reused by wave 2. Nothing a stakeholder can name. It is a chore.

Wave 2 unblocks moving ownership of ACCTDAT. Once the writer has moved, the file no longer has to be shared across the legacy and new sides, and the KSDS can be retired.

## Where the plan is fragile

1. **The wave boundary is a shared file, and the reader moves first.** The contract edge from PROGW to PROGR has high confidence, so the layout is shared. Between waves 1 and 2 the new PROGR reads a file the legacy PROGW writes. The plan holds only if the file stays readable in place until wave 2 (for a refactor, the new side reads the VSAM file through CICS or a replica with change capture). Evidence: `app/cbl/PROGW.cbl:7`, `app/cbl/PROGR.cbl:7`.
2. **The client's must-not-break item is not in the tree.** The nightly batch cycle has no JCL, proc, scheduler or batch program in this tree, so no unit can be tied to it and no deviation can be justified from it. If the cycle reads or writes ACCTDAT, it joins wave 2 at least (a writer) or wave 1 (a reader), and the plan changes. That is why wave 2 is `low` confidence. Evidence: analysis field `meta.files_seen`, inference.
3. **Two waves for 22 lines of code is a cost trade.** The contract edge crosses the wave boundary. If the client prefers to move both programs and the file in one release, that is a coherent choice. It is not recorded as a deviation, because nothing in a dependency, a strongly connected component or a must-not-break item forces it. Evidence: inference.

## Deviations

None. No must-not-break item can be cited, there is no strongly connected component, no facade dependency, no wave over 25 units, no computed call, and `risks.json` puts no unit in high-high. Evidence: analysis fields `sccs` and `unresolved_dynamic`, `modernization-assessment/risks.json:13`, `modernization-assessment/risks.json:38`.

## Risk quadrants

| Unit | Port difficulty | Blast radius | Quadrant | Wave | Confidence | Evidence |
|---|---|---|---|---|---|---|
| PROGR | 2 | 2 | low-low | 1 | medium | `app/cbl/PROGR.cbl:7` |
| PROGW | 2 | 4 | low-high | 2 | medium | `app/cbl/PROGW.cbl:7` |

PROGW is low-high. The port is easy, and the verification is the work. It goes second, and only once the harness in `06-test-strategy.md` is proven on PROGR.
