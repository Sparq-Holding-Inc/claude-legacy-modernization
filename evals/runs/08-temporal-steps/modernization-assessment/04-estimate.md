# 04 Estimate

Method: one wave, sized by the edges that cross its boundary, not by lines of code. The system has
12 lines of COBOL and 5 lines of JCL (`modernization-assessment/graph.json` node field `loc`), so
line count says almost nothing.

| Wave | Range | Method | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Days, not weeks, for the tree as it stands | No edge crosses the boundary. Three empty programs and one five-line job. | low | `app/cbl/PGMA.cbl:4`, `app/jcl/SEQJOB.jcl:5` |

The range holds only if the tree is the whole system. I cannot show that. The two assumptions the
range is most sensitive to:

1. **Assumes the programs are as empty as they look.** Each body is one GOBACK
   (`app/cbl/PGMA.cbl:4`, `app/cbl/PGMB.cbl:4`, `app/cbl/PGMC.cbl:4`). If the real programs have logic that
   is not in this tree, the estimate says nothing about them, and the port effort could be weeks or months.
2. **Assumes the duplicate STEP2 (`app/jcl/SEQJOB.jcl:5`) is a copy error and the job order is the file
   order.** If the client's scheduler restarts or conditions on step names, the order rules are in a
   file I have not seen, and the test work for the job grows.

Other things that move the estimate, in the order the skill lists them:

| Driver | Finding | Confidence | Evidence |
|---|---|---|---|
| Coupling edges across the boundary | None | high | `analysis` field `edge_counts` |
| Behavioral oracle | Not in the tree. Job logs and return codes are the only candidate. | low | inference |
| God modules | None | high | `analysis` field `god_modules` |
| Business logic in the database | No DB2 or SQL in the tree | medium | `analysis` field `node_counts` |
| Team can read the source language | Not known | low | inference |

## Where Claude Code can help

It can transliterate the three programs and the job. That is mechanical, and there is no logic to
mis-port. It cannot tell you what the programs were meant to do, because they hold nothing. The
intent, if any, lives outside this tree.
