# LUMI-IQ Software Stack Deployment & Module Management on LUMI

This guide details how to build, deploy, manage, and share the **LUMI-IQ Hybrid HPC-QC Software Stack** (Task 2.1) on the **LUMI supercomputer**.

It covers three deployment models:
1. **Project-Level Shared Module (`/project/<your_project_id>/`)**: Accessible to all members of the LUMI-IQ project.
2. **Public / All-Users Module (`chmod a+rX`)**: Accessible to any authorized LUMI user across the entire system.
3. **CSC / System-Wide Namespace Integration (`/appl/...`)**: Reference workflow for CSC application specialists and system administrators to stage the module into official LUMI software collections.

---

## 1. Prerequisites & Container Wrapper (Tykky)

In strict adherence to the **LUMI Lustre Parallel Filesystem Policy**, Python environments must not be installed directly on Lustre file systems (which causes severe metadata degradation). 

Instead, the stack is compiled using the **LUMI Container Wrapper (Tykky)** via `conda-containerize`, producing a single self-contained SquashFS container image mounted transparently at runtime.

### Loading Tykky on LUMI:
```bash
module load LUMI
module load lumi-container-wrapper
```

### Dependency Resolution (QaaS & Py4Lexis):
The QaaS client framework and Py4Lexis are distributed via the IT4Innovations OpenCode Package Registry:
```
--extra-index-url https://opencode.it4i.eu/api/v4/projects/107/packages/pypi/simple
```
This repository is publicly readable (HTTP 200) without requiring credentials or private tokens. Both `env.yml` and `requirements.txt` already include this index.

---

## 2. Fast-Track Deployment Modes

### Mode A: Shared Project Deployment (Recommended for LUMI-IQ)
Builds the environment directly in the shared project storage (`/project/<your_project_id>/`) with permissions allowing all project members (and optionally all LUMI users) to execute it:

```bash
cd lumi-iq/WP2/Task_2.1-Initial_Software_Stack

# Build directly in /project/<your_project_id>/ (Takes ~3.5 min on login/compute node)
bash modules/scripts/deploy_module.sh --project <your_project_id> --build
```

#### What this script does automatically:
1. Provisions the SquashFS container at `/project/<your_project_id>/software/lumi-iq-env`.
2. Sets group permissions (`g+rX`) and public permissions (`o+rX`).
3. Generates the Lmod modulefiles:
   - `/project/<your_project_id>/modulefiles/Lumi-IQ-qaas/VLQ.lua`
   - `/project/<your_project_id>/modulefiles/Lumi-IQ-qaas/default` (symlink)
4. Registers the JupyterLab kernel in `/project/<your_project_id>/software/lumi-iq-env/share/jupyter/kernels/lumi-iq`.
5. Verifies package imports (`qiskit`, `qaas`, `py4lexis`, `iqm.qiskit_iqm`).

#### Available Environment Recipes:
The repository provides recipes mapped directly to the software stack tool tables:
- **`env.yml` / `recipes/env-initial.yml`**: Baseline software stack (Qiskit, Qiskit-IQM, QaaS, Py4LEXIS, PySCF, PyTorch, QCut / circuit-knitting-toolbox).
- **`recipes/env-later-additions.yml`**: Roadmap additions (MQT Predictor, PennyLane, PennyLane-IQM, BQSKit, Qiskit Addons).
- **`recipes/env-complete.yml`**: Consolidated master recipe combining baseline and additions into one single All-in-One environment.

To build with a specific recipe (e.g. the complete consolidated suite):
```bash
bash modules/scripts/deploy_module.sh --project <your_project_id> --build "" recipes/env-complete.yml
```

---

### Mode B: User-Level Private Sandbox (Individual Testing)
Builds an isolated module in the user's home directory (`$HOME/lumi-iq-env` and `$HOME/modulefiles`):

```bash
cd lumi-iq/WP2/Task_2.1-Initial_Software_Stack
bash build_tykky_module.sh
```

---

## 3. How Users Load and Run the Module

### 1. In Interactive Bash / Command Line (SSH or `salloc`):
```bash
# Add the project module path:
module use /project/<your_project_id>/modulefiles

# Load the module:
module load Lumi-IQ-qaas/VLQ

# Verify:
which python
python -c 'import qaas, py4lexis, iqm.qiskit_iqm; print("LUMI-IQ Active!")'

# Configure LEXIS project allocation:
export LEXIS_PROJECT=your_vlq_project

# Authenticate once via browser (OAuth 2.0 Device Flow, saves to ~/.lumi-iq/token):
python auth.py
```

To make module loading and project export persistent for every login session:
```bash
echo "module use /project/<your_project_id>/modulefiles" >> ~/.bashrc
echo "export LEXIS_PROJECT=your_vlq_project" >> ~/.bashrc
```

### 2. In Slurm Batch Scripts (`#SBATCH`):
```bash
#!/bin/bash
#SBATCH --account=<your_project_id>
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:30:00

module purge
module use /project/<your_project_id>/modulefiles
module load Lumi-IQ-qaas/VLQ

# Configure LEXIS project allocation
export LEXIS_PROJECT=your_vlq_project

# Run quantum workflow (reads token automatically from ~/.lumi-iq/token)
python submit_job.py --use-case 2 --backend VLQ
```

### 3. In Interactive JupyterLab (LUMI Open OnDemand – lumi.csc.fi):
Researchers can launch interactive Jupyter notebooks via the web portal:
1. Log in to [lumi.csc.fi](https://lumi.csc.fi) -> **Interactive Apps** -> **Jupyter**.
2. Select `<your_project_id>`, partition, and time limit.
3. Under **Settings -> Advanced**, set **Custom Python type** to `Script`.
4. In **Script or path to script**, enter:
   ```bash
   module use /project/<your_project_id>/modulefiles
   module load Lumi-IQ-qaas/VLQ
   ```
5. Click **Launch**.
6. In JupyterLab, the **Python 3.12 (LUMI-IQ Hybrid QC)** kernel is automatically available in the Launcher menu and notebook kernel dropdown.

---

## 4. Integration into CSC / System-Wide LUMI Namespace (`/appl/local/lumiiq`)

The official system-wide LUMI-IQ application directory on LUMI is configured at:
* **Production Runtime Path:** `/appl/local/lumiiq/`
* **Lustre Staging & Build Root:** `/pfs/lustrep1/appl/local/lumiiq/`
* **Sync Script:** `/appl/local/lumiiq/scripts/sync_to_appl.sh` (mirrored from `/pfs/lustrep1/appl/local/lumiiq/scripts/`)

### Automated Staging, Build & Sync Workflow:
1. **End-to-End Automated Deployment**:
   ```bash
   bash /appl/local/lumiiq/scripts/deploy_to_lumiiq.sh --all
   ```

2. **Manual Step-by-Step Deployment (System Maintainers)**:
   ```bash
   # Step A: Build Tykky container in Lustre staging
   bash /appl/local/lumiiq/scripts/build_container_module.sh \
       /pfs/lustrep1/appl/local/lumiiq/software/lumi-iq-env \
       env.yml

   # Step B: Synchronize Lustre staging to system /appl/local
   bash /appl/local/lumiiq/scripts/sync_to_appl.sh

   # Step C: Verify deployment
   bash /appl/local/lumiiq/scripts/verify_module.sh
   ```

3. **Lmod Module Structure (`/appl/local/lumiiq/modulefiles`)**:
   ```
   /appl/local/lumiiq/modulefiles/
   ├── Lumi-IQ-qaas/
   │   ├── VLQ.lua
   │   └── default -> VLQ.lua
   ├── Lumi-IQ-core/
   │   └── vlq.lua
   └── Lumi-IQ-qml/
       └── vlq.lua
   ```

4. **Loading the System Module**:
   ```bash
   module use /appl/local/lumiiq/modulefiles
   module load Lumi-IQ-qaas/VLQ
   ```

---

## 5. Summary Table of Module Deployment Options

| Scope | Software Root (`LUMI_IQ_ENV`) | Module Root (`MODULEPATH`) | Target Audience | Permissions |
|---|---|---|---|---|
| **System-Wide (`/appl`)** | `/appl/local/lumiiq/software/lumi-iq-env` | `/appl/local/lumiiq/modulefiles` | Official LUMI system-wide catalog | Managed via `sync_to_appl.sh` (`g+rX,o+rX`) |
| **Project Shared** | `/project/<your_project_id>/software/lumi-iq-env` | `/project/<your_project_id>/modulefiles` | All LUMI-IQ consortium members | `chmod -R g+rX,o+rX` |
| **All LUMI Users** | `/project/<your_project_id>/software/lumi-iq-env` | `/project/<your_project_id>/modulefiles` | Any user with LUMI account (`module use`) | `chmod -R a+rX` |
| **User Sandbox** | `$HOME/lumi-iq-env` | `$HOME/modulefiles` | Individual developer sandbox | Private (`chmod 700`) |
