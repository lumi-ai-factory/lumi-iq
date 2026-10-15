# Use Case 1: Quantum Anomaly Detection for Car Manufacturing

| Item | Details |
|---|---|
| **Author / Lead** | Dr. Van Binh Henri VU (IT4Innovations, VSB - Technical University of Ostrava) |
| **Domain** | Automotive Quality Assurance / Defect Detection |
| **Quantum Approach** | Quantum Kernel Methods (`ZZFeatureMap` 4-qubit fidelity statevector kernel) |
| **Classical Baselines** | One-Class SVM (RBF kernel), Isolation Forest |
| **Execution Modes** | Standalone Python Script (`run_car_manufacturing.py`) & JupyterLab Notebook (`car_manufacturing.ipynb`) |

---

## 1. Overview

This use case detects rare manufacturing defects in car body assembly from multi-sensor deviations (panel gap, weld strength, vibration, torque). Because defects occur at low frequencies (~5%), training operates under a **one-class classification paradigm** where the model trains exclusively on known-good reference parts. 

A 4-qubit quantum statevector fidelity kernel maps the 4-dimensional sensor feature vectors into a Hilbert space via parameterized entangling rotations, measuring the overlap between test parts and the normal reference baseline.

---

## 2. Directory Structure

```
01_car_manufacturing/
├── README.md                     # Documentation and execution guide
├── run_car_manufacturing.py      # Standalone CLI / Slurm batch script
├── car_manufacturing.ipynb       # Interactive notebook for LUMI Open OnDemand
└── result_car_manufacturing.png  # Generated benchmark plot (ROC curves & catch rates)
```

---

## 3. Quick Start on LUMI

### Option A: Command Line / Slurm Batch Execution

Activate the unified LUMI-IQ environment and run:

```bash
module use $HOME/modulefiles
module load lumi-iq

python run_car_manufacturing.py
```

The script evaluates the quantum anomaly scores against classical baselines, prints detailed classification metrics (AUC, Precision, Recall, F1), and generates `result_car_manufacturing.png`.

### Option B: Interactive JupyterLab via Open OnDemand

1. Launch JupyterLab on [lumi.csc.fi](https://lumi.csc.fi) using the `lumi-iq` module script.
2. Open `car_manufacturing.ipynb`.
3. Run all cells sequentially.
