# Use Case 1: Quantum Anomaly Detection for Car Manufacturing

| Item | Details |
|---|---|
| **Author / Lead** | LUMI-IQ Consortium (WP2) |
| **Domain** | Automotive Quality Assurance / Defect Detection |
| **Quantum Approach** | Quantum Kernel Methods (`ZZFeatureMap` 4-qubit fidelity statevector kernel & hardware overlap circuits) |
| **Hardware Target** | Local Statevector Simulation (`SIM`) or Real QPU (`VLQ` 24-qubit Star topology at IT4Innovations) |
| **Classical Baselines** | One-Class SVM (RBF kernel), Isolation Forest |
| **Execution Modes** | Standalone Python Script (`run_car_manufacturing.py`) & JupyterLab Notebook (`car_manufacturing.ipynb`) |

---

## 1. Overview

This use case detects rare manufacturing defects in car body assembly from multi-sensor deviations (panel gap, weld strength, vibration, torque). Because defects occur at low frequencies (~5%), training operates under a **one-class classification paradigm** where the model trains exclusively on known-good reference parts. 

A 4-qubit quantum statevector fidelity kernel maps the 4-dimensional sensor feature vectors into a Hilbert space via parameterized entangling rotations, measuring the overlap between test parts and the normal reference baseline.

---

## 2. Hardware Execution: Why & How It Runs on VLQ

* **Hardware Compatibility:** The sensor feature map requires only **4 qubits** and a shallow entangling depth ($\sim 15$ gates), well within the coherence time of the **24-qubit VLQ QPU**.
* **Hybrid Partitioning:**
  * **Full dataset baseline training:** Evaluated via simulation on LUMI CPU to avoid flooding the queue with $80 \times 140 = 11\,200$ pairwise circuit evaluations.
  * **Hardware Verification (`--backend VLQ`):** Submits real 4-qubit overlap circuits $U(x_{\text{ref}})^\dagger U(x_{\text{test}})$ with 1024 shots to **VLQ** via QaaS to verify incoming test parts against reference baselines.

---

## 3. Directory Structure

```
01_car_manufacturing/
├── README.md                     # Documentation and execution guide
├── run_car_manufacturing.py      # Standalone CLI / Slurm batch script (--backend SIM | VLQ)
├── car_manufacturing.ipynb       # Interactive notebook for LUMI Open OnDemand
└── result_car_manufacturing.png  # Generated benchmark plot (ROC curves & catch rates)
```

---

## 4. Quick Start on LUMI

### Option A: Command Line / Slurm Batch Execution

Activate the unified LUMI-IQ environment:

```bash
module use $HOME/modulefiles
module load Lumi-IQ-qaas/VLQ

# Run standard simulation on LUMI CPU (fast test):
python run_car_manufacturing.py --backend SIM

# Or submit verification circuits to the real VLQ quantum computer:
python run_car_manufacturing.py --backend VLQ --shots 1024
```

### Option B: Interactive JupyterLab via Open OnDemand

1. Launch JupyterLab on [lumi.csc.fi](https://lumi.csc.fi) using the `lumi-iq` module script.
2. Open `car_manufacturing.ipynb`.
3. Set `TARGET_BACKEND = "SIM"` or `"VLQ"` and run all cells sequentially.
