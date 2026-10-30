# -*- coding: utf-8 -*-
"""能耗公式的 G3 修正：边权降低、遍历偏好。"""

import random


def effective_learning_rate(base_lr, u, v, edge_boost_dict):
    """G3 修正后的有效学习率：base_lr * (1 + boost)。"""
    key = tuple(sorted([u, v]))
    boost = edge_boost_dict.get(key, 0.0)
    return float(base_lr) * (1.0 + float(boost))


def weighted_neighbor_choice(neighbors, u, edge_boost_dict, base_weights, rng=None):
    """按基础边权与 boost 加权选邻居。

    概率 ∝ (1 / (w + 0.01)) * (1 + boost)。
    """
    if rng is None:
        rng = random

    probs = []
    for v in neighbors:
        key = tuple(sorted([u, v]))
        boost = edge_boost_dict.get(key, 0.0)
        w = base_weights.get((u, v), 1.0)
        p = (1.0 / (w + 0.01)) * (1.0 + boost)
        probs.append(p)

    total = sum(probs)
    if total <= 0:
        return rng.choice(neighbors)
    return rng.choices(neighbors, weights=probs, k=1)[0]