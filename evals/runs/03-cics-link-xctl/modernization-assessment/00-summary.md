# 00 Summary

Assessment of the tree at `.` (four COBOL programs under `app/cbl/`). Run non-interactively.

## Scoping answers

- Target state: refactor (given as a flag).
- What must not break: "the nightly batch cycle" (given as a flag).
- Runtime telemetry: none (given as a flag). Every dead-code claim is provisional.
- Defaults: no defaults applied. All three answers came as flags.

## The system as extracted

Four CICS programs, 38 lines in all. PROGA calls PROGB by LINK, PROGC by XCTL and PROGD by XCTL, and has
one more LINK whose target comes from its COMMAREA (analysis: `edge_counts`, `unresolved_dynamic`;
`app/cbl/PROGA.cbl:12`, `app/cbl/PROGA.cbl:16`, `app/cbl/PROGA.cbl:20`, `app/cbl/PROGA.cbl:23`). The tree holds no
copybook, no JCL, no CICS system definition, no scheduler and no dataset (analysis: `meta.files_seen`).
No entry point was found, so nothing can be proven reachable or unreachable.

## Wave count

1. The seed placed none, because it found no entry point. I placed the four programs in one wave by
   deviation, because the plan validator needs at least one wave and because PROGA is the single
   articulation point. Treat it as a placeholder, at low confidence, that unblocks nothing nameable
   (`03-waves.md`; `app/cbl/PROGA.cbl:16`).

## Largest risk

PROGA's LINK at line 16 takes its target from the caller's COMMAREA (`app/cbl/PROGA.cbl:15`,
`app/cbl/PROGA.cbl:16`). What it can reach cannot be bounded from this tree. A port that fixes the target
set will misroute any caller that passes a name not on the list, and it will do so without a compile error.
PROGA is the only high-high unit in `risks.json` (`modernization-assessment/risks.json:13`). It goes last, behind a
facade that keeps the program-name contract.

The client's stated must-not-break item is a related blind spot. The nightly batch cycle is not in the
tree, so I cannot say whether these programs touch it.

## Other findings

- The XCTL at line 20 never returns, so the XCTL to PROGD at line 23 and the RETURN at line 26 cannot run.
  PROGD is not thereby dead, because the COMMAREA-driven LINK could reach it (inference:
  `app/cbl/PROGA.cbl:20`, `app/cbl/PROGA.cbl:23-26`).
- The computed XCTL at line 20 is bounded to PROGC, by the one assignment at line 19 (inference:
  `app/cbl/PROGA.cbl:19`, `app/cbl/PROGA.cbl:20`).
- PROGB, PROGC and PROGD are four-line RETURN programs. Either they are stubs in this copy, or they are
  truly empty (`app/cbl/PROGB.cbl:4`, `app/cbl/PROGC.cbl:4`, `app/cbl/PROGD.cbl:4`).
- Dormancy was not measured: no git dates. The dead-code register has four unknown units and nothing
  else (`05-dead-code.md`).
- Estimate for wave 1: about 9 to 28 person-days, mostly discovery and harness, not code (`04-estimate.md`).

## Open Questions

For the client's own engineers.

1. Where are the JCL, PROCs and scheduler definitions for "the nightly batch cycle"? The tree has none
   (analysis: `meta.files_seen`). Does any batch step start PROGA, PROGB, PROGC or PROGD, for example
   through an external CICS interface, or write the values PROGA reads?
2. What fills PROGA's COMMAREA, and which program names does it hold in production? The LINK at
   `app/cbl/PROGA.cbl:16` cannot be bounded without that. Is there an allow-list anywhere?
3. Which CICS transaction starts PROGA? No CSD is in the tree, so no entry point was found. Are PROGB,
   PROGC and PROGD the real production programs, or stubs? Each holds only a RETURN
   (`app/cbl/PROGB.cbl:4`).
4. Lines 23 to 26 of PROGA follow an XCTL that never returns. Are they leftovers, or is a HANDLE
   CONDITION or RESP handled elsewhere in the region's setup? Is PROGD ever run
   (`app/cbl/PROGA.cbl:20`, `app/cbl/PROGA.cbl:23-26`)?
5. What should happen when PROGA gets no COMMAREA, or fewer than 8 bytes? Line 15 reads it without an
   EIBCALEN test (`app/cbl/PROGA.cbl:15`). And what should a missing target do: abend, as today, or
   something else (`app/cbl/PROGA.cbl:16`)?
6. Can they supply 12 months of CICS program usage statistics or SMF 110 records? Without them the four
   unknown items stay unknown, and dormancy stays unmeasured (analysis: `warnings`).
7. Is this tree a full copy of the source, or a slice? It is not a git repository, so no history is
   available (analysis: `meta.git_dates`).

## Limits in `meta.limits` that touch this system

- A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program. This
  is why the target at `app/cbl/PROGA.cbl:16` stays open and the one at `app/cbl/PROGA.cbl:20` stays open
  though the source bounds it.
- LINK and XCTL are both call edges and control flow is not modeled. This is why the PROGA to PROGD edge
  at `app/cbl/PROGA.cbl:23` reads as a live edge.
- RETURN TRANSID, START and SEND MAP are not edges. None appears in these four programs, but a chain
  through other programs would not show.
- Files not parsed: none (analysis: `unparsed`).

## Files in this folder

`01-inventory.md`, `02-coupling.md`, `02a-edge-tables.md`, `03-waves.md`, `03a-wave-seed.md`,
`03a-waves-draft.json`, `04-estimate.md`, `05-dead-code.md`, `05a-dead-code-candidates.md`,
`06-test-strategy.md`, `graph.json`, `waves.json`, `dead-code.json`, `risks.json`.
