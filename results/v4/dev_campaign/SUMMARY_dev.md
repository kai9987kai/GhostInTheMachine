# Ghost in the Machine v4 — results summary

> DEV (exploratory)

Preregistration lock verifies: **None** (mismatches: None)

## Authorship campaign (EXPLORATORY dev seeds, 12 network seeds)

**Verdict: level 3 — Self-specific, comparator-dependent authorship effect (M, H1, H2, H3): a self-stabilization mechanism.**

Gate M (authorship is real; TE network→world): diff 0.0562, d_z 1.25, p <0.001 → PASS

| Hypothesis | mean diff [95% CI] | d_z | p (one-sided) | p (Holm) | result |
|---|---|---|---|---|---|
| H1_authorship_self_persistence | 0.0915 [0.0525, 0.1312] | 1.24 | <0.001 | 0.004 | supported |
| H2_self_specificity | 0.0744 [0.0340, 0.1125] | 1.04 | 0.003 | 0.007 | supported |
| H3_comparator_mechanism | 0.1353 [0.0802, 0.1943] | 1.29 | <0.001 | 0.002 | supported |
| H4_authorship_causal_emergence | 0.0700 [-0.0321, 0.1792] | 0.35 | 0.124 | 0.124 | not supported |
| H5_authorship_integration | 0.0126 [0.0068, 0.0188] | 1.12 | <0.001 | 0.004 | supported |
| H6_nonlinear_arrow_of_time | 64.4996 [55.5620, 75.2505] | 3.47 | <0.001 | 0.002 | supported |
| H7_authorship_arrow_of_time | 0.0012 [0.0006, 0.0018] | 1.08 | <0.001 | 0.004 | supported |

Placebo A/A contrasts (same network, no authorship difference; should be null):

| endpoint | mean diff | d_z | p (two-sided) |
|---|---|---|---|
| self_persistence | -0.0224 | -0.72 | 0.033 |
| self_psi | 0.0326 | 0.28 | 0.348 |
| phi_r_mean | -0.0020 | -0.55 | 0.089 |
| irr_nodes | 0.0003 | 0.40 | 0.197 |
| te_net_to_obs | -0.0001 | -0.01 | 0.986 |

Emergence atlas — authorship effect on macro persistence per population:

| population | mean diff | d_z | p | q (BH) |
|---|---|---|---|---|
| sensory | -0.0320 | -0.56 | 0.076 | 0.229 |
| association | 0.0410 | 0.89 | 0.014 | 0.085 |
| memory | 0.0417 | 0.46 | 0.142 | 0.267 |
| workspace | 0.0502 | 0.68 | 0.043 | 0.172 |
| self | 0.0915 | 1.24 | 0.001 | 0.018 |
| dmn | 0.0366 | 0.44 | 0.156 | 0.267 |
| thalamus | -0.0032 | -0.04 | 0.895 | 0.944 |
| striatum | 0.0393 | 0.45 | 0.151 | 0.267 |
| gpe | 0.0111 | 0.14 | 0.628 | 0.754 |
| stn | 0.0271 | 0.34 | 0.277 | 0.416 |
| gpi | -0.0021 | -0.02 | 0.944 | 0.944 |
| control | -0.0222 | -0.30 | 0.315 | 0.421 |

Secondary (exploratory, two-sided, BH-FDR):

| contrast | mean diff | d_z | p | q |
|---|---|---|---|---|
| interaction_no_efference | 0.0955 | 1.50 | <0.001 | 0.003 |
| interaction_no_selffeedback | 0.0204 | 0.32 | 0.305 | 0.416 |
| interaction_frozen | 0.0511 | 0.29 | 0.326 | 0.416 |
| authorship_effect_within_no_comparator | -0.0438 | -0.43 | 0.163 | 0.288 |
| authorship_effect_within_no_efference | -0.0040 | -0.10 | 0.732 | 0.732 |
| authorship_effect_within_no_selffeedback | 0.0710 | 0.76 | 0.024 | 0.080 |
| authorship_effect_within_frozen | 0.0403 | 0.21 | 0.479 | 0.580 |
| authorship_self_ntic | -0.0046 | -0.11 | 0.719 | 0.732 |
| authorship_self_micro_dependence | 0.0142 | 0.52 | 0.250 | 0.383 |
| authorship_self_env_dependence | 0.0059 | 0.18 | 0.547 | 0.629 |
| authorship_self_delta | -0.0484 | -0.67 | 0.038 | 0.097 |
| authorship_self_psi_r | 0.0837 | 0.47 | 0.132 | 0.254 |
| authorship_irr_modules_q3 | 0.0086 | 0.37 | 0.229 | 0.375 |
| authorship_lagged_asymmetry | 0.0256 | 0.71 | 0.035 | 0.097 |
| authorship_pr_dimension | -0.3221 | -0.54 | 0.094 | 0.216 |
| authorship_fc_mean_abs_corr | 0.0081 | 0.30 | 0.320 | 0.416 |
| authorship_mse_global | -0.0026 | -0.47 | 0.126 | 0.254 |
| authorship_pci_lz_mean | -0.0025 | -0.14 | 0.722 | 0.732 |
| authorship_ignition | -0.0282 | -5.13 | <0.001 | 0.003 |
| authorship_activity | -0.0038 | -0.91 | 0.014 | 0.052 |
| authorship_prediction_error | -0.0803 | -8.71 | <0.001 | 0.003 |
| authorship_self_model_error | -0.0040 | -6.24 | <0.001 | 0.003 |
| authorship_te_obs_to_net | 0.1440 | 1.02 | 0.003 | 0.016 |

Specificity fingerprint (median z of real vs null; * = in ≥50% of seeds real differs from its surrogates at p≤0.05 AND by ≥1%; ≡ = exactly invariant; predicted ceiling in brackets):

| metric | kind | L0_shuffle | L1_iaaft | L2_mvphase | L3_var |
|---|---|---|---|---|---|
| pr_dimension | zero-lag | 0.0≡ [cannot] | -232.1* [can] | 0.0≡ [cannot] | 0.2 [cannot] |
| fc_mean_abs_corr | zero-lag | 0.0≡ [cannot] | 68.0* [can] | 0.0≡ [cannot] | 0.0 [cannot] |
| mse_global | univariate-temporal | -110.6* [can] | -19.5* [cannot] | 0.2 [cannot] | -0.1 [cannot] |
| self_persistence | lagged-linear | 1813.5* [can] | 104.4* [can] | 1.7 [cannot] | 0.4 [cannot] |
| self_psi | lagged-linear | 2.1* [can] | -0.1* [can] | 0.0 [cannot] | -0.1 [cannot] |
| phi_r_mean | lagged-linear | 1135.7* [can] | 833.4* [can] | 10.1 [cannot] | -0.5 [cannot] |
| lagged_asymmetry | lagged-linear | -4.1* [can] | 47.8* [can] | -0.1 [cannot] | -0.6 [cannot] |
| irr_nodes | nonlinear-temporal | 46.8* [can] | 61.1* [can] | 59.8* [can] | 58.8* [can] |
| irr_modules_q3 | nonlinear-temporal | 10.5* [can] | 6.6* [can] | 6.2* [can] | 5.5* [can] |

Blind discrimination (leave-one-seed-out AUC; within-pair permutation null):

| task | AUC | null 95% | p | strongest single features |
|---|---|---|---|---|
| real_vs_L0_shuffle | 1.000 | 0.715 | 0.005 | mse_global 1.00, self_persistence 1.00, phi_r_mean 1.00 |
| real_vs_L1_iaaft | 1.000 | 0.764 | 0.005 | pr_dimension 1.00, fc_mean_abs_corr 1.00, phi_r_mean 1.00 |
| real_vs_L2_mvphase | 1.000 | 0.708 | 0.005 | irr_nodes 1.00, irr_modules_q3 0.97, phi_r_mean 0.54 |
| real_vs_L3_var | 1.000 | 0.703 | 0.005 | irr_nodes 1.00, irr_modules_q3 0.98, self_persistence 0.55 |
| master_vs_twin_from_dynamics_alone | 0.667 | 0.611 | 0.015 | irr_nodes 0.70, phi_r_mean 0.67, self_persistence 0.66 |
| placebo_master_vs_master | 0.493 | 0.556 | 0.592 | self_persistence 0.55, atlas_persistence_self 0.55, phi_r_mean 0.54 |

