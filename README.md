# MONICA: simulated vs measured over time

**Site: https://zalf-rpm.github.io/monica_validation/**

How well [MONICA](https://github.com/zalf-rpm/monica) reproduces the
measurements of its test suites, for every commit to master and every release:
yields and soil organic carbon of
[muencheberg_v140](https://github.com/zalf-rpm/muencheberg_v140), N and water
leaching of the [microlysimeters](https://github.com/zalf-rpm/microlysimeter).

This repository is written by MONICA's CI (the `validate` job in
`.github/workflows/build.yml`), not by hand. For every push to master and
every tag it runs the test suites, compares them with the measurements
(`tests/validate.py`, see `tests/README.md` in MONICA) and calls `update.py`
here, which

- stores the run in `runs/<date>-<commit>/`: `validation.json` (the
  statistics) and `report.html` (statistics and plots: simulated time series as
  lines, measurements as dots)
- adds its statistics to `history.json`, which `index.html` shows over time

`report.html` is a few MB, so it is kept for every release and for the latest
50 runs only; the statistics of all runs stay.

## Files

| Path | Purpose |
| --- | --- |
| `index.html` | The overview page: statistics over time per measured quantity, latest run vs last release, list of runs. Plain HTML/JavaScript, reads `history.json`. |
| `history.json` | Statistics of all runs (overall and per group), commit, date, message, release tags, and the commits of the scenarios and parameters used. |
| `runs/` | One directory per run. |
| `update.py` | Adds a run (called by MONICA's CI). |

## Setup

MONICA's workflow pushes here with a deploy key (write access), whose private
key is the `VALIDATION_DEPLOY_KEY` secret of zalf-rpm/monica. GitHub Pages
serves the `main` branch; `.nojekyll` makes it serve the files as they are.

To try `update.py` locally, with the output directory of `tests/validate.py`:

    python update.py --validation ../monica/validation --commit <sha> \
        --date 2026-11-12T10:00:00Z --message "..." [--tag <tag>]
