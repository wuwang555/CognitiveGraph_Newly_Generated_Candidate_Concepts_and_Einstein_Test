# -*- coding: utf-8 -*-
"""
在 B−C 四维距离图上跑演化。

机制（完全对照原论文）：
  - 学习：随机选一条边，边权 *= (1 - learning_rate)
  - 遗忘：每 forget_interval 步，所有边向 original_weight 回归
  - 遍历：以 random_walk_prob 概率触发随机游走，沿路径学习
"""

import random
from typing import List, Tuple

import networkx as nx


def _random_walk(G, start, max_steps, visited=None):
    """从 start 出发的随机游走。"""
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
    """
    演化主循环。

    Returns
    -------
    energy_history : list[float]   每步全局平均边权
    traversal_history : list[list] 每次随机游走的路径
    """
    rng = random.Random(cfg["random_seed"])

    iterations = cfg["iterations"]
    lr = cfg["learning_rate"]
    fr = cfg["forgetting_rate"]
    forget_interval = cfg["forget_interval"]
    walk_prob = cfg["random_walk_prob"]
    max_walk = cfg["max_walk_length"]

    # 初始化
    for u, v, d in G.edges(data=True):
        d["original_weight"] = d.get("original_weight", d["weight"])
        d["traversal_count"] = d.get("traversal_count", 0)

    energy_history: List[float] = []
    traversal_history: List[List[str]] = []

    edges = list(G.edges())
    if not edges:
        return energy_history, traversal_history

    for it in range(iterations):
        # --- 学习：随机选一条边 ---
        u, v = rng.choice(edges)
        if G.has_edge(u, v):
            cur = G[u][v]["weight"]
            G[u][v]["weight"] = max(0.01, cur * (1 - lr))
            G[u][v]["traversal_count"] = G[u][v].get("traversal_count", 0) + 1

        # --- 遍历：随机游走 ---
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

        # --- 遗忘 ---
        if it % forget_interval == 0:
            for a, b, d in G.edges(data=True):
                orig = d.get("original_weight", d["weight"])
                d["weight"] = d["weight"] + (orig - d["weight"]) * fr

        # --- 记录全局能量（平均边权 = 平均距离）---
        if G.number_of_edges() > 0:
            avg = sum(d["weight"] for _, _, d in G.edges(data=True)) / G.number_of_edges()
            energy_history.append(avg)

    return energy_history, traversal_history