# --- Imports ---
from time import sleep

import numpy as np
import random
from functools import reduce
from typing import Literal
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import StatePreparation
from qiskit.quantum_info import Statevector
from qiskit.circuit import Instruction
from qiskit.providers import Backend


def is_job_done(job) -> bool:
    """Helper to check if a quantum job reached terminal state across Qiskit and QaaS backends."""
    if hasattr(job, "in_final_state"):
        try:
            return bool(job.in_final_state())
        except Exception:
            pass
    if hasattr(job, "is_final_state"):
        try:
            return bool(job.is_final_state())
        except Exception:
            pass
    if hasattr(job, "status"):
        try:
            st = str(job.status()).upper()
            return any(term in st for term in ["DONE", "COMPLETED", "ERROR", "CANCEL", "FAIL"])
        except Exception:
            pass
    return False


# --- Functions ---
def create_snapshot_circuit(
        n_qubit: int,
        initial_state: QuantumCircuit | Statevector | list | str | int,
        U_list: list[Instruction]
        ) -> tuple[QuantumCircuit, list[np.ndarray]]:
    '''
    Creates a quantum circuit that can be used to get a snapshot.

    Args:
        n_qubit: The number of qubits
        initial_state: The initial state of the system
        U_list: A list of unitaries (usually Pauli gates, i.e. [X, Y, Z]) given as quantum gates
    Returns:
        circuit: A quantum circuit for getting the snapshots
        per_qubit_matrices: A list of per-qubit unitary matrices
    '''
    # Prepare a circuit depending on the type of the initial_state
    if isinstance(initial_state, QuantumCircuit):
        circuit = initial_state.copy()
    elif type(initial_state) is int or isinstance(initial_state, (Statevector, list, str)):
        circuit = QuantumCircuit(n_qubit)
        circuit.append(StatePreparation(initial_state), list(range(n_qubit)))
    else:
        raise ValueError(
            f"initial_state must be either a QuantumCircuit, Statevector, list, integer or string. "
            f"Got {type(initial_state)}."
        )

    # Apply a random unitary from U_list to each qubit
    # Store per-qubit unitary matrices
    per_qubit_matrices = []
    for i in range(n_qubit):
        unitary = random.choice(U_list)
        circuit.append(unitary, [i])
        per_qubit_matrices.append(unitary.to_matrix())
    # Measure all qubits
    circuit.measure_all()

    # Return the circuit and the matrices
    return circuit, per_qubit_matrices


def binary_to_vector(
        key: str
        ) -> Statevector:
    '''
    Builds the state vector corresponding to a key value. Counts are given in the format {'key': number}. 

    Args: 
        key: A string containing only binary digits
    Returns: 
        state_vector: The statevector corresponding to the binary string
    '''

    # Create the state vector from the key value
    state_vector = Statevector.from_label(key)

    # Return the state vector that was built
    return state_vector


def calculate_snapshots(
        N: int,
        backend: Backend,
        optimization_level: Literal[0, 1, 2, 3],
        n_qubit: int,
        initial_state: QuantumCircuit | Statevector | list | str | int,
        U_list: list[Instruction],
        batch_size: int = 1000,
        report_per_job_progress: bool = False,
        is_simulation: bool = False
        ) -> list[list[np.ndarray]]:
    '''
    Calculates N snapshots of the quantum state for use in the classical shadow protocol.

    Args:
        N: The number of snapshots to collect
        backend: The backend to run the circuits on
        optimization_level: The transpilation optimization level, options are 0-3
        n_qubit: The number of qubits
        initial_state: The initial state of the system
        U_list: A list of unitaries to randomly apply
        batch_size: The largest number of circuits to put into a single job. Default is 1000.
        report_per_job_progress: If True, prints the id of every job that is submitted
        is_simulation: If True, jobs are not polled for their status, because a local
            simulator has finished by the time its result is asked for and its jobs do
            not have the polling interface that remote backend jobs have. Default is False.
    Returns:
        per_qubit_snapshots: A list of lists of single-qubit snapshot matrices
    '''
    # Check that the optimization level is valid
    if optimization_level not in range(4):
        raise ValueError(
            f"Optimization level not allowed. Must be 0, 1, 2, or 3. Got {optimization_level}."
        )

    # Create the circuits and the qubit matrices
    # Append these to lists
    all_per_qubit_matrices = []
    circuits = []
    for _ in range(N):
        circuit, per_qubit_matrices = create_snapshot_circuit(n_qubit, initial_state, U_list)
        circuits.append(circuit)
        all_per_qubit_matrices.append(per_qubit_matrices)
    # Transpile the circuits
    transpiled_circuits = transpile(circuits, backend=backend, optimization_level=optimization_level)

    # Run the transpiled circuits in batches
    per_qubit_snapshots = []
    for i in range(0, N, batch_size):
        # Run the circuits with 1 shot each
        job = backend.run(transpiled_circuits[i:i+batch_size], shots=1)
        if report_per_job_progress:
            print(f'Running job {i//batch_size + 1} of {((N-1)//batch_size) + 1}... on backend {backend.name}. Job ID: {job.job_id()}')

        time_taken = 0

        if not is_simulation:
            while not is_job_done(job):
                sleep(2)
                time_taken += 2
                if time_taken % 30 == 0:
                    status_str = job.status() if hasattr(job, "status") else "RUNNING"
                    print(f'Job {job.job_id()} is still running after {time_taken} seconds... (status: {status_str})')
                if time_taken > 1800:
                    print(f'Warning: Job {job.job_id()} exceeded timeout (30m). Calling result().')
                    break
            
        results = job.result().get_counts()
        # get_counts returns a bare dict instead of a list when only one circuit was run,
        # which happens whenever the last batch holds a single circuit
        if isinstance(results, dict):
            results = [results]
        for j, result in enumerate(results):
            # Get the key value
            key = next(iter(result))
            qubit_snapshots = []
            for q in range(n_qubit):
                # Get measurement outcome for qubit q from the key value
                # key is in big-endian so reverse index
                key_q = int(key[-(q+1)])
                # Get per-qubit unitary matrix
                U_q = all_per_qubit_matrices[i+j][q]
                # Compute single-qubit state vector |0⟩ or |1⟩
                state_q = np.array([[1-key_q], [key_q]], dtype=complex)
                # Compute single-qubit snapshot U_q†|b_q⟩⟨b_q|U_q
                snapshot_q = U_q.conj().T @ state_q @ state_q.conj().T @ U_q
                qubit_snapshots.append(snapshot_q)
            per_qubit_snapshots.append(qubit_snapshots)

    # Return the single qubit snapshots
    return per_qubit_snapshots
    

def create_pauli_shadow(
        per_qubit_snapshots: list[list[np.ndarray]]
        ) -> list[np.ndarray]:
    '''
    Calculates the classical shadow from per-qubit snapshots taken with Pauli unitaries,
    applying the per-qubit inverse channel M^{-1}(A_i) = 3*A_i - I
    and combining them via tensor product.

    Args:
        per_qubit_snapshots: A list of lists of single-qubit snapshots
    Returns:
        classical_shadow: The classical shadow as a list of matrices
    '''
    # Define an identity matrix of the correct dimensionality
    identity = np.eye(2)

    # Create the classical shadow
    classical_shadow = []
    for qubit_snapshots in per_qubit_snapshots:
        shadow = None
        for single_qubit_snapshot in reversed(qubit_snapshots):
            # Apply per-qubit inverse channel to each single qubit snapshot one at a time
            single_qubit_shadow = 3 * single_qubit_snapshot - identity
            # Combine via tensor product
            if shadow is None:
                shadow = single_qubit_shadow
            else:
                shadow = np.kron(shadow, single_qubit_shadow)
        classical_shadow.append(shadow)

    # Return the classical shadow
    return classical_shadow


def calculate_expectation_value(
        operator: np.ndarray, 
        classical_shadow: list[np.ndarray], 
        K: int
        ) -> float:
    '''
    Calculates the expectation value of an operator using the classical shadow using the median-of-means estimator.
    
    Args:
        operator: The operator whose expectation value is to be determined
        classical_shadow: A classical shadow of a quantum state
        K: The number of parts the shadow should be divided into
    Returns:
        exp_val: The expectation value
    '''
    # Check is it possible to split the classical shadow into equally sized parts
    if len(classical_shadow) % K != 0:
        raise ValueError(f"The shadow can not be equally divided. Change the number of parts. Got K={K} number of parts.")

    # Split the classical shadow into K chunks
    split_shadow = np.array_split(classical_shadow, K)
    # Create an empty list for storing the traces
    traces = []

    # Construct the estimators of rho, one from each part of the classical shadow
    for chunk in split_shadow:
        # Calculate the mean of expectation values for all snapshots in a chunk
        trace = np.mean([np.trace(operator @ shadow) for shadow in chunk])
        # Append the trace to the empty list for storing the traces
        traces.append(trace)

    # Calculate the expectation value as the median of the traces
    # The value is returned as a float
    exp_val = float(np.real(np.median(traces)))

    # Return the expectation value
    return exp_val
