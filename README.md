# Legacy Modernization Assessor

A Claude Code plugin for the first two weeks of a legacy modernization program — the part
where you still don't know what you're dealing with.

Point it at a COBOL, RPG, Oracle ADF, PL/SQL, .NET Framework, or monolithic Java codebase.
It produces four artifacts an engineering leader can actually take into a steering meeting:

1. **A dependency map** — what calls what, which modules are load-bearing, and where the
   hidden coupling is (shared copybooks, global working-storage, database-mediated coupling,
   file-format contracts between jobs).
2. **A risk-ranked migration wave plan** — the codebase cut into waves that can ship
   independently, ordered so the cheap, low-blast-radius work funds and de-risks the rest.
3. **A behavioral-equivalence test strategy** — how you prove the new thing does what the
   old thing did, including where you *can't* prove it and what compensating control covers
   that gap.
4. **A dead-code and dark-logic register** — what looks unreachable, what looks reachable but
   is almost certainly dormant, and what to verify in production telemetry before deleting.

## Why this exists

Most modernization programs fail in the assessment phase, not the build phase. They fail
because the estimate is built on lines of code rather than on coupling, and because nobody
wrote down what "correct" means before the rewrite started. This plugin makes Claude do the
boring, high-value part: read all of it, and write down what it found.

## Install

```
/plugin marketplace add teamsparq/claude-legacy-modernization
/plugin install legacy-modernization
```

Or clone and load locally:

```
git clone https://github.com/teamsparq/claude-legacy-modernization
claude plugin validate ./claude-legacy-modernization
```

## Use

```
/modernize-scan                      # full assessment of the current repo
/modernize-scan src/batch            # scope it to a subtree
/modernize-scan --wave 1             # deep-plan a single wave after the first scan
```

Or just ask: *"assess this codebase for modernization"* — the skills trigger on their own.

## What's in it

| Component | Name | What it does |
|---|---|---|
| Command | `/modernize-scan` | Runs the full four-artifact assessment |
| Skill | `modernization-assessment` | The assessment method: inventory → coupling → waves → estimate |
| Skill | `behavioral-equivalence` | Designing the test harness that proves the port is correct |
| Agent | `dependency-cartographer` | Fans out across the codebase to build the coupling graph |
| Agent | `migration-risk-assessor` | Scores each module for blast radius and port difficulty |

## Scope and honesty

This plugin assesses. It does not port your code. It will tell you, in writing, where its
own analysis is low-confidence — static analysis of a 30-year-old batch system has real
limits, and a tool that hides those limits is worse than no tool.

Outputs are written to `./modernization-assessment/` as Markdown. Nothing is sent anywhere.

## About

Built and maintained by [Sparq](https://teamsparq.com), a Claude Partner Network services
partner. The method here is the front end of engagements we run; we open-sourced the
assessment because the assessment is the part everyone should be able to do for free.

Issues and PRs welcome. Apache-2.0.
