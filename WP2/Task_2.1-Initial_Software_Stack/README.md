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

To run unattended batch jobs without browser prompts while preventing token expiration in the queue:

### Automated Queue-Aware Submission (Recommended)
Use `submit_job.py` to authenticate, persist credentials with `chmod 600`, and dynamically enforce both execution walltime (`--time`) and Slurm queue deadline (`--deadline`):

```bash
cd WP2/Task_2.1-Initial_Software_Stack

# Submit job with default 5-minute walltime and 60s safety margin:
python submit_job.py

# Or specify custom walltime:
python submit_job.py --walltime 00:10:00 --margin 120
```

`submit_job.py` automatically:
1. Validates or obtains the OAuth token, saving it to `~/.lumi-iq/token` and `~/.lumi-iq/refresh_token` (`chmod 600`).
2. Calculates exact token expiration timestamp and sets `--deadline` in Slurm.
3. Enforces the invariant:
   $$\text{Queue Wait Time} + \text{Execution Walltime} \le \text{Token Validity} - \text{Safety Margin}$$
   If the job waits too long in the Slurm queue and cannot complete before token expiration, Slurm automatically cancels it (`DEADLINE`) rather than dispatching it with expired credentials.
4. If the token approaches expiry, it automatically attempts non-interactive renewal using the saved refresh token.

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
