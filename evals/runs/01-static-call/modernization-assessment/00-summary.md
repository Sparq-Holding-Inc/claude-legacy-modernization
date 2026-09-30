# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | flag `--target refactor` |
| Must not break | the nightly batch cycle | flag `--must-not-break` |
| Runtime telemetry | none | flag `--telemetry none` |
| Scope | `.` | no scope argument given |

All three answers came as flags: no defaults applied.

## What was assessed

Two COBOL programs, 11 lines in all. `PROGA` displays a message, calls `PROGB`, and stops. `PROGB` returns.
The tree holds no copybooks, JCL, procs, CICS definitions, scheduler files, shell wrappers or datasets
(`meta.files_seen` in `modernization-assessment/graph.json`).

| Finding | Confidence | Evidence |
|---|---|---|
| One call edge: PROGA calls PROGB with a literal target, resolved, high confidence | high | `app/cbl/PROGA.cbl:6` |
| PROGB does nothing but return | high | `app/cbl/PROGB.cbl:4` |
| No datasets, no contract edges, no temporal edges, no computed calls, no embedded JCL | high for these files | analysis: `edge_counts`, `unresolved_dynamic`, `embedded_jcl` |
| No entry point exists, so no reachability can be shown and both units are unknown | high | analysis: `entry_points`, `dead_code_candidates` |
| PROGA writes the text "CALL FAILED IF WE GET HERE" on every run, before the call, whether or not the call works | high | `app/cbl/PROGA.cbl:5` |
| Nothing handles a failed CALL | medium | `app/cbl/PROGA.cbl:6` |

## Wave count

**1**, and it is a placeholder. The extractor cut zero waves, because the tree has no entry point. The wave
validator rejects an empty plan, so PROGA and PROGB were placed in one wave by a recorded deviation. See
`03-waves.md`. Confidence: low.

## Single largest risk

The must-not-break item, the nightly batch cycle, cannot be assessed from this tree. Nothing in it shows
where PROGA sits in that cycle, what runs before or after it, or whether it runs at all. A migration
planned from these two files could break the cycle in a way this assessment cannot see. Evidence: analysis:
`warnings` (no entry points found), and `app/cbl/PROGA.cbl:1`. Inference for the consequence.

## Open Questions for the client's engineers

1. Which JCL job and which scheduler entry run PROGA, and where does that job sit in the nightly batch
   cycle? Neither JCL nor a scheduler is in the tree (analysis: `entry_points` is empty).
2. Does anything other than PROGA call PROGB, in code that is not in this tree? If so, PROGB is a shared
   subprogram and wave 1 splits.
3. Is the DISPLAY at `app/cbl/PROGA.cbl:5` intentional? Its text says the call failed, but it prints on every run
   before the call. Does any log scraper, alert or operator procedure act on that text?
4. Is the CALL at `app/cbl/PROGA.cbl:6` bound statically or loaded at run time (the DYNAM option), and what
   should happen if PROGB is missing? The tree does not show it, and no ON EXCEPTION is coded.
5. Was the rest of the system left out of this copy on purpose? Copybooks, JCL, procs, CSD, BMS and
   scheduler files all count zero in `meta.files_seen`. The extractor listed nothing as not parsed, so the
   gap is in the tree and not in the tool.
6. Can you supply a full business cycle of job logs or SMF records for the job that runs PROGA? With
   `--telemetry none`, every dead-code claim is provisional, and the oracle for wave 1 is weak.
7. Can you supply source-control or library change dates? The folder is not a git repository, so the
   dormant bucket was not computed (analysis: `warnings`). An empty dormant list means not measured.

## Extractor limits that touch this system

- No last-modified dates, so dormancy was not computed (analysis: `warnings`).
- Only Control-M XML and shell wrappers that name JCL files are read as schedulers, and none were present, so
  no job order is modeled (`meta.limits`).
- IF/THEN/ELSE and COND= in JCL are not modeled. This would matter as soon as JCL arrives (`meta.limits`).
- A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program. Neither
  program makes a variable call (`meta.limits`).
- Files not parsed: none (`unparsed` is empty).

## Files

`01-inventory.md`, `02-coupling.md`, `02a-edge-tables.md`, `03-waves.md`, `03a-wave-seed.md`,
`03a-waves-draft.json`, `04-estimate.md`, `05-dead-code.md`, `05a-dead-code-candidates.md`,
`06-test-strategy.md`, and the four JSON outputs `graph.json`, `waves.json`, `risks.json`, `dead-code.json`.
