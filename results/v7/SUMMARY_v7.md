# Ghost in the Machine v7 — feedback vs innovation, a powered Ψ test, and a robust gain test

> Operational synthetic metrics only. No output of this software is evidence, detection or creation of subjective experience in any system.

Run status: **CONFIRMATORY** · v7 lock verifies: **True** · locked at 2026-09-27T19:11:54+00:00

## K — Feedback vs innovation: which part of the prediction error must be in step?

| hypothesis | estimate [95% CI] | d_z | p (one-sided) | p (Holm, study) | result |
|---|---|---|---|---|---|
| K1_desynchronization_costs_the_author | mean 0.0565 [0.0272, 0.0869] | 0.53 | <0.001 | <0.001 | supported |
| K2_live_state_feedback_restores | mean 0.2534 [0.1609, 0.3612] | 0.70 | <0.001 | <0.001 | supported |
| K3_live_innovation_restores | mean 0.0645 [0.0093, 0.1364] | 0.28 | 0.018 | 0.018 | supported |
| K4_synchrony_matters_more_for_the_author | mean 0.0670 [0.0390, 0.0965] | 0.66 | <0.001 | <0.001 | supported |

**Preregistered decision: both.**

Equivalence (TOST, ±0.04 nats): K2: mean 0.2534, 90% CI [0.1729, 0.3429], not equivalent; K3: mean 0.0645, 90% CI [0.0155, 0.1234], not equivalent

| condition | self persistence (nats) [95% CI] | bounded persistence ρ | injected RMS |
|---|---|---|---|
| master, live error | 1.1506 [1.0932, 1.2081] | 0.9438 | 0.182 |
| master, whole error desynchronized | 1.0941 [1.0423, 1.1460] | 0.9380 | 0.182 |
| master, state-predicted part live, rest desynchronized | 1.3475 [1.2404, 1.4683] | 0.9564 | 0.224 |
| master, state-predicted part desynchronized, rest live | 1.1586 [1.0831, 1.2397] | 0.9419 | 0.195 |
| twin, live error | 1.0249 [0.9697, 1.0804] | 0.9277 | 0.261 |
| twin, whole error desynchronized | 1.0354 [0.9821, 1.0888] | 0.9297 | 0.261 |

Fraction of the desynchronization loss recovered: fbLive_innShift: 4.48 [2.49, 9.69]; fbShift_innLive: 1.14 [0.17, 2.50]

Share of the live prediction error predicted by the network's own state (ridge R²): master 0.638 [0.620, 0.656], twin 0.296 [0.280, 0.313].

Robust versions (bounded persistence ρ, signed-rank):

| hypothesis | Hodges–Lehmann [95% CI] | positive | p (one-sided) |
|---|---|---|---|
| K1 | 0.0058 [0.0021, 0.0090] | 33/48 | 0.002 |
| K2 | 0.0153 [0.0109, 0.0205] | 42/48 | <0.001 |
| K3 | 0.0021 [-0.0007, 0.0059] | 27/48 | 0.093 |
| K4 | 0.0071 [0.0040, 0.0103] | 35/48 | <0.001 |

| secondary | estimate [95% CI] | d_z | p (two-sided) |
|---|---|---|---|
| authorship_effect_live | mean 0.1257 [0.0959, 0.1558] | 1.18 | <0.001 |
| twin_desync_cost | mean -0.0105 [-0.0249, 0.0042] | -0.20 | 0.170 |
| state_predictable_share_master_minus_twin | mean 0.3417 [0.3256, 0.3564] | 6.24 | <0.001 |
| fbLive_vs_innLive | mean 0.1889 [0.0742, 0.3043] | 0.46 | 0.001 |

## L — Powered test of authorship-dependent causal emergence (Ψ)

| hypothesis | estimate [95% CI] | d_z | p (one-sided) | p (Holm, study) | result |
|---|---|---|---|---|---|
| L1_authorship_raises_psi | mean 0.0322 [-0.0299, 0.0925] | 0.12 | 0.154 | 0.154 | not supported |
| L2_authorship_raises_bounded_persistence | HL 0.0163 [0.0131, 0.0197]; 66/72 positive | 1.16 | <0.001 (signed-rank) | <0.001 | supported |

Networks with master > twin: Ψ 41/72, ρ 66/72.

| secondary | estimate [95% CI] | d_z | p (two-sided) |
|---|---|---|---|
| psi_equivalence (TOST ±0.0561) | mean 0.0322, 90% CI [-0.0198, 0.0833] | | TOST p 0.230 → not equivalent |
| gaussian_persistence | mean 0.1580 [0.1313, 0.1859] | 1.31 | <0.001 |
| psi_signed_rank | HL 0.0411 [-0.0137, 0.0952]; 41/72 positive | 0.12 | 0.147 |
| psi_macro_term | mean 0.1580 [0.1312, 0.1859] | 1.31 | <0.001 |
| psi_parts_term | mean 0.1258 [0.0639, 0.1882] | 0.46 | <0.001 |
| state_predictable_share_master_minus_twin | mean 0.2955 [0.2829, 0.3076] | 5.54 | <0.001 |

## M — Comparator gain with a bounded measure and a rank-based test

| hypothesis | estimate [95% CI] | d_z | p (one-sided) | p (Holm, study) | result |
|---|---|---|---|---|---|
| M1_effect_present_at_half_gain | HL 0.0114 [0.0084, 0.0147]; 42/48 positive | 1.07 | <0.001 (signed-rank) | <0.001 | supported |
| M2_effect_grows_with_gain | HL 0.0114 [0.0072, 0.0159]; 38/48 positive | 0.68 | <0.001 (signed-rank) | <0.001 | supported |

| secondary | estimate [95% CI] | d_z | p (two-sided) |
|---|---|---|---|
| robust_effect_gain0.5 | HL 0.0114 [0.0084, 0.0144]; 42/48 positive | 1.07 | <0.001 |
| robust_effect_gain1 | HL 0.0156 [0.0115, 0.0198]; 41/48 positive | 1.17 | <0.001 |
| robust_effect_gain2 | HL 0.0226 [0.0173, 0.0283]; 43/48 positive | 1.24 | <0.001 |
| gaussian_effect_gain0.5 | mean 0.1347 [0.0912, 0.1797] | 0.86 | <0.001 |
| gaussian_effect_gain1 | mean 0.1441 [0.1100, 0.1802] | 1.15 | <0.001 |
| gaussian_effect_gain2 | mean 0.1522 [0.1190, 0.1860] | 1.28 | <0.001 |
| master_rho_gain2_minus_gain0.5 | HL -0.0294 [-0.0347, -0.0241]; 1/48 positive | -1.73 | <0.001 |
| twin_rho_gain2_minus_gain0.5 | HL -0.0415 [-0.0478, -0.0358]; 1/48 positive | -1.91 | <0.001 |

| role, gain | ρ [95% CI] | persistence (nats) | injected RMS |
|---|---|---|---|
| master:gain0.5 | 0.9597 [0.9540, 0.9651] | 1.3416 | 0.088 |
| twin:gain0.5 | 0.9479 [0.9415, 0.9543] | 1.2070 | 0.126 |
| master:gain1 | 0.9480 [0.9413, 0.9543] | 1.2063 | 0.173 |
| twin:gain1 | 0.9319 [0.9244, 0.9392] | 1.0622 | 0.248 |
| master:gain2 | 0.9298 [0.9223, 0.9369] | 1.0394 | 0.337 |
| twin:gain2 | 0.9062 [0.8984, 0.9144] | 0.8872 | 0.484 |

## All v7 primary tests, Holm-corrected across studies

| test | p | p (Holm, all v7) | significant |
|---|---|---|---|
| K:K1_desynchronization_costs_the_author | <0.001 | 0.001 | yes |
| K:K2_live_state_feedback_restores | <0.001 | <0.001 | yes |
| K:K3_live_innovation_restores | 0.018 | 0.035 | yes |
| K:K4_synchrony_matters_more_for_the_author | <0.001 | <0.001 | yes |
| L:L1_authorship_raises_psi | 0.154 | 0.154 | no |
| L:L2_authorship_raises_bounded_persistence | <0.001 | <0.001 | yes |
| M:M1_effect_present_at_half_gain | <0.001 | <0.001 | yes |
| M:M2_effect_grows_with_gain | <0.001 | <0.001 | yes |

## Cumulative meta-analysis of the master − twin contrast (prespecified, exploratory)

_PRESPECIFIED EXPLORATORY (sample list and methods fixed in the v7 preregistration before any v7 data)._ The identity ρ = √(1 − e^(−2I)) used for pre-v7 samples reproduces the directly computed ρ on v7 L data to within 9.9e-10.

**self persistence (nats)**: pooled 0.1389, DL 95% CI [0.1260, 0.1517], HKSJ 95% CI [0.1247, 0.1530], p (DL) <0.001, 8 samples / 360 networks, I² 0.00, prediction interval [0.1229, 0.1548], leave-one-out range [0.1338, 0.1417]; all networks pooled: 320/360 positive, signed-rank p <0.001.

| sample | networks | mean diff [95% CI] | d_z | weight |
|---|---|---|---|---|
| v4 confirmatory | 48 | 0.1404 [0.1075, 0.1733] | 1.21 | 0.15 |
| v5 A replication | 48 | 0.1196 [0.0815, 0.1578] | 0.89 | 0.11 |
| v5 F standard wiring | 24 | 0.1582 [0.1063, 0.2101] | 1.22 | 0.06 |
| v6 G live | 48 | 0.1354 [0.1007, 0.1702] | 1.10 | 0.14 |
| v6 J gain 1 | 24 | 0.0758 [-0.0198, 0.1714] | 0.32 | 0.02 |
| v7 K live | 48 | 0.1257 [0.0955, 0.1560] | 1.18 | 0.18 |
| v7 L | 72 | 0.1580 [0.1301, 0.1859] | 1.31 | 0.21 |
| v7 M gain 1 | 48 | 0.1441 [0.1086, 0.1795] | 1.15 | 0.13 |

**bounded persistence ρ**: pooled 0.0162, DL 95% CI [0.0148, 0.0177], HKSJ 95% CI [0.0146, 0.0179], p (DL) <0.001, 8 samples / 360 networks, I² 0.00, prediction interval [0.0144, 0.0181], leave-one-out range [0.0160, 0.0168]; all networks pooled: 320/360 positive, signed-rank p <0.001.

| sample | networks | mean diff [95% CI] | d_z | weight |
|---|---|---|---|---|
| v4 confirmatory | 48 | 0.0179 [0.0138, 0.0220] | 1.24 | 0.13 |
| v5 A replication | 48 | 0.0153 [0.0107, 0.0199] | 0.94 | 0.10 |
| v5 F standard wiring | 24 | 0.0174 [0.0120, 0.0228] | 1.28 | 0.07 |
| v6 G live | 48 | 0.0173 [0.0136, 0.0210] | 1.32 | 0.16 |
| v6 J gain 1 | 24 | 0.0109 [0.0059, 0.0159] | 0.88 | 0.09 |
| v7 K live | 48 | 0.0161 [0.0115, 0.0207] | 0.99 | 0.10 |
| v7 L | 72 | 0.0170 [0.0136, 0.0203] | 1.16 | 0.19 |
| v7 M gain 1 | 48 | 0.0161 [0.0122, 0.0200] | 1.17 | 0.14 |

**Ψ**: pooled 0.0829, DL 95% CI [0.0334, 0.1325], HKSJ 95% CI [0.0252, 0.1407], p (DL) 0.001, 8 samples / 360 networks, I² 0.56, prediction interval [-0.0574, 0.2233], leave-one-out range [0.0659, 0.0967]; all networks pooled: 232/360 positive, signed-rank p <0.001.

| sample | networks | mean diff [95% CI] | d_z | weight |
|---|---|---|---|---|
| v4 confirmatory | 48 | 0.1684 [0.0881, 0.2488] | 0.59 | 0.15 |
| v5 A replication | 48 | 0.0611 [-0.0273, 0.1495] | 0.20 | 0.14 |
| v5 F standard wiring | 24 | 0.0750 [-0.0648, 0.2148] | 0.21 | 0.08 |
| v6 G live | 48 | 0.1569 [0.0763, 0.2375] | 0.55 | 0.15 |
| v6 J gain 1 | 24 | 0.2612 [-0.0385, 0.5609] | 0.35 | 0.02 |
| v7 K live | 48 | 0.0078 [-0.0642, 0.0798] | 0.03 | 0.16 |
| v7 L | 72 | 0.0322 [-0.0296, 0.0940] | 0.12 | 0.18 |
| v7 M gain 1 | 48 | 0.0565 [-0.0394, 0.1523] | 0.17 | 0.13 |

