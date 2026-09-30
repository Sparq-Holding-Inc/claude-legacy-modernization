# 03 Waves

Target state: `refactor`, as given in `--target`. The plan is in `waves.json`. Scores are in
`risks.json`, which I wrote inline following the `migration-risk-assessor` instructions.

## The answer: one wave

The tree is two programs, one copybook, one CSD and one dataset. The extractor found no call edge, no
cycle, no god module and no scheduler file. I did not invent a second wave. A system this size is one
wave.

| Wave | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|
| 1. ACCTDAT online pair | PROGR, PROGW | high (set by PROGW) | low | `app/csd/DEMO.CSD:4`, `app/csd/DEMO.CSD:6`, `app/cbl/PROGW.cbl:7`, `app/cbl/PROGR.cbl:7` |

The four validity tests for the wave:

- Deploys independently: yes, behind a transaction switch. TRNW runs PROGW and TRNR runs PROGR
  (`app/csd/DEMO.CSD:4-7`).
- Rolls back independently: yes, by pointing the transaction back at the legacy program. `inference`.
  This holds only while the ACCTREC layout stays byte for byte the same.
- Has a testable boundary: yes. The boundary is the 17 byte ACCTREC record in the KSDS
  (`app/cpy/ACCTREC.cpy:1-3`).
- Delivers something a stakeholder can name: online account read and account write. This is weak,
  because the programs are stubs. `inference`.

## Order inside the wave

The two quadrants differ, so the order inside the wave matters.

| Unit | Quadrant | Port difficulty | Blast radius | Evidence |
|---|---|---|---|---|
| PROGR | low-low | 1 | 2 | `app/cbl/PROGR.cbl:7` |
| PROGW | low-high | 2 | 4 | `app/cbl/PROGW.cbl:7`, `app/cpy/ACCTREC.cpy:3` |

1. Port PROGR first. It is read only. It proves the toolchain and the COMP-3 decode against real
   ACCTDAT records, with almost no blast radius.
2. Port PROGW second, and only after the equivalence harness for the ACCTREC record is proven on the
   reader side. It is low-high: the port is easy and the verification is the work. It writes the
   account file, so cut it over last and behind a switch.

Neither program is high-high, so nothing has to be strangled behind a facade at this size.

## What this wave unblocks

The decision on where the ACCTDAT KSDS lives after refactor, and a byte level harness for the ACCTREC
record. If the nightly batch cycle is later supplied, that harness is what a batch wave reuses.
`inference`: the tree has no later wave to unblock.

## Risks to the plan

- The must-not-break item, the nightly batch cycle, has no artifact in the tree
  (`graph.json` `meta.files_seen` shows 0 JCL, 0 proc, 0 scheduler). The wave is only defensible for
  the part of the system that is present. `inference`.
- The wave confidence is low because the one dataset the CSD names is a TEST dataset
  (`app/csd/DEMO.CSD:2`).

## What I would cut if the system were ten times larger

Cut at the seam the extractor found: the dataset that is the articulation point
(`app/cbl/PROGW.cbl:7`, `app/cbl/PROGR.cbl:7`). `inference`:

1. Read only inquiry transactions like TRNR first, to prove the toolchain and the layout harness.
2. Writers like TRNW second, once the harness is proven, with dataset ownership moving with the
   writer wave.
3. Any batch job that reads or writes ACCTDAT last, because it is the must-not-break path and its
   order against the online writes is a temporal edge the harness must keep.

A strongly connected component would move as one unit. This system has none.
