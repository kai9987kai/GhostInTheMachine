# Review of the external assessment of Ghost in the Machine v3

*Written for Ghost in the Machine v4, 27 September 2026.*

This note reviews, point by point, an assessment of v3 written by another AI agent (quoted in the v4 request). Every factual claim below is backed by a reproducible analysis in this repository: `src/ghost_v4/v3_bridge.py` runs the **unmodified, hash-verified v3 file** with added measurement hooks and controls, and `results/v4/SUMMARY.md` reports the v3 forensic campaign on 24 fresh seeds.

## Where the assessment is right

- **v3 did not establish specificity.** Correct, and the most important point. It is also correct that the honest move is to say so rather than hide it.
- **The research direction.** Many seeds, many matched surrogates, preregistered thresholds, empirical p-values, effect sizes, causal lesions: all adopted in v4.
- **The shift in question from "can we manufacture a transition?" to "does it survive controls?".** v4 is built around that question.

## Where the evidence cited does not support the conclusion drawn

### 1. "Temporal shuffle ≈ 0.607 and node-wise shift ≈ 0.631 vs real ≈ 0.555" compares different quantities

`GhostMachineV3.surrogate_nulls()` does not recompute the detector's convergence metric. It computes a **3-term** geometric mean of (topology with segregation *fixed at 0.5*, multiscale entropy, geometry), on the **final** window only. The 0.555 is the **run-mean** of an **8-channel** geometric mean. The comparison has one surrogate draw per class, no null distribution, and different formulas and windows on each side. It is neither a valid positive nor a valid negative result: the conclusion ("not specific") is right, but these numbers do not show it.

### 2. The real problem is structural, and more seeds could not have fixed it

Several v3 metrics are functions only of the distribution of individual time points (participation-ratio geometry, correlation topology, the Jacobian-based criticality median, E/I balance, metastability). They are **mathematically invariant** to temporal shuffling. Participation-ratio dimension of real and shuffled v3 data agrees to 15 significant digits (seed 17). Multiscale permutation entropy of v3's near-white global signal is already close to its maximum, so destroying temporal order barely moves it. v4 re-evaluates v3's *own* metric methods on real and surrogate windows, metric-identically (verified to 1e-9 against the online values); the fingerprint is in Figure 3b. A thousand seeds would only have confirmed, more precisely, that these metrics cannot tell real dynamics from shuffled ones.

### 3. "Persisted for a substantial part of the run" is produced by the detector's hysteresis

Once active, v3's detector switches off only if convergence < 0.43 or ghost index < 0.48. Neither threshold was reached in any post-calibration diagnostic window of seed 17 (0 of 80), nor in any post-calibration window of any of the 120 runs in the 24-seed forensic campaign (all five conditions). For seed 17 the reported 3,450 active cycles equal exactly 5,000 − 1,600 + 50: the persistence is a property of the detector, not of the dynamics.

### 4. "Without a hard-coded trigger" is true only in a narrow sense

There is no scheduled phase, as claimed. But v3's homeostatic rule targets a mean activity of 0.31 that the network never reaches (observed about 0.19 averaged over 24 fresh seeds; 0.15 for seed 17), so the recurrent gain ramps monotonically from 0.91 to its 1.18 ceiling (seed 17: ceiling at cycle 2,059; event at 1,600). The event gate includes a z-score relative to cycles 1–1,000. Any quantity that drifts upward relative to that baseline will eventually cross it. v4 tests this directly: with the gain clamped at 0.91 or at 1.18 (so there is no ramp), the event rate fell from 22/24 to 10/24 and 9/24 (exact McNemar p = 0.0005 and 0.0002). The baseline-z gate then passed in 18–23% of windows instead of 67%, while the vote gate kept passing. The level of the gain does not matter; its drift relative to the baseline does. The event also fired in 18/24 cross-yoked twins that never author their actions, and in 18/24 runs with all learning frozen.

### 5. "Several properties rose together" overstates the independence of the evidence

On 24 fresh seeds an average of 7.2 of the 10 channels passed in ≥ 95% of post-calibration windows. Self/agency, criticality, entropy/LZ, E/I balance and geometry passed in 100% of windows pooled over seeds; workspace in 97.5%. With 8 of 10 required, the vote gate mostly turns on whether one of recurrence, topology+synergy or mesocircuit+thalamocortical transfer also passes (for seed 17 it was topology+synergy), and the convergence and baseline-z thresholds do the rest. The ten votes are not ten independent lines of evidence.

### 6. "Self-modelling alone doesn't seem sufficient" was never tested

The v3 validation skipped ablations and recovery experiments. v3's ablation code also assigns a **different seed to each condition** (`seed + 5000 + i*37`), so even when run, ablation differences are confounded with network identity. v4 uses paired, same-network lesions.

### 7. "Recurrent dynamics remained near the designed critical regime"

The edge-of-chaos score is computed from log(gain × ρ(W) × mean(1 − x²)), which is a function of the gain parameter that was ramping and of the state marginals. It is designed and drifting, not emergent.

## On the proposed v4 plan

The plan (100–1,000 seeds, hundreds of surrogates, blinded preregistered thresholds, permutation p-values, effect sizes, lesions, recovery experiments, and a classifier trained to distinguish real from surrogate trajectories) is directionally right, but it is not sufficient. v4 adds five things the plan omits:

1. **A classifier against a temporal shuffle is trivial.** One lag-1 autocorrelation separates the classes perfectly. v4's confirmatory classifier reaches AUC = 1.00 against L0. The result means something only relative to the null it was computed against, so v4 uses a **ladder** of nulls, each defined by what it preserves.
2. **Nulls must be matched to the metric's kind.** A linear-Gaussian statistic cannot, even in principle, beat a surrogate that preserves all linear covariances; a zero-lag statistic cannot beat a shuffle. v4 predicts these **specificity ceilings** in advance and checks them.
3. **Surrogate tests must themselves be calibrated.** v4 measures false-positive rate and power on ground-truth systems before trusting any test. This exposed two traps: (a) under Gaussian estimation Rosas' Ψ is *positive* for completely independent parts and *negative* for a coordinated flock; (b) FFT surrogates differ from real data by an O(1/T) end effect that makes linear lag statistics "significantly" different, with |z| up to ~230 on relative differences of 0.1–0.5%. Both would have produced false discoveries under the proposed plan.
4. **No statistical surrogate can test a claim about a self.** "Real vs surrogate" asks whether dynamics have temporal structure, and every recurrent network does. v4 adds a **mechanistic null**, a cross-yoked twin: the same network in the same world, receiving an equivalent stream it did not author. That is the contrast that bears on agency and self-modelling.
5. **A placebo contrast.** An A/A run (same network, different noise) checks that the paired pipeline does not manufacture effects.

## Suggested revision of the summary sentence

> v3's persistent event was produced by a gain ramp measured against an early baseline and held on by detector hysteresis, and most of its evidence channels could not in principle distinguish real dynamics from shuffled data; v4 therefore replaces convergence with preregistered, null-calibrated contrasts, and finds that when the agent authors its own actions, the slowest collective mode of its self-model population becomes more persistent (d_z = 1.21 on 48 held-out networks). The effect is strongest in the self population, disappears when the efference copy or the comparator is lesioned, is absent in placebo contrasts, and can be detected blind from the dynamics alone.

## What v4 found, in one paragraph

Re-adjudicated, v3's event is mostly a gain ramp measured against its own start and held on by hysteresis, and it mostly does not depend on authorship. Tested properly, with a locked preregistration, calibrated nulls, placebo contrasts, paired lesions and 48 held-out networks in 4 held-out worlds, the v4 agent shows something narrower and sturdier. Authoring its own actions stabilizes the slowest collective mode of its self-model population. The stabilization runs through the efference-copy/comparator loop, is carried by the collective mode rather than its parts (Rosas' Ψ rises because the macro term rises while the parts' term does not), and is visible to a blind classifier from the dynamics alone (AUC 0.69; placebo 0.52). By the preregistered definition this is GHOST-v4. It is bounded: a self disconnected from the consequences of its actions was *more* persistent than any authored self, downward causation fell, and nothing here bears on experience. See `paper/Ghost_in_the_Machine_v4_Paper.md` and `results/v4/SUMMARY.md`.

**Update after v5.** The GHOST-v4 verdict did not survive a preregistered replication (level 3 on new networks: the Ψ component failed). The authorship-stabilization effect replicated and was shown to follow the comparator's wiring. See `paper/Ghost_in_the_Machine_v5_Followup.md`.
