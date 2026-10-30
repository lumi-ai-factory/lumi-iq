# LUMI-IQ Work Package 2: Integrated Use Cases

This directory contains the 4 domain-specific quantum use cases of the **LUMI-IQ** project, adapted and standardized to run seamlessly on the **LUMI Supercomputer** and the **Czech National Quantum Computer (VLQ)** using the unified `lumi-iq` software stack.

---

## 1. Hardware Execution Model: Why & How Each Use Case Runs on VLQ

The **VLQ** quantum processor at IT4Innovations is a **24-qubit Star-topology transmon QPU** with native single-qubit rotations (`PRX`) and two-qubit controlled-Z gates (`CZ`).

All 4 use cases require between **4 and 8 qubits**, making them an architectural match for VLQ. To maximize performance and respect queue limits, each use case implements an intelligent **hybrid classical-quantum execution partitioning**:

| # | Use Case | Qubits | Classical HPC Role (LUMI) | Quantum QPU Role (VLQ) | Real VLQ Command |
|---|---|---|---|---|---|
| **1** | **[01_car_manufacturing](01_car_manufacturing/)** | 4 Qubits | Full dataset baseline training and classical baselines (SVM, Isolation Forest) | Evaluates 4-qubit overlap fidelity circuits $U(x_{\text{ref}})^\dagger U(x_{\text{test}})$ on VLQ QPU | `python run_car_manufacturing.py --backend VLQ` |
| **2** | **[02_health_life_science](02_health_life_science/)** | 4 Qubits | PySCF Hartree-Fock calculation, active space selection, Jordan-Wigner Hamiltonian | Executes VQE parameter optimization and Classical Shadows snapshot measurements | `python run_health_vqe.py --backend VLQ` |
| **3** | **[03_terrestrial_network](03_terrestrial_network/)** | 8 Qubits | QUBO formulation, Ising Hamiltonian mapping, and analytical parameter calculation | Evaluates 8-qubit BF-DCQO routing circuit transpiled to native IQM Star gates (`CZ`, `PRX`) | `python run_terrestrial_network.py --backend VLQ` |
| **4** | **[04_qml_time_series](04_qml_time_series/)** | 8 Qubits | COBYLA optimization of 80 variational $\theta$ parameters on CPU | Dispatches the 1-hour ahead price forecast circuit to VLQ, measuring $\langle Z_0 \rangle$ | `python run_time_series_forecasting.py --backend VLQ` |
| **5** | **[05_small_scale_qec](05_small_scale_qec/)** | 5 Qubits | Stabilizer simulation (Stim), noise injection, and MWPM syndrome decoding (PyMatching) | Evaluates 5-qubit repetition code on VLQ QPU / Aer SIM with syndrome ancilla readout | `python run_small_scale_qec.py --backend VLQ` |

---

## 2. Standardized Directory Layout

Every use case folder adheres to a strictly identical architecture:

```
use_cases/<use_case_dir>/
├── README.md               # Dedicated documentation and execution guide
├── run_<name>.py           # Standalone Python script with '--backend SIM' and '--backend VLQ'
├── <name>.ipynb            # Interactive notebook for LUMI Open OnDemand JupyterLab
└── result_<name>.png       # Standardized benchmark evaluation visualization
```

---

## 3. Universal Execution on LUMI

All four use cases use the single unified `Lumi-IQ-qaas/VLQ` environment module. No local `venv` or `pip install` commands are needed.

### Terminal / Slurm Batch Execution
```bash
# 1. Activate module in any terminal session:
module use $HOME/modulefiles
module load Lumi-IQ-qaas/VLQ

# 2. Run on local simulator (fast test, no credentials required):
cd WP2/Task_2.1-Initial_Software_Stack/use_cases/01_car_manufacturing && python run_car_manufacturing.py --backend SIM
cd ../02_health_life_science && python run_health_vqe.py --backend SIM
cd ../03_terrestrial_network && python run_terrestrial_network.py --backend SIM
cd ../04_qml_time_series && python run_time_series_forecasting.py --backend SIM

# 3. Or submit directly to real VLQ hardware:
# Set your allocated LEXIS project and authenticate once:
export LEXIS_PROJECT=vlq_demo_project
python ../../auth.py

# Execute use cases on VLQ (uses ~/.lumi-iq/token automatically):
python run_car_manufacturing.py --backend VLQ
python run_health_vqe.py --backend VLQ --shots 256
python run_terrestrial_network.py --backend VLQ --shots 1024
python run_time_series_forecasting.py --backend VLQ --shots 1024
```

### Interactive JupyterLab on LUMI Open OnDemand (lumi.csc.fi)
1. Start Jupyter on [lumi.csc.fi](https://lumi.csc.fi) with **Custom Python type**: `Script` (`module use $HOME/modulefiles && module load Lumi-IQ-qaas/VLQ`).
2. Open any `.ipynb` notebook from the directories above.
3. Toggle `TARGET_BACKEND = "SIM"` or `"VLQ"` in the setup cell and run all cells sequentially.

---

## 4. Submitting as an Unattended Slurm HPC Job on LUMI

In compliance with LUMI fair-use policy, production and heavy classical computation can be submitted directly to Slurm compute nodes with QPU offload via `submit_job.py`:

```bash
cd WP2/Task_2.1-Initial_Software_Stack

# Submit individual use cases to Slurm with real VLQ QPU offload:
python submit_job.py --use-case 1 --backend VLQ   # Car Manufacturing
python submit_job.py --use-case 2 --backend VLQ   # Health Life Science VQE
python submit_job.py --use-case 3 --backend VLQ   # Terrestrial Network Routing
python submit_job.py --use-case 4 --backend VLQ   # QML Time Series

# Submit all 4 use cases & master test suite to Slurm:
python submit_job.py --use-case all --backend VLQ
# (or: bash run_all_tests.sh --backend VLQ --slurm)
```

