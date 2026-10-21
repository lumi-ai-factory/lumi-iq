# Use Case 2: Health & Life Science — Molecular VQE & Classical Shadows

| Item | Details |
|---|---|
| **Author / Lead** | LUMI-IQ Consortium (WP2) |
| **Domain** | Computational Chemistry / Life Sciences |
| **Quantum Approach** | VQE (`EfficientSU2` ansatz + SPSA optimizer) & Classical Shadows observable estimation |
| **Hardware Target** | Local Simulator (`SIM` via Qiskit Aer) & Real QPU (`VLQ` 24-qubit Star topology via LEXIS) |
| **Execution Modes** | Standalone Python Script (`run_health_vqe.py`) & JupyterLab Notebook (`health_vqe.ipynb`) |

---

## 1. Overview

This use case computes the molecular ground state energy of small molecules (such as $H_2$) using a hybrid quantum-classical architecture partitioned across classical HPC and the VLQ quantum processor:

1. **Classical Stage (LUMI CPU):** PySCF performs Hartree-Fock self-consistent field calculation and Automated Valence Active Space (AVAS) selection, mapped to a Jordan-Wigner qubit Hamiltonian.
2. **Quantum VQE Stage (LUMI / VLQ):** Evaluates parameterized quantum states via SPSA optimization to converge on ground state parameters.
3. **Post-Processing Stage (Classical Shadows):** Constructs randomized Pauli snapshot measurements to reconstruct multi-qubit observable expectation values with reduced sample complexity $\mathcal{O}(\log M)$.

---

## 2. Directory Structure

```
02_health_life_science/
├── README.md               # Documentation and execution guide
├── run_health_vqe.py       # Standalone CLI / Slurm batch runner
├── health_vqe.ipynb        # Interactive notebook for LUMI Open OnDemand
├── result_health.png       # Generated VQE energy convergence plot
├── vqe_trajectory.csv      # Saved optimizer parameter trajectory
├── vqe-replay.csv          # Re-measured high-shot ground state trajectory
└── code/                   # Core modular components
    ├── main.py             # Workflow orchestration (adapted for centralized config)
    ├── hamiltonian.py      # Hartree-Fock & Jordan-Wigner Hamiltonian builder
    ├── vqe.py              # Circuit ansatz, grouping & SPSA optimization
    ├── classical_shadow.py # Snapshot circuits & shadow observable estimator
    ├── fetch_replay.py     # Asynchronous job retrieval utility
    └── plot.py             # Trajectory visualization
```

---

## 3. Quick Start on LUMI

### Option A: Command Line / Slurm Batch Execution

Activate the unified LUMI-IQ environment and run:

```bash
module use $HOME/modulefiles
module load Lumi-IQ-qaas/VLQ

# Run on local Aer simulator:
python run_health_vqe.py --backend SIM --max-iters 15

# Or dispatch to real VLQ hardware (uses ~/.lumi-iq/token automatically):
python run_health_vqe.py --backend VLQ --max-iters 20 --shots 256
```

### Option B: Interactive JupyterLab via Open OnDemand

1. Launch JupyterLab on [lumi.csc.fi](https://lumi.csc.fi) using the `lumi-iq` module script.
2. Open `health_vqe.ipynb`.
3. Set `TARGET_BACKEND = "SIM"` or `"VLQ"` and run all cells sequentially.