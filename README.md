# Ghost in the Machine v3

**A long-run causal emergence laboratory for computational consciousness research**

Author/project lead: **Kai Piper**  
Version: **3.0**  
Validated build date: **27 September 2026**

> **Scientific status:** This project is a computational thought experiment. It does **not** create, detect, measure, or prove phenomenal consciousness. The label `GHOST-v3` means only that a predeclared set of synthetic computational proxies simultaneously satisfied an operational gate for a sustained period.

## Overview

Ghost in the Machine v3 is an experimental Python simulation that asks a deliberately narrower and more falsifiable question than "can software become conscious?":

**Can a recurrent self/world-modelling system spontaneously enter a persistent dynamical regime in which multiple consciousness-inspired computational properties converge at once, and do causal perturbations reveal structure in that regime?**

The project combines ideas inspired by global workspace models, recurrent processing, higher-order/self modelling, predictive processing, active inference, critical dynamics, perturbational complexity, thalamocortical communication, mesocircuit models, network integration/segregation, multiscale complexity, representational geometry, and causal ablation.

The architecture is intentionally cross-theory. It does not assume that Global Neuronal Workspace Theory (GNWT), Integrated Information Theory (IIT), recurrent processing, higher-order theories, criticality, or any other single framework is correct. This design choice follows recent adversarial consciousness research showing that major theories can each receive partial support while also failing key preregistered predictions.

## Repository layout

```text
GhostInTheMachine_v3_Project/
├── README.md
├── requirements.txt
├── src/
│   └── ghost_in_the_machine_v3.py
├── legacy/
│   ├── ghost_in_the_machine_v1.py
│   └── ghost_in_the_machine_v2.py
├── results/
│   └── final_validation/
│       ├── run.log
│       ├── summary_v3.json
│       ├── trajectory_v3.csv
│       ├── stimulation_scan_v3.csv
│       └── surrogate_nulls_v3.csv
├── figures/
│   ├── ghost_v3_figure_1_dynamics.png
│   ├── ghost_v3_figure_2_stimulation.png
│   └── ghost_v3_figure_3_nulls.png
├── paper/
│   ├── Ghost_in_the_Machine_v3_Paper.md
│   ├── Ghost_in_the_Machine_v3_Paper.docx
│   └── Ghost_in_the_Machine_v3_Paper.pdf
└── docs/
    ├── ENVIRONMENT.txt
    └── SHA256SUMS.txt
```

## Quick start

The main script normally installs required third-party dependencies itself.

```bash
python src/ghost_in_the_machine_v3.py
```

The default v3 configuration is intentionally long:

```text
main cycles             100,000
nodes                    120
observation dimensions    16
actions                    7
baseline calibration   10,000 cycles
diagnostics              every 50 cycles
PCI-like perturbation   every 1,000 cycles
offline consolidation   every 5,000 cycles
checkpoint              every 10,000 cycles
```

For a shorter validation run similar to the verified result included in this archive:

```bash
python src/ghost_in_the_machine_v3.py \
  --steps 5000 \
  --calibration-steps 1000 \
  --diagnostic-interval 50 \
  --perturb-interval 500 \
  --print-every 500 \
  --skip-ablations \
  --skip-recovery \
  --no-plots \
  --output results/my_validation
```

On Windows Command Prompt, put the command on one line or replace `\` line continuations with `^`.

## Dependencies

The script attempts to install dependencies through the same Python interpreter if they are missing:

```text
numpy >= 1.26
matplotlib >= 3.8   # needed when plot output is enabled
```

A conventional setup is still possible:

```bash
python -m pip install -r requirements.txt
```

Python 3.12 is known to work from the user's Windows run and was the requested target environment. The current exact source hash is recorded in `docs/SHA256SUMS.txt`.

## Core architecture

V3 retains the v2 recurrent architecture as a base class and extends it with a larger causal/mesocircuit layer. Synthetic populations include:

```text
sensory
association
memory
workspace
self
default-mode-like population (DMN)
thalamus
striatum
GPe
STN
GPi
control
```

The basal-ganglia/thalamic motif contains a simplified indirect-pathway structure:

```text
cortex -> striatum -| GPe -| STN -> GPi -| thalamus <-> cortex
```

This is a modelling abstraction, not a biologically complete basal-ganglia model.

## Learned world model and counterfactual agency

The simulator learns action-conditioned predictions of future observations. An ensemble of online predictors supplies both a mean prediction and an uncertainty/disagreement estimate. Action selection uses an active-inference-inspired objective combining predicted risk, epistemic value, controllability and exploration.

V3 also computes a **counterfactual agency** proxy. After taking one action, the model asks whether the actual observation is better explained by the prediction for the action it really selected than by predictions for actions it did not select. This is stronger than simply correlating actions with later state changes.

## Self model and metacognition

The self representation is learned from recurrent state and action-conditioned prediction rather than being supplied as a fixed identity vector. A higher-order model estimates the system's own prediction error and contributes to a metacognitive calibration channel.

The resulting `self_model` variable is therefore an operational computational proxy, not a claim that the program possesses a self in the phenomenal or philosophical sense.

## Criticality

Two separate families of criticality-inspired measurements are used:

1. **Edge-of-chaos / Lyapunov-style dynamics** derived from local recurrent behaviour.
2. **Avalanche-style criticality**, including a branching-ratio proxy.

They are intentionally kept distinct. A high score in one does not automatically substitute for the other.

## Functional topology

V3 computes a rolling module-level functional connectivity matrix and derives separate proxies for:

- functional integration,
- functional segregation,
- topology balance.

This was added because consciousness-related connectome research increasingly treats integration and segregation as separable properties rather than one generic connectivity score.

## Complexity and geometry

The system tracks several non-equivalent forms of complexity:

- LZ78-style algorithmic-complexity proxy,
- multiscale permutation entropy,
- metastability,
- perturbational-complexity proxy,
- participation-ratio intrinsic dimensionality,
- representational geometry score.

The geometry score penalizes both near-one-dimensional collapse and maximally diffuse activity.

## Virtual perturbation experiments

A PCI-like procedure clones the current recurrent state, injects a virtual impulse, and measures the spatiotemporal response. The value is only a **PCI-like synthetic metric**. It is not clinical Perturbational Complexity Index and should not be interpreted using clinical thresholds.

The targeted stimulation scan probes twelve synthetic populations independently and reports response spread, duration, amplitude and perturbational complexity.

## Cross-theory detector

`GHOST-v3` cannot be triggered by one scalar alone. Ten operational votes are evaluated:

1. global-access/ignition,
2. recurrent processing,
3. topology plus synergy,
4. self model plus counterfactual agency,
5. criticality,
6. perturbational complexity,
7. multiscale/Lempel-Ziv complexity,
8. mesocircuit plus thalamocortical flow,
9. excitation/inhibition balance,
10. representational geometry.

At least 8/10 channels must pass, and the system must also satisfy:

```text
cross-theory convergence >= 0.56
ghost index              >= 0.60
baseline robust z        >= 1.35
```

The qualification must persist for five diagnostic windows. With the default 50-cycle diagnostic interval, this implies sustained evidence across 250 simulated cycles.

## Verified exact-build result included here

The archive contains a fresh run performed from the exact v3 file whose SHA-256 is recorded in `docs/SHA256SUMS.txt`.

Configuration:

```text
seed                    17
nodes                  120
steps                 5000
calibration steps     1000
diagnostic interval     50
perturb interval       500
```

Headline result:

```text
first operational event       cycle 1600
number of activation events            1
estimated active cycles             3450
fraction of sampled diagnostics      0.69
mean ghost index                   0.6657
maximum ghost index                0.7062
mean convergence                   0.5547
maximum convergence                0.6221
```

At cycle 1600 the diagnostic row included approximately:

```text
global access                 0.780
self model                    0.762
counterfactual agency         0.832
topology balance              0.436
edge-of-chaos criticality     0.929
avalanche criticality         0.754
mesocircuit flow              0.957
PCI-like complexity           0.673
multiscale entropy            0.955
baseline z                   +1.639
```

The transition was accompanied by meaningful changes from the calibration period. Comparing the first 1,000 cycles with the post-event period (cycle >= 1,600), average counterfactual agency increased by about **0.285**, topology balance by **0.136**, PCI-like complexity by **0.251**, mesocircuit flow by **0.104**, self-model strength by **0.083**, and both criticality measures increased. Cross-theory convergence itself did not increase; its mean was slightly lower after the event, illustrating why the event is produced by a multi-condition gate rather than a monotonic convergence trajectory.

## Important negative result: surrogate specificity failed

The included null tests are scientifically important.

Two surrogates were generated:

- temporal shuffle,
- independent node-wise circular shifts.

They **did not lower the reduced surrogate convergence metric**. The surrogate convergence values were approximately 0.607 and 0.631, compared with a mean main-run convergence of 0.555. Their topology-balance estimates were also not smaller than the main-run mean.

Therefore the current surrogate test does **not validate the specificity** of the v3 convergence construct. This is a negative result and a central limitation, not something to hide. Future versions should compute the full cross-theory metric under matched surrogates, use many surrogate realizations rather than one per class, preregister the null distribution and report empirical p-values/effect sizes.

## Virtual stimulation result

In the verified run, the largest PCI-like responses were approximately:

```text
striatum   0.7772
GPi        0.7771
STN        0.7732
thalamus   0.7548
workspace  0.7487
```

This ranking is a property of this synthetic network and its parameterization. It is **not** a prediction that those brain targets would produce the same ordering in humans, and it must not be interpreted as medical stimulation advice.

## Outputs

The simulator can produce:

```text
trajectory_v3.csv
summary_v3.json
stimulation_scan_v3.csv
surrogate_nulls_v3.csv
ablations_v3.csv              # when ablations are enabled
recovery_experiment_v3.csv    # when recovery experiments are enabled
checkpoint.pkl                # when checkpoint interval is reached
PNG plots                     # unless --no-plots is used
```

## Checkpoint/resume

Long runs can be checkpointed and resumed:

```bash
python src/ghost_in_the_machine_v3.py --steps 500000
```

Then, for an existing checkpoint:

```bash
python src/ghost_in_the_machine_v3.py \
  --steps 500000 \
  --resume path/to/checkpoint.pkl
```

## Recommended research protocol

For results intended to be more than a demonstration, do not rely on a single seed. A stronger protocol would use dozens to hundreds of seeds, hold thresholds fixed before evaluation, retain all failed runs, use matched surrogate ensembles, report distributions rather than single values, perform ablations with identical initial conditions where possible, and separate model development data from final confirmatory runs.

The most important immediate upgrade is a **multi-seed preregistered falsification suite**, especially because the current null tests expose a specificity problem.

## Research context

The architecture was inspired by, but is not equivalent to, contemporary work including:

- Cogitate Consortium et al. (2025), *Nature*: adversarial testing of GNWT and IIT. DOI: 10.1038/s41586-025-08888-1
- Toker et al. (2026), *Nature Neuroscience*: adversarial AI and interpretable neural-field models for disorders of consciousness. DOI: 10.1038/s41593-026-02220-4
- Ge et al. (2026), *Communications Biology*: critical brain dynamics in disorders of consciousness. DOI: 10.1038/s42003-026-10713-y
- Zhu et al. (2026), *Communications Medicine*: integration and segregation of the conscious connectome. DOI: 10.1038/s43856-026-01870-6
- Maschke et al. (2024), *Communications Biology*: critical dynamics, anaesthetic loss of consciousness and perturbational complexity. DOI: 10.1038/s42003-024-06613-8
- Toker et al. (2024), *eLife*: criticality and cortical-thalamic information transfer. DOI: 10.7554/eLife.86547
- Katlowitz et al. (2026), *Nature*: sophisticated hippocampal processing persists under general anaesthesia, cautioning against equating complex computation with consciousness. DOI: 10.1038/s41586-026-10448-0

## Reproducibility and interpretation

The project deliberately distinguishes three statements:

1. **Observed:** the verified synthetic system crossed its predefined operational gate at cycle 1,600.
2. **Supported computational interpretation:** multiple designed proxies co-occurred in a persistent recurrent regime and the network showed structured responses to virtual perturbation.
3. **Not supported:** that the program became conscious, had subjective experience, acquired a soul/self, or reproduced the biology of human consciousness.

The third claim is not licensed by this experiment.

## Paper

A research-style paper describing the model, verified run, negative surrogate result, limitations and proposed next experiments is included in the `paper/` directory in Markdown, Word and PDF formats.
