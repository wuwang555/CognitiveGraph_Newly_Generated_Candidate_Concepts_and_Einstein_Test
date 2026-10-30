# README — Three Downstream Modules of the Cognitive Graph Project

> This document describes three downstream modules built on top of the
> two postulates of the original paper (*The Geometry, Algebra, and
> Dynamics of Cognition*): the **Generative Graph** (candidate new
> concepts), the **Einstein Test** (discoverability of insight from raw
> material), and the **Self-Reflection Loop** (self-modification under
> feedback).
>
> The overall stance is identical to the main project: **do not aim for
> fitting, aim for computability**. Each module states clearly what it
> does and what it observes, and marks its boundaries in the
> conclusion.

---

## 0. Common ground: what the three modules share

All three modules sit on top of the same upstream pipeline, which is
already implemented in the main project and **must not be modified**:

```
G1  cognitive energy graph
    ↓ spontaneous compression events
G2  undirected weighted co-occurrence graph
    ↓ fixpoint detection (methods A / B / C)
fixpoints  (core / boundary / logic / energy)
    ↓ mapping
four-dimensional continuous space  (b, c, g1, g2)
```

None of the three modules introduces a new postulate. Every threshold
is absolute, so scales remain comparable. Every candidate is a
candidate, not a verified concept. The three modules differ only in
**what they do with the fixpoints and the 4D coordinates**:

| Module | Input from the shared layer | What it does | What it produces |
|---|---|---|---|
| **Generative Graph** | fixpoints (B or C), 4D coordinates, G2 edges | evolve a sparse graph whose nodes are fixpoints and whose edge weight is the 4D Euclidean distance; detect compression and migration | **candidate new concepts** (clusters and paths of fixpoints) |
| **Einstein Test** | 82 pre-relativity concepts, full pipeline | check whether migration detection can connect "principle of relativity" to tensor analysis / Riemannian geometry / Maxwell's equations | **evidence that insight chains are discoverable** from raw material |
| **Self-Reflection Loop** | G3 results (clusters + migrations from the generative graph) | abstract feedback rules K and write them back into G1's energy formula, traversal preference, and detection criteria; iterate | **observation of how the system drifts** under self-feedback |

The three modules are *downstream* of "抓重点" (extracting what the
system repeatedly focuses on). They are **not** part of the main
repository's "抓重点" layer, and they **do not claim to generate
verified new concepts**. What they generate are candidate structures
whose meaning must be interpreted afterwards.

---

## 1. Generative Graph — candidate new concepts

### 1.1 What it is

The generative graph treats **fixpoints as nodes**, uses **G2
co-occurrence edges as the graph structure**, and uses the **4D
Euclidean distance as the edge weight**:

```
d_ij = sqrt( Δb² + Δc_norm² + Δg1_norm² + Δg2_norm² )
```

It then runs the original paper's evolution and compression/migration
detection on this graph. In the language of the original paper:

| Original paper | Generative graph |
|---|---|
| Fully-connected energy graph | Sparse co-occurrence graph over fixpoints |
| `E_ij = α(1−sim) + β/(1+H) + γ·div` | `E_ij = d_ij` (4D distance) |
| Energy descent | Distance descent |
| Compression `Φ = internal / external` | Compression `Φ = external distance / internal distance` |
| Migration `E_az + E_zb < E_ab − Δ` | Migration `d_az + d_zb < d_ab × (1−ε)` |

### 1.2 Why fixpoints rather than raw concepts

A raw concept is a node in G1. A fixpoint is a **stable unit** that the
system repeatedly compresses. When several fixpoints are connected by
compression or migration on the generative graph, the resulting cluster
or path is what we call a **candidate new concept**:

- its **core** is the set of fixpoints joined by compression or migration;
- its **boundary** is the union of the fixpoints' own boundaries, kept
  per-fixpoint (the same boundary concept may carry different `logic`
  weights toward different fixpoints — we do not collapse them);
- its **logic** is the per-fixpoint `logic` strength, preserved as a
  bipartite structure `(boundary concept, fixpoint) → strength`;
- its **description** is not an action of the system but a property of
  the definition form: once the core / boundary / logic are recorded,
  the description exists automatically.

### 1.3 What it does **not** do

- It does **not** claim to "generate concepts" in the sense of adding
  new nodes to G1. The candidate clusters and paths are **observed
  structures on top of existing fixpoints**, not new units fed back
  into the first-order system.
- It does **not** filter candidates by external semantic criteria. A
  candidate is a candidate; whether it is "meaningful" is a downstream
  judgement, not a property of the graph.
- It does **not** collapse the per-fixpoint boundary structure. The
  boundary of a candidate is a bipartite object, not a flat set.

### 1.4 Entry point and outputs

```
src/generative_graph/
    build_graph.py      build the sparse 4D-distance graph
    evolve.py           run the original paper's evolution
    detect.py           compression and migration detection
    run_generative.py   end-to-end entry point
```

Outputs (per config, per scale, per fixpoint method):

```
results/generative_graph/config_{X}/pool_{P}/scale{N}/
    graph_nodes.csv
    graph_edges.csv
    energy_history.csv
    traversal_history.csv
    candidate_compressions.csv
    candidate_migrations.csv
    info.json
results/generative_graph/summary.csv
```

---

## 2. Einstein Test — discoverability of insight from raw material

### 2.1 What it is

The Einstein Test asks a narrow, falsifiable question:

> Given only the conceptual raw material available **before** the birth
> of relativity, can the four-dimensional concept-space migration
> detection connect "principle of relativity" to tensor analysis /
> Riemannian geometry / Maxwell's equations?

The concept set contains **82 concepts** from 8 domains (classical
mechanics, electromagnetism, thermodynamics, fluids/elasticity,
mathematics, spacetime/relativity, astronomy, principles), and
explicitly **excludes** "relativity", "quantum mechanics", and
"quantum field theory".

The test looks for migrations of the form:

- `principle of relativity → (bridge) → Maxwell's equations` (special relativity)
- `principle of relativity → (bridge) → tensor analysis` (the language of general relativity)
- `principle of relativity → (bridge) → Riemannian geometry` (the geometry of general relativity)
- `absolute spacetime → (bridge) → principle of relativity` (the shift of spacetime view)

**Not all four are required to appear.** A single appearance is enough
to show that "from raw material to insight" is observable in the 4D
concept space.

### 2.2 What "success" means and does not mean

- **Success** means: a chain of the right *shape* is discoverable from
  the raw material. It does **not** mean the system "invented
  relativity". The system has no trigger word, no historical context,
  no experimental constraints.
- **Partial success is success.** If steps 4–7 of Einstein's reasoning
  chain are traversed but steps 1–3 are missing, that is still a
  positive result: it demonstrates *structural discoverability under
  incomplete initial conditions*.
- **Failure is informative.** If no chain appears, it means the raw
  material as encoded does not support the chain under the current
  distance metric. That is an observation about the encoding, not a
  refutation of the original paper.

### 2.3 Entry point and outputs

```
src/einstein_test/
    concepts_einstein.py   82 concepts, 8 domains, meta-structure
    run_all.py             end-to-end entry point
```

Outputs:

```
results/einstein_test/
    stage1_universe/       raw compression events + energy summary
    stage2_graph/          G2 co-occurrence graph
    stage3_fixpoints/      fixpoints A/B/C + structured definitions
    stage4_g1/             G1 energy graph export
    stage5_four_dim/       4D space + PCA
    stage6_generative/     generative graph + compression/migration candidates
    einstein_test_summary.json
```

The stage numbering mirrors the six-ring logic chain of the main
project, so the Einstein Test can be read as "the same pipeline, run on
a deliberately restricted concept set".

---

## 3. Self-Reflection Loop — self-modification under feedback

### 3.1 What it is

The Self-Reflection Loop is the only module that **modifies the
first-order system**. It does so in a strictly bounded way:

```
G1 → G2 → fixpoints → 4D → generative graph → G3 (clusters + migrations)
    ↑                                                   │
    └────── feedback K (edge boosts, preferred paths) ──┘
```

At each round:

1. Run G1 for a fixed number of iterations (`interval_iterations`).
2. Build G2, detect fixpoints, map to 4D, build the generative graph,
   and detect compression and migration (**G3**).
3. Abstract a feedback rule set **K** from G3:
   - `edge_boosts`: for each pair of concepts that appears together in
     a high-Φ cluster or a high-improvement migration, an extra
     learning-rate multiplier `(1 + δ)`.
   - `preferred_paths`: the actual high-improvement paths, used to
     bias neighbor selection during traversal.
   - `cluster_patterns`: the high-Φ clusters, used to tag future
     compression events with a `g3_matched` flag.
4. Write K back into G1:
   - `record_edge_activation`: learning rate × `(1 + boost)`.
   - `_random_traversal`: neighbor selection weighted by
     `(1 / weight) × (1 + boost)`.
   - `_detect_emergence`: matching events get a `g3_matched` flag.
5. Continue the next round from the saved G1 state.

### 3.2 What "self-modification" changes — and what it does not

**It changes the connection layer.** The feedback is applied to edge
weights, traversal preferences, and detection flags. This is the layer
that decides *how the system walks between fixpoints*.

**It does not change the criterion layer.** The two postulates, all
thresholds (`lattice_min_support`, `role_min_stability`,
`compression_phi_threshold`, `migration_epsilon`, ...), and all
detection rules remain fixed. The system does not decide "what counts
as a fixpoint" differently across rounds.

**It does not change the membership layer.** In the observed five-round
run, B stayed at 33–34 members and C at 19–20. Only one concept
(`attention mechanism`) entered at round 4 and stayed; one
(`generative adversarial network`) dropped out of C at round 3 and
returned at round 4. The core membership is essentially stable.

So the self-modification is **not** "the system learns new concepts".
It is "the system learns new *routes* between existing stable units".

### 3.3 What the five-round run shows

The observation is best described as **drift**, not as "improvement" or
"degradation". Three facts stand out:

1. **The drift has a direction.** Over five rounds, the path layer
   shifted from CS-infrastructure hubs (IoT, information security,
   algorithms) toward AI / software-engineering / compiler /
   NLP hubs. The physics axis stayed present throughout and swung back
   to the head at round 5. This is a *directional* drift, not random
   noise.
2. **The drift has a structure.** The head of the improvement
   distribution did not rise monotonically; the number of paths in the
   middle band (0.1–0.3) kept growing while the head peaked around
   round 2. The drift widens the *middle*, not the *head*.
3. **The drift does not run away.** `raw_compressions` stayed in
   1184–1265 (±6.8%); `edge_boosts` stayed at 202–215;
   `preferred_paths` stayed at 193–227. The feedback rule set K is
   **recomputed each round, not accumulated**, which prevents the
   system from locking onto a small set of edges.

### 3.4 On "correctness" — there is no external check

This is the most important boundary of the Self-Reflection Loop.

- The system has **no external semantic check**. There is no reward
  function, no labeled data, no downstream task accuracy. There is no
  "right answer" against which to compare the drift.
- What the system **does** have is **internal consistency**: K is
  abstracted from G3, and G3's `improvement` is defined in terms of the
  system's own 4D distance. The boosted edges are those that the
  previous round's G3 considered "energy-cheaper" under the current
  metric.
- Therefore, the drift is **self-consistent directional drift**, not
  random noise and not verified improvement. The distinction matters:
  *self-consistent* does not mean *correct*; it means the drift is
  organized by the system's own criterion rather than by external
  supervision.

Any statement about whether the drift is "good" belongs to a different
kind of inquiry — LLM reward functions, human semantic review, or
downstream task evaluation. Those are *external* checks, and this
module deliberately does not perform them.

### 3.5 Entry point and outputs

```
src/self_reflection/
    config_reflect.py     loop configuration
    state_io.py           save / load G1 state across rounds
    feedback_rules.py     abstract K from G3
    energy_patch.py       energy-formula / traversal-preference patch
    detector_patch.py     no-truncation compression detector
    reflected_universe.py wrap G1 to support "original" / "reflected" modes
    pipeline_adapter.py   G2 → fixpoints → 4D → generative graph → detect
    reflect_loop.py       main loop
    run_reflection.py     entry point
```

Outputs:

```
results/self_reflection/
    round_001/
        universe_state/    graph.pkl + state.json
        g3/                g3_result.json + fixpoints_selected.json
        feedback_K.json
    round_002/
        ...
    summary.csv           one row per round
```

The `summary.csv` columns are:

```
round, mode, iter_start, iter_end,
raw_compressions, raw_migrations,
g2_nodes, g2_edges,
n_B, n_C, n_selected,
n_b_fps, n_c_fps,
gen_nodes, gen_edges,
n_clusters, n_migrations,
n_edge_boosts, n_preferred_paths,
fixpoint_method
```

---

## 4. How the three modules relate

```
                          ┌─────────────────────────┐
                          │  Einstein Test          │
                          │  (82 raw concepts)      │
                          │  asks: is an insight    │
                          │  chain discoverable     │
                          │  from raw material?     │
                          └───────────┬─────────────┘
                                      │ same pipeline
                                      ▼
main project ──► G1 ──► G2 ──► fixpoints ──► 4D
                                      │
                                      ▼
                          ┌─────────────────────────┐
                          │  Generative Graph       │
                          │  (fixpoints as nodes)   │
                          │  asks: which fixpoint   │
                          │  clusters / paths are   │
                          │  candidate new concepts?│
                          └───────────┬─────────────┘
                                      │ G3: clusters + migrations
                                      ▼
                          ┌─────────────────────────┐
                          │  Self-Reflection Loop   │
                          │  asks: how does the     │
                          │  system drift when its  │
                          │  own G3 is fed back?    │
                          └─────────────────────────┘
```

- The **Generative Graph** is the *observation layer*: it reads
  fixpoints and 4D coordinates, and produces candidate structures.
- The **Einstein Test** is the *discoverability layer*: it applies the
  same pipeline to a deliberately restricted concept set, and asks
  whether a known insight chain is structurally discoverable.
- The **Self-Reflection Loop** is the *feedback layer*: it consumes
  G3 and writes K back into G1, producing a sequence of rounds whose
  drift can be described.

All three modules share the same design stance:

- **No new postulates.** The two axioms of the original paper remain
  the only driving force.
- **No absolute thresholds change.** Every module uses the same
  absolute thresholds so that scales remain comparable.
- **No claim of verified concepts.** Everything produced is a
  *candidate*. Verification, if it happens, is external.
- **No fitting.** The goal is to construct a computable system and
  observe what it does.

---

## 5. Running the three modules

```bash
# Generative graph
cd src/generative_graph
python run_generative.py

# Einstein test
cd src/einstein_test
python run_all.py

# Self-reflection loop
cd src/self_reflection
CONFIG_METHOD=A python run_reflection.py \
    --rounds 5 --interval 10000 --num_concepts 51
```

Dependencies: `numpy`, `pandas`, `networkx`, `scipy`, `matplotlib`,
`jieba`.

---

## 6. Boundaries — one paragraph each

**Generative Graph.** The clusters and paths it produces are candidate
new concepts, not verified concepts and not new nodes in G1. The
boundary of a candidate is a per-fixpoint bipartite structure, not a
flat set. Whether a candidate is meaningful is a downstream judgement.

**Einstein Test.** The test does not claim that the system "invented
relativity". It claims that a chain of the right shape is
*structurally discoverable* from the raw material under the current
distance metric. Partial success (steps 4–7 traversed, steps 1–3
missing) is still a positive result. Failure is an observation about
the encoding, not a refutation.

**Self-Reflection Loop.** The system changes its *connection layer*,
not its *criterion layer* or *membership layer*. There is no external
check; the drift is *self-consistent* directional drift, not verified
improvement. Any judgement of "good" or "bad" drift belongs to external
checks (reward functions, human review, downstream tasks), which this
module deliberately does not perform.

---

## 7. One-line summary

**The Generative Graph produces candidate new concepts by connecting
fixpoints on a 4D-distance graph; the Einstein Test checks whether a
known insight chain is structurally discoverable from restricted raw
material; the Self-Reflection Loop feeds G3 back into G1 and observes
how the system drifts. The three modules share the same two postulates,
the same absolute thresholds, and the same stance: no fitting, no claim
of verified concepts, only computable observations with explicit
boundaries. What the Self-Reflection Loop shows is that under
self-feedback the system drifts in a direction and with a structure,
without running away — a self-consistent directional drift, not a
verified improvement.**