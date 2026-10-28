# -*- coding: utf-8 -*-
"""
从 B−C 概念 + 四维距离构建生成图。

步骤：
  1. 加载四维坐标（config_{X}/scale{N}.csv）
  2. 加载 B 和 C fixpoints，计算 B−C 集合
  3. 从 raw_events 重建 G2 边，只保留两端都在 B−C 中的边
  4. 边权 = 四维欧氏距离
"""

import json
import math
from collections import Counter
from pathlib import Path

import pandas as pd
import networkx as nx


def _euclidean_4d(a, b, use_normalized=True):
    """四维欧氏距离。use_normalized=True 用 (b, c_norm, g1_norm, g2_norm)；
    False 用 (b, c, g1_z, g2_z)。"""
    if use_normalized:
        keys = ["b", "c_norm", "g1_norm", "g2_norm"]
    else:
        keys = ["b", "c", "g1_z", "g2_z"]
    s = 0.0
    for k in keys:
        s += (float(a[k]) - float(b[k])) ** 2
    return math.sqrt(s)


def _load_4d_coords(input_root, config, scale):
    """加载四维坐标，返回 {concept: {b, c, g1_z, g2_z, c_norm, g1_norm, g2_norm}}。"""
    path = Path(input_root) / "four_dim_vectors" / f"config_{config}" / f"scale{scale}.csv"
    if not path.exists():
        print(f"  [debug] 4D coords not found at: {path.resolve()}")
        return None
    df = pd.read_csv(path)
    out = {}
    for _, row in df.iterrows():
        out[str(row["concept"])] = {
            "b":        float(row["b"]),
            "c":        float(row["c"]),
            "g1_z":     float(row["g1_z"]),
            "g2_z":     float(row["g2_z"]),
            "c_norm":   float(row["c_norm"]),
            "g1_norm":  float(row["g1_norm"]),
            "g2_norm":  float(row["g2_norm"]),
        }
    return out


def _load_fixpoint_members(results_root, config, scale, minsize, method):
    """加载 fixpoint_{method} 的所有 core 成员（并集）。"""
    path = (Path(results_root) / "endo_result" / f"scale{scale}" / f"config_{config}"
            / f"minsize_{minsize}" / f"fixpoint_{method}" / "fixpoints.json")
    if not path.exists():
        return set()
    with open(path, "r", encoding="utf-8") as f:
        fps = json.load(f)
    members = set()
    for fp in fps:
        for m in fp.get("core", []):
            members.add(m)
    return members


def _load_raw_events(results_root, config, scale):
    """加载 raw_events_{config}/raw_compression_events.csv，按 scale 过滤。"""
    path = Path(results_root) / "endo_result" / f"raw_events_{config}" / "raw_compression_events.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    if "scale" in df.columns:
        df = df[df["scale"] == scale]
    return df if not df.empty else None


def _extract_g2_edges(events_df, allowed_nodes):
    """从 raw events 重建 G2 的 clique 边，只保留两端都在 allowed_nodes 中的。"""
    counts = Counter()
    for _, row in events_df.iterrows():
        center = row.get("center")
        if pd.isna(center):
            continue
        center = str(center)
        raw_rel = row.get("related_nodes", "")
        if pd.isna(raw_rel):
            related = []
        else:
            related = [r.strip() for r in str(raw_rel).split("|") if r.strip()]
        nodes = list(dict.fromkeys([center] + related))
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                u, v = nodes[i], nodes[j]
                if u in allowed_nodes and v in allowed_nodes:
                    counts[tuple(sorted([u, v]))] += 1
    return counts


def build_bc_graph(config, scale, cfg):
    """
    构建 B−C 四维距离图。

    Returns
    -------
    G : nx.Graph  或  None（数据缺失）
        - 节点属性：b, c, g1_z, g2_z, c_norm, g1_norm, g2_norm
        - 边属性：weight（四维距离）、original_weight（同初值）、count（共现次数）
    info : dict   诊断信息
    """
    input_root = cfg["input_root"]
    minsize = cfg["minsize"]
    use_norm = cfg["use_normalized"]
    pool = cfg["concept_pool"]

    # 1. 四维坐标
    coords = _load_4d_coords(input_root, config, scale)
    if coords is None:
        return None, {"status": "missing_4d_coords"}

    # 2. B 和 C 成员
    b_members = _load_fixpoint_members(input_root, config, scale, minsize, "B")
    c_members = _load_fixpoint_members(input_root, config, scale, minsize, "C")

    if pool == "B_minus_C":
        selected = b_members - c_members
    elif pool == "B":
        selected = b_members
    elif pool == "C":
        selected = c_members
    else:
        raise ValueError(f"Unknown concept_pool: {pool}")

    # 3. 过滤节点
    selected_nodes = {c: coords[c] for c in selected if c in coords}
    if len(selected_nodes) < 2:
        return None, {"status": "too_few_nodes", "n_selected": len(selected_nodes)}

    # 4. G2 边（只保留 B−C 内的）
    events = _load_raw_events(input_root, config, scale)
    if events is None:
        return None, {"status": "missing_raw_events"}

    edge_counts = _extract_g2_edges(events, set(selected_nodes.keys()))
    if not edge_counts:
        return None, {
            "status": "no_edges_within_pool",
            "n_selected": len(selected_nodes),
        }

    # 5. 构建图
    G = nx.Graph()
    for node, attrs in selected_nodes.items():
        G.add_node(node, **attrs)

    for (u, v), cnt in edge_counts.items():
        d = _euclidean_4d(selected_nodes[u], selected_nodes[v], use_normalized=use_norm)
        G.add_edge(u, v, weight=d, original_weight=d, count=int(cnt))

    info = {
        "status": "ok",
        "config": config,
        "scale": scale,
        "n_B": len(b_members),
        "n_C": len(c_members),
        "n_B_minus_C": len(b_members - c_members),
        "n_selected_nodes": len(selected_nodes),
        "n_edges": G.number_of_edges(),
        "concept_pool": pool,
    }
    return G, info