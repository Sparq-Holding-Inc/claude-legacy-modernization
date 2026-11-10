# Output shapes

The exact shape of four JSON files: `graph.json`, `waves.json`, `dead-code.json` and `risks.json`. Nothing runs them for you. You check each file by reading it back with Read and Grep, using the Self-check at the end.

How to assemble `graph.json` is in [graph-model.md](graph-model.md). This file only fixes its shape.

## Conventions

- UTF-8 JSON. No comments, no trailing commas, double quotes only.
- An integer is a whole number. `true`, `1.5` and `"3"` are not integers.
- Evidence entry: `{"file": "app/cbl/CBACT01C.cbl", "line": 231}`. `file` is a non-empty path from the project root. `line` is an integer from 1 to the last line of that file. An `evidence` list holds at least one entry.
- A finding carries `evidence` (non-empty list) or `"inference": true`. Use inference only when no line proves the claim.
- Enums are exact lowercase strings:
  - confidence: `high`, `medium`, `low`
  - unit_type: `online_txn`, `batch`, `subprogram`, `copybook`, `jcl_job`, `jcl_step`, `proc`, `dataset`, `map`, `scheduler_job`, `external`
  - lang: `cobol`, `jcl`, `bms`, `csd`, `scheduler`, or `null`
  - edge kind: `call`, `include`, `data`, `contract`, `temporal`
  - edge mode: `read`, `write`, `read_write`, or `null`
  - target_state: `rehost`, `replatform`, `refactor`, `rewrite`, `unknown`
  - telemetry: `none`, `partial`, `provided`
- Program types are `online_txn`, `batch` and `subprogram`.

Node ids carry a prefix by kind, because names collide across kinds. A program id is the bare name with no colon (`CBTRN02C`). Others: `cpy:NAME` copybook, `map:NAME`, `job:NAME`, `step:JOB.STEP` (a repeat gets `#2`, a proc step is `step:JOB.STEP.PROCSTEP`), `proc:NAME`, `ds:NAME` dataset (`ds:dd:PROGRAM.DDNAME` for an unmapped DD, `ds:db2:TABLE` for a table), `sch:FOLDER/JOB`, `ext:NAME` for a target with no source in the tree, `?dynamic:SOURCE:LINE` for a computed target.

---

## graph.json

Facts only. Every edge cites a file and line.

**Required.** Top level: `nodes` (list), `edges` (list).
- Node: `id` (unique string), `unit_type`, `lang`, `path` (string or null), `loc` (integer >= 0, write 0 if not counted), `last_modified` (`"YYYY-MM-DD"` or null), `entry_point` (boolean).
- Edge: `src`, `dst` (node ids), `kind`, `mode`, `evidence`, `resolved` (boolean), `confidence`. `mode` is `read`, `write` or `read_write` on a `data` edge and `null` on every other kind.

**Optional.** Node: `line` (integer >= 1), `note`, `entry_evidence` (evidence list). Edge: `note` (string). Top level: `unparsed` (list of `{"file", "reason"}` strings), `meta` (any object), `analysis` (object).

`analysis` is lighter in the lean method. Every key in it is optional, and nothing checks it except as noted below. Later steps read these when present:
- `entry_points`: list of node ids.
- `sccs`: list of components, each a list of node ids that call each other in a cycle.
- `dead_code_candidates`: `{"unreachable": [ids], "dormant": [ids], "unknown": [ids]}`.
- `unresolved_dynamic`, fan-in, fan-out, data hubs, god modules: free form.

```json
{
  "nodes": [
    {"id": "job:READACCT", "unit_type": "jcl_job", "lang": "jcl", "path": "app/jcl/READACCT.jcl", "loc": 30, "last_modified": "2022-07-18", "entry_point": true},
    {"id": "CBACT01C", "unit_type": "batch", "lang": "cobol", "path": "app/cbl/CBACT01C.cbl", "loc": 358, "last_modified": "2022-07-18", "entry_point": false},
    {"id": "CBTRN01C", "unit_type": "batch", "lang": "cobol", "path": "app/cbl/CBTRN01C.cbl", "loc": 491, "last_modified": "2022-07-18", "entry_point": false},
    {"id": "cpy:UNUSED1Y", "unit_type": "copybook", "lang": "cobol", "path": "app/cpy/UNUSED1Y.cpy", "loc": 6, "last_modified": "2022-07-18", "entry_point": false},
    {"id": "ds:AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS", "unit_type": "dataset", "lang": null, "path": null, "loc": 0, "last_modified": null, "entry_point": false},
    {"id": "ext:COBDATFT", "unit_type": "external", "lang": null, "path": null, "loc": 0, "last_modified": null, "entry_point": false}
  ],
  "edges": [
    {"src": "job:READACCT", "dst": "CBACT01C", "kind": "call", "mode": null, "evidence": [{"file": "app/jcl/READACCT.jcl", "line": 22}], "resolved": true, "confidence": "high"},
    {"src": "CBACT01C", "dst": "ds:AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS", "kind": "data", "mode": "read", "evidence": [{"file": "app/cbl/CBACT01C.cbl", "line": 60}], "resolved": true, "confidence": "high"},
    {"src": "CBACT01C", "dst": "ext:COBDATFT", "kind": "call", "mode": null, "evidence": [{"file": "app/cbl/CBACT01C.cbl", "line": 231}], "resolved": true, "confidence": "high", "note": "Assembler routine, no source in the tree."}
  ],
  "analysis": {"entry_points": ["job:READACCT"], "sccs": [], "dead_code_candidates": {"unreachable": ["cpy:UNUSED1Y"], "dormant": [], "unknown": ["CBTRN01C"]}}
}
```

### Rules this file must follow

1. The top level is an object. `nodes` and `edges` are lists of objects.
2. Every node has a non-empty string `id`. No two nodes share an id.
3. `unit_type` and `lang` are in their enums. `path` is a string or null. `loc` is an integer >= 0. `entry_point` is a boolean.
4. `last_modified` is `YYYY-MM-DD` (a time may follow) or null.
5. If present, `line` is an integer >= 1 and `entry_evidence` is a valid evidence list.
6. A copybook, map, jcl_job, jcl_step, proc, dataset or scheduler_job id starts with its prefix. A program id has no colon and does not start with `?`. An `external` id starts with `ext:` or `?dynamic:`.
7. Every edge `src` and `dst` is the id of a node in the file.
8. `kind` and `mode` are in their enums. A `data` edge has a mode. Every other kind has `mode` null.
9. Every edge has a valid evidence list, a boolean `resolved`, a `confidence` in the enum, and a string `note` if it has one.
10. A `?dynamic:` target has `resolved` false. An edge with `resolved` false never has confidence `high`.
11. No two edges share `src`, `dst`, `kind` and `mode`. Merge them and keep all the evidence in one list.
12. `unparsed`, if present, is a list. Each entry has a string `file` and a string `reason`.
13. A computed call is never dropped. A named target with no source in the tree points to an `ext:` node with `resolved` true.

---

## waves.json

The migration sequence. Each wave is a set of units that move together.

**Required.** `target_state`, and `waves` (list, may be empty only when `unassigned` is non-empty). Each wave: `wave` (integer >= 1), `units` (non-empty list of node id strings), `name`, `rationale`, `unblocks` (non-empty strings), `blast_radius` (`low`, `medium` or `high`), `confidence`, and `evidence` or `"inference": true`.

**Optional.** Wave: `family` (string label). Top level: `unassigned` (list of `{"id", "reason"}`), `deviations` (list of `{"unit", "reason"}` plus evidence or inference, and optional `from_wave`, `to_wave`).

```json
{
  "target_state": "refactor",
  "waves": [
    {
      "wave": 1,
      "family": "batch-readonly",
      "name": "Read-only batch utilities",
      "units": ["CBACT01C", "job:READACCT"],
      "rationale": "Reads the account master and writes nothing another job uses. Proves the toolchain.",
      "unblocks": "The decimal type and layout mapping that later waves reuse.",
      "blast_radius": "low",
      "confidence": "medium",
      "evidence": [{"file": "app/jcl/READACCT.jcl", "line": 1}, {"file": "app/cbl/CBACT01C.cbl", "line": 29}]
    }
  ],
  "unassigned": [{"id": "CBTRN01C", "reason": "Nothing in the tree runs it. Held until someone confirms it never runs."}],
  "deviations": [{"unit": "job:READACCT", "from_wave": 2, "to_wave": 1, "reason": "It runs only CBACT01C, so it moves with its program.", "evidence": [{"file": "app/jcl/READACCT.jcl", "line": 22}]}]
}
```

### Rules this file must follow

1. `target_state` is in its enum.
2. `waves` is a list. It is empty only for a tree with no entry point (no node has `entry_point` true), with every unit in `unassigned`. If any node has `entry_point` true, `waves` is not empty.
3. Each wave is an object. `wave` is an integer >= 1. Numbers run 1 to N with no gaps and no repeats, N being the number of waves.
4. `units` is a non-empty list of strings. No unit is in two waves.
5. `name`, `rationale` and `unblocks` are non-empty and not blank.
6. `blast_radius` is `low`, `medium` or `high`. `confidence` is in the enum.
7. Every wave has valid evidence or `"inference": true`.
8. Each deviation has a string `unit`, a non-empty `reason`, and evidence or `"inference": true`. The `unit` is a node in `graph.json`. A `to_wave` is a wave number in this plan.
9. Each `unassigned` entry has a string `id` and a non-empty `reason`. No id is listed twice. No id is also in a wave.
10. Every id in a wave or in `unassigned` is a node in `graph.json`.
11. A wave holds only programs, `job:`, `proc:` and `sch:` ids. Steps, copybooks, datasets, maps and external nodes move with their owner and are never listed.
12. Every program, jcl_job, proc and scheduler_job node in `graph.json` is in exactly one wave or in `unassigned`.
13. No wave splits a strongly connected component. All members of one component that appear in the plan share one wave, or all sit in `unassigned`. Take components from `analysis.sccs`. If it is absent, find the call cycles yourself (see [graph-model.md](graph-model.md)).

---

## dead-code.json

Three buckets, never two.

**Required.** `telemetry`, and the three keys `unreachable`, `dormant`, `unknown`, each a list, present even when empty. Each item: `id` (a node id in `graph.json`), `reason` (non-empty string), `confidence`, and `evidence` or `"inference": true`. Optional on a `dormant` item: `last_modified` (`YYYY-MM-DD` or null).

```json
{
  "telemetry": "none",
  "unreachable": [
    {"id": "cpy:UNUSED1Y", "reason": "No program includes it. Provisional: telemetry is none.", "confidence": "high", "evidence": [{"file": "app/cpy/UNUSED1Y.cpy", "line": 1}]}
  ],
  "dormant": [],
  "unknown": [
    {"id": "CBTRN01C", "reason": "No JCL step, CSD entry or scheduler names it. Only telemetry can say it never runs.", "confidence": "medium", "evidence": [{"file": "app/cbl/CBTRN01C.cbl", "line": 23}]}
  ]
}
```

### Rules this file must follow

1. `telemetry` is `none`, `partial` or `provided`.
2. `unreachable`, `dormant` and `unknown` are all present and all lists.
3. Every item has a string `id`, a non-empty `reason`, a `confidence` in the enum, and valid evidence or `"inference": true`.
4. An id appears in one bucket only.
5. A `dormant` item's `last_modified`, if present, is `YYYY-MM-DD` or null.
6. Every item id is a node in `graph.json`.
7. The baseline is `analysis.dead_code_candidates`. If it is absent, build the three lists from the graph first (see [graph-model.md](graph-model.md)) and use them as the baseline.
8. Every baseline candidate is in one of your three buckets. None is dropped.
9. An `unreachable` id was a baseline `unreachable` candidate. No program moves from unknown to unreachable. If a baseline bucket looks wrong, move the item toward `unknown`, cite the evidence, and add no new keys.
10. A `dormant` id was a baseline `dormant` candidate. Dormancy comes from `last_modified` dates, not judgment.
11. An `unknown` id was a baseline candidate in any bucket. A unit with a static path from an entry point belongs in no bucket.

---

## risks.json

Two independent axes per unit. Never one combined number.

**Required.** `units` (non-empty list). Each unit: `id` (node id, unique), `port_difficulty` and `blast_radius` (each `{"score": integer 1-5, "why": one-line non-empty string}`), `quadrant`, `wave` (integer or `null`), `driving_fact` (non-empty string), `confidence`, and `evidence` or `"inference": true`.

**Optional.** `do_not_port`: list of `{"id", "reason"}`.

Quadrant is `low-low`, `high-low`, `low-high` or `high-high`, port difficulty first. A score of 1 or 2 is low. A score of 3, 4 or 5 is high. A three is not low. By method, not by check: score each program that is reachable or unknown, and each `job:` unit. Skip steps, copybooks and datasets.

```json
{
  "units": [
    {
      "id": "CBACT01C",
      "port_difficulty": {"score": 3, "why": "358 lines, three REDEFINES layouts, calls assembler COBDATFT with no source."},
      "blast_radius": {"score": 1, "why": "Read-only print utility. Failure is loud and nothing reads its output."},
      "quadrant": "high-low",
      "wave": 1,
      "driving_fact": "Calls assembler COBDATFT at line 231.",
      "confidence": "medium",
      "evidence": [{"file": "app/cbl/CBACT01C.cbl", "line": 231}]
    },
    {
      "id": "job:READACCT",
      "port_difficulty": {"score": 1, "why": "One step, one program, no arithmetic of its own."},
      "blast_radius": {"score": 1, "why": "Prints the account master. Nothing downstream consumes it."},
      "quadrant": "low-low",
      "wave": 1,
      "driving_fact": "Runs only CBACT01C.",
      "confidence": "low",
      "inference": true
    }
  ],
  "do_not_port": [{"id": "cpy:UNUSED1Y", "reason": "No program includes it. Delete it."}]
}
```

### Rules this file must follow

1. `units` is a non-empty list of objects with a string `id`. No id appears twice.
2. No unit has the key `risk_score`, `score`, `combined`, `total`, `overall`, `risk`, `composite` or `priority_score`. `score` is allowed only inside the two axis objects.
3. `port_difficulty` and `blast_radius` are objects. Each `score` is an integer 1 to 5. Each `why` is a non-empty single line (no newline).
4. `quadrant` equals what the two scores give: each axis is low (1-2) or high (3-5), written `difficulty-blast`.
5. `driving_fact` is non-empty. `confidence` is in the enum. `wave` is an integer or null.
6. Every unit has valid evidence or `"inference": true`.
7. `do_not_port`, if present, is a list.
8. Every unit id is a node in `graph.json`.
9. Each non-null `wave` is a wave number that exists in `waves.json`.
10. Each unit's `wave` equals the number of the wave in `waves.json` that lists its id. A unit in `unassigned` or in no wave has `wave` null.

### Setting the wave field by hand

`apply-waves` is now manual. Once `waves.json` is final, edit the `wave` field on every risk unit. Find the unit's id in `waves.json` and write that wave's number. If the id is in `unassigned` or in no wave, write `null`. Repeat after any change to `waves.json`.

---

## Self-check

Walk this list before you finish. Open each file with Read and use Grep to count and compare. Fix every miss, then read the file back.

**All files**
- [ ] Braces and brackets balance, no trailing commas, no comments, all strings quoted.
- [ ] Every evidence `line` is an integer >= 1. Grep `"line": ?(0\b|-|"|null|[0-9]+\.)` finds nothing.
- [ ] Every cited `file` exists (Glob). Every cited `line` is within that file (Grep `-c ""` gives its line count).
- [ ] Every finding has `evidence` or `"inference": true`. Every `confidence` is `high`, `medium` or `low`.

**graph.json**
- [ ] `nodes` and `edges` are lists. Count `"entry_point"` against `"unit_type"`: equal.
- [ ] No duplicate node id (Grep `"id":`, scan for repeats).
- [ ] `unit_type`, `lang`, `kind`, `mode` are in their enums. Each id has the prefix for its type. Program ids have no colon.
- [ ] `last_modified` is `YYYY-MM-DD` or null. `loc` is an integer >= 0. Node `line`, if present, is >= 1.
- [ ] Every edge `src` and `dst` is an existing node id.
- [ ] Every `data` edge has a mode. Every other edge has `"mode": null`.
- [ ] Every edge has `resolved` (boolean), `confidence` and `evidence`.
- [ ] Every `?dynamic:` target has `"resolved": false`. No `"resolved": false` edge has confidence `high`.
- [ ] No two edges share `src`, `dst`, `kind` and `mode`.
- [ ] `unparsed` entries each have a `file` and a `reason`. Computed calls are kept, not dropped.

**waves.json**
- [ ] `target_state` is in its enum. `waves` is empty only when no node has `"entry_point": true`.
- [ ] Wave numbers run 1 to N with no gap or repeat (Grep `"wave":`).
- [ ] Each wave has non-empty `name`, `rationale`, `unblocks`, a valid `blast_radius`, a valid `confidence`, and evidence or inference.
- [ ] Every id in a wave or `unassigned` is a node in `graph.json` (Grep the id there).
- [ ] Every listed id is a program, `job:`, `proc:` or `sch:` unit. No step, copybook, dataset, map or external node.
- [ ] No id appears twice across all waves and `unassigned`.
- [ ] Count of program, jcl_job, proc and scheduler_job nodes in `graph.json` equals the count of ids in waves plus `unassigned`.
- [ ] No strongly connected component is split across waves or between a wave and `unassigned`.
- [ ] Each deviation has `unit`, `reason`, evidence or inference. Its `unit` is a node. Its `to_wave` is a wave in this plan.
- [ ] Each `unassigned` entry has a non-empty `reason`.

**dead-code.json**
- [ ] `telemetry` is `none`, `partial` or `provided`.
- [ ] `unreachable`, `dormant` and `unknown` are all present as lists, even when empty (Grep each key).
- [ ] Each item has `id`, non-empty `reason`, valid `confidence`, and evidence or inference.
- [ ] Every item id is a node in `graph.json`. No id is in two buckets.
- [ ] Every baseline candidate appears in a bucket. None is missing.
- [ ] Every `unreachable` id was an `unreachable` candidate. Nothing moved from unknown to unreachable.
- [ ] Every `dormant` id was a `dormant` candidate. Any `last_modified` is a date or null.
- [ ] Every `unknown` id was a candidate, and none has a static path from an entry point.

**risks.json**
- [ ] `units` is a non-empty list with no repeated `id`. Every id is a node in `graph.json`.
- [ ] Grep `"(risk_score|combined|total|overall|risk|composite|priority_score)"` finds nothing. The count of `"score":` equals twice the number of units.
- [ ] Each `score` is an integer 1 to 5. Each `why` is one non-empty line.
- [ ] Each `quadrant` matches its scores. A 3 is high.
- [ ] `driving_fact` is non-empty on every unit. `wave` is an integer or `null`.
- [ ] Wave sync: each unit's `wave` equals the number of the wave in `waves.json` that lists its id, or `null` if it is in `unassigned` or in no wave. No `wave` names a number `waves.json` lacks.
- [ ] `do_not_port`, if present, is a list.
