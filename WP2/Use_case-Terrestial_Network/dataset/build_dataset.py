"""
build_dataset.py

Pipeline: parse Topology Zoo GML -> select connected subgraph (6-8 nodes) ->
augment with energy cost, capacity, and demand -> validate -> serialize.

Design note (read this before modifying):
    Each stage is a separate function with a narrow input/output contract
    (networkx.Graph in, networkx.Graph out, or plain dict/JSON out for the
    final stage). This means you can unit test "does augmentation produce
    positive costs" without needing GML parsing to be involved at all, and
    you can swap the subgraph-selection rule later without touching the
    augmentation logic. This is the main architectural habit worth copying
    into the rest of the project: resist the urge to write one big function
    that does everything end to end.
"""

import json
import math
import random
from pathlib import Path

import networkx as nx

RNG_SEED = 42  # fixed seed -> reproducible dataset, required for any real experiment log

# Resolve data files next to this script, so it runs from any working directory.
HERE = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Stage 1: parse
# ---------------------------------------------------------------------------

def load_topology(gml_path: str) -> nx.Graph:
    """Load a Topology Zoo GML file as an undirected graph.

    Topology Zoo files are undirected physical topologies (a link is a link,
    not a directed flow), so nx.Graph is correct here. Directionality of
    FLOW is a separate concept we introduce later in the QUBO, not a
    property of the physical graph.
    """
    g = nx.read_gml(gml_path, label="id")
    return g


# ---------------------------------------------------------------------------
# Stage 2: subgraph selection
# ---------------------------------------------------------------------------

def select_connected_subgraph(g: nx.Graph, target_size: int, seed: int = RNG_SEED) -> nx.Graph:
    """Select a connected induced subgraph of `target_size` nodes.

    Why not just g.subgraph(random_sample)?
        A uniformly random node sample from a sparse graph like Abilene
        (14 edges / 11 nodes, i.e. close to a tree) will very likely be
        DISCONNECTED. A disconnected subgraph has no valid source->sink
        routing at all, which silently breaks every downstream stage.

    Method used here: breadth-first "snowball" sampling from a random seed
    node. This guarantees connectivity by construction (every node added
    is adjacent to the growing set), which is a stronger guarantee than
    "sample then check and retry," and is O(target_size) instead of
    potentially many rejected retries.

    A secondary requirement we care about (see conversation): the subgraph
    should retain at least one cycle (an alternate path between some pair
    of nodes), otherwise there is only one possible route and BF-DCQO has
    nothing to select between. We check this explicitly and resample the
    seed node if the first attempt yields a tree.
    """
    rng = random.Random(seed)
    nodes = list(g.nodes())

    for attempt_seed_node in rng.sample(nodes, len(nodes)):
        visited = [attempt_seed_node]
        frontier = [attempt_seed_node]
        visited_set = {attempt_seed_node}

        while len(visited) < target_size and frontier:
            current = frontier.pop(0)
            neighbors = [n for n in g.neighbors(current) if n not in visited_set]
            rng.shuffle(neighbors)
            for n in neighbors:
                if len(visited) >= target_size:
                    break
                visited.append(n)
                visited_set.add(n)
                frontier.append(n)

        if len(visited) < target_size:
            continue  # this seed's component was too small, try another seed

        sub = g.subgraph(visited).copy()
        if not nx.is_connected(sub):
            continue  # shouldn't happen given BFS construction, but guard anyway

        n_edges = sub.number_of_edges()
        n_nodes = sub.number_of_nodes()
        has_cycle = n_edges >= n_nodes  # tree has exactly n_nodes - 1 edges

        if has_cycle:
            return sub
        # else: keep this as a fallback candidate, but keep looking for a cyclic one
        fallback = sub

    # If no cyclic subgraph of this size exists anywhere in the graph,
    # return the last connected (but tree-shaped) candidate and let the
    # caller decide -- this is a real limitation to surface, not hide.
    return fallback


# ---------------------------------------------------------------------------
# Stage 3: augmentation (energy cost, capacity, demand)
# ---------------------------------------------------------------------------

def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance between two lat/lon points, in km."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def augment_graph(
    g: nx.Graph,
    base_capacity_gbps: float = 10.0,   # OC-192 ~ 9.953 Gbps, rounded
    cost_per_km: float = 1.0,           # arbitrary energy-cost unit per km; see note below
    capacity_jitter_frac: float = 0.3,  # +/- 30% perturbation
    seed: int = RNG_SEED,
) -> nx.Graph:
    """Attach edge attributes `cost` and `capacity` that Topology Zoo does not provide.

    IMPORTANT (flag this in any writeup that uses this dataset):
    This is SYNTHETIC AUGMENTATION layered on REAL topology, not real
    operational data. Two explicit modeling choices are made here:

    1. cost_ij = cost_per_km * haversine_km(i, j)
       Physical justification: energy cost of a fiber link scales
       roughly with the number of optical amplifiers / regeneration
       sites needed, which scales with physical distance. This is a
       simplification -- real energy cost also depends on equipment
       generation, traffic load (some of it dynamic power), and
       amplifier spacing -- but distance-proportional cost is a
       standard, defensible first-order model in the network energy
       efficiency literature, and it uses information Topology Zoo
       actually gives us (real lat/lon), rather than inventing numbers
       with no grounding at all.

    2. capacity_ij = base_capacity_gbps * (1 + U(-jitter, +jitter))
       All Abilene links are physically OC-192 (uniform ~10 Gbps), so
       using that value uniformly would make the congestion-coupling
       term in the QUBO structurally inert -- every edge is equally
       "roomy" relative to any demand, so congestion penalties can
       never differentiate between routes. The jitter is a declared,
       seeded random perturbation whose ONLY purpose is to give the
       congestion term something non-trivial to act on. This must be
       reported as synthetic, not as recovered real capacity data.
    """
    rng = random.Random(seed)
    g = g.copy()

    for u, v, data in g.edges(data=True):
        lat_u, lon_u = float(g.nodes[u]["Latitude"]), float(g.nodes[u]["Longitude"])
        lat_v, lon_v = float(g.nodes[v]["Latitude"]), float(g.nodes[v]["Longitude"])
        dist_km = _haversine_km(lat_u, lon_u, lat_v, lon_v)

        data["distance_km"] = round(dist_km, 2)
        data["cost"] = round(cost_per_km * dist_km, 4)

        jitter = rng.uniform(-capacity_jitter_frac, capacity_jitter_frac)
        data["capacity"] = round(base_capacity_gbps * (1 + jitter), 3)

    return g


def add_demand(g: nx.Graph, source: int, sink: int, demand_gbps: float) -> dict:
    """Package a single-commodity demand alongside the graph.

    Kept as a separate plain dict (not a graph attribute) deliberately:
    demand is a property of a ROUTING REQUEST, not of the network itself.
    The same augmented graph should be reusable for many different
    (source, sink, demand) instances later (e.g. for QRC-driven re-runs
    in a future step) without re-deriving cost/capacity each time.
    """
    if source not in g.nodes or sink not in g.nodes:
        raise ValueError(f"source={source} or sink={sink} not in subgraph node set {list(g.nodes)}")
    return {"source": source, "sink": sink, "demand_gbps": demand_gbps}


# ---------------------------------------------------------------------------
# Stage 4: validation
# ---------------------------------------------------------------------------

def validate(g: nx.Graph, demand: dict) -> list:
    """Return a list of validation problems (empty list == passes).

    Kept as an explicit function (not just asserts scattered around) so
    the pipeline can report ALL problems at once rather than stopping at
    the first one -- useful when iterating on augmentation parameters.
    """
    problems = []

    if not nx.is_connected(g):
        problems.append("subgraph is not connected")

    n, m = g.number_of_nodes(), g.number_of_edges()
    if m < n:
        problems.append(f"subgraph is a tree ({m} edges, {n} nodes) -- no alternate paths exist anywhere")

    # BUG CAUGHT DURING INSPECTION (worth keeping this comment as a record):
    # "graph has >=1 cycle somewhere" is NOT the same as "source and sink
    # have >=2 simple paths between them." The first Abilene subgraph
    # generated (Chicago -> Indianapolis demand) passed the old weaker
    # check but had exactly ONE simple path between source and sink,
    # because the cycle in the subgraph didn't happen to involve either
    # endpoint. Checking path count for the SPECIFIC demand pair is the
    # check that actually matters for whether BF-DCQO has a real decision
    # to make.
    src, sink = demand["source"], demand["sink"]
    if src in g and sink in g and nx.has_path(g, src, sink):
        n_paths = sum(1 for _ in nx.all_simple_paths(g, src, sink, cutoff=n))
        if n_paths < 2:
            problems.append(
                f"only {n_paths} simple path(s) exist between source={src} and sink={sink} "
                f"-- routing decision is trivial, no alternate route to optimize over"
            )

    for u, v, data in g.edges(data=True):
        if data.get("cost", 0) <= 0:
            problems.append(f"edge ({u},{v}) has non-positive cost")
        if data.get("capacity", 0) <= 0:
            problems.append(f"edge ({u},{v}) has non-positive capacity")

    if src in g and sink in g and not nx.has_path(g, src, sink):
        problems.append(f"no path exists between source={src} and sink={sink}")

    # sanity check: is demand satisfiable by at least one simple path's
    # bottleneck capacity? (weak check -- doesn't prove multi-flow feasibility,
    # just rules out an obviously-impossible instance)
    if nx.has_path(g, src, sink):
        best_bottleneck = 0.0
        for path in nx.all_simple_paths(g, src, sink):
            bottleneck = min(g[path[i]][path[i + 1]]["capacity"] for i in range(len(path) - 1))
            best_bottleneck = max(best_bottleneck, bottleneck)
        if best_bottleneck < demand["demand_gbps"]:
            problems.append(
                f"demand {demand['demand_gbps']} Gbps exceeds best single-path "
                f"bottleneck capacity {best_bottleneck:.3f} Gbps -- infeasible instance"
            )

    return problems


# ---------------------------------------------------------------------------
# Stage 5: serialize
# ---------------------------------------------------------------------------

def serialize(g: nx.Graph, demand: dict, out_path: str, meta: dict):
    """Write a plain JSON representation -- deliberately NOT a pickled
    networkx object. JSON keeps the QUBO-construction stage (which we
    haven't built yet) decoupled from networkx as a dependency, and makes
    the dataset human-inspectable/diffable, which matters for a defensible
    writeup.
    """
    payload = {
        "meta": meta,
        "nodes": [
            {"id": n, "label": g.nodes[n].get("label", str(n))}
            for n in g.nodes
        ],
        "edges": [
            {
                "u": u,
                "v": v,
                "cost": data["cost"],
                "capacity": data["capacity"],
                "distance_km": data["distance_km"],
            }
            for u, v, data in g.edges(data=True)
        ],
        "demand": demand,
    }
    Path(out_path).write_text(json.dumps(payload, indent=2))
    return payload


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main():
    target_size = 7  # midpoint of the 6-8 range you chose

    g_full = load_topology(str(HERE / "Abilene.gml"))
    print(f"Loaded full Abilene topology: {g_full.number_of_nodes()} nodes, "
          f"{g_full.number_of_edges()} edges")

    g_sub = select_connected_subgraph(g_full, target_size=target_size)
    labels = [g_sub.nodes[n]["label"] for n in g_sub.nodes]
    print(f"Selected subgraph: {g_sub.number_of_nodes()} nodes, "
          f"{g_sub.number_of_edges()} edges -> {labels}")

    g_aug = augment_graph(g_sub)

    # Pick source/sink to be the pair with the MOST alternate simple paths,
    # among all pairs -- this is the pair where BF-DCQO actually has a
    # non-trivial decision to make. (Contrast with just taking the first
    # and last node in networkx's arbitrary node ordering, which is what
    # an earlier version of this script did, and which produced a
    # source/sink pair connected by a single direct edge with no
    # alternate route -- caught by inspecting the output, not by the
    # validator, which is exactly why validate() was tightened above.)
    node_list = list(g_aug.nodes)
    best_pair, best_n_paths = None, -1
    for i, a in enumerate(node_list):
        for b in node_list[i + 1:]:
            n_paths = sum(1 for _ in nx.all_simple_paths(g_aug, a, b, cutoff=g_aug.number_of_nodes()))
            if n_paths > best_n_paths:
                best_pair, best_n_paths = (a, b), n_paths
    src, sink = best_pair
    print(f"Chosen demand pair: {g_aug.nodes[src]['label']} -> {g_aug.nodes[sink]['label']} "
          f"({best_n_paths} alternate simple paths)")

    # pick demand at ~60% of the mean capacity so the instance is
    # non-trivially constrained but not obviously infeasible
    mean_cap = sum(d["capacity"] for _, _, d in g_aug.edges(data=True)) / g_aug.number_of_edges()
    demand = add_demand(g_aug, source=src, sink=sink, demand_gbps=round(0.6 * mean_cap, 2))

    problems = validate(g_aug, demand)
    if problems:
        print("VALIDATION PROBLEMS:")
        for p in problems:
            print(f"  - {p}")
    else:
        print("Validation passed: connected, has alternate paths, positive cost/capacity, demand feasible.")

    meta = {
        "source_topology": "Abilene (Internet Topology Zoo)",
        "citation": "Knight, S., Nguyen, H.X., Falkner, N., Bowden, R., Roughan, M. "
                    "'The Internet Topology Zoo.' IEEE JSAC, 2011.",
        "subgraph_selection": "BFS snowball sample, seeded, requires >=1 cycle",
        "augmentation": "SYNTHETIC: cost = cost_per_km * haversine_distance_km; "
                        "capacity = base_capacity_gbps * (1 + jitter), jitter ~ U(-0.3, 0.3). "
                        "Real Abilene links are uniform OC-192; capacity heterogeneity here "
                        "is entirely synthetic, introduced to make congestion-coupling terms "
                        "non-trivial.",
        "rng_seed": RNG_SEED,
        "target_subgraph_size": target_size,
    }

    out_path = str(HERE / "abilene_subgraph_dataset.json")
    payload = serialize(g_aug, demand, out_path, meta)

    print(f"\nWrote dataset to {out_path}")
    return payload


if __name__ == "__main__":
    main()
