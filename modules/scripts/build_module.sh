#!/bin/bash
# ==============================================================================
# LUMI-IQ Module Builder via Tykky (conda-containerize)
#
# Adheres to LUMI Lustre Parallel Filesystem Policy:
# Compiles Python 3.12 dependencies into an immutable SquashFS image.
# ==============================================================================

set -euo pipefail

# ANSI color codes
BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

TARGET_ENV="${1:-/pfs/lustrep1/appl/local/lumiiq/software/lumi-iq-env}"
RECIPE_FILE="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULES_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Resolve recipe file
if [ -z "$RECIPE_FILE" ]; then
    RECIPE_FILE="$MODULES_DIR/recipes/env-initial.yml"
fi

if [ ! -f "$RECIPE_FILE" ]; then
    echo -e "${RED}[ERROR] Recipe file not found: $RECIPE_FILE${RESET}"
    exit 1
fi

echo -e "${BOLD}${CYAN}======================================================================${RESET}"
echo -e "${BOLD}${CYAN}            LUMI-IQ Module Build (conda-containerize)                ${RESET}"
echo -e "${BOLD}${CYAN}======================================================================${RESET}"
echo -e "Target Environment : ${BOLD}$TARGET_ENV${RESET}"
echo -e "Recipe File        : ${BOLD}$RECIPE_FILE${RESET}"
echo -e "${CYAN}----------------------------------------------------------------------${RESET}"

# 1. Clean environment
module unload Lumi-IQ-qaas/VLQ 2>/dev/null || true
module unload Lumi-IQ-qaas/SIM 2>/dev/null || true
module unload lumi-iq 2>/dev/null || true
unset PYTHONPATH 2>/dev/null || true
unset PYTHONHOME 2>/dev/null || true
unset CONDA_NO_PLUGINS 2>/dev/null || true
export APPTAINERENV_PYTHONPATH=""
export SINGULARITYENV_PYTHONPATH=""
export APPTAINERENV_PYTHONHOME=""
export SINGULARITYENV_PYTHONHOME=""

# Strip any existing lumi-iq / lumiiq container paths from PATH to satisfy Tykky validation
NEW_PATH=""
IFS=':' read -ra ADDR <<< "$PATH"
for p in "${ADDR[@]}"; do
    if [[ "$p" != *"lumi-iq"* && "$p" != *"lumiiq"* && "$p" != *"$TARGET_ENV"* && -n "$p" ]]; then
        if [ -z "$NEW_PATH" ]; then
            NEW_PATH="$p"
        else
            NEW_PATH="$NEW_PATH:$p"
        fi
    fi
done
export PATH="$NEW_PATH"

# 2. Check Tykky
module load LUMI lumi-container-wrapper 2>/dev/null || module load lumi-container-wrapper 2>/dev/null || true

if ! command -v conda-containerize &>/dev/null; then
    for candidate in /appl/lumi/SW/LUMI-*/common/EB/lumi-container-wrapper/*/bin/conda-containerize; do
        if [ -x "$candidate" ]; then
            export PATH="$(dirname "$candidate"):$PATH"
            break
        fi
    done
fi

if ! command -v conda-containerize &>/dev/null; then
    echo -e "${RED}[ERROR] conda-containerize not found. Run: module load LUMI lumi-container-wrapper${RESET}"
    exit 1
fi

echo -e "Using conda-containerize: $(which conda-containerize)"

# 3. Clean existing target environment if rebuilding
if [ -d "$TARGET_ENV" ]; then
    echo -e "${YELLOW}[NOTICE] Removing existing environment at $TARGET_ENV for fresh build...${RESET}"
    rm -rf "$TARGET_ENV"
fi
mkdir -p "$(dirname "$TARGET_ENV")"

# 4. Prepare post-install hook for QaaS client (physical VLQ access without dependency pin conflict)
POST_SCRIPT="$(mktemp /tmp/post_qaas_XXXXXX.sh)"
cat << 'EOF' > "$POST_SCRIPT"
#!/bin/bash
pip install --no-deps --extra-index-url https://opencode.it4i.eu/api/v4/projects/107/packages/pypi/simple qaas==0.5.4
EOF
chmod +x "$POST_SCRIPT"

# 5. Execute conda-containerize
echo -e "${BOLD}Building container image via Tykky with post-install hook... (approx. 3-4 minutes)${RESET}"
conda-containerize new \
    --prefix "$TARGET_ENV" \
    --post-install "$POST_SCRIPT" \
    "$RECIPE_FILE"

rm -f "$POST_SCRIPT"

# 5. Register Jupyter kernel inside the container tree
KERNEL_DIR="$TARGET_ENV/share/jupyter/kernels/lumi-iq"
mkdir -p "$KERNEL_DIR"
if [ -f "$MODULES_DIR/kernel/kernel.json" ]; then
    cp "$MODULES_DIR/kernel/kernel.json" "$KERNEL_DIR/kernel.json"
else
    cat <<EOF > "$KERNEL_DIR/kernel.json"
{
  "argv": [
    "$TARGET_ENV/bin/python",
    "-m",
    "ipykernel_launcher",
    "-f",
    "{connection_file}"
  ],
  "display_name": "Python 3.12 (LUMI-IQ Hybrid QC)",
  "language": "python",
  "metadata": {
    "debugger": true
  }
}
EOF
fi

# 6. Set shared permissions
chmod -R g+rX,o+rX "$TARGET_ENV" 2>/dev/null || true

echo -e "${BOLD}${GREEN}======================================================================${RESET}"
echo -e "${BOLD}${GREEN}[SUCCESS] Module environment built successfully!${RESET}"
echo -e "${BOLD}${GREEN}======================================================================${RESET}"
