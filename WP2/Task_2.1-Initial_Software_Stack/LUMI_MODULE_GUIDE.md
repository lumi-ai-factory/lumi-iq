# LUMI-IQ Software Stack Deployment & Module Management on LUMI

This guide details how to build, deploy, manage, and share the **LUMI-IQ Hybrid HPC-QC Software Stack** (Task 2.1) on the **LUMI supercomputer**.

It covers three deployment models:
1. **Project-Level Shared Module (`/project/project_462001789/`)**: Accessible to all members of the LUMI-IQ project.
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
Builds the environment directly in the shared project storage (`/project/project_462001789/`) with permissions allowing all project members (and optionally all LUMI users) to execute it:

```bash
cd lumi-iq/WP2/Task_2.1-Initial_Software_Stack

# Build directly in /project/project_462001789/ (Takes ~3.5 min on login/compute node)
bash deploy_shared_module.sh project_462001789 --build
```

#### What this script does automatically:
1. Provisions the SquashFS container at `/project/project_462001789/software/lumi-iq-env`.
2. Sets group permissions (`g+rX`) and public permissions (`o+rX`).
3. Generates the Lmod modulefiles:
   - `/project/project_462001789/modulefiles/lumi-iq/1.0.lua`
   - `/project/project_462001789/modulefiles/lumi-iq/default` (symlink)
   - `/project/project_462001789/modulefiles/LUMI-IQ-qaas/VLQ.lua` (alias)
4. Registers the JupyterLab kernel in `/project/project_462001789/software/lumi-iq-env/share/jupyter/kernels/lumi-iq`.
5. Verifies package imports (`qiskit`, `qaas`, `py4lexis`, `iqm.qiskit_iqm`).

#### Available Environment Recipes (Deliverable D2.1 Mapping):
The repository provides recipes mapped directly to the Deliverable D2.1 tool tables:
- **`env.yml` / `recipes/env-initial.yml`**: Official Section 3.4.1 Baseline (Qiskit, Qiskit-IQM, QaaS, Py4LEXIS, PySCF, PyTorch, QCut / circuit-knitting-toolbox).
- **`recipes/env-later-additions.yml`**: Section 3.4.2 Roadmap additions (MQT Predictor, PennyLane, PennyLane-IQM, BQSKit, Qiskit Addons).
- **`recipes/env-complete.yml`**: Consolidated master recipe combining Section 3.4.1 and 3.4.2 into one single All-in-One environment.

To build with a specific recipe (e.g. the complete consolidated suite):
```bash
bash deploy_shared_module.sh project_462001789 --build "" recipes/env-complete.yml
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
module use /project/project_462001789/modulefiles

# Load the module:
module load lumi-iq

# Verify:
which python
python -c 'import qaas, py4lexis, iqm.qiskit_iqm; print("LUMI-IQ Active!")'
```

To make this persistent for every login session:
```bash
echo "module use /project/project_462001789/modulefiles" >> ~/.bashrc
```

### 2. In Slurm Batch Scripts (`#SBATCH`):
```bash
#!/bin/bash
#SBATCH --account=project_462001789
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:30:00

module purge
module use /project/project_462001789/modulefiles
module load lumi-iq

# Run quantum workflow
python submit_job.py --use-case 2 --backend VLQ
```

### 3. In Interactive JupyterLab (LUMI Open OnDemand – lumi.csc.fi):
Researchers can launch interactive Jupyter notebooks via the web portal:
1. Log in to [lumi.csc.fi](https://lumi.csc.fi) -> **Interactive Apps** -> **Jupyter**.
2. Select `project_462001789`, partition, and time limit.
3. Under **Settings -> Advanced**, set **Custom Python type** to `Script`.
4. In **Script or path to script**, enter:
   ```bash
   module use /project/project_462001789/modulefiles
   module load lumi-iq
   ```
5. Click **Launch**.
6. In JupyterLab, the **Python 3.12 (LUMI-IQ Hybrid QC)** kernel is automatically available in the Launcher menu and notebook kernel dropdown.

---

## 4. Integration into CSC / System-Wide LUMI Namespace (For System Administrators)

To transition the software stack into the official central LUMI application tree (`/appl/local/...` or LUMI software collections):

1. **Build container into the central application path**:
   ```bash
   bash build_tykky_module.sh \
       /appl/local/quantum/software/lumi-iq-env \
       env.yml \
       /appl/local/quantum/modulefiles \
       true
   ```

2. **Lmod Module Structure**:
   ```
   /appl/local/quantum/modulefiles/
   └── lumi-iq/
       ├── 1.0.lua
       └── default -> 1.0.lua
   ```

3. **Lmod Modulefile Definition (`1.0.lua`)**:
   ```lua
   -- -*- lua -*-
   help([[
   LUMI-IQ Hybrid Classical/Quantum AI Software Stack
   Work Package 2 (Task 2.1)
   Backend: Czech National Quantum Computer (VLQ, 24-qubit Star topology QPU)
   ]])

   whatis("Name: LUMI-IQ")
   whatis("Version: 1.0")
   whatis("Category: Quantum Computing / Hybrid HPC-QC")
   whatis("URL: https://opencode.it4i.eu/qclab/lumi-iq")

   local env_root = "/appl/local/quantum/software/lumi-iq-env"

   prepend_path("PATH", pathJoin(env_root, "bin"))
   prepend_path("JUPYTER_PATH", pathJoin(env_root, "share/jupyter"))
   setenv("LUMI_IQ_ENV", env_root)
   setenv("LUMI_IQ_BACKEND", "VLQ")
   ```

4. Once staged by CSC, users load the module directly without specifying custom `module use` paths:
   ```bash
   module load lumi-iq
   ```

---

## 5. Summary Table of Module Deployment Options

| Scope | Software Root (`LUMI_IQ_ENV`) | Module Root (`MODULEPATH`) | Target Audience | Permissions |
|---|---|---|---|---|
| **Project Shared** | `/project/project_462001789/software/lumi-iq-env` | `/project/project_462001789/modulefiles` | All LUMI-IQ consortium members | `chmod -R g+rX,o+rX` |
| **All LUMI Users** | `/project/project_462001789/software/lumi-iq-env` | `/project/project_462001789/modulefiles` | Any user with LUMI account (`module use`) | `chmod -R a+rX` |
| **System-Wide (CSC)** | `/appl/local/quantum/software/lumi-iq-env` | `/appl/local/quantum/modulefiles` | Official LUMI module catalog | Managed by CSC |
| **User Sandbox** | `$HOME/lumi-iq-env` | `$HOME/modulefiles` | Individual developer sandbox | Private (`chmod 700`) |
