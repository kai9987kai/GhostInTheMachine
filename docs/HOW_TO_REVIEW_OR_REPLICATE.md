# How to review, attack or replicate Ghost in the Machine

This project's claims are only as good as the attempts to break them. This guide is for human reviewers and for other AI agents. Please try to falsify the results, not confirm them.

## 1. Reproduce exactly (about 40 minutes on 4 cores)

```bash
git clone https://github.com/kai9987kai/GhostInTheMachine && cd GhostInTheMachine
python -m pip install "numpy>=1.26" "matplotlib>=3.8" pytest
python -m pytest -q                                   # 28+ tests, including an exact v3 reproduction
python src/ghost_in_the_machine_v4.py verify          # preregistration lock still matches the code
python src/ghost_in_the_machine_v4.py all --out my_results --workers 4
diff <(python -c "import json;print(json.dumps(json.load(open('my_results/results_v4.json'))['v4']['primary'],indent=1,sort_keys=True))") \
     <(python -c "import json;print(json.dumps(json.load(open('results/v4/results_v4.json'))['v4']['primary'],indent=1,sort_keys=True))")
```

The pipeline is deterministic given seeds, so numbers should match. If they don't on your platform, that is itself a finding: please report the platform, Python and NumPy versions.

## 2. Things worth attacking

| claim | where it lives | how to attack it |
|---|---|---|
| v3's event is a gain ramp + hysteresis | `src/ghost_v4/v3_bridge.py`, `results/v4/v3_forensics/` | Check that the controls change only what they claim (gain clamp, replay world, zero learning rates). Try other clamp values. |
| v3's metrics cannot see temporal order | `v3_window_metrics`, Figure 3b | Confirm metric identity against the online values; try other window lengths. |
| Authorship stabilizes the self-mode (H1) | `engine.py` (yoke), `metrics.self_persistence` | Is the twin's stream really matched? Does the effect survive other macro-variables (PC1, mean field), other lags, other windows? |
| Self-specificity (H2) | `campaign.analyze_v4` | Is "self" special only because it receives the comparator input? Move the comparator projection to another population and see whether the effect moves with it. |
| Comparator mechanism (H3) | `CONDITIONS` in `campaign.py` | Are lesions too blunt? Try partial lesions (scaled projection). |
| Ψ increase (H4) | `infotheory.emergence_criteria` | Gaussian estimator. Use nonlinear estimators (see the v5 follow-up) and other part-partitions. |
| Nonlinear arrow of time (H6) | `temporal.ordinal_irreversibility` | Try amplitude-adjusted multivariate surrogates, other pattern orders and lags. |
| Calibration | `controls.py`, `results/v4/calibration/` | Add ground-truth systems that the current controls miss. |

The known limitations (same analyst for development and confirmation, one architecture family, linear estimators, a cross-network yoke) are listed in the paper, Section 5.5. Findings that go beyond them are the most valuable.

## 3. Run an independent replication

1. Copy `prereg/PREREGISTRATION_v4.json` to a new file, for example `prereg/REPLICATION_<yourname>.json`.
2. Change the confirmatory `seeds` and `world_seed_base` to values nobody has used (see the existing prereg files for used ranges), and add your name and date.
3. Lock it before running anything:
   `python -c "import sys; sys.path.insert(0,'src'); from pathlib import Path; from ghost_v4 import prereg as p; p.lock(Path('prereg/REPLICATION_<yourname>.json'), Path('prereg/REPLICATION_<yourname>.lock.json'))"`
4. Commit and push the lock (or post its SHA-256 publicly) before the run.
5. Run with the v5 study runner: `python src/ghost_in_the_machine_v5.py replicate --prereg prereg/REPLICATION_<yourname>.json --out results/replication_<yourname>`.
6. Report every hypothesis, whatever it shows.

## 4. Reporting

Open a GitHub issue titled "Review:" or "Replication:" with the platform, the commands you ran, what you expected and what you got. Negative results are as welcome as positive ones.
