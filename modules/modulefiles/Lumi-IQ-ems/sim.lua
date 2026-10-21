-- -*- lua -*-
-- =============================================================================
-- Standard Notation: Lumi-IQ-<module_name>/<quantum_device>
-- Module: Lumi-IQ-ems/sim
-- Central System-Wide Deployment: /appl/local/lumiiq
-- =============================================================================

help([[
Module: Lumi-IQ-ems/sim
Naming Scheme: Lumi-IQ-<module_name>/<quantum_device>
Module Name: ems (Error Mitigation & Classical Shadows)
Target Device: Local High-Performance Simulator (Qiskit Aer on AMD EPYC CPU & AMD Instinct GPU)
Software Root: /appl/local/lumiiq/software/lumi-iq-env

Included Packages: fiqci-ems, Classical Shadows, Mitiq, PySCF, QaaS Client, Qiskit

Usage:
  module use /appl/local/lumiiq/modulefiles
  module load Lumi-IQ-ems/sim
  python your_script.py
]])

whatis("Name: Lumi-IQ-ems/sim")
whatis("Version: 1.0")
whatis("Category: Quantum Computing / Hybrid HPC-QC Simulator")
whatis("Description: LUMI-IQ Error Mitigation & Classical Shadows Stack (Simulator target)")
whatis("URL: https://github.com/lumi-ai-factory/lumi-iq")

local base_root = "/appl/local/lumiiq"
local env_root  = pathJoin(base_root, "software/lumi-iq-env")

prepend_path("PATH", pathJoin(env_root, "bin"))
prepend_path("JUPYTER_PATH", pathJoin(env_root, "share/jupyter"))
setenv("LUMI_IQ_ENV", env_root)
setenv("LUMI_IQ_ROOT", base_root)
setenv("LUMI_IQ_BACKEND", "SIM")
setenv("LUMI_IQ_MODULE_ROOT", pathJoin(base_root, "modulefiles"))
