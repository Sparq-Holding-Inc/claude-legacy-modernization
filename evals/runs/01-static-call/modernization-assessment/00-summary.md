# 00 Summary

Scope: the current directory (`.`). The tree is two fixed-format COBOL programs, PROGA and PROGB,
11 lines in all (`app/cbl/PROGA.cbl:1-7`, `app/cbl/PROGB.cbl:1-4`).

## Scoping answers

All three answers came in as flags on a non-interactive run, so **no defaults applied**.

- Target state: refactor.
- Must not break: "the nightly batch cycle". It maps to no unit in the tree. The tree holds no JCL,
  scheduler or CSD, so I did not invent a mapping.
- Telemetry: none. Every dead-code claim is provisional.

## Result

- **Wave count: 0.** The tree has no entry point, so nothing can be sequenced. `waves.json` has
  `"waves": []` and both programs are in `unassigned`. Nothing can be sequenced until the client
  supplies JCL, a CSD or a scheduler export.
- **Coupling:** one static call edge, PROGA to PROGB, high confidence (`app/cbl/PROGA.cbl:6`). No shared
  data, no copybook, no computed call, no cycle.
- **Risk:** both programs score low-low. PROGA is scored with low confidence, because its place in the
  nightly cycle cannot be shown.
- **Dead code:** unreachable none, dormant none (not measured, no dates), unknown PROGA and PROGB.
- **Estimate:** 0.5 to 2 engineer-days for the port of the two files, inference. The cycle around
  them is not estimated.

## The single largest risk

**The must-not-break item cannot be located.** "The nightly batch cycle" is the one thing you said
must not break, and the tree holds nothing that defines a cycle: no JCL, no PROC, no scheduler, no
CSD (`analysis.entry_points` is empty, and `meta.files_seen` in `graph.json` is zero for those kinds).
The two programs may be part of it, may be a fragment of something larger, or may be unrelated to it.
Any plan made from this tree would rest on a guess. This is a finding about the input, and the
analysis of the two programs themselves shows little risk.

## Open Questions for the client's engineers

1. **What runs the nightly batch cycle?** Please supply the JCL for every job in it, its PROCs, and
   the scheduler export (Control-M XML, CA-7, TWS or other), with the order and the condition-code
   rules. Is PROGA in it? Nothing in the tree says so.
2. **Is the PROGB in this tree the one that runs in production?** It is a single `GOBACK`
   (`app/cbl/PROGB.cbl:4`). Is it a stub, a placeholder, or a real no-op? If a different PROGB is
   link-edited from another library, the source we have is not the program that runs.
3. **Who else calls PROGA or PROGB?** The extractor sees only callers inside the tree. Are there
   other programs, jobs or transactions outside it?
4. **Does anything read the console line `CALL FAILED IF WE GET HERE`?** It is printed before the call,
   so it prints on every run (`app/cbl/PROGA.cbl:5`). Does an operator, a log scanner or an alert
   depend on it? A port should copy it as it is until you decide otherwise, and a change goes in the
   Deviation Register (`06-test-strategy.md`).
5. **Does the cycle test the return code of PROGA's step?** Neither program sets `RETURN-CODE`
   (inference), so the step ends with the default code. If a later step is conditional on it, that is
   a behavior a port must keep.
6. **Was PROGA compiled with static or dynamic calls?** The `CALL 'PROGB'` at `app/cbl/PROGA.cbl:6` is a
   literal. The compile option decides whether PROGB is bound into PROGA's load module or loaded at run
   time. It is not in the tree. It changes whether the two can be deployed and rolled back
   separately.
7. **Which programs ran in the last 12 months?** Can you supply SMF type 30 records or the scheduler
   run log for the cycle? Without telemetry, PROGA and PROGB stay in the unknown bucket.
8. **Do you have source-control dates for the two files?** The tree is not a git repository, so the
   extractor had no last-modified date and did not compute the dormant bucket.
9. **Is there an archive of job output for the cycle** (SYSOUT, reports, GDG generations,
   partner extracts)? It is the oracle for the equivalence harness. Does the old cycle have a window
   where it can run beside the new one, and does that window include a month-end?
10. **Who can read COBOL on your team?** It sets how much of the port needs outside help.

## Files not parsed

None. `unparsed` in `graph.json` is empty. Both files were read as fixed format.

## Extractor limits that touch this system

These are the entries in `meta.limits` in `graph.json` that bear on what this tree needs.

- Only Control-M XML and shell wrappers that name JCL files are read as schedulers. If the cycle runs
  under another scheduler, its definitions will not be read, and the ordering has to come from you.
- `IF/THEN/ELSE` and `COND=` in JCL are not modeled, and step order is file order. If the cycle has
  conditional steps, the extractor will show a straight line.
- A called subprogram gets no DDs from its caller's JCL step. PROGB has none of its own.
- The other limits (CICS chains, DB2, IMS and MQ drivers, IDCAMS cards, variable call targets,
  `COPY REPLACING`) do not touch these two files, which use none of them
  (`app/cbl/PROGA.cbl:1-7`, `app/cbl/PROGB.cbl:1-4`).

## Other files

- `01-inventory.md`, `02a-edge-tables.md`, `03a-wave-seed.md`, `03a-waves-draft.json`,
  `05a-dead-code-candidates.md`: generated by the scripts.
- `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md`: written
  for this assessment.
- `graph.json`, `waves.json`, `dead-code.json`, `risks.json`: machine-readable outputs.
