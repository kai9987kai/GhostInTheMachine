# Ghost in the Machine v6: The Authorship Effect Is Carried by the Prediction Error

**Kai Piper**
27 September 2026

> **Scientific status.** Synthetic computational experiments. Nothing here creates, detects, measures or proves phenomenal consciousness in any system.

## Abstract

v4 and v5 established, under locked preregistrations and a direct replication, a robust effect in a synthetic self/world-modelling agent: when the agent authors its own actions, the slowest collective mode of the population receiving its comparator's prediction-error signal becomes more persistent. v6 asks *why*. The comparator's only input to the network is the prediction error, so v6 makes that stream an experimental variable. It transplants the stream between an agent and its cross-yoked twin, desynchronizes it, phase-randomizes it and rescales it.

Three studies were preregistered and locked before any v6 data (48 + 48 + 24 new networks, 816 runs). The main study pitted a deflationary **amplitude** account (a non-author's larger errors act as injected noise) against a **contingency** account (the error matters because it is in step with the network's own state).

- **The effect travels with the error stream.** An author given a non-author's stream falls to 0.08 of the way from twin to master (d_z = 1.02). A non-author given the author's stream rises to 0.85 (d_z = 0.99).
- **Amplitude alone does not explain it.** Desynchronizing the author's own stream, which keeps every value, the amplitude and the spectrum exactly, removes 40% of the effect (d_z = 0.64). The amplitude account had predicted no change. By the preregistered decision rule, the contingency account is supported. Amplitude contributes too: rescaling the twin's stream to the author's amplitude recovers 28 points (d_z = 1.19).
- **The comparator perturbs; authorship attenuates.** Silencing the comparator raises persistence far above either agent (+0.35 nats in the master). The prediction error perturbs the slow mode, and authorship makes that perturbation smaller, spectrally gentler and better timed. This is a dynamical analogue of sensory attenuation.
- **Near-full authorship.** 5% foreign actions reduce persistence (d_z = 0.83); 1% does not. Foreign actions degrade the forward model's predictions even for the agent's own actions (d_z = 2.39). Within networks, persistence tracks the prediction error almost perfectly across authorship levels (d_z = −2.55). v5's apparent threshold at exactly 100% authorship was a coarse-grid artifact.
- **Comparator gain.** Scaling the comparator gain (Study J) was inconclusive, because two networks whose twins' slow mode nearly froze dominate the means.

Two exploratory analyses revise the record:
- None of v5's null results is evidence of absence (equivalence tests; small telescopes).
- A random-effects meta-analysis over all five independent samples (192 networks) finds the persistence effect entirely consistent (+0.134 nats, I² = 0). It also finds a **modest, variable causal-emergence (Ψ) effect** (+0.129 [0.077, 0.181], I² = 0.20). v5's "Ψ did not replicate" was therefore too strong.

A new claims ledger checks every headline number in CI against its results file. It caught one rounding error in the v5 report.

## 1. Question

In this agent, the comparator injects `W_cmp · (observation − forward-model prediction for the intended action)` into its target populations. v5 showed that the authorship effect needs that term, appears and disappears with it, and follows its wiring. That still leaves two quite different explanations.

- **Amplitude (deflationary).** A twin's predictions are about actions that did not happen, so its prediction errors are larger. Larger injected input shakes the slow mode more. On this account, "authorship" is just "smaller noise".
- **Contingency.** An author's error is in step with its own state and actions. The error then acts less like external noise and more like part of the network's own closed-loop dynamics.

Existing v4 data, examined before v6 was designed, made the question pressing. The twin's prediction error was about twice the master's in every one of 48 networks (0.232 vs 0.118). Yet across networks, the size of that excess did not predict the size of the persistence effect (r = 0.05).

## 2. Methods

### 2.1 A replaceable prediction-error channel

`src/ghost_v6/engine.py` mirrors the v5 agent line for line. It reproduces v5, and therefore v4, **bit for bit** at default settings, for masters, twins and graded authorship (unit tests). It records the full 16-dimensional mismatch vector at every cycle. From a chosen cycle onward, it can inject a prescribed stream `r_t` in place of the live mismatch, and it can scale the comparator term by a gain *k*.

Only the injected term changes. The forward model still learns from the real observation, and salience still uses the real prediction error. Two properties are unit-tested:
- Replaying a run's own recorded stream reproduces that run bit for bit.
- A replay that starts at the analysis window leaves every earlier cycle identical to the live run.

So every condition shares its history with its live reference up to cycle 2,000, and differs only in what the comparator injects while persistence is measured (cycles 2,001–6,000).

### 2.2 Studies

| study | networks | conditions | primary tests |
|---|---|---|---|
| **G** transplant | 48 new (10000–10047), 4 new worlds | master: live, silent, own stream **desynchronized** (circular shift by half the window: identical values, amplitude, waveform and spectrum), own stream **phase-randomized** (multivariate Fourier surrogate), **twin's** stream, twin's stream **rescaled** per channel to the master's mean and SD · twin: live, silent, **master's** stream | G1 necessary: master live > master given twin's stream · G2 sufficient: twin given master's stream > twin live · G3 contingency: master live > master desynchronized · G4 amplitude: master given rescaled twin stream > master given twin stream |
| **I** near-full authorship | 48 new (11000–11047), 4 new worlds | p ∈ {0.75, 0.90, 0.95, 0.99, 1} in a live world | I1: p = 1 > p = 0.95 · I2: p = 1 > p = 0.99 · I3: own-action prediction error higher at 0.95 than at 1 · I4: within-network correlation of persistence and prediction error across levels < 0 |
| **J** gain | 24 new (12000–12023), 2 new worlds | master and twin at k ∈ {0.5, 1, 2} | J1: authorship effect at k = 0.5 > 0 · J2: effect at k = 2 > effect at k = 0.5 |

Decision rule for G, fixed in advance:
- **amplitude account** if G1, G2 and G4 are significant, G3 is not, and G3 is statistically equivalent to zero;
- **contingency account** if G1 and G3 are significant;
- otherwise undetermined.

### 2.3 Statistics

The tests are those of v4 and v5: one-sided paired sign-flip tests, Holm correction within each study, and bootstrap CIs and d_z. v6 adds **equivalence tests** (TOST; Lakens 2017) with a preregistered smallest effect size of interest of 0.04 nats, about a third of the authorship effect in v4 (0.140) and in its replication (0.120). A null can be claimed only when an equivalence test supports it.

### 2.4 Process

1. The hypotheses, code and decision rule were committed and pushed before any v6 data (`e7da0f1`).
2. A technical pilot ran on six development networks already examined in v4. It found no software faults, its estimates are recorded in the preregistration, and nothing was changed.
3. The v6 preregistration and all v4, v5 and v6 sources were hashed and locked, and the lock was pushed (`88b10c2`, 15:54 UTC) before the confirmatory run.
4. The runner labels output CONFIRMATORY only if the lock verifies. Runs are stored under random codes with a separate unblinding key.

Two analyses were added after the data were seen and are labelled exploratory: the re-reading of v5 nulls (Section 4.1) and the meta-analysis (Section 4.2). The meta-analysis sample list was written before the Study J results were available.

## 3. Results

All numbers come from `results/v6/results_v6.json`, produced under the verified v6 lock (status CONFIRMATORY). Full tables are in `results/v6/SUMMARY_v6.md`.

![Figure 6](../figures/ghost_v6_figure_6_transplant.png)

### 3.1 Study G: prediction-error transplant

The positive control passed: the authorship effect appeared in this third independent sample (+0.135 nats, d_z = 1.10).

| | mean diff [95% CI] | d_z [95% CI] | p (Holm) |
|---|---|---|---|
| G1 PE content necessary | +0.124 [0.093, 0.160] | 1.02 [0.78, 1.72] | < 0.001 |
| G2 PE content sufficient | +0.115 [0.086, 0.151] | 0.99 [0.80, 1.72] | < 0.001 |
| G3 contingency matters | +0.054 [0.031, 0.078] | 0.64 [0.39, 0.97] | < 0.001 |
| G4 amplitude matters | +0.038 [0.029, 0.047] | 1.19 [0.84, 1.71] | < 0.001 |

**Preregistered decision: contingency account.** G3 is significant, and its 90% CI [0.035, 0.075] extends well past the +0.04 equivalence bound, so it is not equivalent to zero. The amplitude account's key prediction, that desynchronizing the author's own stream would change nothing, failed. The rule's contingency branch does not require amplitude to be irrelevant, and it is not: G4 is significant.

Where each condition lands between the twin (0) and the master (1):

| condition | position [95% CI] | injected RMS |
|---|---|---|
| twin, its own live error | 0 | 0.248 |
| master, given the twin's stream | 0.08 [−0.02, 0.19] | 0.248 |
| master, twin's stream rescaled to master amplitude | 0.36 [0.23, 0.52] | 0.193 |
| master, own stream phase-randomized | 0.54 [0.33, 0.73] | 0.190 |
| master, own stream desynchronized | 0.60 [0.44, 0.75] | 0.191 |
| twin, given the master's stream | 0.85 [0.68, 1.10] | 0.191 |
| master, its own live error | 1 | 0.191 |
| master, comparator silent | 3.55 [2.74, 4.61] | 0 |
| twin, comparator silent | 3.66 [2.80, 4.85] | 0 |

**A descriptive decomposition** (not a preregistered test; it depends on the order of substitution). Starting from the author given the non-author's stream (0.08):
- matching the amplitude adds 0.28 (to 0.36);
- replacing the temporal and spectral structure with the author's own adds 0.24 (to the desynchronized own stream, 0.60);
- restoring synchrony with the network's own state adds the last 0.40 (to 1).

Phase-randomizing, which keeps only linear structure, is indistinguishable from desynchronizing (0.54 vs 0.60, p = 0.11), so non-Gaussian structure in the stream adds nothing detectable.

**Silence beats both.** Without comparator input, persistence is far higher than in either live agent: 1.46 in the master and 1.48 in the twin, against 1.12 and 0.98. The comparator's input as a whole perturbs the slow mode, and authorship limits the damage. The G1 contrast also holds in the comparator's other target population, association (d_z = 0.79). As a secondary result, the master-minus-twin Ψ difference was significant in this sample (d_z = 0.55, p < 0.001).

### 3.2 Study I: near-full authorship

The manipulation hit its targets: intention/outcome agreement was 0.789, 0.915, 0.958, 0.992 and 1.000 (expected 0.786, 0.914, 0.957, 0.991, 1.000).

| | mean diff [95% CI] | d_z | p (Holm) |
|---|---|---|---|
| I1 5% foreign actions reduce persistence | +0.034 [0.024, 0.046] | 0.83 | < 0.001 |
| I2 1% foreign actions reduce persistence | +0.003 [−0.005, 0.013] | 0.09 | 0.29 (not supported) |
| I3 foreign actions raise own-action prediction error | +0.0025 [0.0022, 0.0028] | 2.39 | < 0.001 |
| I4 persistence tracks prediction error (within-network Fisher z) | −1.65 [−1.83, −1.47] | −2.55 | < 0.001 |

Relative to full authorship, persistence was −0.088, −0.053, −0.034, −0.003 and 0 nats at p = 0.75, 0.90, 0.95, 0.99 and 1. The prediction-error RMS fell monotonically across the same levels: 0.232, 0.214, 0.207, 0.2015, 0.2001.

The curve rises steadily from 75% to 99% authorship and is flat from 99% to 100%. Together with v5's Study B (flat from 0% to 75%), the dose-response has a floor below about 75% authorship and saturates near 99%. v5's "threshold at full authorship" came from a grid with nothing between 0.75 and 1.

I3 identifies one route: a few percent of foreign actions contaminate the forward model's training data, so even the agent's own actions are predicted slightly worse (+1.2% RMS at p = 0.95).

### 3.3 Study J: comparator gain

| | mean diff [95% CI] | d_z | p (Holm) |
|---|---|---|---|
| J1 effect at half gain | +0.080 [−0.023, 0.156] | 0.34 | 0.10 (not supported) |
| J2 effect grows with gain | +0.037 [−0.039, 0.144] | 0.16 | 0.31 (not supported) |

Neither hypothesis was supported. Two of the 24 networks (12012 and 12023) developed a near-frozen slow mode in the twin (persistence 2.0–2.6 nats, against about 1.1 typically), producing large negative differences that dominate the mean. Descriptively, the master exceeded the twin in 21, 22 and 23 of 24 networks at gains 0.5, 1 and 2 (median differences +0.13, +0.11, +0.10).

Raising the gain lowered persistence in both master (d_z = −1.28) and twin (d_z = −1.64), consistent with the comparator acting as a perturbation. Whether the authorship effect scales with coupling remains **open**.

### 3.4 All v6 primary tests

Holm-corrected across all ten v6 primary tests, seven remain significant: G1–G4, I1, I3 and I4. I2, J1 and J2 are not significant.

## 4. Exploratory re-analyses

### 4.1 v5's null results, re-read

v5 reported non-significant tests as "did not replicate" or "did not move". Here each is re-read with an equivalence test, using bounds of a third of the v4 effect (Ψ ±0.056; persistence ±0.04 nats), and, for the replication, with the small-telescopes test (Simonsohn 2015).

| v5 result | mean diff | 90% CI | evidence of absence? |
|---|---|---|---|
| A:H4 Ψ (replication) | 0.061 | [−0.010, 0.136] | no |
| B3 Ψ slope over authorship | 0.055 | [−0.032, 0.147] | no |
| D Ψ, four architectures | −0.002 to 0.060 | widths 0.12–0.27 | no, in all four |
| E persistence effect, comparator switched off | −0.019 | [−0.056, 0.021] | no (but the upper bound is under a fifth of the effect with the comparator on) |

The replication's Ψ estimate is significantly below v4's (v4's 0.168 lies above the replication's 95% CI). But the replication cannot rule out an effect of size d33 = 0.18, the effect v4 had 33% power to detect (p = 0.58). **None of the v5 nulls is evidence of absence.** "Ψ did not move in any architecture" should read "no architecture showed a detectable Ψ effect".

### 4.2 A living meta-analysis

Single-sample verdicts are noisy. This analysis pools every independent sample that ran the default master-vs-twin contrast, using random effects (DerSimonian & Laird 1986): v4 confirmatory (48 networks), v5 replication (48), v5 F standard wiring (24), v6 G (48) and v6 J at gain 1 (24). Networks are never reused across samples.

| | pooled master − twin [95% CI] | I² | 95% prediction interval |
|---|---|---|---|
| self persistence (nats) | +0.134 [0.115, 0.153] | 0.00 | [0.104, 0.164] |
| Ψ | +0.129 [0.077, 0.181] | 0.20 | [0.011, 0.247] |

The persistence effect is strikingly consistent across samples. The Ψ effect is real on average but smaller and more variable: per-sample d_z was 0.59, 0.20, 0.21, 0.55 and 0.35. The preregistered replication's miss is therefore best read as sampling variation around a modest effect, not as proof that v4's Ψ result was a fluke. The preregistered verdicts stand as reported: level 4 in the v4 sample, level 3 in the replication. But the claim itself moves from "not replicated" to **revised: modest and variable**.

A new preregistered test of Ψ would need about 66 networks per sample for 90% power at the pooled d_z of 0.36.

### 4.3 The claims ledger

`claims/claims.json` records every claim the project has made, its status, and for each quoted number the results file and JSON pointer it comes from. `tools/claims.py` checks that the data round to every stated value and renders the README's evidence table. CI fails if either drifts.

On its first run, it found that the v5 report had rounded the replication's blind-discrimination AUC (0.7947) to 0.80; the correct value, 0.79, is now used. Retracted and revised claims keep their entries.

## 5. Discussion

### 5.1 What the effect is

The most economical description of the whole v4–v6 programme is now mechanistic:

> The comparator injects prediction errors into its target population, and those errors perturb the population's slowest collective mode. When the agent authors its own actions, its errors are (i) smaller, (ii) spectrally gentler and (iii) in step with its own state. Each of these reduces the perturbation.

This is a dynamical analogue of **sensory attenuation**: self-produced consequences are predicted, so they perturb the internal model less, as in the comparator account of why self-produced tickle is attenuated (Blakemore, Wolpert & Frith 1998). Here the attenuation is not built in. It emerges from the comparator loop, and it is measurable as the stability of the target population's slow dynamics.

### 5.2 What "contingency" might be

The live error is `observation − f(state, intention)`. Part of it therefore depends on the network's own current state, so the comparator is also a feedback loop through the forward model. Desynchronizing the stream cuts that loop and turns the same values into external input. The 40% loss under desynchronization may be the loss of this feedback term rather than of anything "informational". v6 cannot tell these apart. An intervention that injects only the state-dependent term `−W_cmp·f(state, intention)` could.

One observation does not yet fit a simple story:
- A twin given the author's stream reaches 0.85.
- An author given its own desynchronized stream reaches only 0.60.

Both receive author-sized errors out of step with their state. One possibility is that synchrony helps only when the errors come from accurate self-prediction, so cutting the twin's own feedback loop costs it little. This is a hypothesis for a future preregistration, not a finding.

### 5.3 Limitations

- The same analyst ran every study. Locks and pushes make the order auditable, but independent replication remains the most important missing step (`docs/HOW_TO_REVIEW_OR_REPLICATE.md`).
- The persistence metric, Gaussian I(V_t; V_t+1) = −½ log(1 − ρ²), is unbounded as ρ → 1 and therefore heavy-tailed. Study J's inconclusive means come from two such networks. A bounded or rank-based variant should be preregistered next to it.
- The decomposition in Section 3.1 is descriptive and order-dependent.
- Studies J and the meta-analysis mix sample sizes. The meta-analysis is exploratory.
- All results concern one model family and its labelled populations.

### 5.4 Next

1. Separate the comparator's feedback term from its information content (Section 5.2).
2. Preregister a Ψ study sized for the pooled effect (about 66 networks per sample) and a robust persistence metric.
3. Rerun Study J with the robust metric and more networks.
4. Independent external replication with the locked code.

## References (additional to the v4 and v5 papers)

- Blakemore, S.-J., Wolpert, D. M., & Frith, C. D. (1998). Central cancellation of self-produced tickle sensation. *Nature Neuroscience* 1, 635–640.
- DerSimonian, R., & Laird, N. (1986). Meta-analysis in clinical trials. *Controlled Clinical Trials* 7, 177–188.
- Lakens, D. (2017). Equivalence tests: a practical primer for t tests, correlations, and meta-analyses. *Social Psychological and Personality Science* 8, 355–362.
- Simonsohn, U. (2015). Small telescopes: detectability and the evaluation of replication results. *Psychological Science* 26, 559–569.

## Data, code and preregistration

- Hypotheses before data: commit `e7da0f1`. Lock: `prereg/PREREGISTRATION_v6.lock.json` (locked 2026-09-27T15:54:13Z, commit `88b10c2`, pushed before the confirmatory run). Results: commit `0d4a521`.
- Code: `src/ghost_v6/` (entry point `src/ghost_in_the_machine_v6.py`), building on the frozen `src/ghost_v4/` and `src/ghost_v5/`. Exploratory analyses: `src/ghost_v6/posthoc_v5.py` and `src/ghost_v6/meta.py`.
- Results: `results/v6/results_v6.json`, `results/v6/SUMMARY_v6.md`, coded runs in `results/v6/{G,I,J}/`, the technical pilot in `results/v6_pilot/`.
- Reproduce: run the `run --study all`, `posthoc`, `analyze` and `report` commands of `src/ghost_in_the_machine_v6.py` (about 10 minutes on 4 cores).
- Claims ledger: `claims/claims.json`, `docs/CLAIMS.md`; `python tools/claims.py check`.
