# 04 Estimate

**Basis: engineer-weeks, shown for two delivery cases side by side, conventional (no AI coding help) and AI-assisted (engineers using an AI coding agent, with human review).** `--delivery` was not given, so both are quoted and neither is the headline. This plugin carries no calibrated productivity data. Every rate below is a planning assumption, not a benchmark. Replace them with the team's measured velocity after wave 2.

## Per wave

Understanding the code is not charged. This assessment did it. What remains is the client's answers (`00-summary.md`).

| Wave | Program LOC | Conventional (weeks) | AI-assisted (weeks) | Confidence | Evidence |
|---|---|---|---|---|---|
| 1. Setup and utility jobs | 0 (JCL only) | 3 to 5 | 2 to 3 | medium | inference |
| 2. Read-only batch | 1,084 | 6 to 10 | 4 to 6 | medium | inference |
| 3. Sign-on, menus, read-only screens | 2,679 | 10 to 16 | 6 to 10 | medium | inference |
| 4. Build and GDG jobs | 0 (JCL only) | 2 to 4 | 1 to 2 | medium | inference |
| 5. Reference-data refresh, statements | 1,355 | 8 to 12 | 5 to 8 | medium | inference |
| 6. Master refresh, posting, report | 2,328 | 24 to 40 | 16 to 28 | low | inference |
| 7. Online screens that write | 7,972 | 30 to 50 | 20 to 34 | low | inference |
| 8. Authorization and DB2 unload and load | 2,602 | 14 to 24 | 10 to 18 | low | inference |
| 9. Authorization screens, type maintenance | 4,469 | 16 to 28 | 11 to 20 | low | inference |
| Total | 22,489 | 113 to 189 | 75 to 129 | low | inference |

LOC are summed from the program table (`01-inventory.md:25`). The totals row sums the rows above and has no source line of its own.

## What each term does under AI assistance

Each reduction is a falsifiable assumption, not a multiplier.

| Term | Does AI assistance shrink it? | Assumption | Evidence |
|---|---|---|---|
| Port (transliteration) | Yes, when a comparison harness exists | Review takes about a quarter of the authoring time it replaces, at roughly 1 review-day per 1,000 lines | inference |
| Boundary work (facade over the VSAM masters) | Partly | The code is quick; choosing the boundary is not. Wave 6 carries it | inference |
| Equivalence harness | Partly | Harness code is quick to write. Getting the oracle (archived GDG generations, job logs) is not | inference |
| Oracle, approvals, rehearsals, cutover windows, client availability | No | These dominate waves 6 and 7 and are the same in both columns | inference |

The two columns differ least in waves 6 and 7 for that reason: the cutover and rehearsal terms do not shrink.

## What the range is most sensitive to

1. **The oracle exists.** Assumes archived `TRANSACT.BKUP` and `DALYREJS` generations cover a month-end (`app/jcl/TRANREPT.jcl:23`, `app/jcl/POSTTRAN.jcl:23`). If the client keeps none, wave 6 moves from replay to characterization tests and roughly doubles.
2. **A facade over the three VSAM masters is enough.** Assumes the online writers in wave 7 can call the same facade the batch jobs use (`02-coupling.md`). If the online side needs its own bridge, wave 7 grows by about half.
3. **The date and layout copybooks are the only contract.** Assumes the SORT offsets in the report match `CVTRA05Y` (`app/cpy/CVTRA05Y.cpy:5`) and nothing else reads the files by byte offset. A second consumer outside the tree would add a harness per consumer.
4. **The two assembler modules are small.** Assumes `app/asm/COBDATFT.asm:1` is a date-format routine with a few cases. If it is not, waves 6 and 7 both slip.

## Where an AI agent can do the work, and where it cannot

- **Strong:** transliterating the batch programs (`CBTRN02C`, `CBTRN03C`, `CBACT04C`) and the reload jobs once the harness gives it a pass-or-fail signal. Writing the diff harness itself.
- **Weak:** inferring intent behind undocumented rules. Examples the risk assessor found: reject reason 109 is set but never reaches the reject file (`app/cbl/CBTRN02C.cbl:556`), expiry is compared as a string (`app/cbl/CBTRN02C.cbl:414`), and `CBTRN03C` appears to add the last record twice (`app/cbl/CBTRN03C.cbl:198`). A porter must decide whether each is a bug to keep or fix, and that goes in the Deviation Register. An agent should not decide it.
- **Cannot:** read the unparsed DB2 DDL, IMS DBD and PSB, and assembler files for waves 8 and 9 until someone confirms what they hold.
