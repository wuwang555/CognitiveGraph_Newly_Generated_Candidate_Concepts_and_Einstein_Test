# Einstein Test

## In a Nutshell

Feed the **82** physics/mathematics concepts from "before the birth of relativity" into the system, and see whether it can connect the "principle of relativity" with "tensor analysis / Riemannian geometry / Maxwell's equations" through migration detection in the four-dimensional concept space—this corresponds to the core insight of relativity.

## Concept Set Design

**Excludes**: "Relativity", "Quantum Mechanics", "Quantum Field Theory"
**Includes**: all the "raw materials" Einstein needed to develop relativity, **82** concepts in total, belonging to 8 domains.

| Domain | Count | Concepts |
|----|------|------|
| Classical Mechanics | 22 | Newton's Laws, Universal Gravitation, Mechanics, Kinematics, Momentum, Conservation of Energy, Friction, Rigid Body, Vibration, Wave, Inertia, Acceleration, Work, Power, Angular Momentum, Kepler's Laws, Tidal Force, Centrifugal Force, Coriolis Force, Velocity, Inertial Mass, Gravitational Mass |
| Electromagnetism | 15 | Electrostatic Force, Electromagnetism, Maxwell's Equations, Speed of Light, Ether, Optics, Acoustics, Electric Field, Magnetic Field, Electric Potential, Inductance, Capacitance, Electromagnetic Waves, Interference of Light, Diffraction of Light |
| Thermodynamics | 9 | Thermodynamics, Heat Conduction, Entropy, Temperature, Heat, Ideal Gas, Heat Engine, Carnot Cycle, Thermal Radiation |
| Fluid/Elasticity | 2 | Fluid Mechanics, Elasticity |
| Mathematics | 17 | Calculus, Geometry, Linear Algebra, Differential Equations, Calculus of Variations, **Tensor Analysis**, **Non-Euclidean Geometry**, **Riemannian Geometry**, Topology, Group Theory, Partial Differential Equations, Spherical Harmonics, Complex Functions, Fourier Transform, Differential Geometry, Vector Analysis, Probability Theory |
| Space-Time/Relativity | 10 | **Absolute Space-Time**, **Principle of Relativity**, Inertial Frame, **Galilean Transformation**, Coordinate System, Reference Frame, Simultaneity, Time, Space, Length |
| Astronomy | 3 | Celestial Mechanics, Cosmology, Gravitational Field |
| Methodology | 4 | **Symmetry**, Conservation Laws, Field, **Covariance** |

**Bolded** items are key raw materials directly related to the insight of relativity: Tensor Analysis, Non-Euclidean Geometry, Riemannian Geometry, Absolute Space-Time, Principle of Relativity, Galilean Transformation, Symmetry, Covariance.

**Domain division note**: The concept set is divided into 8 domains by `EINSTEIN_DOMAINS`. The methodology domain is named `principles` in the code, so as to enjoy the original paper's "cross-domain 0.6" preference; this does not affect the concepts themselves, only the cross-domain edge weights when building the graph.

## What to Look For

After running, open `stage6_generative/candidate_migrations.csv` and see whether the following appear:

- `Principle of Relativity → (bridge) → Maxwell's Equations` → the core of special relativity
- `Principle of Relativity → (bridge) → Tensor Analysis` → the language of general relativity
- `Principle of Relativity → (bridge) → Riemannian Geometry` → the geometry of general relativity
- `Absolute Space-Time → (bridge) → Principle of Relativity` → the transformation of the view of space-time

**Not all are required to appear**. As long as one appears, it shows that the path "from raw materials to insight" is observable in the four-dimensional concept space.

**Supplementary reading**:

- Each row of `candidate_migrations.csv` is `start, via, end, direct_distance, path_distance, improvement`. The larger `improvement` is, the more this migration path "saves" compared with a direct connection, i.e., the stronger the structural role of the bridge node (`via`).
- `candidate_compressions.csv` gives compression candidates (`center, cluster, size, phi`), which can be used to observe whether key concepts such as "Principle of Relativity", "Absolute Space-Time", and "Tensor Analysis" appear as compression centers or cluster members.
- `stage3_fixpoints/fixpoints.json` gives the structured definitions of fixpoints A/B/C. For Method A: `size=1` are atomic fixpoint candidates, `size>1` are high-frequency whole candidates at the raw event level; itemsets with `size≥2` carry `phi`. For Methods B/C: under `minsize=1`, typically outputs single-concept candidates with size=1 and `phi=null`.

## Outputs

```
results/einstein_test/
├── stage1_universe/    raw compression events + energy summary
├── stage2_graph/       compression association graph G2
├── stage3_fixpoints/   fixpoints A/B/C + structured definitions
├── stage4_g1/          G1 energy graph export
├── stage5_four_dim/    four-dimensional concept space + PCA
├── stage6_generative/  generative graph + compression/migration candidates
└── einstein_test_summary.json
```

**Each stage corresponds to the six-stage logic chain of this repository**:

| stage | Corresponding stage | Main outputs |
|-------|---------|---------|
| `stage1_universe/` | First-order system evolution | `raw_compression_events.csv`, energy summary |
| `stage2_graph/` | Stage 1: G2 relation graph | `compression_edges.csv`, graph statistics |
| `stage3_fixpoints/` | Stage 4: Fixpoints | `fixpoints.json`, `concept_structure.json` |
| `stage4_g1/` | Stage 5: G1 export | `g1_nodes.csv`, `g1_edges.csv`, `energy_history.csv` |
| `stage5_four_dim/` | Stage 5: Four-dimensional space | `scale{N}.csv`, `scale{N}_pca.csv` |
| `stage6_generative/` | Generative graph at the input side of hierarchy reduction | `candidate_compressions.csv`, `candidate_migrations.csv` |

**Note**: The "generative graph" in `stage6_generative/` is an observation graph built on fixpoints within the scope of this repository, used to detect compression/migration candidates. It is not the "concept-generation graph construction and hierarchy-reduction re-compression/migration" of another project—this repository only does "capturing the essentials", not concept generation.

## How to Run

```bash
cd src/einstein_test
python run_all.py
```

## Concept Set Source

Concept definitions are in `EINSTEIN_CONCEPTS` of `concepts_einstein.py` (82 concepts), domain divisions are in `EINSTEIN_DOMAINS` (8 domains), and meta-structures are in `EINSTEIN_META` (10 meta-structures: Structure, Motion, Energy, Force, Abstraction, Medium, Celestial Body, Field, Quantity, Space-Time).

**Design principles** (from `concepts_einstein.py`):

- Each definition is one sentence, natural, without piling up bridge words;
- Use the "basic vocabulary" of physics/mathematics (force, motion, field, space, time, law, conservation, symmetry, transformation, metric, geometry, coordinate, reference frame);
- Let jieba naturally segment shared words, rather than inserting them manually;
- The methodology domain is renamed `principles`, so as to enjoy the original paper's "cross-domain 0.6" preference.