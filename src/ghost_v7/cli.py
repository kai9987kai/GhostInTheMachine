"""
Command-line interface for the v7 studies.

    python src/ghost_in_the_machine_v7.py pilot                 # technical pilot on development seeds
    python src/ghost_in_the_machine_v7.py lock                  # freeze the v7 preregistration
    python src/ghost_in_the_machine_v7.py verify
    python src/ghost_in_the_machine_v7.py run --study all       # K, L, M
    python src/ghost_in_the_machine_v7.py analyze               # preregistered tests + prespecified meta-analysis
    python src/ghost_in_the_machine_v7.py report                # figures
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from ghost_v4 import DISCLAIMER
from ghost_v4.campaign import write_json

from . import __version__
from . import prereg as pr
from . import studies as S

DEFAULT_OUT = pr.ROOT / "results" / "v7"
ANALYZERS = {"K": S.analyze_K, "L": S.analyze_L, "M": S.analyze_M}


def _banner(title: str) -> None:
    print("=" * 100)
    print(f"GHOST IN THE MACHINE v{__version__} — {title}")
    print("=" * 100)
    print(DISCLAIMER)
    print("-" * 100)


def _status(args) -> str:
    ok, bad, _ = pr.verify()
    if ok:
        return "CONFIRMATORY"
    if not getattr(args, "allow_unlocked", False):
        raise SystemExit(f"v7 preregistration lock does not verify ({bad}). Run `lock` first, "
                         "or pass --allow-unlocked to produce EXPLORATORY output.")
    return "EXPLORATORY (lock mismatch)"


def cmd_pilot(args) -> None:
    _banner("TECHNICAL PILOT (development seeds; EXPLORATORY)")
    doc = pr.load()
    out = Path(args.out)
    res = {}
    for study, runner in S.RUNNERS.items():
        print(f"[pilot {study}]")
        runner(dict(doc["pilot_spec"]), out / study, workers=args.workers)
        res[study] = ANALYZERS[study](out / study)
    write_json(out / "pilot_results.json", res)
    for st, r in res.items():
        for n, t in r["primary"].items():
            est = t.get("hodges_lehmann", t["mean_diff"])
            print(f"{st} {n:48s} estimate={est:+.4f} d_z={t['d_z']:+.2f} p={t['p']:.3f}")


def cmd_lock(args) -> None:
    print(json.dumps(pr.lock(), indent=2))
    print("\nCommit and push prereg/ NOW, before running any confirmatory study.")


def cmd_verify(args) -> None:
    ok, bad, _ = pr.verify()
    print("v7 lock verifies" if ok else f"v7 lock MISMATCH: {bad}")
    sys.exit(0 if ok else 1)


def cmd_run(args) -> None:
    status = _status(args)
    doc = pr.load()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    studies = list(S.RUNNERS) if args.study == "all" else [args.study]
    write_json(out / "manifest_v7.json", {"status": status, "studies": studies, "version": __version__,
                                          "lock": pr.verify()[2]})
    for study in studies:
        t = time.time()
        _banner(f"STUDY {study} — {status}")
        S.RUNNERS[study](doc["studies"][study]["spec"], out / study, workers=args.workers)
        print(f"[study {study}] {time.time() - t:.0f}s")


def cmd_analyze(args) -> None:
    out = Path(args.out)
    ok, bad, payload = pr.verify()
    results = {"version": __version__, "disclaimer": DISCLAIMER,
               "preregistration": {"lock_verifies": ok, "mismatches": bad, "lock": payload}}
    if (out / "manifest_v7.json").exists():
        results["status"] = json.loads((out / "manifest_v7.json").read_text())["status"]
    studies = {k: fn(out / k) for k, fn in ANALYZERS.items() if (out / k / "runs_coded.json").exists()}
    results["studies"] = studies
    results["across_study_holm"] = S.across_study_holm(studies)
    if all(k in studies for k in ANALYZERS):
        from .meta import run as meta_run
        results["meta_analysis"] = meta_run(pr.ROOT)
    write_json(out / "results_v7.json", results)
    from .report import write_summary
    write_summary(results, out / "SUMMARY_v7.md")
    print((out / "SUMMARY_v7.md").read_text(encoding="utf-8"))


def cmd_report(args) -> None:
    from .report import make_figures
    results = json.loads((Path(args.out) / "results_v7.json").read_text())
    for p in make_figures(results, Path(args.figures)):
        print("wrote", p)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="ghost_in_the_machine_v7", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("pilot")
    a.add_argument("--out", default=str(pr.ROOT / "results" / "v7_pilot"))
    a.add_argument("--workers", type=int, default=4)
    a.set_defaults(fn=cmd_pilot)
    sub.add_parser("lock").set_defaults(fn=cmd_lock)
    sub.add_parser("verify").set_defaults(fn=cmd_verify)
    r = sub.add_parser("run")
    r.add_argument("--study", choices=list(S.RUNNERS) + ["all"], default="all")
    r.add_argument("--out", default=str(DEFAULT_OUT))
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--allow-unlocked", action="store_true")
    r.set_defaults(fn=cmd_run)
    an = sub.add_parser("analyze")
    an.add_argument("--out", default=str(DEFAULT_OUT))
    an.set_defaults(fn=cmd_analyze)
    rep = sub.add_parser("report")
    rep.add_argument("--out", default=str(DEFAULT_OUT))
    rep.add_argument("--figures", default=str(pr.ROOT / "figures"))
    rep.set_defaults(fn=cmd_report)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
