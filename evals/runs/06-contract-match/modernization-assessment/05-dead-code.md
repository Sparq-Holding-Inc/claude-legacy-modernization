# 05 Dead code

Telemetry: **none**. Every dead-code claim in this file is provisional. The generated candidate tables are in `05a-dead-code-candidates.md`. All three buckets came back empty. I kept them that way, and here is why each empty bucket is or is not reassuring.

## Unreachable: none

Both programs are named by an EXEC PGM= step in an entry job (`app/jcl/READJOB.jcl:2`, `app/jcl/WRITEJOB.jcl:2`). The one copybook is included by both programs (`app/cbl/PGMR.cbl:11`, `app/cbl/PGMW.cbl:11`). Nothing is left without a static path.

This is weaker than it looks. The extractor treats every JCL job as an entry point (`app/jcl/READJOB.jcl:1`, `app/jcl/WRITEJOB.jcl:1`), and no scheduler artifact was parsed. So "reachable" means only that the job exists in the tree. It does not show that anyone submits it (inference).

## Reachable but dormant: none, and this is not evidence of freshness

Every node has `last_modified` of null. The tree is not under git, so the extractor took no dates (`git_dates` is false in `graph.json`). The dormancy rule of 5 years could not be applied to anything. An empty dormant bucket here means "not measured". Do not read it as "recently changed" (inference).

## Unknown: none

The extractor found no computed call, so nothing can be reached dynamically and the unknown bucket is empty (inference, from `unresolved_dynamic` being empty). There is no `CALL` of a variable in either program (`app/cbl/PGMR.cbl:12`, `app/cbl/PGMW.cbl:12`).

## What would firm this up

- Job scheduling and SMF or job log history for READJOB and WRITEJOB over 12 months. That turns "reachable on paper" into "ran".
- Source control history or file dates for the five source members. That lets the dormancy rule run.
- The scheduler export. If either job is not in it, that job is a dead-code candidate the extractor cannot currently see.

## Register

| Bucket | Units | Confidence | Evidence |
|---|---|---|---|
| Unreachable | none | low | inference |
| Dormant | none (dates not available) | low | inference |
| Unknown | none | low | inference |
