"""
Publication figures for v4 (static PNG, light surface).

Visual conventions: one axis per panel (never dual-axis), thin marks, hairline
solid gridlines, text in ink tokens (never series colours), categorical colours
from a CVD-validated three-slot palette, a blue-grey-red diverging scale for
signed z, and emphasis (one accent hue, the rest grey) where one element is the
point. Every value shown is also tabulated in SUMMARY.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
GREY = "#b5b3ab"
DIV_NEG, DIV_MID, DIV_POS = "#2a78d6", "#f0efec", "#e34948"
RUNGS = ["L0_shuffle", "L1_iaaft", "L2_mvphase", "L3_var"]
RUNG_LABELS = ["L0\nshuffle", "L1\nIAAFT", "L2\nmultivariate\nphase", "L3\nVAR(2)"]


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 9.5, "text.color": INK, "axes.labelcolor": INK2, "axes.edgecolor": AXIS,
        "axes.linewidth": 0.8, "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
        "axes.grid": False, "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
        "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold",
        "axes.titlesize": 10.5, "axes.titlecolor": INK, "axes.titlelocation": "left",
        "legend.frameon": False, "legend.fontsize": 8.5,
    })
    return plt


def _style(ax, grid_axis="x"):
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def _hbar_ci(ax, labels, values, ci, colors, xlabel):
    y = np.arange(len(labels))[::-1]
    for yi, v, (lo, hi), c in zip(y, values, ci, colors):
        ax.plot([lo, hi], [yi, yi], color=c, linewidth=2, solid_capstyle="round", alpha=0.55)
        ax.plot([v], [yi], "o", color=c, markersize=6.5, markeredgecolor=SURFACE, markeredgewidth=1.5)
    ax.axvline(0, color=AXIS, linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel(xlabel)
    _style(ax)


def fig_v3_forensics(v3: Dict, path: Path) -> Path:
    plt = _plt()
    fig = plt.figure(figsize=(12.5, 7.8))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05], hspace=0.55, wspace=0.42)

    # (a) gain ramp and event onsets, masters
    ax = fig.add_subplot(gs[0, :])
    tr = v3["traces"]["master"]
    steps = np.asarray(tr["step"])
    G = np.asarray(tr["gain"])
    ax.fill_between(steps, np.percentile(G, 10, axis=0), np.percentile(G, 90, axis=0), color=BLUE, alpha=0.10, linewidth=0)
    ax.plot(steps, np.median(G, axis=0), color=BLUE, linewidth=2)
    ax.axhline(1.18, color=AXIS, linewidth=1)
    ax.text(steps[-1], 1.183, "gain ceiling 1.18", ha="right", va="bottom", color=INK2, fontsize=8.5)
    onsets = v3["conditions"]["master"]["onsets"]
    lo = float(np.percentile(G, 10, axis=0).min())
    ax.plot(onsets, np.full(len(onsets), lo - 0.02), "|", color=ORANGE, markersize=14, markeredgewidth=2)
    ax.text(float(np.median(onsets)) if onsets else steps[0], lo - 0.045,
            f"GHOST-v3 onsets (n={len(onsets)}/{v3['n_seeds']})", ha="center", va="top", color=INK2, fontsize=8.5)
    ax.axvspan(0, 1000, color=GRID, alpha=0.45, linewidth=0)
    ax.text(500, np.median(G, axis=0)[0] + 0.1, "calibration\n(baseline for z)", ha="center", color=INK2, fontsize=8.5)
    ax.set_xlim(0, steps[-1])
    ax.set_ylim(lo - 0.08, 1.24)
    ax.set_xlabel("cycle")
    ax.set_ylabel("recurrent gain")
    ax.set_title("a  v3's homeostatic gain ramps to its ceiling (median, 10–90% band) while the events fire")
    _style(ax, "y")

    # (b) event rate per condition
    ax = fig.add_subplot(gs[1, 0])
    order = ["master", "twin", "clamp_low", "clamp_high", "frozen"]
    labels = {"master": "unmodified v3", "twin": "cross-yoked twin", "clamp_low": "gain clamped 0.91",
              "clamp_high": "gain clamped 1.18", "frozen": "learning frozen"}
    y = np.arange(len(order))[::-1]
    for yi, c in zip(y, order):
        r = v3["conditions"][c]
        col = BLUE if c == "master" else GREY
        ax.barh(yi, r["event_rate"], height=0.5, color=col)
        lo_, hi_ = r["event_rate_ci95"]
        ax.plot([lo_, hi_], [yi, yi], color=INK2, linewidth=1)
        ax.text(min(r["event_rate"], 1.0) + 0.02, yi + 0.3, f"{r['event_rate']:.2f}", va="center", color=INK, fontsize=8.5)
    ax.set_yticks(y)
    ax.set_yticklabels([labels[c] for c in order])
    ax.set_xlim(0, 1.12)
    ax.set_xlabel("fraction of seeds with a GHOST-v3 event (95% CI)")
    ax.set_title("b  Event rate under controls")
    _style(ax)

    # (c) channel pass rates (masters)
    ax = fig.add_subplot(gs[1, 1])
    pr = v3["channel_pass_rates"]["master"]
    names = list(pr)
    vals = [pr[n] for n in names]
    y = np.arange(len(names))[::-1]
    cols = [ORANGE if v >= 0.95 else BLUE for v in vals]
    ax.barh(y, vals, height=0.55, color=cols)
    ax.axvline(0.95, color=AXIS, linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("fraction of post-calibration windows the vote passes")
    ax.set_title("c  Detector channels: 'free votes' (≥95%) in orange")
    _style(ax)
    fig.suptitle("Figure 1 — Forensic re-adjudication of v3", x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_authorship(v4: Dict, path: Path) -> Path:
    plt = _plt()
    fig = plt.figure(figsize=(12.5, 8.4))
    gs = fig.add_gridspec(2, 2, hspace=0.5, wspace=0.55)

    # (a) primary + gate + placebo forest (standardized)
    ax = fig.add_subplot(gs[:, 0])
    rows = [("M  gate: TE network→world", v4["gate_manipulation_check"], v4["gate_manipulation_check"]["pass"])]
    short = {
        "H1_authorship_self_persistence": "H1  self persistence",
        "H2_self_specificity": "H2  self-specific",
        "H3_comparator_mechanism": "H3  comparator-dependent",
        "H4_authorship_causal_emergence": "H4  causal emergence Ψ",
        "H5_authorship_integration": "H5  integration Φ_R",
        "H6_nonlinear_arrow_of_time": "H6  arrow of time vs L2 (z)",
        "H7_authorship_arrow_of_time": "H7  arrow of time",
    }
    for k, r in v4["primary"].items():
        rows.append((short.get(k, k), r, r["significant"]))
    for k, r in v4["placebo_AA"].items():
        rows.append((f"placebo A/A  {k}", r, False))
    labels = [r[0] for r in rows]
    vals = [r[1]["d_z"] for r in rows]
    ci = [r[1].get("d_z_ci95", [r[1]["d_z"], r[1]["d_z"]]) for r in rows]
    cols = [BLUE if r[2] else GREY for r in rows]
    _hbar_ci(ax, labels, vals, ci, cols, "standardized paired effect d_z (95% bootstrap CI)")
    ax.set_title("a  Preregistered tests (blue = supported after Holm)")

    # (b) atlas
    ax = fig.add_subplot(gs[0, 1])
    atlas = v4["atlas"]
    pops = list(atlas)
    vals = [atlas[p]["persistence"]["d_z"] for p in pops]
    ci = [atlas[p]["persistence"].get("d_z_ci95", [v, v]) for p, v in zip(pops, vals)]
    cols = [ORANGE if p == "self" else GREY for p in pops]
    _hbar_ci(ax, pops, vals, ci, cols, "authorship effect on macro persistence, d_z")
    ax.set_title("b  Emergence atlas: master − twin, per population")

    # (c) mechanism
    ax = fig.add_subplot(gs[1, 1])
    conds = ["full", "no_comparator", "no_efference", "no_selffeedback", "frozen"]
    sec = v4["secondary"]
    res = [v4["primary"]["H1_authorship_self_persistence"]] + [sec[f"authorship_effect_within_{c}"] for c in conds[1:]]
    vals = [r["mean_diff"] for r in res]
    ci = [r["ci95"] for r in res]
    cols = [BLUE] + [GREY] * (len(conds) - 1)
    _hbar_ci(ax, ["intact agent", "comparator lesioned", "efference lesioned", "self-feedback lesioned",
                  "learning frozen"], vals, ci, cols, "self persistence, master − twin (nats, 95% CI)")
    ax.set_title("c  Which mechanism carries the authorship effect?")
    fig.suptitle("Figure 2 — Authorship: the same network, authoring vs. not authoring its actions",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def _diverging_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("bgr", [DIV_NEG, DIV_MID, DIV_POS])


def _fingerprint_panel(ax, fp: Dict, title: str, predicted: bool):
    names = list(fp)
    Z = np.array([[fp[n]["rungs"][r]["median_z"] for r in RUNGS] for n in names], dtype=float)
    S = np.sign(Z) * np.log10(1.0 + np.abs(Z))
    lim = 2.0
    im = ax.imshow(np.clip(S, -lim, lim), cmap=_diverging_cmap(), vmin=-lim, vmax=lim, aspect="auto")
    for i, n in enumerate(names):
        for j, r in enumerate(RUNGS):
            c = fp[n]["rungs"][r]
            z = Z[i, j]
            txt = f"{z:.0f}" if abs(z) >= 10 else f"{z:.1f}"
            differs = c.get("observed_differs", c.get("fraction_windows_differ", 0) >= 0.5)
            if c.get("exactly_invariant"):
                txt = "≡"
            weight = "bold" if differs else "normal"
            ink = "white" if abs(S[i, j]) > 1.35 else INK
            ax.text(j, i, txt, ha="center", va="center", fontsize=8, color=ink, fontweight=weight)
            if predicted and c.get("predicted_can_differ") is False and differs:
                ax.add_patch(__import__("matplotlib").patches.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                                                         edgecolor=INK, linewidth=1.4))
    ax.set_xticks(range(len(RUNGS)))
    ax.set_xticklabels(RUNG_LABELS, fontsize=8.5)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([f"{n}  ({fp[n]['kind']})" for n in names], fontsize=8.5)
    ax.set_title(title)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    return im


def fig_fingerprints(v4: Dict, v3: Dict, path: Path) -> Path:
    plt = _plt()
    fig = plt.figure(figsize=(16.5, 7.4))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.045], wspace=1.05)
    ax1 = fig.add_subplot(gs[0, 0])
    im = _fingerprint_panel(ax1, v4["fingerprint"], "a  v4 metrics on v4 agents (median z)", True)
    ax2 = fig.add_subplot(gs[0, 1])
    _fingerprint_panel(ax2, v3["v3_metric_fingerprint"], "b  v3's own metrics, metric-identical (median z)", False)
    cax = fig.add_subplot(gs[0, 2])
    cb = fig.colorbar(im, cax=cax)
    ticks = [-2, -1, 0, 1, 2]
    cb.set_ticks(ticks)
    cb.set_ticklabels(["−99", "−9", "0", "+9", "+99"])
    cb.outline.set_visible(False)
    cb.set_label("real vs its own surrogates (signed log z)", color=INK2)
    fig.text(0.01, -0.03, "Bold = real differs from its surrogates (p ≤ 0.05 and ≥1% deviation) in ≥50% of seeds/windows. "
             "≡ = exactly invariant. Boxed = differs although the metric's kind predicts it cannot.",
             color=INK2, fontsize=8.5)
    fig.suptitle("Figure 3 — Specificity fingerprints: which structure each metric actually reads",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_calibration_and_discrimination(cal: Dict, v4: Dict, path: Path) -> Path:
    plt = _plt()
    fig = plt.figure(figsize=(13, 6.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1], wspace=0.75)
    ax = fig.add_subplot(gs[0, 0])
    rows = cal["rows"]
    role_col = {"false_positive_rate": BLUE, "power": ORANGE}
    labels, y = [], np.arange(len(rows))[::-1]
    for yi, r in zip(y, rows):
        c = role_col.get(r["role"], AQUA)
        lo, hi = r["ci95"]
        ax.plot([lo, hi], [yi, yi], color=c, linewidth=2, alpha=0.55, solid_capstyle="round")
        ax.plot([r["detection_rate"]], [yi], "o", color=c, markersize=6.5, markeredgecolor=SURFACE, markeredgewidth=1.5)
        labels.append(f"{r['system']} · {r['metric']} · {r['rung'].split('_')[0]}")
    ax.axvline(0.05, color=AXIS, linewidth=1)
    ax.axvline(0.80, color=AXIS, linewidth=1)
    ax.set_xticks([0.0, 0.05, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xticklabels(["0", "α", "0.2", "0.4", "0.6", "0.8", "1"])
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlim(-0.02, 1.05)
    ax.set_xlabel("detection rate at α = 0.05 (95% Wilson CI)")
    ax.set_title("a  Instrument calibration on ground-truth systems")
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([], [], marker="o", color=c, linestyle="", label=l) for l, c in
                       (("property absent (false-positive rate)", BLUE), ("property present (power)", ORANGE),
                        ("rung preserves property (ceiling)", AQUA))],
              loc="upper left", bbox_to_anchor=(0.0, -0.11), ncol=2)
    _style(ax)

    ax = fig.add_subplot(gs[0, 1])
    disc = v4["discrimination"]
    tasks = list(disc)
    nice = {"real_vs_L0_shuffle": "real vs L0 shuffle", "real_vs_L1_iaaft": "real vs L1 IAAFT",
            "real_vs_L2_mvphase": "real vs L2 multivariate phase", "real_vs_L3_var": "real vs L3 VAR",
            "master_vs_twin_from_dynamics_alone": "master vs twin (dynamics only)",
            "placebo_master_vs_master": "placebo: master vs master"}
    y = np.arange(len(tasks))[::-1]
    for yi, t in zip(y, tasks):
        r = disc[t]
        ax.plot([r["null_mean"], r["null_95"]], [yi, yi], color=GREY, linewidth=6, alpha=0.6, solid_capstyle="butt")
        c = BLUE if r["p"] <= 0.05 else GREY
        ax.plot([r["auc"]], [yi], "o", color=c, markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.text(1.02, yi, f"{r['auc']:.2f}", va="center", color=INK, fontsize=8.5)
    ax.axvline(0.5, color=AXIS, linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels([nice.get(t, t) for t in tasks])
    ax.set_xlim(0.3, 1.08)
    ax.set_xlabel("leave-one-seed-out AUC (grey bar: permutation null mean → 95th pct)")
    ax.set_title("b  Blind discrimination")
    _style(ax)
    fig.suptitle("Figure 4 — Can the instrument fail, can it pass, and what can be told apart blind?",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def build_all(results: Dict, out_dir: Path, fig_dir: Path) -> List[Path]:
    fig_dir.mkdir(parents=True, exist_ok=True)
    made = []
    if results.get("v3_forensics"):
        made.append(fig_v3_forensics(results["v3_forensics"], fig_dir / "ghost_v4_figure_1_v3_forensics.png"))
    if results.get("v4"):
        made.append(fig_authorship(results["v4"], fig_dir / "ghost_v4_figure_2_authorship.png"))
        if results.get("v3_forensics"):
            made.append(fig_fingerprints(results["v4"], results["v3_forensics"],
                                         fig_dir / "ghost_v4_figure_3_fingerprints.png"))
        if results.get("calibration"):
            made.append(fig_calibration_and_discrimination(results["calibration"], results["v4"],
                                                           fig_dir / "ghost_v4_figure_4_calibration_discrimination.png"))
    return made
