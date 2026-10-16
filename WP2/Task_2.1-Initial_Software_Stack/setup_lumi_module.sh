#!/bin/bash
# ==============================================================================
# Setup Lmod Modulefile & Jupyter Kernel for LUMI-IQ on LUMI
# Project: LUMI-IQ (Task 2.1)
#
# Generates Lmod Lua modulefiles (lumi-iq/1.0.lua, default, and LUMI-IQ-qaas/VLQ.lua)
# and registers the JupyterLab kernel for LUMI Open OnDemand (lumi.csc.fi).
# ==============================================================================

set -euo pipefail

ENV_DIR="${1:-$HOME/lumi-iq-env}"
MODULE_ROOT="${2:-${HOME}/modulefiles}"
IS_SHARED="${3:-false}"

MODULE_DIR="${MODULE_ROOT}/lumi-iq"
ALIAS_DIR="${MODULE_ROOT}/LUMI-IQ-qaas"

echo "=== Configuring LUMI-IQ Lmod Module & Jupyter Kernel ==="
echo "Target Software Directory : $ENV_DIR"
echo "Module Root Directory     : $MODULE_ROOT"
echo "Shared / World-Readable   : $IS_SHARED"

# 1. Create directory structure
mkdir -p "$MODULE_DIR"
mkdir -p "$ALIAS_DIR"

# 2. Register JupyterLab Kernel inside container tree
KERNEL_DIR="${ENV_DIR}/share/jupyter/kernels/lumi-iq"
mkdir -p "$KERNEL_DIR"

cat <<EOF > "${KERNEL_DIR}/kernel.json"
{
  "argv": [
    "${ENV_DIR}/bin/python",
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

# Also register in user's personal Jupyter directory if writable
USER_KERNEL_DIR="${HOME}/.local/share/jupyter/kernels/lumi-iq"
if mkdir -p "$USER_KERNEL_DIR" 2>/dev/null; then
    cp "${KERNEL_DIR}/kernel.json" "${USER_KERNEL_DIR}/kernel.json" 2>/dev/null || true
fi

# 3. Generate Primary Modulefile: lumi-iq/1.0.lua
cat <<EOF > "$MODULE_DIR/1.0.lua"
-- -*- lua -*-
-- =============================================================================
-- LUMI-IQ Hybrid Quantum-Classical Software Stack
-- Project: LUMI-IQ (Horizon Europe Grant Agreement 101239031) - Work Package 2
-- =============================================================================

help([[
Module: lumi-iq/1.0
Description: LUMI-IQ Hybrid Quantum-Classical Software Stack (Task 2.1)
Environment: Containerized Python 3.12 (LUMI Tykky Container Wrapper)
Key Libraries: Qiskit, Qiskit Aer/Nature/ML, PySCF, QaaS, Py4LEXIS, IQM Client
Hardware Target: Czech National Quantum Computer (VLQ, 24-qubit Star topology QPU)

Usage in Bash / Slurm:
  module use $MODULE_ROOT
  module load lumi-iq
  python your_quantum_workflow.py

Interactive JupyterLab on LUMI Open OnDemand (lumi.csc.fi):
  The module automatically exposes the "Python 3.12 (LUMI-IQ Hybrid QC)"
  kernel to JupyterLab via JUPYTER_PATH.
]])

whatis("Name: LUMI-IQ")
whatis("Version: 1.0")
whatis("Category: Quantum Computing / Hybrid HPC-QC")
whatis("Description: LUMI-IQ Hybrid Quantum-Classical Stack connecting LUMI to physical QPUs")
whatis("URL: https://opencode.it4i.eu/qclab/lumi-iq")

local env_root = "$ENV_DIR"

-- Prepend Tykky container wrapper binaries to PATH
prepend_path("PATH", pathJoin(env_root, "bin"))

-- Expose container Jupyter kernel to LUMI Open OnDemand JupyterLab
prepend_path("JUPYTER_PATH", pathJoin(env_root, "share/jupyter"))

-- Environment markers for LUMI-IQ scripts
setenv("LUMI_IQ_ENV", env_root)
setenv("LUMI_IQ_BACKEND", "VLQ")
EOF

# 4. Create default symlink for Lmod (allows: module load lumi-iq)
ln -sf "1.0.lua" "$MODULE_DIR/default"

# 5. Create Deliverable D2.1 Standard Notation: Lumi-IQ-<module_name>/<quantum_device>
for alias_name in "Lumi-IQ-qaas" "LUMI-IQ-qaas"; do
    TARGET_ALIAS_DIR="${MODULE_ROOT}/${alias_name}"
    mkdir -p "$TARGET_ALIAS_DIR"
    cat <<EOF > "$TARGET_ALIAS_DIR/VLQ.lua"
-- -*- lua -*-
-- =============================================================================
-- Deliverable D2.1 Notation: Lumi-IQ-<module_name>/<quantum_device>
-- Module: ${alias_name}/VLQ
-- Description: Official LUMI-IQ Deliverable D2.1 Software Stack targeting VLQ QPU
-- =============================================================================

help([[
Module: ${alias_name}/VLQ
Deliverable D2.1 Notation: Lumi-IQ-<module_name>/<quantum_device>
Module Name: qaas (Quantum-as-a-Service Client & Hybrid AI Stack)
Target Device: VLQ (24-qubit Star-topology transmon QPU at IT4Innovations)

Usage:
  module load ${alias_name}/VLQ
  python your_script.py
]])

whatis("Name: ${alias_name}/VLQ")
whatis("Version: 1.0")
whatis("Category: Quantum Computing / Hybrid HPC-QC")
whatis("Description: Official LUMI-IQ Deliverable D2.1 QaaS/VLQ Software Stack")
whatis("URL: https://opencode.it4i.eu/qclab/lumi-iq")

local env_root = "$ENV_DIR"

prepend_path("PATH", pathJoin(env_root, "bin"))
prepend_path("JUPYTER_PATH", pathJoin(env_root, "share/jupyter"))
setenv("LUMI_IQ_ENV", env_root)
setenv("LUMI_IQ_BACKEND", "VLQ")
EOF
    ln -sf "VLQ.lua" "$TARGET_ALIAS_DIR/default"
done

# 6. Apply shared permissions if requested
if [ "$IS_SHARED" = "true" ] || [ "$IS_SHARED" = "1" ]; then
    echo "Applying shared permissions (g+rX, o+rX)..."
    chmod -R g+rX,o+rX "$ENV_DIR" 2>/dev/null || true
    chmod -R g+rX,o+rX "$MODULE_ROOT" 2>/dev/null || true
fi

# 7. Add to ~/.bashrc for user-level modules if not already present
if [ "$MODULE_ROOT" = "${HOME}/modulefiles" ]; then
    if ! grep -q "module use.*${HOME}/modulefiles" "$HOME/.bashrc" 2>/dev/null; then
        echo "module use \$HOME/modulefiles" >> "$HOME/.bashrc"
        echo "Notice: Added 'module use \$HOME/modulefiles' to ~/.bashrc"
    fi
fi

echo "======================================================================"
echo "[SUCCESS] LUMI-IQ Module configured successfully!"
echo "======================================================================"
echo "Module files: $MODULE_DIR/1.0.lua"
echo "Jupyter kernel: $KERNEL_DIR/kernel.json"
echo ""
echo "To load this module, run:"
echo "  module use $MODULE_ROOT"
echo "  module load lumi-iq"
echo ""
echo "Verify functionality:"
echo "  python -c 'import qaas, py4lexis, iqm.qiskit_iqm; print(\"LUMI-IQ Module Ready!\")'"
echo "======================================================================"
