# Scheduler recipes

Two kinds of scheduler file give order between jobs: Control-M style XML, and shell wrappers that name JCL files. Anything else is listed as not parsed.

Patterns are ripgrep patterns (Rust regex: no lookaround, no backreferences). Run them case-insensitive (`-i`) with line numbers. Every hit is cited as `path:line`, path relative to the scanned root. Read the hit line before you write an edge.

## 0. Find the scheduler files

Control-M XML. Pattern, run on `*.xml`, `*.ctm`, `*.controlm`, files-with-matches:

```
<(DEFTABLE|SMART_FOLDER|FOLDER)\b
```

An XML file with no hit is not a scheduler file. Skip it without comment.

Shell wrappers: Glob `**/*.sh`, `**/*.ksh`, `**/*.bash`. A wrapper counts only if section 4 finds a JCL file it names.

Not parsed. Glob `**/*.ca7`, `**/*.jil`, `**/*.tws`, `**/*.cron`, `**/*.crontab`, `**/crontab`. For each file add to `unparsed`: `{"kind": "scheduler", "file": ..., "reason": "<what>, not parsed"}` where what is: .ca7 "CA-7 listing, not Control-M XML"; .jil "Autosys JIL"; .tws "IBM Workload Scheduler"; the rest "cron table". Add to `analysis.warnings`: "FILE is a scheduler file the method cannot parse. Jobs it schedules are counted as unscheduled here, so the unscheduled list is overstated."

## 1. Control-M structure: folders, jobs, conditions

Fact: which folder holds which job, and which conditions each job sets, waits for or deletes.

```
</?(JOB|INCOND|OUTCOND|FOLDER|SMART_FOLDER)\b
```

Run on each Control-M file. The hits form the skeleton in file order. Read each opening tag.
- Folder: attribute `FOLDER_NAME`, or `JOBNAME` for a `SMART_FOLDER`. A job belongs to the nearest folder tag above it that no `</FOLDER>` or `</SMART_FOLDER>` has closed. No folder: the folder name is empty and the id is `sch:/JOB`.
- Job: `JOBNAME` is the name. `MEMNAME` is the JCL member. If `MEMNAME` is missing, use `JOBNAME`. The line is the line of the `<JOB` tag, even when its attributes run onto the next lines.
- Condition: `NAME` is the condition. It counts only when its parent is the job tag itself, between `<JOB ...>` and `</JOB>`. `<INCOND>` is a wait. `<OUTCOND>` with `SIGN="+"`, or no `SIGN`, is a set. `<OUTCOND>` with any other sign (`-`) is a delete.

Traps:
- Attributes can sit on later lines. Read two lines past the hit. A self-closing job has no conditions.
- Minified XML puts many tags on one line. They share one line number.
- `ODATE`, `AND_OR`, calendars, resources, `ON`/`DOCOND` blocks and `SHOUT` are not read. A condition inside `ON`/`DOCOND` is not a job-level condition.
- A broken file: record `{"kind": "scheduler", "file": ..., "reason": "Control-M XML did not parse: <what>"}`. Keep what you read before the break.

## 2. Scheduler node and call edge

For every job write:
- Node `sch:FOLDER/JOBNAME`: unit_type `scheduler_job`, lang `scheduler`, path the XML file, loc 0, line = the `<JOB` line, entry_point true.
- Edge `sch:FOLDER/JOBNAME` -> `job:MEMNAME`, kind `call`, confidence high, evidence the `<JOB` line.

Matching to JCL: the target is the JCL job whose `//NAME JOB` card has `NAME` equal to `MEMNAME`, upper case. Find it with Grep, run on `*.jcl`, `*.job`:

```
^//MEMNAME[[:space:]]+JOB\b
```

Found: the `job:MEMNAME` node already exists. Not found: write a placeholder node `job:MEMNAME`, unit_type `jcl_job`, lang `jcl`, path null, loc 0, entry_point false, note "JCL member MEMNAME is not in the scanned tree". The edge stays high and resolved.

Trap: the file name may match `MEMNAME` while its JOB card has another name. Do not link by file name. Keep the placeholder and add a warning naming both.

## 3. Conditions to temporal edges

Work one XML file at a time. Match on `NAME` alone, exact text. Match `ODATE` never.
- For each name set by job P and waited on by job C, with P and C different jobs: edge `sch:P` -> `sch:C`, kind `temporal`, confidence high, evidence `[P's OUTCOND line, C's INCOND line]`, note "condition NAME".
- Several producers or consumers: one edge per pair. Two conditions between the same pair: one edge, both evidence pairs, notes joined.
- A delete makes no edge. A wait that no job in the same file sets makes no edge.
- Add to `analysis.warnings`: "FILE:LINE: job J waits for condition C, which no job in this file sets. It is an external input." and "FILE:LINE: job J deletes condition C (SIGN -). That order is not an edge."
- A condition set in one file and waited on in another: no edge. Add a warning naming both lines.

## 4. Shell wrappers that name JCL files

Fact: a shell file submits JCL files in a fixed order.

```
\.jcl\b
```

Run on each shell file. To drop comment-led lines in the same pass use:

```
^[[:space:]]*[^#[:space:]].*\.jcl\b
```

Read each hit line, left to right. Per reference:
- Skip it if the line is a comment, or the reference sits after ` #`.
- Skip it if a `$` appears in its path or name. Add a warning with the line.
- The stem is the trailing run of letters, digits, `#`, `@`, `$` before `.jcl`. `jcl/MY_JOB.jcl` has stem `JOB`. Directories are ignored.
- Resolve: find a JCL file in the tree (`.jcl` or `.job`) whose file stem equals the stem, case-insensitive, and that holds a JOB card. The target is the first job in that file, `job:<JOB card name>`. No such file: no edge, add a warning.

Write, only if at least one reference resolved:
- Node `sch:<wrapper path>`: unit_type `scheduler_job`, lang `scheduler`, path the shell file, loc 0, entry_point true. No line.
- Edge `sch:<path>` -> each job, kind `call`, confidence high, evidence the line.
- For each pair of consecutive resolved references with different jobs A then B: edge `job:A` -> `job:B`, kind `temporal`, confidence medium, evidence `[line of A, line of B]`, note "order of submits in <path>". A, A gives no temporal edge. A, B, A gives A -> B and B -> A.

Traps: order is file order, not run order. Branches, loops, `&` and `wait` are not modeled. That is why the temporal edge is medium. References to `.job` files are not followed.

## 5. Worked examples

A. Control-M, tree with `app/scheduler/nightly.xml` (JOBA, JOBB in folder NIGHTLY) and JCL for both. Skeleton hits: line 4 `<JOB JOBNAME="JOBA">`, 5 `<INCOND NAME="EXTERNAL-FEED">`, 6 `<OUTCOND NAME="JOBA-DONE" SIGN="+">`, 8 `<JOB JOBNAME="JOBB">`, 9 `<INCOND NAME="JOBA-DONE">`, 10 `<OUTCOND NAME="JOBA-DONE" SIGN="-">`, 11 `<OUTCOND NAME="JOBB-DONE" SIGN="+">`.
- `sch:NIGHTLY/JOBA` -> `job:JOBA` call high, nightly.xml:4. `sch:NIGHTLY/JOBB` -> `job:JOBB` call high, nightly.xml:8.
- `sch:NIGHTLY/JOBA` -> `sch:NIGHTLY/JOBB` temporal high, evidence nightly.xml:6 and nightly.xml:9.
- Line 5: no job sets EXTERNAL-FEED, so a warning, no edge. Line 10: a delete, so a warning, no edge.

B. Delete trap, `app/scheduler/f.xml`: JOBX sets X-DONE (line 5, `+`), JOBY deletes it (line 8, `-`), JOBZ waits on it (line 11). One edge: `sch:F/JOBX` -> `sch:F/JOBZ` temporal high, f.xml:5 and f.xml:11. Nothing for JOBY. No JCL for any job, so three placeholder `job:` nodes with entry_point false. Calls at lines 4, 7, 10.

C. MEMNAME differs, `<JOB JOBNAME="RPTNITE" MEMNAME="RPTJOB">` at line 4: `sch:NIGHTLY/RPTNITE` -> `job:RPTJOB` call high, line 4.

D. Wrapper `jobs/nightly.sh`: line 4 `submit jcl/JOBA.jcl`, line 5 `submit jcl/JOBB.jcl`, line 6 `# submit jcl/JOBC.jcl`. Line 6 is skipped.
- `sch:jobs/nightly.sh` -> `job:JOBA` call high, :4. `sch:jobs/nightly.sh` -> `job:JOBB` call high, :5.
- `job:JOBA` -> `job:JOBB` temporal medium, evidence nightly.sh:4 and nightly.sh:5.
- `job:JOBC` has no call from the wrapper. It stays an entry point and is unscheduled.

E. Three submits (RPTJOB line 3, UPDJOB line 4, DBJOB line 5) give three calls and two temporal edges: RPTJOB -> UPDJOB (lines 3, 4) and UPDJOB -> DBJOB (lines 4, 5), both medium.

## 6. After the recipes

- Unscheduled jobs: if JCL jobs exist and at least one `sch:` node exists, every job with a path and no `call` edge from a `sch:` node goes in `analysis.unscheduled_jobs`. Warn: "N JCL job(s) are not named by any parsed scheduler or wrapper. Every job counts as an entry point, so none of them appears in the dead code buckets. Ask whether they still run."
- JCL jobs exist and no `sch:` node exists: warn "N JCL job(s) are in the tree but no scheduler artifact was parsed. The order jobs run in across jobs is unknown. Ask for the scheduler's job definitions."

## Not covered

- CA-7, Autosys JIL, Workload Scheduler, cron, and any other vendor format. Listed as not parsed.
- Control-M calendars, resources, `ON`/`DOCOND` actions, cyclic jobs, time windows, `ODATE` logic, nested job dependencies other than conditions.
- Shell wrappers that build names from variables, submit `.job` files, call `tso submit` with a dataset member, or read job lists from a file.
- Conditions matched across two XML files.
- Runtime order. These are declared orders only.
