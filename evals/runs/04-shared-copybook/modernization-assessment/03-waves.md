# 03 Waves

Target state: **refactor**, from the `--target refactor` flag. Machine-readable plan: `waves.json`. Risk scores: `risks.json`.

## One wave

The system in this tree is two 8-line programs and one 3-line copybook. That is one wave. Splitting PROGA from PROGB would put one definition of `SHARED-AREA` in two places for the length of the migration, so the pair is one unit of change.

| Wave | Name | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | Shared customer-area pair | PROGA, PROGB (copybook `cpy:SHARED01` moves with them) | low | low | `app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5`, `app/cpy/SHARED01.cpy:1` |

Confidence is `low`. Blast radius is `low` on what is visible, which is very little. The tree holds no JCL, scheduler or dataset, so the link between these programs and "the nightly batch cycle" is unverified. Both programs score `low-low` (port difficulty 1, blast radius 2, `risks.json`).

## Wave validity, checked

| Test | Result | Evidence |
|---|---|---|
| Deployed independently, behind a flag or facade | Yes, by keeping the legacy load modules and switching per program at the job step. The job step is not in the tree, so this is untested. | inference |
| Rolled back independently | Yes. Legacy load modules stay in place until the equivalence exit bar in `06-test-strategy.md` is met. | inference |
| Testable boundary | The visible boundary is the layout of `SHARED-AREA` after each program runs. With no dataset in the tree, the real boundary is job output, which is not visible here. | `app/cpy/SHARED01.cpy:1-3` |
| Delivers something a stakeholder can name | One definition of the shared customer area in the target, and a proven toolchain and harness on a small unit. | inference |

## What this wave unblocks

Inside this tree, nothing depends on PROGA or PROGB, so it unblocks no other unit here. Its value is the single target-language definition of `SHARED-AREA`, including the packed decimal `SH-BALANCE` at `app/cpy/SHARED01.cpy:3`. Any other program outside this tree that includes SHARED01 can then move without a second copy of the layout. That is inference: the tree does not show other includers.

## If the system were ten times larger

The cut would follow the copybook families. Programs that include the same layout copybook go in the same wave, and a layout copybook that fans out to many programs marks a wave boundary. Order:

1. Wave 1: `low-low` programs with no shared datasets, to prove toolchain and harness.
2. Wave 2: `high-low` programs, to learn packed decimal and date patterns where a failure is cheap.
3. Later: `low-high` programs once the harness is proven, and `high-high` programs last, strangled behind a facade.

The strongly connected components and articulation points from `graph.json` would fix the boundaries. Here both lists are empty.

## Ordering against the target state

For `refactor`, the port keeps the program structure and moves it to the target language and runtime. Each program becomes one module and `SHARED01` becomes one shared record type. A rehost would not touch the source. A rewrite would ask what the programs are for, and neither the code nor the tree says.

## Unassigned

Nothing. The copybook is not a unit. It moves with its owners.
