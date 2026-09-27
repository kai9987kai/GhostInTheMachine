# Ghost in the Machine v5: Replication, Dose-Response and Mechanism of the Authorship Effect

**Kai Piper**
27 September 2026

> **Scientific status.** Synthetic computational experiments. Nothing here creates, detects, measures or proves phenomenal consciousness in any system.

## Abstract

v4 reported, under a locked preregistration, that when a recurrent self/world-modelling agent authors its own actions, the slowest collective mode of its "self" population becomes more persistent. The effect depended on an efference-copy/comparator loop and came with a rise in Rosas' causal-emergence criterion Ψ, a conjunction v4 labelled GHOST-v4. v5 tests that result in six preregistered studies, hashed and locked before any confirmatory run, on 168 new networks in 14 new worlds plus a re-simulation of the 48 v4 networks.

**The core effect is robust.** It replicated with the frozen v4 pipeline (d_z = 0.89). It grew with the degree of authorship (slope d_z = 0.76, 42/48 networks) and only with the comparator intact. It was larger under nonlinear (KSG, d_z = 1.38) and copula (1.27) estimators, and held in all four architectural variants tested (d_z 0.53–1.32). It is an online mechanism: it appeared when the comparator was switched on mid-run (d_z = 1.28) and vanished when it was switched off. It followed the comparator's wiring: rerouting the comparator from the self population to the DMN population moved the peak effect to DMN (d_z 0.96 → 1.70; shift d_z = 1.26).

**Two parts of the v4 story did not survive.**
1. **The emergence claim.** Authorship-dependent Ψ (H4) was significant in the v4 networks under all three estimators. But it did not replicate in new networks (d_z = 0.20, p = 0.10), showed no dose-response (d_z = 0.14), and was null in every architectural variant. The replication therefore reaches **level 3 of the preregistered ladder, not level 4: GHOST-v4 did not replicate.**
2. **The self's special status.** The effect's specificity to the "self" population is a property of where the comparator projects, not of the population.

The dose-response is threshold-like: almost flat from 0% to 75% authorship, with most of the effect appearing only when every action is the agent's own.

What survives is a narrower, sturdier claim. In this model, complete authorship stabilizes the slow dynamics of whichever population receives the comparator's prediction-error signal, online and in proportion to that coupling.

## 1. Why a follow-up

v4's main weaknesses, stated in its own limitations, were:
- a single confirmatory sample;
- the same analyst for development and confirmation;
- linear-Gaussian estimators;
- one architecture;
- a two-point authorship contrast;
- the untested possibility that "self-specificity" was simply where the comparator was wired.

Its most striking claim, authorship-dependent causal emergence (H4), also had the weakest support: it was not supported in development (d_z = 0.35) and was supported in confirmation (d_z = 0.59). v5 was designed to attack each of these directly, and its hypotheses were fixed before any v5 data existed.

## 2. Methods

### 2.1 Process

The v5 hypotheses were written and pushed (commit `7452b44`) before any v5 simulation. A technical pilot of studies B–F then ran on six development networks already examined in v4 (seeds 100–105, world 1). Its only purpose was to catch software faults; none were found and no hypothesis was changed (the pilot's estimates are recorded in the preregistration). The v5 preregistration, the replication preregistration, the frozen v4 sources and the v5 study code were then hashed and locked (commit `5c38075`, pushed) before any confirmatory run. The runner refuses to label output CONFIRMATORY unless the lock verifies. Every run is stored under a random code with a separate unblinding key, as in v4.

v4's code is untouched and its own lock still verifies. The v5 engine (`src/ghost_v5/engine.py`) mirrors v4's agent line for line and reproduces it **bit for bit** at default settings, for both masters and yoked twins (unit tests). It adds three handles:

- **graded authorship** in a live world: with probability 1 − p, the executed action is taken from a donor network's recorded closed-loop actions instead of the agent's own intention;
- a **comparator schedule** (the cycles during which comparator mismatch reaches the network);
- **comparator rerouting** (the same random projection with a different target mask).

### 2.2 Studies

| study | question | networks | design | primary tests |
|---|---|---|---|---|
| A | does v4 replicate? | 48 new (5000–5047), 4 new worlds | frozen v4 pipeline and analysis | M, H1–H7, verdict ladder |
| B | does the effect scale with the degree of authorship? | 48 new, 4 new worlds | p ∈ {0, .25, .5, .75, 1} in a live world, comparator intact and lesioned | B1 persistence slope > 0; B2 slope needs the comparator; B3 Ψ slope > 0 |
| C | does it survive nonlinear estimation? | the 48 v4 networks, re-simulated | KSG (k = 4) and Gaussian-copula MI for persistence and Ψ | C1–C4 master > twin |
| D | does it survive other architectures? | 24 new, 2 new worlds | leak 1.0, leak 0.3, radius 0.9, radius 1.1 | H1 in each variant |
| E | is it an online effect of the comparator? | 24 new, 2 new worlds | comparator always on / switched off at 3,000 / switched on at 3,000; window 3,501–6,000 | E1 appears when switched on; E2 disappears when switched off; E3 present without a switch |
| F | does it follow the comparator's wiring? | 24 new, 2 new worlds | comparator → self + association (standard) vs → DMN + association (rerouted) | F1 rerouted effect in DMN; F2 (DMN − self) effect shift |

Each study's primary family is Holm-corrected; Holm across all v5 primary tests is also reported. Tests are one-sided paired sign-flip randomization tests in the preregistered direction (exact for n ≤ 16, otherwise 20,000 flips). Effect sizes are given as mean differences (or mean per-network slopes for B) with 95% bootstrap CIs, and as d_z.

### 2.3 Nonlinear estimators

- **KSG.** The Kraskov–Stögbauer–Grassberger k-nearest-neighbour estimator (algorithm 1; Kraskov et al. 2004) is consistent for arbitrary dependence. It is implemented for pairs of one-dimensional variables, which is all that persistence and Ψ require.
- **Gaussian copula.** Gaussian-copula MI (Ince et al. 2017) rank-transforms each variable to normal marginals before Gaussian estimation. It is invariant to monotone transforms of each variable.
- **Validation.** Both are unit-tested against analytic Gaussian MI. KSG detects a purely nonlinear dependence (y = x² + noise) that the Gaussian estimator misses. Both reproduce the calibration signs of v4: Ψ > 0 for independent parts and Ψ < 0 for a redundant flock.

## 3. Results

All numbers come from `results/v5/results_v5.json`, produced under the verified v5 lock (status CONFIRMATORY). Every table is reproduced in `results/v5/SUMMARY_v5.md`. Figure 5 summarizes the studies.

![Figure 5](../figures/ghost_v5_figure_5_followup.png)

### 3.1 Study A: direct replication (48 new networks, 4 new worlds)

| | v4 confirmatory d_z | replication d_z [95% CI] | replication p (Holm) | replicated? |
|---|---|---|---|---|
| M manipulation check | 0.71 | 0.83 | < 0.001 | yes |
| H1 self persistence | 1.21 | 0.89 [0.58, 1.29] | < 0.001 | yes |
| H2 self-specific | 0.84 | 0.41 [0.14, 0.73] | 0.005 | yes (weaker) |
| H3 comparator-dependent | 0.54 | 0.75 [0.48, 1.09] | < 0.001 | yes |
| **H4 causal emergence Ψ** | 0.59 | **0.20 [−0.08, 0.51]** | **0.097** | **no** |
| H5 integration Φ_R | 0.39 | 0.83 [0.55, 1.20] | < 0.001 | yes |
| H6 nonlinear arrow of time | 2.55 | 3.48 [3.06, 4.21] | < 0.001 | yes |
| H7 authorship → arrow of time | 0.44 | 0.58 [0.29, 0.97] | < 0.001 | yes |

**Replication verdict: level 3** ("self-specific, comparator-dependent authorship effect: a self-stabilization mechanism"). GHOST-v4 (level 4) did not replicate.

Blind discrimination of master from twin using network dynamics alone was stronger than in v4 (AUC 0.80, null 95th percentile 0.56). The placebo master-vs-master classifier stayed at chance (AUC 0.50). Four of five placebo A/A contrasts were null. The fifth (irreversibility, d_z = 0.32, p = 0.035) is about the rate expected by chance across five tests; it is reported as a watch item.

The lesion pattern replicated:
- with the comparator lesioned, the authorship effect was d_z = −0.07;
- with the efference copy lesioned, d_z = −0.22 (interaction d_z = 0.93);
- without self-surprise feedback it remained intact (d_z = 0.99);
- with learning frozen it was reduced but present (d_z = 0.46).

The atlas did **not** replicate the v4 impression that the effect is strongest in the self population. The self effect (d_z = 0.89) was exceeded by association (1.10) and was similar to workspace (0.83) and memory (0.77); every population except sensory was significant. H2 still holds as preregistered (self larger than the *average* of the others), but "strongest in self" does not.

### 3.2 Study B: graded authorship

The manipulation hit its targets: intention/outcome agreement was 0.143, 0.364, 0.575, 0.788 and 1.000 at p = 0, 0.25, 0.5, 0.75 and 1 (expected 0.143, 0.357, 0.571, 0.786, 1.000).

| | mean per-network slope [95% CI] | d_z | p (Holm) |
|---|---|---|---|
| B1 persistence rises with authorship | +0.106 nats per unit p [0.067, 0.143] | 0.76 | < 0.001 |
| B2 slope needs the comparator (intact − lesioned) | +0.114 [0.063, 0.165] | 0.62 | < 0.001 |
| B3 Ψ rises with authorship | +0.055 [−0.046, 0.169] | 0.14 | 0.163 (not supported) |

42 of 48 networks had a positive slope. **The curve is not linear.** Relative to each network's own p = 0 run, persistence changed by +0.023, +0.009, +0.028 and **+0.130** nats at p = 0.25, 0.5, 0.75 and 1. Adjacent steps were n.s., n.s. and +0.019 (p = 0.002), followed by **+0.102 (p < 0.001)** from 75% to 100%. With the comparator lesioned the curve was flat. Most of the stabilization appears only when *every* executed action is the agent's own. This shape was not predicted and is reported as an exploratory observation. It suggests that even a minority of unexplained consequences keeps the comparator-driven perturbation going.

### 3.3 Study C: nonlinear estimators (v4 networks re-simulated)

The re-simulation reproduced the stored v4 values exactly (maximum |Δ self persistence| = 0).

| | master − twin | d_z [95% CI] | p (Holm) |
|---|---|---|---|
| C1 KSG persistence | +0.139 | 1.38 [1.05, 1.89] | < 0.001 |
| C2 KSG Ψ | +0.134 | 0.46 [0.20, 0.75] | 0.001 |
| C3 Gaussian-copula persistence | +0.130 | 1.27 [0.94, 1.76] | < 0.001 |
| C4 Gaussian-copula Ψ | +0.163 | 0.61 [0.34, 0.92] | < 0.001 |

The persistence effect is not an artifact of linear-Gaussian estimation; it is slightly larger under KSG than under the Gaussian estimator (d_z 1.21). In the v4 networks the Ψ effect also holds under both nonlinear estimators, driven by the macro term: the KSG parts-information contrast is d_z = 0.02. **v4's H4 result was therefore not an estimator artifact. It was a sample-specific result that did not generalize** (Studies A, B, D).

### 3.4 Study D: architecture robustness

| variant | self persistence, master − twin, d_z [95% CI] | p (Holm) | Ψ d_z | self-specificity d_z (p) |
|---|---|---|---|---|
| leak 1.0 (v3-style units) | 1.05 [0.77, 1.54] | < 0.001 | 0.08 | 0.35 (0.10) |
| leak 0.3 | 0.87 [0.51, 1.32] | < 0.001 | 0.04 | 0.34 (0.11) |
| radius 0.9 | 1.32 [1.03, 1.85] | < 0.001 | 0.16 | 0.55 (0.009) |
| radius 1.1 | 0.53 [0.04, 1.98] | 0.006 | −0.01 | 0.74 (< 0.001) |

The persistence effect held in every variant; Ψ did not move in any.

### 3.5 Study E: comparator timing (window 3,501–6,000)

| schedule | authorship effect on self persistence | d_z | p |
|---|---|---|---|
| sham (comparator always on) | +0.111 | 1.09 | < 0.001 |
| switched **off** at cycle 3,000 | −0.019 | −0.16 | 0.45 (two-sided) |
| switched **on** at cycle 3,000 | +0.142 | 1.28 | < 0.001 |

E1 (appears when switched on), E2 (disappears when switched off; d_z = 0.83) and E3 all passed. The effect is an **online** consequence of the comparator signal currently reaching the network, not a trait installed by training with it: 3,000 cycles of comparator-driven training leave no trace once the signal is removed, and 3,000 cycles without it do not prevent the effect once it arrives.

### 3.6 Study F: comparator rerouting

With the comparator rerouted from self + association to DMN + association (identical random projection, only the target mask moved):
- the DMN effect rose from d_z 0.96 to **1.70** (F1, p < 0.001);
- the self effect fell from 1.22 to 1.03;
- the preregistered shift, (DMN − self | rerouted) − (DMN − self | standard), was d_z = 1.26 (F2, p < 0.001).

In both wirings the effect was broad: every population except sensory showed it. Its **peak follows the comparator**.

### 3.7 All v5 primary tests together

Holm-corrected across all 23 v5 primary tests, 21 remain significant. The two that fail are both Ψ tests: A:H4 (p_Holm = 0.19) and B3 (p_Holm = 0.19).

## 4. Discussion

### 4.1 What survives

In this synthetic agent, **authoring one's own actions stabilizes the slow collective dynamics of the network, most strongly in whichever population receives the comparator's prediction-error signal.** This effect:

- replicated on new networks and new worlds with the frozen pipeline;
- grew with the degree of authorship, mainly at full authorship;
- is not an artifact of linear estimation;
- survives the architectural changes tested;
- is online: it exists while the comparator signal arrives and not otherwise;
- moves with the comparator's wiring;
- is detectable blind from the dynamics.

This is the comparator model of agency with a dynamical signature: the predictability of one's own consequences keeps the representation that receives the prediction errors stable.

### 4.2 What was retracted

1. **GHOST-v4 did not replicate.** The preregistered replication reached level 3. Authorship-dependent Ψ was real in the v4 sample under three estimators, but it did not generalize to new networks, did not scale with authorship, and did not appear in any architectural variant. Level 4 should be read as a property of one sample, not of the model.
2. **"Specific to the self population" was wiring, not selfhood.** The self population was special in v4 because the comparator projected into it. Move the projection and the effect moves. What the model calls its "self" is, dynamically, just the population that the comparator loop drives. That is arguably a more interesting statement than the original label, but it removes any claim that the self population is special in itself.

### 4.3 What was learned about the method

- **The most "profound" claim was the fragile one.** The conjunction that earned the GHOST-v4 label rested on its weakest component. Only a replication could reveal this: the v4 sample passed every preregistered test, so no amount of internal rigour on one sample could have shown it.
- **Estimator robustness and generalization are different questions.** Study C showed that the v4 Ψ result was not an estimator artifact. Study A showed it did not generalize. Either check alone would have told half the story.
- **Graded manipulations reveal shape.** A two-point contrast cannot distinguish a graded mechanism from a threshold. The dose-response did.

### 4.4 Limitations

- The same analyst ran every study. The locks and pushes make the order auditable, but independent replication remains the key missing step (see `docs/HOW_TO_REVIEW_OR_REPLICATE.md`).
- The threshold shape in Study B was not predicted and needs its own confirmatory test with finer levels near p = 1.
- Studies D–F used 24 networks each.
- All results concern one model family and its labelled populations.
- In the v4-style atlas, the effect is broad across populations. "Peak follows the comparator" is well supported; "confined to the comparator's target" is not.

### 4.5 Next

- Confirm the threshold with authorship levels between 0.75 and 1.
- Test whether *which* consequences are foreign matters (random vs consequential actions).
- Partial comparator gains, to test whether the effect scales with coupling strength.
- Independent external replication with the locked code.

## References (additional to the v4 paper)

- Ince, R. A. A., Giordano, B. L., Kayser, C., Rousselet, G. A., Gross, J., & Schyns, P. G. (2017). A statistical framework for neuroimaging data analysis based on mutual information estimated via a Gaussian copula. *Human Brain Mapping* 38, 1541–1573.
- Kraskov, A., Stögbauer, H., & Grassberger, P. (2004). Estimating mutual information. *Physical Review E* 69, 066138.

## Data, code and preregistration

- Hypotheses before data: commit `7452b44`. Lock: `prereg/PREREGISTRATION_v5.lock.json` (locked 2026-09-27T14:57:16Z, commit `5c38075`, pushed before any confirmatory run). Replication prereg: `prereg/REPLICATION_v4_1.json`.
- Code: `src/ghost_v5/` (entry point `src/ghost_in_the_machine_v5.py`), building on the frozen `src/ghost_v4/`.
- Results: `results/v5/results_v5.json`, `results/v5/SUMMARY_v5.md`, coded runs per study in `results/v5/<A–F>/`, the technical pilot in `results/v5_pilot/`.
- Reproduce: run the `run --study all`, `analyze` and `report` commands of `src/ghost_in_the_machine_v5.py` (about 30 minutes on 4 cores).
