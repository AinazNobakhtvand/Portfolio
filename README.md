# Portfolio — Ainaz Nobakhtvand

**MSc student in Biomedical Engineering** | Image Processing · Signal Processing · Machine Learning  
📧 ainaz.nobakhtvand@umfiasi.ro

---

## About

This repository showcases my research and course-based projects in biomedical signal and image processing, with a focus on EEG analysis, medical image segmentation, and machine learning. The projects span neuroscience, ophthalmology, oncology, and biomechanics — reflecting my interest in applying computational methods to real clinical and research problems.

---

## Projects

### 1. 🧠 Perceptual Decision-Making in Autism and Dyslexia *(Master's Thesis — In Progress)*
**`EEG-Perceptual-DecisionMaking-Autism-Dyslexia/`**

A multi-dataset EEG study comparing perceptual decision-making across children with Autism Spectrum Disorder (ASD), developmental dyslexia, and typically developing (TD) controls. This work replicates and extends two landmark studies (Manning et al., 2022) using a unified Drift-Diffusion Model (DDM) + EEG framework — the first direct autism–dyslexia comparison of this kind. Analysis begins from pre-processed EEG data (MATLAB), with RCA, Unfold deconvolution, DDM fitting, and ML classification performed independently.

**Key methods:**
- EEG preprocessing pipeline: band-pass filtering, ICA, ASR, average re-referencing (MNE-Python / EEGLAB)
- Reliable Components Analysis (RCA) and stimulus-response deconvolution (Unfold toolbox)
- Centro-Parietal Positivity (CPP) slope extraction as a neural accumulator measure
- 5-parameter hierarchical Bayesian DDM with DE-MCMC sampling and Savage-Dickey Bayes factors
- Machine learning classification (Logistic Regression, SVM, Random Forest, XGBoost) with SHAP feature importance and ablation study across behavioural, DDM, and EEG feature modalities

**Status:** RCA, Unfold deconvolution, DDM fitting, and comparative analysis complete. ML classification in progress.

**Tech stack:** Python, R (hDDM, MatchIt), MNE-Python, EEGLAB, Unfold, scikit-learn, XGBoost

---

### 2. 🔬 EEG Face/Car Stimulus Classification *(Course Project)*
**`EEG-Perceptual-DecisionMaking-FaceCar/`**

Analysis and classification of a 64-channel EEG dataset (216 trials) from a visual stimulus paradigm, investigating neural discrimination between face and car stimuli. Starting from pre-processed, epoched EEGLAB data, the project covers ERP analysis, dimensionality reduction, and multi-classifier comparison to identify the most discriminative brain features.

**Key methods:**
- Loading pre-processed EEGLAB `.mat` files (scipy.io / h5py for v7.3+ files); time-window extraction (0–500ms post-stimulus)
- ERP analysis: N170 component identification (150–200ms), grand-average and single-trial variability plots
- PCA on 64-channel × 500ms EEG data; loading heatmaps (channel × time) to interpret spatio-temporal patterns
- Classification of face vs. car stimuli using PCA features: Logistic Regression, SVM, Random Forest, Neural Network
- Accuracy vs. number of PCs analysis; 5-fold cross-validation

**Tech stack:** Python, NumPy, SciPy, h5py, scikit-learn, Matplotlib, ipywidgets

---

### 3. 🏥 Pituitary Tumor Segmentation *(Course Project)*
**`Pituitary-Tumor-Segmentation/`**

Deep learning pipeline for automatic segmentation of pituitary tumors in brain CT scans, trained on 994 annotated images with binary segmentation masks.

**Key methods:**
- U-Net CNN architecture (5-block encoder-decoder with skip connections)
- Data preprocessing: normalisation, channel dimension expansion, train/test split (70/30)
- Model training with TensorFlow/Keras (Conv2D, MaxPooling2D, BatchNormalization, Dropout)
- Evaluation via segmentation accuracy and visual mask overlays

**Tech stack:** Python, TensorFlow/Keras, OpenCV, NumPy, Matplotlib

---

### 4. 👁️ OCT Retinal Image Analysis *(Course Project)*
**`OCT-Image-Analysis/`**

Image processing and classification pipeline applied to a pre-existing Optical Coherence Tomography (OCT) retinal image, covering coordinate transformation, denoising, segmentation, feature extraction, and supervised classification.

**Key methods:**
- Polar-to-Cartesian coordinate transformation with interpolation
- Five filtering strategies: Gaussian, Median, Bilateral, and combinations
- Segmentation: Otsu's thresholding and K-Means clustering
- Feature extraction: Local Mean/Std, Sobel gradient, entropy, GLCM (local range), LBP
- Supervised classification: SVM (RBF kernel) and Random Forest with confusion matrix evaluation

**Tech stack:** Python, NumPy, scikit-image, scikit-learn, SciPy, Matplotlib

---

### 5. 🦿 Post-Stroke Gait Analysis Pipeline *(Research Project)*
**`Biomechanics-Data-Processing/`**

A musculoskeletal modelling pipeline for analysing gait biomechanics in post-stroke patients vs healthy controls, built around OpenSim. Covers the full workflow from raw motion capture data to joint reaction forces and muscle force outputs, with custom Python scripts for data conversion, processing, and visualisation.

**Key methods:**
- Data sourced from Van Criekinge et al. (2023) — a public full-body motion capture dataset of 138 able-bodied adults and 50 stroke survivors (*Scientific Data*)
- Three post-stroke individuals (mild, moderate, severe hemiparesis) compared against two healthy controls
- Force plate data conversion: CSV → OpenSim-compatible GRF `.mot` files, including Centre of Pressure (CoP) calculation from forces and moments across 4 force plates
- OpenSim pipeline: Inverse Kinematics (IK), Inverse Dynamics (ID), Static Optimisation (SO), Joint Reaction Analysis (JRA), and Forward Dynamics (FD)
- Gait cycle normalisation (0–100%) and comparison of hip, knee, and ankle kinematics across stroke severities
- Visualisation of joint reaction forces, muscle forces, and sub-muscle contributions across the gait cycle

**Tech stack:** Python, OpenSim, Mokka, NumPy, Pandas, Matplotlib, Seaborn

---

## Skills Summary

| Area | Tools & Methods |
|---|---|
| EEG / Signal Processing | MNE-Python, EEGLAB, Unfold, ICA, RCA, ERPs, PCA, DDM |
| Medical Image Processing | U-Net, OCT analysis, MRI segmentation, OpenCV, scikit-image |
| Machine Learning | SVM, Random Forest, XGBoost, SHAP, scikit-learn |
| Deep Learning | TensorFlow, Keras, CNN architectures |
| Statistical Modelling | Hierarchical Bayesian DDM, Bayes factors, R (hDDM, MatchIt) |
| Biomechanics / Musculoskeletal | OpenSim, Mokka, IK, ID, JRA, GRF processing, gait analysis |
| Languages | Python, R, MATLAB |

---

## Repository Structure

```
Portfolio/
├── README.md
├── EEG-Perceptual-DecisionMaking-Autism-Dyslexia/   # MSc thesis (in progress)
├── EEG-Perceptual-DecisionMaking-FaceCar/            # EEG course project
├── Pituitary-Tumor-Segmentation/                     # Deep learning, CT segmentation
├── OCT-Image-Analysis/                               # Image processing + ML
└── Biomechanics-Data-Processing/                     # Post-stroke gait analysis
```

---

*This portfolio is actively updated as my thesis and projects progress.*
