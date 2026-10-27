# LUMI-IQ: Quantum Computing

LUMI-IQ is the experimental quantum computing platform of the LUMI AI Factory, designed for
hybrid HPC+AI+QC workloads. It builds on the LUMI supercomputer and will be deployed alongside
the new LUMI-AI supercomputer. The first LUMI-IQ system will be an IQM Halocene quantum
computer, to be installed in 2027 and upgraded in stages towards fault-tolerant quantum
computing with logical qubits.

For the goals, planned system and roadmap of LUMI-IQ, see:

- [Computing infrastructure: LUMI-IQ](https://lumi-ai-factory.eu/about-us/computing-infrastructure/) (LUMI AI Factory)
- [LUMI-IQ project page](https://csc.fi/project/lumi-iq/) (CSC)
- [First LUMI AI Factory quantum services now available](https://lumi-ai-factory.eu/articles/first-lumi-ai-factory-quantum-services-now-available/)
- [Quantum services](https://lumi-ai-factory.eu/services/quantum-services/) in the LUMI AI Factory service catalogue

!!! info "The LUMI-Q VLQ quantum computer stands in as LUMI-IQ for now"

    Until the LUMI-IQ system is delivered, the **VLQ** quantum computer of the
    [LUMI-Q consortium](https://www.it4i.cz/en/infrastructure/vlq-quantum-computer) is used
    as LUMI-IQ. VLQ is hosted at IT4Innovations in Ostrava, Czech Republic, and is operated by
    IT4Innovations.
    Skills and hybrid workflows developed on VLQ now are a head start for LUMI-IQ.

## The quantum computer: VLQ (LUMI-IQ)

VLQ is a superconducting quantum computer supplied by IQM Quantum Computers. It is funded
jointly by EuroHPC JU and eight countries (Czechia, Belgium, Denmark, Finland, Norway, the
Netherlands, Poland and Sweden) and was installed and commissioned in 2025.

| Property | Value |
|---|---|
| Qubit technology | Superconducting transmon qubits |
| Number of qubits | 24 physical qubits |
| Topology | Star-shaped: the qubits are connected to a central resonator |
| Supplier | IQM Quantum Computers |
| Location | IT4Innovations National Supercomputing Center, Ostrava, Czech Republic |
| Programming frameworks | Qiskit and Cirq |
| Execution levels | Gate level and pulse level (through IQM Pulla) |
| Accounting unit | QPU seconds |

The star-shaped topology minimizes the number of swap operations needed to run a circuit.
Swaps are a common bottleneck in quantum circuits, so fewer of them makes better use of the
qubit coherence time and allows more complex algorithms to be executed reliably. When writing
circuits, keep in mind that any pair of qubits is connected through the central resonator
rather than directly to each other.

The current state of the device is published on the
[Calibration and Health](https://docs.it4i.cz/en/docs/clusters/vlq/calibration_health) page.

## Getting access

Access works differently from standard LUMI projects. Allocations are given in QPU seconds
and are handled by the LUMI-Q allocation brokers.

1. **Estimate your needs** with the
   [Estimating Consumption on VLQ](https://docs.it4i.cz/en/docs/clusters/vlq/vlq-consumption-guide)
   guide.
2. **Apply for an allocation** from EuroHPC JU, IT4Innovations, or the LUMI-Q broker of your
   country. For Finland this is CSC (resource id `VLQ-FI`). The full list of brokers and
   resource ids is in the
   [VLQ access guide](https://docs.it4i.cz/en/docs/clusters/vlq/access#lumi-q-brokers).
3. **Receive a PROJECT id and a RESOURCE id** from your broker.
4. **Request project access** at [portal.lexis.tech](https://portal.lexis.tech) using your
   MyAccessID credentials.
5. **Sign the Acceptable Use Policy (AUP)**. IT4I support will contact you and confirm the
   activation of your project.

The LUMI AI Factory also offers VLQ access together with LUMI resources as the
[Quantum computing resource access](https://lumi-ai-factory.eu/quantum-computing-resource-access/)
service, and
[Quantum expert support and consulting](https://lumi-ai-factory.eu/quantum-expert-support-and-consulting/)
to help you get started.

You also need a regular LUMI project and account to run your code on LUMI. See
[Access to LUMI](https://docs.lumi-supercomputer.eu/firststeps/accessLUMI/).

## Loading the modules

The modules are made available in: 

```bash
module use /appl/local/lumiiq/modulefiles
```

```bash
module avail
```

The quantum modules then appear at the top of the output of `module avail`. 

## Extending the modules

The `Lumi-IQ-core` module contains what is needed to run on LUMI-IQ. If you need additional Python
packages, you can build your own container using [LUMI container wrapper](https://docs.lumi-supercomputer.eu/software/installing/container-wrapper/), see also the LUMI documentation on
[installing software](https://docs.lumi-supercomputer.eu/software/).

!!! important "`qaas` and `py4lexis` are required to authenticate on LUMI-IQ"

    The `lumi-iq-qaas` module provides these packages. If you build your own module or
    environment, it must also include `qaas` and `py4lexis`, otherwise you cannot authenticate
    to or submit jobs to LUMI-IQ. The required package versions, and the Python version they work
    with, change frequently and are listed in the
    [access guide](https://docs.it4i.cz/en/docs/clusters/vlq/access#set-up-python-environment).

!!! warning "Strain on Lustre file system"

    Installing Python packages creates many small files, which strains the Lustre file system
    and may exceed your file quota. If you need many or large packages, build a container
    instead. See
    [Singularity/Apptainer](https://docs.lumi-supercomputer.eu/software/containers/singularity/)
    for how to extend container images, and
    [LAIF AI containers](https://docs.lumi-supercomputer.eu/laif/software/ai-environment/)
    for the same approach with the AI images.


## Running your first job

LUMI-IQ jobs are executed **from within Python**. Your script runs on any machine with network
access to the quantum computer, such as a LUMI node, and submits circuits to the quantum computer. Use a regular LUMI Slurm job (or an
[interactive job](https://docs.lumi-supercomputer.eu/runjobs/scheduled-jobs/interactive/))
for the classical part of your workflow.

The script authenticates with your MyAccessID credentials, selects your PROJECT and RESOURCE
ids, and gets a backend object that circuits are submitted to:

```python
from py4lexis.session import LexisSession
from qaas.client import QProvider, QBackend, QJob

# 1. Authentication (opens a login page; the access token can be saved and reused)
lexis_session = LexisSession()
token = lexis_session.get_access_token()

# 2. Configure resources
PROJECT = "PROJECT id"    # e.g. OPEN-37-1
RESOURCE = "RESOURCE id"  # e.g. VLQ-FI

# 3. Initialize QaaS and get the backend
provider = QProvider(PROJECT, token)
backend: QBackend = provider.get_backend(RESOURCE)
```

Complete circuits, such as the GHZ examples, are in the notebooks linked below.


## More information

- [More information on the quantum computer](https://www.it4i.cz/en/infrastructure/vlq-quantum-computer)
- [Estimating consumption](https://docs.it4i.cz/en/docs/clusters/vlq/vlq-consumption-guide) and [Calibration and health](https://docs.it4i.cz/en/docs/clusters/vlq/calibration_health)
- [Examples](https://docs.it4i.cz/en/general/) 
- [IQM documentation](https://docs.iqm.tech/)
- [CSC quantum computing documentation](https://docs.csc.fi/computing/quantum-computing/)
- [Slurm quickstart](https://docs.lumi-supercomputer.eu/runjobs/scheduled-jobs/slurm-quickstart/) and [Module environment](https://docs.lumi-supercomputer.eu/runjobs/lumi_env/Lmod_modules/)
- [LUMI User Support Team](https://lumi-supercomputer.eu/user-support/need-help/) for questions.