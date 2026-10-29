# LUMI-IQ: Hybrid Classical/Quantum AI Software Stack & Module Deployment

This repository serves as the official software codebase, unified module packaging repository, and verification suite for **Work Package 2 (WP2: Hybrid Classical/Quantum AI Computations)** of the **LUMI-IQ project**.

It establishes an end-to-end operational pipeline seamlessly bridging the **LUMI Supercomputer** (HPE Cray EX) with quantum execution backends:
1. **The VLQ Quantum Computer:** Physical 24-qubit Star-topology transmon QPU (hosted at IT4Innovations), interfaced via RESTful **QaaS** (Quantum-as-a-Service), **LEXIS Platform** (OIDC OAuth 2.0 Device Flow authentication), and **QScheduler**.
2. **Local Quantum Simulator:** High-performance quantum simulator (`qiskit-aer` on AMD EPYC CPU and AMD Instinct GPU nodes) running natively on LUMI without external credentials or network latency.

---

## Repository Structure

```text
lumi-iq/
├── README.md                                    # Master repository documentation (this file)
├── modules/                                     # Unified LUMI module packaging & deployment
│   ├── README.md                                # Comprehensive module deployment guide
│   ├── modulefiles/                             # Lmod Lua environment definitions
│   │   ├── Lumi-IQ-qaas/
│   │   │   ├── VLQ.lua                          # Primary environment module (physical QPU target)
│   │   │   ├── SIM.lua                          # Simulation module (local CPU/GPU target)
│   │   │   └── default -> VLQ.lua
│   │   ├── Lumi-IQ-core/
│   │   │   ├── vlq.lua                          # Core Qiskit & QaaS stack (VLQ QPU target)
│   │   │   ├── sim.lua                          # Core Qiskit & QaaS stack (Simulator target)
│   │   │   └── default -> vlq.lua
│   │   ├── Lumi-IQ-qml/
│   │   │   ├── vlq.lua                          # Quantum ML & AI stack (VLQ QPU target)
│   │   │   ├── sim.lua                          # Quantum ML & AI stack (Simulator target)
│   │   │   └── default -> vlq.lua
│   │   └── Lumi-IQ-ems/
│   │       ├── vlq.lua                          # Error mitigation & Classical Shadows (VLQ target)
│   │       ├── sim.lua                          # Error mitigation & Classical Shadows (Simulator target)
│   │       └── default -> vlq.lua
│   ├── recipes/                                 # Pinned Conda/Pip environment recipes
│   │   ├── env-initial.yml                      # Baseline software stack
│   │   ├── env-later-additions.yml              # Future roadmap extensions
│   │   └── env-complete.yml                     # Consolidated All-in-One master recipe
│   ├── scripts/                                 # Maintenance, build & synchronization scripts
│   │   ├── build_module.sh                      # Tykky (conda-containerize) container builder
│   │   ├── sync_to_appl.sh                      # Lustre (/pfs/lustrep1) -> /appl/local sync script
│   │   ├── deploy_module.sh                     # Master orchestrator (--appl | --project <ID> | --user)
│   │   └── verify_module.sh                     # Smoke test & verification script
│   └── kernel/                                  # JupyterLab Open OnDemand configuration
│       └── kernel.json                          # Open OnDemand kernel definition
└── WP2/
    ├── README.md                                # Work Package 2 overview
    └── Task_2.1-Initial_Software_Stack/         # Primary operational software suite
        ├── README.md                            # Detailed Task 2.1 user & developer manual
        ├── LUMI_MODULE_GUIDE.md                 # Complete module packaging & permissions guide
        ├── env.yml                              # Baseline Conda environment definition
        ├── requirements.txt                     # Pinned Python package dependencies
        ├── submit_job.py                        # Queue-aware Slurm batch submitter
        ├── submit_lumi.sbatch                   # Standard Slurm batch job template
        ├── auth.py                              # LEXIS OAuth 2.0 Device Flow authenticator
        ├── config.py                            # Centralized project configuration loader
        ├── run_all_tests.sh                     # Single-command master test runner
        ├── run_all_tests.py                     # Python test orchestrator (SIM & VLQ backends)
        ├── vlq_bell_state.ipynb                 # Interactive 2-qubit Bell state demo notebook
        ├── vlq_bell_state.py                    # Standalone Bell state script
        └── use_cases/                           # Standardized WP2 hybrid use cases
            ├── 01_car_manufacturing/            # UC1: Quantum kernel anomaly detection
            ├── 02_health_life_science/          # UC2: VQE & classical shadows molecular ground state
            ├── 03_terrestrial_network/          # UC3: QKD optical network routing via QUBO/QAOA
            └── 04_qml_time_series/              # UC4: QNN electricity spot-price forecasting
```

---

## Software Packaging on LUMI (Tykky & Lustre Architecture)

In compliance with the **LUMI Lustre Parallel Filesystem Policy**, Python packages are packaged using the **LUMI Container Wrapper (Tykky)** via `conda-containerize`. This encapsulates dependencies into a single immutable SquashFS container image (`lumi-iq-env.sqsh`), avoiding Lustre inode saturation.

### Central System Deployment (`/appl/local/lumiiq`)
On LUMI, central applications follow a two-tier model:
1. **Build & Staging Tier (`/pfs/lustrep1/appl/local/lumiiq`)**: Writable Lustre scratch space where containers are built and modulefiles are staged.
2. **Production Tier (`/appl/local/lumiiq`)**: Mounted across all login and compute nodes for user workloads.
3. **Synchronization (`sync_to_appl.sh`)**: An atomic rsync script synchronizing updates from `/pfs/lustrep1` to `/appl/local` with enforced group permissions (`g+rX,o+rX`).

---

## Quickstart for Users on LUMI

### 1. Loading the Module (CLI & Slurm Batch Jobs)

The LUMI-IQ module tree provides **dual execution targets** via Lmod:

```bash
# Add LUMI-IQ central modulepath:
module use /appl/local/lumiiq/modulefiles

# -----------------------------------------------------------------------------
# Target 1: Local High-Performance Simulation (CPU/GPU)
# -----------------------------------------------------------------------------
# Ideal for rapid local development, prototyping, algorithmic benchmarking, and CI.
# - Runs accelerated statevector / MPS simulation directly on LUMI compute nodes
# - Requires NO external network connection, tokens, or credentials
# - Automatically configures LUMI_IQ_BACKEND="SIM" for CLI runners
module load Lumi-IQ-qaas/SIM

# -----------------------------------------------------------------------------
# Target 2: Physical Quantum Hardware Offload (IT4I VLQ 24-Qubit QPU)
# -----------------------------------------------------------------------------
# Dispatches compiled circuits to the physical 24-qubit Star-topology QPU.
# - Offloads jobs over secure WAN via QaaS, LEXIS AAI, and QScheduler
# - Requires active LEXIS authentication token (run `python auth.py` once)
# - Automatically configures LUMI_IQ_BACKEND="VLQ" for CLI runners
module load Lumi-IQ-qaas/VLQ
```

#### Specialized Sub-Modules:
In addition to the primary all-in-one `Lumi-IQ-qaas` module, domain-specific modulefiles are available:
* **Core Quantum Stack:** `module load Lumi-IQ-core/sim` (Simulation) or `module load Lumi-IQ-core/vlq` (Hardware)
* **Quantum Machine Learning:** `module load Lumi-IQ-qml/sim` (Simulation) or `module load Lumi-IQ-qml/vlq` (Hardware)
* **Error Mitigation & Chemistry:** `module load Lumi-IQ-ems/sim` (Simulation) or `module load Lumi-IQ-ems/vlq` (Hardware)

#### Verifying Environment:
```bash
which python
python -c "import qiskit, qiskit_aer, qaas, py4lexis, pyscf, torch; print('LUMI-IQ environment ready!')"
```

To make the module permanently available in every login shell:
```bash
echo "module use /appl/local/lumiiq/modulefiles" >> ~/.bashrc
```

### 2. Interactive JupyterLab via LUMI Open OnDemand (`www.lumi.csc.fi`)
1. Log into **[www.lumi.csc.fi](https://www.lumi.csc.fi)** &rarr; **Interactive Apps** &rarr; **Jupyter**.
2. Select partition, time limit, and your LUMI project account.
3. Under **Settings** &rarr; **Advanced**, switch **Custom Python type** to `Script`.
4. In **Script or path to script**, insert either target:
   ```bash
   module use /appl/local/lumiiq/modulefiles
   # For local simulation (no credentials needed):
   module load Lumi-IQ-qaas/SIM

   # Or for physical QPU hardware access:
   # module load Lumi-IQ-qaas/VLQ
   ```
5. Click **Launch**. The **Python 3.12 (LUMI-IQ Hybrid QC)** kernel is pre-configured and immediately available in the notebook launcher.

### 3. Submitting Hybrid Batch Jobs to Slurm (`submit_job.py`)
Workloads must run on compute nodes in compliance with LUMI policies. The `submit_job.py` wrapper provides automated queue-aware token expiration enforcement and scratch-space execution:

```bash
cd WP2/Task_2.1-Initial_Software_Stack

# --- Simulation Mode (runs immediately on compute node, no tokens required) ---
# Submit Use Case 4 (Electricity Price Forecasting) via local Qiskit Aer simulation:
python submit_job.py --use-case 4 --backend SIM

# Submit Use Case 2 (Health & Life Science VQE) on Simulator:
python submit_job.py --use-case 2 --backend SIM

# Run the complete test suite across all 4 use cases on compute node (Simulator):
python submit_job.py --use-case all --backend SIM

# --- Physical Hardware Mode (offloads circuits to 24-qubit Star VLQ QPU via LEXIS) ---
# Submit Use Case 4 with physical VLQ QPU offload:
python submit_job.py --use-case 4 --backend VLQ

# Submit Use Case 2 (Health & Life Science VQE) with VLQ QPU offload:
python submit_job.py --use-case 2 --backend VLQ

# Submit Use Case 1 (Car Manufacturing Anomaly Detection) with VLQ QPU offload:
python submit_job.py --use-case 1 --backend VLQ

# Submit Use Case 3 (Terrestrial Network QKD Routing) with VLQ QPU offload:
python submit_job.py --use-case 3 --backend VLQ

# Run the complete test suite on compute node with VLQ QPU offload:
python submit_job.py --use-case all --backend VLQ
```

---

## Administration & Deployment Guide (For System Administrators & Maintainers)

To deploy or update the central `/appl/local/lumiiq` software module on LUMI:

```bash
# 1. Full end-to-end automated build, sync, and verification:
bash modules/scripts/deploy_module.sh --appl --build --recipe modules/recipes/env-initial.yml

# 2. Or user-space test build:
bash modules/scripts/deploy_module.sh --user --build --recipe modules/recipes/env-initial.yml

# 3. Synchronize Lustre staging to system /appl/local:
bash modules/scripts/sync_to_appl.sh

# 4. Verify installation and module imports:
bash modules/scripts/verify_module.sh
```

---

## Automated Master Test Suite (`run_all_tests.sh`)

Validate the entire software stack, hardware connectivity, and all 4 use cases with a single command:

```bash
cd WP2/Task_2.1-Initial_Software_Stack

# Fast simulation mode (validates all 4 use cases in ~1-2 minutes):
bash run_all_tests.sh --backend SIM

# Full physical QPU validation (dispatches circuits to VLQ QPU):
bash run_all_tests.sh --backend VLQ

# Submit validation suite as an unattended Slurm HPC job:
bash run_all_tests.sh --backend VLQ --slurm
```

---

## Project Information

* **Project:** LUMI-IQ
* **Work Package:** Work Package 2 – Hybrid Classical/Quantum AI Computations (WP2)
* **Repository & Codebase:** `https://github.com/lumi-ai-factory/lumi-iq`

---

## License

This software and deployment recipes are released under the terms of the project consortium agreement.
