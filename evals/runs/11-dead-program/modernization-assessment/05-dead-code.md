# 05 Dead code

The extractor's candidates are in `05a-dead-code-candidates.md`. The machine-readable register is `modernization-assessment/dead-code.json`. I kept the extractor's buckets as they are and moved nothing.

**Every claim below is provisional.** Telemetry is `none`, so nobody has shown which programs ran in the last 12 months. Static reachability says what can run. It does not say what does run.

## Two limits on the register

- **The dormant bucket was not computed.** No file has a last-modified date, because the tree is not a git repository (analysis: `warnings`). The empty dormant list means not measured. It does not mean nothing is dormant. PGMMAIN and PGMLIVE are reachable on paper, and whether they have run in 5 years is not known.
- **No scheduler was parsed.** One JCL job is in the tree and no scheduler artifact names it (analysis: `warnings`). `unscheduled_jobs` is empty because the extractor only fills it when a scheduler was parsed (analysis: `unscheduled_jobs`), so an empty list here means not measured. Every job counts as an entry point, so `job:MAINJOB` cannot show up as dead in any bucket. Whether it still runs is an open question, not a finding.

## Unreachable

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| PGMDEAD | No job step, program or scheduler in the tree runs it, and there is no computed call that could reach it. Its one statement calls PGMLIVE, which stays live through PGMMAIN, so deleting PGMDEAD leaves the live path whole | medium | `app/cbl/PGMDEAD.cbl:1`, `app/cbl/PGMDEAD.cbl:4` |
| `cpy:UNUSED` | No program in the tree includes it | high | `app/cpy/UNUSED.cpy:1` |

Proposal: instrument first, then delete. Deleting PGMDEAD on static evidence alone is defensible for the tree as given. Two things keep it provisional. Telemetry is none. And an entry point outside this tree, such as another JCL library or a scheduler, could still run it.

A note on direction. PGMDEAD calls a live program, but a live program does not call PGMDEAD. Calling a live program does not make a program live (`app/cbl/PGMDEAD.cbl:4`, `app/cbl/PGMMAIN.cbl:4`).

## Reachable but dormant

Empty, and not measured. See the first limit above. Propose PGMMAIN and PGMLIVE for instrumentation, not deletion. Dormant means old, not unused, and PGMMAIN is called by a job step unconditionally (`app/jcl/MAINJOB.jcl:2`), so it very likely runs.

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| none | not computed: no last-modified dates | low | analysis: `dead_code_candidates.dormant` |

## Unknown

Empty. The tree has no computed call (analysis: `unresolved_dynamic`) and no embedded JCL (analysis: `embedded_jcl`), so nothing can reach an unreached program without a static edge. That is true of this tree only. A computed call in code outside it is invisible here.

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| none | no computed call or embedded JCL in the tree | medium | analysis: `dead_code_candidates.unknown` |

## What to ask

- Job history or SMF records for `job:MAINJOB`, PGMMAIN, PGMLIVE and PGMDEAD over the last 12 months.
- Whether any JCL library, scheduler, or CICS definition outside this tree names PGMDEAD or `cpy:UNUSED`.
- Source-control history or member timestamps, so the dormant bucket can be computed.
