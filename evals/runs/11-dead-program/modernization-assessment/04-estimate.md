# 04 Estimate

Target state: refactor. Every figure below is inference. It is a range in person-days, built from the
factors in the table, not from lines of code. There is one wave, so there is no single number to give
for the system. The estimate covers only the tree we were given.

## Method

The weight goes to the things that move an estimate most. Line count is not one of them.

| Factor | What the tree shows | Effect | Confidence | Evidence |
|---|---|---|---|---|
| Coupling edges crossing the wave boundary | None. Wave 1 holds every live unit. | Pushes the estimate down | high | analysis: `articulation_points` and `data_hubs` are empty |
| Behavioral oracle | Unknown. The job has no DD, so no archived output file exists in the tree. | Sets the harness cost. This is the main driver. | low | `app/jcl/MAINJOB.jcl:2` |
| God modules in the wave | None | Pushes down | high | analysis: `god_modules` is empty |
| Business logic in the database | None in the tree. No SQL, no DB2 table, no dataset. | Pushes down | medium | analysis: `data_hubs` is empty |
| A team member who reads COBOL | Not stated | Unknown. Not priced. | low | inference |

The live source is 11 lines: `PGMMAIN` 5, `PGMLIVE` 4 and `MAINJOB` 2
(`app/cbl/PGMMAIN.cbl:5`, `app/cbl/PGMLIVE.cbl:4`, `app/jcl/MAINJOB.jcl:2`).

## Estimate by wave

| Wave | Part | Range (person-days) | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Port the three units to the refactor target | 0.5 to 1.5 | medium | inference |
| 1 | Build the comparison harness and run it against the legacy job | 3 to 8 | low | inference |
| 1 | Normalization spec, deviation register, sign-off | 1 to 2 | low | inference |
| 1 | Total | 4.5 to 11.5 | low | inference |
| Cleanup | Remove `PGMDEAD` and `cpy:UNUSED` once telemetry confirms | 0.5 | medium | `app/cbl/PGMDEAD.cbl:4`, `app/cpy/UNUSED.cpy:1` |

The port is a small share. The harness is most of the cost, because a job with no output has to be
verified from its return code, its log and its place in the cycle.

## The assumptions this range is most sensitive to

1. Assumes `job:MAINJOB` is the whole nightly batch cycle. If the real cycle has other jobs, this range
   covers only the fragment we were given. It carries no ordering work and no shared-data work, and the
   plan has to be cut again from the client's scheduler export. The total then grows with the number of
   jobs and adds a cycle-level harness. Low confidence. (`app/jcl/MAINJOB.jcl:1`)
2. Assumes a legacy run of `job:MAINJOB` can be observed, by a parallel run or by at least 12 months of
   archived job logs. If neither exists, the only oracle is a characterization test written from the
   source. That test proves a call returns and nothing more. The harness cost falls to the low end, but
   the equivalence claim stays provisional and cannot sign off the wave. (inference)
3. Assumes the source in the tree is the source behind the production load modules. `PGMMAIN` and `PGMLIVE`
   hold no logic (`app/cbl/PGMLIVE.cbl:4`). If production runs different code, the port range is wrong by
   an unknown multiple. (inference)

## Where Claude Code can do the port, and where it cannot

| Part | Claude Code | Confidence | Evidence |
|---|---|---|---|
| Transliterate `PGMMAIN`, `PGMLIVE` and the JCL step into the refactor target | Strong. It is a call and a return, and a good harness will catch any slip. | high | `app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMLIVE.cbl:4` |
| Write the harness scaffold and the normalization spec | Strong | medium | inference |
| Say whether `job:MAINJOB` is the nightly batch cycle | Cannot. This is business intent the source does not carry. Ask the client. | high | `app/jcl/MAINJOB.jcl:1` |
| Say what runs after the job and what checks its return code | Cannot. It lives in a scheduler that is not in the tree. | high | analysis: `warnings` names the missing scheduler |
