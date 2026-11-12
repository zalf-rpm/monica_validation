#!/usr/bin/env python3
"""Add a MONICA validation run to this site.

    python update.py --validation DIR --commit SHA --date ISO-DATE \
                     --message "commit message" [--tag 3.7.5] [--keep 50]

DIR is the output of tests/validate.py in zalf-rpm/monica (validation.json,
report.html). The run goes into runs/<date>-<commit>/ and its statistics into
history.json, which index.html shows over time. A commit seen before (e.g. a
master push and then its release tag) updates its entry instead of adding one.

Reports with plots (a few MB each) are kept for every release and for the
last --keep runs; older ones are deleted, their statistics stay. Only the
standard library is used.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent
HISTORY = SITE / "history.json"
RUNS = SITE / "runs"
# per statistics record, in this order (see tests/validate.py)
FIELDS = ["n", "obs_mean", "sim_mean", "bias", "mae", "rmse", "nrmse", "r2", "d", "nse"]


def compact(stats: dict) -> list:
    """A statistics dict as a list of FIELDS, rounded to 4 significant digits."""
    out = []
    for f in FIELDS:
        v = stats.get(f)
        out.append(v if v is None or isinstance(v, int) else float(f"{v:.4g}"))
    return out


def sets_of(validation: dict) -> dict:
    """{"suite: name": {...}} with the statistics overall and per group."""
    out = {}
    for suite, sets in validation["suites"].items():
        for name, st in sets.items():
            out[f"{suite}: {name}"] = {
                "unit": st.get("unit", ""),
                "group": st.get("group", ""),
                "all": compact(st["all"]),
                "groups": {g: compact(s) for g, s in st.get("groups", {}).items()},
                "unmatched": st.get("unmatched", 0),
            }
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--validation", type=Path, required=True,
                   help="directory with validation.json and report.html")
    p.add_argument("--commit", required=True, help="full MONICA commit hash")
    p.add_argument("--date", required=True, help="commit date, ISO 8601")
    p.add_argument("--message", default="", help="commit message")
    p.add_argument("--tag", help="release tag of this commit, if any")
    p.add_argument("--keep", type=int, default=50,
                   help="keep the reports of this many latest runs (default 50; "
                        "releases always)")
    a = p.parse_args()

    validation = json.loads((a.validation / "validation.json").read_text(encoding="utf-8"))
    history = (json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.is_file()
               else {"fields": FIELDS, "runs": []})
    if history.get("fields") != FIELDS:
        sys.exit(f"error: {HISTORY} has other fields than this script, convert it first")

    entry = next((r for r in history["runs"] if r["commit"] == a.commit), None)
    if entry is None:
        entry = {"id": f"{a.date[:10]}-{a.commit[:10]}", "commit": a.commit, "tags": []}
        history["runs"].append(entry)
    if a.tag and a.tag not in entry["tags"]:
        entry["tags"].append(a.tag)
    entry.update({
        "date": a.date,
        "message": a.message.strip().splitlines()[0][:200] if a.message.strip() else "",
        "version": validation["monica"]["version"],
        "inputs": validation.get("inputs", {}),
        "sets": sets_of(validation),
    })

    run_dir = RUNS / entry["id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(a.validation / "validation.json", run_dir / "validation.json")
    report = a.validation / "report.html"
    entry["report"] = report.is_file()
    if entry["report"]:
        shutil.copy2(report, run_dir / "report.html")

    history["runs"].sort(key=lambda r: r["date"])
    for r in history["runs"][:-a.keep] if a.keep > 0 else history["runs"]:
        if r.get("report") and not r["tags"]:
            (RUNS / r["id"] / "report.html").unlink(missing_ok=True)
            r["report"] = False

    HISTORY.write_text(json.dumps(history, separators=(",", ":"), ensure_ascii=False) + "\n",
                       encoding="utf-8")
    print(f"{entry['id']}: {len(entry['sets'])} measured quantities, "
          f"{len(history['runs'])} runs in history.json")


if __name__ == "__main__":
    main()
