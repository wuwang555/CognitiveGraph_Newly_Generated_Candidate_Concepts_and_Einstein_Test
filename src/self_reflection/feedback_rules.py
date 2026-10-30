# -*- coding: utf-8 -*-
"""从 G3 结果抽象反馈规则 K。

- clusters 不去重：同一个 core、不同 center 是合法输出。
- migrations 用 start/via/end 构造 path，保证 preferred_paths 非零。
"""

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parents[1]
for _p in (str(_HERE), str(_PROJ)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _resolve(p):
    p = Path(p)
    return p if p.is_absolute() else (_PROJ / p)


def _migration_path(m):
    """优先 path；否则 [start, via, end]。"""
    p = m.get("path")
    if p and len(p) >= 2:
        return list(p)
    s, v, e = m.get("start"), m.get("via"), m.get("end")
    if s and v and e:
        return [s, v, e]
    return []


def from_g3(g3_result, cfg):
    K = {
        "version": 1,
        "source": {
            "n_clusters": len(g3_result.get("clusters", [])),
            "n_migrations": len(g3_result.get("migrations", [])),
            "fixpoint_method": g3_result.get("fixpoint_method", "B"),
        },
        "edge_boosts": [],
        "preferred_paths": [],
        "cluster_patterns": [],
    }

    min_phi = float(cfg.get("min_g3_phi", 1.5))
    min_imp = float(cfg.get("min_g3_improvement", 0.1))
    scale = float(cfg.get("edge_boost_scale", 0.3))

    # ---------- 压缩：不去重 ----------
    for cluster in g3_result.get("clusters", []):
        phi = float(cluster.get("phi", 0.0))
        if phi < min_phi:
            continue
        members = list(cluster.get("cluster", []))
        if len(members) < 2:
            continue
        rel = min(2.0, phi / min_phi) / 2.0
        delta = scale * rel
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                u, v = sorted([members[i], members[j]])
                K["edge_boosts"].append({
                    "u": u, "v": v, "delta": delta, "source": "cluster",
                })
        K["cluster_patterns"].append({"members": members, "phi": phi})

    # ---------- 迁移：用 start/via/end ----------
    for m in g3_result.get("migrations", []):
        imp = float(m.get("improvement", 0.0) or 0.0)
        if imp < min_imp:
            continue
        path = _migration_path(m)
        if len(path) < 2:
            continue
        rel = min(1.0, imp / 0.5)
        delta = scale * rel
        for i in range(len(path) - 1):
            u, v = sorted([path[i], path[i + 1]])
            K["edge_boosts"].append({
                "u": u, "v": v, "delta": delta, "source": "migration",
            })
        K["preferred_paths"].append({"path": path, "improvement": imp})

    # ---------- 同一对边取 max delta ----------
    merged = {}
    for eb in K["edge_boosts"]:
        key = (eb["u"], eb["v"])
        if key not in merged or merged[key]["delta"] < eb["delta"]:
            merged[key] = eb
    K["edge_boosts"] = list(merged.values())

    return K


def save(K, path):
    path = _resolve(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(K, f, ensure_ascii=False, indent=2)
    print(f"  [save] {path}  "
          f"edge_boosts={len(K.get('edge_boosts', []))} "
          f"preferred_paths={len(K.get('preferred_paths', []))}")


def load(path):
    path = _resolve(path)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def to_edge_boost_dict(K):
    if K is None:
        return {}
    out = {}
    for eb in K.get("edge_boosts", []):
        key = tuple(sorted([eb["u"], eb["v"]]))
        out[key] = float(eb["delta"])
    return out