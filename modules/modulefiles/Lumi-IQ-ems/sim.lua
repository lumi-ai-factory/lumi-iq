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
Target Device: Local High-Performance Simulator (Qiskit Aer on LUMI compute nodes)
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
local sim_dir   = pathJoin(base_root, "software/lumi-iq-sim")
if not isDir(sim_dir) then
    sim_dir     = pathJoin(base_root, "lumi-iq-sim")
end
local env_root  = isDir(sim_dir) and sim_dir or pathJoin(base_root, "software/lumi-iq-env")
if not isDir(env_root) then
    env_root    = pathJoin(base_root, "lumi-iq-env")
end

prepend_path("PATH", pathJoin(env_root, "bin"))
prepend_path("JUPYTER_PATH", pathJoin(env_root, "share/jupyter"))
setenv("LUMI_IQ_ENV", env_root)
setenv("LUMI_IQ_ROOT", base_root)
setenv("LUMI_IQ_BACKEND", "SIM")
setenv("LUMI_IQ_MODULE_ROOT", pathJoin(base_root, "modulefiles"))
