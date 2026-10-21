# Dataset Description: Abilene Subgraph Routing Instance

**Location:** `Terrestial Network\dataset\`
**Files:** `Abilene.gml`, `build_dataset.py`, `abilene_subgraph_dataset.json`
**Status:** First validation instance for BF-DCQO routing QUBO (pure BF-DCQO, no QRC)

---

## 1. Why three files, not one

These three files represent three different **stages of provenance**, and keeping
them separate (rather than only shipping the final JSON) is a deliberate choice:

| File | What it is | Why it's kept |
|---|---|---|
| `Abilene.gml` | Raw, unmodified real-world topology | Provenance record — proves what came from the real dataset vs. what we added |
| `build_dataset.py` | The transformation logic | Reproducibility — anyone (including future you) can regenerate the JSON from the GML and verify no silent changes crept in |
| `abilene_subgraph_dataset.json` | Final augmented, validated instance | The actual input consumed by the next stage (QUBO construction) |

If we only kept the JSON, there would be no way to distinguish "real data" from
"data we invented" without digging through chat history — a problem for anyone
trying to check this work later, including a reviewer, a collaborator, or you
in six months. This separation is a basic reproducibility habit worth carrying
through the rest of the project: **raw source → transformation script →
derived artifact**, each independently inspectable.

---

## 2. `Abilene.gml` — raw source data

- **Source:** The Internet Topology Zoo, a public repository of real ISP/backbone
  network topologies transcribed from network operator data.
- **Citation:** Knight, S., Nguyen, H.X., Falkner, N., Bowden, R., Roughan, M.
  *"The Internet Topology Zoo."* IEEE Journal on Selected Areas in Communications, 2011.
- **What it is:** Abilene — the (historic, ~2005) Internet2 U.S. research
  backbone network.
- **Contents:** 11 nodes (major U.S. cities: New York, Chicago, Washington DC,
  Seattle, Sunnyvale, Los Angeles, Denver, Kansas City, Houston, Atlanta,
  Indianapolis), 14 undirected edges, each labeled `OC-192` (~9.953 Gbps SONET
  link, uniform across the whole network).
- **What it does NOT contain:** per-link energy cost, per-link differentiated
  capacity, or any traffic demand. Topology Zoo records physical topology and
  provenance metadata only — it is not a traffic engineering dataset.

This file is the **ground-truth anchor** for the whole pipeline: real node
positions (lat/lon) and real connectivity. Nothing in this file was modified.

---

## 3. `build_dataset.py` — the transformation pipeline

This script turns the raw 11-node topology into a small, solvable routing
instance. It is structured as five explicit stages, each with a narrow
input/output contract, so any one stage can be tested, debugged, or replaced
without touching the others:

```
load_topology()  ->  select_connected_subgraph()  ->  augment_graph()
                                                          |
                                                          v
                                                     add_demand()
                                                          |
                                                          v
                                                      validate()
                                                          |
                                                          v
                                                     serialize()
```

### Stage 1 — `load_topology()`
Parses the GML file into a NetworkX graph. Kept as its own function so the
rest of the pipeline never needs to know GML exists — if we swap to a
different Topology Zoo network later, only this function's input path changes.

### Stage 2 — `select_connected_subgraph()`
Abilene has 11 nodes; we need 6–8. A **uniformly random** node sample would
very likely produce a **disconnected** subgraph, since Abilene is sparse
(14 edges over 11 nodes — close to tree-like). A disconnected subgraph has no
valid source→sink route at all, silently breaking everything downstream.

Instead, this uses **BFS "snowball" sampling**: start from a random seed node,
repeatedly add graph-adjacent neighbors until the target size is reached.
Connectivity is guaranteed by construction — every added node is adjacent to
the growing set — rather than relying on "sample and hope."

It also checks for at least one cycle in the sampled subgraph, because a
tree-shaped subgraph would mean the whole network has only one possible route
between any two nodes, in which case BF-DCQO has literally nothing to
optimize over.

**Current output:** 7 nodes — Chicago, Washington DC, Denver, Kansas City,
Houston, Atlanta, Indianapolis — with 7 edges (exactly one cycle).

### Stage 3 — `augment_graph()` + `add_demand()`
This is where **synthetic data is added on top of real topology** — the most
important thing to flag honestly in any writeup that uses this dataset.

- **`cost` (energy cost per edge)** = `cost_per_km × great-circle distance (km)`.
  Justification: fiber-link energy cost scales roughly with physical distance
  (more optical amplifiers / regeneration sites over longer spans). This uses
  the *real* lat/lon from Topology Zoo, so it's a grounded first-order model,
  not an arbitrary number — but it is still a simplification (ignores
  equipment generation, load-dependent dynamic power, etc.) and should be
  described as such.
- **`capacity` (per edge)** = `base_capacity_gbps × (1 + jitter)`, jitter drawn
  from `Uniform(-0.3, +0.3)` with a fixed random seed.
  Justification: real Abilene links are *uniformly* OC-192 — if we kept that
  uniform value, every edge would be equally "roomy" relative to any demand,
  and the congestion-coupling term in the QUBO would have nothing to
  differentiate between routes. The jitter is **entirely synthetic** and
  exists solely to make congestion coupling non-trivial. This must be
  reported as synthetic, not mistaken for recovered real capacity data.
- **`demand`** (source, sink, demand in Gbps) is kept as a *separate* object
  from the graph, not baked into node/edge attributes — because demand
  describes a specific routing *request*, while cost/capacity describe the
  *network*. The same augmented graph should be reusable for other demand
  instances later (e.g., different demand pairs, or eventually time-varying
  demand fed by the QRC extension) without re-deriving cost/capacity each time.

The demand pair is chosen as the (source, sink) combination with the **most
alternate simple paths** among all pairs in the subgraph — i.e., the pair
where BF-DCQO actually has a non-trivial routing decision to make, rather than
an arbitrary pair that might only have one possible route.

**Current instance:** Chicago → Washington DC, 5.98 Gbps demand, with two
feasible routes of meaningfully different cost (1822.9 vs. 4035.4 cost units),
both sharing a bottleneck edge (Atlanta–Washington DC).

### Stage 4 — `validate()`
Checks, and reports *all* problems at once rather than stopping at the first:
- subgraph connectivity,
- the subgraph isn't a tree,
- **the specific demand pair has ≥2 simple paths** (not just "a cycle exists
  somewhere in the graph" — see note below),
- all costs and capacities are positive,
- a path exists between source and sink,
- the demand is satisfiable by at least one path's bottleneck capacity.

> **Note on a bug caught during development:** an earlier version of this
> validator only checked "does the subgraph contain a cycle anywhere,"
> which is *not* the same as "does the source/sink pair have an alternate
> route." The first generated instance (Chicago→Indianapolis) passed that
> weaker check but turned out to have exactly one possible route — the graph's
> only cycle didn't happen to touch either endpoint. This was caught by
> independently re-deriving all simple paths, not by trusting the validator's
> own "passed" message. The validator was rewritten to check path count for
> the *specific* demand pair, and the demand-selection logic in `main()` was
> changed to actively pick the pair with the most alternate routes. Kept as a
> comment in the code and here as a reminder: a validator is only as good as
> the condition it actually checks — "it ran without error" is not the same
> as "it's correct."

### Stage 5 — `serialize()`
Writes the final graph, demand, and full provenance metadata (source citation,
augmentation formulas, RNG seed, selection method) to plain JSON — deliberately
*not* a pickled NetworkX object. This keeps the next stage (QUBO construction)
free of a NetworkX dependency, and keeps the dataset human-readable and
diffable, which matters for a defensible, inspectable writeup.

---

## 4. `abilene_subgraph_dataset.json` — the final instance

Structure:
```json
{
  "meta": { ... provenance, citation, augmentation formulas, RNG seed ... },
  "nodes": [ { "id": ..., "label": ... }, ... ],
  "edges": [ { "u": ..., "v": ..., "cost": ..., "capacity": ..., "distance_km": ... }, ... ],
  "demand": { "source": ..., "sink": ..., "demand_gbps": ... }
}
```

This is the file the next pipeline stage (QUBO/Ising formulation for BF-DCQO)
should read. It fully specifies one solvable routing instance:

- 7 nodes, 7 edges (Chicago, Washington DC, Denver, Kansas City, Houston,
  Atlanta, Indianapolis)
- per-edge energy cost and capacity (real distance-based cost, synthetic
  capacity jitter)
- one single-commodity demand: Chicago → Washington DC, 5.98 Gbps
- small enough to brute-force for validation against BF-DCQO's output

---

## 5. Known limitations (carry these into the technical writeup)

- **Single commodity, static snapshot.** No concurrent demands, no time
  variation. Appropriate for first-pipeline validation; not yet representative
  of real multi-flow traffic engineering.
- **Synthetic augmentation.** Cost and capacity are modeled, not measured.
  Cost has a physical grounding (real distance); capacity heterogeneity is
  purely synthetic (real Abilene links are uniform OC-192).
- **Small scale.** 7 nodes is deliberately brute-forceable, not representative
  of production-scale ISP topology. Scaling behavior of BF-DCQO on this
  instance size says nothing about scaling to hundreds of nodes.
- **Reproducibility depends on the fixed seed (`RNG_SEED = 42`)** in
  `build_dataset.py`. Changing the seed will select a different subgraph
  and/or different capacity jitter values, and regenerate a different
  (but equally valid) instance.

---

## 6. To regenerate

```bash
python build_dataset.py
```

Reads `Abilene.gml` from the same directory, writes
`abilene_subgraph_dataset.json`. Deterministic given the fixed seed — running
it again produces an identical file, which is the point.


**Author:** LUMI-IQ Consortium (WP2)
