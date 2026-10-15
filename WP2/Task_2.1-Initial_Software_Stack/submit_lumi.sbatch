#!/bin/bash
# ==============================================================================
# LUMI Supercomputer - Slurm Batch Job Script for Hybrid Quantum-Classical (VLQ)
# Project: LUMI-IQ (D2.1 Initial Software Stack)
# ==============================================================================

#SBATCH --job-name=lumi-iq-vlq
#SBATCH --account=project_462001789        # Your LUMI project ID
#SBATCH --partition=small                  # 'small' partition for sub-node CPU allocation
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=00:05:00                    # Default execution walltime; overridden by submit_job.py
#SBATCH --output=lumi_iq_%j.out
#SBATCH --error=lumi_iq_%j.err

echo "=== Starting LUMI-IQ Hybrid Job on LUMI ==="
echo "Job ID: ${SLURM_JOB_ID:-local}"
echo "Node  : $(hostname)"
echo "Date  : $(date)"
echo "WorkDir: $(pwd)"

# 1. Clean environment and load LUMI software modules quietly (suppressing sticky module noise)
module --force purge 2>/dev/null || true
module load LUMI/24.03 2>/dev/null || true
module use "$HOME/modulefiles" 2>/dev/null || true

# 2. Load the LUMI-IQ environment
if module is-avail lumi-iq 2>/dev/null; then
    module load lumi-iq
elif [ -d "$HOME/lumi-iq-env/bin" ]; then
    export PATH="$HOME/lumi-iq-env/bin:$PATH"
fi

# 3. Securely set LEXIS authentication token
TOKEN_FILE="$HOME/.lumi-iq/token"
if [ -z "${LEXIS_TOKEN:-}" ] && [ -f "$TOKEN_FILE" ]; then
    export LEXIS_TOKEN=$(cat "$TOKEN_FILE")
    echo "Using secure token from $TOKEN_FILE (permissions: 0600)"
fi

if [ -z "${LEXIS_TOKEN:-}" ] && [ ! -f "$TOKEN_FILE" ]; then
    echo "ERROR: LEXIS_TOKEN is not set and $TOKEN_FILE does not exist. Run python submit_job.py to authenticate first."
    exit 1
fi

# 4. Locate target script (current scratch directory or submit directory)
if [ -f "./vlq_bell_state.py" ]; then
    TARGET_SCRIPT="./vlq_bell_state.py"
elif [ -n "${SLURM_SUBMIT_DIR:-}" ] && [ -f "$SLURM_SUBMIT_DIR/vlq_bell_state.py" ]; then
    TARGET_SCRIPT="$SLURM_SUBMIT_DIR/vlq_bell_state.py"
else
    TARGET_SCRIPT="vlq_bell_state.py"
fi

# 5. Execute the hybrid quantum workflow on LUMI compute node
echo "Executing quantum circuit on VLQ QPU ($TARGET_SCRIPT)..."
srun python -u "$TARGET_SCRIPT"

echo "=== Job Completed Successfully ==="
