# -*- coding: utf-8 -*-
"""包装 RawRecordingUniverseEnhanced，支持 original / reflected 两种模式。

只改三个方法：
  - record_edge_activation : reflected 模式下学习率乘 (1 + boost)
  - _random_traversal      : reflected 模式下按 boost 加权选邻居
  - _detect_emergence      : reflected 模式下给匹配 G3 的事件打标记

其余全部继承自主仓库，不做任何修改。
"""

import random
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parents[1]
for _p in (str(_HERE), str(_PROJ)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from src.compression_graph.raw_recorder import RawRecordingUniverseEnhanced

from src.self_reflection.state_io import save_universe_state, load_universe_state
from src.self_reflection.feedback_rules import to_edge_boost_dict
from src.self_reflection.energy_patch import (
    effective_learning_rate, weighted_neighbor_choice,
)


def _resolve(p):
    p = Path(p)
    return p if p.is_absolute() else (_PROJ / p)


class ReflectedUniverse(RawRecordingUniverseEnhanced):
    """带"记住 G3"能力的一阶系统。"""

    def __init__(self, feedback_K=None, mode="original",
                 individual_params=None, network_seed=42, num_concepts=51,
                 init_state_dir=None):
        super().__init__(
            individual_params=individual_params,
            network_seed=network_seed,
            num_concepts=num_concepts,
        )
        self.mode = mode
        self.feedback_K = feedback_K
        self.edge_boost = to_edge_boost_dict(feedback_K)
        self.init_state_dir = _resolve(init_state_dir) if init_state_dir else None
        self.rng = random.Random(network_seed)

    def initialize_semantic_network(self):
        if self.mode == "reflected" and self.init_state_dir is not None:
            try:
                load_universe_state(self, self.init_state_dir)
                print(f"[reflected] loaded state from {self.init_state_dir}")
                return
            except Exception as e:
                print(f"[reflected] load failed: {e}, fallback to init")
        super().initialize_semantic_network()

    # ------------------------------------------------------------------ #
    def record_edge_activation(self, u, v):
        """和父类 CognitiveUniverse.record_edge_activation 一致，reflected 模式乘 (1+boost)。"""
        self.last_activation_time[(u, v)] = self.iteration_count
        current_energy = self.G[u][v]["weight"]
        base_lr = 0.1

        if self.mode == "reflected" and self.edge_boost:
            lr = effective_learning_rate(base_lr, u, v, self.edge_boost)
        else:
            lr = base_lr

        new_energy = current_energy * (1.0 - lr)
        self.G[u][v]["weight"] = max(0.05, new_energy)

    # ------------------------------------------------------------------ #
    def _random_traversal(self):
        """reflected 模式下按 boost 加权选邻居；original 模式走父类。"""
        if self.mode != "reflected" or not self.edge_boost:
            return super()._random_traversal()

        nodes = list(self.G.nodes())
        if len(nodes) < 2:
            return

        start = self.rng.choice(nodes)
        path = [start]
        current = start
        max_len = self.rng.randint(2, 4)

        for _ in range(max_len - 1):
            neighbors = list(self.G.neighbors(current))
            if not neighbors:
                break
            base_weights = {(current, v): self.G[current][v]["weight"] for v in neighbors}
            nxt = weighted_neighbor_choice(
                neighbors, current, self.edge_boost, base_weights, self.rng
            )
            if nxt in path:
                break
            path.append(nxt)
            current = nxt

        if len(path) >= 2:
            self.traversal_history.append({
                "path": list(path),
                "iteration": self.iteration_count,
                "type": "reflected_traversal",
            })
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                if self.G.has_edge(u, v):
                    self.record_edge_activation(u, v)

    # ------------------------------------------------------------------ #
    def _detect_emergence(self, iteration):
        """先走父类记录，再给新增事件打 G3 匹配标记。"""
        n_c = len(self.raw_compressions)
        n_m = len(self.raw_migrations)
        super()._detect_emergence(iteration)

        if self.mode != "reflected" or not self.feedback_K:
            return

        cp = self.feedback_K.get("cluster_patterns", [])
        pp = self.feedback_K.get("preferred_paths", [])
        for c in self.raw_compressions[n_c:]:
            c["g3_matched"] = self._match_cluster_pattern(c, cp)
        for m in self.raw_migrations[n_m:]:
            m["g3_matched"] = self._match_path_pattern(m, pp)

    def _match_cluster_pattern(self, compression, patterns):
        center = compression.get("center")
        members = set(compression.get("related_nodes", []))
        if center:
            members.add(center)
        for p in patterns:
            if len(set(p.get("members", [])) & members) >= 2:
                return True
        return False

    def _match_path_pattern(self, migration, patterns):
        ps = set()
        for k in ("from_node", "to_node", "principle_node"):
            if migration.get(k):
                ps.add(migration[k])
        for p in patterns:
            if len(set(p.get("path", [])) & ps) >= 2:
                return True
        return False