# Use Case 4: QML Time Series Forecasting (Electricity Prices)

| Item | Details |
|---|---|
| **Author / Lead** | LUMI-IQ Consortium (WP2) |
| **Domain** | Energy Markets & Financial Time Series Forecasting |
| **Quantum Approach** | Quantum Neural Network (QNN) Regressor (`ZFeatureMap` + `EfficientSU2` 80-parameter PQC) |
| **Hardware Target** | Local Simulation (`SIM`) or Real QPU (`VLQ` 24-qubit Star topology at IT4Innovations) |
| **Data Source** | Real historical hourly electricity market prices from OTE-CR (Czech Market Operator) |
| **Execution Modes** | Standalone Python Script (`run_time_series_forecasting.py`) & JupyterLab Notebook (`time_series_forecasting.ipynb`) |

---

## 1. Overview

This use case demonstrates predicting the dynamics of financial energy time series — specifically 1-hour ahead electricity prices in the Czech market — using a parameterized Quantum Neural Network (QNN). 

Historical series are embedded into quantum states using an 8-qubit $Z$-feature map, processed by a parameterized 4-repetition `EfficientSU2` ansatz (80 trainable $\theta$ parameters), and evaluated via a statevector estimator trained with COBYLA.

---

## 2. Hardware Execution: Why & How It Runs on VLQ

* **Hardware Compatibility:** The 8-qubit feature window and `EfficientSU2` circuit maps directly onto **8 qubits** of the **24-qubit VLQ QPU**.
* **Hybrid Partitioning (Why training vs inference differs):**
  * **Classical Training (LUMI CPU):** Training the 80 variational $\theta$ parameters over 100+ COBYLA iterations requires evaluating thousands of circuit variants. Running this iterative optimization loop on current NISQ hardware would incur hours of queue wait time and shot-noise drift. Therefore, model training is performed classically on LUMI CPU nodes.
  * **Quantum Inference on Hardware (`--backend VLQ`):** Once trained, the fixed optimal model parameters are loaded. To forecast the next hour's electricity price, a **single 8-qubit quantum circuit** encoding the latest 8-hour price window is transpiled to VLQ native gates (`CZ`, `PRX`) and submitted to **VLQ** with 1024 shots. The measured $\langle Z_0 \rangle$ expectation value directly determines the forecasted market clearing price in EUR/MWh.

---

## 3. Directory Structure

```
04_qml_time_series/
├── README.md                           # Documentation and execution guide
├── run_time_series_forecasting.py      # Standalone forecasting inference script (--backend SIM | VLQ)
├── run_time_series_training.py         # Standalone model training script (LUMI CPU)
├── time_series_forecasting.ipynb       # Interactive notebook for LUMI Open OnDemand
├── result_time_series.png              # Generated forecast plot vs real market prices
├── data.npy                            # Historical OTE-CR market price dataset
├── QNN_0.7706084854606758-model_state.dill # Pre-trained high-accuracy QNN model
└── QNN_0.15116397768110135-model_state.dill # Baseline QNN model
```

---

## 4. Quick Start on LUMI

### Option A: Command Line / Slurm Batch Execution

Activate the unified LUMI-IQ environment:

```bash
module use $HOME/modulefiles
module load Lumi-IQ-qaas/VLQ

# Run standard simulation inference on LUMI CPU (instant execution across 360 hours):
python run_time_series_forecasting.py --backend SIM

# Or submit the 1-hour ahead forecast circuit directly to the real VLQ quantum computer:
python run_time_series_forecasting.py --backend VLQ --shots 1024

# (Optional) Retrain a new QNN model on CPU:
python run_time_series_training.py 50
```

### Option B: Interactive JupyterLab via Open OnDemand

1. Launch JupyterLab on [lumi.csc.fi](https://lumi.csc.fi) using the `lumi-iq` module script.
2. Open `time_series_forecasting.ipynb`.
3. Set `TARGET_BACKEND = "SIM"` or `"VLQ"` and run all cells sequentially.
