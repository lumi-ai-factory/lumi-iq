# LUMI-IQ Task 2.1: Initial Software Stack Deployment (VLQ & LUMI)

This directory contains the initial software stack deployment, configuration scripts, and validation notebooks for **Task 2.1** under **Work Package 2 (WP2)** of the **LUMI-IQ** project.

It provides an end-to-end operational pipeline connecting the **LUMI supercomputer** with the Czech National Quantum Computer (**VLQ**, 24-qubit Star-topology transmon QPU at IT4Innovations) via **QaaS**, **HEAppE**, and **QScheduler**.

---

## Directory Contents

| File | Description |
|---|---|
| **[vlq_bell_state.ipynb](vlq_bell_state.ipynb)** | Interactive Jupyter Notebook demonstrating Bell state preparation, transpilation, and execution on VLQ via QScheduler. Supports interactive browser login (OAuth Device Flow). |
| **[vlq_bell_state.py](vlq_bell_state.py)** | Standalone Python script executable in batch mode via Slurm. |
| **[requirements.txt](requirements.txt)** | Python dependencies referencing the IT4Innovations private PyPI repository for `qaas[iqm_qiskit]`, `iqm-client`, and Qiskit. |
| **[build_tykky_module.sh](build_tykky_module.sh)** | Script to containerize the software environment on LUMI using the **Tykky wrapper (`pip-containerize`)**, complying with the LUMI Lustre parallel file system policy. |
| **[setup_lumi_jupyter.sh](setup_lumi_jupyter.sh)** | Script to register the Tykky container as an official Jupyter kernel in **LUMI Open OnDemand** (`www.lumi.csc.fi`). |
| **[submit_lumi.sbatch](submit_lumi.sbatch)** | Official Slurm batch script template for non-interactive execution on LUMI compute nodes (`project_465003105`). |
| **[D2.1_Deliverable_Revised_Sections.md](D2.1_Deliverable_Revised_Sections.md)** | Revision document for Deliverable D2.1 addressing all peer-review comments and LUMI policy compliance. |
| **[.env.example](.env.example)** | Template for local environment variable configuration (no secrets). |

---

## 1. Interactive Execution on LUMI Open OnDemand (JupyterLab)

1. Navigate to **[www.lumi.csc.fi](https://www.lumi.csc.fi)** and select **Interactive Apps -> Jupyter**.
2. Configure your session:
   - **Project**: `project_465003105`
   - **Partition**: `interactive`
   - **Time**: `1:00:00`
3. Launch the session and open the built-in **Terminal** in JupyterLab.
4. Run the Tykky build and kernel registration (one-time setup):
   ```bash
   cd WP2/Task_2.1-Initial_Software_Stack
   bash build_tykky_module.sh
   bash setup_lumi_jupyter.sh
   ```
5. Reload JupyterLab, open **`vlq_bell_state.ipynb`**, and select the kernel **`LUMI-IQ (Python 3.12 - VLQ Quantum)`**.
6. Execute cells interactively. In Step 3, follow the link to authenticate via **MyAccessID** (OAuth Device Flow).

---

## 2. Non-Interactive Batch Execution on LUMI (Slurm)

To run unattended batch jobs without browser prompts:

1. Store your Personal Access Token (PAT) securely (chmod 600):
   ```bash
   mkdir -p ~/.lumi-iq
   echo "<YOUR_LEXIS_PAT_TOKEN>" > ~/.lumi-iq/pat.token
   chmod 600 ~/.lumi-iq/pat.token
   ```

2. Submit the Slurm batch job:
   ```bash
   sbatch submit_lumi.sbatch
   ```

3. Monitor job execution:
   ```bash
   squeue --me
   cat lumi_iq_*.out
   ```
