#!/usr/bin/env python3
"""
Use case: Quantum Anomaly Detection for Car Manufacturing - Rare Defect Detection
Author: Dr. Van Binh Henri VU (IT4Innovations, VSB - Technical University of Ostrava)
Adapted for LUMI-IQ Software Stack (Task 2.1)

Executes quantum fidelity anomaly detection using ZZFeatureMap and compares against
classical baselines (Isolation Forest, One-Class SVM).
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore", message=".*IProgress not found.*")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.metrics import (
    roc_auc_score, roc_curve, confusion_matrix,
    precision_score, recall_score, f1_score,
)

from qiskit.circuit.library import ZZFeatureMap
from qiskit_machine_learning.kernels import FidelityStatevectorKernel
from qiskit_algorithms.utils import algorithm_globals

def main():
    print("=" * 65)
    print("Use Case: Quantum Anomaly Detection for Car Manufacturing")
    print("Hardware / Stack: LUMI-IQ Module (Python 3.12 / Qiskit ML)")
    print("=" * 65)

    # 1. Reproducibility
    SEED = 42
    algorithm_globals.random_seed = SEED
    np.random.seed(SEED)

    # 2. Synthetic manufacturing sensor dataset
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

    print(f"Total parts: {len(X)} ({n_normal} normal, {n_defect} defective - 5% rate)")
    print(f"Training pool (normal only): {len(X_train_normal)} parts")
    print(f"Test set: {len(X_test)} parts (normal={np.sum(y_test==0)}, defect={np.sum(y_test==1)})")

    # 3. Setup Quantum Kernel (ZZFeatureMap)
    n_reference = 80
    ref_idx = rng.choice(len(X_train_normal), size=min(n_reference, len(X_train_normal)), replace=False)
    X_ref = X_train_normal[ref_idx]

    scaler = MinMaxScaler(feature_range=(0, np.pi / 4))
    scaler.fit(X_ref)
    X_ref_scaled = scaler.transform(X_ref)
    X_test_scaled = scaler.transform(X_test)

    feature_map = ZZFeatureMap(feature_dimension=n_features, reps=1, entanglement='full')
    quantum_kernel = FidelityStatevectorKernel(feature_map=feature_map)

    print(f"\nConstructed Quantum Feature Map: {n_features} qubits, {feature_map.reps} reps, full entanglement.")
    print("Evaluating quantum fidelity matrix on test vs reference parts...")

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

    # 5. Evaluate
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
        print(f"  Confusion Matrix [[TN, FP], [FN, TP]]:\n{cm}")
        return {"name": name, "auc": auc, "precision": prec, "recall": rec, "f1": f1, "cm": cm}

    q_res = evaluate("Quantum Fidelity Anomaly Detector", y_test, quantum_pred, quantum_anomaly_score, False)
    iso_res = evaluate("Isolation Forest", y_test, iso_pred, iso_score, True)
    svm_res = evaluate("One-Class SVM", y_test, svm_pred, svm_score, True)

    # 6. Plot & Save Summary Figure
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # ROC Curves
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
    axes[0].set_title("ROC — Quantum vs. Classical Anomaly Detectors")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Catch vs False Alarm
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
    axes[1].set_title("Rare-Defect Detection: Catch Rate vs False Alarm Rate")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    output_png = "result_car_manufacturing.png"
    plt.savefig(output_png, dpi=150)
    print(f"\n[SUCCESS] Execution complete. Results chart saved to {output_png}")

if __name__ == "__main__":
    main()
