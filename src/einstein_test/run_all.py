# -*- coding: utf-8 -*-
"""
爱因斯坦测试主入口。

流程：
  Stage 1. universe → 原始压缩事件
  Stage 2. 压缩关联图（G2）
  Stage 3. 不动点检测（A / B / C）
  Stage 4. G1 能量图导出
  Stage 5. 四维概念空间（b, c, g1, g2）
  Stage 6. 生成图（B−C + 四维距离 + 压缩/迁移检测）

输出：results/einstein_test/

用法：
    cd src/einstein_test
    python run_all.py
"""

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---- 路径 ----
_HERE = Path(__file__).resolve().parent          # .../src/einstein_test
_SRC = _HERE.parent                               # .../src
_PROJ = _SRC.parent                               # project root
for _p in (str(_HERE), str(_SRC), str(_PROJ)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ====================================================================== #
# ★ 在导入任何子模块之前，先替换 config 里的概念集
# ====================================================================== #
def setup_einstein_concepts():
    """把 config 里的三张概念表替换为爱因斯坦测试集。

    注意：
      - 不 reload config（reload 会把刚才的修改重置回默认值）
      - 只修改属性，下游 `from config import X` 在模块加载时取新值
      - 所以本函数必须在任何依赖 config 的子模块第一次被 import 之前调用
    """
    import config
    from concepts_einstein import (
        EINSTEIN_CONCEPTS, EINSTEIN_DOMAINS, EINSTEIN_META,
    )

    config.CORE_CONCEPT_DEFINITIONS = EINSTEIN_CONCEPTS
    config.CONCEPT_DOMAINS = EINSTEIN_DOMAINS
    config.META_STRUCTURE_MAP = EINSTEIN_META
    return len(EINSTEIN_CONCEPTS)


# ====================================================================== #
# Stage 1: universe 演化 + 原始压缩事件
# ====================================================================== #
def stage_1_universe(cfg, out_dir):
    print("\n" + "=" * 70)
    print("[Stage 1] universe 演化")
    print("=" * 70)

    import config
    from src.compression_graph.raw_recorder import RawRecordingUniverseEnhanced
    from src.utils.individual_variation import (
        IndividualVariation, create_enhanced_individual_params,
    )

    var = IndividualVariation(config.BASE_PARAMETERS, config.VARIATION_RANGES)
    base_params = var.generate_individual("einstein_test")
    ind_params = create_enhanced_individual_params(base_params)

    # ★ 用 RawRecordingUniverseEnhanced（有 raw_compressions）
    universe = RawRecordingUniverseEnhanced(
        individual_params=ind_params,
        network_seed=cfg["network_seed"],
        num_concepts=None,
    )

    # 保险：补全 observations 里可能被父类 __init__ 覆盖掉的键
    for key in (
        'spontaneous_compressions', 'emergent_migrations',
        'traversal_patterns', 'energy_minimization_traces',
        'network_evolution_snapshots',
    ):
        universe.observations.setdefault(key, [])

    universe.initialize_semantic_network()
    print(f"  节点数：{universe.G.number_of_nodes()}  "
          f"边数：{universe.G.number_of_edges()}")

    # ★ 用 evolve_with_emergence_detection（会触发 _detect_emergence，
    #   从而填充 raw_compressions）
    universe.evolve_with_emergence_detection(
        iterations=cfg["iterations"],
        detection_interval=cfg["detection_interval"],
    )

    raw = universe.raw_compressions
    print(f"  原始压缩事件：{len(raw)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "raw_compression_events.csv"
    import pandas as pd
    rows = []
    for i, ev in enumerate(raw):
        related = ev.get("related_nodes", []) or []
        rows.append({
            "event_id": i,
            "detection_iteration": ev.get("detection_iteration", -1),
            "center": ev.get("center", ""),
            "related_nodes": "|".join(related),
            "cluster_size": len(related),
            "emergence_strength": ev.get("emergence_strength", None),
        })
    pd.DataFrame(rows).to_csv(csv_path, index=False, encoding="utf-8-sig")

    final_energy = float(universe.calculate_network_energy())
    initial_energy = (float(universe.energy_history[0])
                      if universe.energy_history else final_energy)
    summary = {
        "n_nodes": universe.G.number_of_nodes(),
        "n_edges": universe.G.number_of_edges(),
        "n_raw_events": len(raw),
        "initial_energy": initial_energy,
        "final_energy": final_energy,
        "energy_reduction_pct": (
            float((initial_energy - final_energy) / initial_energy * 100)
            if initial_energy > 0 else None
        ),
    }
    with open(out_dir / "universe_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"  能量：{initial_energy:.4f} → {final_energy:.4f}  "
          f"({summary['energy_reduction_pct']:.1f}%)")
    print(f"  [saved] {csv_path}")
    return universe, raw, summary


# ====================================================================== #
# Stage 2: 压缩关联图 G2
# ====================================================================== #
def stage_2_graph(universe, raw, out_dir):
    print("\n" + "=" * 70)
    print("[Stage 2] 压缩关联图 G2")
    print("=" * 70)

    from src.compression_graph.cg_core import UndirectedCompressionGraph

    out_dir.mkdir(parents=True, exist_ok=True)
    g = UndirectedCompressionGraph(edge_mode="clique")
    g.add_compressions(raw)
    g.build(seed_nodes=list(universe.G.nodes()))

    stats = g.stats()
    print(f"  节点 {stats['nodes']}  边 {stats['edges']}  "
          f"count_max={stats['count_max']}  count_mean={stats['count_mean']:.2f}")

    import pandas as pd
    edge_rows = []
    for u, v, d in g.G.edges(data=True):
        edge_rows.append({
            "concept_a": u, "concept_b": v,
            "count": int(d.get("count", 0)),
        })
    pd.DataFrame(edge_rows).to_csv(
        out_dir / "compression_edges.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([stats]).to_csv(
        out_dir / "summary.csv", index=False, encoding="utf-8-sig")
    print(f"  [saved] {out_dir}")
    return g


# ====================================================================== #
# Stage 3: 不动点检测（A/B/C）
# ====================================================================== #
def stage_3_fixpoints(raw, cfg, out_dir):
    print("\n" + "=" * 70)
    print("[Stage 3] 不动点检测（A/B/C）")
    print("=" * 70)

    from src.compression_graph.endo_concept.config_endo import ENDO_CONCEPT_CONFIG
    from src.compression_graph.endo_concept.fixpoint import FixpointDetector
    from src.compression_graph.endo_concept.structure import build_concept_structure
    from src.compression_graph.endo_concept.logic_derive import LogicDeriver
    from src.compression_graph.cg_core import UndirectedCompressionGraph

    out_dir.mkdir(parents=True, exist_ok=True)
    summary_rows = []

    # 建一个小图，供 structure 使用
    g = UndirectedCompressionGraph(edge_mode="clique")
    g.add_compressions(raw)
    g.build()

    for method in cfg["fixpoint_methods"]:
        print(f"\n  [method={method}]")
        fp_cfg = dict(ENDO_CONCEPT_CONFIG)
        fp_cfg["fixpoint_method"] = method
        fp_cfg["fp_min_itemset_size"] = cfg["minsize"]
        fp_cfg["lattice_min_set_size"] = cfg["minsize"]
        fp_cfg["role_min_set_size"] = cfg["minsize"]

        detector = FixpointDetector(fp_cfg)
        fps = detector.detect(raw)
        print(f"    fixpoints: {len(fps)}")

        sub_dir = out_dir / f"fixpoint_{method}"
        sub_dir.mkdir(parents=True, exist_ok=True)

        with open(sub_dir / "fixpoints.json", "w", encoding="utf-8") as f:
            json.dump(fps, f, ensure_ascii=False, indent=2, default=str)

        try:
            logic = LogicDeriver(fp_cfg).derive(fps, raw)
            structure = build_concept_structure(fps, logic, raw, g)
            with open(sub_dir / "concept_structure.json", "w", encoding="utf-8") as f:
                json.dump(structure, f, ensure_ascii=False, indent=2)
            print(f"    structures: {len(structure)}")
        except Exception as e:
            print(f"    [warn] structure build failed: {e}")

        summary_rows.append({
            "method": method,
            "n_fixpoints": len(fps),
        })

    import pandas as pd
    pd.DataFrame(summary_rows).to_csv(
        out_dir / "fixpoints_summary.csv", index=False, encoding="utf-8-sig")
    print(f"\n  [saved] {out_dir}")
    return summary_rows


# ====================================================================== #
# Stage 4: G1 能量图导出
# ====================================================================== #
def stage_4_g1(universe, out_dir):
    print("\n" + "=" * 70)
    print("[Stage 4] G1 能量图导出")
    print("=" * 70)

    import numpy as np
    import pandas as pd

    out_dir.mkdir(parents=True, exist_ok=True)
    G = universe.G

    edge_rows = []
    for u, v, d in G.edges(data=True):
        edge_rows.append({
            "concept_a": u, "concept_b": v,
            "weight": float(d["weight"]),
            "original_weight": float(d.get("original_weight", d["weight"])),
            "traversal_count": int(d.get("traversal_count", 0)),
            "similarity": float(d.get("similarity", 0.0)),
        })
    pd.DataFrame(edge_rows).to_csv(
        out_dir / "g1_edges.csv", index=False, encoding="utf-8-sig")

    nw = defaultdict(list)
    nd = defaultdict(list)
    for u, v, d in G.edges(data=True):
        w = d["weight"]
        ow = d.get("original_weight", w)
        for node in (u, v):
            nw[node].append(w)
            nd[node].append(ow - w)

    tf = Counter()
    for t in universe.traversal_history:
        path = t.get("path") if isinstance(t, dict) else None
        if path:
            for n in path:
                tf[n] += 1

    node_rows = []
    for c in set(nw.keys()) | set(tf.keys()):
        ws = nw.get(c, [])
        ds = nd.get(c, [])
        node_rows.append({
            "concept": c,
            "mean_weight": float(np.mean(ws)) if ws else None,
            "min_weight": float(np.min(ws)) if ws else None,
            "weight_drop": float(np.mean(ds)) if ds else 0.0,
            "traversal_freq": int(tf.get(c, 0)),
        })
    pd.DataFrame(node_rows).to_csv(
        out_dir / "g1_nodes.csv", index=False, encoding="utf-8-sig")

    pd.DataFrame({
        "iteration": list(range(len(universe.energy_history))),
        "energy": [float(e) for e in universe.energy_history],
    }).to_csv(out_dir / "energy_history.csv", index=False, encoding="utf-8-sig")

    pd.DataFrame([
        {"concept": c, "freq": n} for c, n in tf.most_common()
    ]).to_csv(out_dir / "traversal_freq.csv", index=False, encoding="utf-8-sig")

    print(f"  [saved] {out_dir}")
    print(f"    edges={len(edge_rows)}, nodes={len(node_rows)}, "
          f"traversals={len(universe.traversal_history)}")


# ====================================================================== #
# Stage 5: 四维概念空间
# ====================================================================== #
def stage_5_four_dim(g1_dir, raw, out_dir):
    print("\n" + "=" * 70)
    print("[Stage 5] 四维概念空间（b, c, g1, g2）")
    print("=" * 70)

    import numpy as np
    import pandas as pd
    import networkx as nx

    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- 1. 从 raw events 算 b, c ----
    n_center = Counter()
    n_member = Counter()
    total = 0
    for e in raw:
        center = e.get("center")
        if not center:
            continue
        total += 1
        n_center[center] += 1
        for m in (e.get("related_nodes") or []):
            if m and m != center:
                n_member[m] += 1

    bc = {}
    for x in set(n_center) | set(n_member):
        cc = n_center.get(x, 0)
        mc = n_member.get(x, 0)
        tot = cc + mc
        bc[x] = {
            "b": tot / max(1, total),
            "c": max(cc, mc) / tot if tot > 0 else 0.5,
        }

    # ---- 2. 从 raw events 重建 G2 算 g2 ----
    counts = Counter()
    for e in raw:
        center = e.get("center")
        if not center:
            continue
        nodes = list(dict.fromkeys(
            [center] + [m for m in (e.get("related_nodes") or []) if m]))
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                counts[tuple(sorted([nodes[i], nodes[j]]))] += 1

    G2 = nx.Graph()
    for (u, v), c in counts.items():
        G2.add_edge(u, v, count=int(c), weight=int(c))

    def _z(arr):
        arr = np.asarray(arr, dtype=float)
        m, s = arr.mean(), arr.std()
        return np.zeros_like(arr) if s == 0 else (arr - m) / s

    nodes2 = list(G2.nodes())
    wdeg = dict(G2.degree(weight="count"))
    try:
        bt = nx.betweenness_centrality(G2)
    except Exception:
        bt = {n: 0.0 for n in G2.nodes()}
    wd = np.array([wdeg.get(n, 0) for n in nodes2], dtype=float)
    bt_arr = np.array([bt.get(n, 0) for n in nodes2], dtype=float)
    g2_scores = dict(zip(nodes2, 0.6 * _z(wd) + 0.4 * _z(bt_arr)))

    # ---- 3. 从 g1_nodes 算 g1 ----
    g1_nodes = pd.read_csv(g1_dir / "g1_nodes.csv")
    for col in ("mean_weight", "weight_drop", "traversal_freq"):
        g1_nodes[col] = g1_nodes[col].fillna(g1_nodes[col].median())
    g1_arr = (
        0.40 * _z(-g1_nodes["mean_weight"].values)
        + 0.30 * _z(g1_nodes["weight_drop"].values)
        + 0.30 * _z(g1_nodes["traversal_freq"].values)
    )
    g1_scores = dict(zip(g1_nodes["concept"], g1_arr))

    # ---- 4. 拼四维表 ----
    rows = []
    for concept in set(g1_scores) | set(bc):
        rows.append({
            "concept": concept,
            "b": float(bc.get(concept, {}).get("b", 0.0)),
            "c": float(bc.get(concept, {}).get("c", 0.5)),
            "g1_z": float(g1_scores.get(concept, 0.0)),
            "g2_z": float(g2_scores.get(concept, 0.0)),
        })
    df = pd.DataFrame(rows)

    def _minmax(arr):
        lo, hi = arr.min(), arr.max()
        return np.zeros_like(arr) if hi == lo else (arr - lo) / (hi - lo)

    df["c_norm"] = (df["c"] - 0.5) * 2
    df["g1_norm"] = _minmax(df["g1_z"].values)
    df["g2_norm"] = _minmax(df["g2_z"].values)

    df.to_csv(out_dir / "four_dim.csv", index=False, encoding="utf-8-sig")

    # ---- 5. PCA ----
    X = df[["b", "c_norm", "g1_norm", "g2_norm"]].values
    Xc = X - X.mean(axis=0)
    try:
        U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
        var = (S ** 2) / ((S ** 2).sum() + 1e-12)
        pca_df = pd.DataFrame({
            "component": [f"PC{i+1}" for i in range(4)],
            "var_explained": var,
            "cumulative": np.cumsum(var),
            "b_loading": Vt[:, 0],
            "c_loading": Vt[:, 1],
            "g1_loading": Vt[:, 2],
            "g2_loading": Vt[:, 3],
        })
        pca_df.to_csv(out_dir / "pca.csv", index=False, encoding="utf-8-sig")
        print(f"  PCA: PC1={var[0]:.3f}, PC2={var[1]:.3f}, "
              f"PC1+PC2={var[0] + var[1]:.3f}")
    except Exception as e:
        print(f"  [warn] PCA failed: {e}")

    print(f"  四维向量：{len(df)} 个概念")
    print(f"  [saved] {out_dir}")
    return df


# ====================================================================== #
# Stage 6: 生成图 + 压缩/迁移检测
# ====================================================================== #
def stage_6_generative(four_dim_df, raw, fixpoints_dir, out_dir, cfg, pool):
    """
    跑单个 pool 的生成图。

    pool ∈ {"B", "C", "B_minus_C"}
    """
    print("\n" + "=" * 70)
    print(f"[Stage 6] 生成图（pool={pool}）")
    print("=" * 70)

    import math
    import random
    import pandas as pd
    import networkx as nx

    out_dir.mkdir(parents=True, exist_ok=True)

    def _load_members(method):
        p = fixpoints_dir / f"fixpoint_{method}" / "fixpoints.json"
        if not p.exists():
            return set()
        with open(p, "r", encoding="utf-8") as f:
            fps = json.load(f)
        s = set()
        for fp in fps:
            for m in fp.get("core", []):
                s.add(m)
        return s

    b_members = _load_members("B")
    c_members = _load_members("C")

    if pool == "B_minus_C":
        selected = b_members - c_members
    elif pool == "B":
        selected = b_members
    elif pool == "C":
        selected = c_members
    else:
        raise ValueError(f"Unknown pool: {pool}")

    coords = {}
    for _, row in four_dim_df.iterrows():
        coords[row["concept"]] = {
            "b": float(row["b"]),
            "c_norm": float(row["c_norm"]),
            "g1_norm": float(row["g1_norm"]),
            "g2_norm": float(row["g2_norm"]),
        }

    selected = {c: coords[c] for c in selected if c in coords}
    print(f"  B={len(b_members)}, C={len(c_members)}, pool={pool}, "
          f"selected={len(selected)}")

    if len(selected) < 2:
        print(f"  [skip] pool={pool} 少于 2 个概念，无法构图")
        return None

    # 从 raw events 提 G2 边（只保留 selected 内的）
    edge_counts = Counter()
    for e in raw:
        center = e.get("center")
        if not center:
            continue
        nodes = list(dict.fromkeys(
            [center] + [m for m in (e.get("related_nodes") or []) if m]))
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                u, v = nodes[i], nodes[j]
                if u in selected and v in selected:
                    edge_counts[tuple(sorted([u, v]))] += 1

    print(f"  G2 中 pool 内的边：{len(edge_counts)}")
    if not edge_counts:
        print(f"  [skip] pool={pool} 内无共现边")
        return None

    def _d(a, b):
        return math.sqrt(
            (a["b"] - b["b"]) ** 2
            + (a["c_norm"] - b["c_norm"]) ** 2
            + (a["g1_norm"] - b["g1_norm"]) ** 2
            + (a["g2_norm"] - b["g2_norm"]) ** 2
        )

    G = nx.Graph()
    for n, attrs in selected.items():
        G.add_node(n, **attrs)
    for (u, v), cnt in edge_counts.items():
        G.add_edge(u, v, weight=_d(selected[u], selected[v]),
                   original_weight=_d(selected[u], selected[v]),
                   count=int(cnt), traversal_count=0)

    print(f"  图：{G.number_of_nodes()} 节点，{G.number_of_edges()} 边")

    # ---- 演化 ----
    rng = random.Random(42)
    lr = cfg["gen_learning_rate"]
    fr = cfg["gen_forgetting_rate"]
    fi = cfg["gen_forget_interval"]
    wp = cfg["gen_random_walk_prob"]
    mw = cfg["gen_max_walk_length"]

    energy = []
    edges_list = list(G.edges())
    for it in range(cfg["gen_iterations"]):
        if edges_list:
            u, v = rng.choice(edges_list)
            if G.has_edge(u, v):
                cur = G[u][v]["weight"]
                G[u][v]["weight"] = max(0.01, cur * (1 - lr))
                G[u][v]["traversal_count"] += 1
        if rng.random() < wp:
            start = rng.choice(list(G.nodes()))
            path = [start]
            cur = start
            for _ in range(mw - 1):
                nbrs = [n for n in G.neighbors(cur) if n not in path]
                if not nbrs:
                    break
                nxt = rng.choice(nbrs)
                path.append(nxt)
                cur = nxt
            for i in range(len(path) - 1):
                a, b = path[i], path[i + 1]
                if G.has_edge(a, b):
                    cur_w = G[a][b]["weight"]
                    G[a][b]["weight"] = max(0.01, cur_w * (1 - lr))
                    G[a][b]["traversal_count"] += 1
        if it % fi == 0:
            for a, b, d in G.edges(data=True):
                ow = d.get("original_weight", d["weight"])
                d["weight"] = d["weight"] + (ow - d["weight"]) * fr
        if G.number_of_edges() > 0:
            avg = sum(d["weight"] for _, _, d in G.edges(data=True)) / G.number_of_edges()
            energy.append(avg)

    print(f"  能量（距离）：{energy[0]:.4f} → {energy[-1]:.4f}  "
          f"({(energy[0] - energy[-1]) / energy[0] * 100:.1f}%)")

    # ---- 压缩 ----
    def _phi(cluster):
        S = set(cluster)
        internal, external = [], []
        for u in S:
            if u not in G:
                continue
            for v in G.neighbors(u):
                w = G[u][v]["weight"]
                if v in S:
                    if u < v:
                        internal.append(w)
                else:
                    external.append(w)
        if not internal or not external:
            return None
        ai = sum(internal) / len(internal)
        ae = sum(external) / len(external)
        return ae / ai if ai > 1e-9 else None

    comps = []
    for center in G.nodes():
        nbrs = sorted(G.neighbors(center), key=lambda n: G[center][n]["weight"])
        for k in range(cfg["min_cluster_size"],
                       min(cfg["max_cluster_size"], len(nbrs)) + 1):
            cluster = [center] + nbrs[:k]
            phi = _phi(cluster)
            if phi is not None and phi >= cfg["compression_phi_threshold"]:
                comps.append({
                    "center": center,
                    "cluster": "|".join(cluster),
                    "size": len(cluster),
                    "phi": float(phi),
                })
    comps.sort(key=lambda x: x["phi"], reverse=True)

    # ---- 迁移 ----
    migs = []
    eps = cfg["migration_epsilon"]
    nodes = list(G.nodes())
    for a in nodes:
        for b in nodes:
            if a >= b or not G.has_edge(a, b):
                continue
            direct = G[a][b]["weight"]
            if direct <= 1e-9:
                continue
            for z in nodes:
                if z in (a, b):
                    continue
                if not (G.has_edge(a, z) and G.has_edge(z, b)):
                    continue
                pd_ = G[a][z]["weight"] + G[z][b]["weight"]
                if pd_ < direct * (1 - eps):
                    migs.append({
                        "start": a, "via": z, "end": b,
                        "direct_distance": float(direct),
                        "path_distance": float(pd_),
                        "improvement": float((direct - pd_) / direct),
                    })
    migs.sort(key=lambda x: x["improvement"], reverse=True)

    print(f"  压缩候选：{len(comps)}  迁移候选：{len(migs)}")

    # ---- 保存 ----
    node_rows = []
    for n, d in G.nodes(data=True):
        node_rows.append({"concept": n, **{
            k: d[k] for k in ("b", "c_norm", "g1_norm", "g2_norm") if k in d
        }})
    pd.DataFrame(node_rows).to_csv(
        out_dir / "graph_nodes.csv", index=False, encoding="utf-8-sig")

    edge_rows = []
    for u, v, d in G.edges(data=True):
        edge_rows.append({
            "concept_a": u, "concept_b": v,
            "weight": float(d["weight"]),
            "original_weight": float(d["original_weight"]),
            "count": int(d["count"]),
            "traversal_count": int(d["traversal_count"]),
        })
    pd.DataFrame(edge_rows).to_csv(
        out_dir / "graph_edges.csv", index=False, encoding="utf-8-sig")

    if comps:
        pd.DataFrame(comps).to_csv(
            out_dir / "candidate_compressions.csv",
            index=False, encoding="utf-8-sig")
    if migs:
        pd.DataFrame(migs).to_csv(
            out_dir / "candidate_migrations.csv",
            index=False, encoding="utf-8-sig")

    info = {
        "pool": pool,
        "n_B": len(b_members),
        "n_C": len(c_members),
        "n_selected": len(selected),
        "n_graph_nodes": G.number_of_nodes(),
        "n_graph_edges": G.number_of_edges(),
        "initial_distance": float(energy[0]),
        "final_distance": float(energy[-1]),
        "n_compressions": len(comps),
        "n_migrations": len(migs),
    }
    with open(out_dir / "info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    print(f"  [saved] {out_dir}")
    return G, comps, migs, info

# ====================================================================== #
# 主流程
# ====================================================================== #
def main():
    from config_einstein import EINSTEIN_CONFIG

    cfg = EINSTEIN_CONFIG
    out_root = _PROJ / cfg["output_root"]
    out_root.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("爱因斯坦测试")
    print("=" * 70)

    n_concepts = setup_einstein_concepts()
    print(f"概念集：{n_concepts} 个")

    universe, raw, universe_summary = stage_1_universe(
        cfg, out_root / "stage1_universe")

    g2 = stage_2_graph(universe, raw, out_root / "stage2_graph")

    fp_summary = stage_3_fixpoints(raw, cfg, out_root / "stage3_fixpoints")

    stage_4_g1(universe, out_root / "stage4_g1")

    four_dim = stage_5_four_dim(
        out_root / "stage4_g1", raw, out_root / "stage5_four_dim")

    # ★ 循环跑三种 pool
    gen_results = {}
    for pool in cfg["concept_pools"]:
        result = stage_6_generative(
            four_dim, raw,
            out_root / "stage3_fixpoints",
            out_root / "stage6_generative" / pool,
            cfg,
            pool,
        )
        gen_results[pool] = result[3] if result else None

    final = {
        "n_concepts": n_concepts,
        "universe": universe_summary,
        "fixpoints": fp_summary,
        "generative": gen_results,
    }
    with open(out_root / "einstein_test_summary.json", "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"完成。输出：{out_root}")
    print("=" * 70)

    # 打印三种 pool 的对比
    print("\n三种 pool 的生成图对比：")
    for pool, info in gen_results.items():
        if info is None:
            print(f"  [{pool:12s}] 无法构图（概念太少或无共现边）")
        else:
            print(f"  [{pool:12s}] {info['n_graph_nodes']} 节点，"
                  f"{info['n_graph_edges']} 边，"
                  f"压缩 {info['n_compressions']}，"
                  f"迁移 {info['n_migrations']}")

if __name__ == "__main__":
    main()