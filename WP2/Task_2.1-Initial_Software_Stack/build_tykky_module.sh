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
MODULE_ROOT="${3:-$HOME/modulefiles}"
IS_SHARED="${4:-false}"

echo "=== Building LUMI-IQ Environment using Tykky (conda-containerize) ==="
echo "Target directory: $TARGET_DIR"
echo "Environment definition: $ENV_FILE"

# 0. Clean environment to prevent Tykky / Miniforge build collision
module unload lumi-iq Lumi-IQ-qaas Lumi-IQ 2>/dev/null || true
unset PYTHONPATH 2>/dev/null || true
unset PYTHONHOME 2>/dev/null || true
unset CONDA_NO_PLUGINS 2>/dev/null || true
export APPTAINERENV_PYTHONPATH=""
export SINGULARITYENV_PYTHONPATH=""
export APPTAINERENV_PYTHONHOME=""
export SINGULARITYENV_PYTHONHOME=""

NEW_PATH=""
IFS=':' read -ra ADDR <<< "$PATH"
for p in "${ADDR[@]}"; do
    if [[ "$p" != *"$TARGET_DIR"* && "$p" != *"lumi-iq-env"* && "$p" != *"lumiiq"* && -n "$p" ]]; then
        if [ -z "$NEW_PATH" ]; then
            NEW_PATH="$p"
        else
            NEW_PATH="$NEW_PATH:$p"
        fi
    fi
done
export PATH="$NEW_PATH"

# 1. Clean existing target directory if present for a fresh rebuild
if [ -d "$TARGET_DIR" ]; then
    echo "Notice: Removing existing $TARGET_DIR for a clean rebuild..."
    rm -rf "$TARGET_DIR"
fi

# 2. Load LUMI container wrapper module (Tykky)
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

# 2. Run conda-containerize new
conda-containerize new \
    --prefix "$TARGET_DIR" \
    "$ENV_FILE"

# 2b. Inject QaaS and fiqci-ems via conda-containerize update --post-install
echo "Injecting QaaS client for physical VLQ hardware access..."
POST_SCRIPT="$(mktemp /tmp/post_qaas_XXXXXX.sh)"
cat << 'EOF' > "$POST_SCRIPT"
#!/bin/bash
pip install --no-deps fiqci-ems
pip install --extra-index-url https://opencode.it4i.eu/api/v4/projects/107/packages/pypi/simple qaas==0.5.4
EOF
chmod +x "$POST_SCRIPT"
conda-containerize update "$TARGET_DIR" --post-install "$POST_SCRIPT"
rm -f "$POST_SCRIPT"

echo "=== Tykky Container Built Successfully! ==="

# 3. Automatically configure Lmod module
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/setup_lumi_module.sh" ]; then
    bash "$SCRIPT_DIR/setup_lumi_module.sh" "$TARGET_DIR" "$MODULE_ROOT" "$IS_SHARED"
fi
