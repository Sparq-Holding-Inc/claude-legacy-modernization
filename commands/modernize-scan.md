---
description: Run a full modernization assessment of a legacy codebase — inventory, coupling map, wave plan, estimate, dead-code register, and test strategy.
argument-hint: "[path] [--wave N]"
---

Run a modernization assessment using the `modernization-assessment` skill, then the
`behavioral-equivalence` skill.

Scope: $1 (if empty, assess the whole repository).

If `--wave N` was passed, skip phases 1–2 by reading the existing
`modernization-assessment/01-inventory.md` and `02-coupling.md`, and produce a detailed
build plan for wave N only: the module-by-module port order, the test harness for that
wave's boundary, and the rollback procedure.

Before you begin, ask the user the three scoping questions the assessment skill requires —
target state, what must not break, and whether runtime telemetry is available. Do not
proceed on assumptions; the answers change the output substantially.

Write all artifacts to `./modernization-assessment/`. Finish by printing a short summary to
the conversation: wave count, the single largest risk you found, and the top three open
questions for the client's engineers.
