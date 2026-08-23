
Use case by Jiri Tomcala

This use case is demonstrating the possible use of QNN (Quantum Neural Network) for predicting the development of a time series, in this case electricity prices.
The Python script loads real historical data and the trained QNN model. It then predicts the electricity price 1 hour ahead and saves the results to a png file.
The resulting graph shows the real data (red), the training set (blue points), and the prediction (green).

files:
LUMI-IQ_Use_case-QML_time_series_forecasting.py ... Python script
data.npy ... real historical data
QNN_0.9405658017321574-model_state.dill ... trained QNN model
result_prediction.png ... resulting graph

usage:
python3 LUMI-IQ_Use_case-QML_time_series_forecasting.py

required packages:
numpy, matplotlib, qiskit_machine_learning
