# -*- coding: utf-8 -*-
"""
在 B−C 四维距离图上做压缩/迁移检测。

- 压缩：Φ = 外部平均距离 / 内部平均距离。Φ > threshold = 内部紧致。
- 迁移：d(a,z) + d(z,b) < d(a,b) × (1 - ε)。通过中间节点更近。
"""

from typing import List, Dict, Any, Optional

import networkx as nx


# ====================================================================== #
# 压缩
# ====================================================================== #
def _compression_potential(G, cluster):
    """
    Φ = 外部平均距离 / 内部平均距离。

    Φ > 1  = 内部距离远小于外部 = 紧致。
    """
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
    """
    对每个节点作为中心，取 top-k 邻居构成簇，计算 Φ。

    Returns
    -------
    list of dict: [{"center", "cluster", "size", "phi"}, ...]
    """
    min_k = cfg["min_cluster_size"]
    max_k = cfg["max_cluster_size"]
    threshold = cfg["compression_phi_threshold"]

    candidates = []
    for center in G.nodes():
        nbrs = list(G.neighbors(center))
        if len(nbrs) < min_k:
            continue
        # 按距离升序（越近越优先）
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


# ====================================================================== #
# 迁移
# ====================================================================== #
def detect_migration(G, cfg):
    """
    对每对 (a, b) 有直接边的，检查是否存在 z 使得：
        d(a,z) + d(z,b) < d(a,b) × (1 - ε)

    即通过中间节点更近。

    Returns
    -------
    list of dict: [{"start", "via", "end", "direct", "path", "improvement"}, ...]
    """
    epsilon = cfg["migration_epsilon"]
    nodes = list(G.nodes())

    migrations = []
    for a in nodes:
        for b in nodes:
            if a >= b:  # 对称，只处理一次
                continue
            if not G.has_edge(a, b):
                continue
            direct = G[a][b]["weight"]
            if direct <= 1e-9:
                continue

            # 找中间节点 z
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