# Post-Stroke Gait Analysis Pipeline

**Research Project - MSc Biomedical Engineering**

---

## Overview

A Python-based musculoskeletal modelling pipeline for analysing gait biomechanics in post-stroke patients of varying severity compared to healthy controls. Built around OpenSim, the pipeline covers the full workflow from raw motion capture and force plate data through to joint reaction forces and muscle force outputs.

**Subjects:** Three post-stroke individuals (mild, moderate, and severe hemiparesis) and two healthy controls, selected from the publicly available Van Criekinge et al. (2023) dataset. Subjects performed self-selected speed walking trials with 3D marker trajectories and ground reaction forces (GRF) recorded. C3D and CSV files were inspected and processed using Mokka prior to OpenSim analysis.

## Dataset Attribution

> The motion capture and force plate data used in this project are from the publicly available dataset:
>
> Van Criekinge, T., Saeys, W., Truijen, S., Vereeck, L., Sloot, L. H., & Hallemans, A. (2023). *A full-body motion capture gait dataset of 138 able-bodied adults across the life span and 50 stroke survivors.* Scientific Data, 10. https://doi.org/10.1038/s41597-023-02767-y
>
> All Python scripts for data conversion, processing, and visualisation are original work developed independently for this project.

---

## Pipeline Overview

The analysis follows this sequential workflow:

```
Raw Data (CSV + C3D)
        │
        ▼
1. csv2grf.py              ← Convert force plate CSV → OpenSim GRF .mot
        │
        ▼
2. grf.mot2grf.xml.py      ← Generate ExternalLoads.xml for OpenSim
        │
        ▼
3. [OpenSim GUI]           ← Run Scaling → IK → ID → Static Optimisation
        │
        ▼
4. convertIK to radian.py  ← Convert IK output to radians if needed
        │
        ▼
5. JointReaction.xml.py    ← Generate Joint Reaction Analysis setup XML
   FD.xml.py               ← Generate Forward Dynamics setup XML
        │
        ▼
6. [OpenSim GUI]           ← Run JRA and Forward Dynamics
        │
        ▼
7. Visualisation scripts   ← Plot results
```

---

## Scripts

### Data Preparation
| Script | Description |
|---|---|
| `csv2grf.py` | Converts raw force plate CSV (Fx, Fy, Fz, Mx, My, Mz) to OpenSim-compatible GRF `.mot` file. Calculates Centre of Pressure (CoP) for 4 force plates, converts moments from Nmm to Nm, and handles column mapping. |
| `grf.mot2grf.xml.py` | Generates the `ExternalLoads.xml` configuration file needed to apply ground reaction forces in OpenSim's Inverse Dynamics tool. |
| `convertIK to radian.py` | Converts Inverse Kinematics output from degrees to radians for downstream modelling if required. |

### OpenSim Setup
| Script | Description |
|---|---|
| `JointReaction.xml.py` | Generates the XML setup file for OpenSim's Joint Reaction Analysis tool, specifying joints and bodies of interest. |
| `FD.xml.py` | Generates the XML setup file for OpenSim's Forward Dynamics tool, using Static Optimisation activations as controls and IK results as initial states. |

### Visualisation
| Script | Description |
|---|---|
| `Gait Kinematics Comparison Plot.py` | Plots hip, knee, and ankle joint angles (0–100% gait cycle) comparing post-stroke and healthy subjects, with mean ± SD normative band. |
| `results_analysis.py` | Plots joint reaction forces (hip, knee, ankle — bilateral) from the JRA `.sto` output file. |
| `muscle forces.py` | Plots bilateral muscle forces from Static Optimisation results across 43+ lower limb and trunk muscles. |
| `JFR subplot.py` | Generates multi-panel subplot visualisations of joint reaction forces for presentation. |
| `submuscles plot.py` | Plots forces for individual sub-muscles (e.g., gluteus medius parts 1–3) for detailed analysis. |

---

## Requirements

```
pip install pandas numpy matplotlib seaborn
```

OpenSim must be installed separately: [https://opensim.stanford.edu](https://opensim.stanford.edu)

---

## Data Format

Input files expected by the scripts:
- Force plate data: `.csv` (exported from motion capture system, e.g., Vicon)
- Model file: `.osim` (scaled OpenSim musculoskeletal model)
- IK results: `.mot` file from OpenSim Inverse Kinematics
- SO results: `.sto` file from OpenSim Static Optimisation
- JRA results: `.sto` file from OpenSim Joint Reaction Analysis

> **Note:** File paths in all scripts are currently set to local data directories and must be updated before running.

---

## Tech Stack

Python, OpenSim, Mokka, NumPy, Pandas, Matplotlib, Seaborn
