# 04 Estimate

Target state is `refactor`, the same behavior in restructured code. Every figure below is
`inference`. There is no history of this team's port velocity, and the tree is 16 lines of source
(`modernization-assessment/graph.json:24`, the `files_seen` block, and `01-inventory.md`).

## Method

Effort follows the number of coupling edges that cross the wave boundary, not lines of code. For
wave 1 that number is one, and it is the open one: the computed CALL at `app/cbl/PGMMAIN.cbl:9`. The
lines of code contribute almost nothing. What the effort is made of is discovery and the oracle.
I estimate the three parts separately and give a range for each, in person-days.

## Wave 1 (`job:MAINJOB`, `PGMMAIN`)

| Part | Range (person-days) | Confidence | Evidence |
|---|---|---|---|
| Port the two units and put a facade around the computed CALL | 1 to 3 | medium | `app/cbl/PGMMAIN.cbl:9` |
| Build the equivalence harness and the oracle (job outputs archived) | 2 to 5 | low | inference |
| Build the harness from characterization tests only (nothing archived) | 4 to 10 | low | inference |
| Discovery: bound the callee set, confirm what the nightly cycle is | 1 to 3, client engineer time | low | `app/cbl/PGMMAIN.cbl:8` |
| **Wave 1 total, outputs archived** | **4 to 11** | low | inference |
| **Wave 1 total, nothing archived** | **6 to 16** | low | inference |

`HIDDEN01` is not in a wave. If the run-time input names it, porting it adds well under a day
(`app/cbl/HIDDEN01.cbl:4`, a four-line program that returns).

## The assumptions the range is most sensitive to

1. **The callee set is a short list, and every program on it is in the tree we were given.** If
   the run-time input can name a program that is not in this tree, wave 1 cannot be finished until
   that program is supplied, and the range above is open at the top. The call is at
   `app/cbl/PGMMAIN.cbl:9` and the value comes from `app/cbl/PGMMAIN.cbl:8`.
2. **The job's return code, plus at least one output the callee produces, is archived for a period
   that includes month end.** If it is not, the oracle drops to characterization tests, which encode
   what the source says. The harness part then roughly doubles, as the two harness rows show.
3. **`job:MAINJOB` is the whole nightly batch cycle.** The tree has one job and no scheduler
   (`analysis`, field `warnings`). If the cycle has other jobs, this estimate covers one of N, and
   the sequencing in `03-waves.md` will change with the other jobs' data edges.

## What the whole engagement would cost

I do not give a number. The nightly batch cycle that must not break has no visible mapping in this
tree (see `00-summary.md`, Open Questions). Estimating the system from a fragment of 16 lines would
be an invented figure. What I can say is where the cost will sit once the missing material arrives:
in the datasets and record layouts the cycle reads and writes, and in the equivalence harness, not
in the COBOL. `inference`

## Where Claude Code can do the port, and where it cannot

| Work | Claude Code | Confidence | Evidence |
|---|---|---|---|
| Transliterate `PGMMAIN` and `HIDDEN01` into the target language | Strong. Ten lines with no arithmetic and no files | high | `app/cbl/PGMMAIN.cbl:6` |
| Translate the computed CALL into a dispatch table | Strong, once someone gives it the list of names | medium | `app/cbl/PGMMAIN.cbl:9` |
| Say what value `WS-PGM-NAME` holds in production | Cannot. The value is input at run time and is not in the tree | high | `app/cbl/PGMMAIN.cbl:8` |
| Say what the callee does and what the business rule is | Cannot, if the callee is not in the tree. It infers intent poorly from undocumented rules | medium | inference |
| Build the harness | Strong at writing it, weak at choosing the oracle. That needs the client's archives and job logs | medium | inference |

Whether the client has anyone who reads COBOL is not known. It moves the estimate, and it is in the
Open Questions.
