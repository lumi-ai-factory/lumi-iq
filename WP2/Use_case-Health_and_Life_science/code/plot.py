import os
import matplotlib.pyplot as plt
import pandas as pd

iterations = list(range(1, 41))
E_CI = -1.85238817356958

def plot_results(csv_path=None, output_path="HealthExamplePlot.png"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)

    if csv_path is None or not os.path.exists(csv_path):
        for candidate in [
            os.path.join(parent_dir, "vqe-replay.csv"),
            os.path.join(parent_dir, "vqe_trajectory.csv"),
            os.path.join(script_dir, "vqe-replay.csv"),
        ]:
            if os.path.exists(candidate):
                csv_path = candidate
                break

    if not csv_path or not os.path.exists(csv_path):
        print("Notice: No CSV file found to plot.")
        return

    df = pd.read_csv(csv_path)
    vqe_energies = df.iloc[:, 1].dropna().tolist()
    iterations = list(range(1, len(vqe_energies) + 1))

    # plotting
    plt.figure(figsize=(10, 6))
    plt.plot(iterations, vqe_energies, marker='o', markersize=4, linewidth=2, color='#1f77b4', label='VQE Iterations (SPSA)')
    plt.axhline(y=E_CI, color='#2ca02c', linestyle='--', linewidth=2, label=f'E(CI) Target ({E_CI:.4f} Hartree)')

    plt.title('VQE Energy Convergence vs. E(CI) Target Energy', fontsize=14, fontweight='bold')
    plt.xlabel('Optimizer Iteration', fontsize=12)
    plt.ylabel('Energy (Hartree)', fontsize=12)
    plt.legend(fontsize=11, loc='upper right')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    plot_results()
