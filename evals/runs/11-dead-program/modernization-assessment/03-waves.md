# 03 Waves

Target state: **refactor**. This is the middle case. The plan below would change little under rehost or replatform, because the tree is too small for the target to move the cut.

## Verdict: one wave

The live system is one JCL job, one step, and a two-program call chain. There is no dataset, no contract edge and no ordering edge inside it (`modernization-assessment/graph.json:184`). A system this size is one wave. Cutting it would create waves that fail the four tests: they could not be rolled back or tested apart.

## The wave

| Wave | Units | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|
| 1. Nightly batch cycle, whole tree | `job:MAINJOB`, `PGMMAIN`, `PGMLIVE` | medium | medium | Retiring the COBOL runtime for this cycle. A proven toolchain and harness for whatever else the client has outside this tree. | `app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMLIVE.cbl:4` |

Step `step:MAINJOB.S1` moves with its job. It is not listed as a unit.

## The four validity tests

| Test | Holds? | Evidence |
|---|---|---|
| Deployable independently, behind a flag or facade | Yes. Run the refactored job beside MAINJOB and switch the scheduler entry. The tree has no shared dataset to guard. | `app/jcl/MAINJOB.jcl:2` |
| Rollback independently | Yes. Keep MAINJOB in the scheduler as the fallback. Rollback is a scheduler switch. This assumes the cycle writes nothing irreversible, which the tree cannot show (inference). | inference |
| Testable boundary | Partly. The boundary is the job's return code and any output it produces. The tree shows no output, so the boundary cannot be named yet. See `06-test-strategy.md`. | `app/jcl/MAINJOB.jcl:1` |
| Delivers something a stakeholder can name | Yes, on one assumption: MAINJOB is the nightly batch cycle the client said must not break. Nothing in the tree confirms that (inference). | inference |

## Why the blast radius is medium, not low

The risk quadrants put PGMLIVE at low-low, and PGMMAIN and MAINJOB at low-high (`modernization-assessment/risks.json:13`, `modernization-assessment/risks.json:38`, `modernization-assessment/risks.json:63`). All three are trivial to port. They are not cheap to get wrong, because they are by inference the path the client named as must not break.

The ordering rule says early waves should buy learning at low blast radius. This system cannot follow it, because the only live wave is the must-not-break cycle. The mitigation is process, not sequence: shadow the refactored job against MAINJOB for several nights before cutover, and keep MAINJOB as the fallback.

## Units left out of every wave

| Unit | Why | Evidence |
|---|---|---|
| PGMDEAD | Unreachable from any entry point. It is not ported. Propose deletion once instrumentation or out-of-tree JCL confirms it never runs. | `app/cbl/PGMDEAD.cbl:4` |
| cpy:UNUSED | No program includes it. It is not ported. Propose deletion. | `app/cpy/UNUSED.cpy:1` |

## If the system were ten times larger

This is inference from how the plan would scale, not something read in the tree.

1. Wave 1: leaf subprograms with no dataset edges and one live caller, the shape PGMLIVE has. They prove the toolchain and the harness.
2. Wave 2: batch programs with private datasets and no `medium` contract edges.
3. Wave 3 and later: programs that write shared datasets, cut at the articulation points and data hubs the extractor computes, with any strongly connected component moving as one unit.
4. Last: god modules and anything high-high, strangled behind a facade.

Business value would lead only from wave three.
