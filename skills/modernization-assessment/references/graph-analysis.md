# Graph analysis

Procedures for turning the node list and edge table into structure. Follow them by hand with Read, Grep, Glob and LS. Every result is either counted from edge rows (cite the row or its source file:line) or labeled `inference`.

Conventions. Programs have bare ids (`PGMMAIN`). Other ids carry a prefix: `job:`, `step:`, `proc:`, `cpy:`, `ds:`, `ds:db2:`, `ds:dd:`, `sch:`, `ext:`. A computed call points to `?dynamic:PROGRAM:LINE`. Edge kinds: `call`, `include`, `data` (with mode read, write or read_write), `contract`, `temporal`. A program is any node of type online_txn, batch or subprogram. Only programs, JCL jobs, procs and scheduler jobs are units that a wave can hold.

## 1. Entry points and reachable nodes

Entry points are:
- every JCL job whose JCL file is in the tree (Grep `^//[A-Z0-9@#$]{1,8}\s+JOB\b`). A job that a scheduler also names is still an entry point;
- every scheduler job (Control-M job, Grep `MEMNAME=`) and every shell wrapper that submits JCL files in the tree;
- every program a CSD transaction names (Grep `DEFINE\s+TRANSACTION`, then read its `PROGRAM(...)`, which may sit on the next line). Cite the CSD line.

A job that exists only as a name in a scheduler, with no JCL file, is not an entry point.

Reachable nodes: start from the entry points and follow `call` and `include` rows only. Never follow `data`, `contract` or `temporal` rows. In practice:
- scheduler job to JCL job (call), job to its steps (include), step to program or proc (call);
- program to program (CALL, CICS LINK, XCTL), program to copybook (include), copybook to copybook;
- a proc runs through the step that invokes it. The programs inside it are reached by that job's expanded steps, so a proc nobody invokes reaches nothing;
- a program a step names at run time counts as called by that step. Two forms: the IMS region PARM of `DFSRRC00` (`DLI|DBB|BMP,PROGRAM,PSB`), and a TSO step's in-stream card `RUN PROGRAM(NAME)`. Only when the program is in the tree.

Example (JCL job MAINJOB, step S1 runs PGMMAIN, PGMMAIN calls PGMLIVE, PGMDEAD calls PGMLIVE):
```
job:MAINJOB -> step:MAINJOB.S1 include
step:MAINJOB.S1 -> PGMMAIN call
PGMMAIN -> PGMLIVE call
PGMDEAD -> PGMLIVE call
```
Reachable: job:MAINJOB, step:MAINJOB.S1, PGMMAIN, PGMLIVE. PGMDEAD calls a live program but nothing reaches PGMDEAD.

Method: write the entry list. Mark each. Repeat: for each marked node, Grep its rows as caller or container, mark the targets, until a pass marks nothing. Report "R of N programs reachable".

## 2. Fan-in, fan-out and god modules

Set P = programs reachable from an entry point. If the tree has no entry point, P = all programs and say so.

Count over `call` rows where caller and callee are both in P:
- skip self-calls (caller equals callee);
- skip rows to `ext:` and `?dynamic:` nodes, and JCL step rows;
- count distinct pairs. Calling twice from the same program counts once;
- a caller outside P (dead code) adds nothing.

fan-out(p) is the number of distinct callees. fan-in(p) is the number of distinct callers. The edge table holds one row per caller and callee pair, so Grep the call rows for the program as callee (`-c` gives the count), then subtract self-calls and callers outside P. Use zero for programs with none.

God module, exact rule:
1. If P has fewer than 10 programs, there are none.
2. Sort the fan-in values of every program in P (zeros included), smallest first. With n values, the fan-in threshold is the value at position ceil(0.9 x n), counting from 1. Do the same for fan-out.
3. A program is a god module when fan-in is at or above its threshold, fan-out is at or above its threshold, and both thresholds are above zero.

Example, n = 10, fan-in values `0 0 0 0 1 1 1 2 2 5`: position ceil(9) = 9, so the threshold is 2. Fan-out threshold works out to 3. A program with fan-in 5 and fan-out 4 is a god module. One with fan-in 5 and fan-out 1 is not.

Report fan-in leaders as a table: Program, Callers, Calls out to, Evidence. Gods cannot move in one wave. Note that for the coupling write-up.

## 3. Cycles, self-recursion and articulation points

Graph for cycles: the distinct `call` rows between programs in P.

Self-recursion: a program with a call row to itself. List it apart. It is not a strongly connected component (SCC) and does not count in fan-in or fan-out.

SCC: a set of two or more programs that can all reach one another by following calls. The whole set moves together, in one wave.

Shortcut for small graphs (up to about 30 programs):
1. Trim. Remove any program with no callee left in the set, or no caller left in the set. Repeat until nothing is removed. No removed program is in a cycle.
2. For each program v left, list F(v), everything reachable by following calls from v, and B(v), everything that reaches v. The SCC of v is F(v) and B(v) together, the programs in both lists.
3. If the SCC has one member, discard it. Otherwise record it with members sorted, once.

Tarjan procedure, for the programs left after trimming (or for all of P):
1. counter = 0. Empty stack S. Take programs in alphabetical order. Skip any that has an index.
2. visit(v): index(v) = low(v) = counter. counter + 1. Push v on S.
3. For each callee w of v:
   - w has no index: visit(w), then low(v) = min(low(v), low(w));
   - w is on S: low(v) = min(low(v), index(w));
   - otherwise ignore w.
4. When v's callees are done, if low(v) = index(v), pop S down to and including v. The popped programs are one component.
5. Keep components with two or more members.

Example: `A->B, B->C, C->A, C->D`. visit A (0), B (1), C (2). C sees A on S, so low(C) = 0. D gets index 3 and pops alone. B and A take low 0. A has low = index, so pop C, B, A. SCC = {A, B, C}. D is not in a cycle.

Articulation point: a vertex whose removal splits its connected part of the graph in two or more pieces. Use an undirected graph:
- vertices: programs in P, plus dataset nodes;
- edges: `call` rows between two different programs in P; `data` rows from a program in P to a dataset (any mode, including `ds:db2:`). Leave out `ds:dd:` datasets, JCL step data rows, include, contract and temporal rows.
- With 2 or fewer vertices there are none. A dataset can be an articulation point.

Procedure, by neighbor test:
1. Write the adjacency list. A vertex with one neighbor is never a point. Drop it from the candidates.
2. Quick screen: a vertex with a one-neighbor vertex hanging off it, and at least one other neighbor, is always a point. (A program that alone uses a dataset is an example.)
3. For each other candidate v: take its neighbors. Remove v. Flood-fill from one neighbor without passing through v. If any other neighbor of v is not reached, v is a point.

Example: edges `P1-P2, P2-P3, P3-P1, P3-P4`. P3 has neighbors P1, P2, P4. Remove P3: P1-P2 stay joined, P4 is alone. P3 is a point. P1 and P2 are not (their other neighbors stay joined).

Points are candidate wave boundaries. If the candidate list is longer than about 40, see section 7 and label the result inference.

## 4. Data hubs

Use `data` rows whose destination is a dataset node (any `ds:` id, including `ds:db2:` and `ds:dd:`). The source must be a program in P or any JCL step (a step carries a data row only when its program has no source in the tree).

Per dataset:
- writers = distinct sources with mode write or read_write;
- readers = distinct sources with mode read or read_write. A read_write source counts in both.

Rank by writers + readers, highest first. Break ties by dataset id in plain character order. Keep the top 15. Report Dataset, Writers, Readers, Evidence.

Grep the data rows for `ds:NAME` to count. Rule: every writer of a hub runs before its readers, so a hub is an ordering constraint. Contract rows say how the record layout is shared.

Example: `PGMA -> ds:MASTER write`, `PGMB -> ds:MASTER write`, `PGMR -> ds:MASTER read`. MASTER has 2 writers, 1 reader, total 3.

## 5. Dead-code buckets

Candidates are programs, copybooks and procs only. JCL jobs, scheduler jobs, steps, maps and datasets are never in a bucket. Three buckets, never two.

Apply in order:

1. No entry point in the tree: every candidate is unknown. Reason: "no entry points in the tree". Write a warning. There is no unreachable and no dormant list. Nothing can be sequenced. (Two programs, PROGA calls PROGB, no JCL, CSD or scheduler: both unknown.)
2. Unreached = candidates not reachable (section 1).
3. Computed calls. A reachable computed call is a `call` row to a `?dynamic:` node whose caller is reachable. (Grep COBOL for `CALL\s+[A-Z]` with no quote, and `PROGRAM\(\s*[A-Z]` on CICS LINK or XCTL.) A computed call in an unreached program does not count.
   If at least one exists, take every unreached program, then everything unreached that those programs call or include (programs, copybooks, procs), recursively. All of it is unknown. Reason: "not reached by any static edge, and K reachable computed call(s) could target it", with one file:line. The rest of the unreached list stays unreachable. A computed call in reachable code never leaves a program unreachable.
   Example: MAINJOB runs PGMMAIN. PGMMAIN has `CALL WS-PGM-NAME` at line 9. HIDDEN01 has no inbound row. HIDDEN01 is unknown.
4. Embedded JCL. Grep `['"]//[A-Z0-9#@$]*\s+EXEC\s+(PROC=|PGM=)?[A-Z0-9#@$]{1,8}` in COBOL. The literal names a proc or program that a running program can submit. No edge exists. If the submitting program is reachable and the target is currently unreachable, then the target, plus the programs a proc runs and everything those call or include, that is currently unreachable, moves to unknown. Reason: "named in JCL text inside PROGRAM at file:line, which a running program can submit". Warn with the count.
   Example: PGMMAIN holds `"//STEP1 EXEC PROC=LATERPRC"`. proc:LATERPRC runs PGMLATER. Both unknown. PGMDEAD stays unreachable.
5. Runtime-named programs (section 1) are already reachable. If you skipped them, redo reach first.
6. Every unreached candidate not moved above is unreachable. Reason: "no static path from any entry point and no reachable computed call in the tree".
7. Dormant. Take reachable programs and copybooks (not procs) that have a last-modified date. Dormant means the date is earlier than as-of date minus N years. N is 5 unless the user set it. Compare YYYY-MM-DD. For 29 February use 28 February. Reason: "reachable, last modified DATE, older than N years". A unit with no date is not dormant. Dormant units are reachable, so they are never also unknown or unreachable.
   Example: as-of 2026-09-30, N = 5, cutoff 2021-09-30. OLDPGM modified 2011-03-04 is dormant. NEWPGM modified 2026-05-01 is not.
   If no program has a date (not a git checkout, dates not read), dormancy was not computed. Write that in the register: "The dormant bucket was NOT computed. An empty list means not measured." Never write an empty dormant list as "none found".

Moves go one way. A unit may move toward unknown with cited evidence. A program may never move from unknown to unreachable. Dormant means old, not unused. Propose instrumentation, not deletion. If a live program calls a dormant one unconditionally, say it very likely runs.

Unscheduled jobs. A JCL job no scheduler or wrapper names is still an entry point, so it is never in a bucket.
- JCL jobs exist but no scheduler artifact was found: warn that the order across jobs is unknown.
- Scheduler artifacts exist: list the jobs in the tree that no `sch:` call row names. Warn and ask whether they still run.

## 6. The wave seed

A first cut from facts only. It judges no risk.

### 6.1 Roots and what they own

Roots are JCL jobs in the tree and programs a CSD transaction names. Scheduler jobs are not roots.

A root is online when it is a CSD-named program that holds no embedded JCL (section 5, step 4). A program that submits JCL counts as batch.

owned(R) is everything R reaches by `call` and `include` rows (section 1), plus runtime-named programs, the programs a proc runs, and the proc or program that embedded JCL in an owned program names.

used(R) is the set of datasets that owned units have a `data` row to, leaving out `ds:dd:`, plus datasets a utility writes. wrote(R) is the part written (mode write or read_write, or utility write). A dataset is shared when two or more roots use it in any mode.

Utility writes. For `PGM=IDCAMS`, read the SYSIN cards. These write: `DELETE name`, `ALTER name`, `DEFINE ... NAME(name)`, and `REPRO`, `BLDINDEX`, `IMPORT`, `EXPORT` into the dataset of `OUTFILE(dd)` (the DD's DSN) or `OUTDATASET(name)`. The DD says DISP=SHR or OLD, which reads as a read, so the cards are the only sign of a write.

### 6.2 Family of a root

Seven families, fixed order. Test each root with the first rule that fits.

| # | Family | Rule |
|---|---|---|
| 7 | subsystem | owned units touch DB2, IMS or MQ |
| 6 | online-writers | online root that writes a shared dataset |
| 5 | batch-writers | batch root that writes a shared dataset |
| 4 | batch-data-jobs | batch root that reads a shared dataset through a utility step, the mode coming from DISP alone |
| 3 | online-readonly | other online roots |
| 2 | batch-readonly | other batch roots that run an application program (one with source in the tree) |
| 1 | batch-utility | other batch roots with no application program |

Test order: subsystem, writer, data job, then online or batch, then program or none. Wave order is the family number, 1 to 7.

"Touches DB2, IMS or MQ" means: a `data` row to a `ds:db2:` node, or a `call` row to `ext:` plus one of `MQ` followed by two or more capitals, `CBLTDLI`, `AIBTDLI`, `DFSRRC00`, `DSNTEP2`, `DSNTEP4`, `DSNTIAD`, `DSNTIAUL`, `DSNUTILB`, `DSN`. A run-time named `DSN` command (TSO card `DSN SYSTEM(`) counts too.

"Through a utility" means a read-mode `data` row from a step whose note says the mode was inferred from DISP. Online roots are never in this family.

Record the deciding row's file:line for each root. For online-readonly use the CSD line. Where no row decides, use the first call or data row of the root, else the JCL job card line.

### 6.3 Scheduler chains

Build chains from jobs and scheduler jobs. Link a scheduler job to each job it runs (`call` row). Link any two jobs or scheduler jobs joined by a `temporal` row (Control-M conditions, order of submits in a wrapper). A chain is a connected set.

In a chain, take the job roots that are not subsystem. If there are two or more, each moves to the latest family among them. Cite the first temporal row in the chain. A subsystem job keeps its own family and does not pull the others up.

Example: a wrapper runs RPTJOB (batch-readonly), UPDJOB (batch-writers), DBJOB (subsystem), with temporal rows between them. RPTJOB moves to batch-writers. DBJOB stays in subsystem.

### 6.4 Place every unit

Take every program, JCL job, proc and scheduler job, once:
1. In the unreachable bucket: not placed, reason from section 5 or "dead code candidate, unreachable".
2. In the unknown bucket and no root owns it: not placed, reason from section 5 or "reachability unknown". (An embedded-JCL target is owned by its submitter, so it is placed.)
3. Scheduler job that runs no job: not placed, "scheduler job that names no JCL job in the tree".
4. Scheduler job: family is the latest among the jobs it runs. If a job it runs has no family (not in the tree), not placed, "no entry point owns it".
5. Any other unit: family is the earliest among the roots that own it. A shared subprogram goes with the first family that uses it. No owner: not placed, "no entry point owns it".

A call cycle always moves whole. Its members are reached from the same roots, so rule 5 gives them one family. Steps, copybooks, datasets and maps are not units.

If the tree has no entry point there are no waves. Every program is unplaced with "no entry points in the tree".

### 6.5 Groups inside a family

Only a family with two or more roots is cut. Two roots of the family are bound when:
- both write the same dataset, or
- both own the same application program (other than themselves).

A reader of a dataset another root writes is ordered after the writer but is not bound to it.

Join bound roots. Roots bound to none are alone. Groups of two or more roots are coupled.
- No coupled group, or exactly one coupled group and no lone root: no cut. One wave, no label.
- Otherwise: lone roots form `independent`, listed first. Then coupled groups, smallest first, ties by the name of the first member. A single coupled group is labeled `coupled`. Several are `coupled-1`, `coupled-2`, and so on.

A unit goes to the smallest group number among its roots in this family. A scheduler job goes to the largest group number among its jobs. A unit with no group goes to the first group.

Example. Family batch-writers has roots WRTA and WRTB (both write MASTER), WRTE and WRTF (different datasets, both call PGMX), WRTC (writes OTHER alone) and WRTD (reads MASTER, writes THIRD, which no writer shares).
```
independent: job:WRTC, job:WRTD
coupled-1:   job:WRTA, job:WRTB      (shared dataset)
coupled-2:   job:WRTE, job:WRTF      (shared program PGMX, so PGMX goes here)
```
Three waves, in that order. Size ties are broken by the first member: WRTA before WRTE.

A coupled group may still be too big to ship as one wave. Test it against the wave tests in the main procedure and cut it with a cited reason.

### 6.6 Assemble the waves

For family 1 to 7, skip a family with no placed unit. Make one wave per non-empty group, numbered 1 to N with no gaps. For each wave record:
- `family`, and `group` when cut;
- `units`, sorted in plain character order (bare program names, then `job:`, `proc:`, `sch:`);
- `entry_points`: the roots of the group;
- `computed_calls`: units in the wave that make a computed call. A wave with any cannot have high confidence. Say what the call could reach;
- `evidence`: up to 3 distinct file:line, sorted, from the deciding rows of its roots.

Example (small estate): SETUP is a utility job on an unshared dataset. PGMAUD reads the shared master. PGMVIEW and PGMEDIT both call PGMSHARE. PGMVIEW is online and reads. PGMEDIT is online and writes. PGMDB uses DB2.
```
1 batch-utility    job:SETUP
2 batch-readonly   PGMAUD, job:AUDJOB
3 online-readonly  PGMSHARE, PGMVIEW        (PGMSHARE: earliest family that uses it)
5 batch-writers    PGMUPD, job:UPDJOB, ...
6 online-writers   PGMEDIT
7 subsystem        PGMDB, job:DBJOB
```
(Numbers here are family numbers. Wave numbers close up when a family is empty.)

Output shape of the seed, `03a-wave-seed.md`: a table `Wave | Family | Units | Entry points | Evidence` (family shows `family (group)`), one total row with `analysis` as evidence, one section per wave with its description and units, and a table `Unit | Reason` for the units not placed. If a wave lists more than 80 units, show 80 and say how many more.

Output shape of the draft, `03a-waves-draft.json`:
```json
{
 "target_state": null,
 "waves": [
  {"wave": 1, "family": "batch-utility", "name": null, "units": ["job:SETUP"],
   "rationale": null, "unblocks": null, "blast_radius": null, "confidence": null,
   "evidence": [{"file": "app/jcl/SETUP.jcl", "line": 1}]}
 ],
 "unassigned": [{"id": "PGMDEAD", "reason": "dead code candidate, unreachable"}]
}
```

## 7. When the tree is large

These are working limits for hand work. Past about 60 reachable programs, or about 150 call and data rows, do not run the cycle or articulation steps over the whole graph in one pass.

Partition:
1. Compute owned(R) for each root (section 6.1). Programs shared by several roots join the partitions that own them.
2. Run fan-in, SCC and articulation on each partition. Merge the lists. Check every cross-partition call row by hand, because a cycle can run through two partitions.
3. Cap the work: if more than about 40 articulation candidates remain, test only vertices with fan-in 2 or more or a dataset touched by 3 or more programs.

These stay exact on a large tree, because each is a local count or a flood fill: entry points, reach, dead-code buckets, each root's family, scheduler chains, data hubs.

Label `inference`, and say how many rows you checked out of how many:
- articulation points on a partitioned or capped run;
- god modules when any fan count was estimated;
- SCCs found without trimming every program;
- a group cut made on a family with many roots without checking every dataset.

Write the basis in the first line of the section: "all N programs" or "partial: K of N". More than about 20 open edges: give them to the dependency-cartographer agent. What it returns is `inference`.

## 8. End-of-analysis checklist

Run it before writing any finding.
- [ ] Every program, JCL job, proc and scheduler job appears once, either in one wave or in the not-placed list with a reason. Placed + not placed = total units.
- [ ] No wave splits an SCC. For each SCC, all members sit in one wave.
- [ ] No program moved from unknown to unreachable. Every unreachable item has no reachable computed call in the tree behind it.
- [ ] Embedded-JCL and runtime-named targets are not in unreachable.
- [ ] No entry point means: all unknown, no waves, a warning.
- [ ] Dormancy: dates were read, or the register says "NOT computed".
- [ ] Jobs chained by a scheduler share a wave, except subsystem jobs. Scheduler jobs sit with their last family.
- [ ] A shared unit sits in the earliest family of its roots.
- [ ] Wave numbers run 1 to N with no gaps. Empty families are skipped.
- [ ] Each wave has evidence. A wave with computed calls is not high confidence.
- [ ] God thresholds and counts are shown. Every non-exact list is labeled `inference`.
- [ ] Unscheduled jobs and missing-scheduler warnings are in Open Questions.
