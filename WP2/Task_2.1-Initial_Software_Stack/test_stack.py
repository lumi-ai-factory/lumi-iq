#!/usr/bin/env python3
"""
LUMI-IQ Initial Software Stack Verification Script
Tests all tools from Deliverable ED2.1 Table 11 (3.4.1 Initial Software)
and physical VLQ hardware connectivity clients.
"""

import importlib
import sys

# Core Initial Software Stack (Table 11 + Hardware Gateway)
CORE_TOOLS_TABLE = [
    ("Qiskit IQM", "iqm.qiskit_iqm", "Topology aware transpilation on Star architecture"),
    ("Qiskit Aer", "qiskit_aer", "GPU accelerated quantum circuit simulation"),
    ("IQM Qubit Selector", "iqm.qubit_selector", "Calibration aware qubit selection"),
    ("FiQCI-EMS", "fiqci_ems", "Noise tailoring, Clifford Data Regression, ZNE"),
    ("Qiskit AQC-Tensor Addon", "qiskit_addon_aqc_tensor", "Approximate circuit transpilation and compression"),
    ("QCut", "qiskit_addon_cutting", "Circuit Knitting & partitioning"),
    ("qc-parallelizer", "qc_parallelizer", "Parallel execution of quantum circuits"),
    ("PyTorch", "torch", "GPU accelerated AI/ML workflows"),
    ("scikit-learn", "sklearn", "Machine Learning AI/ML workflows"),
    ("SciPy", "scipy", "Parameter optimisation"),
    ("Stim", "stim", "Fast stabilizer circuit simulation for QEC"),
    ("PyMatching", "pymatching", "MWPM syndrome decoding for QEC"),
    ("Pennylane / Pennylane-IQM", "pennylane", "Quantum Machine Learning & hybrid variational"),
    ("QaaS Client (Hardware VLQ)", "qaas", "Direct execution client on Czech National Quantum Computer"),
    ("py4lexis (AAI Gateway)", "py4lexis", "LEXIS authentication and job staging gateway"),
]

# Section 3.4.2 Later Additions (validated when advanced recipes are loaded)
LATER_ADDITIONS_TABLE = [
    ("IQM Error Reduction Tools", "iqm.error_reduction_tools", "Noise tailoring, randomised compilation"),
    ("IQM QAOA", "iqm_qaoa", "QAOA optimised transpilation, circuit synthesis"),
]

def check_tool(name, mod, desc):
    candidates = [mod]
    if name == "FiQCI-EMS":
        candidates = ["fiqci.ems", "fiqci", "fiqci_ems"]
    elif name == "QCut":
        candidates = ["qiskit_addon_cutting", "circuit_knitting_toolbox"]
    elif name == "IQM Qubit Selector":
        candidates = ["iqm.qubit_selector", "iqm.qubit_selector.qubit_selector"]
    elif name == "IQM Error Reduction Tools":
        candidates = ["iqm.error_reduction_tools", "iqm.error_reduction"]
    elif name == "IQM QAOA":
        candidates = ["iqm_qaoa", "qiskit_algorithms.minimum_eigensolvers.qaoa"]

    for c in candidates:
        try:
            importlib.import_module(c)
            return True, None
        except Exception as e:
            last_err = e
            continue
    return False, last_err

def main():
    print("\n" + "=" * 80)
    print("       LUMI-IQ INITIAL SOFTWARE STACK: VERIFICATION TEST (D2.1 TABLE 11)")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for name, mod, desc in CORE_TOOLS_TABLE:
        ok, err = check_tool(name, mod, desc)
        if ok:
            print(f"  [ PASS ] {name:<30} | {desc[:42]}")
            passed += 1
        else:
            print(f"  [ FAIL ] {name:<30} | Error: {err}")
            failed += 1
            
    print("-" * 80)
    print("  Later Additions (Table 12 / Optional Advanced AI Extensions):")
    for name, mod, desc in LATER_ADDITIONS_TABLE:
        ok, _ = check_tool(name, mod, desc)
        if ok:
            print(f"  [ PASS ] {name:<30} | Active in environment")
        else:
            print(f"  [ INFO ] {name:<30} | Table 12 Later Addition (Deferred)")

    print("=" * 80)
    print(f"Summary: {passed} / {len(CORE_TOOLS_TABLE)} core tools verified successfully.")
    print("=" * 80 + "\n")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
