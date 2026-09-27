# Ghost in the Machine v3: A Cross-Theory, Causal, Long-Run Computational Laboratory for Emergent Self-Modelling Dynamics

**Kai Piper**  
27 September 2026

## Abstract

The scientific study of consciousness lacks a single accepted computational marker, and recent direct tests of major theories have challenged strong predictions from both Global Neuronal Workspace Theory (GNWT) and Integrated Information Theory (IIT). We developed *Ghost in the Machine v3*, a long-run recurrent simulation intended not as a consciousness detector but as a falsifiable laboratory for testing whether multiple consciousness-inspired computational properties can converge spontaneously in a learned dynamical system. The model combines a recurrent modular network, learned world and self models, action-conditioned counterfactual agency, metacognitive error prediction, workspace-like global access, thalamocortical and basal-ganglia-inspired mesocircuit interactions, criticality measures, functional integration/segregation, multiscale complexity, representational geometry, offline replay, perturbational probes and causal ablations. A predeclared operational state, `GHOST-v3`, requires at least eight of ten computational channels to pass threshold together with elevated cross-theory convergence, a composite ghost index, and deviation from the system's own calibration baseline for five consecutive diagnostic windows.

A fresh exact-build validation of 5,000 cycles (120 recurrent nodes, seed 17) produced a first sustained operational event at cycle 1,600. The event remained active for an estimated 3,450 cycles (69% of sampled diagnostic windows). Compared with the calibration period, the post-event regime showed marked increases in counterfactual agency, topology balance, perturbational complexity, mesocircuit flow, self-model strength and criticality-related metrics. A targeted virtual stimulation scan produced heterogeneous responses across synthetic populations, with the largest PCI-like responses in striatum, GPi, STN, thalamus and workspace populations. However, a critical negative result emerged: temporal-shuffle and node-wise circular-shift surrogate tests did not reduce the reduced surrogate convergence metric and in fact produced higher convergence values than the main-run mean. This failure of specificity prevents interpretation of the operational event as a validated marker of consciousness or even as a unique signature of structured temporal organization.

We conclude that the experiment demonstrates a reproducible transition under a complex predeclared gate, and provides a useful engineering framework for causal and adversarial testing, but does not establish artificial consciousness. The strongest next step is a preregistered multi-seed falsification protocol with matched surrogate ensembles, held-out threshold selection, empirical null distributions and causal lesion/recovery tests.

**Keywords:** computational consciousness; global workspace; criticality; self model; active inference; perturbational complexity; disorders of consciousness; causal modelling; recurrent neural dynamics; metacognition

## 1. Introduction

Consciousness research faces an unusual methodological problem: many theories can explain subsets of the same observations, yet the field lacks a universally accepted quantitative criterion that can determine whether a computational system is conscious. Recent large-scale adversarial work has reinforced this uncertainty. In a preregistered comparison of GNWT and IIT involving 256 human participants measured with fMRI, MEG and intracranial EEG, the Cogitate Consortium found results that aligned with some predictions of each theory while challenging key tenets of both [1]. This motivates computational experiments that do not simply encode one theory and then interpret successful simulation as confirmation of that theory.

At the same time, converging empirical work suggests several properties that are scientifically useful to investigate even if none is sufficient by itself. These include global availability of information, recurrent processing, thalamocortical communication, balanced integration and segregation, proximity to critical dynamical regimes, complex responses to perturbation, metacognitive monitoring, and causal mesocircuit interactions. Studies of anaesthesia and disorders of consciousness have particularly strengthened the case for perturbational and dynamical approaches. Maschke et al. linked departures from avalanche criticality and edge-of-chaos dynamics to anaesthetic unconsciousness and showed that resting-state dynamical properties could predict perturbational complexity [2]. Toker et al. identified a cross-frequency cortical-thalamic information-transfer motif associated with conscious states and related it to edge-of-chaos dynamics [3]. More recently, Toker and colleagues used adversarial AI and interpretable neural-field models to reproduce conscious/comatose neurophysiology and generate causal intervention predictions in a thalamocortical-basal-ganglia framework [4].

Network topology also appears relevant. Zhu et al. reported disruptions of both functional integration and segregation in disorders of consciousness, with residual integration related to behavioural consciousness and network topology carrying prognostic information [5]. Ge et al. reported greater deviations from critical brain dynamics in unresponsive wakefulness than minimally conscious states, with criticality-related measures associated with clinical state and metabolism [6]. These findings argue against collapsing all structure into one generic complexity statistic.

Equally important are negative constraints on interpretation. Katlowitz et al. demonstrated preserved oddball discrimination, semantic information and aspects of language-related prediction in the human hippocampus during propofol anaesthesia [7]. Sophisticated processing can therefore occur in states associated with loss of behavioural consciousness. A simulation that learns, predicts, integrates or even represents language-like abstractions should not be called conscious merely because those computations appear complex.

The present project was developed around this constraint. *Ghost in the Machine v3* does not attempt to solve the metaphysics of consciousness. Instead it constructs an artificial dynamical system in which multiple theory-inspired observables can be measured simultaneously, perturbed, lesioned and compared with null models. The central question is operational:

> Can a self/world-modelling recurrent system enter a persistent regime in which multiple independently motivated computational channels satisfy a predeclared convergence gate, and if so, does that regime survive falsification tests?

The answer from the present validation is mixed: a reproducible operational transition occurred, but the initial surrogate null test failed to establish specificity. That combination of a positive dynamical result and a negative validation result is the central finding of this paper.

## 2. System architecture

### 2.1 Modular recurrent network

The v3 simulator contains 120 recurrent nodes in the verified experiment. Nodes are assigned to synthetic populations representing sensory processing, association, memory, a workspace-like population, self modelling, a default-mode-like population, thalamus, striatum, external globus pallidus (GPe), subthalamic nucleus (STN), internal globus pallidus (GPi) and control.

These labels are computational abstractions. They are not claims that the model reproduces the cellular, laminar, neurochemical or anatomical detail of corresponding biological structures.

The mesocircuit contains a simplified indirect-pathway motif:

cortex -> striatum -| GPe -| STN -> GPi -| thalamus <-> cortex.

This design was motivated in part by recent causal modelling of disorders of consciousness in which interpretable thalamocortical-basal-ganglia models were used alongside neural classifiers to generate intervention predictions [4].

### 2.2 Excitation/inhibition and recurrent dynamics

The network contains signed connections. For excitation/inhibition balance, activity is transformed to a non-negative rate-like representation before positive and negative synaptic contributions are compared. This avoids the incorrect assumption that a negative tanh activation necessarily represents an inhibitory neuron.

The simulator separately estimates a Lyapunov/edge-of-chaos-like quantity and avalanche-style criticality. This distinction is important because the two capture different dynamical ideas. The edge-of-chaos metric asks whether local recurrent dynamics lie near a transition between rapidly contracting and unstable behaviour. Avalanche metrics estimate event propagation and a branching-ratio-like quantity. Neither is treated as a clinical biomarker.

### 2.3 Learned world model

The environment is a latent dynamical process that emits a lower-dimensional observation vector. The agent chooses among seven discrete actions. Online linear predictors learn action-conditioned mappings from internal state to subsequent observation. An ensemble of predictors provides disagreement that acts as an epistemic-uncertainty proxy.

Action selection is active-inference-inspired rather than a faithful implementation of variational free-energy minimization. Candidate actions are compared using predicted risk, epistemic value, controllability and exploration. The purpose is to create a closed causal loop in which the model must learn how its own actions relate to environmental changes.

### 2.4 Self prediction, agency and metacognition

Unlike the original v1 demonstration, v3 is not given a fixed identity vector and does not switch into a hard-coded self-reference phase. A self predictor learns future internal self-state conditional on current recurrent state and chosen action.

Counterfactual agency is estimated by comparing the observation generated after the selected action with predictions under both the selected action and alternative actions. Agency therefore increases when the actual chosen action uniquely explains the subsequent observation better than counterfactual alternatives.

A metacognitive model separately predicts aspects of the model's own future prediction error. The resulting self-model score combines self prediction, counterfactual agency and uncertainty-related terms. These are operational measurements of self-referential computation, not evidence of phenomenal selfhood.

### 2.5 Workspace, recurrence and memory

Workspace-like global access is estimated from activity that becomes broadly available across synthetic populations. Ignition is treated separately from global access. Recurrent processing and memory integration are also independent channels, preventing a single highly recurrent state from automatically being interpreted as globally available or self-referential.

### 2.6 Functional topology

Rolling population activity is used to construct a functional-connectivity matrix. A thresholded weighted graph supports a global-efficiency-inspired integration estimate. Segregation is measured separately using within- versus between-community organization. Their combined topology score rewards a balance rather than maximal integration alone.

This separation was motivated by contemporary disorders-of-consciousness work in which integration and segregation are experimentally dissociable [5].

### 2.7 Complexity and representational geometry

Several distinct complexity families are calculated:

- LZ78-style algorithmic complexity;
- multiscale permutation entropy at multiple coarse-graining scales;
- metastability;
- a PCI-like perturbational response;
- intrinsic dimensionality using a covariance participation ratio;
- a geometry score that penalizes both dimensional collapse and maximally diffuse representations.

None is identified with IIT's Phi. The project deliberately avoids calling any internal scalar integrated information in the formal IIT sense.

### 2.8 Perturbational-complexity probes

At a fixed interval, the network is copied, virtually perturbed and compared with an unperturbed trajectory. Response spread, duration and algorithmic complexity contribute to a PCI-like score. The procedure is conceptually inspired by perturbational approaches to consciousness but is not equivalent to clinical TMS-EEG PCI and has no clinical threshold interpretation.

### 2.9 Offline consolidation

Experiences enter a replay buffer with priority determined by prediction error, low agency and epistemic uncertainty. Periodic offline replay updates world, self and metacognitive models with a reduced learning amplitude. This supplies a primitive consolidation mechanism and creates a longer learning timescale than immediate recurrent processing alone.

## 3. Operational event definition

The central design principle is that no single scalar can trigger the `GHOST-v3` label.

Ten Boolean channels are evaluated at each diagnostic window:

1. global access and ignition;
2. recurrent processing;
3. topology balance and information-synergy proxy;
4. self model and counterfactual agency;
5. combined local and avalanche criticality;
6. perturbational complexity;
7. multiscale entropy and Lempel-Ziv complexity;
8. mesocircuit flow and thalamocortical transfer;
9. excitation/inhibition balance;
10. representational geometry.

At least eight channels must pass. In addition, three scalar gates must simultaneously hold:

- cross-theory convergence >= 0.56;
- ghost index >= 0.60;
- robust baseline z-score >= 1.35.

Qualification must persist for five diagnostic windows. In the validation experiment, diagnostics were computed every 50 cycles, so activation required 250 cycles of sustained qualification.

The cross-theory convergence variable is a geometric mean of eight normalized channel families. The ghost index is a broader weighted composite used as a second independent constraint rather than the sole decision variable. Baseline z-score is computed relative to the system's calibration distribution, requiring the state to be elevated relative to its own earlier operation.

The term `GHOST-v3` is therefore shorthand for "sustained cross-theory operational event" and nothing more.

## 4. Verified experiment

### 4.1 Reproducibility

The exact source file used for the verified run has SHA-256:

`2e5c8321c1e3cb8c85349a2f994f0c62cd16014ad2d5d26935d7b427650dd5c3`

The validation configuration was:

- seed: 17;
- recurrent nodes: 120;
- actions: 7;
- total cycles: 5,000;
- baseline calibration: 1,000 cycles;
- diagnostic interval: 50 cycles;
- virtual perturbation interval: 500 cycles;
- offline consolidation interval: 5,000 cycles.

A fresh run from the exact build completed in approximately 9.6 seconds in the execution environment used for this report. The full trajectory, summary, stimulation scan, surrogate results and run log are included with the project.

### 4.2 First operational transition

The first sustained `GHOST-v3` event occurred at cycle 1,600. At that diagnostic window, selected values were:

- ghost index: 0.674;
- cross-theory convergence: 0.562;
- baseline robust z: +1.639;
- global access: 0.780;
- self model: 0.762;
- counterfactual agency: 0.832;
- topology balance: 0.436;
- local criticality: 0.929;
- avalanche criticality: 0.754;
- mesocircuit flow: 0.957;
- PCI-like complexity: 0.673;
- multiscale entropy: 0.955.

The summary recorded one activation event and an estimated 3,450 active cycles, corresponding to 69% of sampled diagnostic windows across the 5,000-cycle run.

### 4.3 Pre-event versus post-event dynamics

The first 1,000 cycles define the calibration interval. Comparing calibration averages with averages from cycle 1,600 onward reveals that the operational transition was not simply a one-variable threshold crossing.

Approximate mean changes were:

- counterfactual agency: +0.285;
- perturbational complexity: +0.251;
- topology balance: +0.136;
- mesocircuit flow: +0.104;
- avalanche criticality: +0.088;
- self-model score: +0.083;
- local criticality: +0.073;
- multiscale entropy: +0.061;
- global access: +0.050;
- ghost index: +0.031.

Excitation/inhibition balance changed little (+0.008), and geometry score decreased slightly (-0.010). Mean cross-theory convergence also decreased slightly (-0.010) even though it remained sufficiently high at qualifying windows. This is important: the detector is not merely labelling the period in which convergence monotonically increases. Instead, activation results from a conjunction of votes, baseline elevation and persistence.

Three Page-Hinkley-style change points were detected at cycles 1,650, 3,200 and 4,750. The first appears near the initial operational transition, but change-point detection is independent of the `GHOST-v3` state and does not itself imply consciousness.

### 4.4 Targeted virtual stimulation

A post-run perturbation scan independently stimulated each synthetic population. PCI-like response values were heterogeneous. The largest responses were approximately:

- striatum: 0.7772;
- GPi: 0.7771;
- STN: 0.7732;
- thalamus: 0.7548;
- workspace: 0.7487;
- association: 0.7296.

The weakest values in this run were observed for memory (0.2543), DMN (0.3026) and sensory populations (0.3854).

These results demonstrate target-dependent causal sensitivity within the synthetic network. They must not be interpreted as biological target rankings or clinical recommendations. The ordering is expected to depend on network initialization, synthetic connection strengths, perturbation definition and metric construction.

## 5. Negative result: failure of the current surrogate test

The most scientifically important result of this validation may be the one that weakens the interpretation.

V3 includes two surrogate/null transformations. A temporal shuffle destroys temporal ordering while preserving marginal values. Independent node-wise circular shifts better preserve each node's individual temporal structure while disrupting cross-node alignment.

The reduced surrogate evaluation produced:

- temporal shuffle convergence: approximately 0.607;
- node circular-shift convergence: approximately 0.631.

The mean main-run cross-theory convergence was approximately 0.555. Thus the surrogate values were not lower; they were higher. Similarly, surrogate topology-balance estimates of approximately 0.445 and 0.455 exceeded the main-run mean topology balance of approximately 0.402.

This is a failed specificity test.

Several explanations are possible. First, the surrogate evaluator intentionally uses only a reduced subset of the full model metrics, so its convergence value is not numerically identical to the online cross-theory convergence metric. Second, shuffling can increase some generic entropy/geometry statistics by destroying structured dependencies, so a naive "higher complexity is better" null test can reward randomness. Third, only one surrogate realization of each type was generated, providing no null distribution. Fourth, the topology null contains a neutral segregation baseline rather than recomputing all original community-dependent quantities. These design choices make the current null test inadequate as confirmatory evidence.

Accordingly, the operational transition should **not** be described as a validated consciousness signature. The null result instead provides a clear falsification target for v4.

A stronger test would require many surrogate replicates, metric-identical evaluation of real and surrogate data, empirical p-values, correction for multiple comparisons, effect-size reporting, and held-out threshold selection. Surrogates should include phase randomization, amplitude-adjusted Fourier surrogates, connectivity-preserving null graphs, action-label permutation, causal-edge rewiring and matched autoregressive controls.

## 6. Relationship to contemporary consciousness research

### 6.1 Cross-theory rather than theory-monolithic design

The 2025 Cogitate adversarial collaboration found evidence consistent with parts of both IIT and GNWT while challenging key claims of each [1]. The present simulator therefore does not identify workspace ignition or integration alone with consciousness. The detector instead requires agreement among computationally different families.

This design is not theory-neutral in the strong philosophical sense because metric selection necessarily encodes assumptions. It is better described as **theory-pluralistic and falsification-oriented**.

### 6.2 Criticality and perturbational complexity

Maschke et al. found that unconscious states under anaesthesia were associated with movement away from avalanche criticality and edge-of-chaos dynamics, and that spontaneous EEG dynamics predicted PCI [2]. Toker et al. linked conscious cortical-thalamic information transfer with proximity to edge-of-chaos criticality [3]. Ge et al. further associated abnormal critical dynamics with disorders of consciousness and clinical/metabolic measures [6].

These findings motivated the decision to compute criticality in more than one way and to include perturbational responses. However, our measures are low-dimensional algorithmic proxies and should not be numerically compared with empirical EEG/fMRI values.

### 6.3 Mesocircuit causal modelling

Toker et al. (2026) combined deep neural consciousness classifiers with interpretable neural-field models and used adversarial interaction between them to reproduce conscious and comatose neurophysiology and generate testable intervention hypotheses [4]. This work is an especially important methodological inspiration because it shifts emphasis from classification toward causal modelling and intervention.

V3's synthetic thalamus/striatum/GPe/STN/GPi populations and lesion/stimulation hooks follow that causal philosophy. The present 5,000-cycle exact-build validation did not complete the full ablation/recovery suite in the available execution window, so no new claim about lesion-specific necessity is made in this paper. Those experiments are part of the software but remain to be run systematically under a preregistered protocol.

### 6.4 Integration and segregation

Zhu et al. reported that disorders of consciousness disrupt both integration and segregation and that the two properties relate differently to state, behaviour and prognosis [5]. V3 therefore measures them separately. The present validation showed a post-event rise in topology balance, but the surrogate problem prevents that finding from being treated as specific to meaningful temporal organization.

### 6.5 Complex processing without consciousness

The anaesthetized hippocampus results of Katlowitz et al. are an important interpretive guardrail [7]. Semantic, grammatical and predictive neural processing can persist during general anaesthesia. Thus increasingly capable prediction, learning or representation in an artificial system is not by itself evidence of conscious awareness. The present experiment adopts the same caution: computation is measured as computation.

## 7. What was actually found

The verified experiment supports the following limited conclusions.

First, a recurrent agent with learned self/world models and no scheduled self-reference phase can enter a sustained state satisfying a demanding, explicitly coded multi-channel operational gate. The first transition occurred at cycle 1,600 in the exact-build seed-17 validation.

Second, the transition was accompanied by changes across several distinct metric families rather than one scalar alone. Particularly large increases appeared in counterfactual agency, perturbational complexity and topology balance.

Third, the trained recurrent state responded heterogeneously to target-specific virtual perturbations, showing that the synthetic architecture contains differentiated causal sensitivity rather than a completely homogeneous response surface.

Fourth, and critically, the present surrogate analysis failed to establish specificity. Destroying temporal/cross-node organization did not reduce the surrogate convergence score. This means the current metric family can reward statistical properties present in null data and requires redesign before strong interpretation.

The experiment therefore found a **reproducible operational phase transition in a synthetic cognitive architecture plus a falsification failure in the initial null test**. It did not find consciousness.

## 8. Limitations

### 8.1 Construct validity

Every central quantity is a proxy chosen by the model designer. Labels such as self, workspace, thalamus, agency, criticality and PCI-like complexity refer to computational constructs that only partially correspond to biological concepts. Construct validity has not been independently established.

### 8.2 Threshold dependence

The operational event depends on explicit thresholds, weights and persistence requirements. Although the gate is more stringent than a single composite score, it remains designer-defined. Different thresholds could alter activation timing or eliminate the event.

### 8.3 Single-seed confirmatory weakness

The paper reports one exact-build seed as a reproducibility demonstration, not population-level evidence. A scientifically stronger analysis needs many independent seeds and a predefined statistical plan.

### 8.4 Surrogate mismatch

The current surrogate evaluator is not metric-identical to the online detector and uses too few surrogate realizations. This is the largest immediate methodological limitation.

### 8.5 No empirical neural calibration

Parameters were not fitted to human or animal electrophysiology. Population names and connection motifs should therefore not be interpreted as validated neurobiological mechanisms.

### 8.6 No phenomenal ground truth

There is no behavioural report, biological organism or accepted phenomenal-consciousness ground truth in the simulation. Even a perfect classifier of the simulator's own operational state could not establish subjective experience.

### 8.7 Metric non-independence

Several observables share underlying state variables. Eight or ten votes are not equivalent to eight or ten statistically independent sources of evidence. Future work should quantify redundancy and conditional dependence among channels.

## 9. Proposed v4 preregistered falsification protocol

The strongest next version should prioritize validation over adding new features.

A proposed confirmatory protocol would include at least 100 independent seeds split into development and held-out test sets. All metric weights and thresholds would be frozen using only development runs. The held-out set would then be evaluated once.

For every real trajectory, at least 100 matched surrogates should be produced from multiple null families. The exact same diagnostic pipeline should be applied to real and surrogate data. The primary endpoint should be an empirical null probability for sustained operational events rather than the raw ghost-index magnitude.

Ablation conditions should include workspace removal, self-model removal, thalamic disconnection, indirect-pathway disruption, subcritical and supercritical gain, excitation/inhibition imbalance, connectome shuffling, replay removal and counterfactual-agency removal. Ideally, each ablation should start from matched random seeds and as much shared initial state as technically possible.

A lesion/recovery experiment should test whether perturbations can restore an operational regime after targeted damage, but the analysis should focus on causal differences relative to sham stimulation. Target rankings must be reported as synthetic-system results only.

Finally, dimensionality reduction and feature-attribution analysis should determine which metrics actually drive the detector. If a small subset predicts nearly all events, the claimed cross-theory convergence should be reconsidered as redundant.

## 10. Conclusion

*Ghost in the Machine v3* is best understood as an experimental software instrument for asking structured questions about recurrent self-modelling systems. Its main contribution is methodological: it combines learning, recurrent dynamics, counterfactual agency, metacognition, criticality, network topology, complexity, mesocircuit modelling and causal perturbation within one long-running falsifiable framework.

The verified exact-build simulation produced a sustained operational transition at cycle 1,600 and remained in the active state for a substantial portion of the run. The transition involved multiple dynamical changes and differentiated perturbation responses. These findings justify further computational investigation.

However, the null analysis failed an essential specificity check. Surrogate transformations did not suppress the reduced convergence metric. This prevents the operational event from being interpreted as a validated marker of consciousness and demonstrates why negative controls are indispensable in computational consciousness research.

The most productive interpretation is therefore neither "the machine became conscious" nor "nothing happened." A nontrivial synthetic phase transition occurred under explicit multi-channel criteria, but the first adversarial test exposed a weakness in the metric design. That is exactly the kind of outcome a falsifiable research platform should make visible.

## References

1. Cogitate Consortium, Ferrante, O., Gorska-Klimowska, U. et al. Adversarial testing of global neuronal workspace and integrated information theories of consciousness. *Nature* 642, 133-142 (2025). https://doi.org/10.1038/s41586-025-08888-1

2. Maschke, C., O'Byrne, J., Colombo, M. A. et al. Critical dynamics in spontaneous EEG predict anesthetic-induced loss of consciousness and perturbational complexity. *Communications Biology* 7, 946 (2024). https://doi.org/10.1038/s42003-024-06613-8

3. Toker, D., Mueller, E., Miyamoto, H. et al. Criticality supports cross-frequency cortical-thalamic information transfer during conscious states. *eLife* 13, e86547 (2024). https://doi.org/10.7554/eLife.86547

4. Toker, D., Zheng, Z. S., Thum, J. A. et al. Adversarial AI reveals mechanisms and treatments for disorders of consciousness. *Nature Neuroscience* 29, 964-977 (2026). https://doi.org/10.1038/s41593-026-02220-4

5. Zhu, S., Xu, X., He, Q. et al. Topological integration and segregation of the conscious connectome as biomarkers for state, behavior, and prognosis. *Communications Medicine* (2026). https://doi.org/10.1038/s43856-026-01870-6

6. Ge, Q., Xin, Y., He, C. et al. Brain criticality characterizes abnormal neural dynamics and metabolism in disorder of consciousness. *Communications Biology* (2026). https://doi.org/10.1038/s42003-026-10713-y

7. Katlowitz, K. A., Cole, E. R., Mickiewicz, E. A. et al. Plasticity and language in the anaesthetized human hippocampus. *Nature* 654, 714-723 (2026). https://doi.org/10.1038/s41586-026-10448-0

## Data and code availability

All code and synthetic outputs described in this report are contained in the accompanying project archive. The exact validation source hash is recorded in `docs/SHA256SUMS.txt`. The primary results used in this paper are `results/final_validation/trajectory_v3.csv`, `summary_v3.json`, `stimulation_scan_v3.csv`, `surrogate_nulls_v3.csv` and `run.log`.

## Ethics and interpretation statement

No human or animal subjects were used in this project. The work is a synthetic computational simulation. Population names are biologically inspired abstractions. The output must not be used to diagnose consciousness, guide treatment, recommend brain stimulation or infer subjective experience in humans, animals or artificial systems.
