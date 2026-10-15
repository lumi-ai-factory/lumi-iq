#!/usr/bin/env bash
# ==============================================================================
# LUMI-IQ Master Test Suite Execution Script
# Task 2.1: Unified Software Stack & Use Cases Automated Verification
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Automatic Lmod module loading if running in a LUMI shell without active environment
if command -v module &> /dev/null; then
    if ! python3 -c "import qiskit" &> /dev/null; then
        echo "[INFO] Loading lumi-iq environment module..."
        module use /project/project_462001789/modulefiles 2>/dev/null || true
        module use "$HOME/modulefiles" 2>/dev/null || true
        module load lumi-iq 2>/dev/null || true
    fi
fi

# 2. Ensure unbuffered real-time stdout
export PYTHONUNBUFFERED=1

# 3. Execute master test orchestrator with passed arguments (default: --backend SIM)
python3 "$SCRIPT_DIR/run_all_tests.py" "$@"
