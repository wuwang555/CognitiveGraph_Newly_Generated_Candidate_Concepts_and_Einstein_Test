# -*- coding: utf-8 -*-
"""从 ReflectedUniverse 导出事件 → G2 → 不动点 → 四维 → 生成图 → 压缩/迁移。

中层逻辑与主仓库保持一致：
  - G2        : cg_core.UndirectedCompressionGraph（clique）
  - 不动点     : endo_concept.fixpoint.FixpointDetector（B / C，use_joint_criteria=False）
  - 四维坐标   : continuous_vector.process_one 的等价公式
  - 生成图     : build_graph.build_bc_graph 的等价逻辑
  - 演化       : generative_graph.evolve.evolve
  - 压缩/迁移  : generative_graph.detect.detect_compression / detect_migration（严格复制）
"""

import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parents[1]
for _p in (str(_HERE), str(_PROJ)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pandas as pd
import networkx as nx


def _resolve(p):
    p = Path(p)
    return p if p.is_absolute() else (_PROJ / p)


def _z(arr):
    arr = np.asarray(arr, dtype=float)
    m, s = arr.mean(), arr.std()
    return np.zeros_like(arr) if (s == 0 or np.isnan(s)) else (arr - m) / s


def _minmax(arr):
    arr = np.asarray(arr, dtype=float)
    lo, hi = arr.min(), arr.max()
    return np.zeros_like(arr) if (hi - lo == 0) else (arr - lo) / (hi - lo)


# ====================================================================== #
# 1. 导出事件
# ====================================================================== #
def export_universe_events(universe, out_dir):
    out_dir = _resolve(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for i, c in enumerate(universe.raw_compressions):
        rows.append({
            "scale": universe.G.number_of_nodes(),
            "event_id": i,
            "detection_iteration": c.get("detection_iteration", -1),
            "center": c.get("center", ""),
            "cluster_size": len(c.get("related_nodes", []) or []),
            "related_nodes": "|".join(c.get("related_nodes", []) or []),
            "emergence_strength": c.get("emergence_strength", None),
        })
    columns = ["scale", "event_id", "detection_iteration",
               "center", "cluster_size", "related_nodes",
               "emergence_strength"]
    df = pd.DataFrame(rows, columns=columns)
    path = out_dir / "raw_compression_events.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  [export] {path}  rows={len(df)}")
    return path


def _events_from_universe(universe):
    out = []
    for i, c in enumerate(universe.raw_compressions):
        out.append({
            "event_id": i,
            "detection_iteration": c.get("detection_iteration", -1),
            "center": c.get("center", ""),
            "related_nodes": list(c.get("related_nodes", []) or []),
        })
    return out


# ====================================================================== #
# 2. G2：与 cg_core.UndirectedCompressionGraph(clique) 一致
# ====================================================================== #
def build_g2(events):
    G = nx.Graph()
    counts = Counter()
    for e in events:
        center = e.get("center")
        if not center:
            continue
        rel = [m for m in e.get("related_nodes", []) if m and m != center]
        nodes = list(dict.fromkeys([center] + rel))
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                counts[tuple(sorted([nodes[i], nodes[j]]))] += 1
    for (u, v), c in counts.items():
        G.add_edge(u, v, count=int(c), weight=int(c))
    return G


# ====================================================================== #
# 3. 不动点：直接引用 FixpointDetector，use_joint_criteria=False
# ====================================================================== #
def detect_fixpoint_members(events, cfg):
    from src.compression_graph.endo_concept.fixpoint import FixpointDetector

    base = {
        "fp_min_itemset_size": int(cfg.get("minsize", 1)),
        "fp_max_itemset_size": int(cfg.get("fp_max_itemset_size", 8)),
        "fp_min_support": float(cfg.get("fp_min_support", 0.02)),
        "lattice_min_support": float(cfg.get("lattice_min_support", 0.02)),
        "lattice_min_set_size": int(cfg.get("lattice_min_set_size", 1)),
        "lattice_max_itemset_size": int(cfg.get("lattice_max_itemset_size", 8)),
        "role_min_stability": float(cfg.get("role_min_stability", 0.7)),
        "role_min_support": float(cfg.get("role_min_support", 0.005)),
        "role_min_set_size": int(cfg.get("role_min_set_size", 1)),
        "role_max_itemset_size": int(cfg.get("role_max_itemset_size", 8)),
        "max_candidates": int(cfg.get("max_candidates", 200000)),
        "max_fixpoints": int(cfg.get("max_fixpoints", 1000)),
        # ★ 恢复 joint criteria：C 的 size>1 项集会被 lower-bound 过滤，
        #   只留 size=1 的 role-consistent 项集；B 本来就是 lower-bound，无影响。
        "use_joint_criteria": bool(cfg.get("use_joint_criteria", True)),
        "joint_support_min": float(cfg.get("joint_support_min", 0.02)),
        "joint_stability_min": float(cfg.get("joint_stability_min", 0.6)),
        "use_stability_hard_threshold": bool(cfg.get("use_stability_hard_threshold", False)),
        "use_lower_bound_filter": bool(cfg.get("use_lower_bound_filter", True)),
    }

    b_cfg = dict(base); b_cfg["fixpoint_method"] = "B"
    c_cfg = dict(base); c_cfg["fixpoint_method"] = "C"
    b_fps = FixpointDetector(b_cfg).detect(events)
    c_fps = FixpointDetector(c_cfg).detect(events)

    b_members = set()
    for fp in b_fps:
        for m in fp.get("core", []):
            b_members.add(m)
    c_members = set()
    for fp in c_fps:
        for m in fp.get("core", []):
            c_members.add(m)

    method = str(cfg.get("fixpoint_method", "B"))
    if method == "B":
        selected = b_members
    elif method == "C":
        selected = c_members
    elif method == "B_minus_C":
        selected = b_members - c_members
    else:
        raise ValueError(f"Unknown fixpoint_method: {method}")

    print(f"  [fixpoints] B={len(b_members)}  C={len(c_members)}  "
          f"selected({method})={len(selected)}  "
          f"(n_B_fps={len(b_fps)}, n_C_fps={len(c_fps)})")
    return selected, b_members, c_members, len(b_fps), len(c_fps)

# ====================================================================== #
# 4. 四维坐标：与 continuous_vector.process_one 一致
# ====================================================================== #
def _bc_from_events(events):
    n_center = Counter()
    n_member = Counter()
    total = 0
    for e in events:
        center = e.get("center")
        if not center:
            continue
        total += 1
        n_center[center] += 1
        for m in e.get("related_nodes", []):
            if m and m != center:
                n_member[m] += 1

    out = {}
    for x in set(n_center) | set(n_member):
        c_n = n_center.get(x, 0)
        m_n = n_member.get(x, 0)
        t = c_n + m_n
        if t <= 0:
            continue
        out[x] = {
            "b": t / max(1, total),
            "c": max(c_n, m_n) / t,
        }
    return out


def _g1_from_universe(universe):
    G = universe.G
    if G.number_of_nodes() == 0:
        return {}

    mean_w = {}
    weight_drop = {}
    for n in G.nodes():
        ws, drops = [], []
        for nb in G.neighbors(n):
            d = G[n][nb]
            w = float(d.get("weight", 0.0))
            ow = float(d.get("original_weight", w))
            ws.append(w)
            drops.append(ow - w)
        mean_w[n] = float(np.mean(ws)) if ws else 0.0
        weight_drop[n] = float(np.mean(drops)) if drops else 0.0

    traversal_freq = Counter()
    for entry in universe.traversal_history:
        path = entry.get("path", []) if isinstance(entry, dict) else []
        for n in path:
            traversal_freq[n] += 1

    nodes = list(G.nodes())
    mw = np.array([mean_w[n] for n in nodes], dtype=float)
    dp = np.array([weight_drop[n] for n in nodes], dtype=float)
    tf = np.array([traversal_freq.get(n, 0) for n in nodes], dtype=float)
    score = 0.4 * _z(-mw) + 0.3 * _z(dp) + 0.3 * _z(tf)
    return dict(zip(nodes, score))


def _g2_scores(G2):
    if G2.number_of_nodes() == 0:
        return {}
    wdeg = dict(G2.degree(weight="count"))
    try:
        bt = nx.betweenness_centrality(G2)
    except Exception:
        bt = {n: 0.0 for n in G2.nodes()}
    nodes = list(G2.nodes())
    wd = np.array([wdeg.get(n, 0) for n in nodes], dtype=float)
    btc = np.array([bt.get(n, 0) for n in nodes], dtype=float)
    score = 0.6 * _z(wd) + 0.4 * _z(btc)
    return dict(zip(nodes, score))


def compute_4d_coords(universe, events, G2):
    bc = _bc_from_events(events)
    g1 = _g1_from_universe(universe)
    g2 = _g2_scores(G2)

    rows = []
    for x in set(bc) | set(g1):
        b = float(bc.get(x, {}).get("b", 0.0))
        c_raw = float(bc.get(x, {}).get("c", 0.5))
        rows.append({
            "concept": x,
            "b": b,
            "c": c_raw,
            "g1_z": float(g1.get(x, 0.0)),
            "g2_z": float(g2.get(x, 0.0)),
        })
    if not rows:
        return {}
    df = pd.DataFrame(rows)
    df["c_norm"] = (df["c"] - 0.5) * 2.0
    df["g1_norm"] = _minmax(df["g1_z"].values)
    df["g2_norm"] = _minmax(df["g2_z"].values)
    out = {}
    for _, r in df.iterrows():
        out[r["concept"]] = {
            "b": float(r["b"]),
            "c": float(r["c"]),
            "g1_z": float(r["g1_z"]),
            "g2_z": float(r["g2_z"]),
            "c_norm": float(r["c_norm"]),
            "g1_norm": float(r["g1_norm"]),
            "g2_norm": float(r["g2_norm"]),
        }
    return out


def _euclidean_4d(a, b, use_norm=True):
    keys = (["b", "c_norm", "g1_norm", "g2_norm"] if use_norm
            else ["b", "c", "g1_z", "g2_z"])
    s = 0.0
    for k in keys:
        s += (float(a[k]) - float(b[k])) ** 2
    return math.sqrt(s)


# ====================================================================== #
# 5. 生成图：与 build_graph.build_bc_graph 一致
# ====================================================================== #
def build_generative_graph(selected_nodes, coords, G2, use_norm=True):
    nodes = {c: coords[c] for c in selected_nodes if c in coords}
    if len(nodes) < 2:
        return None

    G = nx.Graph()
    for n, a in nodes.items():
        G.add_node(n, **a)

    for u, v, d in G2.edges(data=True):
        if u in nodes and v in nodes:
            dd = _euclidean_4d(nodes[u], nodes[v], use_norm=use_norm)
            G.add_edge(u, v, weight=dd, original_weight=dd,
                       count=int(d.get("count", 0)))

    print(f"  [gen_graph] nodes={G.number_of_nodes()}  edges={G.number_of_edges()}")
    return G


# ====================================================================== #
# 6. 演化：与 evolve.evolve 一致
# ====================================================================== #
def _random_walk(G, start, max_steps, visited=None):
    if visited is None:
        visited = {start}
    path = [start]
    current = start
    for _ in range(max_steps - 1):
        nbrs = [n for n in G.neighbors(current) if n not in visited]
        if not nbrs:
            break
        nxt = random.choice(nbrs)
        path.append(nxt)
        visited.add(nxt)
        current = nxt
    return path


def evolve(G, cfg):
    rng = random.Random(cfg["random_seed"])
    iterations = cfg["iterations"]
    lr = cfg["learning_rate"]
    fr = cfg["forgetting_rate"]
    forget_interval = cfg["forget_interval"]
    walk_prob = cfg["random_walk_prob"]
    max_walk = cfg["max_walk_length"]

    for u, v, d in G.edges(data=True):
        d["original_weight"] = d.get("original_weight", d["weight"])
        d["traversal_count"] = d.get("traversal_count", 0)

    energy_history = []
    traversal_history = []
    edges = list(G.edges())
    if not edges:
        return energy_history, traversal_history

    for it in range(iterations):
        u, v = rng.choice(edges)
        if G.has_edge(u, v):
            cur = G[u][v]["weight"]
            G[u][v]["weight"] = max(0.01, cur * (1 - lr))
            G[u][v]["traversal_count"] = G[u][v].get("traversal_count", 0) + 1

        if rng.random() < walk_prob:
            start = rng.choice(list(G.nodes()))
            path = _random_walk(G, start, max_walk, visited={start})
            if len(path) >= 2:
                traversal_history.append(path)
                for i in range(len(path) - 1):
                    a, b = path[i], path[i + 1]
                    if G.has_edge(a, b):
                        cur = G[a][b]["weight"]
                        G[a][b]["weight"] = max(0.01, cur * (1 - lr))
                        G[a][b]["traversal_count"] = G[a][b].get("traversal_count", 0) + 1

        if it % forget_interval == 0:
            for a, b, d in G.edges(data=True):
                orig = d.get("original_weight", d["weight"])
                d["weight"] = d["weight"] + (orig - d["weight"]) * fr

        if G.number_of_edges() > 0:
            avg = sum(d["weight"] for _, _, d in G.edges(data=True)) / G.number_of_edges()
            energy_history.append(avg)

    return energy_history, traversal_history


# ====================================================================== #
# 7. 压缩/迁移检测：严格按 detect.py 复制
# ====================================================================== #
def _compression_potential(G, cluster):
    """Φ = 外部平均距离 / 内部平均距离。"""
    S = set(cluster)
    internal = []
    external = []
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
    avg_in = sum(internal) / len(internal)
    avg_ex = sum(external) / len(external)
    if avg_in <= 1e-9:
        return None
    return avg_ex / avg_in


def detect_compression(G, cfg):
    """与 detect.detect_compression 一致：for k in range(min_k, max_here+1)。"""
    min_k = int(cfg["min_cluster_size"])
    max_k = int(cfg["max_cluster_size"])
    threshold = float(cfg["compression_phi_threshold"])

    candidates = []
    for center in G.nodes():
        nbrs = list(G.neighbors(center))
        if len(nbrs) < min_k:
            continue
        # 按距离升序
        nbrs.sort(key=lambda n: G[center][n]["weight"])
        max_here = min(max_k, len(nbrs))
        for k in range(min_k, max_here + 1):
            cluster = [center] + nbrs[:k]
            phi = _compression_potential(G, cluster)
            if phi is None or phi < threshold:
                continue
            candidates.append({
                "center": center,
                "cluster": list(cluster),
                "size": len(cluster),
                "phi": float(phi),
            })
    candidates.sort(key=lambda x: x["phi"], reverse=True)
    return candidates


def detect_migration(G, cfg):
    """与 detect.detect_migration 一致：每个 (a,b,z) 组合都记录。"""
    epsilon = float(cfg["migration_epsilon"])
    nodes = list(G.nodes())

    migrations = []
    for a in nodes:
        for b in nodes:
            if a >= b:
                continue
            if not G.has_edge(a, b):
                continue
            direct = G[a][b]["weight"]
            if direct <= 1e-9:
                continue

            for z in nodes:
                if z == a or z == b:
                    continue
                if not G.has_edge(a, z) or not G.has_edge(z, b):
                    continue
                path_dist = G[a][z]["weight"] + G[z][b]["weight"]
                if path_dist < direct * (1 - epsilon):
                    migrations.append({
                        "start": a,
                        "via": z,
                        "end": b,
                        "direct_distance": float(direct),
                        "path_distance": float(path_dist),
                        "improvement": float((direct - path_dist) / direct),
                    })

    migrations.sort(key=lambda x: x["improvement"], reverse=True)
    return migrations


# ====================================================================== #
# 8. 主入口
# ====================================================================== #
def run_pipeline(universe, out_dir, cfg):
    out_dir = _resolve(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"  [pipeline] raw_compressions = {len(universe.raw_compressions)}")
    print(f"  [pipeline] raw_migrations   = {len(universe.raw_migrations)}")

    if not universe.raw_compressions:
        print("  [pipeline] WARNING: 0 events")
        g3 = {"clusters": [], "migrations": [],
              "n_nodes": 0, "n_edges": 0,
              "g2_nodes": 0, "g2_edges": 0,
              "n_b_members": 0, "n_c_members": 0, "n_selected": 0,
              "n_b_fps": 0, "n_c_fps": 0,
              "fixpoint_method": str(cfg.get("fixpoint_method", "B"))}
        with open(out_dir / "g3_result.json", "w", encoding="utf-8") as f:
            json.dump(g3, f, ensure_ascii=False, indent=2)
        return g3

    events_csv = export_universe_events(universe, out_dir)
    events = _events_from_universe(universe)

    # 1. G2
    G2 = build_g2(events)
    print(f"  [G2] nodes={G2.number_of_nodes()}  edges={G2.number_of_edges()}")

    # 2. 不动点
    selected, b_mem, c_mem, n_b_fps, n_c_fps = detect_fixpoint_members(events, cfg)

    # 3. 四维
    coords = compute_4d_coords(universe, events, G2)
    print(f"  [4d] concepts={len(coords)}")

    # 4. 生成图
    G = build_generative_graph(
        selected, coords, G2,
        use_norm=bool(cfg.get("use_normalized_4d", True)),
    )

    if G is None or G.number_of_edges() == 0:
        print("  [pipeline] WARNING: empty generative graph")
        g3 = {"clusters": [], "migrations": [],
              "n_nodes": G.number_of_nodes() if G else 0,
              "n_edges": 0,
              "g2_nodes": G2.number_of_nodes(),
              "g2_edges": G2.number_of_edges(),
              "n_b_members": len(b_mem),
              "n_c_members": len(c_mem),
              "n_selected": len(selected),
              "n_b_fps": n_b_fps,
              "n_c_fps": n_c_fps,
              "fixpoint_method": str(cfg.get("fixpoint_method", "B"))}
        with open(out_dir / "g3_result.json", "w", encoding="utf-8") as f:
            json.dump(g3, f, ensure_ascii=False, indent=2)
        return g3

    # 5. 演化
    gen_cfg = {
        "iterations": int(cfg.get("gen_iterations", 3000)),
        "learning_rate": float(cfg.get("gen_learning_rate", 0.1)),
        "forgetting_rate": float(cfg.get("gen_forgetting_rate", 0.002)),
        "forget_interval": int(cfg.get("gen_forget_interval", 10)),
        "random_walk_prob": float(cfg.get("gen_random_walk_prob", 0.3)),
        "max_walk_length": int(cfg.get("gen_max_walk_length", 4)),
        "random_seed": int(cfg.get("random_seed", 42)),
    }
    evolve(G, gen_cfg)

    # 6. 压缩/迁移（严格按 detect.py）
    det_cfg = {
        "compression_phi_threshold": float(cfg.get("gen_compression_phi_threshold", 1.5)),
        "min_cluster_size": int(cfg.get("gen_min_cluster_size", 3)),
        "max_cluster_size": int(cfg.get("gen_max_cluster_size", 8)),
        "migration_epsilon": float(cfg.get("gen_migration_epsilon", 0.1)),
    }
    clusters = detect_compression(G, det_cfg)
    migrations = detect_migration(G, det_cfg)
    print(f"  [detect] clusters={len(clusters)}  migrations={len(migrations)}")

    # 7. 保存
    g3 = {
        "clusters": clusters,
        "migrations": migrations,
        "n_nodes": int(G.number_of_nodes()),
        "n_edges": int(G.number_of_edges()),
        "g2_nodes": int(G2.number_of_nodes()),
        "g2_edges": int(G2.number_of_edges()),
        "fixpoint_method": str(cfg.get("fixpoint_method", "B")),
        "n_b_members": len(b_mem),
        "n_c_members": len(c_mem),
        "n_selected": len(selected),
        "n_b_fps": n_b_fps,
        "n_c_fps": n_c_fps,
    }
    with open(out_dir / "g3_result.json", "w", encoding="utf-8") as f:
        json.dump(g3, f, ensure_ascii=False, indent=2, default=str)

    with open(out_dir / "fixpoints_selected.json", "w", encoding="utf-8") as f:
        json.dump({
            "method": str(cfg.get("fixpoint_method", "B")),
            "selected": sorted(selected),
            "b_members": sorted(b_mem),
            "c_members": sorted(c_mem),
        }, f, ensure_ascii=False, indent=2)

    print(f"  [pipeline] saved {out_dir / 'g3_result.json'}")
    return g3