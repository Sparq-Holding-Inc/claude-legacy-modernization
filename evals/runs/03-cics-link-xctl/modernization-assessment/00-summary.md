# 00 Summary

## Scope and scoping answers

Scope: the work folder (`.`). It holds four COBOL programs with EXEC CICS commands. It holds no JCL, no
scheduler, no copybooks, no datasets, no CSD and no BMS maps (`01-inventory.md`). The extractor found no entry
point and nothing it could not parse.

All three scoping answers came as command flags. No default was used and nothing was assumed.

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | `--target refactor` |
| What must not break | the nightly batch cycle | `--must-not-break` |
| Runtime telemetry | none | `--telemetry none`, so every dead-code claim is provisional |

## The most important thing to know about this tree

The stated must-not-break item, the nightly batch cycle, is not in the tree. There is no batch program, JCL
job, scheduler definition or dataset. The four programs are CICS programs that hold no file, SQL or COPY
statement (`app/cbl/PROGA.cbl:1-26`). Nothing here can be tied to the batch cycle, and nothing here rules a
tie out. It may run through a VSAM file, a DB2 table, a queue or an EXCI call, all defined outside the source.
The assessment says nothing about the batch cycle, and the equivalence anchors in `06-test-strategy.md` for it
are still to be defined.

## Result

| Item | Result | Confidence | Evidence |
|---|---|---|---|
| Waves | 1. Four programs and one call chain. Nothing to cut. See `03-waves.md` | low | `app/cbl/PROGA.cbl:12-25` |
| Estimate | Wave 1: 5 to 10 person days expected, 3 to 25 across scenarios. See `04-estimate.md` | low | inference |
| Dead code | Unreachable none, dormant none, unknown all four. No entry point in the tree, no telemetry | low | `app/cbl/PROGA.cbl:1` |
| Largest risk | See below | low | `app/cbl/PROGA.cbl:15-16` |

## Single largest risk

The computed LINK in PROGA. It calls whatever program name the caller puts in the COMMAREA
(`app/cbl/PROGA.cbl:15-16`). The set of programs it reaches cannot be bounded from the source. The callers
are not in the tree. It is an undocumented dispatch contract. A port that resolves it statically would
silently drop reachable programs, and it blocks any confident dead-code claim. PROGA scores high-high on
port difficulty and blast radius (`risks.json`). This rests on thin evidence, so it is a floor.

## What the extractor missed or got wrong by construction

- `graph.json` records LINK and XCTL both as `call`. XCTL does not return, and the code after the XCTL at line
  20 (the XCTL to PROGD and the RETURN) likely never runs. So the graph edge PROGA to PROGD, rated high
  confidence, is probably never taken (inference, `app/cbl/PROGA.cbl:20-26`).
- The extractor left the XCTL at line 20 as a computed call. Reading the program settles it: `WS-NEXT-PGM` is set
  only at line 19, so the target is PROGC (inference, `app/cbl/PROGA.cbl:19-20`).

## Open Questions

For the client's engineers.

1. **Where is the nightly batch cycle, and does it touch these programs?** Provide its JCL, scheduler
   definitions and source. Say whether any batch job reaches PROGA, PROGB, PROGC or PROGD through EXCI, MQ, a
   transient data queue or START, and whether these programs share a VSAM file or DB2 table with the batch
   cycle. Nothing in this tree can answer it.
2. **What names do callers put in the COMMAREA that PROGA LINKs to?** Give the transaction IDs that start
   PROGA, the callers, and a sample or a list of the values sent (`app/cbl/PROGA.cbl:15-16`). Is it a short
   fixed list, or can it be any program in the region? What happens with no COMMAREA, when nothing tests its
   length first (`app/cbl/PROGA.cbl:9`)?
3. **Is the XCTL to PROGD ever reached?** Control does not return from the XCTL at line 20, and no `RESP` or
   `HANDLE CONDITION` covers it (`app/cbl/PROGA.cbl:20-25`). Does anything else, a CSD definition, another
   transaction or the computed LINK, enter PROGD? Is the code after line 20 a leftover?
4. **Are PROGB, PROGC and PROGD the real production source?** Each is four lines and only RETURNs
   (`app/cbl/PROGB.cbl:4`, `app/cbl/PROGC.cbl:4`, `app/cbl/PROGD.cbl:4`). If they are stubs, the assessment covers
   a skeleton and the estimate does not hold.
5. **Which transactions map to which programs?** The CSD is not in the tree, so the extractor found no entry
   point and every program is unknown. Supply the CSD or the transaction to program list.
6. **Can you supply telemetry?** Twelve months of CICS statistics or SMF 110 records would show which of the four
   programs ran and which names went into the COMMAREA. Without it every dead-code claim is provisional.
7. **What are the last change dates of the four sources?** The tree has no git history, so `last_modified` is
   null for every file and the dormancy rule could not run.
8. **Does anything outside the source govern what PROGA does on failure?** A region level abend exit or
   program auto-install would change what a bad program name does (`app/cbl/PROGA.cbl:16-18`, `app/cbl/PROGA.cbl:20-22`).

## Extractor limits that touch this system

Nothing was skipped: the extractor listed no unparsed file.

| Limit in `meta.limits` | How it touches this tree | Confidence | Evidence |
|---|---|---|---|
| A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program | It kept line 20 open, and it cannot resolve line 16 | high | `app/cbl/PROGA.cbl:16`, `app/cbl/PROGA.cbl:20` |
| EXEC CICS RETURN TRANSID, START and SEND MAP are not edges | I read all four programs and found none of them, so no chain is hidden here | high | `app/cbl/PROGA.cbl:26`, `app/cbl/PROGB.cbl:4`, `app/cbl/PROGC.cbl:4`, `app/cbl/PROGD.cbl:4` |
| Only Control-M XML and shell wrappers that name JCL files are read as schedulers | The tree holds no scheduler of any kind, so the batch cycle cannot be seen. This is Open Question 1 | high | inference |
| Git dates | The tree has no git history, so no last-modified dates exist | high | inference |

The other limits (fixed format only, COPY REPLACING, DDs of called subprograms, IDCAMS and SORT cards,
JCL IF/THEN/ELSE and COND, nested PROCs, internal reader) do not touch this tree, because it holds no
JCL, copybook or dataset.

## Files

`00-summary.md`, `01-inventory.md`, `02-coupling.md`, `02a-edge-tables.md`, `03-waves.md`, `04-estimate.md`,
`05-dead-code.md`, `05a-dead-code-candidates.md`, `06-test-strategy.md`, `graph.json`, `waves.json`,
`dead-code.json`, `risks.json`.
