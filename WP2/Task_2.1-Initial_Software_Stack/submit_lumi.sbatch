#!/bin/bash
# ==============================================================================
# LUMI Supercomputer - Slurm Batch Job Script for Hybrid Quantum-Classical (VLQ)
# Project: LUMI-IQ (D2.1 Initial Software Stack)
# ==============================================================================

#SBATCH --job-name=lumi-iq-vlq
#SBATCH --account=project_465003105        # Your LUMI project ID
#SBATCH --partition=standard               # Standard CPU partition (use 'small' or 'interactive' for quick tests, 'gpu' for GPU)
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=lumi_iq_%j.out
#SBATCH --error=lumi_iq_%j.err

echo "=== Starting LUMI-IQ Hybrid Job on LUMI ==="
echo "Node: $(hostname)"
echo "Date: $(date)"

# 1. Clean environment and load LUMI software modules
module purge
module load LUMI/24.03

# 2. Load the LUMI-IQ environment
if module is-avail LUMI-IQ-qaas/VLQ 2>/dev/null; then
    module load LUMI-IQ-qaas/VLQ
elif [ -d "$HOME/lumi-iq-env/bin" ]; then
    export PATH="$HOME/lumi-iq-env/bin:$PATH"
fi

# 3. Securely set LEXIS authentication token
# For batch execution, export LEXIS_TOKEN prior to sbatch (e.g., export LEXIS_TOKEN="...")
if [ -z "${LEXIS_TOKEN:-}" ]; then
    echo "Warning: LEXIS_TOKEN is not set in environment. Interactive Device Flow cannot open browser in batch mode."
fi

# 4. Execute the hybrid quantum workflow on LUMI compute node
echo "Executing quantum circuit on VLQ via QScheduler..."
srun python -u vlq_bell_state.py

echo "=== Job Completed Successfully ==="
