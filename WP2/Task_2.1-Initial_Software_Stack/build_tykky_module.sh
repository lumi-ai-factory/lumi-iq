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
module load LUMI lumi-container-wrapper 2>/dev/null || module load lumi-container-wrapper 2>/dev/null || true

# Robust fallback to LUMI system path if Lmod hierarchy differs:
if ! command -v pip-containerize &>/dev/null; then
    for candidate in /appl/lumi/SW/LUMI-*/common/EB/lumi-container-wrapper/*/bin/pip-containerize; do
        if [ -x "$candidate" ]; then
            export PATH="$(dirname "$candidate"):$PATH"
            break
        fi
    done
fi

if ! command -v pip-containerize &>/dev/null; then
    echo "ERROR: pip-containerize not found. Please run: module load LUMI lumi-container-wrapper"
    exit 1
fi

echo "Using pip-containerize: $(which pip-containerize)"

# 2. Run pip-containerize to build containerized environment
pip-containerize new \
    --prefix "$TARGET_DIR" \
    "$REQUIREMENTS_FILE"

echo "=== Tykky Container Built Successfully! ==="
echo "To use this environment on LUMI:"
echo "  export PATH=\"$TARGET_DIR/bin:\$PATH\""
