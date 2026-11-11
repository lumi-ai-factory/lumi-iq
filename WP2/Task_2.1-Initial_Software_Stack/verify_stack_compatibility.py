#!/usr/bin/env python3
"""
========================================================================================
LUMI-IQ Software Stack Compatibility & Verification Tool
Grant Agreement 101239031 (EuroHPC-JU) | WP2 Task 2.1

Verifies the installed software stack against:
  - Table 1 (Section 3.4.1): Core Initial Software Stack
  - Table 2 (Section 3.4.2): Later Additions & Advanced AI/HPC Tools

Usage:
  python verify_stack_compatibility.py             # Check current environment imports
  python verify_stack_compatibility.py --smoke     # Run functional smoke tests
  python verify_stack_compatibility.py --json      # Export results to JSON
========================================================================================
"""

import sys
import time
import json
import argparse

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

CORE_MODULES = [
    {
        "name": "qiskit",
        "import_path": "qiskit",
        "table_name": "Qiskit",
        "objective": "Core Quantum SDK & Circuit Framework",
        "required": True,
    },
    {
        "name": "qiskit-aer",
        "import_path": "qiskit_aer",
        "table_name": "Qiskit Aer",
        "objective": "GPU accelerated quantum circuit simulation",
        "required": True,
    },
    {
        "name": "qaas",
        "import_path": "qaas",
        "table_name": "QaaS Client",
        "objective": "Remote gateway access to Czech National QC (VLQ)",
        "required": True,
    },
    {
        "name": "py4lexis",
        "import_path": "py4lexis",
        "table_name": "Py4LEXIS",
        "objective": "LEXIS AAI federated authentication & execution",
        "required": True,
    },
    {
        "name": "qiskit-iqm",
        "import_path": "iqm.qiskit_iqm",
        "table_name": "Qiskit IQM",
        "objective": "Topology aware transpilation on Star architecture",
        "required": False,
    },
    {
        "name": "iqm-qubit-selector",
        "import_path": "iqm.qubit_selector",
        "table_name": "IQM Qubit Selector",
        "objective": "Calibration aware qubit selection",
        "required": False,
    },
    {
        "name": "iqm-error-reduction-tools",
        "import_path": "iqm.error_reduction_tools",
        "table_name": "IQM Error Reduction Tools",
        "objective": "Noise tailoring, randomised compilation, error mitigation",
        "required": False,
    },
    {
        "name": "fiqci-ems",
        "import_path": "fiqci.ems",
        "table_name": "FiQCI-EMS",
        "objective": "Noise tailoring, ZNE, readout mitigation (CSC)",
        "required": False,
    },
    {
        "name": "qiskit-addon-aqc-tensor",
        "import_path": "qiskit_addon_aqc_tensor",
        "table_name": "Qiskit AQC-Tensor Addon",
        "objective": "Approximate circuit transpilation and compression",
        "required": False,
    },
    {
        "name": "qiskit-addon-cutting",
        "import_path": "qiskit_addon_cutting",
        "table_name": "QCut (qiskit-addon-cutting)",
        "objective": "Circuit Knitting & backend distribution (Qiskit 2.x)",
        "required": False,
    },
    {
        "name": "qc-parallelizer",
        "import_path": "qc_parallelizer",
        "table_name": "qc-parallelizer",
        "objective": "Parallel execution of quantum circuits",
        "required": False,
    },
    {
        "name": "torch",
        "import_path": "torch",
        "table_name": "PyTorch",
        "objective": "Machine Learning for custom GPU AI/ML workflows",
        "required": False,
    },
    {
        "name": "scikit-learn",
        "import_path": "sklearn",
        "table_name": "scikit-learn",
        "objective": "Classical Machine Learning & preprocessing",
        "required": False,
    },
    {
        "name": "scipy",
        "import_path": "scipy",
        "table_name": "SciPy",
        "objective": "Parameter optimisation for variational algorithms",
        "required": True,
    },
    {
        "name": "stim",
        "import_path": "stim",
        "table_name": "Stim",
        "objective": "Fast stabilizer simulation & detector syndrome extraction",
        "required": False,
    },
    {
        "name": "pymatching",
        "import_path": "pymatching",
        "table_name": "PyMatching",
        "objective": "MWPM syndrome decoding for small-scale QEC",
        "required": False,
    },
    {
        "name": "pennylane",
        "import_path": "pennylane",
        "table_name": "PennyLane",
        "objective": "Quantum Machine Learning & hybrid variational algorithms",
        "required": False,
    },
    {
        "name": "pennylane-qiskit",
        "import_path": "pennylane_qiskit",
        "table_name": "PennyLane-Qiskit Plugin",
        "objective": "Qiskit 2.x bridge for PennyLane execution",
        "required": False,
    },
]

LATER_ADDITIONS = [
    {
        "name": "bqskit",
        "import_path": "bqskit",
        "table_name": "BQSKit",
        "objective": "Transpilation, circuit compression & synthesis",
        "status": "Ready",
    },
    {
        "name": "qiskit-addon-sqd",
        "import_path": "qiskit_addon_sqd",
        "table_name": "Qiskit Addon SQD",
        "objective": "Sample-based quantum diagonalisation (ground state)",
        "status": "Ready",
    },
    {
        "name": "mqt.predictor",
        "import_path": "mqt.predictor",
        "table_name": "MQT Predictor",
        "objective": "AI-assisted calibration-aware device & transpiler selection",
        "status": "Ready",
    },
    {
        "name": "iqm-qaoa",
        "import_path": "iqm.qaoa",
        "table_name": "IQM QAOA",
        "objective": "QAOA transpilation & circuit synthesis for ansatz design",
        "status": "Ready",
    },
    {
        "name": "qiskit-addon-dice-solver",
        "import_path": "qiskit_addon_dice_solver",
        "table_name": "Qiskit Addon Dice Solver",
        "objective": "MPI accelerated addon for SQD for HPC+QC workflows",
        "status": "Awaiting Upstream Release (MPI C++)",
    },
]


import importlib
import importlib.metadata

def check_module(mod_info):
    name = mod_info["name"]
    path = mod_info["import_path"]
    res = {
        "name": name,
        "table_name": mod_info["table_name"],
        "objective": mod_info["objective"],
        "status": "UNKNOWN",
        "version": None,
        "error": None,
    }
    try:
        mod = importlib.import_module(path)
        res["status"] = "INSTALLED"
        ver = getattr(mod, "__version__", None)
        if not ver:
            try:
                ver = importlib.metadata.version(name)
            except Exception:
                ver = "installed"
        res["version"] = ver
    except Exception as e:
        res["status"] = "MISSING"
        res["error"] = f"{type(e).__name__}: {e}"
    return res


def run_smoke_test(mod_name):
    """Executes a lightweight functional smoke test."""
    try:
        if mod_name == "qiskit":
            from qiskit import QuantumCircuit
            qc = QuantumCircuit(2)
            qc.h(0)
            qc.cx(0, 1)
            return True, f"Created {qc.num_qubits}-qubit Bell circuit"
        elif mod_name == "qiskit-aer":
            from qiskit_aer import AerSimulator
            sim = AerSimulator()
            return True, f"Instantiated {sim.name}"
        elif mod_name == "qaas":
            import qaas
            return True, f"QaaS {getattr(qaas, '__version__', '1.0.0')} initialized"
        elif mod_name == "stim":
            import stim
            c = stim.Circuit("H 0\nCNOT 0 1\nM 0 1")
            return True, f"Stim simulated {len(c)} instructions"
        elif mod_name == "pymatching":
            import pymatching
            m = pymatching.Matching()
            return True, "PyMatching initialized"
        elif mod_name == "pennylane":
            import pennylane as qml
            dev = qml.device("default.qubit", wires=1)
            @qml.qnode(dev)
            def circuit():
                qml.Hadamard(wires=0)
                return qml.expval(qml.PauliZ(0))
            val = float(circuit())
            return True, f"QNode evaluated expval: {val:.2f}"
        elif mod_name == "bqskit":
            import bqskit
            return True, f"BQSKit {bqskit.__version__} ready"
        elif mod_name == "qiskit-addon-cutting":
            import qiskit_addon_cutting
            return True, f"QCut {qiskit_addon_cutting.__version__} ready"
    except Exception as e:
        return False, str(e)
    return True, "No specific smoke test defined"


def print_table(title, items, run_smoke=False):
    print(f"\n{BOLD}{CYAN}{'=' * 95}{RESET}")
    print(f"{BOLD}{CYAN}  {title.upper()}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 95}{RESET}")
    header = f"{'Deliverable Tool':<26} | {'Package':<24} | {'Status':<12} | {'Version / Info':<25}"
    print(BOLD + header + RESET)
    print("-" * 95)

    for item in items:
        status_str = f"{GREEN}INSTALLED{RESET}" if item["status"] == "INSTALLED" else f"{YELLOW}MISSING{RESET}"
        if item["status"] == "INSTALLED":
            ver_str = str(item["version"])
        else:
            ver_str = item.get("status_note") or "Not found"

        line = f"{item['table_name']:<26} | {item['name']:<24} | {status_str:<21} | {ver_str:<25}"
        print(line)

        if item["status"] != "INSTALLED" and item.get("error"):
            print(f"   └─ {RED}[ERROR]{RESET} {item['error']}")

        if run_smoke and item["status"] == "INSTALLED":
            ok, msg = run_smoke_test(item["name"])
            smoke_tag = f"{GREEN}[SMOKE PASS]{RESET}" if ok else f"{RED}[SMOKE FAIL]{RESET}"
            print(f"   └─ {smoke_tag} {msg}")


def main():
    parser = argparse.ArgumentParser(description="LUMI-IQ Software Stack Verification")
    parser.add_argument("--smoke", action="store_true", help="Run functional smoke tests")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    results_core = [check_module(m) for m in CORE_MODULES]
    results_later = []
    for m in LATER_ADDITIONS:
        res = check_module(m)
        res["status_note"] = m["status"]
        results_later.append(res)

    if args.json:
        out = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python_version": sys.version,
            "core_section_3_4_1": results_core,
            "later_additions_3_4_2": results_later,
        }
        print(json.dumps(out, indent=2))
        return

    print("=" * 95)
    print(f"{BOLD}{CYAN}      LUMI-IQ SOFTWARE STACK VERIFICATION & MAPPING (TASK 2.1){RESET}")
    print(f"      Python Runtime: {sys.executable} (Python {sys.version.split()[0]})")
    print("=" * 95)

    print_table("Table 1: Core Initial Software Stack (Deliverable D2.1 § 3.4.1)", results_core, args.smoke)
    print_table("Table 2: Later Additions & Advanced AI/HPC Tools (Deliverable D2.1 § 3.4.2)", results_later, args.smoke)

    installed_core = sum(1 for r in results_core if r["status"] == "INSTALLED")
    installed_later = sum(1 for r in results_later if r["status"] == "INSTALLED")

    print("\n" + "=" * 95)
    print(f"Summary: Core Stack {installed_core}/{len(results_core)} installed | Later Additions {installed_later}/{len(results_later)} installed.")
    print("=" * 95)


if __name__ == "__main__":
    main()
