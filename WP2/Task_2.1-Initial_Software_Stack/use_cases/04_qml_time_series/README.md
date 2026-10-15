# Use Case 4: QML Time Series Forecasting (Electricity Prices)

| Item | Details |
|---|---|
| **Author / Lead** | Jiří Tomčala (IT4Innovations National Supercomputing Center) |
| **Domain** | Energy Markets & Financial Time Series Forecasting |
| **Quantum Approach** | Quantum Neural Network (QNN) Regressor (`ZFeatureMap` + `EfficientSU2` 80-parameter PQC) |
| **Data Source** | Real historical hourly electricity market prices from OTE-CR (Czech Market Operator) |
| **Execution Modes** | Standalone Python Script (`run_time_series_forecasting.py`) & JupyterLab Notebook (`time_series_forecasting.ipynb`) |

---

## 1. Overview

This use case demonstrates predicting the dynamics of financial energy time series — specifically 1-hour ahead electricity prices in the Czech market — using a parameterized Quantum Neural Network (QNN). 

Historical series are embedded into quantum states using an 8-qubit $Z$-feature map, processed by a parameterized 4-repetition `EfficientSU2` ansatz (80 trainable $\theta$ parameters), and evaluated via a statevector estimator trained with COBYLA.

---

## 2. Directory Structure

```
04_qml_time_series/
├── README.md                           # Documentation and execution guide
├── run_time_series_forecasting.py      # Standalone forecasting inference script
├── run_time_series_training.py         # Standalone model training script
├── time_series_forecasting.ipynb       # Interactive notebook for LUMI Open OnDemand
├── result_time_series.png              # Generated forecast plot vs real market prices
├── data.npy                            # Historical OTE-CR market price dataset
├── QNN_0.7706084854606758-model_state.dill # Pre-trained high-accuracy QNN model
└── QNN_0.15116397768110135-model_state.dill # Baseline QNN model
```

---

## 3. Quick Start on LUMI

### Option A: Command Line / Slurm Batch Execution

Activate the unified LUMI-IQ environment:

```bash
module use $HOME/modulefiles
module load lumi-iq

# Run forecasting inference using pre-trained QNN model (instant execution):
python run_time_series_forecasting.py

# Or train a new QNN model:
python run_time_series_training.py 50
```

The forecasting script evaluates prediction accuracy against real historical test prices and saves `result_time_series.png`.

### Option B: Interactive JupyterLab via Open OnDemand

1. Launch JupyterLab on [lumi.csc.fi](https://lumi.csc.fi) using the `lumi-iq` module script.
2. Open `time_series_forecasting.ipynb`.
3. Run all cells sequentially.
