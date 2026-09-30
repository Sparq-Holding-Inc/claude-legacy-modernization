# 04 Estimate

Method: per wave, a range in person-days for one engineer who can read COBOL and CICS. The ranges are judgment, not measurement. There is no velocity data and no port history, so every figure below is inference. Size is not the driver. The two programs are 11 lines each. The cost is in the shared file, the test oracle, and the parts of the system the tree does not contain.

## Ranges

| Wave | Scope | Range (person-days) | Main cost drivers | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | PROGR, the ACCTREC decimal mapping, the KSDS access path, the test harness | 5 to 14 | Harness and oracle (2 to 6), KSDS access path from the new side (2 to 6), the mapping and the port itself (1 to 2). | low | `app/cbl/PROGR.cbl:7`, `app/cpy/ACCTREC.cpy:1-3`, inference |
| 2 | PROGW, write semantics, replay against a file copy, cutover of file ownership | 8 to 20 | Write semantics and unit of work (2 to 5), replay and cutover of ownership (4 to 10), the port itself (1 to 2). | low | `app/cbl/PROGW.cbl:7-11`, inference |
| Total | Waves 1 and 2 | 13 to 34 | The nightly batch cycle is not in the tree and is not in this estimate. | low | inference |

## The assumptions the range is most sensitive to

1. **Assumes the ACCTDAT KSDS can stay in place until wave 2, with the new side reading it directly.** If the file must be replicated to a new store with change capture between waves 1 and 2, wave 1 roughly doubles. Evidence: `app/csd/DEMO.CSD:1-3`, inference.
2. **Assumes no job or program outside this tree writes ACCTDAT.** If the nightly batch cycle writes it, wave 2 grows by the batch programs that write it, and the order between those jobs and TRNW has to be kept by the harness. Wave 2 could double or more. Evidence: analysis field `meta.files_seen`, inference.
3. **Assumes a snapshot of the KSDS and a record of real TRNR and TRNW requests are available.** If neither exists, the oracle is characterization tests from source only, which encodes what the code says, and the harness cost goes up by about 3 to 5 days per wave. Evidence: `app/cbl/PROGR.cbl:7-9`, inference.
4. **Assumes the key really is the first 11 bytes of the record, as the layout suggests.** If the VSAM cluster defines the key differently, each wave adds 1 to 2 days. The cluster definition is not in the tree. Evidence: `app/cpy/ACCTREC.cpy:2`, inference.

## What moves the estimate

| Factor | Where this system stands | Confidence | Evidence |
|---|---|---|---|
| Coupling edges crossing the wave boundary | One contract edge and one dataset. Small, but it is the whole system. | high | `app/cbl/PROGW.cbl:7`, `app/cbl/PROGR.cbl:7` |
| A behavioral oracle | None in the tree. No data files, no archived outputs, no logs. | high | analysis field `meta.files_seen` |
| God modules in the wave | None. | high | analysis field `god_modules` |
| Business logic in the database or in copybooks rather than code | The behavior sits in the file definition and the VSAM catalog (key, record length, share options), which are not in the tree. | low | `app/csd/DEMO.CSD:1-3`, inference |
| Anyone who can read the source language | Unknown. This is an open question in `00-summary.md`. | low | inference |

## Where Claude Code can do the port, and where it cannot

- **Can, with a harness:** transliterate the two programs, and turn ACCTREC into a decimal typed record with the same byte layout. The programs are straight line code. Evidence: `app/cbl/PROGR.cbl:6-11`, `app/cpy/ACCTREC.cpy:1-3`.
- **Cannot, from this source alone:** say where the key comes from, what a not found or duplicate key should do, or what the installed file attributes allow. None of it is in the code. It needs an engineer who knows the transactions. Evidence: `app/cbl/PROGR.cbl:4-10`, inference.
- **Cannot at all:** anything about the nightly batch cycle. Its source is not in the tree. Evidence: analysis field `meta.files_seen`.
