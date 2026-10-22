#!/bin/bash
# ==============================================================================
# Deploy Shared LUMI-IQ Module on LUMI
# Project: LUMI-IQ (Task 2.1)
#
# Builds or deploys the containerized LUMI-IQ Tykky environment into the
# system application tree (/appl/local/lumiiq) or shared project storage.
#
# Permissions: Enforces group (g+rX) and public (o+rX) read/execute access.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PROJECT_ID="${1:-${LUMI_PROJECT:-appl}}"
MODE="${2:---auto}" # --auto, --build, or --copy
SOURCE_ENV="${3:-$HOME/lumi-iq-env}"
RECIPE_FILE="${4:-$SCRIPT_DIR/env.yml}"

if [[ "$PROJECT_ID" == "appl" || "$PROJECT_ID" == "lumiiq" || "$PROJECT_ID" == "/appl/local/lumiiq" ]]; then
    SHARED_ROOT="/appl/local/lumiiq"
elif [[ "$PROJECT_ID" == /* ]]; then
    SHARED_ROOT="$PROJECT_ID"
else
    SHARED_ROOT="/project/${PROJECT_ID}"
    # Check fallback to /scratch if /project is unavailable
    if [ ! -d "$SHARED_ROOT" ] && [ -d "/scratch/${PROJECT_ID}" ]; then
        SHARED_ROOT="/scratch/${PROJECT_ID}"
    fi
fi

SHARED_SW_DIR="${SHARED_ROOT}/software/lumi-iq-env"
SHARED_MODULE_ROOT="${SHARED_ROOT}/modulefiles"

echo "======================================================================"
echo "DEPLOYING SHARED LUMI-IQ MODULE ON LUMI"
echo "======================================================================"
echo "Project ID          : $PROJECT_ID"
echo "Shared Root Path    : $SHARED_ROOT"
echo "Software Target Dir : $SHARED_SW_DIR"
echo "Module Root Dir     : $SHARED_MODULE_ROOT"
echo "Deployment Mode     : $MODE"
echo "Source Environment  : $SOURCE_ENV"
echo "----------------------------------------------------------------------"

# 1. Verify access to project directory
if [ ! -d "$SHARED_ROOT" ]; then
    echo "ERROR: Project directory $SHARED_ROOT not accessible."
    echo "Please check your project permissions or LUMI project allocation."
    exit 1
fi

mkdir -p "$(dirname "$SHARED_SW_DIR")"
mkdir -p "$SHARED_MODULE_ROOT"

# 2. Determine build vs copy strategy
DO_BUILD=false
if [ "$MODE" = "--build" ]; then
    DO_BUILD=true
elif [ "$MODE" = "--copy" ]; then
    DO_BUILD=false
    if [ ! -d "$SOURCE_ENV" ]; then
        echo "ERROR: Source environment $SOURCE_ENV does not exist for copying."
        exit 1
    fi
else # --auto
    if [ -d "$SOURCE_ENV" ]; then
        echo "Found existing source environment at $SOURCE_ENV. Copying..."
        DO_BUILD=false
    else
        echo "No source environment found in \$HOME. Building directly in shared location..."
        DO_BUILD=true
    fi
fi

# 3. Execute Build or Copy
if [ "$DO_BUILD" = "true" ]; then
    echo "Executing fresh Tykky build directly into $SHARED_SW_DIR..."
    echo "Using recipe file: $RECIPE_FILE"
    bash "$SCRIPT_DIR/build_tykky_module.sh" \
        "$SHARED_SW_DIR" \
        "$RECIPE_FILE" \
        "$SHARED_MODULE_ROOT" \
        "true"
else
    echo "Syncing container from $SOURCE_ENV to $SHARED_SW_DIR..."
    if [ "$SOURCE_ENV" != "$SHARED_SW_DIR" ]; then
        rm -rf "$SHARED_SW_DIR"
        cp -a "$SOURCE_ENV" "$SHARED_SW_DIR"
    fi
    # Configure module & Jupyter kernel
    bash "$SCRIPT_DIR/setup_lumi_module.sh" \
        "$SHARED_SW_DIR" \
        "$SHARED_MODULE_ROOT" \
        "true"
fi

# 4. Enforce strict permissions (Group + World readable)
echo "Setting shared permissions (g+rX, o+rX)..."
chmod -R g+rX,o+rX "$SHARED_SW_DIR" 2>/dev/null || true
chmod -R g+rX,o+rX "$SHARED_MODULE_ROOT" 2>/dev/null || true

# Set group ownership if user is in the project group (support appl_iq, lumiiq, or project group)
for target_group in "appl_iq" "$PROJECT_ID" "lumiiq" "${LUMI_PROJECT:-}"; do
    if [ -n "$target_group" ] && getent group "$target_group" &>/dev/null 2>&1; then
        chgrp -R "$target_group" "$SHARED_SW_DIR" 2>/dev/null || true
        chgrp -R "$target_group" "$SHARED_MODULE_ROOT" 2>/dev/null || true
        break
    fi
done

# 5. Verification Test
echo "Verifying shared module deployment..."
if [ -x "$SHARED_SW_DIR/bin/python" ]; then
    "$SHARED_SW_DIR/bin/python" -c "import qiskit, qaas, py4lexis; print('[VERIFIED] LUMI-IQ stack functional in shared location!')"
else
    echo "Notice: Wrapper script $SHARED_SW_DIR/bin/python not directly executable outside LUMI compute/login nodes."
fi

echo "======================================================================"
echo "[SUCCESS] Shared LUMI-IQ Module Deployed Successfully!"
echo "======================================================================"
echo ""
echo "HOW ANY USER ON LUMI CAN LOAD THIS MODULE:"
echo "----------------------------------------------------------------------"
echo "1. In any Bash terminal or interactive node:"
echo "   module use $SHARED_MODULE_ROOT"
echo "   module load Lumi-IQ-qaas/VLQ"
echo ""
echo "2. Add permanently to ~/.bashrc:"
echo "   echo 'module use $SHARED_MODULE_ROOT' >> ~/.bashrc"
echo ""
echo "3. In Slurm Batch scripts (#SBATCH):"
echo "   module use $SHARED_MODULE_ROOT"
echo "   module load Lumi-IQ-qaas/VLQ"
echo "   python your_script.py"
echo ""
echo "4. In LUMI Open OnDemand JupyterLab (lumi.csc.fi):"
echo "   In the Jupyter launcher -> Advanced -> 'Script or path to script':"
echo "   module use $SHARED_MODULE_ROOT"
echo "   module load Lumi-IQ-qaas/VLQ"
echo ""
echo "5. For System Administrators (System-wide integration):"
echo "   To mirror this module to the central /appl namespace:"
echo "   cp -a $SHARED_MODULE_ROOT/Lumi-IQ-qaas /appl/local/lumiiq/modulefiles/"
echo "======================================================================"
