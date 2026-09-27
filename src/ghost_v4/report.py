"""Human-readable summary and figures for a v4 results bundle."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List


def _f(x, nd=3):
    if x is None:
        return "n/a"
    try:
        return f"{x:.{nd}f}"
    except (TypeError, ValueError):
        return str(x)


def _p(x):
    if x is None:
        return "n/a"
    return "<0.001" if x < 0.001 else f"{x:.3f}"


def write_summary(results: Dict, path: Path) -> None:
    L: List[str] = []
    L.append("# Ghost in the Machine v4 — results summary\n")
    L.append(f"> {results['disclaimer']}\n")
    pre = results.get("preregistration", {})
    L.append(f"Preregistration lock verifies: **{pre.get('lock_verifies')}**"
             + (f" (mismatches: {pre.get('mismatches')})" if not pre.get("lock_verifies") else "")
             + (f" · locked at {pre.get('lock', {}).get('locked_at_utc')}" if pre.get("lock") else "") + "\n")

    v4 = results.get("v4")
    if v4:
        L.append(f"## Authorship campaign ({results.get('campaign_status')}, {v4['n_seeds']} network seeds)\n")
        vd = v4["verdict"]
        L.append(f"**Verdict: level {vd['level']} — {vd['label']}**\n")
        g = v4["gate_manipulation_check"]
        L.append(f"Gate M (authorship is real; TE network→world): diff {_f(g['mean_diff'], 4)}, "
                 f"d_z {_f(g['d_z'], 2)}, p {_p(g['p'])} → {'PASS' if g['pass'] else 'FAIL'}\n")
        L.append("| Hypothesis | mean diff [95% CI] | d_z | p (one-sided) | p (Holm) | result |")
        L.append("|---|---|---|---|---|---|")
        for name, r in v4["primary"].items():
            ci = r["ci95"]
            L.append(f"| {name} | {_f(r['mean_diff'], 4)} [{_f(ci[0], 4)}, {_f(ci[1], 4)}] | {_f(r['d_z'], 2)} | "
                     f"{_p(r['p'])} | {_p(r['p_holm'])} | {'supported' if r['significant'] else 'not supported'} |")
        L.append("")
        L.append("Placebo A/A contrasts (same network, no authorship difference; should be null):\n")
        L.append("| endpoint | mean diff | d_z | p (two-sided) |")
        L.append("|---|---|---|---|")
        for m, r in v4["placebo_AA"].items():
            L.append(f"| {m} | {_f(r['mean_diff'], 4)} | {_f(r['d_z'], 2)} | {_p(r['p'])} |")
        L.append("")
        L.append("Emergence atlas — authorship effect on macro persistence per population:\n")
        L.append("| population | mean diff | d_z | p | q (BH) |")
        L.append("|---|---|---|---|---|")
        for p, r in v4["atlas"].items():
            q = r["persistence"]
            L.append(f"| {p} | {_f(q['mean_diff'], 4)} | {_f(q['d_z'], 2)} | {_p(q['p'])} | {_p(q.get('q_bh'))} |")
        L.append("")
        L.append("Secondary (exploratory, two-sided, BH-FDR):\n")
        L.append("| contrast | mean diff | d_z | p | q |")
        L.append("|---|---|---|---|---|")
        for n, r in v4["secondary"].items():
            L.append(f"| {n} | {_f(r['mean_diff'], 4)} | {_f(r['d_z'], 2)} | {_p(r['p_two_sided'])} | {_p(r['q_bh'])} |")
        L.append("")
        L.append("Specificity fingerprint (median z of real vs null; * = in ≥50% of seeds real differs from its "
                 "surrogates at p≤0.05 AND by ≥1%; ≡ = exactly invariant; predicted ceiling in brackets):\n")
        rungs = ["L0_shuffle", "L1_iaaft", "L2_mvphase", "L3_var"]
        L.append("| metric | kind | " + " | ".join(rungs) + " |")
        L.append("|---|---|" + "---|" * len(rungs))
        for name, fp in v4["fingerprint"].items():
            cells = []
            for rg in rungs:
                c = fp["rungs"][rg]
                mark = "≡" if c["exactly_invariant"] else ("*" if c["observed_differs"] else "")
                cells.append(f"{_f(c['median_z'], 1)}{mark} [{'can' if c['predicted_can_differ'] else 'cannot'}]")
            L.append(f"| {name} | {fp['kind']} | " + " | ".join(cells) + " |")
        L.append("")
        L.append("Blind discrimination (leave-one-seed-out AUC; within-pair permutation null):\n")
        L.append("| task | AUC | null 95% | p | strongest single features |")
        L.append("|---|---|---|---|---|")
        for n, r in v4["discrimination"].items():
            feats = ", ".join(f"{k} {_f(v, 2)}" for k, v in list(r["best_single_feature_auc"].items())[:3])
            L.append(f"| {n} | {_f(r['auc'], 3)} | {_f(r['null_95'], 3)} | {_p(r['p'])} | {feats} |")
        L.append("")

    v3 = results.get("v3_forensics")
    if v3:
        L.append(f"## v3 forensic re-adjudication ({v3['n_seeds']} fresh seeds)\n")
        L.append("| condition | event rate [95% CI] | median onset | active fraction | free votes | switch-off condition met |")
        L.append("|---|---|---|---|---|---|")
        for c, r in v3["conditions"].items():
            ci = r["event_rate_ci95"]
            L.append(f"| {c} | {_f(r['event_rate'], 2)} [{_f(ci[0], 2)}, {_f(ci[1], 2)}] | {_f(r['median_onset'], 0)} | "
                     f"{_f(r['mean_active_fraction'], 2)} | {_f(r['mean_free_votes'], 1)} | {_f(r['switch_off_condition_rate'], 3)} |")
        L.append("")
        L.append("| comparison | master-only events | other-only events | McNemar p | active-fraction diff | p |")
        L.append("|---|---|---|---|---|---|")
        for n, r in v3["comparisons"].items():
            a = r["active_fraction"]
            L.append(f"| {n} | {r['discordant_master_only']} | {r['discordant_other_only']} | {_p(r['mcnemar_exact_p'])} | "
                     f"{_f(a['mean_diff'], 3)} | {_p(a['p'])} |")
        L.append("")
        ga = v3["gain_audit"]
        L.append(f"Gain audit: ceiling reached in {_f(100 * ga['cap_reached_rate'], 0)}% of master runs "
                 f"(median cycle {_f(ga['median_cap_step'], 0)}); mean activity {_f(ga['mean_activity'], 3)} vs "
                 f"homeostatic target {ga['homeostatic_target']}; mean gain at event onset {_f(ga['mean_gain_at_first_event'], 3)}.\n")
        L.append("v3's own metrics under the metric-identical null ladder (median z; fraction of windows where real "
                 "differs from its surrogates at p≤0.05 and by ≥1%):\n")
        rungs = ["L0_shuffle", "L1_iaaft", "L2_mvphase", "L3_var"]
        L.append("| v3 metric | kind | " + " | ".join(rungs) + " |")
        L.append("|---|---|" + "---|" * len(rungs))
        for name, fp in v3["v3_metric_fingerprint"].items():
            cells = [f"{_f(fp['rungs'][rg]['median_z'], 1)} ({_f(fp['rungs'][rg]['fraction_windows_differ'], 2)})" for rg in rungs]
            L.append(f"| {name} | {fp['kind']} | " + " | ".join(cells) + " |")
        L.append("")

    cal = results.get("calibration")
    if cal:
        L.append("## Instrument calibration on ground-truth systems\n")
        L.append("| system | metric | rung | role | detection rate [95% CI] | pass |")
        L.append("|---|---|---|---|---|---|")
        for r in cal["rows"]:
            ci = r["ci95"]
            L.append(f"| {r['system']} | {r['metric']} | {r['rung']} | {r['role']} | "
                     f"{_f(r['detection_rate'], 2)} [{_f(ci[0], 2)}, {_f(ci[1], 2)}] | {'yes' if r['pass'] else 'NO'} |")
        L.append(f"\nAll calibration rows pass: **{cal['all_pass']}**\n")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def make_figures(results: Dict, out_dir: Path, fig_dir: Path) -> List[Path]:
    from .figures import build_all
    return build_all(results, out_dir, fig_dir)
