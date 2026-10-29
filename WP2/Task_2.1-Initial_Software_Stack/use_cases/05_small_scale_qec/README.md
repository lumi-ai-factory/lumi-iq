# Small-Scale Quantum Error Correction (QEC) Demonstration

This module implements and validates the **small-scale Quantum Error Correction (QEC)** capabilities of the LUMI-IQ Task 2.1 software stack, fulfilling the project proposal commitment:
> *"Quantum Error Correction (QEC) will be enabled at a small scale."*

## Architecture & Components

The demonstration combines high-performance stabilizer simulation and graph-based syndrome decoding with portable Qiskit circuit execution:

1. **Stim Stabilizer Simulation (`stim`)**:
   - Ultra-fast Clifford circuit simulation and Pauli noise propagation.
   - Generates distance-3 (and configurable distance-$d$) repetition and stabilizer codes.
   - Extracts detector error models (DEM) and syndrome detection defect events.

2. **Minimum-Weight Perfect Matching Decoding (`pymatching`)**:
   - Graph-based syndrome decoding using Blossom/MWPM algorithms.
   - Decodes syndromes across thousands of Monte Carlo shots in milliseconds.
   - Quantifies logical error rates ($P_L$) versus physical injected error rates ($p$).

3. **Portable Qiskit Repetition Code**:
   - 3-qubit bit-flip code with 2 syndrome ancilla qubits (5 qubits total).
   - Compatible with the IQM Star architecture of the Czech National Quantum Computer (VLQ) and LUMI GPU nodes via Qiskit Aer.
   - Automatically localizes bit-flip errors and recovers the logical state.

## Execution

### Run on Local Simulator (LUMI Node)
```bash
python run_small_scale_qec.py --backend SIM --shots 2048
```

### Run on Physical Hardware (Czech National QC - VLQ)
```bash
python run_small_scale_qec.py --backend VLQ --shots 1024
```
