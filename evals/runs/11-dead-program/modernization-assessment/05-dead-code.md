# 05 Dead code

`05a-dead-code-candidates.md` holds the extractor's candidates. This file adds the judgment. `dead-code.json` holds the same three buckets in machine form.

**Telemetry is none.** Every claim here is provisional. Nobody has shown which programs ran in the last 12 months.

## Unreachable

| Unit | Confidence | Reason | Evidence |
|---|---|---|---|
| PGMDEAD | medium | No JCL step runs it, no program in the tree calls it, and the tree has no computed call that could reach it. Propose for deletion. Confidence is medium, not high: it is a batch main program that a job outside the tree could start, and telemetry is none. | `app/cbl/PGMDEAD.cbl:2`, `modernization-assessment/graph.json:159` |
| cpy:UNUSED | high | No program in the tree has a COPY of it. It holds one field of 10 bytes. Propose for deletion after the client confirms no out-of-tree program includes it. | `app/cpy/UNUSED.cpy:1` |

PGMDEAD calls PGMLIVE (`app/cbl/PGMDEAD.cbl:4`). PGMLIVE stays reachable through PGMMAIN (`app/cbl/PGMMAIN.cbl:4`), so deleting PGMDEAD does not orphan it. The extractor counts fan-in for PGMLIVE as 1 because it ignores dead callers (`modernization-assessment/graph.json:172`).

## Reachable but dormant

Empty. **This is an absence of data, not a finding.** The extractor had no git history, so every `last_modified` is null and the five-year rule could not run (`modernization-assessment/graph.json:7`, `modernization-assessment/graph.json:38`). A dormant list of zero must not be read as "everything was changed recently". Ask for source-control history or dataset last-referenced dates.

## Unknown

Empty. The tree has no computed call (`modernization-assessment/graph.json:171`), so nothing is held in this bucket for that reason. The bucket could fill if out-of-tree code makes a computed call (inference).

## What would firm this up

| Ask the client for | What it changes | Evidence |
|---|---|---|
| Twelve months of job logs or SMF records | Turns the PGMDEAD and cpy:UNUSED claims from provisional to evidence | inference |
| A scheduler export for every job that could run PGMDEAD | Confirms or refutes the unreachable claim | `modernization-assessment/graph.json:197` |
| Source-control history | Lets the dormant rule run over PGMMAIN and PGMLIVE | `modernization-assessment/graph.json:7` |
