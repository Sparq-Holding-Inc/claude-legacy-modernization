# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Scope | `.` (the current directory) | none given |
| Target state | refactor | `--target refactor` |
| Must not break | the nightly batch cycle | `--must-not-break` |
| Telemetry | none | `--telemetry none` |
| Delivery | not given. The estimate shows conventional and AI-assisted. | `--delivery` missing |

No defaults applied. All three scoping answers came as flags.

Because telemetry is none, every dead-code claim is provisional.

## What was found

The tree is very small: two JCL jobs, each a single `IEFBR14` step (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`), and one Control-M file of two jobs (`app/scheduler/nightly.xml:3`). There are no COBOL programs, copybooks, datasets or computed calls. Nothing the extractor could not parse (`unparsed` is empty).

- **Waves: 1.** The nightly cycle, JOBA then JOBB. See `03-waves.md`. No deviations from the seed.
- **Coupling:** temporal only. `JOBA-DONE` gates JOBB (`app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9`).
- **Estimate:** 3 to 7 engineer-weeks conventional, 2.5 to 5.5 AI-assisted, both for the visible scope only. See `04-estimate.md`.
- **Dead code:** none found, and dormancy was not measured. See `05-dead-code.md`.
- **Test strategy:** scheduler trace diff under a parallel run. See `06-test-strategy.md`.

## Largest risk

**The tree probably does not contain the nightly batch cycle it is meant to protect.** Both jobs run `IEFBR14`, which does nothing, and have no DD statements (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`). What is here sequences work and does none. If the real cycle lives elsewhere, this assessment covers its scheduler skeleton only, and wave count, cost and risk will all change once the real programs are supplied. Confidence: medium. The alternative, that these are intentional placeholders, cannot be ruled out from the tree (`inference`).

A second, quieter risk sits on the same path. JOBA starts only when `EXTERNAL-FEED` is set, and nothing in the tree sets it (`app/scheduler/nightly.xml:5`). If the feed is late or missing, neither job runs, and nothing fails.

## Open Questions for the client's engineers

1. **Where is the real work?** JOBA and JOBB run only IEFBR14 (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`). Are they stubs, or is the nightly cycle's real code (programs, procs, other JCL, other Control-M folders) in another repository or library that was not given to us?
2. **What sets `EXTERNAL-FEED`?** It is an input condition with no setter in the tree (`app/scheduler/nightly.xml:5`). Another scheduler folder, a file watcher, an operator, or an upstream system? What happens if it never arrives?
3. **Why does JOBB delete `JOBA-DONE`?** (`app/scheduler/nightly.xml:10`). Run-once protection, housekeeping, or something a downstream job relies on? The new scheduler must reproduce it if it matters.
4. **Which other jobs belong to "the nightly batch cycle"?** The must-not-break item maps here only to the `NIGHTLY` folder (`app/scheduler/nightly.xml:3`). Is that the whole item?
5. **Is a parallel run possible?** Can the old Control-M keep ordering `NIGHTLY` while a new scheduler runs a shadow copy for at least three cycles including a month-end? This decides the oracle.
6. **What Control-M settings are missing from this file?** The export holds no calendars, time windows, resources, `CONFIRM` flags, shout or notification rules, or run-as users. Can we have the full folder definition and the calendars it uses?
7. **Do these jobs still run, and since when?** There is no git history and no telemetry, so dormancy was not measured. Can we have 12 months of job logs or SMF?
8. **What happens in JCL the extractor does not model?** `IF/THEN/ELSE` and `COND=` are not read (`graph.json` `meta.limits`). Do the real jobs use them?

## Limits that touch this system

From `graph.json` `meta.limits`: JCL `IF/THEN/ELSE` and `COND=` are not modeled. Only Control-M XML and shell wrappers are read as schedulers, so any other scheduler format (for example CA-7 or TWS) would have been listed as not parsed, and none was. The "not parsed" list is empty.
