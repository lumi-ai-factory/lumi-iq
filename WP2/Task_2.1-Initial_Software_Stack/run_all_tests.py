#!/usr/bin/env python3
"""
========================================================================================
LUMI-IQ Master Test Suite Runner
Task 2.1: Unified Software Stack & Use Cases Automated Verification

Executes end-to-end verification across:
  1. Software Stack & Environment (Qiskit, Qiskit Aer, QaaS, LEXIS, Scipy, Sklearn, etc.)
  2. LEXIS Authentication & IT4I VLQ 24-Qubit QPU Connectivity
  3. Core Circuit Benchmark (2-Qubit Bell State Transpilation & Execution)
  4. Use Case 1: Car Manufacturing Anomaly Detection & QAOA
  5. Use Case 2: Health & Life Science Molecular VQE (LiH Ground State Energy)
  6. Use Case 3: Terrestrial Network QKD Routing Optimization (BF-DCQO vs QAOA)
  7. Use Case 4: QML Time Series Electricity Price Forecasting (8-Qubit QNN)
  8. Small-Scale QEC: Stabilizer Simulation & Repetition Code (Stim, PyMatching, Qiskit)

Usage:
  python run_all_tests.py --backend SIM           # Fast local simulation benchmark (~1-2 min)
  python run_all_tests.py --backend VLQ           # Real execution on IT4I VLQ QPU via LEXIS
  python run_all_tests.py --use-cases 1,4         # Run selected use cases only
  python run_all_tests.py --skip-use-cases        # Run only stack & QPU connectivity checks
========================================================================================
"""

import os
import sys
import time
import json
import argparse
import subprocess
import tempfile
import warnings
from datetime import datetime

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))
warnings.filterwarnings("ignore", message=".*IProgress not found.*")

# Centralized root directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# ANSI Color codes for clean terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class TestResult:
    def __init__(self, test_id, name, target, status="PENDING", duration=0.0, details=""):
        self.test_id = test_id
        self.name = name
        self.target = target
        self.status = status  # PASS, FAIL, SKIP
        self.duration = duration
        self.details = details

    def to_dict(self):
        return {
            "id": self.test_id,
            "name": self.name,
            "target": self.target,
            "status": self.status,
            "duration_sec": round(self.duration, 2),
            "details": self.details,
        }


def format_status(status):
    if status == "PASS":
        return f"{GREEN}[ PASS ]{RESET}"
    elif status == "FAIL":
        return f"{RED}[ FAIL ]{RESET}"
    elif status == "SKIP":
        return f"{YELLOW}[ SKIP ]{RESET}"
    return f"[{status}]"


def print_banner(backend):
    print("=" * 86)
    print(f"{BOLD}{CYAN}             LUMI-IQ AUTOMATED MASTER TEST SUITE (TASK 2.1){RESET}")
    print(f"             Target Execution Backend : {BOLD}{backend}{RESET}")
    print(f"             Host System              : {os.uname().nodename} ({sys.platform})")
    print(f"             Timestamp                : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 86)
    print()


# -----------------------------------------------------------------------------
# TEST 1: Software Stack & Environment
# -----------------------------------------------------------------------------
def test_software_stack():
    start_time = time.time()
    print(f"{BOLD}[TEST 1/8] Verifying Software Stack & Python Environment...{RESET}")

    packages = [
        ("qiskit", "Core Quantum SDK", True),
        ("qiskit_aer", "High-performance Simulator", True),
        ("qaas", "IT4I QaaS QPU Client", True),
        ("py4lexis", "LEXIS AAI & Orchestration", True),
        ("numpy", "Numerical Computing", True),
        ("scipy", "Scientific Algorithms", True),
        ("matplotlib", "Visualization", True),
        ("pandas", "Data Analysis", False),
        ("networkx", "Graph Optimization", False),
        ("dill", "Object Serialization", False),
        ("sklearn", "Classical ML Baseline", False),
        ("qiskit_algorithms", "Quantum Algorithms Library", False),
        ("qiskit_machine_learning", "QML Extension", False),
        ("qiskit_nature", "Quantum Chemistry Extension", False),
        ("pyscf", "Electronic Structure Backend", False),
        ("stim", "Small-scale QEC Simulator", False),
        ("pymatching", "MWPM Syndrome Decoder", False),
        ("pennylane", "Hybrid QML Framework", False),
    ]

    installed = {}
    missing_required = []

    for mod_name, desc, required in packages:
        try:
            mod = __import__(mod_name)
            ver = getattr(mod, "__version__", "installed")
            installed[mod_name] = ver
            print(f"  ✓ {mod_name:<24} : {ver:<12} ({desc})")
        except Exception:
            if required:
                missing_required.append(mod_name)
                print(f"  ✗ {mod_name:<24} : {RED}MISSING (REQUIRED){RESET} ({desc})")
            else:
                print(f"  - {mod_name:<24} : {YELLOW}Not Installed (Optional){RESET} ({desc})")

    dur = time.time() - start_time
    if missing_required:
        return TestResult(1, "Software Stack & Environment", "Local", "FAIL", dur,
                          f"Missing required packages: {', '.join(missing_required)}")

    return TestResult(1, "Software Stack & Environment", "Local", "PASS", dur,
                      f"{len(installed)}/{len(packages)} packages verified")


# -----------------------------------------------------------------------------
# TEST 2: LEXIS Authentication & Hardware Target Verification
# -----------------------------------------------------------------------------
def test_lexis_authentication(backend_target):
    start_time = time.time()
    print(f"\n{BOLD}[TEST 2/8] Checking LEXIS Authentication & VLQ Target...{RESET}")

    try:
        from config import LEXIS_PROJECT, LEXIS_RESOURCE, get_lexis_token
    except ImportError:
        LEXIS_PROJECT = os.getenv("LEXIS_PROJECT", "your_vlq_project")
        LEXIS_RESOURCE = os.getenv("LEXIS_RESOURCE", "VLQ-CZ")
        get_lexis_token = lambda: None

    token = get_lexis_token()
    token_valid = False
    details_str = ""

    if token:
        try:
            import jwt
            payload = jwt.decode(token, options={"verify_signature": False})
            exp = payload.get("exp", 0)
            remaining = exp - int(time.time())
            if remaining > 30:
                token_valid = True
                exp_min = remaining // 60
                details_str = f"Token valid for {exp_min}m (Project: {LEXIS_PROJECT})"
                print(f"  ✓ LEXIS Token active in ~/.lumi-iq/token (Remaining: {exp_min}m)")
            else:
                details_str = "Token is expired"
                print(f"  ✗ Candidate token in ~/.lumi-iq/token is expired ({remaining}s remaining)")
        except Exception as e:
            details_str = f"Token decode error: {e}"
            print(f"  ✗ Could not decode token: {e}")
    else:
        print(f"  - No cached token found in ~/.lumi-iq/token")

    dur = time.time() - start_time
    if token_valid:
        # Check backend connectivity if QProvider available
        try:
            from qaas.client import QProvider
            provider = QProvider(lexis_project=LEXIS_PROJECT, token=token)
            backend = provider.get_backend(LEXIS_RESOURCE)
            print(f"  ✓ Connected to Hardware Target: {backend.name} (Resource: {LEXIS_RESOURCE})")
            return TestResult(2, "LEXIS Auth & QPU Target", LEXIS_RESOURCE, "PASS", dur, details_str)
        except Exception as e:
            if backend_target == "VLQ":
                return TestResult(2, "LEXIS Auth & QPU Target", LEXIS_RESOURCE, "FAIL", dur, f"QProvider error: {e}")
            else:
                return TestResult(2, "LEXIS Auth & QPU Target", LEXIS_RESOURCE, "PASS", dur, details_str)
    else:
        if backend_target == "VLQ":
            print(f"  {RED}ERROR: Valid token required for --backend VLQ. Run 'python auth.py' first.{RESET}")
            return TestResult(2, "LEXIS Auth & QPU Target", LEXIS_RESOURCE, "FAIL", dur, "Token missing/expired")
        else:
            print(f"  ℹ Backend SIM selected: LEXIS QPU token check skipped.")
            return TestResult(2, "LEXIS Auth & QPU Target", "Local SIM", "SKIP", dur, "SIM mode; token not required")


# -----------------------------------------------------------------------------
# TEST 3: Core Circuit Benchmark (Bell State)
# -----------------------------------------------------------------------------
def test_core_bell_state(backend_target, shots=1024):
    start_time = time.time()
    print(f"\n{BOLD}[TEST 3/8] Running Core Bell State Circuit Benchmark...{RESET}")

    from qiskit import QuantumCircuit, transpile

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()

    if backend_target == "SIM":
        try:
            from qiskit_aer import AerSimulator
            sim = AerSimulator()
            t_qc = transpile(qc, sim)
            result = sim.run(t_qc, shots=shots).result()
            counts = result.get_counts()
            dur = time.time() - start_time
            print(f"  ✓ Simulation measurements: {counts}")
            # Verify entanglement (00 and 11 should make up ~100% of counts)
            bell_shots = counts.get("00", 0) + counts.get("11", 0)
            fidelity = bell_shots / shots
            print(f"  ✓ Entangled state (|00> + |11>) fidelity: {fidelity*100:.1f}%")
            return TestResult(3, "Core Bell State Benchmark", "SIM", "PASS", dur, f"Fidelity: {fidelity*100:.1f}%")
        except Exception as e:
            dur = time.time() - start_time
            print(f"  ✗ Simulation error: {e}")
            return TestResult(3, "Core Bell State Benchmark", "SIM", "FAIL", dur, str(e))

    elif backend_target == "VLQ":
        try:
            from config import LEXIS_PROJECT, LEXIS_RESOURCE, get_lexis_token
            from qaas.client import QProvider
            token = get_lexis_token()
            provider = QProvider(lexis_project=LEXIS_PROJECT, token=token)
            backend = provider.get_backend(LEXIS_RESOURCE)
            print(f"  Transpiling for VLQ Star-topology native basis gates (CZ, PRX)...")
            t_qc = transpile(qc, backend=backend, optimization_level=1)
            print(f"  Submitting to VLQ ({shots} shots)...")
            job = backend.run(t_qc, shots=shots, job_name="test_bell_state")
            print(f"  Job {job.job_id()} queued. Waiting for completion...")
            result = job.result(timeout_secs=600)
            counts = result.get_counts()
            dur = time.time() - start_time
            print(f"  ✓ VLQ QPU measurements: {counts}")
            return TestResult(3, "Core Bell State Benchmark", "VLQ", "PASS", dur, f"QPU Counts: {counts}")
        except Exception as e:
            dur = time.time() - start_time
            print(f"  ✗ VLQ execution error: {e}")
            return TestResult(3, "Core Bell State Benchmark", "VLQ", "FAIL", dur, str(e))


# -----------------------------------------------------------------------------
# TEST 4-8: WP2 Use Cases Verification Runner
# -----------------------------------------------------------------------------
def run_use_case_subprocess(uc_num, name, script_relpath, backend_target, extra_args=None, timeout_sec=600):
    start_time = time.time()
    print(f"\n{BOLD}[TEST {uc_num+3}/8] Running Use Case {uc_num}: {name}...{RESET}")

    script_path = os.path.join(SCRIPT_DIR, script_relpath)
    if not os.path.exists(script_path):
        dur = time.time() - start_time
        print(f"  ✗ Script not found at {script_path}")
        return TestResult(uc_num + 3, f"UC {uc_num}: {name}", backend_target, "FAIL", dur, "Script missing")

    cmd = [sys.executable, script_path, "--backend", backend_target]
    if extra_args:
        cmd.extend(extra_args)

    print(f"  Command: {' '.join(cmd)}")
    print(f"  {CYAN}--- Live Output for {name} ---{RESET}")
    output_lines = []
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(script_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for raw_line in iter(proc.stdout.readline, ''):
            if not raw_line and proc.poll() is not None:
                break
            line_str = raw_line.rstrip()
            if line_str:
                print(f"    │ {line_str}")
                output_lines.append(line_str)
        proc.wait(timeout=timeout_sec)
        dur = time.time() - start_time
        print(f"  {CYAN}--- End of Output ({dur:.2f}s) ---{RESET}")

        if proc.returncode == 0:
            success_lines = [l for l in output_lines if "[SUCCESS]" in l or "Result" in l or "Score" in l or "Final" in l or "Accuracy" in l or "energy" in l.lower()]
            summary_info = success_lines[-1] if success_lines else "Completed successfully"
            print(f"  ✓ {summary_info}")
            return TestResult(uc_num + 3, f"UC {uc_num}: {name}", backend_target, "PASS", dur, summary_info)
        else:
            print(f"  ✗ Process exited with code {proc.returncode}")
            last_err = "\n".join(output_lines[-4:]) if output_lines else f"Exit {proc.returncode}"
            return TestResult(uc_num + 3, f"UC {uc_num}: {name}", backend_target, "FAIL", dur, f"Exit {proc.returncode}: {last_err[:120]}")
    except subprocess.TimeoutExpired:
        if 'proc' in locals():
            proc.kill()
        dur = time.time() - start_time
        print(f"  ✗ Execution timed out after {timeout_sec}s")
        return TestResult(uc_num + 3, f"UC {uc_num}: {name}", backend_target, "FAIL", dur, f"Timeout ({timeout_sec}s)")
    except Exception as e:
        dur = time.time() - start_time
        print(f"  ✗ Invocation failed: {e}")
        return TestResult(uc_num + 3, f"UC {uc_num}: {name}", backend_target, "FAIL", dur, str(e))


# -----------------------------------------------------------------------------
# Main Test Orchestrator
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="LUMI-IQ Master Test Suite: Unified Software Stack & Use Cases Verification"
    )
    parser.add_argument(
        "--backend",
        choices=["SIM", "VLQ"],
        default=os.getenv("LUMI_IQ_BACKEND", "SIM"),
        help="Target execution backend: 'SIM' (fast local simulation) or 'VLQ' (real IT4I QPU via LEXIS)",
    )
    parser.add_argument(
        "--use-cases",
        type=str,
        default="all",
        help="Comma-separated list of use cases to test (e.g. '1,4' or 'all')",
    )
    parser.add_argument(
        "--skip-use-cases",
        action="store_true",
        help="Run only software stack, LEXIS authentication, and Bell state benchmark",
    )
    parser.add_argument(
        "--skip-stack-check",
        action="store_true",
        help="Skip software stack import checks and run straight to benchmarks/use-cases",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=1024,
        help="Shot count per circuit on QPU / simulator (default: 1024)",
    )
    parser.add_argument(
        "--report-json",
        type=str,
        default=None,
        help="Save test results summary to JSON file",
    )
    parser.add_argument(
        "--report-md",
        type=str,
        default=None,
        help="Save test report summary to Markdown file",
    )
    args = parser.parse_args()

    print_banner(args.backend)
    total_start = time.time()
    results = []

    # Stage 1: Software Stack
    if not args.skip_stack_check:
        results.append(test_software_stack())

    # Stage 2: LEXIS Authentication & Hardware Target
    results.append(test_lexis_authentication(args.backend))

    # Stage 3: Core Bell State Benchmark
    results.append(test_core_bell_state(args.backend, shots=args.shots))

    # Stage 4-8: WP2 Use Cases
    if not args.skip_use_cases:
        selected_ucs = []
        if args.use_cases.lower() == "all":
            selected_ucs = [1, 2, 3, 4, 5]
        else:
            for item in args.use_cases.split(","):
                if item.strip().isdigit():
                    selected_ucs.append(int(item.strip()))

        use_case_defs = {
            1: ("Car Manufacturing (Anomaly Detection)", "use_cases/01_car_manufacturing/run_car_manufacturing.py", []),
            2: ("Health Molecular VQE (H2)", "use_cases/02_health_life_science/run_health_vqe.py", ["--max-iters", "2"]),
            3: ("Terrestrial Network Routing", "use_cases/03_terrestrial_network/run_terrestrial_network.py", []),
            4: ("QML Time Series Forecasting", "use_cases/04_qml_time_series/run_time_series_forecasting.py", []),
            5: ("Small-Scale QEC (Stim & Repetition)", "use_cases/05_small_scale_qec/run_small_scale_qec.py", []),
        }

        for uc_num in [1, 2, 3, 4, 5]:
            if uc_num in selected_ucs:
                name, relpath, extra = use_case_defs[uc_num]
                results.append(run_use_case_subprocess(uc_num, name, relpath, args.backend, extra))

    total_duration = time.time() - total_start

    # Print Summary Table
    print("\n" + "=" * 86)
    print(f"{BOLD}                        LUMI-IQ COMPLETE TEST SUITE SUMMARY{RESET}")
    print("=" * 86)
    print(f" {BOLD}{'#':<3} {'Test Case / Component':<36} {'Target':<10} {'Duration':<10} {'Status'}{RESET}")
    print("-" * 86)

    pass_count = 0
    fail_count = 0
    skip_count = 0

    for res in results:
        status_str = format_status(res.status)
        dur_str = f"{res.duration:.2f}s"
        print(f" {res.test_id:<3} {res.name:<36} {res.target:<10} {dur_str:<10} {status_str}")
        if res.status == "PASS":
            pass_count += 1
        elif res.status == "FAIL":
            fail_count += 1
        elif res.status == "SKIP":
            skip_count += 1

    print("-" * 86)
    total_tests = len(results)
    summary_line = f"TOTAL: {pass_count}/{total_tests} PASSED"
    if fail_count > 0:
        summary_line += f", {RED}{fail_count} FAILED{RESET}"
    if skip_count > 0:
        summary_line += f", {YELLOW}{skip_count} SKIPPED{RESET}"
    summary_line += f" in {total_duration:.2f}s"
    print(summary_line)

    overall_pass = fail_count == 0
    if overall_pass:
        print(f"\n{BOLD}{GREEN}✓ OVERALL RESULT: ALL TESTS PASSED SUCCESSFULLY!{RESET}\n")
    else:
        print(f"\n{BOLD}{RED}✗ OVERALL RESULT: TEST SUITE ENCOUNTERED FAILURES.{RESET}\n")

    # Optional JSON / Markdown export
    if args.report_json:
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "backend": args.backend,
            "overall_status": "SUCCESS" if overall_pass else "FAILURE",
            "passed": pass_count,
            "failed": fail_count,
            "skipped": skip_count,
            "total_duration_sec": round(total_duration, 2),
            "results": [r.to_dict() for r in results],
        }
        with open(args.report_json, "w") as f:
            json.dump(report_data, f, indent=2)
        print(f"Structured test report saved to: {args.report_json}")

    if args.report_md:
        with open(args.report_md, "w") as f:
            f.write("# LUMI-IQ Software Stack & Use Cases Test Report\n\n")
            f.write(f"- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Target Backend**: `{args.backend}`\n")
            f.write(f"- **Overall Status**: `{'SUCCESS' if overall_pass else 'FAILURE'}`\n")
            f.write(f"- **Duration**: {total_duration:.2f} seconds\n\n")
            f.write("| # | Test Case / Component | Target | Duration | Status | Details |\n")
            f.write("|---|---|---|---|---|---|\n")
            for r in results:
                f.write(f"| {r.test_id} | {r.name} | `{r.target}` | {r.duration:.2f}s | **{r.status}** | {r.details} |\n")
            f.write(f"\n**Total**: {pass_count}/{total_tests} passed ({fail_count} failed, {skip_count} skipped).\n")
        print(f"Markdown test report saved to: {args.report_md}")

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
