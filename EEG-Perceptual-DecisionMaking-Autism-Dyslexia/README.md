# Perceptual Decision-Making in Autism and Dyslexia
### Replication, Comparative Analysis, and Machine Learning Classification

**Master's Thesis - MSc Biomedical Engineering** | *In Progress*

---

## Overview

This thesis investigates whether children with Autism Spectrum Disorder (ASD) and children with developmental dyslexia show distinct or overlapping signatures in perceptual decision-making, using a unified computational and neural framework applied to two independent datasets.

The work is structured in three parts:

1. **Replication** - Independently replicate the findings of two landmark EEG studies (Manning et al., 2022) on ASD and dyslexia separately, verifying their DDM and neural results
2. **Comparative Analysis** - Directly compare ASD, dyslexia, and typically developing (TD) controls within the same DDM + EEG framework - the first study of this kind
3. **Machine Learning Classification** - Classify neurodevelopmental group membership using behavioural, DDM, and EEG features, with SHAP-based interpretability

---

## Datasets

| Dataset | Source | Participants | Task |
|---|---|---|---|
| Autism | Manning et al., 2022 (*Scientific Reports*) | Children with ASD + TD controls | Visual motion coherence + direction integration |
| Dyslexia | Manning et al., 2022 (*Journal of Neuroscience*) | Children with dyslexia + TD controls | Visual motion coherence + direction integration |

Groups were matched on age and performance IQ using R `MatchIt`. EEG was recorded with a 128-channel Geodesic Net at 500 Hz.

---

## Methods

### Starting Point
Analysis begins from pre-processed EEG data provided as MATLAB `.m` files (band-pass filtered, ICA applied, re-referenced). The following steps were performed independently:

### Neural Signal Extraction
- **Reliable Components Analysis (RCA):** Response-locked epochs (−600 to +200 ms), spatial component decomposition
- **Stimulus-response deconvolution:** Unfold toolbox with ridge regression regularisation
- **CPP slope extraction:** Centro-Parietal Positivity slope over −200 to 0 ms pre-response, used as a neural accumulator measure

### Drift-Diffusion Modelling (DDM)
- 5-parameter hierarchical Bayesian DDM (drift rate *v*, boundary separation *a*, non-decision time *t_er*, starting point *z/a*)
- DE-MCMC sampling (15 chains, 4000 iterations)
- Convergence diagnostics: Gelman-Rubin R-hat
- Bayesian inference via Savage-Dickey Bayes factors
- Covariate models: Performance IQ, Age, Reading ability
- Joint DDM-EEG model: Drift rate ↔ CPP slope correlation

### Machine Learning Classification *(in progress)*
- Features: Behavioural (accuracy, RT), DDM parameters, EEG (CPP slope, amplitude, latency)
- Classifiers: Logistic Regression, SVM, Random Forest, XGBoost
- Validation: Stratified 10-fold CV and LOOCV
- Interpretability: SHAP feature importance, modality-level ablation study (Behavioural vs DDM vs EEG vs All)

---

## Important Note

> The RCA, Unfold, DDM, and comparative analysis scripts in this repository are adapted from the original code accompanying Manning et al. (2022). Modifications were made to adapt file paths, environment settings, and dependencies for local execution. All scientific methodology follows the original published protocols. The machine learning classification scripts are original work developed independently as part of this thesis.

---

## Code Attribution

| Scripts | Origin |
|---|---|
| RCA, Unfold deconvolution, CPP extraction | Adapted from Manning et al. (2022) original code, modified for local environment (file paths, dependencies, execution) |
| DDM fitting (hDDM / R) | Adapted from Manning et al. (2022) original code, modified for local environment |
| Comparative analysis | Adapted from Manning et al. (2022) original code, modified for local environment |
| **ML classification** | **Original work** |

> The datasets and original analysis code are publicly available via the Open Science Framework (OSF) links provided in the original Manning et al. publications. Scripts in this repository represent adaptations for local execution and the original ML classification work.

---

## Repository Contents (will be added after the project is compeletely done)

```
EEG-Perceptual-DecisionMaking-Autism-Dyslexia/
├── rca_unfold/           # RCA + Unfold scripts (adapted from Manning et al.)
├── ddm/                  # DDM fitting scripts (adapted from Manning et al.)
├── analysis/             # Comparative analysis (adapted from Manning et al.)
├── ml/                   # ML classification — original work (in progress)
└── figures/              # Output plots and visualisations
```

---

## Status

| Component | Status |
|---|---|
| RCA + CPP extraction (Unfold) | ✅ Complete |
| DDM fitting (ASD) | ✅ Complete |
| DDM fitting (Dyslexia) | ✅ Complete |
| Comparative analysis | ✅ Complete |
| ML classification | 🔄 In progress |

---

## Tech Stack

Python (MNE-Python, scikit-learn, XGBoost, SHAP), R (hDDM, MatchIt), MATLAB (EEGLAB, Unfold, RCA toolbox)

---

## References

- Manning, C., et al. (2022). Characteristics of perceptual decision-making in autistic children. *Scientific Reports.*
- Manning, C., et al. (2022). Perceptual averaging and decision-making in developmental dyslexia. *Journal of Neuroscience.*
