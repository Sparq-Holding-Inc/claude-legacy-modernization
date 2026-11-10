# Sample assessment: AWS CardDemo

This folder holds one complete assessment produced by the plugin. It is here so you can see what the
output looks like before you run it on your own system.

**What was assessed.** AWS CardDemo, an open source COBOL, CICS, JCL and VSAM application built by AWS to
exercise modernization tools. Commit `59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e`. It is licensed under
Apache-2.0. See `NOTICE.md` at the top of this repo. CardDemo is a small, synthetic system. Do not read this
sample as a measure of what the plugin does on a large production estate.

**How it was produced.** By version 0.2.0 of this plugin, the scripted engine, not by this build. The engine extracted the graph with a Python parser and checked citations with a Stop hook. This build finds the same facts with grep recipes, so its output on the same tree can differ. The files here are kept as a sample of the output format and the depth of the argument. Model: Claude Sonnet 5.5.

**Which run this is.** Three runs were made in the last round. This is the one with the most citations that
all resolve, among the runs that passed every automatic check. The rule was written before the runs finished.
The other two runs of that round are in the scripted engine's evidence repository. Risk scores differ between runs.

**How much of the wave plan is Claude's.** Less than it looks. The extractor computes a first cut of the waves
from facts, and Claude named the waves and changed the plan in 2 place(s). Each change is in `deviations` in
`waves.json` with its reason. The three runs agree closely because they kept the same draft. That is
repeatability. It is not evidence that the wave boundaries are right. A mainframe engineer should read
`03-waves.md` before anyone relies on it.

**Paths in citations.** A citation such as `modernization-assessment/waves.json:365` points at a file in this folder. The run wrote its output to a folder with that name. Every other citation is a path inside the CardDemo checkout.

**The wave plan in this sample predates the group cut in the wave seed.** This plan has 7 waves. The current
plugin cuts the 55-unit batch writers family into groups, and its three headless CardDemo runs each made 9 waves.

**The estimate in this sample predates the two-case rule.** `04-estimate.md` is on a conventional basis and does
not show an AI-assisted case. The skill now asks for both, and states the basis in the first line.

**Read it with care.**
- The graph facts (`graph.json`, `01-inventory.md`, `02a-edge-tables.md`, `05a-dead-code-candidates.md`) come
  from the extractor. Every row cites a file and a line.
- The wave plan, risk scores, estimate and test strategy are Claude's judgment. Every claim cites a source line
  or says `inference`. They are opinions with reasons. A mainframe engineer may disagree.
- The CardDemo answer key used to grade the extractor is a draft that no domain reviewer has confirmed.

| File | What it is |
|---|---|
| `00-summary.md` | Scope, headline, and the open questions for the client's engineers |
| `01-inventory.md` | Every unit, its size and last change (generated) |
| `02-coupling.md` | The coupling patterns that constrain the sequence |
| `02a-edge-tables.md` | Every edge with evidence (generated) |
| `03-waves.md`, `waves.json` | The wave plan |
| `04-estimate.md` | Ranges and the assumptions they depend on |
| `05-dead-code.md`, `dead-code.json`, `05a-dead-code-candidates.md` | Three buckets |
| `06-test-strategy.md` | The behavioral-equivalence strategy |
| `risks.json` | Two scores per unit, never combined |
| `graph.json` | The full graph. At 560 KB it is kept in the [evidence repo](https://github.com/Sparq-Holding-Inc/claude-legacy-modernization-evidence/blob/main/examples/carddemo/graph.json), not here |
