#!/bin/bash
# ==============================================================================
# Setup Lmod Modulefile & Jupyter Kernel for LUMI-IQ on LUMI
# Project: LUMI-IQ (Task 2.1)
#
# Generates Lmod Lua modulefiles (Lumi-IQ-qaas/VLQ.lua)
# and registers the JupyterLab kernel for LUMI Open OnDemand (lumi.csc.fi).
# ==============================================================================

set -euo pipefail

ENV_DIR="${1:-$HOME/lumi-iq-env}"
MODULE_ROOT="${2:-${HOME}/modulefiles}"
IS_SHARED="${3:-false}"

MODULE_DIR="${MODULE_ROOT}/Lumi-IQ-qaas"

echo "=== Configuring LUMI-IQ Lmod Module & Jupyter Kernel ==="
echo "Target Software Directory : $ENV_DIR"
echo "Module Root Directory     : $MODULE_ROOT"
echo "Shared / World-Readable   : $IS_SHARED"

# 1. Create directory structure
mkdir -p "$MODULE_DIR"

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

# 3. Generate Primary Modulefile: Lumi-IQ-qaas/VLQ.lua
cat <<EOF > "$MODULE_DIR/VLQ.lua"
-- -*- lua -*-
-- =============================================================================
-- Module: Lumi-IQ-qaas/VLQ
-- Standard Notation: Lumi-IQ-<module_name>/<quantum_device>
-- =============================================================================

help([[
Module: Lumi-IQ-qaas/VLQ
Naming Scheme: Lumi-IQ-<module_name>/<quantum_device>
Module Name: qaas (Quantum-as-a-Service Client & Hybrid AI Stack)
Target Device: VLQ (24-qubit Star-topology transmon QPU at IT4Innovations)
Software Root: $ENV_DIR

Usage:
  module use $MODULE_ROOT
  module load Lumi-IQ-qaas/VLQ
  python your_script.py

Repository & Documentation:
  https://github.com/lumi-ai-factory/lumi-iq
]])

whatis("Name: Lumi-IQ-qaas/VLQ")
whatis("Version: 1.0")
whatis("Category: Quantum Computing / Hybrid HPC-QC")
whatis("Description: Official LUMI-IQ QaaS/VLQ Software Stack")
whatis("URL: https://github.com/lumi-ai-factory/lumi-iq")

local env_root = "$ENV_DIR"

prepend_path("PATH", pathJoin(env_root, "bin"))
prepend_path("JUPYTER_PATH", pathJoin(env_root, "share/jupyter"))
setenv("LUMI_IQ_ENV", env_root)
setenv("LUMI_IQ_BACKEND", "VLQ")
EOF

# 3b. Generate Simulator Modulefile: Lumi-IQ-qaas/SIM.lua
cat <<EOF > "$MODULE_DIR/SIM.lua"
-- -*- lua -*-
-- =============================================================================
-- Module: Lumi-IQ-qaas/SIM
-- Standard Notation: Lumi-IQ-<module_name>/<quantum_device>
-- =============================================================================

help([[
Module: Lumi-IQ-qaas/SIM
Naming Scheme: Lumi-IQ-<module_name>/<quantum_device>
Module Name: qaas (Quantum-as-a-Service Client & Hybrid AI Stack)
Target Device: Local High-Performance Simulator (Qiskit Aer on AMD EPYC CPU & AMD Instinct GPU)
Software Root: $ENV_DIR

Usage:
  module use $MODULE_ROOT
  module load Lumi-IQ-qaas/SIM
  python your_script.py

Repository & Documentation:
  https://github.com/lumi-ai-factory/lumi-iq
]])

whatis("Name: Lumi-IQ-qaas/SIM")
whatis("Version: 1.0")
whatis("Category: Quantum Computing / Hybrid HPC-QC Simulator")
whatis("Description: Official LUMI-IQ Simulation Stack (CPU/GPU local simulation)")
whatis("URL: https://github.com/lumi-ai-factory/lumi-iq")

local env_root = "$ENV_DIR"

prepend_path("PATH", pathJoin(env_root, "bin"))
prepend_path("JUPYTER_PATH", pathJoin(env_root, "share/jupyter"))
setenv("LUMI_IQ_ENV", env_root)
setenv("LUMI_IQ_BACKEND", "SIM")
EOF

# 4. Create default symlink for Lmod (default to VLQ)
ln -sf "VLQ.lua" "$MODULE_DIR/default"

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
echo "  module load Lumi-IQ-qaas/VLQ"
echo ""
echo "Verify functionality:"
echo "  python -c 'import qaas, py4lexis, iqm.qiskit_iqm; print(\"LUMI-IQ Module Ready!\")'"
echo "======================================================================"
