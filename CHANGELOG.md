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
- The estimate states its basis and shows a conventional case and an AI-assisted case for every wave, with
  the reduction written as an assumption per term. `--delivery` picks which leads. Added after a reviewer
  asked whether the estimate assumed AI. It did not say. The sample in `examples/carddemo/` predates this.
- A wave seed. The extractor cuts a first plan from facts alone: every entry point goes in a family
  (read-only batch, batch writers, online writers, DB2 or IMS or MQ, and so on) in a fixed order.
  It writes `03a-wave-seed.md` and a draft `03a-waves-draft.json`. Claude names the waves and may
  change them only for a cited reason. Each change goes in `deviations`.
- The wave seed cuts a family into groups. Two entry points in a family are bound when both write the
  same dataset or run the same application program. Bound entry points share a wave. The rest form one
  independent wave, listed first. A reader is ordered after a writer but is not bound to it. This split
  the 55-unit batch writers wave on CardDemo into two. It was added after a real headless run cut that
  wave by hand and the other two runs did not. A coupled group can still be too big to ship as one wave.
- A totals row in a findings table now says `inference` in its Evidence cell. The citation hook had
  flagged a bare totals row in a real run. The wave seed table in `03a-wave-seed.md` gains a totals row.
- The wave seed keeps jobs together when a scheduler chains them (a wrapper script or a Control-M
  folder), in the latest family of the chain. A program that submits JCL through the internal reader
  counts as batch and owns what it submits.
- Facts inside utility steps: the datasets an IDCAMS card deletes, defines or loads, and the program
  an IMS `PARM` or a TSO `RUN PROGRAM` card names. They are not edges. They keep those programs out
  of the unreachable bucket and tell the wave seed which jobs write shared data.
- JCL text inside a COBOL literal (a job that submits itself through the internal reader) is
  noticed. What it names is called unknown, never unreachable.
- Assembler, DB2 DDL, IMS DBD and PSB, DCLGEN and control card files are listed as not read.
- Three machine readable outputs next to the markdown: `waves.json`, `dead-code.json`,
  `risks.json`. One schema file checks all four JSON files.
- A Stop hook that blocks the first finish of an assessment when a citation does not resolve. It runs
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
- The saved eval runs and the sample's full `graph.json` moved to
  [claude-legacy-modernization-evidence](https://github.com/Sparq-Holding-Inc/claude-legacy-modernization-evidence),
  copied byte for byte from commit `229de03`. This repo now holds the plugin and the code that tests it.
  `run_e2e_evals.py --score-only` reads the evidence repo. It stops without writing when it finds no runs,
  or when the source trees the runs assessed are missing.
- The fixture runner passes git only the variables it needs, not the caller's whole environment.
- `plugin.json` carries the directory listing fields: documentation, support and privacy links. The
  directory finds the icon without a field.
- The Python scripts drop their `#!/usr/bin/env python3` line. None is executable, and every caller
  runs them with `python3`.
- The eval provenance now describes the headless runs of 2026-10-14, including the two CardDemo runs
  where the citation hook skipped its check.

Kept, on purpose
- Two risk axes, never multiplied.
- Three dead code buckets, never two.
- Early waves maximize learning per unit of blast radius, not business value.

## 0.1.0

Prototype. Two skills, two subagents, one command, one manifest. The method was written down.
Nothing was extracted by script and nothing was tested.
