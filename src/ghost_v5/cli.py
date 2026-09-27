"""
Command-line interface for the v5 follow-up studies.

    python src/ghost_in_the_machine_v5.py pilot                 # technical pilot on development seeds
    python src/ghost_in_the_machine_v5.py lock                  # freeze the v5 preregistration
    python src/ghost_in_the_machine_v5.py verify
    python src/ghost_in_the_machine_v5.py run --study all       # A (replication) and B-F
    python src/ghost_in_the_machine_v5.py analyze               # preregistered tests -> results_v5.json, SUMMARY_v5.md
    python src/ghost_in_the_machine_v5.py report                # figures
    python src/ghost_in_the_machine_v5.py replicate --prereg prereg/REPLICATION_<name>.json --out results/replication_<name>
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from ghost_v4 import DISCLAIMER
from ghost_v4.campaign import analyze_v4, run_v4, write_json

from . import __version__
from . import prereg as pr
from . import studies as S

DEFAULT_OUT = pr.ROOT / "results" / "v5"


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
        raise SystemExit(f"v5 preregistration lock does not verify ({bad}). Run `lock` first, "
                         "or pass --allow-unlocked to produce EXPLORATORY output.")
    return "EXPLORATORY (lock mismatch)"


def _replication_spec(prereg_path: Path) -> dict:
    doc = json.loads(prereg_path.read_text(encoding="utf-8"))
    spec = dict(doc["design"]["common"])
    spec.update(doc["design"]["confirm"])
    return doc, spec


def cmd_pilot(args) -> None:
    _banner("TECHNICAL PILOT (development seeds; EXPLORATORY)")
    doc = pr.load()
    spec = dict(doc["pilot_spec"])
    out = Path(args.out)
    for study, runner in S.RUNNERS.items():
        sp = dict(spec)
        if study == "E":
            sp["burn"] = doc["studies"]["E"]["spec"]["burn"]
        print(f"[pilot {study}]")
        runner(sp, out / study, workers=args.workers)
    res = {"B": S.analyze_B(out / "B"), "D": S.analyze_D(out / "D"), "E": S.analyze_E(out / "E"),
           "F": S.analyze_F(out / "F")}
    write_json(out / "pilot_results.json", res)
    for st, r in res.items():
        for n, t in r["primary"].items():
            print(f"{st} {n:52s} mean={t['mean_diff']:+.4f} d_z={t['d_z']:+.2f} p={t['p']:.3f}")


def cmd_lock(args) -> None:
    print(json.dumps(pr.lock(), indent=2))
    print("\nCommit and push prereg/ NOW, before running any confirmatory study.")


def cmd_verify(args) -> None:
    ok, bad, _ = pr.verify()
    print("v5 lock verifies" if ok else f"v5 lock MISMATCH: {bad}")
    sys.exit(0 if ok else 1)


def cmd_run(args) -> None:
    status = _status(args)
    doc = pr.load()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    studies = list("ABCDEF") if args.study == "all" else [args.study]
    write_json(out / "manifest_v5.json", {"status": status, "studies": studies, "version": __version__,
                                          "lock": pr.verify()[2]})
    for study in studies:
        t = time.time()
        _banner(f"STUDY {study} — {status}")
        if study == "A":
            _, spec = _replication_spec(pr.REPLICATION_PATH)
            run_v4(spec, out / "A", workers=args.workers)
        else:
            S.RUNNERS[study](doc["studies"][study]["spec"], out / study, workers=args.workers)
        print(f"[study {study}] {time.time() - t:.0f}s")


def cmd_replicate(args) -> None:
    doc, spec = _replication_spec(Path(args.prereg))
    lock = Path(args.prereg).with_suffix(".lock.json")
    from ghost_v4 import prereg as p4
    ok = False
    if lock.exists():
        ok, bad, _ = p4.verify(Path(args.prereg), lock)
    _banner(f"REPLICATION — {'CONFIRMATORY' if ok else 'EXPLORATORY (no verified lock)'}")
    out = Path(args.out)
    run_v4(spec, out, workers=args.workers)
    res = analyze_v4(out, doc)
    write_json(out / "results_replication.json", res)
    print(f"verdict: level {res['verdict']['level']} — {res['verdict']['label']}")


def cmd_analyze(args) -> None:
    out = Path(args.out)
    ok, bad, payload = pr.verify()
    results = {"version": __version__, "disclaimer": DISCLAIMER,
               "preregistration": {"lock_verifies": ok, "mismatches": bad, "lock": payload}}
    if (out / "manifest_v5.json").exists():
        results["status"] = json.loads((out / "manifest_v5.json").read_text())["status"]
    rep_doc = json.loads(pr.REPLICATION_PATH.read_text())
    studies = {}
    if (out / "A" / "runs_coded.json").exists():
        studies["A"] = analyze_v4(out / "A", rep_doc)
    if (out / "B" / "runs_coded.json").exists():
        studies["B"] = S.analyze_B(out / "B")
    if (out / "C" / "runs_coded.json").exists():
        studies["C"] = S.analyze_C(out / "C", pr.ROOT / "results" / "v4" / "campaign")
    for k, fn in (("D", S.analyze_D), ("E", S.analyze_E), ("F", S.analyze_F)):
        if (out / k / "runs_coded.json").exists():
            studies[k] = fn(out / k)
    results["studies"] = studies
    if "B" in studies:
        from .report import b_within_network
        results["descriptive"] = {"B_within_network": b_within_network(out / "B"),
                                  "note": "post-lock descriptive statistics for figures; not hypothesis tests"}
    results["across_study_holm"] = S.across_study_holm(studies)
    write_json(out / "results_v5.json", results)
    from .report import write_summary
    write_summary(results, out / "SUMMARY_v5.md")
    print((out / "SUMMARY_v5.md").read_text())


def cmd_report(args) -> None:
    from .report import make_figures
    results = json.loads((Path(args.out) / "results_v5.json").read_text())
    for p in make_figures(results, Path(args.figures)):
        print("wrote", p)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="ghost_in_the_machine_v5", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("pilot")
    a.add_argument("--out", default=str(DEFAULT_OUT / "pilot"))
    a.add_argument("--workers", type=int, default=4)
    a.set_defaults(fn=cmd_pilot)
    sub.add_parser("lock").set_defaults(fn=cmd_lock)
    sub.add_parser("verify").set_defaults(fn=cmd_verify)
    r = sub.add_parser("run")
    r.add_argument("--study", choices=list("ABCDEF") + ["all"], default="all")
    r.add_argument("--out", default=str(DEFAULT_OUT))
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--allow-unlocked", action="store_true")
    r.set_defaults(fn=cmd_run)
    rp = sub.add_parser("replicate")
    rp.add_argument("--prereg", required=True)
    rp.add_argument("--out", required=True)
    rp.add_argument("--workers", type=int, default=4)
    rp.set_defaults(fn=cmd_replicate)
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
