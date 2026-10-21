-- -*- lua -*-
-- =============================================================================
-- Standard Notation: Lumi-IQ-<module_name>/<quantum_device>
-- Module: Lumi-IQ-qaas/SIM
-- Central System-Wide Deployment: /appl/local/lumiiq
-- =============================================================================

help([[
Module: Lumi-IQ-qaas/SIM
Naming Scheme: Lumi-IQ-<module_name>/<quantum_device>
Module Name: qaas (Quantum-as-a-Service Client & Hybrid AI Stack)
Target Device: Local High-Performance Simulator (Qiskit Aer on LUMI compute nodes)
Software Root: /appl/local/lumiiq/software/lumi-iq-env

Features:
  - Fast local simulation of quantum circuits directly on LUMI compute nodes
  - Accelerated statevector, density matrix, and Matrix Product State (MPS) methods
  - No external LEXIS credentials or network connectivity required
  - Automatically sets LUMI_IQ_BACKEND="SIM" for CLI scripts

Usage:
  module use /appl/local/lumiiq/modulefiles
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

local base_root = "/appl/local/lumiiq"
local env_root  = pathJoin(base_root, "software/lumi-iq-env")

prepend_path("PATH", pathJoin(env_root, "bin"))
prepend_path("JUPYTER_PATH", pathJoin(env_root, "share/jupyter"))
setenv("LUMI_IQ_ENV", env_root)
setenv("LUMI_IQ_ROOT", base_root)
setenv("LUMI_IQ_BACKEND", "SIM")
setenv("LUMI_IQ_MODULE_ROOT", pathJoin(base_root, "modulefiles"))
