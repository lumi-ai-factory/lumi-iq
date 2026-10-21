# Use Case 3: Terrestrial Network Routing Optimization

| Item | Details |
|---|---|
| **Author / Lead** | LUMI-IQ Consortium (WP2) |
| **Domain** | Telecommunications & Network Traffic Routing |
| **Quantum Approach** | QUBO Formulation, Ising Mapping, Bias-Field Counterdiabatic Driving (BF-DCQO) & QAOA |
| **Hardware Target** | Local Simulator (`SIM` via Qiskit Aer) or Real QPU (`VLQ` 24-qubit Star topology at IT4Innovations) |
| **Execution Modes** | Standalone Python Script (`run_terrestrial_network.py`) & JupyterLab Notebook (`terrestrial_network.ipynb`) |

---

## 1. Overview

This use case addresses energy-efficient and congestion-aware routing on a terrestrial backbone communication network (derived from the Abilene topology). The problem of selecting optimal network paths under flow conservation and capacity constraints is formulated as a Quadratic Unconstrained Binary Optimization (QUBO) problem and mapped to an Ising Hamiltonian.

The quantum optimization benchmarks:
1. **Bias-Field Digitized Counterdiabatic Quantum Optimization (BF-DCQO):** Shortcuts-to-adiabaticity driving using an adiabatic gauge potential (AGP) with zero classical optimization loops.
2. **Quantum Approximate Optimization Algorithm (QAOA):** Variational ansatz trained via classical COBYLA optimizer.
3. **IQM Native Architecture Transpilation:** Mapping circuits to native IQM Star-topology transmon gates (`CZ`, `PRX`).

---

## 2. Hardware Execution: Why & How It Runs on VLQ

* **Hardware Compatibility:** The routing instance on the Abilene 7-node subgraph requires **8 qubits**, fitting comfortably onto the **24-qubit VLQ QPU**.
* **Zero-Classical-Iteration Advantage:** Unlike QAOA (which requires ~100 classical optimizer evaluations on the QPU), **BF-DCQO at $p=1$ has zero training iterations** — the circuit parameters are calculated analytically from the network topology.
* **Direct Execution (`--backend VLQ`):** A single 8-qubit BF-DCQO circuit is transpiled to VLQ native gates (`CZ`, `PRX`) and executed with 1024 shots to sample the optimal path (Chicago &rarr; New York &rarr; Washington DC) directly from the quantum hardware.

---

## 3. Directory Structure

```
03_terrestrial_network/
├── README.md                      # Documentation and execution guide
├── run_terrestrial_network.py     # Standalone CLI / Slurm batch script (--backend SIM | VLQ)
├── terrestrial_network.ipynb      # Interactive notebook for LUMI Open OnDemand
├── result_terrestrial_network.png # Benchmark comparison plot (BF-DCQO vs QAOA)
├── data_description.md           # Dataset schema and network parameters
└── dataset/                       # Network topology datasets
    ├── Abilene.gml                # Full network graph definition
    ├── abilene_subgraph_dataset.json # Extracted 7-node subgraph dataset
    └── build_dataset.py           # Dataset extraction and generation script
```

---

## 4. Quick Start on LUMI

### Option A: Command Line / Slurm Batch Execution

Activate the unified LUMI-IQ environment:

```bash
module use $HOME/modulefiles
module load Lumi-IQ-qaas/VLQ

# Run local benchmark on LUMI CPU (Aer simulator):
python run_terrestrial_network.py --backend SIM

# Or execute the 8-qubit routing circuit directly on the real VLQ QPU:
python run_terrestrial_network.py --backend VLQ --shots 1024
```

### Option B: Interactive JupyterLab via Open OnDemand

1. Launch JupyterLab on [lumi.csc.fi](https://lumi.csc.fi) using the `lumi-iq` module script.
2. Open `terrestrial_network.ipynb`.
3. Set `TARGET_BACKEND = "SIM"` or `"VLQ"` and run all cells sequentially.
