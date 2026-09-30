# 03 Waves

Target state: refactor. The number of waves is zero.

## Why there is no wave plan

The extractor finds no entry point in this tree: no JCL job, no CSD transaction, no scheduler job and
no shell wrapper (`03a-wave-seed.md`, analysis `entry_points` is empty). A wave is built from the
family of the entry points that use a unit. With no entry point there is no family, so the seed
places nothing. `03a-waves-draft.json` has an empty `waves` list and both programs in `unassigned`.
I kept that. `waves.json` has `"waves": []` and lists `PROGA` and `PROGB` in `unassigned`, with a
reason for each. I invented no wave and made no deviation.

Nothing can be sequenced until the client supplies JCL, a CSD or a scheduler export.

## Units not placed

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| `PROGA` | No entry point names it. It makes a computed call, so what it starts is unknown. | high | `app/cbl/PROGA.cbl:9` |
| `PROGB` | No entry point and no static caller. `PROGA`'s computed call could name it, and that cannot be proven or ruled out. | high | `app/cbl/PROGB.cbl:1`, `app/cbl/PROGA.cbl:9` |

## The four tests for a valid wave, and where each fails

| Test | Result for this tree | Evidence |
|---|---|---|
| Can deploy independently, behind a flag or facade | Cannot be answered. No entry point shows how either program is started. | analysis (`entry_points`, warning "No entry points were found") |
| Can roll back independently | Cannot be answered for the same reason. | analysis (`entry_points`) |
| Has a testable boundary | The boundary of `PROGA` is the name it reads and whatever that program does. The name source is not in the tree. | `app/cbl/PROGA.cbl:8` |
| Delivers something a stakeholder can name | Cannot be answered. The must-not-break item, the nightly batch cycle, maps to no unit in the tree. | inference |

## Risk quadrants, for when the plan exists

`risks.json` scores both programs. `PROGB` is low-low, and `PROGA` is low-high on thin evidence. If
JCL later shows `PROGA` is the driver of the nightly cycle, it stops being a candidate for an early
wave. Its blast radius would then be the whole cycle, and the computed call would be the thing to put
behind a facade first. That is a possibility, not a finding, because nothing in the tree ties
`PROGA` to the nightly cycle.

| Unit | Port difficulty | Blast radius | Quadrant | Confidence | Evidence |
|---|---|---|---|---|---|
| `PROGA` | 2 | 3 | low-high | low | `app/cbl/PROGA.cbl:9` |
| `PROGB` | 1 | 1 | low-low | medium | `app/cbl/PROGB.cbl:4` |

## What the client must supply so waves can be cut

- The JCL that runs `PROGA`, with its SYSIN or PARM. This creates an entry point.
- The scheduler export for the nightly batch cycle, so that the cycle maps to units and job order
  becomes a temporal edge.
- The list of program names that reach the `ACCEPT`, so the computed call can be bounded.

Until then the plan is empty on purpose. A confident plan built on two programs and one unresolved
call would look rigorous and be wrong.
