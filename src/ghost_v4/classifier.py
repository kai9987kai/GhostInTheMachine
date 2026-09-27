"""
Blind discrimination: can a classifier tell two conditions apart from metric
panels alone, on seeds it never trained on?

Design choices that matter:
* Leave-one-seed-out cross-validation. Both members of a pair (real vs
  surrogate, or master vs twin of the same network) are held out together, so
  the classifier can never exploit network identity.
* Feature standardization is fitted on training folds only.
* The null distribution of the cross-validated AUC is built by swapping labels
  within pairs, which preserves the pairing structure exactly.

A caution learned from v3: against a temporal shuffle this task is trivial
(one lag-1 autocorrelation separates the classes perfectly). An AUC is only
informative relative to the null rung it was computed against.
"""

from __future__ import annotations

from typing import Dict, Sequence

import numpy as np


def _fit_logistic(X: np.ndarray, y: np.ndarray, l2: float = 1.0, iters: int = 50) -> np.ndarray:
    Xb = np.column_stack([np.ones(len(X)), X])
    w = np.zeros(Xb.shape[1])
    reg = l2 * np.eye(Xb.shape[1])
    reg[0, 0] = 0.0
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(Xb @ w, -30, 30)))
        grad = Xb.T @ (p - y) + reg @ w
        H = (Xb * (p * (1 - p))[:, None]).T @ Xb + reg + 1e-9 * np.eye(len(w))
        step = np.linalg.solve(H, grad)
        w -= step
        if np.max(np.abs(step)) < 1e-8:
            break
    return w


def auc(scores: np.ndarray, y: np.ndarray) -> float:
    """Area under the ROC curve (Mann-Whitney U with tie correction)."""
    scores = np.asarray(scores, dtype=float)
    y = np.asarray(y, dtype=int)
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores))
    s_sorted = scores[order]
    i = 0
    while i < len(scores):
        j = i
        while j + 1 < len(scores) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    n1 = int(y.sum())
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def loso_auc(X: np.ndarray, y: np.ndarray, groups: np.ndarray, l2: float = 1.0) -> float:
    X = np.asarray(X, dtype=float)
    scores = np.empty(len(y))
    for g in np.unique(groups):
        test = groups == g
        train = ~test
        mu = X[train].mean(axis=0)
        sd = X[train].std(axis=0)
        sd[sd < 1e-12] = 1.0
        w = _fit_logistic((X[train] - mu) / sd, y[train], l2=l2)
        Xt = (X[test] - mu) / sd
        scores[test] = np.column_stack([np.ones(len(Xt)), Xt]) @ w
    return auc(scores, y)


def paired_discrimination(A: np.ndarray, B: np.ndarray, feature_names: Sequence[str],
                          n_perm: int = 200, rng: np.random.Generator | None = None, l2: float = 1.0) -> Dict:
    """
    A, B: (n_pairs, n_features) panels for condition A (label 1) and B (label 0),
    row i of A paired with row i of B (same seed).
    """
    rng = rng or np.random.default_rng(0)
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)
    keep = np.all(np.isfinite(A), axis=0) & np.all(np.isfinite(B), axis=0)
    A, B = A[:, keep], B[:, keep]
    n = len(A)
    X = np.vstack([A, B])
    y = np.r_[np.ones(n), np.zeros(n)].astype(int)
    groups = np.r_[np.arange(n), np.arange(n)]
    real = loso_auc(X, y, groups, l2)
    null = []
    for _ in range(n_perm):
        flip = rng.random(n) < 0.5
        yp = y.copy()
        yp[:n][flip] = 0
        yp[n:][flip] = 1
        null.append(loso_auc(X, yp, groups, l2))
    null = np.asarray(null)
    # Single-feature AUCs (pooled, not cross-validated) show which metrics carry the signal.
    single = {}
    for j, name in enumerate(np.asarray(feature_names)[keep]):
        a = auc(X[:, j], y)
        single[str(name)] = float(max(a, 1.0 - a))
    return {
        "auc": real,
        "null_mean": float(null.mean()),
        "null_95": float(np.quantile(null, 0.95)),
        "p": float((1 + np.sum(null >= real)) / (1 + len(null))),
        "n_pairs": n,
        "best_single_feature_auc": dict(sorted(single.items(), key=lambda kv: -kv[1])[:5]),
    }
