# 04 Estimate

**Basis:** `--delivery` was not given, so every figure shows two cases: conventional (no AI coding assistance) and AI-assisted (engineers using an AI coding agent, with human review). This plugin carries no calibrated productivity data. Every rate below is a planning assumption, not a benchmark. Replace it with the team's measured velocity after wave 1.

The numbers cover only what the tree shows: two no-op jobs and a 6-line wrapper (`jcl/JOBA.jcl:2`, `scripts/nightly.sh:4`). They are a floor. If the client's real nightly cycle lives outside the tree, the estimate is not valid (see sensitivities).

## Wave 1. Nightly batch cycle (target: refactor)

| Term | Conventional | AI-assisted | Does AI shrink it? | Confidence | Evidence |
|---|---|---|---|---|---|
| Understanding the code | 0 days | 0 days | Already done by this assessment. What remains is the client's answers. | high | `scripts/nightly.sh:1` |
| Port (JOBA, JOBB, wrapper to the target scheduler) | 1 to 3 days | 0.5 to 1.5 days | Yes. Transliteration of two IEFBR14 steps is trivial. Assumes review takes a quarter of the authoring time it replaces. | medium | `jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2` |
| Boundary work (keep order, keep `set -e` stop-on-failure) | 1 to 2 days | 1 to 2 days | Little. Choosing what the boundary is, is the work. | low | `scripts/nightly.sh:3` |
| Equivalence harness (see `06-test-strategy.md`) | 2 to 4 days | 1.5 to 3 days | Partly. The code is quick. The oracle is not. | low | inference |
| Oracle, approvals, rehearsals, cutover window | 3 to 10 days elapsed | 3 to 10 days elapsed | No. Client availability and a cutover window set this. | low | inference |
| JOBC retirement (confirm, instrument, delete) | 0.5 day plus one cycle of waiting | the same | No. Waiting is the cost. | medium | `scripts/nightly.sh:6` |

**Range for the wave:** conventional 7 to 19 engineer-days; AI-assisted 6 to 17. The spread is the same under both because the longest terms are elapsed time and approvals.

## Where an AI coding agent can and cannot help

| Work | Fit | Reason | Evidence |
|---|---|---|---|
| Rewriting the two job definitions and the wrapper in the target scheduler | Strong | Mechanical, and a comparison harness can check it | `scripts/nightly.sh:4` |
| Inferring what `submit` returns and when | Weak | The command is not in the tree, so it is guesswork | `scripts/nightly.sh:4` |
| Deciding if JOBB should run when JOBA fails | Weak | It is a business rule, not code | `scripts/nightly.sh:3` |

## Most sensitive assumptions

1. **Assumes the nightly cycle is only these two jobs.** If the jobs run real programs or load datasets that the tree omits, this estimate is a fraction of the true cost, and the wave count rises. A missing program set would likely multiply the figure by an order of magnitude (inference).
2. **Assumes `submit` returns non-zero when the job fails, so `set -e` stops the chain** (`scripts/nightly.sh:3`). If `submit` only reports that the job was accepted, JOBB runs regardless, and the target scheduler needs different dependency rules. The harness work roughly doubles.
3. **Assumes an oracle of archived job logs and return codes exists.** If not, the harness has to be built from characterization tests and the equivalence term gets a provisional label.
