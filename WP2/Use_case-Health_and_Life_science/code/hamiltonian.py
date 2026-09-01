# --- Imports ---
import numpy as np
from pyscf import gto, scf, mcscf, ao2mo
from pyscf.mcscf import avas
from qiskit.quantum_info import SparsePauliOp
from qiskit_nature.second_q.operators import ElectronicIntegrals, FermionicOp
from qiskit_nature.second_q.hamiltonians import ElectronicEnergy
from qiskit_nature.second_q.mappers import JordanWignerMapper

# --- Functions ---
def run_hf(
        atom: str,
        basis: str,
        spin: int = 0
        ) -> scf.hf.SCF:
    '''
    Runs the Hartree-Fock calculation. RHF is used if the number of unpaired electrons if zero, i.e. the system is closed-shell.
    ROHF is used if there are unpaired electrons, i.e. the system is open-shell.

    Args:
        atom: Atomic geometry string
        basis: Basis set name
        spin: Number of unpaired electrons. Zero for closed-shell and a positive integer for open-shell. Default value is 0.
    Returns:
        mf: The converged HF object (RHF or ROHF)
    '''
    # Check that the provided spin value is valid
    if type(spin) is not int or spin < 0:
        raise ValueError(f"Spin must be a non-negative integer. Got spin={spin}.")
    
    # Define the molecule
    mol = gto.M(
        atom = atom,
        basis = basis,
        spin = spin
        )

    # Run the RHF or ROHF calculation depending on the provided spin
    if spin == 0:
        mf = scf.RHF(mol).run()
    else:
        mf = scf.ROHF(mol).run()

    # Return the result of the calculation
    return mf


def select_active_space(
        mf: scf.hf.SCF,
        ao_labels: list[str],
        threshold: float = 0.2
        ) -> tuple[int, int, int]:
    '''
    Selects the active space using AVAS method.

    Args:
        mf: The converged RHF object or ROHF
        ao_labels: List of atomic orbital labels that should be included in the active space
        threshold: Threshold for the atomic orbital projector. Orbitals that have overlap above this value will be included in the active space. Default is 0.2.
    Returns:
        n_orbitals: The number of orbitals
        n_alpha: The number of alpha electrons
        n_beta: The number of beta electrons
    '''
    n_orbitals, n_electrons, _ = avas.avas(mf, ao_labels, threshold=threshold)
    # Get the spin
    spin = mf.mol.spin
    # Split the electron into alpha and beta electrons
    n_alpha = (n_electrons + spin) // 2
    n_beta = (n_electrons - spin) // 2
    
    # Return the number of orbitals, alpha electrons and beta electrons
    return n_orbitals, n_alpha, n_beta


def active_space_hamiltonian(
        mf: scf.hf.SCF, 
        n_alpha: int, 
        n_beta: int, 
        n_orbitals: int
        ) -> FermionicOp:
    '''
    Creates the active space Hamiltonian as a second-quantized fermionic Hamiltonian.

    Args:
        mf: The converged RHF or ROHF object
        n_alpha: Number of active alpha electrons
        n_beta: Number of active beta electrons
        n_orbitals: Number of active orbitals

    Returns:
        fermionic_hamiltonian: The active space Hamiltonian as a second-quantized fermionic Hamiltonian

    '''
    # Check the number of active electrons
    if n_alpha > n_orbitals or n_beta > n_orbitals:
        raise ValueError(
            f"Number of active alpha or beta electrons cannot exceed the number of orbitals."
            f"Got values n_alpha={n_alpha}, n_beta={n_beta}, and n_orbitals={n_orbitals}."
            )
    # CASSCF for orbitail optimization
    mc = mcscf.CASSCF(mf, n_orbitals, (n_alpha, n_beta))
    # Run only orbital optimzation
    mc.kernel()

    # One-electron integrals
    h1, energy_core = mc.get_h1eff()
    # Antisymmetrized two-electron integrals
    h2 = mc.get_h2eff()

    # Un-antisymmetrize the two-electron integrals as PySCF return antisymmetrized integrals
    h2_full = ao2mo.restore(1, h2, n_orbitals)

    # Get the spin blocks
    # Same spatial integrals for all spins because RHF or ROHF was used
    h2_aa = h2_full
    h2_bb = h2_full
    h2_ba = h2_full

    # Turn the electron integrals into a form that Qiskit Nature requires
    # h1_a = h1_b = h1 because using RHF or ROHF the one-electron integrals are spin independent
    integrals = ElectronicIntegrals.from_raw_integrals(h1, h2_aa, h1, h2_bb, h2_ba)

    # Build the active space Hamiltonian 
    # Add core energy as a constant offset
    hamiltonian = ElectronicEnergy(integrals, constants={"nuclear_repulsion_energy": energy_core})
    # Get the fermionic Hamiltonian
    fermionic_hamiltonian = hamiltonian.second_q_op()

    # Return the active space Hamiltonian in fermionic form
    return fermionic_hamiltonian


def qubit_hamiltonian(
        fermionic_hamiltonian: FermionicOp
        ) -> tuple[np.ndarray, SparsePauliOp]:
    ''' 
    Transforms an active space Hamiltonian in the second quantization form into a qubit Hamiltonian using the Jordan-Wigner transformation.

    Args:
        fermionic_hamiltonian: The active space Hamiltonian as a second-quantized fermionic Hamiltonian

    Returns:
        hamiltonian_matrix: The same Hamiltonian as a matrix
        pauli_hamiltonian: The same Hamiltonian expressed using Paulis
    '''

    # If one wishes to use some other mapping (for example parity mapping) instead of Jordan-Wigner, then this line should be changed to fit that mapping
    mapper = JordanWignerMapper()
    # Map the fermionic_hamiltonian using the mapper defined above
    pauli_hamiltonian = mapper.map(fermionic_hamiltonian)

    # Creating a matrix representation of the mapped Hamiltonian
    hamiltonian_matrix = pauli_hamiltonian.to_matrix()

    # Return the Hamiltonian in matrix form and SparsePauliOp form
    return hamiltonian_matrix, pauli_hamiltonian


def ground_state_amplitudes(
        hamiltonian_matrix: np.ndarray
        ) -> np.ndarray:
    '''
    Calculates the ground state amplitudes from the active space Hamiltonian (as a second-quantized fermionic Hamiltonian) that is given in matrix form.

    Args:
        hamiltonian_matrix: The Hamiltonian as a matrix

    Returns:
        amplitudes: The ground state amplitudes. A normalized vector in little endian ordering
    '''

    # Get all of the eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian_matrix)

    # Get the eigenvector corresponding to the lowest eigenvalue
    # This is the amplitude vector in little endian
    amplitudes = eigenvectors[:, 0]

    # Return the amplitude vector
    return amplitudes
