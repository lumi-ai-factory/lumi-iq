#!/bin/bash
# ==============================================================================
# LUMI Supercomputer - Slurm Batch Job Script for Hybrid Quantum-Classical (VLQ)
# Project: LUMI-IQ (Task 2.1 Initial Software Stack)
# ==============================================================================

#SBATCH --job-name=lumi-iq-vlq
#SBATCH --account=your_lumi_project_id        # Set your LUMI project ID (e.g. project_<id>) or use submit_job.py
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

# 0. Load centralized configuration if available
if [ -f "./.env" ]; then
    set -a; source "./.env"; set +a
elif [ -n "${SLURM_SUBMIT_DIR:-}" ] && [ -f "$SLURM_SUBMIT_DIR/.env" ]; then
    set -a; source "$SLURM_SUBMIT_DIR/.env"; set +a
elif [ -f "$HOME/.lumi-iq/config" ]; then
    set -a; source "$HOME/.lumi-iq/config"; set +a
fi

# 1. Clean environment and load LUMI software modules quietly (suppressing sticky module noise)
module --force purge 2>/dev/null || true
module load LUMI/24.03 2>/dev/null || true
module use /appl/local/lumiiq/modulefiles 2>/dev/null || true
module use "$HOME/modulefiles" 2>/dev/null || true

# 2. Load the LUMI-IQ environment
if module is-avail Lumi-IQ-qaas/VLQ 2>/dev/null; then
    module load Lumi-IQ-qaas/VLQ
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

# 4. Locate target script and arguments
TARGET_SCRIPT="${TARGET_SCRIPT:-./vlq_bell_state.py}"
TARGET_ARGS="${TARGET_ARGS:-}"

if [ ! -f "$TARGET_SCRIPT" ] && [ -n "${SLURM_SUBMIT_DIR:-}" ] && [ -f "$SLURM_SUBMIT_DIR/$TARGET_SCRIPT" ]; then
    TARGET_SCRIPT="$SLURM_SUBMIT_DIR/$TARGET_SCRIPT"
fi

# 5. Execute the hybrid quantum workflow on LUMI compute node with QPU offload
echo "Executing hybrid quantum workflow on LUMI compute node:"
echo "Script : $TARGET_SCRIPT"
echo "Args   : $TARGET_ARGS"
echo "--------------------------------------------------------"
srun python -u "$TARGET_SCRIPT" $TARGET_ARGS

echo "=== Job Completed Successfully ==="
