###############################
## Use case by Jiri Tomcala
###############################

import os
import sys
import warnings
warnings.filterwarnings("ignore", message=".*IProgress not found.*")

script_dir = os.path.dirname(os.path.abspath(__file__))

if len(sys.argv) < 2:
    modelfile = os.path.join(script_dir, "QNN_0.7706084854606758-model_state.dill")
    print(f"No model file specified, using default: {os.path.basename(modelfile)}")
else:
    modelfile = sys.argv[1]
    if not os.path.isabs(modelfile) and not os.path.exists(modelfile):
        modelfile = os.path.join(script_dir, modelfile)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit_machine_learning.algorithms.regressors import NeuralNetworkRegressor

data_path = os.path.join(script_dir, "data.npy")
data_orig = np.load(data_path, allow_pickle=True)
data_orig = data_orig[96:]

n = 360
data = ((2*np.pi) * (data_orig - min(data_orig[0:(8+n)])) / (max(data_orig[0:(8+n)]) - min(data_orig[0:(8+n)]))) - np.pi

inputs = []
for i in range(n):
    inputs.append(data[i:(i+8)])
inputs = np.array(inputs)

reg = NeuralNetworkRegressor.from_dill(modelfile)

outputs = np.array(data[8:(8+n)])
outputs_norm = ((outputs - min(outputs)) / (max(outputs) - min(outputs))) - 0.5
outputs_orig = np.array(data_orig[8:(8+n)])
outputs_train_orig = outputs_orig[0:240]

plt.rcParams["figure.figsize"] = (20, 5)
# plot real data
plt.plot(range(len(outputs_orig)), outputs_orig[range(len(outputs_orig))], "r--")

# plot train data
plt.plot(range(len(outputs_train_orig)), outputs_train_orig, "b.")

# plot predicted data
outputs_predicted_norm = reg.predict(inputs)[:,0]
outputs_predicted_norm_pi = (outputs_predicted_norm + 0.5) * (max(outputs) - min(outputs)) + min(outputs)
outputs_predicted_orig = (outputs_predicted_norm_pi + np.pi)/(2*np.pi) * (max(data_orig[0:(8+n)]) - min(data_orig[0:(8+n)])) + min(data_orig[0:(8+n)])

score = reg.score(inputs, outputs_norm)

plt.title(f"Forecasting electricity price with model from {modelfile} on simulator. Average precision = {score*100:.2f}% (8-qubits PQC with 80 trainable parameters θ was used)")
plt.xlabel("Time [h]")
plt.ylabel("Price [EUR/MWh]")
plt.plot(range(len(outputs_predicted_orig)), outputs_predicted_orig, "g-")
plt.legend(['real values', 'training set points', 'prediction'])
plt.grid()
plt.savefig("result_prediction.png", dpi=150)
plt.savefig("result_time_series.png", dpi=150)
print(f"Average precision = {score*100:.2f}%")
print("Result saved in result_time_series.png (and result_prediction.png)")
