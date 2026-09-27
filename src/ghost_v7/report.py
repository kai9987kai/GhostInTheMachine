"""Summary and figure for the v7 studies (not hashed: presentation only)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np

from ghost_v4.report import _f, _p

STUDY_TITLES = {
    "K": "Feedback vs innovation: which part of the prediction error must be in step?",
    "L": "Powered test of authorship-dependent causal emergence (Ψ)",
    "M": "Comparator gain with a bounded measure and a rank-based test",
}

K_LABELS = {
    "master:live": "master, live error",
    "master:shift": "master, whole error desynchronized",
    "master:fbLive_innShift": "master, state-predicted part live, rest desynchronized",
    "master:fbShift_innLive": "master, state-predicted part desynchronized, rest live",
    "twin:live": "twin, live error",
    "twin:shift": "twin, whole error desynchronized",
}


def _row(name: str, r: Dict) -> str:
    if "hodges_lehmann" in r:
        return (f"| {name} | HL {_f(r['hodges_lehmann'], 4)} [{_f(r['hl_ci95'][0], 4)}, {_f(r['hl_ci95'][1], 4)}]; "
                f"{r['positive']}/{r['n']} positive | {_f(r['d_z'], 2)} | {_p(r['p'])} (signed-rank) | {_p(r.get('p_holm'))} | "
                f"{'supported' if r.get('significant') else 'not supported'} |")
    ci = r["ci95"]
    return (f"| {name} | mean {_f(r['mean_diff'], 4)} [{_f(ci[0], 4)}, {_f(ci[1], 4)}] | {_f(r['d_z'], 2)} | {_p(r['p'])} | "
            f"{_p(r.get('p_holm'))} | {'supported' if r.get('significant') else 'not supported'} |")


def _table(L: List[str], tests: Dict) -> None:
    L.append("| hypothesis | estimate [95% CI] | d_z | p (one-sided) | p (Holm, study) | result |")
    L.append("|---|---|---|---|---|---|")
    for name, r in tests.items():
        L.append(_row(name, r))
    L.append("")


def _secondary(L: List[str], sec: Dict) -> None:
    L.append("| secondary | estimate [95% CI] | d_z | p (two-sided) |")
    L.append("|---|---|---|---|")
    for n, r in sec.items():
        if "bound" in r:
            L.append(f"| {n} (TOST ±{r['bound']}) | mean {_f(r['mean_diff'], 4)}, 90% CI [{_f(r['ci90'][0], 4)}, {_f(r['ci90'][1], 4)}] | | "
                     f"TOST p {_p(r['p'])} → {'equivalent' if r['equivalent'] else 'not equivalent'} |")
        elif "hodges_lehmann" in r:
            L.append(f"| {n} | HL {_f(r['hodges_lehmann'], 4)} [{_f(r['hl_ci95'][0], 4)}, {_f(r['hl_ci95'][1], 4)}]; "
                     f"{r['positive']}/{r['n']} positive | {_f(r['d_z'], 2)} | {_p(r['p_two_sided'])} |")
        else:
            L.append(f"| {n} | mean {_f(r['mean_diff'], 4)} [{_f(r['ci95'][0], 4)}, {_f(r['ci95'][1], 4)}] | "
                     f"{_f(r['d_z'], 2)} | {_p(r['p_two_sided'])} |")
    L.append("")


def write_summary(results: Dict, path: Path) -> None:
    L = ["# Ghost in the Machine v7 — feedback vs innovation, a powered Ψ test, and a robust gain test\n",
         f"> {results['disclaimer']}\n"]
    pre = results["preregistration"]
    L.append(f"Run status: **{results.get('status')}** · v7 lock verifies: **{pre['lock_verifies']}**"
             + (f" · locked at {pre['lock'].get('locked_at_utc')}" if pre.get("lock") else "") + "\n")
    S = results["studies"]
    if "K" in S:
        k = S["K"]
        L.append(f"## K — {STUDY_TITLES['K']}\n")
        _table(L, k["primary"])
        L.append(f"**Preregistered decision: {k['account']}.**\n")
        L.append(f"Equivalence (TOST, ±{k['equivalence_sesoi_nats']} nats): "
                 + "; ".join(f"{n}: mean {_f(e['mean_diff'], 4)}, 90% CI [{_f(e['ci90'][0], 4)}, {_f(e['ci90'][1], 4)}], "
                             f"{'equivalent' if e['equivalent'] else 'not equivalent'}" for n, e in k["equivalence"].items()) + "\n")
        L.append("| condition | self persistence (nats) [95% CI] | bounded persistence ρ | injected RMS |")
        L.append("|---|---|---|---|")
        for key, lab in K_LABELS.items():
            v = k["levels"][key]
            L.append(f"| {lab} | {_f(v['mean'], 4)} [{_f(v['ci95'][0], 4)}, {_f(v['ci95'][1], 4)}] | {_f(v['rho'], 4)} | {_f(v['injected_rms'], 3)} |")
        L.append("")
        L.append("Fraction of the desynchronization loss recovered: " + "; ".join(
            f"{n}: {_f(r['fraction_of_desync_loss_recovered'], 2)} [{_f(r['ci95'][0], 2)}, {_f(r['ci95'][1], 2)}]"
            for n, r in k["recovered"].items()) + "\n")
        sp = k["state_predictable_share"]
        L.append(f"Share of the live prediction error predicted by the network's own state (ridge R²): master "
                 f"{_f(sp['master'], 3)} [{_f(sp['master_ci95'][0], 3)}, {_f(sp['master_ci95'][1], 3)}], twin "
                 f"{_f(sp['twin'], 3)} [{_f(sp['twin_ci95'][0], 3)}, {_f(sp['twin_ci95'][1], 3)}].\n")
        L.append("Robust versions (bounded persistence ρ, signed-rank):\n")
        L.append("| hypothesis | Hodges–Lehmann [95% CI] | positive | p (one-sided) |")
        L.append("|---|---|---|---|")
        for n, r in k["robust_rho_signed_rank"].items():
            L.append(f"| {n} | {_f(r['hodges_lehmann'], 4)} [{_f(r['hl_ci95'][0], 4)}, {_f(r['hl_ci95'][1], 4)}] | "
                     f"{r['positive']}/{r['n']} | {_p(r['p'])} |")
        L.append("")
        _secondary(L, k["secondary"])
    if "L" in S:
        l_ = S["L"]
        L.append(f"## L — {STUDY_TITLES['L']}\n")
        _table(L, l_["primary"])
        L.append(f"Networks with master > twin: Ψ {l_['psi_positive']}/{l_['n_seeds']}, ρ {l_['rho_positive']}/{l_['n_seeds']}.\n")
        _secondary(L, l_["secondary"])
    if "M" in S:
        m = S["M"]
        L.append(f"## M — {STUDY_TITLES['M']}\n")
        _table(L, m["primary"])
        _secondary(L, m["secondary"])
        L.append("| role, gain | ρ [95% CI] | persistence (nats) | injected RMS |")
        L.append("|---|---|---|---|")
        for key, v in m["levels"].items():
            L.append(f"| {key} | {_f(v['rho'], 4)} [{_f(v['rho_ci95'][0], 4)}, {_f(v['rho_ci95'][1], 4)}] | "
                     f"{_f(v['persistence'], 4)} | {_f(v['injected_rms'], 3)} |")
        L.append("")
    L.append("## All v7 primary tests, Holm-corrected across studies\n")
    L.append("| test | p | p (Holm, all v7) | significant |")
    L.append("|---|---|---|---|")
    for n, r in results["across_study_holm"].items():
        L.append(f"| {n} | {_p(r['p'])} | {_p(r['p_holm_all_v7'])} | {'yes' if r['significant'] else 'no'} |")
    L.append("")
    ma = results.get("meta_analysis")
    if ma:
        L.append("## Cumulative meta-analysis of the master − twin contrast (prespecified, exploratory)\n")
        L.append(f"_{ma['status']}._ The identity ρ = √(1 − e^(−2I)) used for pre-v7 samples reproduces the directly "
                 f"computed ρ on v7 L data to within {ma['rho_identity_max_abs_error']:.1e}.\n")
        for metric, label in (("self_persistence", "self persistence (nats)"), ("self_rho", "bounded persistence ρ"),
                              ("self_psi", "Ψ")):
            r = ma[metric]
            loo = [v["pooled_mean_diff"] for v in r["leave_one_out"].values()]
            L.append(f"**{label}**: pooled {_f(r['pooled_mean_diff'], 4)}, DL 95% CI [{_f(r['ci95'][0], 4)}, {_f(r['ci95'][1], 4)}], "
                     f"HKSJ 95% CI [{_f(r['hksj']['ci95'][0], 4)}, {_f(r['hksj']['ci95'][1], 4)}], p (DL) {_p(r['p_two_sided'])}, "
                     f"{r['k']} samples / {r['n_networks']} networks, I² {_f(r['I2'], 2)}, prediction interval "
                     f"[{_f(r['prediction_interval95'][0], 4)}, {_f(r['prediction_interval95'][1], 4)}], leave-one-out range "
                     f"[{_f(min(loo), 4)}, {_f(max(loo), 4)}]; all networks pooled: {r['all_networks_signed_rank']['positive']}/"
                     f"{r['all_networks_signed_rank']['n']} positive, signed-rank p {_p(r['all_networks_signed_rank']['p'])}.\n")
            L.append("| sample | networks | mean diff [95% CI] | d_z | weight |")
            L.append("|---|---|---|---|---|")
            for s in r["samples"]:
                L.append(f"| {s['sample']} | {s['n']} | {_f(s['mean_diff'], 4)} [{_f(s['ci95'][0], 4)}, {_f(s['ci95'][1], 4)}] | "
                         f"{_f(s['d_z'], 2)} | {_f(s['weight'], 2)} |")
            L.append("")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def make_figures(results: Dict, fig_dir: Path) -> List[Path]:
    from ghost_v4.figures import AXIS, BLUE, GREY, INK2, ORANGE, SURFACE, _hbar_ci, _plt, _style
    plt = _plt()
    fig_dir.mkdir(parents=True, exist_ok=True)
    S = results["studies"]
    fig = plt.figure(figsize=(14.5, 9.0))
    gs = fig.add_gridspec(2, 3, hspace=0.62, wspace=0.95, width_ratios=[1.25, 0.9, 1.0])

    # (a) K condition means
    ax = fig.add_subplot(gs[0, 0])
    if "K" in S:
        lv = S["K"]["levels"]
        keys = list(K_LABELS)
        _hbar_ci(ax, [K_LABELS[k] for k in keys], [lv[k]["mean"] for k in keys], [lv[k]["ci95"] for k in keys],
                 [ORANGE if k.startswith("twin") else BLUE for k in keys], "self persistence (nats)")
        ax.axvline(lv["master:live"]["mean"], color=AXIS, linewidth=1, linestyle=":")
        ax.set_xlim(min(lv[k]["ci95"][0] for k in keys) - 0.05, max(lv[k]["ci95"][1] for k in keys) + 0.05)
    ax.set_title("a  Which part must be in step? (Study K)")

    # (b) share of the error the state predicts
    ax = fig.add_subplot(gs[0, 1])
    if "K" in S:
        sp = S["K"]["state_predictable_share"]
        xs = [0, 1]
        vals = [sp["master"], sp["twin"]]
        cis = [sp["master_ci95"], sp["twin_ci95"]]
        for x, v, (lo, hi), col in zip(xs, vals, cis, (BLUE, ORANGE)):
            ax.bar(x, v, width=0.55, color=col, alpha=0.85)
            ax.plot([x, x], [lo, hi], color=INK2, linewidth=1.5)
        ax.set_xticks(xs)
        ax.set_xticklabels(["master\n(author)", "twin"])
        ax.set_ylim(0, 1)
        ax.set_ylabel("share of prediction error\npredicted by own state (R²)")
    ax.set_title("b  An author's error is its own")
    _style(ax, "y")

    # (c) M robust effect by gain
    ax = fig.add_subplot(gs[0, 2])
    if "M" in S:
        sec = S["M"]["secondary"]
        gains = [0.5, 1.0, 2.0]
        hl = [sec[f"robust_effect_gain{k:g}"]["hodges_lehmann"] for k in gains]
        ci = [sec[f"robust_effect_gain{k:g}"]["hl_ci95"] for k in gains]
        pos = [sec[f"robust_effect_gain{k:g}"]["positive"] for k in gains]
        n = sec["robust_effect_gain1"]["n"]
        xs = np.arange(3)
        for x, h, (lo, hi), p in zip(xs, hl, ci, pos):
            ax.plot([x, x], [lo, hi], color=BLUE, linewidth=2, alpha=0.55)
            ax.plot([x], [h], "o", color=BLUE, markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5)
            ax.text(x + 0.09, h, f"{p}/{n} networks", color=INK2, fontsize=8.5, va="center", ha="left")
        ax.axhline(0, color=AXIS, linewidth=1)
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{k:g}" for k in gains])
        ax.set_xlim(-0.3, 2.9)
        ax.set_ylim(0, max(c[1] for c in ci) * 1.12)
        ax.set_xlabel("comparator gain k")
        ax.set_ylabel("authorship effect on ρ\n(Hodges–Lehmann, 95% CI)")
    ax.set_title("c  Gain, robust (Study M)")
    _style(ax, "y")

    # (d)-(e) cumulative meta-analysis: Psi and bounded persistence
    ma = results.get("meta_analysis")
    for cell, (metric, label, title) in ((gs[1, 0], ("self_psi", "Ψ, master − twin", "d  Ψ across every sample")),
                                         (gs[1, 1:3], ("self_rho", "bounded persistence ρ, master − twin",
                                                       "e  Persistence across every sample"))):
        ax = fig.add_subplot(cell)
        if ma:
            r = ma[metric]
            names = [s["sample"] for s in r["samples"]] + ["pooled (DL)", "pooled (HKSJ)"]
            vals = [s["mean_diff"] for s in r["samples"]] + [r["pooled_mean_diff"]] * 2
            cis = [s["ci95"] for s in r["samples"]] + [r["ci95"], r["hksj"]["ci95"]]
            cols = [GREY] * len(r["samples"]) + [BLUE, BLUE]
            _hbar_ci(ax, names, vals, cis, cols, label)
        ax.set_title(title)
    fig.suptitle("Figure 7 — v7: the in-step part of the error, a powered Ψ test, and a robust gain test",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    path = fig_dir / "ghost_v7_figure_7_feedback.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return [path]
