#!/bin/bash
# ==============================================================================
# Build Tykky Container Wrapper on LUMI
# Project: LUMI-IQ (Task 2.1)
#
# Adheres to LUMI Lustre Parallel Filesystem Policy:
# Packages all Python libraries into a single SquashFS container image,
# avoiding thousands of small files/inodes on Lustre.
# ==============================================================================

set -euo pipefail

TARGET_DIR="${1:-$HOME/lumi-iq-env}"
REQUIREMENTS_FILE="${2:-requirements.txt}"

echo "=== Building LUMI-IQ Environment using Tykky ==="
echo "Target directory: $TARGET_DIR"
echo "Requirements file: $REQUIREMENTS_FILE"

# 1. Load LUMI container wrapper module (Tykky)
# On LUMI, pip-containerize is provided by the lumi-container-wrapper module
if ! command -v pip-containerize &>/dev/null; then
    module load lumi-container-wrapper 2>/dev/null || module load LUMI lumi-container-wrapper 2>/dev/null || true
fi

if ! command -v pip-containerize &>/dev/null; then
    echo "ERROR: pip-containerize command not found."
    echo "Trying: module spider lumi-container-wrapper"
    exit 1
fi

echo "Using pip-containerize: $(which pip-containerize)"

# 2. Run pip-containerize to build containerized environment
# Note: --extra-index-url is already specified inside requirements.txt
pip-containerize new \
    --prefix "$TARGET_DIR" \
    "$REQUIREMENTS_FILE"

echo "=== Tykky Container Built Successfully! ==="
echo "To use this environment on LUMI:"
echo "  export PATH=\"$TARGET_DIR/bin:\$PATH\""
echo "Or load via Lmod module: module load LUMI-IQ-qaas/VLQ"
