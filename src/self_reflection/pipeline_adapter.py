# -*- coding: utf-8 -*-
"""从 ReflectedUniverse 导出事件 → G2 → 不动点 → 四维 → 生成图 → 压缩/迁移。

所有中层逻辑在此复制，和主仓库对应文件保持一致：
  - G2            : 与 src/compression_graph/cg_core.py 一致
  - 不动点         : 与 src/compression_graph/endo_concept/fixpoint.py 的 A/B/C 一致
  - 四维坐标       : 与 src/compression_graph/endo_concept/continuous_vector.py 一致
  - 生成图         : 与 src/generative_graph/build_graph.py 一致
  - 演化           : 与 src/generative_graph/evolve.py 一致
  - 压缩/迁移检测   : 与 src/generative_graph/detect.py 一致

不 import 上述文件，避免模块级 argparse / 文件系统依赖。
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
# 1. 导出事件（唯一一次写 raw_compression_events.csv）
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


def _events_from_csv(csv_path):
    df = pd.read_csv(csv_path)
    out = []
    for _, row in df.iterrows():
        rel_raw = row.get("related_nodes", "")
        rel = [] if pd.isna(rel_raw) else [
            x.strip() for x in str(rel_raw).split("|") if x.strip()
        ]
        out.append({
            "event_id": int(row.get("event_id", len(out))),
            "detection_iteration": int(row.get("detection_iteration", -1)),
            "center": str(row.get("center", "")),
            "related_nodes": rel,
        })
    return out


# ====================================================================== #
# 2. G2：与 cg_core.UndirectedCompressionGraph 一致（clique）
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
# 3. 不动点：与 fixpoint.FixpointDetector 的 A/B/C 一致
# ====================================================================== #
class _FixpointDetector:
    """精简版 FixpointDetector，只保留 B 和 C 的过滤语义。

    与 src/compression_graph/endo_concept/fixpoint.py 对应方法一致：
      B: powerset 枚举 + support + 下界过滤
      C: B 的基础上加角色一致性
    """

    def __init__(self, cfg):
        self.cfg = cfg

    @staticmethod
    def _events_to_transactions(events):
        out = []
        for e in events:
            center = e.get("center")
            if not center:
                continue
            members = e.get("related_nodes") or []
            txn = frozenset([center] + [m for m in members if m and m != center])
            if len(txn) >= 1:
                out.append(txn)
        return out

    @staticmethod
    def _stability_scores(events):
        n_center = Counter()
        n_member = Counter()
        for e in events:
            center = e.get("center")
            members = e.get("related_nodes") or []
            if center:
                n_center[center] += 1
            for m in members:
                if m and m != center:
                    n_member[m] += 1

        out = {}
        for concept in set(n_center) | set(n_member):
            c = n_center.get(concept, 0)
            m = n_member.get(concept, 0)
            total = c + m
            if total <= 0:
                continue
            out[concept] = max(c, m) / total
        return out

    @staticmethod
    def _enumerate_powerset(events, min_size, max_size, max_candidates):
        transactions = _FixpointDetector._events_to_transactions(events)
        N = len(transactions)
        if N == 0:
            return Counter(), 0

        counter = Counter()
        lower = max(1, int(min_size))
        upper = max(lower, int(max_size))

        from itertools import combinations
        for t in transactions:
            items = list(t)
            n = len(items)
            top = min(upper, n)
            for size in range(lower, top + 1):
                for combo in combinations(items, size):
                    counter[frozenset(combo)] += 1
            if len(counter) > max_candidates:
                break
        return counter, N

    @staticmethod
    def _is_lower_bound(s, frequent_set):
        from itertools import combinations
        if len(s) <= 1:
            return True
        for sub in combinations(s, len(s) - 1):
            if frozenset(sub) in frequent_set:
                return False
        return True

    def method_B(self, events):
        cfg = self.cfg
        min_size = int(cfg.get("lattice_min_set_size", 1))
        max_size = int(cfg.get("lattice_max_itemset_size", 8))
        min_support = float(cfg.get("lattice_min_support", 0.02))
        max_cand = int(cfg.get("max_candidates", 200000))
        max_fp = int(cfg.get("max_fixpoints", 1000))

        counter, N = self._enumerate_powerset(events, min_size, max_size, max_cand)
        if N == 0:
            return []
        min_count = max(1, int(math.ceil(min_support * N)))
        stab = self._stability_scores(events)

        frequent = {s: cnt for s, cnt in counter.items() if cnt >= min_count}
        frequent_set = set(frequent.keys())

        out = []
        for s, cnt in frequent.items():
            if not self._is_lower_bound(s, frequent_set):
                continue
            members = sorted(s)
            mean_stab = float(np.mean([stab.get(m, 0.5) for m in members]))
            out.append({
                "core": members,
                "support": cnt / N,
                "count": cnt,
                "stability": mean_stab,
                "method": "B",
            })
        out.sort(key=lambda r: (r["support"], len(r["core"])), reverse=True)
        return out[:max_fp]

    def method_C(self, events):
        cfg = self.cfg
        min_size = int(cfg.get("role_min_set_size", 1))
        max_size = int(cfg.get("role_max_itemset_size", 8))
        min_stability = float(cfg.get("role_min_stability", 0.7))
        min_support = float(cfg.get("role_min_support", 0.005))
        max_cand = int(cfg.get("max_candidates", 200000))
        max_fp = int(cfg.get("max_fixpoints", 1000))

        counter, N = self._enumerate_powerset(events, min_size, max_size, max_cand)
        if N == 0:
            return []
        min_count = max(1, int(math.ceil(min_support * N)))
        stab = self._stability_scores(events)

        out = []
        for itemset, cnt in counter.items():
            if cnt < min_count:
                continue
            members = sorted(itemset)
            mean_stab = float(np.mean([stab.get(m, 0.5) for m in members]))
            if mean_stab < min_stability:
                continue
            out.append({
                "core": members,
                "support": cnt / N,
                "count": cnt,
                "stability": mean_stab,
                "method": "C",
            })
        out.sort(key=lambda r: (r["stability"], r["support"]), reverse=True)
        return out[:max_fp]


def detect_fixpoint_members(events, cfg):
    det = _FixpointDetector(cfg)
    b_fps = det.method_B(events)
    c_fps = det.method_C(events)

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
          f"selected({method})={len(selected)}")
    return selected, b_members, c_members


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
    """与 g1_exporter + continuous_vector.compute_g1_scores 一致。

    g1_nodes.csv 的字段: mean_weight, min_weight, weight_drop, traversal_freq。
    compute_g1_scores 的公式: 0.4*z(-mean_weight) + 0.3*z(weight_drop) + 0.3*z(traversal_freq)。
    """
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
    """与 continuous_vector.compute_g2_scores 一致：
    0.6*z(weighted_degree) + 0.4*z(betweenness)。
    """
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
# 7. 压缩/迁移检测：与 detect.detect_compression / detect_migration 一致
# --------------------------------------------------------------------- #
# 压缩：对每个节点作为中心，取邻居中 weight 低于阈值且相似度 > 0.4 的，
# 若 >=3 个则构成簇，计算 phi = 内部平均 / 外部平均。
# 与主仓库 detect.py 的行为一致（不去重、center 不同即视为不同候选）。
# ====================================================================== #
def _compute_phi(G, cluster):
    S = set(cluster)
    internal, external = [], []
    seen = set()
    for u in S:
        if u not in G:
            continue
        for v in G.neighbors(u):
            key = tuple(sorted((u, v)))
            if key in seen:
                continue
            seen.add(key)
            c = float(G[u][v].get("count", 1))
            if v in S:
                internal.append(c)
            else:
                external.append(c)
    if not internal or not external:
        return None
    avg_in = sum(internal) / len(internal)
    avg_ex = sum(external) / len(external)
    if avg_ex == 0:
        return None
    return avg_in / avg_ex


def detect_compression(G, cfg):
    """与主仓库 detect_compression 一致：遍历每个节点作为中心，产出候选。

    一个 k 元簇最多出现 k 次（每个成员作为 center 各一次），
    不去重，因为 center 不同即边界不同。
    """
    min_size = int(cfg.get("min_cluster_size", 3))
    max_size = int(cfg.get("max_cluster_size", 8))
    phi_thr = float(cfg.get("compression_phi_threshold", 1.5))

    clusters = []
    for center in G.nodes():
        nbrs = list(G.neighbors(center))
        if len(nbrs) < min_size - 1:
            continue
        # 按 weight 升序取邻居（低权重优先）
        nbrs_sorted = sorted(nbrs, key=lambda n: G[center][n]["weight"])
        take = nbrs_sorted[: max_size - 1]
        cluster = [center] + take
        if len(cluster) < min_size:
            continue
        phi = _compute_phi(G, cluster)
        if phi is None or phi < phi_thr:
            continue
        clusters.append({
            "center": center,
            "cluster": list(cluster),
            "size": len(cluster),
            "phi": float(phi),
        })

    clusters.sort(key=lambda c: c["phi"], reverse=True)
    return clusters


def _path_improvement(G, path):
    if len(path) < 2:
        return 0.0
    u, v = path[0], path[-1]
    if not G.has_edge(u, v):
        return 0.0
    direct = float(G[u][v]["weight"])
    if direct <= 0:
        return 0.0
    path_sum = 0.0
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        if not G.has_edge(a, b):
            return 0.0
        path_sum += float(G[a][b]["weight"])
    return max(0.0, (direct - path_sum) / direct)


def detect_migration(G, cfg):
    """与主仓库 detect_migration 一致：对每个节点对，找 via 节点，
    若 path 距离 < direct * (1 - epsilon) 则记为迁移候选。

    主仓库的实现基于遍历历史；这里用全节点对 × 全节点 via 的穷举，
    结果集合一致，只是计算顺序不同。
    """
    eps = float(cfg.get("migration_epsilon", 0.1))
    nodes = list(G.nodes())
    migrations = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = nodes[i], nodes[j]
            if not G.has_edge(a, b):
                continue
            direct = float(G[a][b]["weight"])
            if direct <= 0:
                continue
            # 找 via
            best = None
            for v in nodes:
                if v == a or v == b:
                    continue
                if not (G.has_edge(a, v) and G.has_edge(v, b)):
                    continue
                path_sum = float(G[a][v]["weight"]) + float(G[v][b]["weight"])
                imp = (direct - path_sum) / direct
                if imp < eps:
                    continue
                if best is None or imp > best["improvement"]:
                    best = {
                        "start": a, "via": v, "end": b,
                        "direct_distance": direct,
                        "path_distance": path_sum,
                        "improvement": float(imp),
                    }
            if best is not None:
                migrations.append(best)

    migrations.sort(key=lambda m: m["improvement"], reverse=True)
    return migrations


# ====================================================================== #
# 8. 主入口
# ====================================================================== #
def run_pipeline(universe, out_dir, cfg):
    out_dir = _resolve(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"  [pipeline] raw_compressions = {len(universe.raw_compressions)}")
    if not universe.raw_compressions:
        print("  [pipeline] WARNING: 0 events")
        g3 = {"clusters": [], "migrations": [],
              "n_nodes": 0, "n_edges": 0,
              "g2_nodes": 0, "g2_edges": 0,
              "n_b_members": 0, "n_c_members": 0, "n_selected": 0,
              "fixpoint_method": str(cfg.get("fixpoint_method", "B"))}
        with open(out_dir / "g3_result.json", "w", encoding="utf-8") as f:
            json.dump(g3, f, ensure_ascii=False, indent=2)
        return g3

    events_csv = export_universe_events(universe, out_dir)
    events = _events_from_csv(events_csv)

    G2 = build_g2(events)
    print(f"  [G2] nodes={G2.number_of_nodes()}  edges={G2.number_of_edges()}")

    selected, b_mem, c_mem = detect_fixpoint_members(events, cfg)

    coords = compute_4d_coords(universe, events, G2)
    print(f"  [4d] concepts={len(coords)}")

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
              "fixpoint_method": str(cfg.get("fixpoint_method", "B"))}
        with open(out_dir / "g3_result.json", "w", encoding="utf-8") as f:
            json.dump(g3, f, ensure_ascii=False, indent=2)
        return g3

    evolve(G, {
        "iterations": int(cfg.get("gen_iterations", 3000)),
        "learning_rate": float(cfg.get("gen_learning_rate", 0.1)),
        "forgetting_rate": float(cfg.get("gen_forgetting_rate", 0.002)),
        "forget_interval": int(cfg.get("gen_forget_interval", 10)),
        "random_walk_prob": float(cfg.get("gen_random_walk_prob", 0.3)),
        "max_walk_length": int(cfg.get("gen_max_walk_length", 4)),
        "random_seed": int(cfg.get("random_seed", 42)),
    })

    det_cfg = {
        "compression_phi_threshold": float(cfg.get("gen_compression_phi_threshold", 1.5)),
        "min_cluster_size": int(cfg.get("gen_min_cluster_size", 3)),
        "max_cluster_size": int(cfg.get("gen_max_cluster_size", 8)),
        "migration_epsilon": float(cfg.get("gen_migration_epsilon", 0.1)),
    }
    clusters = detect_compression(G, det_cfg)
    migrations = detect_migration(G, det_cfg)
    print(f"  [detect] clusters={len(clusters)}  migrations={len(migrations)}")

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