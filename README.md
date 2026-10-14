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
| **Computed call** | A call whose target is a variable, so the extractor cannot always see where it goes. |
| **Behavioral equivalence** | Proof that the new system does what the old one did. The test that proves it needs an oracle. |
| **Oracle** | The source of truth the new system is compared against, such as archived output from the old system. |
| **Citation** | A file and line that backs a claim. The Stop hook checks that each one exists. |

Point the plugin at a COBOL, CICS, JCL and VSAM codebase. It produces what an engineering leader can take
into a steering meeting:

1. **A dependency map.** What calls what, which datasets are shared, which programs are bound
   together by a file layout nobody wrote down, and which jobs must run in order. Every edge cites a
   file and a line.
2. **A risk-ranked wave plan.** The system cut into waves that can ship on their own. Cheap,
   low-blast-radius work goes first, so it pays for the rest and teaches the team. The extractor
   proposes the cut from the graph. Claude explains it and can change it, with a cited reason.
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
fluent text and no way to check it. So this plugin splits the work:

- **Scripts find the facts.** A small Python extractor reads the source and builds the graph.
- **Claude makes the judgments.** How much business logic a program holds, where to cut the waves,
  what the real risk is, what to do about the edges the scripts could not resolve.
- **A hook checks the citations.** When the assessment finishes, a Stop hook checks that every cited
  file and line exists. It blocks the first stop and lists the bad ones. If they are still wrong on
  the second try, it lets the run end and adds an "Unresolved citations" section to the summary.
  A bad citation is made visible. It is not made impossible.

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

You need Python 3 on your path. The scripts use the standard library only. Nothing to install.

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

## What it reads

| Reads | Notes |
|---|---|
| COBOL source | Fixed format. Free format files are listed as not parsed. |
| Copybooks | Expanded, so a statement inside a copybook counts for every program that copies it. |
| CICS | `EXEC CICS` LINK, XCTL and file I/O. The CICS system definition (CSD) gives entry points and the CICS file to dataset mapping. |
| JCL and PROCs | Steps, DDs, PROC expansion, symbolic parameters, DD overrides. |
| VSAM | Through `SELECT ... ASSIGN`, `OPEN` modes, CICS file I/O and JCL DDs. |
| Control-M | XML job definitions with conditions. |
| Shell wrappers | Scripts that name JCL files. |
| DB2 tables | Table references in `EXEC SQL` become data edges. |

Anything else that looks like a scheduler is listed as not parsed. It is never skipped in silence.

## Where it is weak

Read this before you trust it.

- **It has been measured on one open source benchmark**, AWS CardDemo. The benchmark's answer key was
  labeled by Claude subagents reading the source. It has not been confirmed by a mainframe
  engineer. The scores in `evals/RESULTS.md` are provisional until that happens.
- **A computed call stays unresolved.** The extractor resolves a variable target only from `VALUE`
  clauses and literal `MOVE`s in the same program. A menu table or a value from a queue is out of its
  reach. It says so, and the dead code register keeps everything that call could reach in the
  unknown bucket.
- **A called subprogram gets no DDs from its caller.** In a real run its files belong to the calling
  step. The extractor does not model that.
- **Utility steps take their dataset mode from `DISP`.** An IDCAMS `REPRO` target is `DISP=SHR` and
  is read as a read on the edge. The IDCAMS `DELETE`, `DEFINE` and `REPRO` cards are read as separate
  facts (`utility_writes`), and the wave seed uses them. SORT cards and other in-stream input are not
  parsed. A card that uses a symbol such as `&HLQ` is skipped.
- **A program named at run time is a fact, not an edge.** IMS `PARM` and TSO `RUN PROGRAM` cards are
  read, so the program counts as reachable. Other drivers that start a program by name are not.
- **JCL `IF/THEN/ELSE` and `COND=` are not modeled.** Step order is file order.
- **`RETURN TRANSID`, `START`, `SEND MAP`, IMS and MQ are not edges.**
- **COPY `REPLACING` is not applied.**
- **The wave seed is crude.** It sorts entry points by what they write and where they run. It does
  not know your business. It puts a compile job and a posting job in neighboring families if both
  write shared data. Claude and you are expected to argue with it.
- **A citation proves a line exists, not that it says what the claim says.** The hook and the
  validators check structure: the file and line are real, the plan covers every unit, the dead code
  buckets agree with the extractor, and a risk's wave matches the plan. Whether the cited line
  supports the sentence is for a person to check.
- **The estimate is uncalibrated, and it is shown on two bases.** `04-estimate.md` gives engineer-weeks for a
  conventional team and for an AI-assisted team, and says which parts shrink with AI and which do not
  (getting the oracle, approvals, cutover). Every rate in it is Claude's planning assumption. The plugin carries
  no measured productivity data. Replace the rates with your team's measured velocity from the first wave.
  `--delivery conventional|ai-assisted|agent-led` picks which case leads the summary.
- **The judgment is Claude's.** Risk scores and every change to the wave seed are opinions with
  cited reasons. Two runs on the same graph can differ. `evals/RESULTS.md` says by how much.

## Privacy

Outputs stay local. Nothing leaves beyond your own Claude session.

The extractor makes no network calls. It is Python standard library only. Claude reads the parts of
your code that it needs through your Claude session, the way it does in any Claude Code work.

## Evals

`evals/RESULTS.md` holds the scorecard. `evals/README.md` explains how to run it. The sample
assessment of CardDemo is in `examples/carddemo/`.

## Roadmap

Not supported today: RPG, Oracle ADF, PL/SQL, .NET Framework, and Java. Each needs its own extractor
and its own benchmark. None is claimed until it has been measured.

## About

Sparq is a Select partner in the Claude Partner Network Services Track.

Issues and pull requests are welcome. Apache-2.0. See `LICENSE` and `NOTICE`.
