# LUMI-IQ: Hybrid HPC, AI and Quantum Computing Platform

LUMI-IQ is the experimental quantum computing platform of the LUMI AI Factory, designed for hybrid HPC+AI+QC workloads. It builds on the LUMI supercomputer and will be deployed alongside the new LUMI-AI supercomputer.

LUMI-IQ establishes a hybrid HPC+QC architecture, allowing classical workloads to run on the LUMI infrastructure while quantum circuits are dispatched to the QPU.

!!! info "The LUMI-Q VLQ quantum computer stands in as LUMI-IQ today"

    Until the dedicated LUMI-IQ system is commissioned, the **VLQ** quantum computer of the
    [LUMI-Q consortium](https://www.it4i.cz/en/infrastructure/vlq-quantum-computer) serves as the primary hardware target. VLQ is hosted and operated by the IT4Innovations National Supercomputing Center in Ostrava, Czech Republic.
    Hybrid HPC-QC workflows and software modules deployed on VLQ today run seamlessly and provide an immediate head start for LUMI-IQ.

---

## Loading the modules

The LUMI-IQ software stack is centrally integrated into LUMI’s module system under `/appl/local/lumiiq/modulefiles`. To inspect the available modules:

```bash
module use /appl/local/lumiiq/modulefiles
module avail
```

To load the environment:

```bash
module load Lumi-IQ
```

*(Note: When targeting the local simulator for testing without QPU credentials, you can load the simulation profile `module load Lumi-IQ-qaas/SIM`).*

### Module Hierarchy

To accommodate diverse hybrid scientific workflows, the stack is organized into specialized domain modules:

| Module | Description | 
|---|---|
| **`Lumi-IQ-qaas/VLQ`** | **Primary Hardware Target**: Direct submission to the physical 24-qubit VLQ QPU. |
| **`Lumi-IQ-qaas/SIM`** | **HPC Simulator Target**: High-performance classical circuit simulation on LUMI CPU nodes. |
| **`Lumi-IQ-core`** | Baseline quantum circuit transpilation and hybrid orchestration. |
| **`Lumi-IQ-qml`** | Quantum Machine Learning and Hybrid AI computations. |
| **`Lumi-IQ-ems`** | Quantum Error Mitigation & Noise Tailoring (FiQCI-EMS, IQM Error Reduction Tools). |

---

## Running your first job

LUMI-IQ jobs are executed **from within Python**. Your script runs on any machine with network access to the quantum computer, such as a LUMI node, and submits circuits to the physical QPU or local simulator.

Heavy classical computations and hybrid variational loops must **not** run on login nodes. Schedule them on LUMI compute nodes using Slurm.

!!! note "Targeting the VLQ QPU"

    Submitting circuits to the physical QPU requires a dedicated quantum allocation (see the [Quantum Hardware Access Guide](https://docs.it4i.cz/en/docs/clusters/vlq/access)), while real-time calibration and fidelity metrics are published on the [Calibration and Health Status](https://docs.it4i.cz/en/docs/clusters/vlq/calibration_health) dashboard.

For complete, runnable hybrid examples (including authentication, Variational Quantum Eigensolver, Quantum Machine Learning, and Error Mitigation) as well as sample Slurm batch scripts (`sbatch`), please refer to the official repository:

- [LUMI-IQ GitHub Repository & Example Workflows](https://github.com/lumi-ai-factory/lumi-iq)
- [Sample Slurm Batch Scripts (`sbatch`)](https://github.com/lumi-ai-factory/lumi-iq/tree/main/WP2)

---

## More information

- [LUMI AI Factory Quantum Services](https://lumi-ai-factory.eu/services/quantum-services/)
- [IQM Hardware Documentation](https://docs.iqm.tech/)
- [LUMI User Support Team](https://lumi-supercomputer.eu/user-support/need-help/)
