# LUMI-IQ Work Package 2: Integrated Use Cases

This directory contains the 4 domain-specific quantum use cases of the **LUMI-IQ** project, adapted and standardized to run seamlessly on the **LUMI Supercomputer** and the **Czech National Quantum Computer (VLQ)** using the unified `lumi-iq` software stack.

---

## Standardized Use Case Matrix

Every use case adheres to a strictly unified layout featuring both non-interactive CLI / Slurm scripts and interactive JupyterLab notebooks:

| # | Use Case Directory | Domain & Problem | Quantum Algorithm / Hardware Target | CLI Runner Script | Open OnDemand Notebook | Output Artifact |
|---|---|---|---|---|---|---|
| **1** | **[01_car_manufacturing](01_car_manufacturing/)** | Automotive Quality Assurance (Rare Defect Detection) | 4-qubit `ZZFeatureMap` Quantum Fidelity Statevector Kernel | `python run_car_manufacturing.py` | `car_manufacturing.ipynb` | `result_car_manufacturing.png` |
| **2** | **[02_health_life_science](02_health_life_science/)** | Computational Chemistry (Molecular Ground State Energy) | VQE (`EfficientSU2` ansatz + SPSA) & Classical Shadows Observable Estimation (VLQ QPU & Aer) | `python run_health_vqe.py --backend [SIM\|VLQ]` | `health_vqe.ipynb` | `result_health.png` |
| **3** | **[03_terrestrial_network](03_terrestrial_network/)** | Telecommunications (Energy-Efficient Traffic Routing) | QUBO & Ising Mapping, BF-DCQO vs. QAOA, Native IQM Star Transpilation | `python run_terrestrial_network.py` | `terrestrial_network.ipynb` | `result_terrestrial_network.png` |
| **4** | **[04_qml_time_series](04_qml_time_series/)** | Energy Market Forecasting (Hourly Electricity Prices) | 8-qubit QNN Regressor (`ZFeatureMap` + `EfficientSU2` 80-parameter PQC) | `python run_time_series_forecasting.py` | `time_series_forecasting.ipynb` | `result_time_series.png` |

---

## Universal Execution on LUMI

All four use cases use the single unified `lumi-iq` environment module. No local `venv` or `pip install` commands are needed.

### 1. Terminal / Slurm Batch Execution
```bash
# One-time activation in any session:
module use $HOME/modulefiles
module load lumi-iq

# Run any use case directly:
cd WP2/Task_2.1-Initial_Software_Stack/use_cases/01_car_manufacturing && python run_car_manufacturing.py
cd ../02_health_life_science && python run_health_vqe.py --backend SIM
cd ../03_terrestrial_network && python run_terrestrial_network.py
cd ../04_qml_time_series && python run_time_series_forecasting.py
```

### 2. Interactive JupyterLab on LUMI Open OnDemand (lumi.csc.fi)
1. Start Jupyter on [lumi.csc.fi](https://lumi.csc.fi) with **Custom Python type**: `Script` (`module use $HOME/modulefiles && module load lumi-iq`).
2. Open any `.ipynb` notebook from the directories above.
3. Run all cells sequentially.
