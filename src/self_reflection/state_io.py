# -*- coding: utf-8 -*-
"""保存 / 加载 universe 状态，用于跨轮延续。"""

import json
import pickle
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parents[1]
for _p in (str(_HERE), str(_PROJ)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd


def _resolve(p):
    p = Path(p)
    return p if p.is_absolute() else (_PROJ / p)


def save_universe_state(universe, out_dir):
    """保存 G、iteration_count、energy_history、traversal_history 等。"""
    out_dir = _resolve(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "graph.pkl", "wb") as f:
        pickle.dump(universe.G, f)

    last_act = {f"{u}|{v}": int(t) for (u, v), t in universe.last_activation_time.items()}
    state = {
        "iteration_count": int(universe.iteration_count),
        "energy_history": [float(x) for x in universe.energy_history],
        "traversal_history": universe.traversal_history,
        "learning_rate": float(universe.learning_rate),
        "forgetting_rate": float(universe.forgetting_rate),
        "last_activation_time": last_act,
        "n_raw_compressions": len(getattr(universe, "raw_compressions", []) or []),
        "n_raw_migrations": len(getattr(universe, "raw_migrations", []) or []),
    }
    with open(out_dir / "state.json", "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

    raw = getattr(universe, "raw_compressions", None)
    if raw is not None:
        rows = []
        for i, c in enumerate(raw):
            rows.append({
                "event_id": i,
                "center": c.get("center", ""),
                "related_nodes": "|".join(c.get("related_nodes", []) or []),
                "detection_iteration": c.get("detection_iteration", -1),
                "emergence_strength": c.get("emergence_strength"),
            })
        df = pd.DataFrame(rows)
        path = out_dir / "raw_compressions.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  [save] {path}  rows={len(df)}")

    mig = getattr(universe, "raw_migrations", None)
    if mig is not None and len(mig) > 0:
        mrows = []
        for i, m in enumerate(mig):
            mrows.append({
                "event_id": i,
                "from_node": m.get("from_node", ""),
                "to_node": m.get("to_node", ""),
                "principle_node": m.get("principle_node", ""),
                "efficiency_gain": m.get("efficiency_gain"),
                "detection_iteration": m.get("detection_iteration", -1),
            })
        mpath = out_dir / "raw_migrations.csv"
        pd.DataFrame(mrows).to_csv(mpath, index=False, encoding="utf-8-sig")
        print(f"  [save] {mpath}  rows={len(mrows)}")


def load_universe_state(universe, in_dir):
    """恢复 universe 的图与运行状态。

    注意：raw_compressions / raw_migrations 不恢复，每轮从空列表开始，
    只记录本轮新检测到的事件。这是设计意图。
    """
    in_dir = _resolve(in_dir)
    with open(in_dir / "graph.pkl", "rb") as f:
        universe.G = pickle.load(f)
    with open(in_dir / "state.json", "r", encoding="utf-8") as f:
        state = json.load(f)

    universe.iteration_count = int(state.get("iteration_count", 0))
    universe.energy_history = list(state.get("energy_history", []))
    universe.traversal_history = list(state.get("traversal_history", []))
    universe.learning_rate = float(state.get("learning_rate", 0.85))
    universe.forgetting_rate = float(state.get("forgetting_rate", 0.002))

    universe.last_activation_time = {}
    for k, t in state.get("last_activation_time", {}).items():
        u, v = k.split("|")
        universe.last_activation_time[(u, v)] = int(t)

    # 显式重置本轮的原始事件记录
    universe.raw_compressions = []
    universe.raw_migrations = []

    return universe