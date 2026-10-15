#!/usr/bin/env python3
"""
Use Case 4: QML Time Series Forecasting (Electricity Prices)
Author: Jiří Tomčala (IT4Innovations National Supercomputing Center)
Adapted for LUMI-IQ Software Stack (Task 2.1)

Supports dual execution targets:
- '--backend SIM': Full series inference across 360 hours on local Qiskit simulator.
- '--backend VLQ': Real execution of the 8-qubit trained QNN forward pass circuit
                   on the 24-qubit Star-topology transmon QPU at IT4Innovations via QaaS / LEXIS.
"""

import os
import sys
import argparse
import tempfile
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))

import warnings
warnings.filterwarnings("ignore", message=".*IProgress not found.*")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_machine_learning.algorithms.regressors import NeuralNetworkRegressor

# Ensure parent directory is in path for centralized config
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(script_dir, "../..")))

try:
    from config import LEXIS_PROJECT, LEXIS_RESOURCE, get_lexis_token
    from qaas.client import QProvider
except ImportError:
    QProvider = None
    LEXIS_PROJECT = "vlq_demo_project"
    LEXIS_RESOURCE = "VLQ-CZ"
    get_lexis_token = lambda: None


def main():
    parser = argparse.ArgumentParser(
        description="QML Time Series: Electricity Price Forecasting on LUMI / VLQ"
    )
    parser.add_argument(
        "--backend",
        choices=["SIM", "VLQ"],
        default="SIM",
        help="Target execution backend: 'SIM' (local simulation on CPU) or 'VLQ' (real QPU via LEXIS)",
    )
    parser.add_argument(
        "--model-file",
        type=str,
        default=os.path.join(script_dir, "QNN_0.7706084854606758-model_state.dill"),
        help="Path to pre-trained QNN model state",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=1024,
        help="Number of shots per circuit on VLQ (default: 1024)",
    )
    args = parser.parse_args()

    modelfile = args.model_file
    if not os.path.isabs(modelfile) and not os.path.exists(modelfile):
        modelfile = os.path.join(script_dir, modelfile)

    print("=" * 70)
    print("Use Case 4: QML Time Series Forecasting (Electricity Prices)")
    print(f"Target Backend   : {args.backend}")
    print(f"Hardware Target  : {'IT4Innovations VLQ 24-Qubit QPU' if args.backend == 'VLQ' else 'Local Simulation'}")
    print(f"Loaded Model     : {os.path.basename(modelfile)}")
    print("=" * 70)

    # 1. Load Data
    data_path = os.path.join(script_dir, "data.npy")
    data_orig = np.load(data_path, allow_pickle=True)[96:]

    n = 360
    min_val = min(data_orig[0:(8+n)])
    max_val = max(data_orig[0:(8+n)])
    data = ((2 * np.pi) * (data_orig - min_val) / (max_val - min_val)) - np.pi

    inputs = []
    for i in range(n):
        inputs.append(data[i:(i+8)])
    inputs = np.array(inputs)

    outputs = np.array(data[8:(8+n)])
    outputs_norm = ((outputs - min(outputs)) / (max(outputs) - min(outputs))) - 0.5
    outputs_orig = np.array(data_orig[8:(8+n)])
    outputs_train_orig = outputs_orig[0:240]

    # 2. Load Pre-trained QNN Regressor
    reg = NeuralNetworkRegressor.from_dill(modelfile)
    qnn = reg.neural_network
    weights = reg.weights

    # 3. Execution on Selected Backend
    vlq_predicted_price = None
    if args.backend == "VLQ":
        print("\n=== Initializing Connection to VLQ Quantum Computer ===")
        token = get_lexis_token()
        if token:
            print(f"Using authenticated token from ~/.lumi-iq/token (project: {LEXIS_PROJECT})")
            provider = QProvider(lexis_project=LEXIS_PROJECT, token=token)
        else:
            print(f"Initiating OAuth Device Flow for LEXIS project '{LEXIS_PROJECT}'...")
            provider = QProvider(lexis_project=LEXIS_PROJECT)

        backend = provider.get_backend(LEXIS_RESOURCE)
        print(f"Connected to QPU: {backend.name} (target: {LEXIS_RESOURCE})")

        # Evaluate the 1-hour ahead forecast for the latest test window
        latest_input = inputs[-1]
        print(f"Encoding latest 8-hour price window into 8-qubit parameterized circuit...")

        # Construct evaluation circuit with bound input and weight parameters
        eval_circuit = qnn.circuit.copy()
        param_dict = {}
        for p, val in zip(qnn.input_params, latest_input):
            param_dict[p] = val
        for p, val in zip(qnn.weight_params, weights):
            param_dict[p] = val

        eval_circuit.assign_parameters(param_dict, inplace=True)
        # Measure qubit 0 (which measures expectation value <Z_0>)
        eval_circuit.measure_all()

        print(f"Transpiling 8-qubit QNN circuit for VLQ Star-topology native gates (CZ, PRX)...")
        t_circuit = transpile(eval_circuit, backend=backend, optimization_level=1)
        print(f"Transpiled circuit depth: {t_circuit.depth()}, 2-qubit CZ gates: {t_circuit.count_ops().get('cz', 0)}")

        print(f"Submitting QNN forward pass to VLQ ({args.shots} shots)...")
        job = backend.run(t_circuit, shots=args.shots)
        print(f"Job ID: {job.job_id()} queued on VLQ.")
        print("Awaiting QPU measurement execution...")

        result = job.result(timeout_secs=600)
        counts = result.get_counts()
        print(f"\n[VLQ SUCCESS] Received measurements from VLQ QPU!")

        # Calculate <Z_0> expectation value from qubit 0 counts
        c0, c1 = 0, 0
        for bitstr, cnt in counts.items():
            # Qiskit ordering: qubit 0 is the rightmost character
            if bitstr[-1] == "0":
                c0 += cnt
            else:
                c1 += cnt

        exp_val = (c0 - c1) / args.shots
        vlq_norm_pi = (exp_val + 0.5) * (max(outputs) - min(outputs)) + min(outputs)
        vlq_predicted_price = (vlq_norm_pi + np.pi) / (2 * np.pi) * (max_val - min_val) + min_val
        actual_price = outputs_orig[-1]

        print("-" * 65)
        print(f"VLQ QPU Measured Expectation <Z_0> : {exp_val:+.4f}")
        print(f"VLQ 1-Hour Ahead Price Forecast    : {vlq_predicted_price:.2f} EUR/MWh")
        print(f"Actual Market Clearing Price       : {actual_price:.2f} EUR/MWh")
        print(f"Forecast Error                     : {abs(vlq_predicted_price - actual_price):.2f} EUR/MWh")
        print("-" * 65)

    # Full series simulation baseline for visualization
    outputs_predicted_norm = reg.predict(inputs)[:, 0]
    outputs_predicted_norm_pi = (outputs_predicted_norm + 0.5) * (max(outputs) - min(outputs)) + min(outputs)
    outputs_predicted_orig = (outputs_predicted_norm_pi + np.pi) / (2 * np.pi) * (max_val - min_val) + min_val
    score = reg.score(inputs, outputs_norm)

    # 4. Generate Plot
    plt.figure(figsize=(16, 5))
    plt.plot(range(len(outputs_orig)), outputs_orig, "r--", label="Real Market Prices (OTE-CR)")
    plt.plot(range(len(outputs_train_orig)), outputs_train_orig, "b.", label="Training Window")
    plt.plot(range(len(outputs_predicted_orig)), outputs_predicted_orig, "g-", linewidth=1.5, label=f"QNN Model ({score*100:.2f}% avg precision)")

    if vlq_predicted_price is not None:
        idx_last = len(outputs_orig) - 1
        plt.scatter([idx_last], [vlq_predicted_price], color="gold", edgecolor="black", s=120, zorder=5, label=f"VLQ QPU Forecast: {vlq_predicted_price:.2f} EUR/MWh")

    backend_str = "VLQ QPU & Simulation" if args.backend == "VLQ" else "Simulation"
    plt.title(f"Forecasting Electricity Price with 8-Qubit QNN on {backend_str}", fontsize=13, fontweight="bold")
    plt.xlabel("Time [Hours]", fontsize=11)
    plt.ylabel("Price [EUR/MWh]", fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)
    plt.tight_layout()

    out_file = os.path.join(script_dir, "result_time_series.png")
    plt.savefig(out_file, dpi=150)
    plt.savefig(os.path.join(script_dir, "result_prediction.png"), dpi=150)
    print(f"\n[SUCCESS] Forecast complete. Result plot saved to {out_file}")


if __name__ == "__main__":
    main()
