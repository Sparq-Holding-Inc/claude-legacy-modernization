# 04 Estimate

## Method

The estimate is per wave, as a range, and every number is inference. It is not measured and it does not come
from lines of code. The tree is 12 lines of COBOL and 5 lines of JCL, and a line count says nothing here
(`app/cbl/PGMA.cbl:4`, `app/jcl/SEQJOB.jcl:5`). I ranked the drivers in the order that moves the effort:

| Driver | What the tree shows | Effect on wave 1 | Evidence |
|---|---|---|---|
| Coupling edges that cross the wave boundary | None. There is one wave and no dataset, so nothing crosses it. | Lowers the estimate | `analysis` field `edge_counts` |
| A behavioral oracle | None in the tree. No dataset, log or report is present. | Raises it. This is the largest cost. | inference |
| God modules in the wave | None. | Neutral | `analysis` field `god_modules` |
| Business logic held in the database | Unknown. No SQL is in the programs. | Unknown | `app/cbl/PGMA.cbl:3` |
| Someone who can read the source language | Unknown. Not stated. | Unknown | inference |

## Wave 1 range

| Piece of work | Range in person-days | Confidence | Evidence |
|---|---|---|---|
| Port PGMA, PGMB and PGMC | under 1 | medium | `app/cbl/PGMA.cbl:4`, `app/cbl/PGMB.cbl:4`, `app/cbl/PGMC.cbl:4` |
| Port the job: step order, return codes, the step name rule | 1 to 3 | low | `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5` |
| Build the oracle and the harness: collect logs and outputs, agree the normalization spec, run the comparison | 3 to 10 | low | inference |
| Total for wave 1 | about 5 to 14 | low | inference |

There is one wave, so the total for the assessment is the same range. Do not read it as a quote. It is what
this tree supports, and the tree is thin.

## The assumptions this range is most sensitive to

1. **The programs in the tree are the programs that run.** The range assumes PGMA, PGMB and PGMC really are
   no-ops. If production runs programs with real logic and real files, this range does not apply at all.
   The estimate would have to be redone from the real source, and it would likely be several times larger.
   That is the assumption that matters most. Each program is four lines with only `GOBACK`
   (`app/cbl/PGMA.cbl:4`, `app/cbl/PGMB.cbl:4`, `app/cbl/PGMC.cbl:4`).
2. **The client can supply job logs with return codes for SEQJOB for at least 13 months.** If only the last
   few weeks exist, the harness effort roughly doubles, because month-end and year-end cases must be built by
   hand. Nothing in the tree gives a log (`analysis` field `warnings`).
3. **The repeated step name STEP2 is a defect in this copy, not a feature of production.** If production
   really runs a name collision, the port needs a step identity rule and a restart rule, and the job port
   grows by 2 to 4 days (`app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5`).

## Where Claude Code helps, and where it does not

| Task | Claude Code | Evidence |
|---|---|---|
| Transliterate PGMA, PGMB, PGMC | Strong. Each is a single `GOBACK`, so this is mechanical. | `app/cbl/PGMA.cbl:4` |
| Reproduce the step sequence in the target's orchestrator | Strong once the step name rule is decided by a human. | `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:5` |
| Say what the nightly cycle is for | Weak. Nothing is written down, and the tree has no comment, schedule or dataset that shows intent. | inference |
| Decide whether the second STEP2 is a defect | Weak. It is a client decision. | `app/jcl/SEQJOB.jcl:5` |
| Build the comparison harness once outputs exist | Strong, given a written normalization spec. | inference |

## A note on the target

The target is refactor: the same behavior in restructured code, often as services. The tree gives no reason
to split three no-op programs into services, since they share no code and no data (`analysis` fields
`fan_in`, `fan_out`). The choice of target will matter once the real programs arrive. That is inference.
