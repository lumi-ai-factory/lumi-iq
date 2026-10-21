#!/usr/bin/env python3
"""
Use case: Quantum Anomaly Detection for Car Manufacturing - Rare Defect Detection
Author: LUMI-IQ Consortium (WP2)
Adapted for LUMI-IQ Software Stack (Task 2.1)

Supports dual execution targets:
- '--backend SIM': Full dataset simulation via Qiskit Aer statevector kernel on LUMI CPU.
- '--backend VLQ': Real quantum hardware execution of 4-qubit fidelity overlap circuits
                   on the 24-qubit Star-topology transmon QPU at IT4Innovations via QaaS / LEXIS.
"""

import os
import sys
import argparse
import tempfile
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))

import warnings
warnings.filterwarnings("ignore", message=".*IProgress not found.*")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.metrics import (
    roc_auc_score, roc_curve, confusion_matrix,
    precision_score, recall_score, f1_score,
)

from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import ZZFeatureMap
from qiskit_machine_learning.kernels import FidelityStatevectorKernel
from qiskit_algorithms.utils import algorithm_globals

# Ensure parent directory is in path for centralized config
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(script_dir, "../..")))

try:
    from config import LEXIS_PROJECT, LEXIS_RESOURCE, get_lexis_token, save_lexis_token
    from qaas.client import QProvider
except ImportError:
    QProvider = None
    LEXIS_PROJECT = os.getenv("LEXIS_PROJECT", "your_vlq_project")
    LEXIS_RESOURCE = os.getenv("LEXIS_RESOURCE", "VLQ-CZ")
    get_lexis_token = lambda: None
    save_lexis_token = lambda t: None


def build_overlap_circuit(feature_map, x1, x2):
    """Constructs fidelity measurement circuit: U(x2)^dagger * U(x1) measured in Z basis."""
    qc = QuantumCircuit(feature_map.num_qubits)
    # Forward encoding of x1
    qc.compose(feature_map.assign_parameters(x1), inplace=True)
    # Inverse encoding of x2
    qc.compose(feature_map.assign_parameters(x2).inverse(), inplace=True)
    qc.measure_all()
    return qc


def main():
    parser = argparse.ArgumentParser(
        description="Car Manufacturing: Quantum Anomaly Detection on LUMI / VLQ"
    )
    parser.add_argument(
        "--backend",
        choices=["SIM", "VLQ"],
        default="SIM",
        help="Target execution backend: 'SIM' (local simulation on CPU) or 'VLQ' (real QPU via LEXIS)",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=1024,
        help="Number of shots per circuit when running on VLQ (default: 1024)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Use Case 1: Quantum Anomaly Detection for Car Manufacturing")
    print(f"Target Backend   : {args.backend}")
    print(f"Hardware Target  : {'IT4Innovations VLQ 24-Qubit QPU' if args.backend == 'VLQ' else 'Local Statevector Simulation'}")
    print("=" * 70)

    # 1. Reproducibility & Synthetic manufacturing sensor dataset
    SEED = 42
    algorithm_globals.random_seed = SEED
    np.random.seed(SEED)

    n_normal = 380
    n_defect = 20   # 5% defect rate
    feature_names = ["panel_gap", "weld_strength", "vibration", "torque"]
    n_features = len(feature_names)
    rng = np.random.RandomState(SEED)

    X_normal = rng.normal(loc=0.0, scale=1.0, size=(n_normal, n_features))
    mean_defect = np.array([2.2, -1.8, 1.6, 1.3])
    X_defect = rng.normal(loc=mean_defect, scale=1.3, size=(n_defect, n_features))

    X = np.vstack([X_normal, X_defect])
    y = np.concatenate([np.zeros(n_normal), np.ones(n_defect)])

    perm = rng.permutation(len(X))
    X, y = X[perm], y[perm]

    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.35, stratify=y, random_state=SEED
    )
    X_train_normal = X_train_full[y_train_full == 0]

    print(f"Dataset Size     : {len(X)} parts ({n_normal} normal, {n_defect} defective - 5% rate)")
    print(f"Training Pool    : {len(X_train_normal)} normal reference parts")
    print(f"Test Set         : {len(X_test)} parts (normal={np.sum(y_test==0)}, defect={np.sum(y_test==1)})")

    # 2. Setup Reference Pool & Scaling
    n_reference = 80
    ref_idx = rng.choice(len(X_train_normal), size=min(n_reference, len(X_train_normal)), replace=False)
    X_ref = X_train_normal[ref_idx]

    scaler = MinMaxScaler(feature_range=(0, np.pi / 4))
    scaler.fit(X_ref)
    X_ref_scaled = scaler.transform(X_ref)
    X_test_scaled = scaler.transform(X_test)

    feature_map = ZZFeatureMap(feature_dimension=n_features, reps=1, entanglement='full')
    print(f"Quantum Encoding : 4-Qubit ZZFeatureMap (reps=1, full entanglement, {feature_map.num_parameters} parameters)")

    # 3. Execution on Selected Backend
    if args.backend == "VLQ":
        print("\n=== Initializing Connection to VLQ Quantum Computer ===")
        token = get_lexis_token()
        if token:
            print(f"Using authenticated token from ~/.lumi-iq/token (project: {LEXIS_PROJECT})")
            provider = QProvider(lexis_project=LEXIS_PROJECT, token=token)
        else:
            print(f"Initiating OAuth Device Flow for LEXIS project '{LEXIS_PROJECT}'...")
            provider = QProvider(lexis_project=LEXIS_PROJECT)
            if getattr(provider, "_token", None):
                save_lexis_token(provider._token)

        backend = provider.get_backend(LEXIS_RESOURCE)
        print(f"Connected to QPU: {backend.name} (target: {LEXIS_RESOURCE})")

        # Select a sample of test parts (e.g. 5 incoming parts: mix of normal and defect) to test on hardware
        test_sample_idx = [0, 1, 2, 3, 4]
        print(f"\nSubmitting fidelity overlap verification for {len(test_sample_idx)} test parts to VLQ QPU...")

        circuits_to_run = []
        # Compare each test part against 3 representative normal parts
        comp_ref = X_ref_scaled[:3]
        for t_idx in test_sample_idx:
            for r in comp_ref:
                circuits_to_run.append(build_overlap_circuit(feature_map, X_test_scaled[t_idx], r))

        print(f"Transpiling {len(circuits_to_run)} circuits for native VLQ gate set...")
        t_circuits = transpile(circuits_to_run, backend=backend, optimization_level=1)
        job = backend.run(t_circuits, shots=args.shots)
        print(f"Submitted to Slurm queue on VLQ. Job ID: {job.job_id()}")
        print(f"Awaiting QPU execution results (timeout: 600s)...")

        result = job.result(timeout_secs=600)
        counts = result.get_counts()
        if isinstance(counts, dict):
            counts = [counts]

        print(f"\n[VLQ SUCCESS] Received measurements from {len(counts)} quantum circuits on VLQ!")
        all_zeros = "0" * n_features
        fidelities = [c.get(all_zeros, 0) / args.shots for c in counts]

        # Reshape into (len(test_sample_idx), 3) and average
        fid_matrix = np.array(fidelities).reshape((len(test_sample_idx), 3))
        avg_fidelities = fid_matrix.mean(axis=1)

        print("\nVLQ QPU Quantum Anomaly Verification Results:")
        print("-" * 55)
        for i, t_idx in enumerate(test_sample_idx):
            actual_label = "DEFECT" if y_test[t_idx] == 1 else "NORMAL"
            fid = avg_fidelities[i]
            verdict = "DEFECT FLAG" if fid < 0.55 else "NORMAL PASS"
            print(f"Part #{t_idx:02d} | Actual: {actual_label:<6s} | VLQ Overlap Fidelity: {fid:.4f} | System: {verdict}")
        print("-" * 55)

    # In parallel, compute reference metrics via statevector for complete visualization
    quantum_kernel = FidelityStatevectorKernel(feature_map=feature_map)
    K_test_ref = quantum_kernel.evaluate(x_vec=X_test_scaled, y_vec=X_ref_scaled)
    quantum_anomaly_score = K_test_ref.mean(axis=1)

    K_ref_ref = quantum_kernel.evaluate(x_vec=X_ref_scaled)
    ref_self_scores = K_ref_ref.mean(axis=1)
    quantum_threshold = np.percentile(ref_self_scores, 5)
    quantum_pred = (quantum_anomaly_score < quantum_threshold).astype(int)

    # 4. Classical Baselines
    iso_forest = IsolationForest(contamination=n_defect / (n_normal + n_defect), random_state=SEED)
    iso_forest.fit(X_ref_scaled)
    iso_pred = (iso_forest.predict(X_test_scaled) == -1).astype(int)
    iso_score = -iso_forest.score_samples(X_test_scaled)

    oc_svm = OneClassSVM(nu=n_defect / (n_normal + n_defect), kernel='rbf', gamma='scale')
    oc_svm.fit(X_ref_scaled)
    svm_pred = (oc_svm.predict(X_test_scaled) == -1).astype(int)
    svm_score = -oc_svm.score_samples(X_test_scaled)

    # 5. Evaluate Metrics
    def evaluate(name, y_true, y_pred, score, score_high_is_anomaly):
        s = score if score_high_is_anomaly else -score
        auc = roc_auc_score(y_true, s)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        cm = confusion_matrix(y_true, y_pred)
        print(f"\n--- {name} ---")
        print(f"  AUC:       {auc:.3f}")
        print(f"  Precision: {prec:.3f}")
        print(f"  Recall:    {rec:.3f} (fraction of real defects caught)")
        print(f"  F1 Score:  {f1:.3f}")
        return {"name": name, "auc": auc, "precision": prec, "recall": rec, "f1": f1, "cm": cm}

    q_res = evaluate("Quantum Fidelity Anomaly Detector", y_test, quantum_pred, quantum_anomaly_score, False)
    iso_res = evaluate("Isolation Forest", y_test, iso_pred, iso_score, True)
    svm_res = evaluate("One-Class SVM", y_test, svm_pred, svm_score, True)

    # 6. Plot & Save Summary Figure
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for name, y_true, score, high_is_anom in [
        ("Quantum Fidelity", y_test, quantum_anomaly_score, False),
        ("Isolation Forest", y_test, iso_score, True),
        ("One-Class SVM", y_test, svm_score, True),
    ]:
        s = score if high_is_anom else -score
        fpr, tpr, _ = roc_curve(y_true, s)
        auc = roc_auc_score(y_true, s)
        axes[0].plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})")
    axes[0].plot([0, 1], [0, 1], 'k--', alpha=0.4, label="Random guess")
    axes[0].set_xlabel("False Positive Rate")
    axes[0].set_ylabel("True Positive Rate (Recall)")
    axes[0].set_title("ROC Curves — Anomaly Detectors")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    n_test = len(y_test)
    n_defects = int(y_test.sum())
    names = ["Quantum Fidelity", "Isolation Forest", "One-Class SVM"]
    results_list = [q_res, iso_res, svm_res]
    catch_rates = [r["cm"].ravel()[3] / n_defects for r in results_list]
    false_alarm_rates = [r["cm"].ravel()[1] / (n_test - n_defects) for r in results_list]

    x = np.arange(len(names))
    width = 0.35
    axes[1].bar(x - width/2, catch_rates, width, label='Defect catch rate (higher=better)', color='tab:green')
    axes[1].bar(x + width/2, false_alarm_rates, width, label='False alarm rate (lower=better)', color='tab:orange')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(names)
    axes[1].set_ylim(0, 1.05)
    axes[1].set_ylabel("Rate")
    target_label = "VLQ QPU & Simulation" if args.backend == "VLQ" else "Simulation"
    axes[1].set_title(f"Rare-Defect Detection: Catch Rate vs False Alarm ({target_label})")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    output_png = os.path.join(script_dir, "result_car_manufacturing.png")
    plt.savefig(output_png, dpi=150)
    print(f"\n[SUCCESS] Execution complete. Results chart saved to {output_png}")


if __name__ == "__main__":
    main()
