
Use case by LUMI-IQ Consortium (WP2)

This use case is demonstrating the possible use of QNN (Quantum Neural Network) for predicting the development of a time series, in this case electricity prices.
The Python training script loads real historical data, trains the QNN model with the specified number of iterations and saves it to a file.
The Python forecasting script loads real historical data and the trained QNN model. It then predicts the electricity price 1 hour ahead and saves the results to a png file.
The resulting graph shows the real data (red), the training set (blue points), and the prediction (green).

files:
LUMI-IQ_Use_case-QML_time_series-training.py ... Python script for creating trained model
LUMI-IQ_Use_case-QML_time_series_forecasting.py ... Python script for forecasting using trained model
data.npy ... real historical data (source: https://www.ote-cr.cz)
QNN_0.7706084854606758-model_state.dill ... trained QNN model
QNN_0.15116397768110135-model_state.dill ... trained QNN model
result_prediction.png ... resulting graph

usage:
python3 LUMI-IQ_Use_case-QML_time_series-training.py <number_of_iterations>
python3 LUMI-IQ_Use_case-QML_time_series_forecasting.py <file_with_trained_model>

required packages:
numpy, matplotlib, qiskit_machine_learning, 

Required packages with the versions:
numpy, matplotlib, dill
qiskit>=2.2,<2.5
qiskit-machine-learning==0.9.1
