# --- Imports ---
import argparse

import numpy as np

from hamiltonian import run_hf, select_active_space, active_space_hamiltonian, qubit_hamiltonian
from main import get_backend
from vqe import pauli_measurement_layout, energies_from_counts, load_trajectory

# --- Functions ---
def fetch_counts(
        backend,
        job_id: str,
        timeout_secs: float = 3600
        ) -> list[dict[str, int]]:
    '''
    Fetches the counts of an already submitted job from the backend.

    Args:
        backend: The backend the job was submitted to
        job_id: The id of the job, as printed when the job was submitted
        timeout_secs: How long to wait for the job to finish before giving up.
            Default is 3600.
    Returns:
        counts_list: The counts of every circuit of the job, in submission order
    '''
    job = backend.retrieve_job(job_id)
    print(f'Retrieved job {job_id} from backend {backend.name}, status: {job.status()}')

    counts_list = job.result(timeout_secs=timeout_secs).get_counts()
    # get_counts returns a bare dict instead of a list when only one circuit was run
    if isinstance(counts_list, dict):
        counts_list = [counts_list]
    print(f'Job {job_id} returned counts for {len(counts_list)} circuits')

    return counts_list


def rebuild_layout(
        atom: str,
        basis: str,
        spin: int,
        ao_labels: list[str],
        threshold: float
        ) -> tuple[list[list[tuple[int, float]]], float]:
    '''
    Rebuilds the measurement groups that the job was built from.

    The counts of a job do not carry any information about which Pauli terms they encode,
    so the grouping has to be redone here. It only depends on the Hamiltonian, and both
    the Hartree-Fock step and the grouping are deterministic, so running the classical
    part again with the same molecule arguments reproduces the groups in the exact order
    in which their circuits were submitted.

    Args:
        atom: Atomic geometry string
        basis: Basis set name
        spin: Number of unpaired electrons
        ao_labels: List of atomic orbital labels for AVAS active space selection
        threshold: AVAS threshold for active space selection
    Returns:
        terms_per_group: A list of the term lists of the measurement groups, in submission order
        const: The constant term in the Hamiltonian that does not require any circuit to be run
    '''
    print('Running Hartree-Fock calculation...')
    mf = run_hf(atom, basis, spin)
    print(f'RHF energy: {mf.e_tot:.6f} Hartree')

    print('Selecting active space using AVAS...')
    n_orbitals, n_alpha, n_beta = select_active_space(mf, ao_labels, threshold)
    print(f'Active space: {n_orbitals} orbitals, {n_alpha} alpha electrons, {n_beta} beta electrons')

    print('Building active space Hamiltonian...')
    fermionic_hamiltonian = active_space_hamiltonian(mf, n_alpha, n_beta, n_orbitals)
    _, pauli_hamiltonian = qubit_hamiltonian(fermionic_hamiltonian)
    print(
        f'Hamiltonian built with {pauli_hamiltonian.num_qubits} qubits '
        f'and {len(pauli_hamiltonian)} Pauli terms'
    )

    layout, const = pauli_measurement_layout(pauli_hamiltonian)
    print(f'The Hamiltonian needs {len(layout)} measurement groups, so {len(layout)} circuits per iterate')

    return [terms for _, terms in layout], const


def save_replay(
        path: str,
        replay_energies: list[float],
        trajectory: list[tuple[np.ndarray, float]] | None = None
        ) -> None:
    '''
    Saves the re-measured energies as a csv file.

    One row is written per iterate. When the trajectory of the same run is given, its
    live energies and parameters are written into the same file as extra columns, which
    gives a file in the same format as the one that save_trajectory writes.

    Args:
        path: The path of the csv file to write
        replay_energies: The re-measured energy of each iterate, in trajectory order
        trajectory: The trajectory the job was built from, or None if it is not available
    '''
    if trajectory is not None and len(trajectory) != len(replay_energies):
        raise ValueError(
            f'The trajectory has {len(trajectory)} iterates but the job returned '
            f'{len(replay_energies)} energies. It is probably from a different run.'
        )

    header = ['iteration', 'replay_energy']
    if trajectory is not None:
        num_params = len(trajectory[0][0])
        header = ['iteration', 'live_energy', 'replay_energy']
        header += [f'parameter_{i}' for i in range(num_params)]

    with open(path, 'w') as csv_file:
        csv_file.write(','.join(header) + chr(10))
        for index, replay_energy in enumerate(replay_energies, start=1):
            if trajectory is None:
                values = [str(index), repr(float(replay_energy))]
            else:
                iterate, live_energy = trajectory[index - 1]
                values = [str(index), repr(float(live_energy)), repr(float(replay_energy))]
                values += [repr(float(value)) for value in iterate]
            csv_file.write(','.join(values) + chr(10))


def parse_args() -> argparse.Namespace:
    '''
    Parses the command line arguments for fetching the results of a job.

    Returns:
        args: The parsed command line arguments
    '''
    parser = argparse.ArgumentParser(
        description='Fetch the results of an already submitted trajectory replay job and '
                    'write the re-measured energies into a csv file.'
    )
    parser.add_argument('job_id',
                        help='The id of the job, as printed when the job was submitted.')
    parser.add_argument('--backend', default='VLQ', choices=['VLQ', 'SIM'],
                        help='The backend the job was submitted to. Default is VLQ.')
    parser.add_argument('--output', default='vqe_replay.csv',
                        help="The csv file to write. Default is 'vqe_replay.csv'.")
    parser.add_argument('--trajectory-file', default=None,
                        help='The csv file of the trajectory that was replayed. If given, its '
                             'live energies and parameters are written into the output file as '
                             'well. Leave it out when the trajectory was not saved.')
    parser.add_argument('--shots', type=int, default=None,
                        help='The number of shots the job was run with. By default the number '
                             'is taken from the counts themselves.')
    parser.add_argument('--timeout', type=float, default=3600,
                        help='How long to wait for the job to finish, in seconds. Default is 3600.')
    # The molecule arguments have to match the run that submitted the job, because the
    # measurement groups are rebuilt from the Hamiltonian
    parser.add_argument('--atom', default='H 0 0 0; H 0 0 0.74',
                        help='Atomic geometry string. Default is the H2 molecule.')
    parser.add_argument('--basis', default='sto-3g',
                        help='Basis set name. Default is sto-3g.')
    parser.add_argument('--spin', type=int, default=0,
                        help='Number of unpaired electrons. Default is 0.')
    parser.add_argument('--ao-labels', nargs='+', default=['H 1s'],
                        help='Atomic orbital labels for AVAS active space selection.')
    parser.add_argument('--threshold', type=float, default=0.2,
                        help='AVAS threshold for active space selection. Default is 0.2.')
    return parser.parse_args()


# --- Main ---
if __name__ == '__main__':
    args = parse_args()

    # Rebuild the measurement groups that the counts have to be decoded with
    terms_per_group, const = rebuild_layout(
        args.atom, args.basis, args.spin, args.ao_labels, args.threshold
    )

    # Fetch the counts of the job and turn them back into energies
    backend = get_backend(args.backend)
    counts_list = fetch_counts(backend, args.job_id, timeout_secs=args.timeout)
    replay_energies = energies_from_counts(counts_list, terms_per_group, const, args.shots)
    print(f'Decoded {len(replay_energies)} iterates from the job')

    # Add the parameters and the live energies of the run when they are available
    trajectory = load_trajectory(args.trajectory_file) if args.trajectory_file else None

    save_replay(args.output, replay_energies, trajectory)
    print(f'Replay energies saved to {args.output}')
    print(f'Lowest replayed energy: {min(replay_energies):.6f} Hartree')
