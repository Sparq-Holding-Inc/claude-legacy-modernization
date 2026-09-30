# 04 Estimate

**Method.** The ranges are in person-days for one engineer who can read COBOL and CICS, built from the coupling that crosses each wave boundary, not from lines of code. The tree has 22 lines of program code (`app/cbl/PROGR.cbl:1-11`, `app/cbl/PROGW.cbl:1-11`), and lines would say "trivial". No port velocity was measured, so every number is inference and should be replaced after wave 1.

| Wave | Range | Edges crossing the boundary | Main drivers | Evidence |
|---|---|---|---|---|
| 1. PROGR | 5 to 10 days | one read of the ACCTDAT file, one shared layout | the ACCTREC decoder, the harness, and how the new reader reaches the file | `app/cbl/PROGR.cbl:7`, `app/cpy/ACCTREC.cpy:2-3` |
| 2. PROGW | 8 to 20 days | one write of the ACCTDAT file, one shared layout | the harness for an irreversible write, the shadow run, the unknown use by batch | `app/cbl/PROGW.cbl:7`, `app/cpy/ACCTREC.cpy:3` |
| Both | 13 to 30 days | | | inference |

The total leaves out the nightly batch cycle, the move of the data itself, the choice and set up of the target runtime, and cutover. None of those can be estimated from this tree.

## What the ranges are most sensitive to

1. **Assumes the nightly batch cycle reads and writes the ACCTDAT file through the ACCTREC copybook.** If it uses layouts of its own, wave 2 roughly doubles, because each private layout needs its own comparison. The batch is not in the tree (`modernization-assessment/graph.json:30`).
2. **Assumes the ACCTDAT file stays where it is, and the new reader can read it, during waves 1 and 2.** If the data has to be copied or moved into a new store before wave 1 can run, wave 1 roughly doubles. The tree does not say how the file is stored or defined beyond its name (`app/csd/DEMO.CSD:1-2`).
3. **Assumes an oracle exists: a snapshot of the file or archived outputs.** If the only oracle is what the source says, wave 2 is provisional and its harness work roughly doubles. There is no data in the tree.

Other things that would move it: whether anyone on the team reads COBOL (unknown), and whether the file definition allows adds. The CSD FILE entry sets no attributes (`app/csd/DEMO.CSD:1-3`), and inference says the CICS default for adds is off. That is unverified.

## Where Claude Code helps and where it does not

- **Strong.** Transliterating both programs, and writing and testing the ACCTREC codec for the display key and the packed decimal balance, once a harness exists. Each program is one file operation and a return (`app/cbl/PROGR.cbl:7-11`, `app/cbl/PROGW.cbl:7-11`).
- **Weak.** Everything that is not in the source. Where the key and the record come from (`app/cbl/PROGR.cbl:9`, `app/cbl/PROGW.cbl:9`), what the transactions are for, what the batch cycle does with the file, and whether a NOTFND or a duplicate key is handled anywhere. No RESP or HANDLE CONDITION appears in either program (`app/cbl/PROGR.cbl:7-10`, `app/cbl/PROGW.cbl:7-10`). Those need the client's engineers.
