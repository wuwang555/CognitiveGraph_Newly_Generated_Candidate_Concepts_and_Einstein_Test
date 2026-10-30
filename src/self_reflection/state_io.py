# -*- coding: utf-8 -*-
"""保存 / 加载 universe 状态。

只保存 graph.pkl 和 state.json。raw_compressions 由 pipeline_adapter
统一导出为 raw_compression_events.csv，这里不再写，避免重复。
"""

import json
import pickle
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


def save_universe_state(universe, out_dir):
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
    }
    with open(out_dir / "state.json", "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


def load_universe_state(universe, in_dir):
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

    universe.raw_compressions = []
    universe.raw_migrations = []
    return universe