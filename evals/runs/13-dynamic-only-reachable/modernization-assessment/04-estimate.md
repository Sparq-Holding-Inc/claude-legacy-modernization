# 04 Estimate

**Basis.** No `--delivery` flag was given, so every figure below is shown for two cases: conventional (no AI coding assistance) and AI-assisted (engineers with an AI coding agent, human review). This plugin carries no calibrated productivity data. Every rate is a planning assumption, not a benchmark. Measured velocity from the first harness run replaces it.

The estimate covers wave 1 only, because the tree has one wave (`modernization-assessment/waves.json:3`). It covers the files given: 14 lines of COBOL and 2 lines of JCL (`app/cbl/PGMMAIN.cbl:10`, `app/cbl/HIDDEN01.cbl:4`, `app/jcl/MAINJOB.jcl:2`). It does not cover whatever PGMMAIN calls at run time.

## Wave 1: nightly batch cycle (MAINJOB)

| Term | Conventional | AI-assisted | Does AI assistance shrink it? | Evidence |
|---|---|---|---|---|
| Port PGMMAIN and HIDDEN01 | 0.5 to 1 engineer-week | 0.25 to 0.5 | Yes. Transliteration of 14 lines is quick. Review is assumed to take as long as the authoring it replaces, because the dispatch design is a decision, not a transliteration. | `app/cbl/PGMMAIN.cbl:9` |
| Boundary work (how run-time dispatch is kept) | 1 to 2 | 0.75 to 1.5 | Partly. The code is quick. Choosing the boundary is not. | `app/cbl/PGMMAIN.cbl:8` |
| Equivalence harness (oracle, normalization spec) | 2 to 4 | 1.5 to 3 | Partly. The harness code is quick. Getting job output and the input list is client work. | inference |
| Rehearsal, approvals, cutover window | 1 to 3 | 1 to 3 | No. Calendar time and client availability. | inference |
| **Total** | **4.5 to 10** | **3.5 to 8** | | inference |

The range is wide because the tree is a fragment. The AI-assisted case saves about a week, not a multiple, since the smallest terms are the ones it shrinks.

## Assumptions the range is most sensitive to

1. Assumes the set of names PGMMAIN can call at run time is short and can be listed by the client. If the target set is open-ended, the harness and boundary terms at least double, and the estimate cannot be bounded.
2. Assumes the called programs are outside this estimate. If they are in scope, wave 1 grows by the size of every program on that list. No figure for that can be given from this tree.
3. Assumes the client can supply job output (reports, return codes, logs) for a full business cycle. If there is none, the oracle is the weaker characterization test and the harness term rises (see `06-test-strategy.md`).

## Where AI can and cannot do the work

| Task | AI-assisted port | Evidence |
|---|---|---|
| Transliterate PGMMAIN to the target language | Strong, with a harness | `app/cbl/PGMMAIN.cbl:6` |
| Decide what `ACCEPT` reads from and what the dispatch table holds | Weak. Intent is not in the source. The client must say. | `app/cbl/PGMMAIN.cbl:8` |
| Decide whether HIDDEN01 is live | Weak. No source shows who calls it. | `app/cbl/HIDDEN01.cbl:2` |

Discovery is not charged. The extractor and this run produced the dependency picture. What remains is the client's answers in `00-summary.md`.
