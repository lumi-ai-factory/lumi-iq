#!/bin/bash
# ==============================================================================
# Build Tykky Container Wrapper on LUMI
# Project: LUMI-IQ (Task 2.1)
#
# Adheres to LUMI Lustre Parallel Filesystem Policy:
# Uses conda-containerize to provision a clean Python 3.12 environment
# packaged into a single SquashFS container image.
# ==============================================================================

set -euo pipefail

TARGET_DIR="${1:-$HOME/lumi-iq-env}"
ENV_FILE="${2:-env.yml}"

echo "=== Building LUMI-IQ Environment using Tykky (conda-containerize) ==="
echo "Target directory: $TARGET_DIR"
echo "Environment definition: $ENV_FILE"

# 1. Load LUMI container wrapper module (Tykky)
module load LUMI lumi-container-wrapper 2>/dev/null || module load lumi-container-wrapper 2>/dev/null || true

# Robust fallback to LUMI system path if Lmod hierarchy differs:
if ! command -v conda-containerize &>/dev/null; then
    for candidate in /appl/lumi/SW/LUMI-*/common/EB/lumi-container-wrapper/*/bin/conda-containerize; do
        if [ -x "$candidate" ]; then
            export PATH="$(dirname "$candidate"):$PATH"
            break
        fi
    done
fi

if ! command -v conda-containerize &>/dev/null; then
    echo "ERROR: conda-containerize not found. Please run: module load LUMI lumi-container-wrapper"
    exit 1
fi

echo "Using conda-containerize: $(which conda-containerize)"

# 2. Run conda-containerize to build containerized Python 3.12 environment
conda-containerize new \
    --prefix "$TARGET_DIR" \
    "$ENV_FILE"

echo "=== Tykky Container Built Successfully! ==="
echo "Next step: configure the Lmod module:"
echo "  bash setup_lumi_module.sh"
