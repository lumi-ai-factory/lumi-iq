-- -*- lua -*-
-- =============================================================================
-- Standard Notation: Lumi-IQ-<module_name>/<quantum_device>
-- Module: Lumi-IQ-qaas/VLQ
-- Central System-Wide Deployment: /appl/local/lumiiq
-- =============================================================================

help([[
Module: Lumi-IQ-qaas/VLQ
Naming Scheme: Lumi-IQ-<module_name>/<quantum_device>
Module Name: qaas (Quantum-as-a-Service Client & Hybrid AI Stack)
Target Device: VLQ (24-qubit Star-topology transmon QPU at IT4Innovations)
Software Root: /appl/local/lumiiq/software/lumi-iq-env

Usage:
  module use /appl/local/lumiiq/modulefiles
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

local base_root = "/appl/local/lumiiq"
local env_root  = pathJoin(base_root, "software/lumi-iq-env")

prepend_path("PATH", pathJoin(env_root, "bin"))
prepend_path("JUPYTER_PATH", pathJoin(env_root, "share/jupyter"))
setenv("LUMI_IQ_ENV", env_root)
setenv("LUMI_IQ_ROOT", base_root)
setenv("LUMI_IQ_BACKEND", "VLQ")
setenv("LUMI_IQ_MODULE_ROOT", pathJoin(base_root, "modulefiles"))
