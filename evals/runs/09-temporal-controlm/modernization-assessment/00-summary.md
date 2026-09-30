# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Scope | `.` (the work folder: two JCL members and one Control-M file) | command argument |
| Target state | refactor | `--target refactor` |
| Must not break | "the nightly batch cycle" | `--must-not-break` |
| Telemetry | none. Every dead-code claim is provisional | `--telemetry none` |

All three answers came as flags: no defaults applied.

## Result

- **Waves: 1.** One family, batch-utility, holding `job:JOBA`, `job:JOBB`, `sch:NIGHTLY/JOBA` and `sch:NIGHTLY/JOBB`. It cannot be split, because the order between the two jobs exists only as a scheduler condition. `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9`. Detail is in `03-waves.md`.
- **Refactor has little to act on here.** There is no application source in the tree. Both steps run IEFBR14, a do-nothing system utility (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`). What must be preserved is the scheduling contract, and that is a finding for the plan, not a code change. inference
- **Estimate:** 8 to 15 person-days for wave 1 plus an elapsed parallel run of one to two months, low confidence. inference. Detail is in `04-estimate.md`.
- **Dead code:** none found, and dormancy was not measured because the tree has no git history. `05-dead-code.md`

## Largest risk

The must-not-break cycle keeps its order only inside the Control-M definition. JOBB waits on the condition JOBA-DONE that JOBA posts, then deletes it (`app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9`, `app/scheduler/nightly.xml:10`). Neither JCL member mentions the other (`app/jcl/JOBA.jcl:1`, `app/jcl/JOBB.jcl:1`). A port that carries the jobs and not the conditions keeps every job and silently loses the cycle. JOBA also waits on EXTERNAL-FEED, which nothing in the tree sets (`app/scheduler/nightly.xml:5`), so the start of the cycle depends on something the team has not shown us. Risk score: both jobs are `low-high` (`modernization-assessment/risks.json:13`, `modernization-assessment/risks.json:42`).

## Open Questions

Addressed to the client's engineers.

| # | Question | Why it matters | Evidence |
|---|---|---|---|
| 1 | What adds the condition EXTERNAL-FEED, and when does it arrive each night? | JOBA cannot start without it, and nothing in the tree sets it. The trigger has to be rebuilt and tested in the target | `app/scheduler/nightly.xml:5` |
| 2 | Are JOBA and JOBB really just IEFBR14 in production? If not, where do the real programs live? | Both steps run a null utility. If the real work is elsewhere, this wave is only the scheduling layer and the wave count and estimate are too low | `app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2` |
| 3 | What reads JOBB-DONE? Does anything outside this folder wait on it? | Nothing in the tree consumes it. A hidden consumer would join the wave | `app/scheduler/nightly.xml:11` |
| 4 | Why does JOBB delete JOBA-DONE, and what is the operators' rerun and restart procedure for each job? | Deleting the condition changes what a rerun does. The target scheduler has to match, and the harness needs a case for each rerun path | `app/scheduler/nightly.xml:10` |
| 5 | What does the scheduler entry omit: start time, calendar, days, cyclic runs, alerts, return code handling, run-as user? | None of these appear in the two entries, yet the cycle must run on the right nights and alert the right people | `app/scheduler/nightly.xml:4`, `app/scheduler/nightly.xml:8` |
| 6 | Are there other scheduler folders, other schedulers, or manual submits that also run JOBA or JOBB? | Only Control-M XML and shell wrappers that name JCL files are read (`meta.limits`). A second trigger would be invisible | `analysis` field `unscheduled_jobs` |
| 7 | Which reports, files, or downstream systems make up "the nightly batch cycle" from the business's side, and what does each night's success look like? | The oracle for the must-not-break item has to come from job output, logs and reports, since the tree has no datasets | `app/jcl/JOBA.jcl:2` |
| 8 | Do you have 12 months of scheduler history and SMF or job logs for JOBA and JOBB? | It is the telemetry needed to settle dormancy, and the source for the parallel run and replay | inference |
| 9 | Can the old and new schedulers run in parallel for one full business cycle, including month end? | It is the strongest oracle available. Teams often wrongly assume it is impossible | inference |

Limits in `meta.limits` that touch this system: JCL `IF/THEN/ELSE` and `COND=` are not modeled, and both members are two lines with neither (`app/jcl/JOBA.jcl:1`, `app/jcl/JOBB.jcl:1`); only Control-M XML and shell wrappers are read as schedulers; the extractor draws no edge for a deleted condition (`app/scheduler/nightly.xml:10`). Files not parsed: none. Dormancy: not computed, since the tree is not a git repository. `analysis` field `warnings`

## Files in this folder

`graph.json` is the extractor output. `01-inventory.md`, `02a-edge-tables.md`, `03a-wave-seed.md`, `03a-waves-draft.json` and `05a-dead-code-candidates.md` were generated by `render.py`. The others are the assessment: `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md`, `waves.json`, `risks.json` and `dead-code.json`.

The `risks.json` scores were written inline by following `agents/migration-risk-assessor.md`. No agent was started. The dependency-cartographer was not needed: there were no open edges.
