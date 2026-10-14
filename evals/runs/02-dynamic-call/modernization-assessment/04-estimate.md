# 04 Estimate

**Basis.** `--delivery` was not given, so both cases are shown. This plugin carries no calibrated productivity data. Every figure below is a planning assumption, not a benchmark.

No per-wave estimate is possible because there are no waves (`03-waves.md`). Sizing the code alone, there are 14 lines of COBOL in two programs (`app/cbl/PROGA.cbl:10`, `app/cbl/PROGB.cbl:4`).

| Item | Conventional | AI-assisted | Evidence |
|---|---|---|---|
| Port of PROGA and PROGB | inference: under 1 engineer-week | inference: under 1 engineer-day | `app/cbl/PROGA.cbl:10` |
| Oracle, approvals, cutover rehearsal for the nightly batch cycle | cannot be sized | cannot be sized, and AI does not shrink it | inference |

The port is trivial. The cost sits elsewhere: the unseen batch cycle around these programs. Both ranges are most sensitive to two assumptions:

1. Assumes PROGA's computed call targets only programs in a small known set. If it can load arbitrary programs, the unit cannot be sized (`app/cbl/PROGA.cbl:9`).
2. Assumes the nightly batch cycle is more than these two programs. If it is, the estimate comes from the JCL, not from this tree.

AI assistance helps with transliteration once a comparison harness exists. It cannot infer what `WS-PGM-NAME` will hold at run time (`app/cbl/PROGA.cbl:8`).
