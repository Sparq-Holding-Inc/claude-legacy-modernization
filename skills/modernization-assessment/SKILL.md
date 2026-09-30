---
name: modernization-assessment
description: Assess a legacy codebase for modernization and produce a dependency map, risk-ranked migration wave plan, effort estimate, and dead-code register. Use when the user asks to assess, analyze, or plan a migration, rewrite, port, or modernization of an existing system — especially COBOL, RPG, JCL, Oracle ADF, PL/SQL, VB6, .NET Framework, WebForms, Struts, or a monolithic Java/C# application. Also use when the user asks "how hard would it be to rewrite this", "where do we start", "what's coupled to what", or "how do we break up this monolith".
---

# Modernization assessment

The goal is a document an engineering leader can take into a steering committee and defend.
Not a summary of the code. An argument about sequence, cost, and risk, with the evidence
attached.

## Before you start

Confirm three things with the user. Do not guess them.

1. **Target state.** Rehost, replatform, refactor, or rewrite? These produce completely
   different wave plans. If the user doesn't know, that's a finding — say so, and assess
   for refactor as the default, since it's the middle case.
2. **What must not break.** Regulatory reports, month-end close, EDI partners, a downstream
   warehouse. Name them. These become the behavioral-equivalence anchors.
3. **Runtime telemetry availability.** Can they tell you which programs actually ran in the
   last 12 months? If yes, the dead-code register goes from speculation to evidence. If no,
   say clearly that every dead-code claim is provisional.

## Phase 1 — Inventory

Walk the tree. Build a table of every compilable/executable unit with:

- path, language, LOC, cyclomatic complexity where derivable
- last modified date (via `git log` if available — age is a strong dormancy signal)
- unit type (online transaction, batch job, copybook/include, stored procedure, screen/form,
  scheduler artifact, data definition)

Do not stop at source. Legacy systems hide behavior in JCL, shell wrappers, cron, scheduler
definitions (Control-M, Autosys), database triggers, and stored procedures. A modernization
plan that only counts application source under-scopes by a wide and embarrassing margin.

Write `modernization-assessment/01-inventory.md`.

## Phase 2 — Coupling

Delegate to the `dependency-cartographer` agent for anything over ~200 units; do it inline
below that. You are looking for four kinds of coupling, in increasing order of how much
trouble they cause:

1. **Call coupling** — A invokes B. Easy to find, easy to reason about.
2. **Data coupling** — A and B both read/write table T or file F. Harder: the dependency is
   real but invisible in the call graph. This is where most migration plans break.
3. **Contract coupling** — A writes a fixed-width file that B parses by column offset. The
   format *is* an API, and nobody wrote it down.
4. **Temporal coupling** — B is correct only if A ran first, enforced by nothing but the
   scheduler. Find these in JCL/scheduler definitions, not in code.

For each, record the evidence (file and line) so a skeptical architect can check you.

Then identify **articulation points**: units whose removal disconnects the graph. These are
your natural wave boundaries. Also identify **god modules** — high fan-in and high fan-out.
These cannot be moved in any single wave and need to be strangled, not ported.

Write `modernization-assessment/02-coupling.md` with a Mermaid graph of the top-level
clusters. Keep the diagram to the cluster level; a 400-node graph communicates nothing.

## Phase 3 — Waves

Cut the system into waves. A wave is valid only if all four hold:

- it can be deployed independently, behind a flag or a facade
- it can be rolled back independently
- it has a testable boundary (you can assert equivalence at its edge)
- it delivers something a business stakeholder can name

Order the waves by this rule: **earliest waves should maximize learning per unit of blast
radius.** Not by business value — that's the instinct, and it's wrong here. The first wave's
job is to prove the toolchain, the test harness, and the team's port velocity on something
that won't take down the month-end close. Business value leads in wave three.

For each wave, state explicitly what it *unblocks*. A wave that unblocks nothing and delivers
nothing is not a wave, it's a chore, and it should be merged into a neighbor.

Invoke the `migration-risk-assessor` agent to score modules before finalizing the cut.

Write `modernization-assessment/03-waves.md`.

## Phase 4 — Estimate

Estimate per wave, and be explicit about the method. Do not produce a single number.

Give a range, and give the two or three assumptions the range is most sensitive to. State
them as falsifiable claims — "assumes the 41 batch jobs in wave 2 share one date-handling
copybook; if they don't, wave 2 roughly doubles." That sentence is worth more than the number.

Drivers that actually move the estimate, in rough order of weight:

- count and nature of the coupling edges crossing the wave boundary (not LOC)
- availability of a behavioral oracle (production data to replay? expected outputs on file?)
- presence of god modules inside the wave
- how much business logic lives in the database rather than the application
- whether the team has anyone who can read the source language

Note where Claude Code can do the mechanical port and where it cannot. It is strong at
transliteration with a good test harness and weak at inferring intent from undocumented
business rules. Say which parts are which.

Write `modernization-assessment/04-estimate.md`.

## Phase 5 — Dead code

Three buckets, never two:

- **Unreachable** — no inbound edge from any entry point. Safe to propose for deletion.
- **Reachable but dormant** — reachable on paper, but no modification in N years and no
  telemetry. Propose for *instrumentation*, not deletion.
- **Unknown** — reflection, dynamic call, `EXEC CICS LINK` with a computed program name,
  `CALL WS-PROGRAM-NAME`. Flag loudly. Dynamic dispatch defeats static analysis, and a
  confident dead-code claim over a dynamic call is how you delete something that runs once
  a year at fiscal close.

Write `modernization-assessment/05-dead-code.md`.

## Output discipline

- Every claim carries a file:line citation or is labeled an inference.
- Maintain a **Confidence** column. Low-confidence findings are not omitted — they are the
  ones the humans need to go verify, and hiding them is the worst thing this tool could do.
- Close the assessment with an **Open Questions** section addressed to the client's own
  engineers. If it's shorter than five items on a system of any size, you weren't looking
  hard enough.

Then hand off to the `behavioral-equivalence` skill to design the test strategy. The
assessment is not finished without it — a migration plan with no definition of "correct"
is a wish.
