# -*- coding: utf-8 -*-
"""去掉 detect_spontaneous_compression 的 [:10] 截断和去重。

原版 detector_fixed.py 末尾是 return compression_candidates[:10]，
且 _is_duplicate_compression 会去重。NonDeduplicatingDetector 只改了
去重，没改 [:10]。这里同时去掉这两个限制，保留其余逻辑完全一致。
"""

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parents[1]
for _p in (str(_HERE), str(_PROJ)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

from src.emergence.detector_fixed import EmergenceDetectorFixed


class NoTruncationDetector(EmergenceDetectorFixed):
    """与 EmergenceDetectorFixed 完全一致，只去掉 [:10] 截断和去重。"""

    def _is_duplicate_compression(self, center, neighbors):
        # 不去重
        return False

    def detect_spontaneous_compression(self, network, energy_history, traversal_history=None):
        compression_candidates = []

        if len(energy_history) < 50:
            return compression_candidates

        node_degrees = dict(network.degree())
        candidate_nodes = [
            node for node, degree in node_degrees.items()
            if 3 <= degree <= 15
        ]

        for center in candidate_nodes:
            neighbors = list(network.neighbors(center))
            if len(neighbors) < self.thresholds['min_cluster_size']:
                continue

            connection_strengths = []
            for neighbor in neighbors:
                if network.has_edge(center, neighbor):
                    weight = network[center][neighbor]['weight']
                    strength = 1.0 / (1.0 + weight)
                    if strength > self.thresholds['min_connection_strength']:
                        connection_strengths.append((neighbor, strength))

            if len(connection_strengths) < self.thresholds['min_cluster_size']:
                continue

            connection_strengths.sort(key=lambda x: x[1], reverse=True)

            if self.thresholds['dynamic_cluster_sizing']:
                cluster_size = self._determine_dynamic_cluster_size(connection_strengths)
            else:
                cluster_size = self.thresholds['max_cluster_size']

            selected_neighbors = [n for n, s in connection_strengths[:cluster_size]]

            cohesion = self._compute_cluster_cohesion(center, selected_neighbors, network)
            energy_sync = self._compute_energy_synchronization_improved(
                center, selected_neighbors, network, energy_history
            )
            emergence_strength = self._compute_comprehensive_emergence_strength(
                center, selected_neighbors, network, cohesion, energy_sync
            )

            if (emergence_strength > self.thresholds['compression_synergy'] and
                    cohesion > self.thresholds['cluster_cohesion'] and
                    energy_sync > self.thresholds['energy_sync_threshold']):
                # ★ 去掉 _is_duplicate_compression 判断（_is_duplicate_compression 已恒 False）
                potential = self._compute_compression_potential(center, selected_neighbors, network)
                compression_candidates.append({
                    'center': center,
                    'related_nodes': selected_neighbors,
                    'energy_synergy': energy_sync,
                    'cohesion': cohesion,
                    'emergence_strength': emergence_strength,
                    'cluster_size': len(selected_neighbors),
                    'avg_connection_strength': np.mean([s for _, s in connection_strengths[:cluster_size]]),
                    'compression_potential': potential
                })

        # ★ 去掉 [:10]，返回全部
        return compression_candidates