# Changelog

## v4.0 - 2026-09-27 — the Specificity Laboratory

v4 changes the question from "do many consciousness-inspired proxies rise together?" to three questions that can each fail: is there a self-level macro-variable whose dynamics depend on the agent **authoring** its actions (A), is that effect **specific** (to the self population, to a mechanism, to structure that survives calibrated nulls) (S), and is it **causally emergent** (E)?

Forensic re-adjudication of v3 (the v3 file is unchanged and hash-verified):
- Bridge that runs v3 with recording, cross-yoked-twin, clamped-gain and frozen-learning hooks; v3's own metric methods re-evaluated on surrogate windows, metric-identical to 1e-9.
- Found: an unreachable homeostatic target drives a monotone gain ramp; 7 of 10 detector votes pass in ≥95% of windows ("free votes"); the switch-off condition is never met, so event persistence equals detector hysteresis; several v3 metrics are exactly invariant to temporal shuffling.
- 24-seed v3 forensic campaign with twin / clamped-gain / frozen controls.

New engine (`src/ghost_v4/engine.py`):
- Fixed effective spectral radius (no gain ramp), leaky rate units.
- Efference copy, comparator (reafference) feedback and self-surprise feedback.
- Cross-yoked twin mode; paired mechanistic lesions; placebo (A/A) replicates.
- Full trajectory recording; ~7x faster than v3.

New measurement science:
- Gaussian information toolkit: MI, CMI, transfer entropy, Rosas et al. Ψ/Δ/Γ, pairwise Φ_R, informational closure (NTIC, dynamical dependence); max-autocorrelation macro-variables.
- Arrow-of-time statistics: ordinal-pattern irreversibility, Q3 asymmetry, lagged cross-correlation asymmetry.
- Four-rung null ladder (shuffle, IAAFT, multivariate phase randomization, VAR) with metric "kinds" and predicted specificity ceilings; SESOI rule for FFT end effects.
- Instrument calibration on ground-truth systems (false-positive rate, power, ceilings).
- Leave-one-seed-out blind discrimination with within-pair permutation nulls.

Research process:
- Cryptographic preregistration (`prereg/`), locked and pushed before confirmatory seeds were run.
- Coded (blinded) run storage with a separate unblinding key.
- Exploratory 12-seed development campaign kept in `results/v4/dev_campaign/`.
- Confirmatory campaign: 48 held-out networks in 4 held-out worlds.
- 28 tests (`pytest`).

Results (see `results/v4/SUMMARY.md` and the v4 paper):
- v3 re-adjudicated on 24 fresh seeds: event rate 22/24, but 18/24 in cross-yoked twins and 18/24 with learning frozen; 10/24 and 9/24 with the gain clamped at 0.91 / 1.18; persistence equals detector hysteresis in every firing run.
- Instrument calibration: 11/13 rows pass; the two failures are the predicted FFT end-effect ceilings, removed post hoc by the 1% SESOI rule.
- Confirmatory campaign (48 held-out networks, 4 held-out worlds): all preregistered tests pass; verdict level 4 (GHOST-v4). Authorship increases the persistence of the self population's slowest collective mode (d_z = 1.21), most strongly in the self population, only with an intact efference-copy/comparator loop; Ψ rises with authorship because the collective term rises while the parts' term does not; placebo contrasts are null.
- Post-hoc module (`src/ghost_v4/posthoc.py`) and paper export tool (`tools/export_paper.py`).

## v3.0 - 2026-09-27

- Expanded to a 100,000-cycle default long-run laboratory.
- Added synthetic sensory, association, memory, workspace, self, DMN, thalamic, striatal, GPe, STN, GPi and control populations.
- Added ensemble world prediction and epistemic uncertainty.
- Added active-inference-inspired action selection and counterfactual agency.
- Added functional integration/segregation and topology balance.
- Added avalanche criticality, multiscale permutation entropy and representational dimensionality.
- Added E/I balance, mesocircuit predictive-flow metrics and change-point detection.
- Added replay/offline consolidation, checkpoint/resume, surrogate nulls and lesion/recovery hooks.
- Upgraded event detector to a 10-channel, 8-of-10 sustained gate plus convergence/index/baseline constraints.
- Exact-build validation packaged with the repository.

## v2.0

- Removed the scripted self-model phase used in v1.
- Added a learned recurrent modular architecture, predictive coding, metacognition, homeostatic criticality, PCI-like probes, stimulation scans, causal ablations and baseline calibration.
- Increased default experiment length to 25,000 cycles.

## v1.0

- Initial 100-cycle theoretical demonstration.
- Implemented recurrent memory, global broadcasting, prediction error, a self-model and a deliberately engineered transition into a self-referential phase.
- Useful as a conceptual prototype, but the transition was intentionally constructed rather than spontaneous.
