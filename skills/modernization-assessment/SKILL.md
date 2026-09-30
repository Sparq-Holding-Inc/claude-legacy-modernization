---
name: modernization-assessment
description: Assess a COBOL, CICS, JCL and VSAM codebase for modernization. Produces a dependency map with file and line evidence, risk-ranked migration waves, an effort estimate, and a dead-code register. Use when the user asks to assess, analyze, or plan a migration, rewrite, port, or modernization of a mainframe system, or asks "how hard would it be to rewrite this", "where do we start", "what is coupled to what", or "how do we break up this monolith".
---

# Modernization assessment

The goal is a document an engineering leader can take into a steering committee and defend.
Not a summary of the code. An argument about sequence, cost, and risk, with the evidence
attached.

## How the work is split

**Facts come from scripts. Judgment comes from you.**

A small Python extractor reads the source and writes `graph.json`. Every edge in it cites a file
and a line. It found the calls, the copybook includes, the dataset reads and writes, the record
layouts two programs share, and the job order a scheduler enforces. You do not re-derive any of
that by reading the tree.

You do the things a script cannot: how much business logic a program holds, whether its
arithmetic is sensitive, where the waves should be cut, what the risk really is, and what to do
about the edges the script gave up on.

Two rules follow.

1. **Never rebuild the graph by reading source.** Read source to make a judgment, or to settle an
   edge the extractor could not resolve.
2. **Every claim carries a `path:line` citation or the word `inference`.** A stop hook checks
   this. A citation that points at a file or line that does not exist blocks the finish.

## Before you start

Confirm three things with the user. Do not guess them. The `/modernize-scan` command can take
them as flags, so check what you were given before you ask.

1. **Target state.** Rehost, replatform, refactor, or rewrite? These give completely different
   wave plans. If the user does not know, that is a finding. Say so, and assess for refactor as
   the default, since it is the middle case. The words mean this. Rehost: the same code on new
   infrastructure or an emulator. Replatform: the same code and language, a new runtime or database.
   Refactor: the same behavior in restructured code, usually as services, in the same or a new language.
   Rewrite: new code written from the behavior, not from the source.
2. **What must not break.** Regulatory reports, month-end close, EDI partners, a downstream
   warehouse. Name them. They become the behavioral-equivalence anchors.
3. **Runtime telemetry.** Can they tell you which programs ran in the last 12 months? If yes, the
   dead-code register goes from speculation to evidence. If no, say clearly that every dead-code
   claim is provisional.

## Step 0. Run the extractor

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/extract.py" <target> --out modernization-assessment
```

Flags: `--as-of YYYY-MM-DD` and `--dormant-years N` (default 5) for the dormancy rule, `--no-git` to
skip git dates. It uses the Python standard library only. It makes no network calls. If `cloc` is
installed it uses it for line counts.

Then write the fact tables. These are generated, so their citations are correct by construction:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/render.py" inventory modernization-assessment/graph.json --out modernization-assessment/01-inventory.md
python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/render.py" edges modernization-assessment/graph.json --out modernization-assessment/02a-edge-tables.md
python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/render.py" deadcode modernization-assessment/graph.json --out modernization-assessment/05a-dead-code-candidates.md
python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/render.py" waveseed modernization-assessment/graph.json --out modernization-assessment/03a-wave-seed.md
python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/render.py" wavedraft modernization-assessment/graph.json --out modernization-assessment/03a-waves-draft.json
```

Now read `graph.json`. Start with the `analysis` block. It already holds:

- `entry_points`, `reachable_nodes`, `reachable_programs`
- `dead_code_candidates` (unreachable, dormant, unknown) with `dead_code_reasons`
- `unresolved_dynamic`: every computed call the script could not resolve
- `embedded_jcl`: JCL text found inside a COBOL literal. The program can submit it at run time. The
  proc or program it names has no edge, so it is unknown, never unreachable
- `wave_seed`: a first cut of the waves, from facts alone (Phase 3)
- `sccs`, `self_recursive`, `articulation_points`, `god_modules`, `fan_in`, `fan_out`
- `data_hubs`: the datasets with the most programs attached
- `unscheduled_jobs`, `warnings` (read the warnings: a missing scheduler is a gap, not a detail)
- `structure_basis`: fan-in, cycles, articulation points and god modules are computed over reachable
  programs only, so dead callers do not distort them

Also read `unparsed` and `meta.limits`. A scheduler or source file the extractor could not parse
is not a footnote. It goes into Open Questions.

**Edge kinds and what they mean**

| Kind | Meaning |
|---|---|
| `call` | CALL, EXEC CICS LINK or XCTL, JCL EXEC PGM or PROC, a scheduler running a job |
| `include` | COPY, EXEC SQL INCLUDE, a job holding its steps |
| `data` | A program reads or writes a dataset, VSAM file, or DB2 table. Mode is read, write, or read_write |
| `contract` | Writer to reader of the same dataset. The record layout is an undocumented API |
| `temporal` | Order enforced by JCL step order, Control-M conditions, or a shell wrapper |

Confidence is `high`, `medium` or `low`. A `low` edge, or `resolved: false`, is one a human must
check. Node ids: programs are bare (`CBTRN02C`). Others carry a prefix: `cpy:`, `job:`, `step:`,
`proc:`, `ds:`, `sch:`, `map:`, `ext:`. A computed call points to `?dynamic:PROGRAM:LINE`.

## Phase 1. Inventory

`01-inventory.md` is already written by `render.py`. Do not retype it. Read it for what is
surprising: an old copybook, a program with no last-modified date, a job no scheduler names.

Legacy systems hide behavior in JCL, shell wrappers, scheduler definitions, and stored procedures.
An assessment that counts only application source under-scopes by a wide and embarrassing margin.
The extractor reads COBOL, copybooks, JCL and PROCs, CICS system definitions, Control-M XML, and
shell wrappers that name JCL files. It does not read anything else. Whatever it lists as not
parsed, you must ask about.

## Phase 2. Coupling

`02a-edge-tables.md` holds every edge. Your file, `02-coupling.md`, holds the argument.

For anything the extractor left open, work the edges yourself if there are a few. If there are
more than about 20, hand them to the `dependency-cartographer` agent. Give it the path to
`graph.json`. What it reports back is inference. Label it that way and cite it.

Then think about what the coupling does to the sequence:

1. **Call coupling** is easy to see and easy to reason about.
2. **Data coupling** is where most migration plans break. Two programs share a VSAM file. The
   dependency is real and invisible in the call graph. Use `data_hubs`.
3. **Contract coupling** matters most. Program A writes a file and program B reads it by column
   offset. Nobody wrote the format down. `high` means both sides use the same layout copybook.
   `medium` means they do not, or the extractor could not tell. Every `medium` contract edge is a
   place a port silently breaks.
4. **Temporal coupling** lives in the scheduler, not in the code. A plan built without it is not a
   plan.

Write `02-coupling.md` with:

- the two or three coupling patterns that will most constrain the migration sequence, each
  with citations
- a Mermaid graph of the top-level clusters. Keep it at cluster level. A node-per-program graph
  of a real system communicates nothing and creates a false impression of rigor
- the strongly connected components (`sccs`). A wave plan that splits one is wrong. They move as a
  unit or not at all
- the god modules. They cannot move in one wave. They are strangled behind a facade, never ported
  wholesale
- the articulation points. They are the natural wave boundaries
- the honest boundary: the computed calls (`unresolved_dynamic`), and what they mean for the rest

## Phase 3. Waves

The extractor already cut a first plan from facts. Read `03a-wave-seed.md`. Start from
`03a-waves-draft.json`. It puts every entry point in one family, in this fixed order:

1. batch jobs that touch no shared data and run no application program
2. read-only batch jobs
3. read-only online transactions
4. batch jobs with no application program that touch shared data (their writes are guesses)
5. batch jobs that write shared data
6. online transactions that write shared data
7. anything that touches DB2, IMS or MQ

A unit that several entry points use moves with the earliest family that uses it. A scheduler job
moves with the last family among the jobs it runs. A call cycle always moves whole.
Every unit is placed, or listed as not placed with a reason. Some families may be empty.

A wave is valid only if all four hold:

- it can be deployed independently, behind a flag or a facade
- it can be rolled back independently
- it has a testable boundary (you can assert equivalence at its edge)
- it delivers something a business stakeholder can name

Invoke the `migration-risk-assessor` agent first. Give it the path to `graph.json` and your
scoping answers. It writes `modernization-assessment/risks.json`.

Copy the draft to `waves.json`. Fill in what only you can: `target_state`, and for each wave its
`name`, `rationale`, `unblocks`, `blast_radius` and `confidence`. Keep the units, the wave order and
the `evidence` as they are. Say in the rationale why the family is a sound wave, or why it is not.
For each wave, say what it *unblocks*. A wave that unblocks nothing is a chore: say so.

Change the plan only for a reason you can cite. These are the reasons that count:

1. A must-not-break item, a strongly connected component or a facade dependency forces a unit
   into another wave. Dependency wins over risk quadrant. A high-high unit that everything else
   depends on cannot go last, so say what you would put behind a facade to make it movable.
2. A wave holds more than 25 units and one argument needs it cut. Cut it at an articulation point
   from `analysis.articulation_points`, and name the point.
3. Something the extractor could not see changes what a unit is: a computed call, a file listed as
   not parsed, JCL text inside COBOL. Cite it.
4. `risks.json` puts a unit in high-high and its family puts it early. Move it to the last wave
   that does not break a dependency.

Do not invent waves. Do not merge waves for tidiness. Do not move a unit because of its name.
Record every change in `deviations`, with the unit, the wave it left, the wave it joined, the reason
and the evidence. A plan with no deviations is a fine answer.

Write `03-waves.md` and `waves.json`. A unit is a program, a JCL job (`job:`), a proc, or a scheduler
job. Steps, copybooks and datasets move with their owner, so do not list them. Every unit must be a
node id in `graph.json`. Every wave needs `evidence` or `"inference": true`. Once the plan exists, set
the `wave` field on each unit in `risks.json`.

```json
{
  "target_state": "refactor",
  "waves": [
    {
      "wave": 1,
      "family": "batch-readonly",
      "name": "Reference data batch",
      "units": ["CBACT01C", "job:READACCT"],
      "rationale": "Reads the account master, writes nothing shared. Proves the toolchain.",
      "unblocks": "The date copybook that waves 2 and 3 share.",
      "blast_radius": "low",
      "confidence": "medium",
      "evidence": [{"file": "app/cbl/CBACT01C.cbl", "line": 29}]
    }
  ],
  "unassigned": [{"id": "COSGN00C", "reason": "Part of a call cycle with the menu. Moves with wave 4."}],
  "deviations": [
    {"unit": "COBIL00C", "from_wave": 6, "to_wave": 4, "reason": "Facade dependency: COBIL00C feeds the posting cycle.",
     "evidence": [{"file": "app/cbl/COBIL00C.cbl", "line": 40}]}
  ]
}
```

`target_state` is one of `rehost`, `replatform`, `refactor`, `rewrite`, `unknown`. Wave numbers run
1 to N with no gaps. `blast_radius` is `low`, `medium` or `high`. The validator rejects a plan that
splits a strongly connected component. Units the seed did not place stay in `unassigned` with its
reason, unless a deviation places them.

## Phase 4. Estimate

Estimate per wave, and be explicit about the method. Do not produce a single number.

Give a range, and give the two or three assumptions the range is most sensitive to. State them as
falsifiable claims: "assumes the 41 batch jobs in wave 2 share one date handling copybook. If they
do not, wave 2 roughly doubles." That sentence is worth more than the number.

What moves the estimate, in rough order of weight:

- count and nature of the coupling edges crossing the wave boundary (not LOC)
- availability of a behavioral oracle (production data to replay, expected outputs on file)
- god modules inside the wave
- how much business logic lives in the database rather than the application
- whether the team has anyone who can read the source language

Say where Claude Code can do the mechanical port and where it cannot. It is strong at
transliteration with a good test harness. It is weak at inferring intent from undocumented business
rules. Name which parts are which.

Write `04-estimate.md`.

## Phase 5. Dead code

Three buckets, never two. The extractor computed the candidates. Start from `dead_code_candidates`.

- **Unreachable.** No static path from any entry point, and no reachable code makes a computed call.
  Safe to propose for deletion.
- **Reachable but dormant.** Reachable on paper, but not modified for N years and no telemetry.
  Propose for *instrumentation*, not deletion.
- **Unknown.** Not reached statically, but a computed call in reachable code could target it. Flag
  it loudly. A confident dead-code claim over a computed call is how you delete something that runs
  once a year at fiscal close.

**You may not move a program from unknown to unreachable.** The validator rejects it. If you find
evidence that an extractor bucket is wrong, for example a run-time submit it could not see, move the
item toward unknown, never away from it, cite the evidence, and add no keys to `dead-code.json`. If you can
bound a computed call (the value comes from a table you can read), say so in the reason, and leave
the program in unknown.

Dormant means old, not unused. If a live program calls a dormant program unconditionally, it very
likely runs. Say that in the reason. Keep the extractor's dormant list as it is, and never propose
deletion on a date alone.

A job that no parsed scheduler names still counts as an entry point, so it never shows in a bucket.
Read `unscheduled_jobs` and the warnings, and ask whether those jobs still run. If a warning says
dormancy was not computed, say that in `05-dead-code.md`. An empty dormant list then means not measured.

If the user gave you telemetry, use it to firm up dormant and unknown. If not, every claim is
provisional and you say so.

Write `05-dead-code.md` and `dead-code.json`.

```json
{
  "telemetry": "none",
  "unreachable": [
    {"id": "cpy:UNUSED1Y", "reason": "No program includes it.", "confidence": "high",
     "evidence": [{"file": "app/cpy/UNUSED1Y.cpy", "line": 1}]}
  ],
  "dormant": [],
  "unknown": [
    {"id": "CBTRN01C", "reason": "No JCL step runs it. Computed calls could reach it.", "confidence": "low",
     "evidence": [{"file": "app/cbl/CBTRN01C.cbl", "line": 1}]}
  ]
}
```

All three keys must be present, even when a list is empty. `telemetry` is `none`, `partial` or
`provided`. The ids come from `graph.json`.

## Output discipline

- Every claim carries a `path:line` citation or is labeled `inference`.
- Any table of findings has a column headed exactly `Evidence`. A row with no citation says `inference`.
- Cite paths from the project root. A file inside the assessment folder is cited as
  `modernization-assessment/waves.json:2`. A fact computed in `graph.json`'s `analysis` block has no
  source line: cite the source line behind it, or write `analysis` in the Evidence cell and name the field.
- Keep a **Confidence** column. Low-confidence findings are not omitted. They are the ones the
  humans need to go verify.
- Write `00-summary.md`: the scoping answers, the wave count, the single largest risk, and an
  **Open Questions** section addressed to the client's own engineers. Fewer than five items on a
  system of any size means you were not looking hard enough. Include every file the extractor
  listed as not parsed, and every limit in `meta.limits` that touches this system.

## Finish

Hand off to the `behavioral-equivalence` skill and write `06-test-strategy.md`. An assessment
without a definition of "correct" is a wish. If the tree holds no datasets, say the oracle has to
come from job output, logs and reports, and say what you would ask the client to supply.

Then check your work. The first command checks the four JSON files. The second checks every citation
in the markdown, the same way the stop hook will:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/schema.py" validate-dir modernization-assessment
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/check_citations.py" --check modernization-assessment
```

Fix every problem. Then mark the run done, so the citation check runs when you finish:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/marker.py" done
```
