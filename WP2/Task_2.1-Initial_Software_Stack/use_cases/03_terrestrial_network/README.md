# Use Case 3: Terrestrial Network Routing Optimization

| Item | Details |
|---|---|
| **Author / Lead** | LUMI-IQ Consortium (WP2) |
| **Domain** | Telecommunications & Network Traffic Routing |
| **Quantum Approach** | QUBO Formulation, Ising Mapping, Bias-Field Counterdiabatic Driving (BF-DCQO) & QAOA |
| **Hardware Target** | Qiskit Aer Simulator & IQM Star-Topology Transpilation (`IQMFakeApollo` / VLQ) |
| **Execution Modes** | Standalone Python Script (`run_terrestrial_network.py`) & JupyterLab Notebook (`terrestrial_network.ipynb`) |

---

## 1. Overview

This use case addresses energy-efficient and congestion-aware routing on a terrestrial backbone communication network (derived from the Abilene topology). The problem of selecting optimal network paths under flow conservation and capacity constraints is formulated as a Quadratic Unconstrained Binary Optimization (QUBO) problem and mapped to an Ising Hamiltonian.

The quantum optimization benchmarks:
1. **Bias-Field Digitized Counterdiabatic Quantum Optimization (BF-DCQO):** Shortcuts-to-adiabaticity driving using an adiabatic gauge potential (AGP) with zero classical optimization loops.
2. **Quantum Approximate Optimization Algorithm (QAOA):** Variational ansatz trained via classical COBYLA optimizer.
3. **IQM Native Architecture Transpilation:** Mapping circuits to native IQM Star-topology transmon gates (`CZ`, `PRX`).

---

## 2. Directory Structure

```
03_terrestrial_network/
├── README.md                      # Documentation and execution guide
├── run_terrestrial_network.py     # Standalone CLI / Slurm batch script
├── terrestrial_network.ipynb      # Interactive notebook for LUMI Open OnDemand
├── result_terrestrial_network.png # Benchmark comparison plot (BF-DCQO vs QAOA)
├── data_description.md           # Dataset schema and network parameters
└── dataset/                       # Network topology datasets
    ├── Abilene.gml                # Full network graph definition
    ├── abilene_subgraph_dataset.json # Extracted 7-node subgraph dataset
    └── build_dataset.py           # Dataset extraction and generation script
```

---

## 3. Quick Start on LUMI

### Option A: Command Line / Slurm Batch Execution

Activate the unified LUMI-IQ environment and run:

```bash
module use $HOME/modulefiles
module load lumi-iq

python run_terrestrial_network.py
```

The script builds the QUBO, evaluates the exact ground state, runs the matched-depth BF-DCQO vs. QAOA comparison, transpiles to IQM hardware topology, and outputs `result_terrestrial_network.png`.

### Option B: Interactive JupyterLab via Open OnDemand

1. Launch JupyterLab on [lumi.csc.fi](https://lumi.csc.fi) using the `lumi-iq` module script.
2. Open `terrestrial_network.ipynb`.
3. Run all cells sequentially.
