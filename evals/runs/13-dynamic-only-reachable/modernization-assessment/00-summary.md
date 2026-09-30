# 00 Summary

Assessment of the tree in `app/`: one JCL job, one step and two COBOL programs.

## Scoping answers

All three came as flags, so no question was asked and no default was used.

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | `--target refactor` |
| What must not break | "the nightly batch cycle" | `--must-not-break` |
| Runtime telemetry | none. Every dead-code claim is provisional | `--telemetry none` |

## Result in one paragraph

The system is one wave. It has one entry point, `job:MAINJOB`, whose only step runs `PGMMAIN`
(`app/jcl/MAINJOB.jcl:2`). `PGMMAIN` reads a program name with `ACCEPT` and calls it
(`app/cbl/PGMMAIN.cbl:8`, `app/cbl/PGMMAIN.cbl:9`). Nothing in the source bounds that name. So the
tree does not tell us what the job really runs, and it does not let us call `HIDDEN01` dead.

## Waves

| Wave | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|
| 1 | `job:MAINJOB`, `PGMMAIN`, `HIDDEN01` | high | low | `app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:9` |

Wave count: 1. It is one wave because the tree is one job and two programs, with no shared dataset, no
strongly connected component and no articulation point. See `03-waves.md`. `PGMMAIN` scores high-high
on the two risk axes, and it is in the only wave. The plan says so plainly and gates the start of the
wave on two facts the client has to supply.

## Single largest risk

The computed call at `app/cbl/PGMMAIN.cbl:9`. The target is a name read at run time
(`app/cbl/PGMMAIN.cbl:8`) into a field with no `VALUE` clause (`app/cbl/PGMMAIN.cbl:5`), and the
call has no `ON EXCEPTION` clause. Three things follow. All three are inference:

- Any program the load library holds could run, and a port that assumes a fixed set will break the
  first time an unlisted name arrives, with no warning in the source.
- `HIDDEN01` has no static caller and only returns (`app/cbl/HIDDEN01.cbl:4`). It looks like dead code
  and is not provably dead. It stays in the unknown bucket, and the plan keeps it (`05-dead-code.md`).
- The client's requirement is that the nightly batch cycle must not break. The tree cannot show that
  `job:MAINJOB` is in that cycle, or what runs around it, because no scheduler was found.

## Artifacts

| File | What it holds |
|---|---|
| `graph.json`, `01-inventory.md`, `02a-edge-tables.md`, `05a-dead-code-candidates.md` | Extractor output and generated tables |
| `02-coupling.md` | Coupling patterns and the computed call |
| `03-waves.md`, `waves.json` | Wave plan |
| `risks.json` | Two-axis risk scores |
| `04-estimate.md` | Range estimate with sensitive assumptions |
| `05-dead-code.md`, `dead-code.json` | Three buckets. Unreachable none, dormant none, unknown one |
| `06-test-strategy.md` | Oracle, normalization spec, targeted cases, deviation register |

## Open Questions for the client's engineers

1. **What names has `PGMMAIN` been given?** The name comes from `ACCEPT` (`app/cbl/PGMMAIN.cbl:8`).
   Send the `SYSIN` or `PARM` history for at least 12 months, including month-end and year-end. Which
   programs, in which libraries, and how often?
2. **Is the JCL complete?** It has one line of substance and no `SYSIN` DD, and no other DD
   (`app/jcl/MAINJOB.jcl:2`). Where does the program name come from at run time? Is there a proc, an
   override or a scheduler parameter that was not copied?
3. **Is `job:MAINJOB` part of the nightly batch cycle, and what else is in it?** No scheduler artifact
   was parsed. Send the Control-M export or the wrapper scripts, and the order the jobs run in.
4. **Does `HIDDEN01` run, and why does it exist?** It has no caller and its body only returns
   (`app/cbl/HIDDEN01.cbl:4`). Is it a stub, a retired program, or something called by name once in a
   while? Who owns it?
5. **What should happen with a blank, unknown or over-long name?** The call has no `ON EXCEPTION`
   clause (`app/cbl/PGMMAIN.cbl:9`). What does the runtime do today, and does any downstream step
   depend on that result?
6. **What do the programs `PGMMAIN` calls read and write?** They are not in the tree. Which datasets,
   DB2 tables or queues do they touch, and which of those feed the nightly cycle's reports and partner
   extracts? A called subprogram gets no DDs from its caller's step in this extractor.
7. **Is anything else part of this system that the plugin does not read?** It reads COBOL, copybooks,
   JCL, PROCs, CICS system definitions, Control-M XML and shell wrappers that name JCL. It does not
   read IMS, DB2 stored procedures, MQ, assembler or a job submitted through the internal reader.
   The extractor listed no file as not parsed.
8. **Is there a behavioral oracle?** Archived generations of reports and extracts, job logs, SMF
   records and partner extracts from the nightly cycle. See `06-test-strategy.md`.
9. **Does the team have someone who can read COBOL and JCL?** The estimate depends on it
   (`04-estimate.md`).
10. **Is this tree the whole system?** Two programs and one job is small for a batch cycle. Is this a
    slice, and if so which slice?

## Limits from the extractor that touch this system

- A variable call target is resolved only from `VALUE` clauses and literal `MOVE`s in the same
  program. `PGMMAIN` has neither, so the call stays open.
- A called subprogram gets no DDs from its caller's JCL step.
- `IF/THEN/ELSE` and `COND=` in JCL are not modeled, and step order is file order. The job has one
  step, so this does not change the graph here (`app/jcl/MAINJOB.jcl:2`).
- Nested PROC calls, `INCLUDE` members and jobs submitted through the internal reader are not
  followed.
- `EXEC CICS RETURN TRANSID`, `START` and `SEND MAP` are not edges.
- Only Control-M XML and shell wrappers that name JCL files are read as schedulers. None was found.
- The tree is not a git checkout, so no unit has a last-modified date. The dormant bucket is empty
  for that reason and not because the code is recent.

Extractor warning, quoted as it stands: one JCL job is in the tree but no scheduler artifact was
parsed, so the order jobs run in across jobs is unknown.
