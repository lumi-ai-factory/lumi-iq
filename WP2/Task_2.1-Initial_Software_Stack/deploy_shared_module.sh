#!/bin/bash
# ==============================================================================
# Deploy Shared LUMI-IQ Module for All Users on LUMI
# Project: LUMI-IQ (Task 2.1)
#
# Copies/deploys the Tykky container image to the shared project directory
# (/project/project_462001789/software/lumi-iq-env) and creates shared Lmod
# modulefiles accessible by all project members and consortium users.
# ==============================================================================

set -euo pipefail

PROJECT_ID="${1:-project_462001789}"
SHARED_ROOT="/project/${PROJECT_ID}"
SHARED_SW_DIR="${SHARED_ROOT}/software/lumi-iq-env"
SHARED_MODULE_ROOT="${SHARED_ROOT}/modulefiles"

SOURCE_ENV="${2:-$HOME/lumi-iq-env}"

echo "======================================================================"
echo "DEPLOYING SHARED LUMI-IQ MODULE FOR ALL USERS"
echo "======================================================================"
echo "Project Allocation  : $PROJECT_ID"
echo "Shared Root Path    : $SHARED_ROOT"
echo "Shared Software Dir : $SHARED_SW_DIR"
echo "Shared Module Dir   : $SHARED_MODULE_ROOT"
echo "Source Environment  : $SOURCE_ENV"
echo "----------------------------------------------------------------------"

# 1. Verify source container exists
if [ ! -d "$SOURCE_ENV" ]; then
    echo "ERROR: Source environment $SOURCE_ENV not found."
    echo "Please build it first with: bash build_tykky_module.sh"
    exit 1
fi

# 2. Verify shared project directory exists
if [ ! -d "$SHARED_ROOT" ]; then
    echo "Notice: $SHARED_ROOT not found directly, checking fallback candidate..."
    if [ -d "/scratch/${PROJECT_ID}" ]; then
        SHARED_ROOT="/scratch/${PROJECT_ID}"
        SHARED_SW_DIR="${SHARED_ROOT}/software/lumi-iq-env"
        SHARED_MODULE_ROOT="${SHARED_ROOT}/modulefiles"
        echo "Using scratch project path: $SHARED_ROOT"
    else
        echo "ERROR: Neither /project/$PROJECT_ID nor /scratch/$PROJECT_ID accessible."
        echo "Please check your project allocation."
        exit 1
    fi
fi

# 3. Create destination software directory and copy container
echo "Syncing Tykky container to shared location..."
mkdir -p "$(dirname "$SHARED_SW_DIR")"
if [ "$SOURCE_ENV" != "$SHARED_SW_DIR" ]; then
    rm -rf "$SHARED_SW_DIR"
    cp -a "$SOURCE_ENV" "$SHARED_SW_DIR"
fi

# 4. Enforce read/execute permissions for project group and others
echo "Setting shared permissions (g+rX, o+rX)..."
chmod -R g+rX,o+rX "$SHARED_SW_DIR" 2>/dev/null || true

# 5. Create Shared Lmod Modulefiles
echo "Generating shared Lmod module definitions..."
mkdir -p "${SHARED_MODULE_ROOT}/lumi-iq"
mkdir -p "${SHARED_MODULE_ROOT}/LUMI-IQ-qaas"

# Module: lumi-iq/1.0.lua
cat <<EOF > "${SHARED_MODULE_ROOT}/lumi-iq/1.0.lua"
-- LUMI-IQ Hybrid Quantum-Classical Environment Module (Shared System-Wide)
help([[
Module: lumi-iq/1.0
Description: LUMI-IQ Hybrid Quantum-Classical Software Stack (Task 2.1)
Target Project: $PROJECT_ID (All Users)
Container Root: $SHARED_SW_DIR
Packages: Qiskit, Qiskit ML, Qiskit Nature, Qiskit Aer, PySCF, QaaS, IQM Client
Target Hardware: Czech National Quantum Computer (VLQ, 24-qubit Star topology QPU)

Usage:
  module use $SHARED_MODULE_ROOT
  module load lumi-iq
  python your_script.py
]])

whatis("Name: LUMI-IQ")
whatis("Version: 1.0")
whatis("Category: Quantum Computing / Hybrid HPC-QC")
whatis("Description: Shared LUMI-IQ Software Stack connecting LUMI to VLQ")
whatis("URL: https://opencode.it4i.eu/qclab/lumi-iq")

local env_root = "$SHARED_SW_DIR"

-- Prepend shared container wrapper bin directory to PATH
prepend_path("PATH", pathJoin(env_root, "bin"))
setenv("LUMI_IQ_ENV", env_root)
setenv("LUMI_IQ_BACKEND", "VLQ")
EOF

# Module: LUMI-IQ-qaas/VLQ.lua (Deliverable D2.1 naming scheme)
cat <<EOF > "${SHARED_MODULE_ROOT}/LUMI-IQ-qaas/VLQ.lua"
-- LUMI-IQ Official Deliverable D2.1 Module Alias
load("lumi-iq/1.0")
whatis("Description: Official LUMI-IQ Deliverable D2.1 QaaS/VLQ Software Stack")
EOF

# Set modulefile permissions
chmod -R g+rX,o+rX "$SHARED_MODULE_ROOT" 2>/dev/null || true

echo "======================================================================"
echo "[SUCCESS] Shared LUMI-IQ Module Deployed Successfully!"
echo "======================================================================"
echo ""
echo "HOW ANY USER CAN LOAD THIS MODULE:"
echo "----------------------------------------------------------------------"
echo "1. CLI / Slurm Scripts:"
echo "   module use $SHARED_MODULE_ROOT"
echo "   module load lumi-iq"
echo ""
echo "2. Permanent activation in ~/.bashrc:"
echo "   echo 'module use $SHARED_MODULE_ROOT' >> ~/.bashrc"
echo ""
echo "3. LUMI Open OnDemand JupyterLab (lumi.csc.fi):"
echo "   Under Advanced -> 'Script or path to script', enter:"
echo "   module use $SHARED_MODULE_ROOT"
echo "   module load lumi-iq"
echo "======================================================================"
