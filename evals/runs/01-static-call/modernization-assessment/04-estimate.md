# 04 Estimate

**Basis: no `--delivery` was given, so both cases are shown, conventional and AI-assisted.** This plugin carries no calibrated productivity data. Every rate here is a planning assumption, not a benchmark. Replace it with the team's measured velocity.

The tree is 11 lines of COBOL in two programs (app/cbl/PROGA.cbl:7, app/cbl/PROGB.cbl:4). There are no waves to estimate per wave, so this is one estimate for the whole tree.

| Term | Conventional | AI-assisted | AI assumption | Confidence | Evidence |
|---|---|---|---|---|---|
| Understanding | 0 days, already done here | 0 days | This assessment covers it | high | modernization-assessment/graph.json:36 |
| Port of two programs | 0.5 to 1 day | 0.25 to 0.5 day | Review takes about as long as writing 11 lines | medium | app/cbl/PROGA.cbl:7 |
| Boundary and harness | 1 to 3 days | 1 to 2 days | Choosing the boundary does not shrink | low | inference |
| Oracle, approvals, rehearsal, cutover | 2 to 10 days | 2 to 10 days | Does not shrink with AI | low | inference |

Total: roughly 3.5 to 14 days conventional, 3.25 to 12.5 days AI-assisted. This is a wide range because the real cost is the nightly cycle, which is not in the tree.

## What the range is most sensitive to

1. Assumes the nightly batch cycle is only PROGA and PROGB. If it holds more programs, JCL or datasets, this estimate does not apply and must be redone from the supplied tree.
2. Assumes a parallel run or archived outputs exist as an oracle. If they do not, the oracle term can double.
3. Assumes no one needs to read COBOL beyond these two files.

## Where Claude Code helps

It is strong at transliterating these 11 lines with a harness. It cannot tell from the code why PROGA prints its message before the call (app/cbl/PROGA.cbl:5). That needs a person who knows the intent.
