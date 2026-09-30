# 05 Dead code

Telemetry: none. Every claim in this file is provisional. There is no run history to firm up any bucket.

## The three buckets

The extractor computed no candidate for any bucket (`05a-dead-code-candidates.md`, `modernization-assessment/dead-code.json:1`).

| Bucket | Extractor result | Why | Confidence | Evidence |
|---|---|---|---|---|
| Unreachable | Empty | Every JCL job and the wrapper is an entry point, and the tree has no program, copybook or dataset that could sit behind them. | high | analysis field `dead_code_candidates` |
| Reachable but dormant | Empty, and **not measured** | The tree is not a git repository, so no unit has a last-modified date. The dormancy rule could not run. An empty list here means not measured. | high | analysis field `warnings` |
| Unknown | Empty | No computed call exists, so nothing is held open by one. | high | analysis field `unresolved_dynamic` |

`dead-code.json` has all three keys, each empty, and `telemetry` set to `none`.

## The one unit that needs a decision: job:JOBC

JOBC is in no bucket, and that is the extractor's rule doing its job, not a finding that it is live.

| Unit | Status | Confidence | Evidence |
|---|---|---|---|
| job:JOBC | An entry point that no parsed scheduler or wrapper runs. It is listed in `unscheduled_jobs`. The wrapper comment calls it retired, and the submit line is commented out. | low | `scripts/nightly.sh:2`, `scripts/nightly.sh:6`, `jcl/JOBC.jcl:1` |

What is fact and what is not:

- Fact: the wrapper does not submit JOBC. The submit line is commented out (`scripts/nightly.sh:6`).
- Fact: the file `jcl/JOBC.jcl` is still in the tree (`jcl/JOBC.jcl:1`).
- Claim, not proven: the comment says JOBC is retired (`scripts/nightly.sh:2`). It is a comment. It is
  not run history.
- Open: the JOBC job could still be run by hand, by another scheduler the tree does not hold, or by a
  job that submits it from inside another job (inference).

I did not put JOBC in `unreachable`. It is an entry point, so it is reachable by definition, and a
comment is not evidence to delete on. I did not put it in `unknown` either, because that bucket
is for units a computed call could reach, and none exists. I did not invent a fourth bucket. The
finding is carried in three other places: the Open Questions in `00-summary.md`, `do_not_port` in
`modernization-assessment/risks.json:104` (provisional, hold from the port), and the wave rationale.

**Proposal.** Instrument first. Ask the client for job run history for JOBC. If there are no runs for a
full business cycle including year-end, propose retirement. Do not delete on the comment.

## What the extractor could not see

- The extractor never opened whatever runs the wrapper (a scheduler, cron or an operator). A second
  wrapper or a scheduler that submits JOBC would not be in the tree (inference).
- `ext:IEFBR14` is a system utility outside the tree. It is not dead code and not in scope for removal
  (`jcl/JOBA.jcl:2`).
