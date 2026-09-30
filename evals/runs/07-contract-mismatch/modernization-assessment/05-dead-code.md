# 05 Dead code

Telemetry: none. Every claim here is provisional. `dead-code.json` holds the same result in
machine form. The extractor's candidate tables are in `05a-dead-code-candidates.md`.

## Result

All three buckets are empty. That needs two careful readings, because "empty" means different things
in each bucket.

| Bucket | Count | What the empty list means | Evidence |
|---|---|---|---|
| Unreachable | 0 | Every program is reachable. Both jobs are entry points and each runs one program | `app/jcl/WRITEJOB.jcl:2`, `app/jcl/READJOB.jcl:2` |
| Unknown | 0 | There are no computed calls in the tree, so nothing can be the hidden target of one | `app/cbl/PGMW.cbl:12-16`, `app/cbl/PGMR.cbl:12-16` |
| Dormant | 0 | This one is not evidence of anything. See below | inference: every node has `last_modified` of null in `graph.json` |

## Why the dormant bucket is empty for the wrong reason

The extractor decides dormancy from the last change date. This tree is not a git repository, so the
extractor read no dates (`meta.git_dates` is false in `graph.json`). Every unit shows "unknown" as
its last-modified date in `01-inventory.md`. With no dates it cannot call anything old.

So the empty dormant list means "cannot tell". It does not mean "nothing is old". With no telemetry
either, there is no evidence in either direction. Do not read this file as saying the system is
free of dead code.

## What I would ask for

- Job logs or SMF records for the last 12 months for `WRITEJOB` and `READJOB`. They turn this file
  from speculation into evidence.
- File dates from the client's source library, or a git history if one exists.
- Whether both jobs really run at all. Each job is an entry point only because it is a job in the
  tree (`app/jcl/WRITEJOB.jcl:1`, `app/jcl/READJOB.jcl:1`). Nothing shows a scheduler that submits
  them (inference).

## Duplicate layout, not dead code

`cpy:LAYOUTX` and `cpy:LAYOUTY` are both included, so neither is unused
(`app/cbl/PGMW.cbl:11`, `app/cbl/PGMR.cbl:11`). They are duplicates of one layout. That is a
coupling problem and it is handled in `02-coupling.md` and `03-waves.md`, not here. I did not put
either one in `do_not_port`, because deleting the reader's copy without a shared replacement would
break the reader.
