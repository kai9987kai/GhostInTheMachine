"""Summary and figures for the v5 follow-up studies."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np

from ghost_v4.report import _f, _p

STUDY_TITLES = {
    "A": "Direct replication (frozen v4 pipeline, 48 new networks, 4 new worlds)",
    "B": "Graded authorship (dose-response, live world)",
    "C": "Nonlinear-estimator robustness (re-simulated v4 networks)",
    "D": "Architecture robustness",
    "E": "Comparator timing",
    "F": "Comparator rerouting",
}


def _table(L: List[str], tests: Dict) -> None:
    L.append("| hypothesis | mean diff [95% CI] | d_z [95% CI] | p (one-sided) | p (Holm, study) | result |")
    L.append("|---|---|---|---|---|---|")
    for name, r in tests.items():
        ci, dci = r["ci95"], r.get("d_z_ci95", [None, None])
        L.append(f"| {name} | {_f(r['mean_diff'], 4)} [{_f(ci[0], 4)}, {_f(ci[1], 4)}] | {_f(r['d_z'], 2)} "
                 f"[{_f(dci[0], 2)}, {_f(dci[1], 2)}] | {_p(r['p'])} | {_p(r.get('p_holm'))} | "
                 f"{'supported' if r.get('significant') else 'not supported'} |")
    L.append("")


def write_summary(results: Dict, path: Path) -> None:
    L = ["# Ghost in the Machine v5 — follow-up studies\n", f"> {results['disclaimer']}\n"]
    pre = results["preregistration"]
    L.append(f"Run status: **{results.get('status')}** · v5 lock verifies: **{pre['lock_verifies']}**"
             + (f" · locked at {pre['lock'].get('locked_at_utc')}" if pre.get("lock") else "") + "\n")
    S = results["studies"]
    if "A" in S:
        a = S["A"]
        L.append(f"## A — {STUDY_TITLES['A']}\n")
        L.append(f"**Replication verdict: level {a['verdict']['level']} — {a['verdict']['label']}**\n")
        g = a["gate_manipulation_check"]
        L.append(f"Gate M: diff {_f(g['mean_diff'], 4)}, d_z {_f(g['d_z'], 2)}, p {_p(g['p'])} → {'PASS' if g['pass'] else 'FAIL'}\n")
        _table(L, a["primary"])
        L.append("Placebo A/A: " + "; ".join(f"{m} d_z {_f(r['d_z'], 2)} (p {_p(r['p'])})" for m, r in a["placebo_AA"].items()) + "\n")
    if "B" in S:
        b = S["B"]
        L.append(f"## B — {STUDY_TITLES['B']}\n")
        L.append("For B1-B3 the effect is the mean per-network OLS slope (nats per unit of authorship p); "
                 "B2 is the difference of slopes, intact minus comparator-lesioned.\n")
        _table(L, b["primary"])
        L.append(f"Networks with a positive persistence slope: {b['seeds_with_positive_slope']}/{b['n_seeds']}\n")
        L.append("| authorship p | intention = outcome | persistence (intact) [95% CI] | persistence (comparator lesioned) | Ψ (intact) |")
        L.append("|---|---|---|---|---|")
        for p in b["intention_outcome_match"]:
            fp = b["levels"]["full_persistence"][p]
            L.append(f"| {p} | {_f(b['intention_outcome_match'][p], 3)} | {_f(fp['mean'], 4)} [{_f(fp['ci95'][0], 4)}, "
                     f"{_f(fp['ci95'][1], 4)}] | {_f(b['levels']['no_comparator_persistence'][p]['mean'], 4)} | "
                     f"{_f(b['levels']['full_psi'][p]['mean'], 4)} |")
        L.append("")
        L.append("Adjacent steps (intact): " + "; ".join(f"{k}: {_f(r['mean_diff'], 4)} (p {_p(r['p_two_sided'])})"
                                                      for k, r in b["adjacent_steps_full"].items()) + "\n")
    if "C" in S:
        c = S["C"]
        L.append(f"## C — {STUDY_TITLES['C']}\n")
        _table(L, c["primary"])
        rm = c["resimulation_matches_v4"]
        L.append(f"Re-simulation reproduces the stored v4 values: **{rm['identical']}** "
                 f"(max |Δ self_persistence| = {rm['max_abs_difference_self_persistence']:.3g}).\n")
        k = c["ksg_parts_information"]
        L.append(f"KSG parts-information contrast: {_f(k['mean_diff'], 4)} (d_z {_f(k['d_z'], 2)}, p {_p(k['p_two_sided'])}). "
                 f"Gaussian reference: H1 d_z {_f(c['gaussian_reference_H1']['d_z'], 2)}, H4 d_z {_f(c['gaussian_reference_H4']['d_z'], 2)}.\n")
    for key in ("D", "E", "F"):
        if key in S:
            L.append(f"## {key} — {STUDY_TITLES[key]}\n")
            _table(L, S[key]["primary"])
            if key in ("D", "E"):
                L.append("| secondary | mean diff | d_z | p (two-sided) |")
                L.append("|---|---|---|---|")
                for n, r in S[key]["secondary"].items():
                    L.append(f"| {n} | {_f(r['mean_diff'], 4)} | {_f(r['d_z'], 2)} | {_p(r['p_two_sided'])} |")
                L.append("")
            if key == "F":
                L.append("| population | effect, standard wiring (d_z, p) | effect, rerouted to DMN (d_z, p) |")
                L.append("|---|---|---|")
                for p, r in S["F"]["atlas"]["standard"].items():
                    q = S["F"]["atlas"]["rerouted"][p]
                    L.append(f"| {p} | {_f(r['d_z'], 2)} ({_p(r['p_two_sided'])}) | {_f(q['d_z'], 2)} ({_p(q['p_two_sided'])}) |")
                L.append("")
    L.append("## All v5 primary tests, Holm-corrected across studies\n")
    L.append("| test | p | p (Holm, all v5) | significant |")
    L.append("|---|---|---|---|")
    for n, r in results["across_study_holm"].items():
        L.append(f"| {n} | {_p(r['p'])} | {_p(r['p_holm_all_v5'])} | {'yes' if r['significant'] else 'no'} |")
    L.append("")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def b_within_network(out_dir: Path) -> Dict:
    """Descriptive (post-lock, figure only): persistence change relative to each network's own p = 0 run."""
    from ghost_v4 import stats as st
    from .studies import LEVELS, _col, _load
    data, seeds = _load(out_dir)
    rng = np.random.default_rng(56)
    out = {}
    for cond in ("full", "no_comparator"):
        Y = np.stack([_col(data, seeds, f"{cond}@p{p:g}", "graded", "self_persistence") for p in LEVELS], axis=1)
        R = Y - Y[:, [0]]
        out[cond] = {f"{p:g}": {"mean": float(R[:, i].mean()), "ci95": st.bootstrap_ci(R[:, i], rng=rng)}
                     for i, p in enumerate(LEVELS)}
    return out


def make_figures(results: Dict, fig_dir: Path) -> List[Path]:
    from ghost_v4.figures import AXIS, BLUE, GREY, INK, INK2, ORANGE, SURFACE, _hbar_ci, _plt, _style
    plt = _plt()
    fig_dir.mkdir(parents=True, exist_ok=True)
    S = results["studies"]
    made = []

    fig = plt.figure(figsize=(13.5, 8.2))
    gs = fig.add_gridspec(2, 2, hspace=0.55, wspace=0.55)

    # (a) dose-response
    ax = fig.add_subplot(gs[0, 0])
    rel = results.get("descriptive", {}).get("B_within_network")
    if "B" in S and rel:
        ps = [float(p) for p in rel["full"]]
        for label, key, col in (("comparator intact", "full", BLUE), ("comparator lesioned", "no_comparator", GREY)):
            m = [rel[key][f"{p:g}"]["mean"] for p in ps]
            lo = [rel[key][f"{p:g}"]["ci95"][0] for p in ps]
            hi = [rel[key][f"{p:g}"]["ci95"][1] for p in ps]
            ax.fill_between(ps, lo, hi, color=col, alpha=0.12, linewidth=0)
            ax.plot(ps, m, "-o", color=col, linewidth=2, markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5)
            ax.text(1.02, m[-1], label, va="center", color=INK2, fontsize=8.5)
        ax.set_xlim(-0.03, 1.35)
        ax.set_xticks(ps)
        ax.set_xlabel("authorship p = P(executed action is the agent's own)")
        ax.axhline(0, color=AXIS, linewidth=1)
        ax.set_ylabel("Δ self persistence vs own p = 0 run (nats)")
    ax.set_title("a  Graded authorship (Study B)")
    _style(ax, "y")

    # (b) replication + estimator + architecture forest (standardized)
    ax = fig.add_subplot(gs[0, 1])
    rows = []
    if "A" in S:
        for k in ("H1_authorship_self_persistence", "H4_authorship_causal_emergence"):
            r = S["A"]["primary"][k]
            rows.append((f"A replication {k.split('_')[0]}", r))
    if "C" in S:
        for k, r in S["C"]["primary"].items():
            rows.append((f"C {k.split('_', 1)[1].replace('_', ' ')}", r))
    if "D" in S:
        for k, r in S["D"]["primary"].items():
            rows.append((f"D {k.split('_')[1]}", r))
    if rows:
        _hbar_ci(ax, [r[0] for r in rows], [r[1]["d_z"] for r in rows],
                 [r[1].get("d_z_ci95", [r[1]["d_z"]] * 2) for r in rows],
                 [BLUE if r[1].get("significant") else GREY for r in rows], "authorship effect, d_z (95% CI)")
    ax.set_title("b  Replication, estimators, architectures")

    # (c) comparator timing
    ax = fig.add_subplot(gs[1, 0])
    if "E" in S:
        sec = S["E"]["secondary"]
        labels = ["sham (always on)", "switched off at 3000", "switched on at 3000"]
        keys = ["authorship_effect_sham", "authorship_effect_off_late", "authorship_effect_on_late"]
        _hbar_ci(ax, labels, [sec[k]["mean_diff"] for k in keys], [sec[k]["ci95"] for k in keys],
                 [BLUE, GREY, ORANGE], "self persistence, master − twin (nats, cycles 3501–6000)")
    ax.set_title("c  Comparator timing (Study E)")

    # (d) rerouting
    ax = fig.add_subplot(gs[1, 1])
    if "F" in S:
        pops = list(S["F"]["atlas"]["standard"])
        y = np.arange(len(pops))[::-1]
        for off, wiring, col in ((0.17, "standard", BLUE), (-0.17, "rerouted", ORANGE)):
            vals = [S["F"]["atlas"][wiring][p]["d_z"] for p in pops]
            ax.barh(y + off, vals, height=0.3, color=col, label={"standard": "comparator → self", "rerouted": "comparator → DMN"}[wiring])
        ax.axvline(0, color=AXIS, linewidth=1)
        ax.set_yticks(y)
        ax.set_yticklabels(pops)
        ax.legend(loc="lower right")
        ax.set_xlabel("authorship effect on persistence, d_z")
    ax.set_title("d  Does the effect follow the comparator? (Study F)")
    _style(ax)
    fig.suptitle("Figure 5 — v5 follow-up: replication, dose-response, robustness and mechanism",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    path = fig_dir / "ghost_v5_figure_5_followup.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    made.append(path)
    return made
