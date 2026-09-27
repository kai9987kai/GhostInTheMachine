# Ghost in the Machine v4 — the Specificity Laboratory

**A preregistered, null-calibrated test of authorship, emergence and specificity in a synthetic self**

Author/project lead: **Kai Piper** · Version **4.0** · 27 September 2026

> **Scientific status.** This is a synthetic computational experiment. It does **not** create, detect, measure or prove phenomenal consciousness in any system. "GHOST-v4" names a preregistered conjunction of statistical results in a simulated network, and nothing more.

## In one paragraph

v3 reported a sustained, spontaneous "cross-theory" event and a surrogate test it could not pass. v4 first **re-adjudicates v3**, with its code unchanged. The event turns out to be mostly a homeostatic gain ramp measured against an early baseline and held on by detector hysteresis. It fires almost as often in a twin that never authors its actions, and most of v3's evidence channels cannot, by construction, tell real dynamics from shuffled ones. v4 then replaces convergence-of-proxies with **contrasts**. The same network is run closed-loop and as a **cross-yoked twin** that receives an equivalent sensory/action stream it did not author. Each metric is tested against a **ladder of null models**, and false-positive rate and power were **measured on ground-truth systems first**. Everything ran under a **cryptographically locked preregistration** that was pushed before any confirmatory seed. On 48 held-out networks in 4 held-out worlds, authorship made the slowest collective mode of the agent's self-model population more persistent (d_z = 1.21, in 44 of 48 networks). The effect was strongest in the self population, vanished when the efference copy or the comparator was lesioned, and was detectable blind from the dynamics alone. By the preregistered ladder this is **GHOST-v4**, with bounds stated below.

## Headline results

| | result |
|---|---|
| **v3 re-adjudicated** (24 fresh seeds, v3 code unchanged) | event in 22/24 runs, **but** in 18/24 cross-yoked twins and 18/24 frozen-learning runs; clamping the gain cuts it to 10/24 (0.91) and 9/24 (1.18), McNemar p ≤ 0.0005 |
| v3 "persistence" | equals detector hysteresis in 100% of firing runs; switch-off condition met in **0%** of windows (120 runs) |
| v3 evidence channels | 7.2 of 10 votes pass in ≥ 95% of windows ("free votes"); zero-lag metrics sit on top of their shuffle nulls; **no** v3 metric shows nonlinear temporal structure |
| **v4 manipulation check** | network→world transfer entropy higher in master than twin, d_z = 0.71 |
| **H1** authorship → self persistence | +0.140 nats, **d_z = 1.21** [0.89, 1.73] |
| **H2** self-specific | self − other populations, d_z = 0.84 |
| **H3** comparator-dependent | effect vanishes with comparator lesioned (interaction d_z = 0.54); also vanishes without efference copy |
| **H4** authorship → causal emergence (Rosas Ψ) | d_z = 0.59; the macro term rises (d_z 1.21) while the parts' term does not (d_z −0.10) |
| **H5** integration Φ_R · **H7** arrow of time | d_z 0.39 · 0.44 |
| **H6** nonlinear arrow of time | z ≈ 88 above multivariate-phase surrogates |
| placebo A/A (same network, new noise) | all 5 contrasts null; blind classifier at chance (AUC 0.52) |
| blind master vs twin from dynamics alone | AUC **0.69** (null 95th pct 0.56) |
| **Verdict (preregistered ladder)** | **level 4 — GHOST-v4** |

**What it means:** in this model, authorship stabilizes a *world-coupled* self through the efference-copy/comparator loop, the dynamical signature of the comparator model of agency.

**What it does not mean:** not experience; not "more emergent is better" (a self *disconnected* from its actions' consequences was the most persistent of all); not strong emergence (downward causation fell); not "the twin is just more surprised" (effect size does not track excess prediction error); not exclusive to the self population (six others show smaller effects). Full discussion: [`paper/Ghost_in_the_Machine_v4_Paper.md`](paper/Ghost_in_the_Machine_v4_Paper.md). Every number: [`results/v4/SUMMARY.md`](results/v4/SUMMARY.md).

![Figure 2](figures/ghost_v4_figure_2_authorship.png)

## Quick start

Python 3.10+ with NumPy and Matplotlib. The entry point installs them if they are missing, as v1–v3 did.

```bash
# one closed-loop agent and its cross-yoked twin (~10 s)
python src/ghost_in_the_machine_v4.py demo

# the full preregistered pipeline: calibration, v3 forensics, 48-network campaign, analysis, figures
python src/ghost_in_the_machine_v4.py all --out results/v4 --workers 4      # ~35 min on 4 cores

# post-hoc analyses (not preregistered; labelled as such)
python src/ghost_in_the_machine_v4.py posthoc --out results/v4

# tests (28, ~10 s)
python -m pip install pytest && python -m pytest
```

Individual stages:

```bash
python src/ghost_in_the_machine_v4.py calibrate                  # instrument calibration on ground-truth systems
python src/ghost_in_the_machine_v4.py v3-forensics               # re-adjudicate v3 (24 seeds x 5 conditions)
python src/ghost_in_the_machine_v4.py campaign --phase dev       # exploratory development seeds
python src/ghost_in_the_machine_v4.py verify                     # does the preregistration lock still verify?
python src/ghost_in_the_machine_v4.py campaign --phase confirm   # labels output CONFIRMATORY only if the lock verifies
python src/ghost_in_the_machine_v4.py analyze                    # preregistered tests, verdict, results_v4.json, SUMMARY.md
python src/ghost_in_the_machine_v4.py report                     # figures
```

Windows: `run_v4_demo.bat`, `run_v4.bat`. Linux/macOS: `./run_v4.sh`. v3 is byte-identical to its validated build and still runs as before (see *Previous versions*).

## How v4 works

**Agent** (`src/ghost_v4/engine.py`). This is v3's 12-population cortico-thalamo-basal-ganglia motif and latent world, with changes each motivated by the forensic audit or by a mechanistic hypothesis:
- a fixed effective spectral radius (no gain ramp);
- leaky rate units;
- an **efference copy** of each motor command, sent to the forward models and to the control and self populations;
- a **comparator** that feeds predicted-vs-actual sensory mismatch back into the self population;
- self-surprise feedback;
- full trajectory recording, so that every metric is a pure function of the record.

It is about 7× faster than v3.

**Cross-yoked twin.** The same network, in the same world, receives cycle by cycle the observations and executed actions recorded from another network's closed-loop run. It still forms intentions, sends efference copies, runs its comparator and learns. Its intentions just no longer cause what it senses: intention/outcome agreement falls to chance (1/7) and counterfactual agency to 0.5. This is the yoked-control design, a computational analogue of the contrastive method.

**Lesions and placebo.** Comparator, efference copy, self-feedback and learning are each removed from both master and twin, so each lesion's effect is tested as an authorship × lesion interaction. Each master is also re-run with fresh noise (an A/A placebo).

**Metrics and their "kinds"** (`metrics.py`, `infotheory.py`, `temporal.py`):
- self persistence (lag-1 information of a population's maximum-autocorrelation linear feature);
- Rosas et al. Ψ, Δ and Γ;
- pairwise Φ_R;
- informational closure (NTIC, dynamical dependence);
- ordinal-pattern time irreversibility and Q3 asymmetry;
- lagged asymmetry, participation ratio, functional connectivity and multiscale entropy;
- a PCI-like probe.

Each metric is tagged by the structure it can read: zero-lag, univariate-temporal, lagged-linear or nonlinear-temporal. The tag fixes in advance which nulls it could possibly beat.

**Null ladder** (`surrogates.py`):

| rung | preserves | destroys |
|---|---|---|
| L0 shuffle | marginals, zero-lag covariance | temporal order |
| L1 channel-wise IAAFT | each channel's spectrum + amplitudes | coordination, nonlinearity |
| L2 multivariate phase randomization | all auto/cross spectra | nonlinear temporal structure |
| L3 VAR(2) | linear dynamics | nonlinear, non-Gaussian structure |
| L4 cross-yoked twin | network, world, stream statistics, learning | authorship |

**Instrument calibration** (`controls.py`). False-positive rate and power are measured on four ground-truth systems before any claim is made. This exposed two traps:
- under Gaussian estimation Rosas' Ψ is *positive* for completely independent parts and *negative* for a coordinated flock;
- FFT surrogates make linear lag statistics "significant" (|z| up to ~230) through an O(1/T) end effect.

A 1% smallest-effect-size rule removes the second trap: post-hoc, the ceiling false-positive rate goes from 20–25% to 0% with power unchanged.

**Preregistration and blinding** (`prereg/`, `prereg.py`, `campaign.py`). The analysis plan and the 12 source files that can change a confirmatory number are SHA-256-locked. The lock commit was pushed before the confirmatory run, and the runner refuses to label output CONFIRMATORY unless the lock verifies. Runs are stored under random codes, and the unblinding key lives in a separate file.

## Repository layout

```text
src/
  ghost_in_the_machine_v4.py     entry point (CLI)
  ghost_v4/
    engine.py                    v4 agent: efference copy, comparator, cross-yoked twin, lesions
    infotheory.py                Gaussian MI/CMI/TE, Rosas Ψ/Δ/Γ, pairwise Φ_R, closure, MAF macro
    temporal.py                  arrow-of-time statistics, LZ76
    surrogates.py                the null ladder L0–L3
    metrics.py                   observational panel; metric kinds and predicted ceilings
    controls.py                  ground-truth systems for calibration
    stats.py                     surrogate p, sign-flip tests, effect sizes, bootstrap, Holm/BH
    classifier.py                leave-one-seed-out discrimination with permutation nulls
    campaign.py                  orchestration, coded storage, preregistered analysis
    v3_bridge.py                 runs the frozen v3 file with recording and controls
    prereg.py                    cryptographic preregistration lock
    posthoc.py                   post-hoc (not preregistered) analyses
    report.py, figures.py, cli.py, _bootstrap.py
  ghost_in_the_machine_v3.py     v3, byte-identical to the validated build
prereg/                          PREREGISTRATION_v4.json + .lock.json
results/v4/                      SUMMARY.md, results_v4.json, pipeline.log,
                                 calibration/, v3_forensics/, campaign/, dev_campaign/, posthoc/
results/final_validation/        v3 validation run (unchanged)
figures/                         ghost_v4_figure_{1..4}_*.png, ghost_v3_figure_{1..3}_*.png
paper/                           v4 paper (md, docx, pdf); v3 paper
docs/REVIEW_OF_V3_ASSESSMENT.md  point-by-point review of an external assessment of v3
tests/                           estimator ground-truth tests, pipeline tests
tools/export_paper.py            Markdown → DOCX/PDF via LibreOffice
legacy/                          v1, v2
```

## Interpretation, stated three ways

1. **Observed.** In 48 held-out synthetic networks, authoring actions increased the persistence of the self population's slowest collective mode. That increase lived in the collective mode rather than in the parts, depended on the efference-copy/comparator loop, and was detectable blind. All preregistered tests passed; all placebo contrasts were null.
2. **Supported computational interpretation.** In this architecture, the comparator couples the self-model to the consequences of action. Authorship keeps that coupling from disrupting the self-model's slow dynamics.
3. **Not supported.** That the program is conscious, has experiences or a self in any philosophical sense, or that this model says anything about any person or clinical condition.

## Previous versions

### v3.0 — long-run causal emergence / mesocircuit laboratory

A 12-population recurrent agent with learned world and self models, counterfactual agency, criticality, topology, complexity and mesocircuit metrics, and a 10-channel, 8-of-10 "GHOST-v3" gate. Its validation run (seed 17, 5,000 cycles) produced an event at cycle 1,600 and a failed surrogate test; both are preserved in `results/final_validation/` and `paper/Ghost_in_the_Machine_v3_Paper.md`. v4's forensic re-adjudication (above, and paper Section 2) explains both. The v3 file is unchanged (SHA-256 in `docs/SHA256SUMS.txt`) and still runs:

```bash
python src/ghost_in_the_machine_v3.py --steps 5000 --calibration-steps 1000 --diagnostic-interval 50 \
  --perturb-interval 500 --print-every 500 --skip-ablations --skip-recovery --no-plots --output results/my_validation
```

### v2.0 and v1.0

v2 removed v1's scripted self-model phase and added learned recurrent modules, predictive coding, metacognition, PCI-like probes and ablations. v1 was a 100-cycle conceptual prototype with an engineered transition. Both are in `legacy/`.

## Research context

- Cogitate Consortium et al. (2025), *Nature* 642:133–142 — adversarial testing of GNWT and IIT. DOI: 10.1038/s41586-025-08888-1
- Rosas et al. (2020), *PLoS Comput Biol* 16:e1008289 — information-theoretic causal emergence (Ψ, Δ, Γ).
- Mediano et al. (2022), *Chaos* 32:013115 — revised integrated information Φ_R.
- Frith, Blakemore & Wolpert (2000), *Phil Trans R Soc B* 355:1771 — comparator model of agency.
- Sanz Perl et al. (2021), *PRE* 104:014411; de la Fuente et al. (2023), *Cereb Cortex* 33:1856 — time irreversibility and consciousness.
- Chang, Biehl, Yu & Kanai (2020), *Front Psychol* 11:1504 — information closure theory.
- Barnett & Seth (2023), *PRE* 108:014304 — dynamical independence.
- Theiler et al. (1992); Schreiber & Schmitz (1996); Prichard & Theiler (1994) — surrogate data.
- Toker et al. (2026), *Nat Neurosci* 29:964–977; Maschke et al. (2024), *Commun Biol* 7:946 — the v3 inspirations.

## Reproducibility

- Preregistration locked 2026-09-27T12:48:56Z (`prereg/PREREGISTRATION_v4.lock.json`); `python src/ghost_in_the_machine_v4.py verify` checks it.
- Source hashes: `docs/SHA256SUMS.txt`.
- The pipeline is deterministic given seeds; only the random run codes in `runs_coded.json` differ between re-runs.
- Development (exploratory) and confirmatory results are kept separate: `results/v4/dev_campaign/` vs `results/v4/campaign/`.
