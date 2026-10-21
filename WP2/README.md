# LUMI-IQ Work Package 2: Hybrid Classical/Quantum AI Computations & Software Stack
**Project:** LUMI-IQ  
**Work Package:** Work Package 2 (WP2)  

---

## Directory Organization

This directory contains the code, recipes, benchmarks, and deployment pipelines for **Work Package 2 (WP2)**:

### 1. `Task_2.1-Initial_Software_Stack/` (Primary Operational Suite)
This is the consolidated, production-ready implementation of the LUMI-IQ software stack for LUMI and remote QPUs:
* **Tykky Container Recipes:** [recipes/](Task_2.1-Initial_Software_Stack/recipes/) (`env-initial.yml`, `env-complete.yml`, `env-later-additions.yml`)
* **Module Deployment Scripts:** Tykky containerization (`build_tykky_module.sh`), Lmod registration (`setup_lumi_module.sh`), and shared deployment (`deploy_shared_module.sh`).
* **HPC Slurm Orchestration:** Token-lifetime-aware batch job submitter (`submit_job.py`) and Slurm script (`submit_lumi.sbatch`).
* **Automated Master Test Suite:** `run_all_tests.sh` and `run_all_tests.py` testing the complete software stack and hardware connectivity in simulation (`SIM`) and physical hardware (`VLQ`).
* **Standardized WP2 Use Cases:**
  * **01 Car Manufacturing:** Quantum kernel anomaly detection for manufacturing quality assurance.
  * **02 Health & Life Science:** Variational Quantum Eigensolver (VQE) with Classical Shadows molecular ground-state estimation.
  * **03 Terrestrial Network:** Quantum Key Distribution (QKD) terrestrial optical network routing via QUBO / QAOA.
  * **04 QML Time Series:** Quantum Neural Network (QNN) electricity spot-price forecasting with OTE-CR ground truth.

### 2. Standalone Reference Implementations (`Use_case-*/`)
The `Use_case-*` directories preserve the standalone reference implementations provided by project contributors during earlier prototyping stages:
* `Use_case-Car_Manufacturing/`
* `Use_case-Health_and_Life_science/`
* `Use_case-QML_time_series_forecasting/`
* `Use_case-Terrestial_Network/`

All four use cases have been harmonized and standardized inside `Task_2.1-Initial_Software_Stack/use_cases/` for single-command verification and shared LUMI module execution.
