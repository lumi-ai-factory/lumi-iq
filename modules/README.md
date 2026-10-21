# LUMI-IQ Module Management & Packaging

**Project:** LUMI-IQ  
**Work Package:** Work Package 2 – Hybrid Classical/Quantum AI Computations  
**System Target:** LUMI Supercomputer & Web Interface (JupyterLab on `www.lumi.csc.fi`)  

---

## 1. Directory Structure

This directory contains the complete software packaging and deployment framework for LUMI-IQ modules on LUMI:

```text
modules/
├── README.md                      # This documentation
├── modulefiles/                   # Lmod Lua environment definitions
│   ├── Lumi-IQ-qaas/
│   │   ├── VLQ.lua               # Primary environment module (physical QPU target)
│   │   ├── SIM.lua               # High-performance simulation module (local CPU/GPU target)
│   │   └── default -> VLQ.lua
│   ├── Lumi-IQ-core/
│   │   ├── vlq.lua               # Core Qiskit & QaaS stack (VLQ QPU target)
│   │   ├── sim.lua               # Core Qiskit & QaaS stack (Simulator target)
│   │   └── default -> vlq.lua
│   ├── Lumi-IQ-qml/
│   │   ├── vlq.lua               # Quantum ML & AI stack (VLQ QPU target)
│   │   ├── sim.lua               # Quantum ML & AI stack (Simulator target)
│   │   └── default -> vlq.lua
│   └── Lumi-IQ-ems/
│       ├── vlq.lua               # Error mitigation & Classical Shadows (VLQ target)
│       ├── sim.lua               # Error mitigation & Classical Shadows (Simulator target)
│       └── default -> vlq.lua
├── recipes/                       # Pinned Conda/Pip environment definitions
│   ├── env-initial.yml           # Baseline software stack (Python 3.12, Qiskit 2.x, QaaS 0.5.3)
│   ├── env-complete.yml          # Consolidated All-in-One environment
│   └── env-later-additions.yml   # Future extensions (PennyLane, BQSKit, MQT Predictor)
├── scripts/                       # Deployment and maintenance scripts
│   ├── build_module.sh           # Tykky containerization (conda-containerize)
│   ├── sync_to_appl.sh           # Lustre (/pfs/lustrep1) -> /appl/local synchronization
│   ├── deploy_module.sh          # Master orchestrator (--appl | --project <ID> | --user)
│   └── verify_module.sh          # Installation smoke test & verification suite
└── kernel/                        # JupyterLab configuration
    └── kernel.json               # Open OnDemand Jupyter kernel definition
```

---

## 2. LUMI Architecture & Module Lifecycle

To comply with the **LUMI Lustre Parallel Filesystem Policy**, Python packages are packaged via the **LUMI Container Wrapper (Tykky)** into a single compressed SquashFS image (`lumi-iq-env.sqsh`), avoiding metadata IOPS degradation.

### Dual-Tier Architecture:
1. **Lustre Staging & Build Root (`/pfs/lustrep1/appl/local/lumiiq/`)**:
   Where containers are built and module recipes are maintained.
2. **System Application Root (`/appl/local/lumiiq/`)**:
   Where the synchronized modules and read-only container stubs live, accessible cluster-wide.
3. **Atomic Synchronization (`sync_to_appl.sh`)**:
   Copies updates from `/pfs/lustrep1` to `/appl/local` and enforces permissions (`g+rX,o+rX`).

---

## 3. How to Deploy the Module

### Option A: System-Wide Deployment (`/appl/local/lumiiq`)
```bash
# Build, sync, and verify in one step:
bash modules/scripts/deploy_module.sh --appl --build

# Or sync modulefiles only (without rebuilding container):
bash modules/scripts/deploy_module.sh --appl
```

### Option B: Project-Level Shared Deployment (`/project/<PROJECT_ID>/`)
```bash
bash modules/scripts/deploy_module.sh --project <PROJECT_ID> --build
```

### Option C: User Sandbox Deployment (`$HOME/lumi-iq-env`)
```bash
bash modules/scripts/deploy_module.sh --user --build
```

---

## 4. How End-Users Load the Module

```bash
# Add module path:
module use /appl/local/lumiiq/modulefiles

# Option A: Target physical 24-qubit VLQ QPU (default):
module load Lumi-IQ-qaas/VLQ

# Option B: Target high-performance local simulator (CPU/GPU, no credentials required):
module load Lumi-IQ-qaas/SIM

# Verify:
which python
python -c "import qiskit, qaas, py4lexis, pyscf, torch; print('LUMI-IQ Module Ready!')"
```
