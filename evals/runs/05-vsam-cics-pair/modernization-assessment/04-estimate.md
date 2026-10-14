# Estimate

**Basis: both cases are shown, because `--delivery` was not given.** Conventional means a team with no AI coding assistance. AI-assisted means engineers using an AI coding agent with human review. This plugin carries no calibrated productivity data. Every rate below is a planning assumption, not a benchmark. The team's measured velocity from wave 1 replaces it.

The code is 22 lines of COBOL and a 3-line copybook (app/cbl/PROGR.cbl:11, app/cbl/PROGW.cbl:11, app/cpy/ACCTREC.cpy:3). Authoring is not where the time goes. The oracle, approvals and cutover are.

| Wave | Term | Conventional | AI-assisted | Does AI shrink it? | Evidence |
|---|---|---|---|---|---|
| 1 | Port PROGR | 1 to 2 days | under 1 day | Yes. Transliteration with a harness. | app/cbl/PROGR.cbl:7 |
| 1 | COMP-3 decode and record harness | 3 to 5 days | 2 to 4 days | Partly. Choosing the boundary is human work. | app/cpy/ACCTREC.cpy:3 |
| 1 | Oracle, rehearsal, cutover | 1 to 2 weeks | 1 to 2 weeks | No. Needs a production file extract and client availability. | inference |
| 2 | Port PROGW | 2 to 3 days | 1 day | Yes. | app/cbl/PROGW.cbl:7 |
| 2 | Write-path harness, dual-write or reconcile | 1 to 2 weeks | 1 week | Partly. | inference |
| 2 | Oracle, rehearsal, cutover, KSDS retirement | 2 to 3 weeks | 2 to 3 weeks | No. | inference |

Totals, as ranges: **conventional about 5 to 8 engineer-weeks, AI-assisted about 4 to 7 engineer-weeks, across both waves.** The AI case saves little because most of the cost is in terms AI does not shrink.

## Assumptions the range is most sensitive to

1. Assumes ACCTDAT has exactly these two users. If a batch job or another transaction also reads or loads it, the contract has a third party and wave 2 roughly doubles. Nothing in the tree shows one, but nothing in the tree shows the batch cycle either (modernization-assessment/00-summary.md).
2. Assumes a production extract of ACCTDAT can be had. If it cannot, the oracle must be built from synthetic records and the harness term grows by a week or more.
3. Assumes AI-assisted review takes about a quarter of the authoring time it replaces. For 22 lines this is hours either way.

## Where an AI agent helps and where it does not

- Strong: transliterating the two CICS READ and WRITE calls, and generating record-comparison tests once the layout is fixed.
- Weak: the intent behind the balance field. The tree holds no arithmetic, sign rule or rounding rule. Those must come from the client's engineers.
