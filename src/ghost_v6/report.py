"""Summary and figure for the v6 studies (not hashed: presentation only)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np

from ghost_v4.report import _f, _p

STUDY_TITLES = {
    "G": "Prediction-error transplant",
    "I": "Near-full authorship, with the prediction error as candidate mediator",
    "J": "Comparator gain",
}

G_LABELS = {
    "twin:live": "twin, its own live error (reference 0)",
    "twin:off": "twin, comparator silent",
    "twin:masterPE": "twin, given the master's error stream",
    "master:live": "master, its own live error (reference 1)",
    "master:off": "master, comparator silent",
    "master:shift": "master, own stream desynchronized",
    "master:phase": "master, own stream phase-randomized",
    "master:twinPE": "master, given the twin's error stream",
    "master:twinPE_scaled": "master, twin's stream at master amplitude",
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


def _secondary(L: List[str], sec: Dict) -> None:
    L.append("| secondary | mean diff [95% CI] | d_z | p (two-sided) |")
    L.append("|---|---|---|---|")
    for n, r in sec.items():
        L.append(f"| {n} | {_f(r['mean_diff'], 4)} [{_f(r['ci95'][0], 4)}, {_f(r['ci95'][1], 4)}] | "
                 f"{_f(r['d_z'], 2)} | {_p(r['p_two_sided'])} |")
    L.append("")


def write_summary(results: Dict, path: Path) -> None:
    L = ["# Ghost in the Machine v6 — what does the comparator's prediction error carry?\n",
         f"> {results['disclaimer']}\n"]
    pre = results["preregistration"]
    L.append(f"Run status: **{results.get('status')}** · v6 lock verifies: **{pre['lock_verifies']}**"
             + (f" · locked at {pre['lock'].get('locked_at_utc')}" if pre.get("lock") else "") + "\n")
    S = results["studies"]
    if "G" in S:
        g = S["G"]
        L.append(f"## G — {STUDY_TITLES['G']}\n")
        gate = g["gate_authorship_effect"]
        L.append(f"Gate (authorship effect, master live − twin live): diff {_f(gate['mean_diff'], 4)}, "
                 f"d_z {_f(gate['d_z'], 2)}, p {_p(gate['p'])} → {'PASS' if gate['pass'] else 'FAIL'}\n")
        _table(L, g["primary"])
        L.append(f"**Preregistered decision: {g['account']} account.**\n")
        L.append(f"Equivalence (TOST, bound ±{g['equivalence_sesoi_nats']} nats):\n")
        L.append("| contrast | mean diff | 90% CI | p (TOST) | equivalent to zero? |")
        L.append("|---|---|---|---|---|")
        for k, e in g["equivalence"].items():
            L.append(f"| {k} | {_f(e['mean_diff'], 4)} | [{_f(e['ci90'][0], 4)}, {_f(e['ci90'][1], 4)}] | "
                     f"{_p(e['p'])} | {'yes' if e['equivalent'] else 'no'} |")
        L.append("")
        L.append("| condition | self persistence [95% CI] | position between twin (0) and master (1) [95% CI] | injected RMS |")
        L.append("|---|---|---|---|")
        for k, lab in G_LABELS.items():
            lv, fr = g["levels"][k], g["fraction_of_effect"][k]
            L.append(f"| {lab} | {_f(lv['mean'], 4)} [{_f(lv['ci95'][0], 4)}, {_f(lv['ci95'][1], 4)}] | "
                     f"{_f(fr['fraction_of_authorship_effect'], 2)} [{_f(fr['ci95'][0], 2)}, {_f(fr['ci95'][1], 2)}] | "
                     f"{_f(g['injected_rms'][k], 3)} |")
        L.append("")
        _secondary(L, g["secondary"])
    if "I" in S:
        i = S["I"]
        L.append(f"## I — {STUDY_TITLES['I']}\n")
        _table(L, i["primary"])
        lv = i["levels"]
        L.append("| authorship p | intention = outcome | self persistence | relative to p = 1 [95% CI] | "
                 "mismatch RMS | own-step mismatch | foreign-step mismatch |")
        L.append("|---|---|---|---|---|---|---|")
        for p in lv["self_persistence"]:
            rel = i["relative_to_full_authorship"][p]
            L.append(f"| {p} | {_f(lv['intention_outcome_match'][p]['mean'], 3)} | {_f(lv['self_persistence'][p]['mean'], 4)} | "
                     f"{_f(rel['mean'], 4)} [{_f(rel['ci95'][0], 4)}, {_f(rel['ci95'][1], 4)}] | "
                     f"{_f(lv['mismatch_rms'][p]['mean'], 4)} | {_f(lv['own_step_mismatch_rms'][p]['mean'], 4)} | "
                     f"{_f(lv['foreign_step_mismatch_rms'][p]['mean'], 4)} |")
        L.append("")
        L.append("Adjacent steps: " + "; ".join(f"{k}: {_f(r['mean_diff'], 4)} (p {_p(r['p_two_sided'])})"
                                              for k, r in i["adjacent_steps"].items()) + "\n")
    if "J" in S:
        j = S["J"]
        L.append(f"## J — {STUDY_TITLES['J']}\n")
        _table(L, j["primary"])
        _secondary(L, j["secondary"])
        dc = results.get("descriptive", {}).get("J_direction_counts")
        if dc:
            L.append("Descriptive (post-lock, not hypothesis tests): networks with master > twin — "
                     + "; ".join(f"{k}: {v['positive']}/{v['n']} (sign test p {_p(v['sign_test_p_one_sided'])}, "
                                 f"median diff {_f(v['median_diff'], 3)})" for k, v in dc.items())
                     + ". The mean-based preregistered tests are dominated by two networks (12012, 12023) whose "
                       "twin's slow mode became nearly frozen (persistence 2.0–2.6 nats).\n")
        L.append("| role, gain | self persistence [95% CI] | injected RMS |")
        L.append("|---|---|---|")
        for k, v in j["levels"].items():
            L.append(f"| {k} | {_f(v['mean'], 4)} [{_f(v['ci95'][0], 4)}, {_f(v['ci95'][1], 4)}] | {_f(v['injected_rms'], 3)} |")
        L.append("")
    L.append("## All v6 primary tests, Holm-corrected across studies\n")
    L.append("| test | p | p (Holm, all v6) | significant |")
    L.append("|---|---|---|---|")
    for n, r in results["across_study_holm"].items():
        L.append(f"| {n} | {_p(r['p'])} | {_p(r['p_holm_all_v6'])} | {'yes' if r['significant'] else 'no'} |")
    L.append("")
    ma = results.get("meta_analysis")
    if ma:
        L.append("## Living meta-analysis of the master − twin contrast (EXPLORATORY)\n")
        L.append(f"_{ma['status']}._ Random-effects (DerSimonian–Laird) pooling over every independent sample "
                 "run with the default architecture and the master vs cross-yoked-twin contrast.\n")
        for metric, label in (("self_persistence", "self persistence (nats)"), ("self_psi", "Ψ")):
            m = ma[metric]
            L.append(f"**{label}**: pooled {_f(m['pooled_mean_diff'], 4)} [{_f(m['ci95'][0], 4)}, {_f(m['ci95'][1], 4)}], "
                     f"p {_p(m['p_two_sided'])}, {m['k']} samples / {m['n_networks']} networks, "
                     f"I² {_f(m['I2'], 2)}, τ² {m['tau2']:.2g}, 95% prediction interval for a new sample "
                     f"[{_f(m['prediction_interval95'][0], 4)}, {_f(m['prediction_interval95'][1], 4)}], "
                     f"pooled d_z {_f(m['pooled_d_z_all_networks'], 2)}.\n")
            L.append("| sample | networks | mean diff [95% CI] | d_z | weight |")
            L.append("|---|---|---|---|---|")
            for s_ in m["samples"]:
                L.append(f"| {s_['sample']} | {s_['n']} | {_f(s_['mean_diff'], 4)} [{_f(s_['ci95'][0], 4)}, {_f(s_['ci95'][1], 4)}] | "
                         f"{_f(s_['d_z'], 2)} | {_f(s_['weight'], 2)} |")
            L.append("")
    ph = results.get("posthoc_v5")
    if ph:
        L.append("## Post-hoc re-reading of the v5 null results (EXPLORATORY)\n")
        L.append(f"_{ph['status']}._ Bounds: persistence ±{ph['bounds']['persistence_nats']} nats, "
                 f"Ψ ±{ph['bounds']['psi']} ({ph['bounds']['psi_rule']}).\n")
        L.append("| v5 result | mean diff | 90% CI | bound | p (TOST) | evidence of absence? |")
        L.append("|---|---|---|---|---|---|")
        for label, e in _posthoc_rows(ph):
            L.append(f"| {label} | {_f(e['mean_diff'], 4)} | [{_f(e['ci90'][0], 4)}, {_f(e['ci90'][1], 4)}] | "
                     f"±{e['bound']} | {_p(e['p'])} | {'yes' if e['equivalent'] else 'no'} |")
        L.append("")
        stl = ph["A_H4_psi"]["small_telescopes"]
        L.append(f"Small telescopes, A:H4 (Ψ): d33 = {_f(stl['d33'], 3)} for the original n = 48; replication d_z = "
                 f"{_f(stl['replication_d_z'], 3)}; p(smaller than d33) = {_p(stl['p_smaller_than_d33'])} → {stl['verdict']}. "
                 f"v4's own estimate lies above the replication's 95% CI: {ph['A_H4_psi']['v4_estimate_outside_replication_ci95']}.\n")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def _posthoc_rows(ph: Dict):
    rows = [("A:H4 Ψ (replication)", ph["A_H4_psi"]["equivalence"]),
            ("B3 Ψ slope over authorship", ph["B3_psi_slope"]["equivalence"])]
    rows += [(f"D {v} Ψ", r["equivalence"]) for v, r in ph["D_psi"].items()]
    rows.append(("E persistence effect, comparator switched off", ph["E_switched_off_persistence"]["equivalence"]))
    return rows


def make_figures(results: Dict, fig_dir: Path) -> List[Path]:
    from ghost_v4.figures import AXIS, BLUE, GREY, INK2, ORANGE, SURFACE, _hbar_ci, _plt, _style
    plt = _plt()
    fig_dir.mkdir(parents=True, exist_ok=True)
    S = results["studies"]

    fig = plt.figure(figsize=(13.5, 8.6))
    gs = fig.add_gridspec(2, 2, hspace=0.55, wspace=0.28, width_ratios=[1.15, 1])

    # (a) where each transplant lands between twin (0) and master (1)
    ax = fig.add_subplot(gs[0, 0])
    if "G" in S:
        g = S["G"]
        keys = [k for k in G_LABELS if not k.endswith(":off")]
        fr = [g["fraction_of_effect"][k] for k in keys]
        cols = [ORANGE if k.startswith("twin") else BLUE for k in keys]
        _hbar_ci(ax, [G_LABELS[k] for k in keys], [f["fraction_of_authorship_effect"] for f in fr],
                 [f["ci95"] for f in fr], cols, "self persistence: 0 = twin live, 1 = master live")
        ax.axvline(1, color=AXIS, linewidth=1, linestyle=":")
    ax.set_title("a  Prediction-error transplant (Study G)")

    # (b) near-full authorship
    ax = fig.add_subplot(gs[0, 1])
    if "I" in S:
        rel = S["I"]["relative_to_full_authorship"]
        ps = [float(p) for p in rel]
        xs = np.arange(len(ps))
        m = [rel[f"{p:g}"]["mean"] for p in ps]
        lo = [rel[f"{p:g}"]["ci95"][0] for p in ps]
        hi = [rel[f"{p:g}"]["ci95"][1] for p in ps]
        ax.fill_between(xs, lo, hi, color=BLUE, alpha=0.12, linewidth=0)
        ax.plot(xs, m, "-o", color=BLUE, linewidth=2, markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.axhline(0, color=AXIS, linewidth=1)
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{p:g}" for p in ps])
        ax.set_xlabel("authorship p (levels evenly spaced, not to scale)")
        ax.set_ylabel("Δ self persistence vs p = 1 (nats)")
    ax.set_title("b  Near-full authorship (Study I)")
    _style(ax, "y")

    # (d) comparator gain
    ax = fig.add_subplot(gs[1, 1])
    if "J" in S:
        lv = S["J"]["levels"]
        gains = sorted({float(k.split("gain")[1]) for k in lv})
        for role, col in (("master", BLUE), ("twin", ORANGE)):
            m = [lv[f"{role}:gain{k:g}"]["mean"] for k in gains]
            lo = [lv[f"{role}:gain{k:g}"]["ci95"][0] for k in gains]
            hi = [lv[f"{role}:gain{k:g}"]["ci95"][1] for k in gains]
            ax.fill_between(gains, lo, hi, color=col, alpha=0.12, linewidth=0)
            ax.plot(gains, m, "-o", color=col, linewidth=2, markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5)
            ax.text(gains[-1] * 1.06, m[-1], role, va="center", color=INK2, fontsize=9)
        ax.set_xscale("log", base=2)
        ax.set_xticks(gains)
        ax.set_xticklabels([f"{k:g}" for k in gains])
        ax.set_xlim(gains[0] / 1.2, gains[-1] * 1.6)
        ax.set_xlabel("comparator gain k")
        ax.set_ylabel("self persistence (nats)")
    ax.set_title("d  Comparator gain (Study J)")
    _style(ax, "y")

    # (c) post-hoc: which v5 nulls are evidence of absence?
    ax = fig.add_subplot(gs[1, 0])
    ph = results.get("posthoc_v5")
    if ph:
        rows = _posthoc_rows(ph)
        vals = [e["mean_diff"] / e["bound"] for _, e in rows]
        cis = [[e["ci90"][0] / e["bound"], e["ci90"][1] / e["bound"]] for _, e in rows]
        cols = [BLUE if e["equivalent"] else GREY for _, e in rows]
        ax.axvspan(-1, 1, color=BLUE, alpha=0.06, linewidth=0)
        _hbar_ci(ax, [r[0] for r in rows], vals, cis, cols, "effect / equivalence bound (90% CI)")
        ax.axvline(-1, color=AXIS, linewidth=1, linestyle=":")
        ax.axvline(1, color=AXIS, linewidth=1, linestyle=":")
    ax.set_title("c  v5 nulls re-read: none is evidence of absence (post hoc)")

    fig.suptitle("Figure 6 — v6: what the comparator's prediction error carries",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    path = fig_dir / "ghost_v6_figure_6_transplant.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return [path]
