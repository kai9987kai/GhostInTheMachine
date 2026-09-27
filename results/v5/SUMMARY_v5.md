# Ghost in the Machine v5 — follow-up studies

> Operational synthetic metrics only. No output of this software is evidence, detection or creation of subjective experience in any system.

Run status: **CONFIRMATORY** · v5 lock verifies: **True** · locked at 2026-09-27T14:57:16+00:00

## A — Direct replication (frozen v4 pipeline, 48 new networks, 4 new worlds)

**Replication verdict: level 3 — Self-specific, comparator-dependent authorship effect (M, H1, H2, H3): a self-stabilization mechanism.**

Gate M: diff 0.0679, d_z 0.83, p <0.001 → PASS

| hypothesis | mean diff [95% CI] | d_z [95% CI] | p (one-sided) | p (Holm, study) | result |
|---|---|---|---|---|---|
| H1_authorship_self_persistence | 0.1196 [0.0820, 0.1569] | 0.89 [0.58, 1.29] | <0.001 | <0.001 | supported |
| H2_self_specificity | 0.0479 [0.0158, 0.0796] | 0.41 [0.14, 0.73] | 0.003 | 0.005 | supported |
| H3_comparator_mechanism | 0.1284 [0.0804, 0.1771] | 0.75 [0.48, 1.09] | <0.001 | <0.001 | supported |
| H4_authorship_causal_emergence | 0.0611 [-0.0243, 0.1498] | 0.20 [-0.08, 0.51] | 0.097 | 0.097 | not supported |
| H5_authorship_integration | 0.0081 [0.0053, 0.0108] | 0.83 [0.55, 1.20] | <0.001 | <0.001 | supported |
| H6_nonlinear_arrow_of_time | 85.4321 [78.8946, 92.3430] | 3.48 [3.06, 4.21] | <0.001 | <0.001 | supported |
| H7_authorship_arrow_of_time | 0.0011 [0.0006, 0.0016] | 0.58 [0.29, 0.97] | <0.001 | <0.001 | supported |

Placebo A/A: self_persistence d_z -0.04 (p 0.797); self_psi d_z 0.01 (p 0.928); phi_r_mean d_z 0.00 (p 0.979); irr_nodes d_z 0.32 (p 0.035); te_net_to_obs d_z 0.03 (p 0.833)

## B — Graded authorship (dose-response, live world)

For B1-B3 the effect is the mean per-network OLS slope (nats per unit of authorship p); B2 is the difference of slopes, intact minus comparator-lesioned.

| hypothesis | mean diff [95% CI] | d_z [95% CI] | p (one-sided) | p (Holm, study) | result |
|---|---|---|---|---|---|
| B1_persistence_rises_with_authorship | 0.1058 [0.0669, 0.1432] | 0.76 [0.45, 1.24] | <0.001 | <0.001 | supported |
| B2_dose_response_needs_comparator | 0.1144 [0.0626, 0.1654] | 0.62 [0.32, 1.07] | <0.001 | <0.001 | supported |
| B3_psi_rises_with_authorship | 0.0553 [-0.0463, 0.1688] | 0.14 [-0.15, 0.42] | 0.163 | 0.163 | not supported |

Networks with a positive persistence slope: 42/48

| authorship p | intention = outcome | persistence (intact) [95% CI] | persistence (comparator lesioned) | Ψ (intact) |
|---|---|---|---|---|
| 0 | 0.143 | 1.0927 [1.0142, 1.1723] | 1.5831 | -0.1146 |
| 0.25 | 0.364 | 1.1161 [1.0306, 1.2057] | 1.5759 | -0.1751 |
| 0.5 | 0.575 | 1.1017 [1.0262, 1.1791] | 1.5723 | -0.0979 |
| 0.75 | 0.788 | 1.1208 [1.0476, 1.1972] | 1.5682 | -0.0985 |
| 1 | 1.000 | 1.2225 [1.1454, 1.3013] | 1.5762 | -0.0838 |

Adjacent steps (intact): 0->0.25: 0.0234 (p 0.493); 0.25->0.5: -0.0144 (p 0.971); 0.5->0.75: 0.0192 (p 0.002); 0.75->1: 0.1017 (p <0.001)

## C — Nonlinear-estimator robustness (re-simulated v4 networks)

| hypothesis | mean diff [95% CI] | d_z [95% CI] | p (one-sided) | p (Holm, study) | result |
|---|---|---|---|---|---|
| C1_ksg_persistence | 0.1391 [0.1114, 0.1674] | 1.38 [1.05, 1.89] | <0.001 | <0.001 | supported |
| C2_ksg_psi | 0.1340 [0.0519, 0.2188] | 0.46 [0.20, 0.75] | 0.001 | 0.001 | supported |
| C3_gc_persistence | 0.1298 [0.1010, 0.1579] | 1.27 [0.94, 1.76] | <0.001 | <0.001 | supported |
| C4_gc_psi | 0.1633 [0.0878, 0.2404] | 0.61 [0.34, 0.92] | <0.001 | <0.001 | supported |

Re-simulation reproduces the stored v4 values: **True** (max |Δ self_persistence| = 0).

KSG parts-information contrast: 0.0051 (d_z 0.02, p 0.907). Gaussian reference: H1 d_z 1.21, H4 d_z 0.59.

## D — Architecture robustness

| hypothesis | mean diff [95% CI] | d_z [95% CI] | p (one-sided) | p (Holm, study) | result |
|---|---|---|---|---|---|
| D_leak1.0_self_persistence | 0.0555 [0.0358, 0.0766] | 1.05 [0.77, 1.54] | <0.001 | <0.001 | supported |
| D_leak0.3_self_persistence | 0.1190 [0.0677, 0.1723] | 0.87 [0.51, 1.32] | <0.001 | <0.001 | supported |
| D_radius0.9_self_persistence | 0.1301 [0.0933, 0.1703] | 1.32 [1.03, 1.85] | <0.001 | <0.001 | supported |
| D_radius1.1_self_persistence | 0.0996 [0.0160, 0.1602] | 0.53 [0.04, 1.98] | 0.006 | 0.006 | supported |

| secondary | mean diff | d_z | p (two-sided) |
|---|---|---|---|
| leak1.0_psi | 0.0134 | 0.08 | 0.724 |
| leak1.0_self_specificity | 0.0252 | 0.35 | 0.104 |
| leak1.0_te_manipulation_check | 0.0641 | 0.80 | <0.001 |
| leak0.3_psi | 0.0153 | 0.04 | 0.852 |
| leak0.3_self_specificity | 0.0437 | 0.34 | 0.110 |
| leak0.3_te_manipulation_check | 0.0400 | 0.69 | 0.002 |
| radius0.9_psi | 0.0601 | 0.16 | 0.447 |
| radius0.9_self_specificity | 0.0553 | 0.55 | 0.009 |
| radius0.9_te_manipulation_check | 0.0757 | 0.89 | <0.001 |
| radius1.1_psi | -0.0022 | -0.01 | 0.985 |
| radius1.1_self_specificity | 0.0824 | 0.74 | <0.001 |
| radius1.1_te_manipulation_check | 0.0568 | 0.86 | <0.001 |

## E — Comparator timing

| hypothesis | mean diff [95% CI] | d_z [95% CI] | p (one-sided) | p (Holm, study) | result |
|---|---|---|---|---|---|
| E1_effect_appears_when_comparator_switched_on | 0.1423 [0.0973, 0.1842] | 1.28 [0.72, 2.26] | <0.001 | <0.001 | supported |
| E2_effect_disappears_when_comparator_switched_off | 0.1300 [0.0705, 0.1930] | 0.83 [0.53, 1.25] | <0.001 | <0.001 | supported |
| E3_effect_present_in_sham_window | 0.1114 [0.0724, 0.1528] | 1.09 [0.75, 1.62] | <0.001 | <0.001 | supported |

| secondary | mean diff | d_z | p (two-sided) |
|---|---|---|---|
| authorship_effect_sham | 0.1114 | 1.09 | <0.001 |
| authorship_effect_off_late | -0.0186 | -0.16 | 0.445 |
| authorship_effect_on_late | 0.1423 | 1.28 | <0.001 |
| on_late_minus_sham | 0.0309 | 0.38 | 0.073 |

## F — Comparator rerouting

| hypothesis | mean diff [95% CI] | d_z [95% CI] | p (one-sided) | p (Holm, study) | result |
|---|---|---|---|---|---|
| F1_rerouted_effect_in_dmn | 0.1253 [0.0972, 0.1554] | 1.70 [1.30, 2.65] | <0.001 | <0.001 | supported |
| F2_effect_follows_comparator | 0.1477 [0.1021, 0.1941] | 1.26 [0.83, 2.00] | <0.001 | <0.001 | supported |

| population | effect, standard wiring (d_z, p) | effect, rerouted to DMN (d_z, p) |
|---|---|---|
| sensory | 0.31 (0.143) | 0.32 (0.137) |
| association | 1.09 (<0.001) | 1.38 (<0.001) |
| memory | 0.97 (<0.001) | 1.32 (<0.001) |
| workspace | 1.09 (<0.001) | 1.39 (<0.001) |
| self | 1.22 (<0.001) | 1.03 (<0.001) |
| dmn | 0.96 (<0.001) | 1.70 (<0.001) |
| thalamus | 0.70 (0.002) | 0.88 (<0.001) |
| striatum | 0.86 (<0.001) | 0.73 (0.002) |
| gpe | 0.77 (<0.001) | 0.82 (<0.001) |
| stn | 0.62 (0.004) | 0.82 (<0.001) |
| gpi | 0.73 (0.001) | 0.87 (<0.001) |
| control | 0.56 (0.011) | 0.66 (0.005) |

## All v5 primary tests, Holm-corrected across studies

| test | p | p (Holm, all v5) | significant |
|---|---|---|---|
| A:H1_authorship_self_persistence | <0.001 | 0.001 | yes |
| A:H2_self_specificity | 0.003 | 0.011 | yes |
| A:H3_comparator_mechanism | <0.001 | 0.001 | yes |
| A:H4_authorship_causal_emergence | 0.097 | 0.195 | no |
| A:H5_authorship_integration | <0.001 | 0.001 | yes |
| A:H6_nonlinear_arrow_of_time | <0.001 | 0.001 | yes |
| A:H7_authorship_arrow_of_time | <0.001 | 0.001 | yes |
| B:B1_persistence_rises_with_authorship | <0.001 | 0.001 | yes |
| B:B2_dose_response_needs_comparator | <0.001 | 0.001 | yes |
| B:B3_psi_rises_with_authorship | 0.163 | 0.195 | no |
| C:C1_ksg_persistence | <0.001 | 0.001 | yes |
| C:C2_ksg_psi | 0.001 | 0.006 | yes |
| C:C3_gc_persistence | <0.001 | 0.001 | yes |
| C:C4_gc_psi | <0.001 | 0.001 | yes |
| D:D_leak1.0_self_persistence | <0.001 | 0.001 | yes |
| D:D_leak0.3_self_persistence | <0.001 | 0.001 | yes |
| D:D_radius0.9_self_persistence | <0.001 | 0.001 | yes |
| D:D_radius1.1_self_persistence | 0.006 | 0.019 | yes |
| E:E1_effect_appears_when_comparator_switched_on | <0.001 | 0.001 | yes |
| E:E2_effect_disappears_when_comparator_switched_off | <0.001 | 0.001 | yes |
| E:E3_effect_present_in_sham_window | <0.001 | 0.001 | yes |
| F:F1_rerouted_effect_in_dmn | <0.001 | 0.001 | yes |
| F:F2_effect_follows_comparator | <0.001 | 0.001 | yes |

