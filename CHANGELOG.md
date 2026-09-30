# Changelog

## 0.2.0 (candidate, not released)

Facts now come from scripts. Judgment still comes from Claude.

Added
- An extractor in plain Python, standard library only. It reads COBOL, copybooks, JCL and PROCs,
  CICS system definitions, Control-M XML, and shell wrappers that name JCL files. It writes
  `graph.json`. Every edge cites a file and a line.
- Five edge kinds: call, include, data, contract, temporal. Contract edges pair a writer and a
  reader of the same dataset and say whether they share a layout copybook.
- Computed calls are kept as unresolved edges. They are never dropped.
- Graph facts computed by script: entry points, reachability, call cycles, articulation points,
  god modules, dataset hubs, and dead code candidates in three buckets.
- A wave seed. The extractor cuts a first plan from facts alone: every entry point goes in a family
  (read-only batch, batch writers, online writers, DB2 or IMS or MQ, and so on) in a fixed order.
  It writes `03a-wave-seed.md` and a draft `03a-waves-draft.json`. Claude names the waves and may
  change them only for a cited reason. Each change goes in `deviations`.
- JCL text inside a COBOL literal (a job that submits itself through the internal reader) is
  noticed. What it names is called unknown, never unreachable.
- Assembler, DB2 DDL, IMS DBD and PSB, DCLGEN and control card files are listed as not read.
- Three machine readable outputs next to the markdown: `waves.json`, `dead-code.json`,
  `risks.json`. One schema file checks all four JSON files.
- A Stop hook that blocks the finish of an assessment when a citation does not resolve. It runs
  only while an assessment is in progress. On a second failure it lets the stop through and
  writes the problems into the summary.
- `/modernize-scan` takes `--target`, `--must-not-break` and `--telemetry`, so it can run
  without questions.
- An eval harness: seeded fixtures with hand written truth, a draft truth file for AWS
  CardDemo, a mutation check that proves the fixtures can fail, and tests for the hook.
- A sample assessment of CardDemo in `examples/carddemo/`.
- `LICENSE` (Apache-2.0) and `NOTICE`.

Changed
- Scope narrowed to COBOL, CICS, JCL and VSAM. RPG, Oracle ADF, PL/SQL, .NET Framework and Java
  are removed from the description and keywords. They are on the roadmap, not in the plugin.
- The risk assessor writes `risks.json`. It scores two axes and the file is rejected if it holds
  a combined score.
- The README privacy and partner statements were rewritten.
- The marketplace file now has a description, so `claude plugin validate --strict` passes.

Kept, on purpose
- Two risk axes, never multiplied.
- Three dead code buckets, never two.
- Early waves maximize learning per unit of blast radius, not business value.

## 0.1.0

Prototype. Two skills, two subagents, one command, one manifest. The method was written down.
Nothing was extracted by script and nothing was tested.
