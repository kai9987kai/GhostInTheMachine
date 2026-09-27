"""
Command-line interface for Ghost in the Machine v4.

    python src/ghost_in_the_machine_v4.py demo                  # one master + one yoked twin
    python src/ghost_in_the_machine_v4.py calibrate             # instrument calibration
    python src/ghost_in_the_machine_v4.py v3-forensics          # re-adjudicate v3
    python src/ghost_in_the_machine_v4.py campaign --phase dev  # exploratory seeds
    python src/ghost_in_the_machine_v4.py lock                  # freeze the preregistration
    python src/ghost_in_the_machine_v4.py campaign --phase confirm
    python src/ghost_in_the_machine_v4.py analyze               # preregistered tests + verdict
    python src/ghost_in_the_machine_v4.py report                # figures + summary
    python src/ghost_in_the_machine_v4.py all                   # everything above, in order
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from . import DISCLAIMER, __version__
from . import prereg as pr

DEFAULT_OUT = pr.ROOT / "results" / "v4"


def _banner(title: str) -> None:
    print("=" * 100)
    print(f"GHOST IN THE MACHINE v{__version__} — {title}")
    print("=" * 100)
    print(DISCLAIMER)
    print("-" * 100)


def cmd_demo(args) -> None:
    import numpy as np
    from .engine import AgentConfig, run_agent
    from .metrics import record_panel
    _banner("DEMO: one closed-loop agent and its cross-yoked twin")
    donor = run_agent(AgentConfig(net_seed=args.seed + 1, world_seed=11, steps=args.steps))
    master = run_agent(AgentConfig(net_seed=args.seed, world_seed=11, steps=args.steps))
    twin = run_agent(AgentConfig(net_seed=args.seed, world_seed=11, steps=args.steps), yoke=donor.stream())
    burn = min(2000, args.steps // 3)
    pm, pt = record_panel(master, burn), record_panel(twin, burn)
    keys = ["intention_outcome_match", "cf_agency", "te_net_to_obs", "self_persistence", "self_psi",
            "phi_r_mean", "irr_nodes", "prediction_error", "ignition"]
    print(f"{'metric':28s} {'master':>10s} {'yoked twin':>12s}")
    for k in keys:
        print(f"{k:28s} {pm[k]:10.4f} {pt[k]:12.4f}")
    print("\nSame network, same world, statistically matched input. Only authorship differs.")


def _phase_spec(prereg: dict, phase: str) -> dict:
    d = prereg["design"]
    spec = dict(d["common"])
    spec.update(d[phase])
    return spec


def cmd_calibrate(args) -> None:
    from .campaign import run_calibration
    prereg = pr.load_prereg()
    _banner("INSTRUMENT CALIBRATION (ground-truth systems)")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    res = run_calibration(prereg["calibration"], out, workers=args.workers)
    for r in res["rows"]:
        print(f"{r['system']:24s} {r['metric']:18s} {r['rung']:11s} {r['role']:38s} "
              f"rate={r['detection_rate']:.3f}  {'PASS' if r['pass'] else 'FAIL'}")
    print(f"all pass: {res['all_pass']}")


def cmd_v3(args) -> None:
    from .campaign import run_v3_forensics
    prereg = pr.load_prereg()
    _banner("v3 FORENSIC RE-ADJUDICATION")
    run_v3_forensics(prereg["v3_forensics"], Path(args.out), workers=args.workers)


def cmd_campaign(args) -> None:
    from .campaign import run_v4, write_json
    prereg = pr.load_prereg()
    out = Path(args.out)
    if args.phase == "confirm":
        ok, bad, payload = pr.verify()
        if not ok and not args.allow_unlocked:
            raise SystemExit(f"Preregistration lock does not verify (mismatch: {bad}). "
                             "Run `lock` before the confirmatory phase, or pass --allow-unlocked "
                             "to produce output labelled EXPLORATORY.")
        status = "CONFIRMATORY" if ok else "EXPLORATORY (lock mismatch)"
    else:
        status = "EXPLORATORY (development seeds)"
        payload = {}
    _banner(f"AUTHORSHIP CAMPAIGN — {args.phase} — {status}")
    spec = _phase_spec(prereg, args.phase)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "campaign_manifest.json", {"phase": args.phase, "status": status, "spec": spec,
                                                "lock": payload, "version": __version__})
    run_v4(spec, out, workers=args.workers)


def cmd_lock(args) -> None:
    payload = pr.lock()
    print(json.dumps(payload, indent=2))
    print("\nCommit prereg/ to git NOW, before running the confirmatory phase.")


def cmd_verify(args) -> None:
    ok, bad, payload = pr.verify()
    print("lock verifies" if ok else f"lock MISMATCH: {bad}")
    sys.exit(0 if ok else 1)


def cmd_analyze(args) -> None:
    from .campaign import analyze_v3, analyze_v4, write_json
    prereg = pr.load_prereg()
    out = Path(args.out)
    results = {"version": __version__, "disclaimer": DISCLAIMER}
    manifest = out / "campaign" / "campaign_manifest.json"
    if (out / "campaign" / "runs_coded.json").exists():
        results["campaign_status"] = json.loads(manifest.read_text())["status"] if manifest.exists() else "unknown"
        results["v4"] = analyze_v4(out / "campaign", prereg)
    if (out / "v3_forensics" / "v3_forensics_runs.json").exists():
        results["v3_forensics"] = analyze_v3(out / "v3_forensics")
    if (out / "calibration" / "calibration.json").exists():
        results["calibration"] = json.loads((out / "calibration" / "calibration.json").read_text())
    ok, bad, payload = pr.verify()
    results["preregistration"] = {"lock_verifies": ok, "mismatches": bad, "lock": payload}
    write_json(out / "results_v4.json", results)
    from .report import write_summary
    write_summary(results, out / "SUMMARY.md")
    print((out / "SUMMARY.md").read_text())


def cmd_report(args) -> None:
    from .report import make_figures
    out = Path(args.out)
    results = json.loads((out / "results_v4.json").read_text())
    for p in make_figures(results, out, Path(args.figures)):
        print("wrote", p)


def cmd_all(args) -> None:
    base = Path(args.out)
    for sub, fn in (("calibration", cmd_calibrate), ("v3_forensics", cmd_v3)):
        a = argparse.Namespace(**vars(args))
        a.out = str(base / sub)
        t = time.time()
        fn(a)
        print(f"[{sub}] {time.time() - t:.0f}s")
    a = argparse.Namespace(**vars(args))
    a.out = str(base / "campaign")
    cmd_campaign(a)
    a.out = str(base)
    cmd_analyze(a)
    cmd_report(a)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="ghost_in_the_machine_v4", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo", help="one master + one cross-yoked twin")
    d.add_argument("--seed", type=int, default=7)
    d.add_argument("--steps", type=int, default=6000)
    d.set_defaults(fn=cmd_demo)

    for name, fn, default_sub in (("calibrate", cmd_calibrate, "calibration"),
                                  ("v3-forensics", cmd_v3, "v3_forensics")):
        s = sub.add_parser(name)
        s.add_argument("--out", default=str(DEFAULT_OUT / default_sub))
        s.add_argument("--workers", type=int, default=4)
        s.set_defaults(fn=fn)

    c = sub.add_parser("campaign")
    c.add_argument("--phase", choices=("dev", "confirm"), required=True)
    c.add_argument("--out", default=None)
    c.add_argument("--workers", type=int, default=4)
    c.add_argument("--allow-unlocked", action="store_true")
    c.set_defaults(fn=cmd_campaign)

    sub.add_parser("lock").set_defaults(fn=cmd_lock)
    sub.add_parser("verify").set_defaults(fn=cmd_verify)

    a = sub.add_parser("analyze")
    a.add_argument("--out", default=str(DEFAULT_OUT))
    a.set_defaults(fn=cmd_analyze)

    r = sub.add_parser("report")
    r.add_argument("--out", default=str(DEFAULT_OUT))
    r.add_argument("--figures", default=str(pr.ROOT / "figures"))
    r.set_defaults(fn=cmd_report)

    al = sub.add_parser("all")
    al.add_argument("--out", default=str(DEFAULT_OUT))
    al.add_argument("--workers", type=int, default=4)
    al.add_argument("--figures", default=str(pr.ROOT / "figures"))
    al.add_argument("--allow-unlocked", action="store_true")
    al.add_argument("--phase", default="confirm")
    al.set_defaults(fn=cmd_all)

    args = p.parse_args(argv)
    if getattr(args, "cmd", None) == "campaign" and args.out is None:
        args.out = str(DEFAULT_OUT / ("campaign" if args.phase == "confirm" else "dev_campaign"))
    args.fn(args)


if __name__ == "__main__":
    main()
