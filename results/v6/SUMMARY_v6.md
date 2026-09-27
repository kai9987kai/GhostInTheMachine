# Ghost in the Machine v6 — what does the comparator's prediction error carry?

> Operational synthetic metrics only. No output of this software is evidence, detection or creation of subjective experience in any system.

Run status: **CONFIRMATORY** · v6 lock verifies: **True** · locked at 2026-09-27T15:54:13+00:00

## G — Prediction-error transplant

Gate (authorship effect, master live − twin live): diff 0.1354, d_z 1.10, p <0.001 → PASS

| hypothesis | mean diff [95% CI] | d_z [95% CI] | p (one-sided) | p (Holm, study) | result |
|---|---|---|---|---|---|
| G1_pe_content_necessary | 0.1239 [0.0928, 0.1600] | 1.02 [0.78, 1.72] | <0.001 | <0.001 | supported |
| G2_pe_content_sufficient | 0.1153 [0.0858, 0.1511] | 0.99 [0.80, 1.72] | <0.001 | <0.001 | supported |
| G3_contingency_matters | 0.0543 [0.0307, 0.0780] | 0.64 [0.39, 0.97] | <0.001 | <0.001 | supported |
| G4_amplitude_matters | 0.0378 [0.0288, 0.0468] | 1.19 [0.84, 1.71] | <0.001 | <0.001 | supported |

**Preregistered decision: contingency account.**

Equivalence (TOST, bound ±0.04 nats):

| contrast | mean diff | 90% CI | p (TOST) | equivalent to zero? |
|---|---|---|---|---|
| G1 | 0.1239 | [0.0978, 0.1549] | 1.000 | no |
| G2 | 0.1153 | [0.0900, 0.1443] | 1.000 | no |
| G3 | 0.0543 | [0.0346, 0.0747] | 0.876 | no |
| G4 | 0.0378 | [0.0304, 0.0455] | 0.317 | no |

| condition | self persistence [95% CI] | position between twin (0) and master (1) [95% CI] | injected RMS |
|---|---|---|---|
| twin, its own live error (reference 0) | 0.9812 [0.9392, 1.0236] | 0.00 [0.00, 0.00] | 0.248 |
| twin, comparator silent | 1.4769 [1.4157, 1.5410] | 3.66 [2.80, 4.85] | 0.000 |
| twin, given the master's error stream | 1.0965 [1.0442, 1.1541] | 0.85 [0.68, 1.10] | 0.191 |
| master, its own live error (reference 1) | 1.1166 [1.0642, 1.1712] | 1.00 [1.00, 1.00] | 0.191 |
| master, comparator silent | 1.4621 [1.4052, 1.5215] | 3.55 [2.74, 4.61] | 0.000 |
| master, own stream desynchronized | 1.0623 [1.0128, 1.1122] | 0.60 [0.44, 0.75] | 0.191 |
| master, own stream phase-randomized | 1.0539 [1.0040, 1.1051] | 0.54 [0.33, 0.73] | 0.190 |
| master, given the twin's error stream | 0.9927 [0.9521, 1.0327] | 0.08 [-0.02, 0.19] | 0.248 |
| master, twin's stream at master amplitude | 1.0305 [0.9856, 1.0753] | 0.36 [0.23, 0.52] | 0.193 |

| secondary | mean diff [95% CI] | d_z | p (two-sided) |
|---|---|---|---|
| phase_vs_live_master | 0.0627 [0.0346, 0.0916] | 0.61 | <0.001 |
| shift_vs_phase_master | 0.0084 [-0.0018, 0.0184] | 0.24 | 0.106 |
| off_master_vs_live_twin | 0.4809 [0.4348, 0.5275] | 2.84 | <0.001 |
| masterPE_twin_vs_live_master | -0.0202 [-0.0479, 0.0118] | -0.19 | 0.201 |
| association_G1 | 0.1844 [0.1294, 0.2590] | 0.79 | <0.001 |
| psi_live_master_minus_twin | 0.1569 [0.0761, 0.2366] | 0.55 | <0.001 |

## I — Near-full authorship, with the prediction error as candidate mediator

| hypothesis | mean diff [95% CI] | d_z [95% CI] | p (one-sided) | p (Holm, study) | result |
|---|---|---|---|---|---|
| I1_five_percent_foreign_reduces_persistence | 0.0343 [0.0235, 0.0464] | 0.83 [0.61, 1.22] | <0.001 | <0.001 | supported |
| I2_one_percent_foreign_reduces_persistence | 0.0031 [-0.0052, 0.0130] | 0.09 [-0.23, 0.31] | 0.286 | 0.286 | not supported |
| I3_foreign_actions_raise_own_step_error | 0.0025 [0.0022, 0.0028] | 2.39 [1.96, 3.09] | <0.001 | <0.001 | supported |
| I4_persistence_tracks_prediction_error | -1.6451 [-1.8324, -1.4700] | -2.55 [-3.13, -2.21] | <0.001 | <0.001 | supported |

| authorship p | intention = outcome | self persistence | relative to p = 1 [95% CI] | mismatch RMS | own-step mismatch | foreign-step mismatch |
|---|---|---|---|---|---|---|
| 0.75 | 0.789 | 1.0722 | -0.0881 [-0.1030, -0.0744] | 0.2321 | 0.2141 | 0.2992 |
| 0.9 | 0.915 | 1.1071 | -0.0532 [-0.0648, -0.0426] | 0.2140 | 0.2054 | 0.3068 |
| 0.95 | 0.958 | 1.1259 | -0.0343 [-0.0462, -0.0233] | 0.2071 | 0.2026 | 0.3108 |
| 0.99 | 0.992 | 1.1572 | -0.0031 [-0.0130, 0.0053] | 0.2015 | 0.2006 | 0.3113 |
| 1 | 1.000 | 1.1603 | 0.0000 [0.0000, 0.0000] | 0.2001 | 0.2001 | n/a |

Adjacent steps: 0.75->0.9: 0.0349 (p <0.001); 0.9->0.95: 0.0189 (p <0.001); 0.95->0.99: 0.0312 (p <0.001); 0.99->1: 0.0031 (p 0.575)

## J — Comparator gain

| hypothesis | mean diff [95% CI] | d_z [95% CI] | p (one-sided) | p (Holm, study) | result |
|---|---|---|---|---|---|
| J1_effect_present_at_half_gain | 0.0796 [-0.0230, 0.1558] | 0.34 [-0.05, 1.84] | 0.052 | 0.104 | not supported |
| J2_effect_grows_with_gain | 0.0372 [-0.0386, 0.1443] | 0.16 [-0.34, 0.42] | 0.307 | 0.307 | not supported |

| secondary | mean diff [95% CI] | d_z | p (two-sided) |
|---|---|---|---|
| authorship_effect_gain0.5 | 0.0796 [-0.0251, 0.1537] | 0.34 | 0.102 |
| authorship_effect_gain1 | 0.0758 [-0.0290, 0.1539] | 0.32 | 0.132 |
| authorship_effect_gain2 | 0.1167 [0.0770, 0.1582] | 1.12 | <0.001 |
| master_gain2_minus_gain0.5 | -0.3275 [-0.4279, -0.2275] | -1.28 | <0.001 |
| twin_gain2_minus_gain0.5 | -0.3647 [-0.4564, -0.2844] | -1.64 | <0.001 |

Descriptive (post-lock, not hypothesis tests): networks with master > twin — gain0.5: 21/24 (sign test p <0.001, median diff 0.130); gain1: 22/24 (sign test p <0.001, median diff 0.106); gain2: 23/24 (sign test p <0.001, median diff 0.096). The mean-based preregistered tests are dominated by two networks (12012, 12023) whose twin's slow mode became nearly frozen (persistence 2.0–2.6 nats).

| role, gain | self persistence [95% CI] | injected RMS |
|---|---|---|
| master:gain0.5 | 1.4090 [1.2747, 1.5627] | 0.095 |
| twin:gain0.5 | 1.3295 [1.1745, 1.5075] | 0.128 |
| master:gain1 | 1.2437 [1.1247, 1.3701] | 0.185 |
| twin:gain1 | 1.1678 [1.0323, 1.3240] | 0.248 |
| master:gain2 | 1.0815 [0.9850, 1.1880] | 0.358 |
| twin:gain2 | 0.9648 [0.8760, 1.0644] | 0.478 |

## All v6 primary tests, Holm-corrected across studies

| test | p | p (Holm, all v6) | significant |
|---|---|---|---|
| G:G1_pe_content_necessary | <0.001 | <0.001 | yes |
| G:G2_pe_content_sufficient | <0.001 | <0.001 | yes |
| G:G3_contingency_matters | <0.001 | <0.001 | yes |
| G:G4_amplitude_matters | <0.001 | <0.001 | yes |
| I:I1_five_percent_foreign_reduces_persistence | <0.001 | <0.001 | yes |
| I:I2_one_percent_foreign_reduces_persistence | 0.286 | 0.572 | no |
| I:I3_foreign_actions_raise_own_step_error | <0.001 | <0.001 | yes |
| I:I4_persistence_tracks_prediction_error | <0.001 | <0.001 | yes |
| J:J1_effect_present_at_half_gain | 0.052 | 0.157 | no |
| J:J2_effect_grows_with_gain | 0.307 | 0.572 | no |

## Living meta-analysis of the master − twin contrast (EXPLORATORY)

_POST-HOC, EXPLORATORY: not preregistered; the preregistered per-sample verdicts stand as reported._ Random-effects (DerSimonian–Laird) pooling over every independent sample run with the default architecture and the master vs cross-yoked-twin contrast.

**self persistence (nats)**: pooled 0.1339 [0.1154, 0.1525], p <0.001, 5 samples / 192 networks, I² 0.00, τ² 0, 95% prediction interval for a new sample [0.1041, 0.1638], pooled d_z 0.89.

| sample | networks | mean diff [95% CI] | d_z | weight |
|---|---|---|---|---|
| v4 confirmatory | 48 | 0.1404 [0.1075, 0.1733] | 1.21 | 0.32 |
| v5 A replication | 48 | 0.1196 [0.0815, 0.1578] | 0.89 | 0.24 |
| v5 F standard wiring | 24 | 0.1582 [0.1063, 0.2101] | 1.22 | 0.13 |
| v6 G live | 48 | 0.1354 [0.1007, 0.1702] | 1.10 | 0.28 |
| v6 J gain 1 | 24 | 0.0758 [-0.0198, 0.1714] | 0.32 | 0.04 |

**Ψ**: pooled 0.1287 [0.0767, 0.1807], p <0.001, 5 samples / 192 networks, I² 0.20, τ² 0.00069, 95% prediction interval for a new sample [0.0108, 0.2466], pooled d_z 0.36.

| sample | networks | mean diff [95% CI] | d_z | weight |
|---|---|---|---|---|
| v4 confirmatory | 48 | 0.1684 [0.0881, 0.2488] | 0.59 | 0.30 |
| v5 A replication | 48 | 0.0611 [-0.0273, 0.1495] | 0.20 | 0.26 |
| v5 F standard wiring | 24 | 0.0750 [-0.0648, 0.2148] | 0.21 | 0.12 |
| v6 G live | 48 | 0.1569 [0.0763, 0.2375] | 0.55 | 0.29 |
| v6 J gain 1 | 24 | 0.2612 [-0.0385, 0.5609] | 0.35 | 0.03 |

## Post-hoc re-reading of the v5 null results (EXPLORATORY)

_POST-HOC, EXPLORATORY: written after the v5 data were seen; not preregistered._ Bounds: persistence ±0.04 nats, Ψ ±0.0561 (one third of the v4 confirmatory H4 mean difference).

| v5 result | mean diff | 90% CI | bound | p (TOST) | evidence of absence? |
|---|---|---|---|---|---|
| A:H4 Ψ (replication) | 0.0611 | [-0.0096, 0.1355] | ±0.0561 | 0.543 | no |
| B3 Ψ slope over authorship | 0.0553 | [-0.0319, 0.1470] | ±0.0561 | 0.495 | no |
| D leak1.0 Ψ | 0.0134 | [-0.0422, 0.0728] | ±0.0561 | 0.123 | no |
| D leak0.3 Ψ | 0.0153 | [-0.1100, 0.1503] | ±0.0561 | 0.308 | no |
| D radius0.9 Ψ | 0.0601 | [-0.0664, 0.1868] | ±0.0561 | 0.522 | no |
| D radius1.1 Ψ | -0.0022 | [-0.1216, 0.1426] | ±0.0561 | 0.313 | no |
| E persistence effect, comparator switched off | -0.0186 | [-0.0562, 0.0211] | ±0.04 | 0.194 | no |

Small telescopes, A:H4 (Ψ): d33 = 0.175 for the original n = 48; replication d_z = 0.196; p(smaller than d33) = 0.583 → cannot rule out an effect of size d33. v4's own estimate lies above the replication's 95% CI: True.

