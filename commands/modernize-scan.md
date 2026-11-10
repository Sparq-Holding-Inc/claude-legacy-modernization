---
description: Assess a COBOL, CICS, JCL and VSAM codebase for modernization. Claude reads the source with grep recipes, cuts the waves and scores the risk. Every claim cites a file and line.
argument-hint: '[path] [--target rehost|replatform|refactor|rewrite] [--must-not-break "text"] [--telemetry none|partial|provided] [--delivery conventional|ai-assisted|agent-led] [--wave N]'
allowed-tools: Read, Grep, Glob, LS
---

Assess the codebase with the `modernization-assessment` skill. Then run the
`behavioral-equivalence` skill.

Arguments you were given: `$ARGUMENTS`

## Read the arguments

- The scope is the first argument that is not a flag and is not the value of a flag. In
  `--target refactor`, the word `refactor` is a value, not a scope. If there is no scope, assess the
  current directory.
- `--target` is the target state: `rehost`, `replatform`, `refactor` or `rewrite`.
- `--must-not-break` is a quoted list of what must not break.
- `--telemetry` says whether runtime telemetry exists: `none`, `partial` or `provided`.
- `--delivery` says how the work will be done, for the estimate: `conventional` (no AI coding assistance),
  `ai-assisted` (engineers using an AI coding agent) or `agent-led` (an agent does most of the port, people
  review). It is optional and it is not a scoping question. If it is missing, the estimate shows both
  conventional and AI-assisted and says so. Record what you were given in `00-summary.md`.
- `--wave N` means: skip the assessment, read the existing `modernization-assessment/` folder, and
  plan wave N in detail. See the last section.

## Scoping questions

The assessment needs three answers: target state, what must not break, and whether telemetry
exists. Ask only for the ones you were not given as flags. If all three came as flags, ask
nothing. Do not proceed on assumptions in an interactive session. The answers change the output.

In a non-interactive session nobody can answer. Use these defaults and say so in
`00-summary.md`: target `refactor`, must-not-break `not stated`, telemetry `none`. If all three came
as flags, write `no defaults applied`.

## Run

1. Once the scope is settled, follow the `modernization-assessment` skill from Step 0 to Finish.
   `<scope>` is the folder path, or `.` when none was given. It is not the target state. Write every
   artifact to `./modernization-assessment/`. Claude asks your permission before it writes there.

2. The skill ends by running the `citation-verifier` agent over the folder and fixing what it
   reports. Do not skip it. Nothing else checks the citations.

3. Finish by printing a short summary in the conversation: the wave count, the single largest risk
   you found, and the top three open questions for the client's engineers.

## With --wave N

The full artifacts must already exist in `./modernization-assessment/`. If `graph.json` is
missing, say so and stop.

Read `graph.json`, `waves.json` and `risks.json`. Write `07-wave-N-plan.md` for wave N only, with
citations: the program-by-program port order, the test harness for that wave's boundary (use the
`behavioral-equivalence` skill), and the rollback procedure. Run the `citation-verifier` agent over
`07-wave-N-plan.md`, fix what it reports, and print a short summary.
