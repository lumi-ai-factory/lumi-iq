import os
# Compatibility shim: qheappe_client.utils erroneously imports JobStatus from iqm_server_client instead of iqm_client
import iqm.iqm_server_client.models
try:
    from iqm.iqm_client.models import JobStatus
except ImportError:
    from qiskit.providers.jobstatus import JobStatus
if not hasattr(JobStatus, "COMPLETED") and hasattr(JobStatus, "DONE"):
    JobStatus.COMPLETED = JobStatus.DONE
iqm.iqm_server_client.models.JobStatus = JobStatus

from qiskit import QuantumCircuit
from qheappe_client.qprovider import QProvider

# 1. Build a Qiskit circuit (Bell state)
qc = QuantumCircuit(2, 3)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])
qc.h(0)
qc.measure(0, 2)
# qc.measure_all()

# OAuth 2.0 Device Code Flow authentication
# If LEXIS_TOKEN is not exported in environment, QProvider initiates interactive Device Code Flow
token = os.getenv("LEXIS_TOKEN")

# 2. Instantiate QProvider with your LEXIS authentication details
# Passing token=None triggers the interactive OAuth Device Code Flow in the browser!
lexis_project = "vlq_qaas_project"
resource_name = "VLQ-CZ-dev_qshceduler-alpha"
lexis_api_url = "https://api.test.lexis.tech"

provider = QProvider(
    lexis_project=lexis_project,
    token=token if token else None,
    lexis_api_url=lexis_api_url,
)

# 3. Initialize the QBackend with the client
backend = provider.get_backend(
    lexis_resource=resource_name,
    backend_name="VLQ",  # Production VLQ backend!
)

# 4. Transpile circuit for VLQ backend
qc_transpiled = backend.transpile(qc)

# 5. Submit the circuit job
job = backend.run(qc_transpiled, shots=1024, job_name="demo_bell_state")
print(f"Job submitted successfully. Job ID: {job.job_id()}")

# 6. Await job execution and retrieve results
# job.result() blocks until a terminal event state (FINISHED, FAILED, CANCELED) is reached
result_legacy = job.result(qiskit_legacy=True, with_measurements=True)
counts_legacy = result_legacy.get_counts()
bitstring_legacy = result_legacy.get_memory()

result = job.result(with_measurements=True)
counts = result[0].data.meas.get_counts()
bitstrings = result[0].data.meas.get_bitstrings()

print("\n--- Legacy Execution Results ---")
print("Counts:", counts_legacy)
print(f"Bitstring: {bitstring_legacy!s:.20s}")

print("\n--- Primitive Execution Results ---")
print("Counts:", counts)
print(f"Bitstring: {bitstrings!s:.20s}")
