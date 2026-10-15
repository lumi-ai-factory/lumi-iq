#!/bin/bash
# ==============================================================================
# Create Lmod Modulefile for LUMI-IQ (Tykky Environment) on LUMI
# ==============================================================================

set -euo pipefail

MODULE_ROOT="${HOME}/modulefiles"
MODULE_DIR="${MODULE_ROOT}/lumi-iq"
ENV_DIR="${1:-$HOME/lumi-iq-env}"

echo "Creating Lmod module for LUMI-IQ..."
mkdir -p "$MODULE_DIR"

cat <<EOF > "$MODULE_DIR/1.0.lua"
-- LUMI-IQ Hybrid Quantum-Classical Environment Module
help([[
Module: lumi-iq/1.0
Description: LUMI-IQ Hybrid Quantum-Classical Software Stack (Task 2.1)
Environment: Python 3.12 (Tykky Container Wrapper)
Packages: Qiskit, QaaS (Branch 40), IQM Client & Pulla, QScheduler
Hardware Target: VLQ (24-qubit Star topology QPU at IT4Innovations)

Usage:
  module use \$HOME/modulefiles
  module load lumi-iq
  python your_script.py
]])

whatis("Name: LUMI-IQ")
whatis("Version: 1.0")
whatis("Category: Quantum Computing / Hybrid HPC-QC")
whatis("Description: LUMI-IQ Hybrid Quantum-Classical Stack connecting LUMI to VLQ")
whatis("URL: https://opencode.it4i.eu/qclab/lumi-iq")

local env_root = "$ENV_DIR"

-- Prepend container wrapper bin directory to PATH
prepend_path("PATH", pathJoin(env_root, "bin"))
setenv("LUMI_IQ_ENV", env_root)
setenv("LUMI_IQ_BACKEND", "VLQ")
EOF

# Ensure module directory is recognized by Lmod
if ! grep -q "module use.*modulefiles" "$HOME/.bashrc" 2>/dev/null; then
    echo "module use \$HOME/modulefiles" >> "$HOME/.bashrc"
    echo "Added 'module use \$HOME/modulefiles' to ~/.bashrc"
fi

echo "=== Lmod Module Created Successfully ==="
echo "Module file location: $MODULE_DIR/1.0.lua"
echo ""
echo "Test it now with:"
echo "  module use \$HOME/modulefiles"
echo "  module load lumi-iq"
echo "  module list"
echo "  python -c 'import qaas, iqm.qiskit_iqm; print(\"LUMI-IQ module active!\")'"
