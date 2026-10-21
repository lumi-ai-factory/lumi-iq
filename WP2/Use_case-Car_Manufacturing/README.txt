
Use case: Quantum Anomaly Detection for Car Manufacturing - Rare Defect Detection
Author: LUMI-IQ Consortium (WP2)

File: Car_manufacturing_rare_event_demo.ipynb

It is recommended to run the notebook in a dedicated virtual environment.
Otherwise the first code cell of the notebook installs the packages itself
with "%pip install".

The virtual environment can be created with uv (https://docs.astral.sh/uv/):

uv venv --python 3.11 carenv
uv pip install --python carenv/bin/python "qiskit==1.4.2" "qiskit-machine-learning==0.8.2" \
  "qiskit-algorithms==0.3.1" "scikit-learn>=1.3,<2.0" "numpy<2.1" matplotlib nbformat nbconvert ipykernel

To register the kernel for Jupyter:

uv run -m ipykernel install --user --name=car_manufacturing --display-name "Python (car-manufacturing)"
