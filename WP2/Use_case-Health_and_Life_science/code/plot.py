import matplotlib.pyplot as plt
import pandas as pd

iterations = list(range(1, 41))
E_CI = -1.85238817356958

df = pd.read_csv('/Path/to/health_and_life_science/vqe-replay_vlq.csv')

vqe_energies = df.iloc[:, 1].dropna().tolist()
iterations = list(range(1, len(vqe_energies) + 1))

final_energy = df.iloc[-1, 1]

# plotting
plt.figure(figsize=(10, 6))
# plot the results from the vqe
plt.plot(iterations, vqe_energies, marker='o', markersize=4, linewidth=2, color='#1f77b4', label='VQE Iterations (SPSA)')
# plot the E(CI) target energy
plt.axhline(y=E_CI, color='#2ca02c', linestyle='--', linewidth=2, label=f'E(CI) Target ({E_CI:.4f} Hartree)')
# plot the final energy estimate from the classical shadow
#plt.axhline(y=final_energy, color='#d62728', linestyle=':', linewidth=2, label=f'Final Shadow Estimate ({final_energy:.4f} Hartree)')

plt.title('VQE Energy Convergence vs. E(CI) Target Energy', fontsize=14, fontweight='bold')
plt.xlabel('Optimizer Iteration', fontsize=12)
plt.ylabel('Energy (Hartree)', fontsize=12)
plt.legend(fontsize=11, loc='upper right')

plt.tight_layout()
plt.show()


