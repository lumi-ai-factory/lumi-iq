# LUMI-IQ Task 2.1: Initial Software Stack Deployment (Simulators, VLQ & LUMI)

This directory contains the initial software stack deployment, configuration scripts, and validation notebooks for **Task 2.1** under **Work Package 2 (WP2)** of the **LUMI-IQ** project.

It provides an end-to-end operational pipeline connecting the **LUMI supercomputer** with local high-performance quantum simulators (`qiskit-aer` on AMD EPYC CPUs and AMD Instinct GPUs) as well as physical quantum processors—specifically the Czech National Quantum Computer (**VLQ**, 24-qubit Star-topology transmon QPU at IT4Innovations as Phase 1 stand-in) via **QaaS**, **HEAppE**, and **QScheduler**, and paving the way for the co-located **LUMI-IQ** QPU in Phase 2.

---

## Directory Contents

| File | Description |
|---|---|
| **[vlq_bell_state.ipynb](vlq_bell_state.ipynb)** | Interactive Jupyter Notebook demonstrating Bell state preparation, transpilation, and execution on VLQ via QScheduler. Supports interactive browser login (OAuth Device Flow). |
| **[vlq_bell_state.py](vlq_bell_state.py)** | Standalone Python script executable in batch mode via Slurm. |
| **[requirements.txt](requirements.txt)** | Python dependencies referencing the IT4Innovations private PyPI repository for `qaas[iqm_qiskit]`, `iqm-client`, and Qiskit. |
| **[build_tykky_module.sh](build_tykky_module.sh)** | Script to containerize the software environment on LUMI using the **Tykky wrapper (`pip-containerize`)**, complying with the LUMI Lustre parallel file system policy. |
| **[deploy_shared_module.sh](deploy_shared_module.sh)** | Deploys container and modulefiles into system `/appl/local/lumiiq` or project space. |
| **[LUMI_MODULE_GUIDE.md](LUMI_MODULE_GUIDE.md)** | Comprehensive guide for module deployment, project-wide sharing, and CSC system-wide integration. |
| **[auth.py](auth.py)** | Standalone utility to obtain a fresh LEXIS token via OAuth Device Flow. |
| **[config.py](config.py)** | Centralized configuration loader for LUMI and LEXIS projects. |
| **[run_all_tests.sh](run_all_tests.sh)** | Master single-command test suite runner executing all stack checks, QPU connectivity, and all 4 WP2 use cases. |
| **[run_all_tests.py](run_all_tests.py)** | Underlying Python test orchestrator supporting `--backend SIM|VLQ`, selective test filters, and structured reporting. |
| **[use_cases/](use_cases/)** | Directory containing the 4 standardized WP2 use cases (Car Manufacturing, Health & Life Science, Terrestrial Network, QML Time Series) adapted for LUMI. |
| **[.env.example](.env.example)** | Template for local environment variable configuration (no secrets). |

---

## Quick Start for New Users (4 Simple Steps)

### Step 1: Clone the repository and checkout branch (on LUMI login node `uan`)
```bash
git clone https://github.com/lumi-ai-factory/lumi-iq.git
cd lumi-iq/WP2/Task_2.1-Initial_Software_Stack
```

### Step 2: Build software environment (One-time Setup, ~2-3 min)
Containerize dependencies into a SquashFS image via LUMI Tykky and register Lmod module:
```bash
bash build_tykky_module.sh
```

### Step 3: Activate the module
```bash
# Add modulepath:
module use /appl/local/lumiiq/modulefiles   # For central system-wide deployment
# (or: module use $HOME/modulefiles         # For local user sandbox build)

# Option A: Target local high-performance simulation (CPU/GPU, no credentials needed):
module load Lumi-IQ-qaas/SIM

# Option B: Target physical 24-qubit VLQ QPU (hardware execution):
module load Lumi-IQ-qaas/VLQ
```

### Step 4: Run your first quantum computation (Simulator or VLQ)
You can immediately verify the installation using the local quantum simulator or dispatch to physical hardware:

- **Option A: High-Performance Simulation on LUMI (No credentials required):**
  ```bash
  # Fast simulation benchmark using Qiskit Aer on CPU/GPU (~10 seconds)
  bash run_all_tests.sh --backend SIM
  ```
  *Requires no external tokens or network connection; verifies the complete software stack instantly.*

- **Option B: Physical Quantum Execution on VLQ QPU:**
  ```bash
  python submit_job.py --backend VLQ
  ```
  - **First launch (browser authentication):** The terminal prints a URL and 8-character user code. Follow the link to log in via browser (OAuth 2.0 Device Flow).
  - **Security:** Token is saved to `~/.lumi-iq/token` with strict `chmod 600` permissions.
  - **Queue-aware scheduling:** The job is submitted to Slurm (using `$LUMI_PROJECT`) with runtime `--time` and queue wait limit `--deadline`.
  - **Scratch execution:** All logs and `results.json` are isolated in `$SCRATCH`.
  - **Future runs:** Just run `python submit_job.py --backend VLQ` directly without browser intervention!

---

## 1. Environment Loading via Lmod Modules (Pure CLI)

Everything runs directly via standard Lmod environment modules:

1. **Load the module**:
   ```bash
   module use /appl/local/lumiiq/modulefiles

   # Option A: Local high-performance simulation (no credentials needed):
   module load Lumi-IQ-qaas/SIM

   # Option B: Physical 24-qubit VLQ QPU (hardware execution):
   module load Lumi-IQ-qaas/VLQ
   ```

2. **Verify active Python environment**:
   ```bash
   which python
   python -c "import qiskit, qiskit_aer, qaas, py4lexis, pyscf, torch; print('LUMI-IQ environment ready!')"
   ```

3. **Run your scripts or submit jobs**:
   ```bash
   python submit_job.py      # Submit batch job to Slurm
   # or run locally:
   python vlq_bell_state.py  # Run directly on login/interactive node
   ```

*(If you are working in LUMI Open OnDemand JupyterLab, simply open the built-in **Terminal** and use the exact same commands).*

---

## 2. Loading & Deploying the LUMI Module

### A. Central System-Wide Module (Default on LUMI):
Any authorized user on LUMI can load the pre-built, production-grade module directly:
```bash
module use /appl/local/lumiiq/modulefiles

# Simulation target (CPU/GPU, no credentials required):
module load Lumi-IQ-qaas/SIM

# Physical VLQ QPU target (hardware execution):
module load Lumi-IQ-qaas/VLQ
```

### B. Project-Level Shared Deployment (`/project/<PROJECT_ID>/`):
To deploy a project-specific copy of the environment:
```bash
bash ../../modules/scripts/deploy_module.sh --project <your_project_id> --build
```
Project members then load it via:
```bash
module use /project/<your_project_id>/modulefiles
module load Lumi-IQ-qaas/VLQ
```
*(Add `module use /appl/local/lumiiq/modulefiles` to `~/.bashrc` to make it permanently available).*

---

### Launching JupyterLab via LUMI Open OnDemand (lumi.csc.fi)

To launch an interactive JupyterLab session on LUMI pre-loaded with the `Lumi-IQ-qaas/VLQ` environment:

1. Log in to [lumi.csc.fi](https://lumi.csc.fi) and navigate to **Interactive Apps** &rarr; **Jupyter**.
2. Select your LUMI project account, partition, and resource limits.
3. Under **Settings**, select the **Advanced** tab.
4. Set **Custom Python type** to `Script`.
5. In **Script or path to script**, insert:
   ```bash
   module use $HOME/modulefiles
   module load Lumi-IQ-qaas/VLQ
   ```
6. *(Optional)* Check **Save settings** to persist this configuration across future sessions.
7. Click **Launch**.

JupyterLab will launch directly with the containerized LUMI-IQ environment active, allowing you to open and run `vlq_bell_state.ipynb` immediately without needing any extra kernel setup.

---

## 2. Centralized Project Configuration (`.env` or `~/.lumi-iq/config`)

You can change project settings for both **LUMI** and **LEXIS** in one single place:

```bash
# Local configuration (in task directory):
cp .env.example .env

# Or global configuration across all sessions ($HOME/.lumi-iq/config):
mkdir -p ~/.lumi-iq
cp .env.example ~/.lumi-iq/config
```

Contents of `.env` / `~/.lumi-iq/config`:
```bash
# LUMI Slurm account
LUMI_PROJECT=your_lumi_project_id

# LEXIS Platform project and QPU backend
LEXIS_PROJECT=your_vlq_project
LEXIS_RESOURCE=VLQ-CZ
```
All scripts (`submit_job.py`, `auth.py`, `vlq_bell_state.py`, `submit_lumi.sbatch`) automatically read these settings.

---

## 3. Dedicated Authentication (`auth.py`)

To obtain a fresh token at any time via browser login without submitting a Slurm job:

```bash
python auth.py
```

Follow the terminal link to log in (OAuth 2.0 Device Flow). The fresh token is saved to `~/.lumi-iq/token` (`chmod 600`).

---

## 4. Hybrid HPC-QC Batch Execution on LUMI (Slurm)

In compliance with the **LUMI Acceptable Use Policy**, production workloads and heavy classical computation (e.g. PySCF electronic structure integrals in UC 2, QUBO formulation in UC 3, QNN inference and optimization in UC 4) must **not** run on login nodes (`uan`). Instead, workloads run on dedicated LUMI compute nodes via Slurm, offloading quantum circuits to the IT4Innovations VLQ QPU across the network.

### Automated Queue-Aware Submission (`submit_job.py`)
`submit_job.py` submits any WP2 use case, custom script, or the full test suite to Slurm (using `$LUMI_PROJECT`):

```bash
cd WP2/Task_2.1-Initial_Software_Stack

# --- Simulation Mode (runs immediately on LUMI CPU/GPU compute nodes, no tokens needed) ---
# Run Use Case 4 (Electricity Price Forecasting) via Qiskit Aer simulation:
python submit_job.py --use-case 4 --backend SIM

# Run Use Case 2 (Health & Life Science VQE) on Simulator:
python submit_job.py --use-case 2 --backend SIM

# Run the complete Master Test Suite across all use cases on an HPC compute node (Simulator):
python submit_job.py --use-case all --backend SIM

# --- Physical Hardware Mode (offloads circuits to 24-qubit Star VLQ QPU via LEXIS) ---
# Run Use Case 4 with real VLQ QPU offload:
python submit_job.py --use-case 4 --backend VLQ

# Run Use Case 2 (Health & Life Science VQE) with VLQ QPU offload:
python submit_job.py --use-case 2 --backend VLQ

# Run Use Case 1 (Car Manufacturing Anomaly Detection) with VLQ QPU offload:
python submit_job.py --use-case 1 --backend VLQ

# Run Use Case 3 (Terrestrial Network QKD Routing) with VLQ QPU offload:
python submit_job.py --use-case 3 --backend VLQ

# Run the complete Master Test Suite across all 4 use cases on an HPC compute node (VLQ QPU):
python submit_job.py --use-case all --backend VLQ

# Run demo Bell state benchmark:
python submit_job.py --use-case bell
```

`submit_job.py` automatically:
1. Validates or refreshes the OAuth token, saving it to `~/.lumi-iq/token` (`chmod 600`).
2. Calculates exact token expiration timestamp and sets `--deadline` in Slurm.
3. Enforces the invariant:
   $$\text{Queue Wait Time} + \text{Execution Walltime} \le \text{Token Validity} - \text{Safety Margin}$$
   If the job waits too long in the Slurm queue and cannot complete before token expiration, Slurm automatically cancels it (`DEADLINE`) rather than dispatching it with expired credentials.
4. Isolates execution, logs, and outputs to `$SCRATCH/$USER/lumi-iq-jobs/run_<timestamp>/`, preserving a clean git working tree.

### Manual Submission
Alternatively, submit directly via `sbatch` using the saved token:
```bash
sbatch submit_lumi.sbatch
```

### Monitoring Jobs
```bash
squeue --me
scontrol show job <JOB_ID> | grep -E "(JobState|Deadline|TimeLimit)"
cat lumi_iq_<JOB_ID>.out
```

---

## 5. Automated Master Test Suite (`run_all_tests.sh`)

The master test suite can be executed in two modes:

### Mode A: Interactive Execution on Login Node (Fast Verification / Debugging)
Useful for rapid development, testing in simulation, or live terminal feedback:
```bash
cd WP2/Task_2.1-Initial_Software_Stack

# Fast local simulation mode (tests all 4 use cases + stack in ~1-2 minutes):
bash run_all_tests.sh --backend SIM

# Interactive execution with real VLQ QPU offload:
bash run_all_tests.sh --backend VLQ

# Run selected use cases only (e.g. Use Case 2 & 4):
bash run_all_tests.sh --use-cases 2,4

# Run only software stack and hardware connectivity checks:
bash run_all_tests.sh --skip-use-cases
```

### Mode B: Unattended Slurm HPC Job on LUMI Compute Node (Recommended for Production)
Submits the entire verification pipeline to Slurm compute nodes with QPU offload:
```bash
# Submit full test suite to Slurm compute node with VLQ QPU offload:
bash run_all_tests.sh --backend VLQ --slurm

# Or submit simulation verification to Slurm:
bash run_all_tests.sh --backend SIM --slurm
```
*(This is functionally equivalent to `python submit_job.py --use-case all --backend VLQ`).*

The test suite automatically:
1. Loads the `Lumi-IQ-qaas/VLQ` Lmod module if running in a fresh shell.
2. Checks all core Python packages (`qiskit`, `qiskit_aer`, `qaas`, `py4lexis`, `scipy`, `sklearn`, `pandas`, `networkx`, `matplotlib`, `dill`, `pyscf`).
3. Verifies active LEXIS credentials (`~/.lumi-iq/token`) and QPU target (`VLQ-CZ`).
4. Executes the core 2-qubit Bell state entanglement benchmark.
5. Executes all 4 standardized WP2 use cases sequentially with timing and validation.
6. Prints a formatted ASCII summary table with execution durations and status (`[ PASS ]`, `[ FAIL ]`, `[ SKIP ]`), returning exit code 0 on complete success.

