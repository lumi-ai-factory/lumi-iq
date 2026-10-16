#!/usr/bin/env bash
# ==============================================================================
# LUMI-IQ Master Test Suite Execution Script
# Task 2.1: Unified Software Stack & Use Cases Automated Verification
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Parse optional --slurm / --hpc flag to submit as an unattended Slurm job
USE_SLURM=false
PASS_ARGS=()

for arg in "$@"; do
    case "$arg" in
        --slurm|--hpc|--batch)
            USE_SLURM=true
            ;;
        *)
            PASS_ARGS+=("$arg")
            ;;
    esac
done

# 2. Automatic Lmod module loading if running in a LUMI shell without active environment
if command -v module &> /dev/null; then
    if ! python3 -c "import qiskit" &> /dev/null; then
        echo "[INFO] Loading lumi-iq environment module..."
        module use /project/project_462001789/modulefiles 2>/dev/null || true
        module use "$HOME/modulefiles" 2>/dev/null || true
        module load lumi-iq 2>/dev/null || true
    fi
fi

# 3. Ensure unbuffered real-time stdout
export PYTHONUNBUFFERED=1

# 4. Execute either as a Slurm HPC batch job or directly in current shell
if [ "$USE_SLURM" = true ]; then
    echo "=== Submitting Test Suite as Slurm HPC Job on LUMI Compute Node ==="
    python3 "$SCRIPT_DIR/submit_job.py" --use-case all "${PASS_ARGS[@]}"
else
    python3 "$SCRIPT_DIR/run_all_tests.py" "${PASS_ARGS[@]}"
fi
