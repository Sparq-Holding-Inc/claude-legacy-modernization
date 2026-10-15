---
description: Assess a COBOL, CICS, JCL and VSAM codebase for modernization. Scripts extract the coupling graph. Claude cuts the waves and scores the risk.
argument-hint: '[path] [--target rehost|replatform|refactor|rewrite] [--must-not-break "text"] [--telemetry none|partial|provided] [--delivery conventional|ai-assisted|agent-led] [--wave N]'
allowed-tools:
  - 'Bash(python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/extract.py" *)'
  - 'Bash(python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/render.py" *)'
  - 'Bash(python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/marker.py" *)'
  - 'Bash(python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/schema.py" *)'
  - 'Bash(python3 "${CLAUDE_PLUGIN_ROOT}/hooks/check_citations.py" *)'
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

1. Once the scope is settled, start the run marker. It turns on the citation check for this run only.
   `<scope>` is the folder path, or `.` when none was given. It is not the target state.

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/marker.py" start --scope <scope>
   ```

2. Follow the `modernization-assessment` skill from Step 0 to Finish. Write every artifact to
   `./modernization-assessment/`. The skill ends by marking the run done. Do not delete the marker
   yourself. The citation check removes it after it passes. If the stop hook does not run in your
   environment, the marker stays at `done`. That is harmless.

3. Finish by printing a short summary in the conversation: the wave count, the single largest risk
   you found, and the top three open questions for the client's engineers.

## With --wave N

The full artifacts must already exist in `./modernization-assessment/`. If `graph.json` is
missing, say so and stop. Start the marker with `--mode wave`:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/marker.py" start --scope <scope> --mode wave
```

Read `graph.json`, `waves.json` and `risks.json`. Write `07-wave-N-plan.md` for wave N only, with
citations: the program-by-program port order, the test harness for that wave's boundary (use the
`behavioral-equivalence` skill), and the rollback procedure. Then run `marker.py done` and print a
short summary.
