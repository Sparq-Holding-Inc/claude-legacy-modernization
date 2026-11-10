# Legacy Modernization Assessor

A Claude Code plugin for the first two weeks of a mainframe modernization program. That is the part
where you still do not know what you are dealing with.

## Terms used in this README

| Term | Meaning |
|---|---|
| **Unit** | The smallest thing the plan moves: a program, a JCL job, a proc, or a scheduler job. Steps, copybooks and datasets move with their owner. |
| **Edge** | One dependency between two units, with the file and line that prove it. Kinds: `call`, `include`, `data`, `contract` and `temporal`. Together the edges are the dependency map (`graph.json`). |
| **Entry point** | Where work starts: a JCL job, a CICS transaction, or a scheduler job. Reachability is traced from here. |
| **Wave** | A group of units that ship together, in a set order. Each wave must deploy on its own, roll back on its own, have a boundary you can test, and be something a stakeholder can name. |
| **Blast radius** | How much breaks, and how far away, if a wave goes wrong. |
| **Dead code** | Code that may be safe to retire, in three buckets. Unreachable: no path from any entry point. Dormant: reachable on paper, but untouched for years. Unknown: a computed call could reach it. |
| **Computed call** | A call whose target is a variable, so a search cannot always see where it goes. |
| **Behavioral equivalence** | Proof that the new system does what the old one did. The test that proves it needs an oracle. |
| **Oracle** | The source of truth the new system is compared against, such as archived output from the old system. |
| **Citation** | A file and line that backs a claim. The `citation-verifier` agent checks that each one exists. |

Point the plugin at a COBOL, CICS, JCL and VSAM codebase. It produces what an engineering leader can take
into a steering meeting:

1. **A dependency map.** What calls what, which datasets are shared, which programs are bound
   together by a file layout nobody wrote down, and which jobs must run in order. Every edge cites a
   file and a line.
2. **A risk-ranked wave plan.** The system cut into waves that can ship on their own. Cheap,
   low-blast-radius work goes first, so it pays for the rest and teaches the team. A first cut comes
   from the graph. Claude explains it and can change it, with a cited reason.
3. **A dead code register.** Three buckets: unreachable, dormant, and unknown. Unknown is where a
   computed call could reach the code. Nothing is called dead over a call it cannot see.
4. **A behavioral-equivalence test strategy.** How you prove the new system does what the old one did,
   including where you cannot prove it.

The same results are written as JSON (`graph.json`, `waves.json`, `dead-code.json`, `risks.json`),
so another tool can read them.

## Why it works this way

Most modernization programs fail in the assessment, not the build. The estimate rests on lines of
code instead of coupling. Nobody wrote down what "correct" means before the rewrite started.

Asking a model to read a large mainframe estate and report what is coupled to what gives you
fluent text and no way to check it. So this plugin makes the work checkable:

- **Search recipes find the facts.** Claude runs fixed grep patterns for COBOL, JCL, CICS and
  scheduler files. Every hit is a file and a line, so every edge cites its source.
- **Claude makes the judgments.** How much business logic a program holds, where to cut the waves,
  what the real risk is, what to do about the edges a search could not resolve.
- **A second agent checks the citations.** When the assessment finishes, the `citation-verifier`
  agent opens every cited file and line. Claude fixes what it reports. If anything is still wrong
  after the second pass, the summary says so. A bad citation is made visible. It is not made impossible.

This build has no scripts and no hooks. Claude assembles the graph by reading search hits, so it is
slower and less certain than a parser. See "Where it is weak".

## Install

```
/plugin marketplace add Sparq-Holding-Inc/claude-legacy-modernization
/plugin install legacy-modernization@sparq
```

To try it from a local clone without installing, point Claude Code at the folder that holds
`.claude-plugin/`:

```
claude --plugin-dir <path to this folder>
```

Nothing else to install. Claude asks your permission before it writes `./modernization-assessment/`.

## Use

```
/legacy-modernization:modernize-scan                       # assess the current folder
/legacy-modernization:modernize-scan src/mainframe         # scope it to a subfolder
/legacy-modernization:modernize-scan --target refactor --must-not-break "month-end close, partner EDI" --telemetry none
/legacy-modernization:modernize-scan --wave 1              # plan one wave in detail, after the first scan
```

Claude asks three scoping questions: the target state (rehost, replatform, refactor or rewrite), what
must not break, and whether runtime telemetry exists. Pass all three as flags and it asks nothing.
You can also just ask: "assess this codebase for modernization".

Everything is written to `./modernization-assessment/`.

## Try it

Start with a small folder: a few COBOL programs, their copybooks and the JCL that runs them. A finished
assessment of a real benchmark is in `examples/carddemo/`. Read `00-summary.md` there first.

## What it reads

| Reads | Notes |
|---|---|
| COBOL source | Fixed format. Free format files are listed as not parsed. |
| Copybooks | Followed from `COPY` statements. |
| CICS | `EXEC CICS` LINK, XCTL and file I/O. The CICS system definition (CSD) gives entry points and the CICS file to dataset mapping. |
| JCL and PROCs | Steps, DDs, PROC expansion, symbolic parameters, DD overrides. |
| VSAM | Through `SELECT ... ASSIGN`, `OPEN` modes, CICS file I/O and JCL DDs. |
| Control-M | XML job definitions with conditions. |
| Shell wrappers | Scripts that name JCL files. |
| DB2 tables | Table references in `EXEC SQL` become data edges. |

Anything else that looks like a scheduler is listed as not parsed. It is never skipped in silence.

## Where it is weak

Read this before you trust it.

- **There is no parser.** Claude builds the graph from search hits and works fan-in, call cycles and
  articulation points by hand. On a large tree it partitions the work and labels what it could not
  compute across partitions as `inference`. Expect it to be slower, to cost more on big estates, and
  to miss edges a parser would find.
- **Nothing has been measured on this build yet.** The scores we published for version 0.2 describe
  the scripted engine, not this one. We do not carry them over.
- **A computed call stays unresolved.** The recipes resolve a variable target only from `VALUE`
  clauses and literal `MOVE`s in the same program. A menu table or a value from a queue is out of
  reach. The dead code register keeps everything that call could reach in the unknown bucket.
- **A called subprogram gets no DDs from its caller.** In a real run its files belong to the calling
  step. The recipes do not model that.
- **Utility steps take their dataset mode from `DISP`.** An IDCAMS `REPRO` target is `DISP=SHR` and
  is read as a read on the edge. IDCAMS `DELETE`, `DEFINE` and `REPRO` cards are read as separate
  facts. SORT cards and other in-stream input are not parsed.
- **Dormancy is not computed without dates.** Without git history or dates you supply, the dormant
  list is empty and the summary says it was not measured.
- **JCL `IF/THEN/ELSE` and `COND=` are not modeled.** Step order is file order.
- **`RETURN TRANSID`, `START`, `SEND MAP`, IMS and MQ are not edges.**
- **COPY `REPLACING` is not applied.**
- **The wave seed is crude.** It sorts entry points by what they write and where they run. It does
  not know your business. Claude and you are expected to argue with it.
- **A citation proves a line exists, not that it says what the claim says.** The verifier checks
  that the file and line are real and spot-checks that the line matches the claim. Whether the
  cited line supports the sentence is for a person to check.
- **The estimate is uncalibrated, and it is shown on two bases.** `04-estimate.md` gives engineer-weeks for a
  conventional team and for an AI-assisted team, and says which parts shrink with AI and which do not
  (getting the oracle, approvals, cutover). Every rate in it is Claude's planning assumption. The plugin carries
  no measured productivity data. Replace the rates with your team's measured velocity from the first wave.
  `--delivery conventional|ai-assisted|agent-led` picks which case leads the summary.
- **The judgment is Claude's.** Risk scores and every change to the wave seed are opinions with
  cited reasons. Two runs on the same tree can differ.

## Privacy

Outputs stay local. Nothing leaves beyond your own Claude session.

The plugin ships no code and makes no network calls. Claude reads the parts of your code that it
needs through your Claude session, the way it does in any Claude Code work.

## The scripted engine

Version 0.2 used a Python extractor and a Stop hook. That build is kept at the `v0.2.0` tag of this
repository, for people who can install scripts:
<https://github.com/Sparq-Holding-Inc/claude-legacy-modernization/tree/v0.2.0>. The sample assessment in
`examples/carddemo/` was produced by that engine.

## Roadmap

Not supported today: RPG, Oracle ADF, PL/SQL, .NET Framework, and Java. Each needs its own recipes
and its own benchmark. None is claimed until it has been measured.

## Support

The GitHub issue tracker is the primary support channel:
<https://github.com/Sparq-Holding-Inc/claude-legacy-modernization/issues>

Bug reports are most useful with the source dialect, the command you ran, and the contents of
`modernization-assessment/00-summary.md`. Do not paste client source into a public issue.

For anything that does not belong in a public issue, including a private report of a defect found
on a client estate, contact the maintainer directly.

- **Maintainer:** Phil Morehead, Sparq
- **Email:** phil.morehead@teamsparq.com

Issues are acknowledged within five business days.

## About

Sparq is a Select partner in the Claude Partner Network Services Track.

Issues and pull requests are welcome. Apache-2.0. See `LICENSE` and `NOTICE.md`.
