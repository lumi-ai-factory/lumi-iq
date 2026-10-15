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

# 1. Load LUMI environment
module purge
module load LUMI/24.03
module load cotainr 2>/dev/null || true

# 2. Run pip-containerize to build containerized environment
# Note: pip-containerize is LUMI's official Tykky tool
pip-containerize new \
    --prefix "$TARGET_DIR" \
    --extra-index-url "https://opencode.it4i.eu/api/v4/projects/107/packages/pypi/simple" \
    "$REQUIREMENTS_FILE"

echo "=== Tykky Container Built Successfully! ==="
echo "To use this environment on LUMI:"
echo "  export PATH=\"$TARGET_DIR/bin:\$PATH\""
echo "Or load via Lmod module: module load LUMI-IQ-qaas/VLQ"
