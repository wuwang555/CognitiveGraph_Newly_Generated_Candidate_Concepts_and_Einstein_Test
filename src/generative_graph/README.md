# generative_graph — From the Four-Dimensional Concept Space to a Generative Graph

## In a Nutshell

Take the **fixpoints of Method B or Method C** as nodes, the G2 co-occurrence edges as the graph structure, and the four-dimensional Euclidean distance as edge weights, then run the original paper's evolution + compression/migration detection. **This is a replica of the original paper, except that `sim` is replaced by `d` and the nodes are replaced by B/C fixpoints.**

## Why Use Method B / Method C Fixpoints

- **Method B** = minimal frequent itemsets: structurally stable, indivisible units.
- **Method C** = role-consistent itemsets: functionally single, clearly bounded units.
- Both output single-concept fixpoints with `size=1` under `minsize=1`, which are suitable as nodes of the generative graph.

**Why not use B−C**: The semantics of B−C ("structurally stable but role-mixed") on the generative graph need to be re-determined later; the current version does not use B−C as a node source, and only builds graphs separately with Method B and Method C fixpoints. The B graph and the C graph are two independent generative graphs that can be compared and observed.

**Differences between the B graph and the C graph**:

- The B graph has more nodes (B is the minimal frequent itemset, covering a wider range);
- The C graph has fewer nodes (C requires role consistency, filtering out role-mixed hubs);
- The edge structures of both graphs come from G2 co-occurrence edges, but the node sets are different, so the compression/migration candidates are also different.

## Three Steps

1. **Nodes** = fixpoints of Method B or Method C (`minsize=1`, `size=1`)
2. **Edge structure** = G2 co-occurrence edges (non-Euclidean, so migration is meaningful)
3. **Edge weights** = four-dimensional Euclidean distance `d_ij = √(Δb² + Δc_norm² + Δg1_norm² + Δg2_norm²)`

## Correspondence with the Original Paper

| Original Paper | This Project |
|--------|--------|
| Fully connected energy graph | Sparse co-occurrence graph of B/C fixpoints |
| `E_ij = α(1−sim) + β/(1+H) + γ·div` | `E_ij = d_ij` (four-dimensional distance) |
| Energy decrease | Distance decrease (approach) |
| Compression: Φ = internal energy / external energy | Compression: Φ = external distance / internal distance |
| Migration: `E_az + E_zb < E_ab − Δ` | Migration: `d_az + d_zb < d_ab × (1−ε)` |

## Inputs

- `results/four_dim_vectors/config_{X}/scale{N}.csv` — four-dimensional coordinates
- `results/endo_result/scale{N}/config_{X}/minsize_{K}/fixpoint_{B}/fixpoints.json` — Method B fixpoints
- `results/endo_result/scale{N}/config_{X}/minsize_{K}/fixpoint_{C}/fixpoints.json` — Method C fixpoints
- `results/endo_result/raw_events_{X}/raw_compression_events.csv` — G2 edge source

## Outputs

- `results/generative_graph/config_{X}/scale{N}/method_{B|C}/`
  - `graph_nodes.csv` — nodes + four-dimensional coordinates
  - `graph_edges.csv` — edges (weight = four-dimensional distance, count = co-occurrence count)
  - `energy_history.csv` — evolution trajectory
  - `traversal_history.csv` — traversal paths
  - `candidate_compressions.csv` — compression candidates
  - `candidate_migrations.csv` — migration candidates
  - `info.json` — diagnostic information
- `results/generative_graph/summary.csv` — summary across config/scale/method

## How to Run

```bash
cd src/generative_graph
python run_generative.py
python run_generative.py --configs A --scales 51 --methods B C
```

## An Observation Point

The B/C graphs have few nodes (for A@51, the B graph has about 31 nodes and the C graph about 18; for B@51, the B graph has about 22 nodes and the C graph about 11; for C@51, the B graph has about 16 nodes and the C graph about 15), and even fewer edges (because both endpoints must be in B/C and must have co-occurred in G2).

**Small scale is a feature, not a defect**—it corresponds to the fact that "the stable core is limited." If both compression and migration are zero, it means that there is indeed no sufficiently dense structure inside this fixpoint set—this is also an observation.

**The B graph and the C graph should be read separately**:

- The B graph covers a wider range, suitable for observing "how minimal frequent units connect to each other";
- The C graph covers a narrower range, suitable for observing "how role-pure atoms connect to each other";
- Under the same config/scale, the compression/migration candidates of the B graph and the C graph can be compared, but the node sets should not be mixed.

## Semantics of Migration

On this sparse graph, `d(a,z) + d(z,b) < d(a,b)` is possible (G2 is non-Euclidean), so migration detection is meaningful. This is the key difference from a "fully connected Euclidean graph"—if the graph were fully connected, the triangle inequality would guarantee that a path is never shorter than a direct edge, and migration would always be zero.

## Boundaries

- This module is part of the concept generation project, not the "capturing the essentials" of the main repository. It takes B/C fixpoints as nodes, constructs a generative graph, and then runs compression/migration detection.
- B−C is not used as a node source for now; the generative graph semantics of B−C need to be re-determined later.
- The fixpoints of Method B and Method C are each used to build their own graphs, without merging.