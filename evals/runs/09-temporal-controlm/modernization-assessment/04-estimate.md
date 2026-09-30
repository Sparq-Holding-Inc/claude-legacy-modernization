# 04 Estimate

All figures here are inference. They are judgment ranges from the graph counts, not calibrated on a team's measured velocity. None of the
numbers below comes from the client. Wave 1 is the only wave, so there is one estimate.

## Wave 1. Nightly batch cycle (JOBA then JOBB)

**Method.** Weight the things the plugin says move an estimate, in order, and count what this tree shows for each.

| Driver | What the tree shows | Effect on the range | Evidence |
|---|---|---|---|
| Coupling edges crossing the wave boundary | Zero program, data or contract edges cross it. One condition enters (EXTERNAL-FEED) and one leaves (JOBB-DONE). | Small, but the two conditions are the whole risk | `app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:11` |
| Behavioral oracle | None in the tree. No dataset, no output, no log | Pushes effort into building an oracle | analysis: `data_hubs` is empty, `node_counts` has no dataset |
| God modules in the wave | None | No effect | analysis: `god_modules` is empty |
| Logic held in the database | No DB2 or SQL in the tree | No effect | inference: no file in the tree touches a database |
| A team that can read the source language | Unknown. The source is two JCL jobs and one scheduler file, which is short to read | Low weight | inference |

**Range (inference).**

| Piece of work | Low | High | Evidence |
|---|---|---|---|
| Re-express two jobs and their conditions in the target scheduler | 2 person-days | 5 person-days | `app/scheduler/nightly.xml:4-12` |
| Pin down where EXTERNAL-FEED and JOBB-DONE come from and go to | 2 person-days | 5 person-days | `app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:11` |
| Build the comparison harness and run it for one full business cycle | 5 person-days | 12 person-days | inference |
| **Wave 1 total** | **9 person-days** | **22 person-days** | inference |

This is a range with a wide tail on purpose. I would not quote 9 to a steering committee. The number is small because the jobs do nothing in this tree. The spread
comes almost entirely from the three assumptions below.

**The assumptions the range is most sensitive to.**

1. Assumes the production members JOBA and JOBB have one step each and that step runs IEFBR14, as the tree shows
   (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`). If the members in production have more steps, the total above no longer applies, and wave 1 has to be
   estimated again from graph.json after the client supplies the full JCL. This one assumption could move the range by an order of magnitude.
2. Assumes EXTERNAL-FEED is set by one process the client can name (`app/scheduler/nightly.xml:5`). If it is set by an operator, or by several feeds, the
   second row roughly doubles.
3. Assumes the target scheduler can hold a condition that JOBB clears after it runs (`app/scheduler/nightly.xml:10`). If it cannot, rerun and restart behavior
   has to be designed and tested, and I would add 3 to 6 person-days to the first row.

**Where Claude Code can do the port and where it cannot.**

- Strong: writing the two job definitions and the condition wiring in the target scheduler's format. It is transliteration of 9 lines of XML
  (`app/scheduler/nightly.xml:4-12`) with a harness to check it.
- Strong: generating the comparison harness that checks order, conditions and return codes.
- Weak: deciding what EXTERNAL-FEED means, who consumes JOBB-DONE, and whether IEFBR14 is a placeholder for a real program. That is undocumented
  intent, and it needs a person at the client. It is not something Claude can read out of these files.

## Not estimated

There is no second wave. No estimate is given for programs, data migration or online work, because the tree holds none of them (`modernization-assessment/01-inventory.md:14-17`).
