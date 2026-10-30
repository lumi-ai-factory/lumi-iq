#!/usr/bin/env python3
"""
LUMI-IQ Initial Software Stack Verification Script
Tests all tools from Deliverable ED2.1 Table 11 (3.4.1 Initial Software)
and physical VLQ hardware connectivity clients.

Features:
- Flavor selection: --flavor vlq (physical hardware) or --flavor sim (simulation)
- Auto-detection: dynamically detects whether VLQ or SIM module is active
- Module Discovery: scans and displays available LUMI-IQ modules (--list-modules)
"""

import argparse
import importlib
import os
import sys

# ==============================================================================
# TOOL DEFINITIONS (Deliverable D2.1 Table 11 & Table 12)
# ==============================================================================

# Core tools common to both VLQ and SIM environments (Table 11)
COMMON_CORE_TOOLS = [
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
]

# Hardware-specific tools for physical VLQ offload (Table 11 Production Gateway)
VLQ_HARDWARE_TOOLS = [
    ("QaaS Client (Hardware VLQ)", "qaas", "Direct execution client on Czech National Quantum Computer"),
    ("py4lexis (AAI Gateway)", "py4lexis", "LEXIS authentication and job staging gateway"),
]

# Simulation-specific tools (Section 3.4.1 Note: supported in SIM)
SIM_SPECIFIC_TOOLS = [
    ("IQM Error Reduction Tools", "iqm.error_reduction_tools", "Noise tailoring, randomised compilation (SIM supported)"),
]

# Later additions and advanced extensions (Table 12)
LATER_ADDITIONS = [
    ("IQM QAOA", "iqm_qaoa", "Domain-specific QAOA circuit synthesis & ansatz design"),
]

# ==============================================================================
# MODULE DISCOVERY & INSPECTION
# ==============================================================================

def find_available_modules():
    """Scans cluster and user module search paths for LUMI-IQ modulefiles."""
    search_paths = [
        "/appl/local/lumiiq/modulefiles",
        "/pfs/lustrep1/appl/local/lumiiq/modulefiles",
        "/pfs/lustrep2/appl/local/lumiiq/modulefiles",
        "/pfs/lustrep3/appl/local/lumiiq/modulefiles",
        "/pfs/lustrep4/appl/local/lumiiq/modulefiles",
        os.path.expanduser("~/modulefiles"),
        os.path.abspath("modules/modulefiles"),
        os.path.abspath("appl/local/lumiiq/modulefiles"),
    ] + [p for p in os.environ.get("MODULEPATH", "").split(":") if p]

    found = {}
    for base in search_paths:
        if os.path.isdir(base):
            for root, _, files in os.walk(base):
                for f in sorted(files):
                    if f.endswith(".lua"):
                        rel = os.path.relpath(os.path.join(root, f), base)
                        mod_name = rel[:-4]
                        full_path = os.path.join(root, f)
                        # Filter strictly to LUMI-IQ modules
                        if "lumi-iq" not in mod_name.lower() and "lumiiq" not in full_path.lower():
                            continue
                        origin = "User" if base.startswith(os.path.expanduser("~")) else "Shared"
                        display_name = f"{mod_name} [{origin}]"
                        if display_name not in found:
                            found[display_name] = (full_path, mod_name, origin)
    return found

def get_loaded_modules():
    """Returns a list of currently loaded Lmod modules."""
    loaded = []
    lm = os.environ.get("LOADEDMODULES", "")
    if lm:
        loaded.extend([m for m in lm.split(":") if m])
    lm_files = os.environ.get("_LMFILES_", "")
    if lm_files:
        for f in lm_files.split(":"):
            if "Lumi-IQ" in f or "lumi-iq" in f:
                base = os.path.basename(f)
                if base.endswith(".lua"):
                    base = base[:-4]
                parent = os.path.basename(os.path.dirname(f))
                loaded.append(f"{parent}/{base}")
    return list(dict.fromkeys(loaded))

def print_modules_listing(full=False):
    """Prints a structured view of available and active LUMI-IQ modules."""
    modules = find_available_modules()
    loaded = get_loaded_modules()

    print("\n" + "=" * 80)
    print("               LUMI-IQ ENVIRONMENT MODULES: DISCOVERY & STATUS")
    print("=" * 80)
    
    iq_loaded = [m for m in loaded if "lumi-iq" in m.lower() or "lumiiq" in m.lower()]
    if iq_loaded:
        print("  Active LUMI-IQ Module(s):")
        for m in iq_loaded:
            print(f"    -> [ ACTIVE ] {m}")
    else:
        print("  Active LUMI-IQ Module(s): None detected in current shell session.")

    print("-" * 80)
    print("  Available Modules on System:")
    if not modules:
        print("    [ INFO ] No pre-configured modulefiles found in standard paths.")
        print("             Run 'module use /appl/local/lumiiq/modulefiles' on LUMI.")
    else:
        for display_name, (path, mod_name, origin) in sorted(modules.items()):
            is_active = any(mod_name.lower() in l.lower() for l in loaded)
            status = "[ ACTIVE ]" if is_active else "[ AVAIL  ]"
            desc = ""
            if "vlq" in mod_name.lower():
                desc = "Physical VLQ 24-Qubit Star QPU execution"
            elif "sim" in mod_name.lower():
                desc = "High-performance local CPU/GPU simulation"
            print(f"    {status}  {display_name:<30} | {desc}")
            if full:
                print(f"                Path: {path}")

    print("-" * 80)
    print("  HOW TO LOAD / SWITCH MODULES ON LUMI:")
    print("    module use /appl/local/lumiiq/modulefiles")
    print("    module load Lumi-IQ-qaas/VLQ   # Physical hardware offload (Czech National QC)")
    print("    module load Lumi-IQ-qaas/SIM   # High-performance local simulation (No tokens needed)")
    print("=" * 80 + "\n")

# ==============================================================================
# FLAVOR DETECTION
# ==============================================================================

def detect_flavor():
    """Auto-detects whether the current environment represents VLQ or SIM flavor."""
    loaded = get_loaded_modules()
    for m in loaded:
        if "sim" in m.lower():
            return "sim", f"Active Lmod module '{m}'"
        if "vlq" in m.lower():
            return "vlq", f"Active Lmod module '{m}'"

    exe = sys.executable.lower()
    if "sim" in exe:
        return "sim", f"Python executable path ({sys.executable})"
    if "vlq" in exe or "lumi-iq-env" in exe:
        return "vlq", f"Python executable path ({sys.executable})"

    try:
        importlib.import_module("qaas")
        return "vlq", "QaaS hardware client detected in Python environment"
    except Exception:
        return "sim", "Simulation baseline (QaaS hardware client not present)"

# ==============================================================================
# TOOL VERIFICATION
# ==============================================================================

def check_tool(name, mod, desc):
    """Imports a tool candidate and returns (status, error, version)."""
    candidates = [mod]
    if name == "FiQCI-EMS":
        candidates = ["fiqci.ems", "fiqci", "fiqci_ems"]
    elif name == "QCut":
        candidates = ["qiskit_addon_cutting", "circuit_knitting_toolbox"]
    elif name == "IQM Qubit Selector":
        candidates = ["iqm.qubit_selector", "iqm.qubit_selector.qubit_selector"]
    elif name == "IQM Error Reduction Tools":
        candidates = ["iqm_error_reduction_tools", "iqm.error_reduction_tools", "iqm.error_reduction"]
    elif name == "IQM QAOA":
        candidates = ["iqm_qaoa", "qiskit_algorithms.minimum_eigensolvers.qaoa"]

    last_err = None
    for c in candidates:
        try:
            m = importlib.import_module(c)
            ver = getattr(m, "__version__", None)
            ver_str = f"v{ver}" if ver else ""
            return True, None, ver_str
        except Exception as e:
            last_err = e
            continue
    return False, last_err, ""

# ==============================================================================
# MAIN RUNNER
# ==============================================================================

def run_tests(flavor, verbose=False):
    auto_flavor, reason = detect_flavor()
    selected_flavor = flavor if flavor != "auto" else auto_flavor

    print("\n" + "=" * 80)
    print("       LUMI-IQ INITIAL SOFTWARE STACK: VERIFICATION TEST (D2.1 TABLE 11)")
    print("=" * 80)
    print(f"  Target Flavor    : {selected_flavor.upper()}")
    print(f"  Selection Reason : {'Explicitly requested by user' if flavor != 'auto' else reason}")
    
    # Active modules summary
    loaded = get_loaded_modules()
    iq_loaded = [m for m in loaded if "lumi-iq" in m.lower() or "lumiiq" in m.lower()]
    if iq_loaded:
        print(f"  Active Module(s) : {', '.join(iq_loaded)}")
    print("-" * 80)

    # Determine core tool suite based on flavor
    if selected_flavor == "vlq":
        core_tools = COMMON_CORE_TOOLS + VLQ_HARDWARE_TOOLS
        later_tools = [
            ("IQM Error Reduction Tools", "iqm.error_reduction_tools", "Table 12 Later Addition (Deferred for remote VLQ gateway, supported in SIM)")
        ] + LATER_ADDITIONS
    elif selected_flavor == "sim":
        core_tools = COMMON_CORE_TOOLS + SIM_SPECIFIC_TOOLS
        later_tools = LATER_ADDITIONS
    else: # all
        core_tools = COMMON_CORE_TOOLS + VLQ_HARDWARE_TOOLS + SIM_SPECIFIC_TOOLS
        later_tools = LATER_ADDITIONS

    passed = 0
    failed = 0

    print(f"  Core Initial Software Stack ({selected_flavor.upper()} Target):")
    for name, mod, desc in core_tools:
        ok, err, ver = check_tool(name, mod, desc)
        if ok:
            ver_disp = f"({ver})" if ver and verbose else ""
            print(f"  [ PASS ] {name:<30} {ver_disp:<10} | {desc[:38]}")
            passed += 1
        else:
            print(f"  [ FAIL ] {name:<30}            | Error: {err}")
            failed += 1

    # Informative & Later additions section
    print("-" * 80)
    print("  Additions, Extensions & Cross-Environment Status:")
    for name, mod, desc in later_tools:
        ok, _, ver = check_tool(name, mod, desc)
        if ok:
            ver_disp = f"({ver})" if ver and verbose else ""
            print(f"  [ PASS ] {name:<30} {ver_disp:<10} | Active in environment")
        else:
            print(f"  [ INFO ] {name:<30}            | {desc[:42]}")

    # For SIM flavor: show explicit info that hardware QaaS/LEXIS is skipped
    if selected_flavor == "sim":
        for name, mod, desc in VLQ_HARDWARE_TOOLS:
            print(f"  [ SKIP ] {name:<30}            | Standalone SIM (Hardware tokens not required)")

    print("=" * 80)
    print(f"Summary: {passed} / {len(core_tools)} core tools verified successfully for {selected_flavor.upper()}.")
    print("=" * 80 + "\n")

    return 0 if failed == 0 else 1

def main():
    parser = argparse.ArgumentParser(
        description="LUMI-IQ Initial Software Stack Verification & Module Discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python test_stack.py                  # Auto-detects flavor from active module
  python test_stack.py --flavor vlq     # Verifies VLQ hardware offload stack (Table 11)
  python test_stack.py --flavor sim     # Verifies standalone SIM simulation stack
  python test_stack.py --list-modules   # Scans and lists available cluster modules
"""
    )
    parser.add_argument(
        "-f", "--flavor",
        choices=["auto", "vlq", "sim", "all"],
        default="auto",
        help="Software stack flavor to verify (default: auto-detect)"
    )
    parser.add_argument(
        "-l", "--list-modules",
        action="store_true",
        help="Scan and list all available LUMI-IQ modules on system and exit"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Display detected version strings and detailed paths"
    )

    args = parser.parse_args()

    if args.list_modules:
        print_modules_listing(full=True)
        return 0

    return run_tests(flavor=args.flavor, verbose=args.verbose)

if __name__ == "__main__":
    sys.exit(main())
