# Evals

Everything here exists to answer one question: how good is this plugin, and how do we know?

`RESULTS.md` holds the scorecard. Read its status line first.

## What is here

| Path | What it is |
|---|---|
| `fixtures/<case>/repo` | A small seeded repo. One trap per fixture. |
| `fixtures/<case>/truth.json` | The answer, written by hand before the extractor code it grades. |
| `carddemo/` | The AWS CardDemo benchmark: pinned source, a draft answer key, and how it was made. |
| `run_extractor_evals.py` | Grades the extractor against the fixtures and CardDemo. |
| `mutation_check.py` | Breaks the extractor on purpose and shows which fixtures notice. |
| `test_hook.py` | Tests for the citation hook. |
| `test_e2e_metrics.py` | Tests for the end to end scorer. |
| `test_validators.py` | Plants wrong assessments (an entry point called unreachable, a plan with a made-up unit, a risk in wave 999) and checks that validation rejects them. |
| `run_e2e_evals.py` | Runs full assessments headless and scores them. |
| `scorecard/` | JSON written by the runners. `RESULTS.md` is built from it. |
| `runs/` | The saved output of every end to end run. |

Python 3 and the standard library. Nothing to install.

## Run it

```bash
python3 evals/run_extractor_evals.py             # fixtures and CardDemo
python3 evals/mutation_check.py                  # can the fixtures fail?
python3 evals/test_hook.py                       # citation hook
python3 evals/test_e2e_metrics.py                # scorer
python3 evals/test_validators.py                 # validators reject wrong assessments
python3 evals/run_e2e_evals.py --cases all       # headless runs, then score (calls the model)
python3 evals/run_e2e_evals.py --score-only      # score runs that already exist
python3 evals/render_results.py                  # rebuild RESULTS.md
```

Two ways to run the end to end evals:

- **Headless.** `run_e2e_evals.py --cases all` calls `claude -p` with the plugin loaded. This is the real
  harness. It needs Claude Code signed in, and it captures dollar cost.
- **By hand.** `run_e2e_evals.py --prepare` makes clean work folders. Run the command and the skill files
  by hand in each (for example through subagents), then `--collect <label>` and `--score-only`. The saved runs
  in `runs/` were made this way, because headless sign-in was not available. `scorecard/e2e-provenance.json`
  says what that harness did not exercise.

The CardDemo checkout is expected at `../bench/carddemo`. See `carddemo/SOURCE.md` for the pinned
commit. The end to end runner calls `claude -p` with `--plugin-dir` pointing at this folder. It
needs Claude Code signed in. Every run is a real model call. Cap it with `--budget-usd`.

## Rules

1. **Truth is written before the code it grades.** Otherwise the eval grades the extractor against
   itself.
2. **Never edit a truth file or a threshold to make a metric pass.** If a metric fails, record it
   with a diagnosis. If the truth looks wrong, say so in `RESULTS.md` and let a reviewer decide.
3. **The CardDemo truth is a draft.** Claude subagents labeled it from the source, twice for the
   COBOL, and one disagreement was settled by reading the source. See `carddemo/LABELING.md` and
   `carddemo/ADJUDICATION.md`. No mainframe engineer has confirmed it yet.
4. **The labelers and the extractor share definitions.** Both follow `carddemo/LABELING.md`. A high
   score means the extractor applies the rules the way a careful reader does. It does not prove the
   rules are right. A domain reviewer has to judge the rules.

## How the truth was made

Fixtures: written by hand from numbered listings of the fixture source, before the extractor
existed. Fixtures 17 to 24 were added later. 17 came from a real miss on CardDemo. 18 to 24 closed
blind spots the mutation check found. Their truth was written the same way, by hand, from the
source, before the fix or the run.

CardDemo: nine independent labeler runs. Each read the source and never saw the extractor. The two
passes on each COBOL partition agreed on nearly every edge. Contract edges are derived from the
labeled data edges by the rule in the labeling guide.

## A note on Anthropic's own eval runner

`claude plugin eval` treats `<plugin>/evals/` as its case folder, but only counts a folder as a case
when it holds a `prompt.md` or a `case.yaml`. Nothing here does. Its results go to
`evals/results/`, which this repo ignores. Ours go to `evals/scorecard/` and `evals/runs/`.
