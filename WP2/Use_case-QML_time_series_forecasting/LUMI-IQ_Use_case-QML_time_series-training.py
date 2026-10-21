###############################
## Use case by LUMI-IQ Consortium (WP2)
###############################

import sys

if (len(sys.argv)) < 2:
    print("Number of iterations is missing.")
    sys.exit()
    
MAXITER = sys.argv[1]

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.primitives import StatevectorEstimator
from qiskit.circuit.library import z_feature_map, efficient_su2
from qiskit_machine_learning.circuit.library import qnn_circuit
from qiskit_machine_learning.neural_networks import EstimatorQNN
from qiskit_machine_learning.optimizers import COBYLA
from qiskit_machine_learning.algorithms.regressors import NeuralNetworkRegressor

data_orig = np.load("data.npy", allow_pickle=True)
data_orig = data_orig[96:]
n = 240
data = ((2*np.pi) * (data_orig - min(data_orig[0:(8+n)])) / (max(data_orig[0:(8+n)]) - min(data_orig[0:(8+n)]))) - np.pi

inputs = []
for i in range(n):
    inputs.append(data[i:(i+8)])
inputs = np.array(inputs)

outputs = np.array(data[8:(8+n)])
outputs = ((outputs - min(outputs)) / (max(outputs) - min(outputs))) - 0.5

x = ParameterVector("x", 8)
θ = ParameterVector("θ", 80)
fm = z_feature_map(8, reps=1)
pqc = efficient_su2(8, reps=4)

# construct a circuit
qc, fm_params, pqc_params = qnn_circuit(feature_map=fm, ansatz=pqc)

estimator = StatevectorEstimator(seed=42)

# construct QNN
regression_estimator_qnn = EstimatorQNN(
    circuit=qc, input_params=fm_params, weight_params=pqc_params, estimator=estimator, 
)

# callback function that prints state of ongoing optimization
def callback_print(weights, obj_func_eval):
    objective_func_vals.append(obj_func_eval)
    print(f"Iteration: {len(objective_func_vals)}/{MAXITER}, Objective function value: {obj_func_eval}", end="\r")

# construct the regressor from the neural network
regressor = NeuralNetworkRegressor(
    neural_network=regression_estimator_qnn,
    loss="absolute_error",
    optimizer=COBYLA(maxiter=MAXITER),
    initial_point = ((2*np.pi)*np.random.random(len(pqc_params)))-np.pi,
    callback=callback_print,
)

# fit to data
objective_func_vals = []
regressor.fit(inputs, outputs)

score = regressor.score(inputs, outputs)
print()
print(f"Score = {score} (Training set accuracy = {score*100:.2f}%)")
regressor.to_dill(f"QNN_{score}-model_state.dill")
print(f"Model saved to: QNN_{score}-model_state.dill")
