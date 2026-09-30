# 04 Estimate

There are no waves, so there is no per-wave estimate. What follows is an estimate for the two
programs supplied, with the method stated, and a refusal to put a number on what the tree does not
show. All figures are inference. They come from counting lines and reading the two files. They are
not a measurement.

## Method

Effort is driven, in order, by coupling edges crossing the boundary, the behavioral oracle, god
modules, logic held in the database, and who can read COBOL. The tree has one coupling edge and it
is unresolved, no god module and no database. The oracle and the team are unknown, and those decide
the range.

## Estimate for what is in the tree

| Scope | Range | Method | Confidence | Evidence |
|---|---|---|---|---|
| Port `PROGB` (a `GOBACK` only) | under 0.5 person-days | Transliterate an empty program. Most of the time is the harness, not the code. | medium | `app/cbl/PROGB.cbl:4` |
| Port `PROGA` (accept a name, call it) to a dispatcher over a registry of allowed names | 1 to 3 person-days | Transliteration is a few lines. The days go to building the registry of target programs and deciding what happens on an unknown name. | low | `app/cbl/PROGA.cbl:9` |
| Discover the real target set of the computed call | 3 to 10 person-days, not estimable in the tree | Needs SYSIN or job history over a business cycle and the load library. It is not in the tree. | low | inference |
| Build the equivalence harness for the two programs | 2 to 5 person-days | Capture the names supplied and the observable results, then replay. See `06-test-strategy.md`. | low | inference |

The total for the tree as given is roughly 7 to 19 person-days, about 1.5 to 4 weeks of one person,
and most of it is discovery. It excludes every program the computed call can start. If the target set holds more than
`PROGB`, those programs need their own assessment and this figure does not cover them.

## Assumptions the range is most sensitive to

1. Assumes the names read by the `ACCEPT` at `app/cbl/PROGA.cbl:8` are a small fixed list of programs
   the client already owns, for example under ten. If the list is open ended, or comes from a table
   the client edits, the dispatcher needs a governed registry and the discovery line roughly doubles.
2. Assumes the nightly batch cycle is not implemented by `PROGA` starting a chain of programs. If it
   is, then the cycle is the real scope, this two-program estimate is a small fraction of it, and
   nothing here sizes it.
3. Assumes the client has job logs or SYSIN history to replay. If it has neither, the harness
   line moves from days to weeks, because the oracle then has to be built by hand from source.

## Where Claude Code helps and where it does not

- Mechanical port of `PROGB` and the call statement in `PROGA`: strong. There is nothing to infer.
- Choosing the target design for the dispatcher (a registry, a routing table, reflection): Claude Code
  can draft it, but a person must decide which names are allowed. That is a business and operations
  decision, not a transliteration.
- Working out what names arrive at run time and what each one does: weak. That intent is not in
  the source. It has to come from the client's job history and its engineers.
