# CardDemo benchmark source

| | |
|---|---|
| Repository | https://github.com/aws-samples/aws-mainframe-modernization-carddemo |
| Pinned commit | `59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e` |
| Commit date | 2025-10-16 |
| License | Apache License 2.0 (checked in `LICENSE` and `README.md` at the pinned commit) |
| Copyright | Amazon.com, Inc. or its affiliates (see `NOTICE` in this repo) |
| Cloned to | `../bench/carddemo`, outside this repository |
| Clone date | 2026-09-30 |

To reproduce:

```bash
git clone https://github.com/aws-samples/aws-mainframe-modernization-carddemo ../bench/carddemo
git -C ../bench/carddemo checkout 59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e
```

## What is graded

The core application: `app/cbl`, `app/cpy`, `app/cpy-bms`, `app/bms`,
`app/jcl`, `app/proc`, `app/csd`, `app/scheduler`, and `scripts`.

The three optional extensions under `app/app-*` use IMS, DB2 and MQ. The
plugin does not claim those. The extractor still reads them. Their edges are
left out of the score.

## Truth status

`truth.json` is a DRAFT. See `LABELING.md` for how it was made and
`ADJUDICATION.md` for what was disputed. Every score against it is
provisional until a domain reviewer confirms or corrects it.
