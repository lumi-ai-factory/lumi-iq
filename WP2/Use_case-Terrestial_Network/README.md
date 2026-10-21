# Terrestrial Network Routing Optimisation — BF-DCQO / QAOA Notebook

Energy-efficient path selection on a terrestrial backbone network, formulated
as a QUBO and solved with Bias-Field Digitized Counterdiabatic Quantum
Optimization (BF-DCQO), benchmarked against QAOA, and transpiled to IQM
hardware's native gate set.

Main notebook: `notebooks/routing_bfdcqo_qaoa.ipynb`

---

## Requirements

- Windows with [Anaconda](https://www.anaconda.com/download) or Miniconda installed
- No GPU or special hardware needed — everything here runs on CPU via
  Qiskit Aer's simulator, and IQM hardware is targeted only via a
  noise-modeled fake backend by default

---

## Installation (conda)

Open **Anaconda Prompt** and run the following, one command at a time.

**1. Create and activate a dedicated environment**
```
conda create -n routing_bfdcqo python=3.12 -y
conda activate routing_bfdcqo
```

**2. Install the pinned package set**
```
pip install qiskit qiskit-aer "qiskit-iqm<18.0" networkx numpy scipy matplotlib jupyter nbformat ipykernel
```

> **Why the `qiskit-iqm<18.0` pin matters:** `qiskit-iqm` versions 18 and
> above switched to a new API (`iqm-client[qiskit]`) and raise a
> `RuntimeError` on import. Pinning below 18 installs the version this
> notebook was built and tested against, and it will also pull in a
> compatible `qiskit` (1.2.x) automatically.

**3. Register the environment as a Jupyter kernel**
```
python -m ipykernel install --user --name=routing_bfdcqo --display-name "Python (routing-bfdcqo)"
```

**4. Verify the install**
```
python -c "import qiskit; print(qiskit.__version__)"
```
This should print `1.2.x` (e.g. `1.2.4`). If it prints a `2.x` version
instead, the pin didn't take — fix it with:
```
pip install --force-reinstall "qiskit-iqm<18.0"
```

---

## Running the notebook

```
jupyter notebook
```

This opens Jupyter in your browser. Navigate to
`notebooks/routing_bfdcqo_qaoa.ipynb`, open it, then:

1. **Kernel → Change Kernel → "Python (routing-bfdcqo)"**
2. **Run All**

Full execution (dataset build → QUBO → Ising mapping → brute-force baseline →
BF-DCQO → QAOA → IQM transpilation → results) takes a few minutes on a
laptop CPU.

---

## What's inside

| Section | Contents |
|---|---|
| 1–2 | Problem statement and the 7-node Abilene-derived dataset (Chicago → Washington DC demand) |
| 3–4 | QUBO formulation (energy cost + flow conservation + congestion coupling) and a brute-force classical baseline |
| 5 | QUBO → Ising Hamiltonian mapping, sanity-checked against the baseline |
| 6 | BF-DCQO: simplified local/mean-field digitized counterdiabatic circuit with bias-field feedback |
| 7 | QAOA benchmark (p = 1, 2, 3), trained with COBYLA |
| 8 | Transpilation to IQM's native gate set (`IQMFakeApollo`); one-line swap for real IQM hardware |
| 9 | Head-to-head results, plots, and explicitly stated limitations |
| 10 | How this maps onto the project's seven-phase roadmap |

---

## Using your own dataset

The notebook currently reconstructs a representative 7-node subgraph rather
than reading `dataset/abilene_subgraph_dataset.json` directly. Section 2
contains a commented block showing exactly how to swap in the real dataset
file if you want the results to reflect it instead of the reconstruction.

---

## Troubleshooting

- **`RequestsDependencyWarning` about urllib3/charset_normalizer** — cosmetic,
  comes from `iqm-client`'s dependencies, safe to ignore.
- **`RuntimeError: The qiskit-iqm package is obsolete...`** — you have
  `qiskit-iqm >= 18`. Reinstall with the pin: `pip install --force-reinstall "qiskit-iqm<18.0"`.
- **Kernel not showing up in Jupyter** — re-run step 3 above with the
  environment activated, then restart Jupyter.
- **Import errors on `qiskit_algorithms`** — not required; this notebook
  implements QAOA manually (via `QAOAAnsatz` + `scipy.optimize`) to avoid a
  known version incompatibility between `qiskit_algorithms` 0.4.0 and
  `qiskit` 1.2.x.

---

**Author:** LUMI-IQ Consortium (WP2)
