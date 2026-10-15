import os
from qiskit import QuantumCircuit
from qaas.client import QProvider

# 1. Build a Qiskit circuit (Bell state)
qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

# OAuth 2.0 Device Code Flow authentication
# If LEXIS_TOKEN is not exported in environment, QProvider initiates interactive Device Code Flow
token = os.getenv("LEXIS_TOKEN")

# 2. Instantiate QProvider with your LEXIS project
# Passing token=None triggers the interactive OAuth Device Code Flow in the browser!
lexis_project = os.getenv("LEXIS_PROJECT", "vlq_qaas_project")
resource_name = os.getenv("LEXIS_RESOURCE", "VLQ-CZ-dev_qshceduler-alpha")

print(f"Connecting to LEXIS project: {lexis_project}...")
provider = QProvider(
    lexis_project=lexis_project,
    token=token if token else None,
)

# 3. Initialize the QBackend with the client
print(f"Retrieving backend for resource: {resource_name}...")
backend = provider.get_backend(
    lexis_resource=resource_name,
)

# 4. Transpile circuit for VLQ backend
print("Transpiling circuit for VLQ Star topology...")
qc_transpiled = backend.transpile(qc)

# 5. Submit the circuit job
print("Submitting job to VLQ...")
job = backend.run(qc_transpiled, shots=1024, job_name="demo_bell_state")
print(f"Job submitted successfully. Job ID: {job.job_id()}")

# 6. Await job execution and retrieve results
print("Waiting for job execution on VLQ...")
result = job.result()
counts = result.get_counts()

print("\n================ Execution Results ================")
print("Counts:", counts)
