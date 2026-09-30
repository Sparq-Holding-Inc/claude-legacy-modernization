# 00 Summary

Assessment of `work`, scope `.`. The extractor read 3 JCL members and 1 shell wrapper: 8 nodes and 9
edges. There is no COBOL, no copybook, no proc and no dataset in the tree.

## Scoping answers

No defaults applied. All three answers came as flags.

| Question | Answer |
|---|---|
| Target state | refactor |
| What must not break | the nightly batch cycle |
| Runtime telemetry | none, so every dead-code claim is provisional |

## Result

- **Waves: 1.** All four units (job:JOBA, job:JOBB, job:JOBC, sch:scripts/nightly.sh) are one
  batch-utility family. No deviations from the seed. See `03-waves.md`.
- **Largest risk.** The one order the nightly cycle depends on, JOBA before JOBB, exists only as line
  order in a shell wrapper that calls a `submit` command the tree does not define
  (`scripts/nightly.sh:4`, `scripts/nightly.sh:5`). A port that treats the jobs as independent tasks
  can reorder or overlap them with no abend. The extractor rates the edge medium confidence.
- **What the tree cannot show.** All three jobs run only `IEFBR14` with no DD statements
  (`jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2`, `jcl/JOBC.jcl:2`). Nothing in the tree says what the nightly cycle
  does. The work is either elsewhere or these are stubs. Every score in `risks.json` is low
  confidence for that reason.
- **Estimate.** 3 to 10 person-days, inference, on the assumption that production matches the tree.
  See `04-estimate.md`.
- **Dead code.** None found and none proposed for deletion. JOBC is a retirement candidate on the
  strength of a comment (`scripts/nightly.sh:2`, `scripts/nightly.sh:6`), which is not proof.
  See `05-dead-code.md`.
- **Test strategy.** The oracle has to come from job history and logs, since the tree holds no
  datasets. See `06-test-strategy.md`.

## Open Questions for the client's engineers

1. What does `submit` do (`scripts/nightly.sh:4`)? Does it wait for the job to end, and what does it
   return if the job abends? This decides whether JOBB depends on JOBA finishing or only on JOBA being
   submitted. `set -e` (`scripts/nightly.sh:3`) only sees the submit command's own status.
2. Are JOBA, JOBB and JOBC really no-op jobs? Each runs only `IEFBR14` with no DD (`jcl/JOBA.jcl:2`,
   `jcl/JOBB.jcl:2`, `jcl/JOBC.jcl:2`). Where is the JCL, program and data the nightly cycle actually
   works on? If production differs from the tree, this assessment must be redone.
3. Is JOBC retired? The wrapper says so and comments out its submit (`scripts/nightly.sh:2`,
   `scripts/nightly.sh:6`). Does any other scheduler, wrapper or person still submit it? Telemetry is `none`.
4. Which scheduler starts `scripts/nightly.sh` in production, and are there other chains, such as a
   month-end, quarter-end or holiday variant? Only shell wrappers and Control-M XML are read as
   schedulers, and this tree has one wrapper.
5. What are the restart and failure rules? If JOBA abends after a good submit, what happens to JOBB?
   The extractor does not model JCL `IF/THEN/ELSE` or `COND=`, and none appears in the members.
6. What consumes the output of the nightly cycle, and what is the completion deadline? The tree has no
   dataset, so the downstream dependents of the cycle are invisible.
7. Can the client supply last-modified dates? The tree is not a git repository, so the dormancy rule was
   not computed and the dormant bucket is not measured.

## Not parsed

Nothing. The extractor listed no unparsed file.

## Extractor limits that touch this system

| Limit | Why it touches this system | Evidence |
|---|---|---|
| Only Control-M XML and shell wrappers that name JCL files are read as schedulers | A scheduler in another form would hold ordering this scan cannot see. | analysis (`meta.limits`) |
| IF/THEN/ELSE and COND= in JCL are not modeled | Failure-dependent job order would not appear as an edge. None is in the three members. | analysis (`meta.limits`) |
| Shell control flow such as `set -e` is not modeled (this is not written in `meta.limits`, I noticed it while reading) | `set -e` is read by hand and carried as inference. | `scripts/nightly.sh:3` |
| No last-modified dates | The tree is not a git repository, so dormancy was not computed. | analysis (`warnings`) |
