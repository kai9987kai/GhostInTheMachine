"""
Command-line interface for the v6 studies.

    python src/ghost_in_the_machine_v6.py pilot                 # technical pilot on development seeds
    python src/ghost_in_the_machine_v6.py lock                  # freeze the v6 preregistration
    python src/ghost_in_the_machine_v6.py verify
    python src/ghost_in_the_machine_v6.py run --study all       # G, I, J
    python src/ghost_in_the_machine_v6.py analyze               # preregistered tests -> results_v6.json, SUMMARY_v6.md
    python src/ghost_in_the_machine_v6.py posthoc               # exploratory equivalence re-reading of the v5 nulls
    python src/ghost_in_the_machine_v6.py report                # figures
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

DEFAULT_OUT = pr.ROOT / "results" / "v6"
ANALYZERS = {"G": S.analyze_G, "I": S.analyze_I, "J": S.analyze_J}


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
        raise SystemExit(f"v6 preregistration lock does not verify ({bad}). Run `lock` first, "
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
            print(f"{st} {n:52s} mean={t['mean_diff']:+.4f} d_z={t['d_z']:+.2f} p={t['p']:.3f}")


def cmd_lock(args) -> None:
    print(json.dumps(pr.lock(), indent=2))
    print("\nCommit and push prereg/ NOW, before running any confirmatory study.")


def cmd_verify(args) -> None:
    ok, bad, _ = pr.verify()
    print("v6 lock verifies" if ok else f"v6 lock MISMATCH: {bad}")
    sys.exit(0 if ok else 1)


def cmd_run(args) -> None:
    status = _status(args)
    doc = pr.load()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    studies = list(S.RUNNERS) if args.study == "all" else [args.study]
    write_json(out / "manifest_v6.json", {"status": status, "studies": studies, "version": __version__,
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
    if (out / "manifest_v6.json").exists():
        results["status"] = json.loads((out / "manifest_v6.json").read_text())["status"]
    studies = {k: fn(out / k) for k, fn in ANALYZERS.items() if (out / k / "runs_coded.json").exists()}
    results["studies"] = studies
    results["across_study_holm"] = S.across_study_holm(studies)
    if (out / "posthoc_v5_equivalence.json").exists():
        results["posthoc_v5"] = json.loads((out / "posthoc_v5_equivalence.json").read_text())
    if "J" in studies:
        results["descriptive"] = {"J_direction_counts": _direction_counts(out / "J"),
                                  "note": "post-lock descriptive statistics; not hypothesis tests"}
    if all(k in studies for k in ("G", "J")):
        from .meta import run as meta_run
        results["meta_analysis"] = meta_run(pr.ROOT)
    write_json(out / "results_v6.json", results)
    from .report import write_summary
    write_summary(results, out / "SUMMARY_v6.md")
    print((out / "SUMMARY_v6.md").read_text(encoding="utf-8"))


def _direction_counts(run_dir: Path) -> dict:
    """Networks with master > twin at each gain, an exact sign-test p and the median difference."""
    import math

    import numpy as np
    from ghost_v5.studies import _col, _load
    data, seeds = _load(run_dir)
    out = {}
    for k in S.GAINS_J:
        d = _col(data, seeds, f"gain{k:g}", "master", "self_persistence") - _col(data, seeds, f"gain{k:g}", "twin", "self_persistence")
        n, pos = len(d), int(np.sum(d > 0))
        p = sum(math.comb(n, i) for i in range(pos, n + 1)) / 2 ** n
        out[f"gain{k:g}"] = {"positive": pos, "n": n, "sign_test_p_one_sided": p, "median_diff": float(np.median(d))}
    return out


def cmd_posthoc(args) -> None:
    from .posthoc_v5 import run
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    res = run(pr.ROOT)
    write_json(out / "posthoc_v5_equivalence.json", res)
    print(json.dumps(res, indent=1)[:4000])


def cmd_report(args) -> None:
    from .report import make_figures
    results = json.loads((Path(args.out) / "results_v6.json").read_text())
    for p in make_figures(results, Path(args.figures)):
        print("wrote", p)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="ghost_in_the_machine_v6", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("pilot")
    a.add_argument("--out", default=str(pr.ROOT / "results" / "v6_pilot"))
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
    ph = sub.add_parser("posthoc")
    ph.add_argument("--out", default=str(DEFAULT_OUT))
    ph.set_defaults(fn=cmd_posthoc)
    rep = sub.add_parser("report")
    rep.add_argument("--out", default=str(DEFAULT_OUT))
    rep.add_argument("--figures", default=str(pr.ROOT / "figures"))
    rep.set_defaults(fn=cmd_report)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
