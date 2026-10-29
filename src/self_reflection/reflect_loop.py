# -*- coding: utf-8 -*-
"""自我推演主循环：跑 → 分析 → 反馈 → 继续。"""

import random
import sys
from pathlib import Path
import pandas as pd

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parents[1]
for _p in (str(_HERE), str(_PROJ)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

from src.self_reflection.config_reflect import REFLECTION_CONFIG
from src.self_reflection.reflected_universe import ReflectedUniverse
from src.self_reflection.feedback_rules import from_g3, save as save_K
from src.self_reflection.pipeline_adapter import run_pipeline
from src.self_reflection.state_io import save_universe_state

SUMMARY_FIELDS = [
    "round", "mode", "iter_start", "iter_end",
    "raw_compressions", "raw_migrations",
    "g2_nodes", "g2_edges",
    "n_B", "n_C", "n_selected",
    "gen_nodes", "gen_edges",
    "n_clusters", "n_migrations",
    "n_edge_boosts", "n_preferred_paths",
    "fixpoint_method",
]

def _resolve(p):
    p = Path(p)
    return p if p.is_absolute() else (_PROJ / p)


def run_reflection_loop(cfg=None):
    cfg = cfg or REFLECTION_CONFIG
    random.seed(cfg["random_seed"])
    np.random.seed(cfg["random_seed"])

    out_root = _resolve(cfg["output_root"])
    out_root.mkdir(parents=True, exist_ok=True)
    print(f"[loop] output_root = {out_root}")

    K = None
    prev_state_dir = None
    summary_rows = []
    for r in range(cfg["max_rounds"]):
        mode = "original" if r == 0 else "reflected"
        round_dir = out_root / f"round_{r + 1:03d}"
        round_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'=' * 70}")
        print(f"Round {r + 1}/{cfg['max_rounds']}  mode={mode}")
        print(f"  round_dir = {round_dir}")
        print(f"  interval  = {cfg['interval_iterations']}  "
              f"num_concepts = {cfg['num_concepts']}")
        print(f"  K edges   = {len((K or {}).get('edge_boosts', []))}")
        print(f"{'=' * 70}")

        universe = ReflectedUniverse(
            feedback_K=K,
            mode=mode,
            num_concepts=cfg["num_concepts"],
            init_state_dir=prev_state_dir,
        )
        universe.initialize_semantic_network()

        n_before = universe.iteration_count
        universe.evolve_with_emergence_detection(
            iterations=cfg["interval_iterations"],
            detection_interval=cfg["detection_interval"],
        )
        n_after = universe.iteration_count
        print(f"  iteration: {n_before} -> {n_after}")
        print(f"  raw_compressions = {len(universe.raw_compressions)}")
        print(f"  raw_migrations   = {len(universe.raw_migrations)}")

        # 1. 保存状态（含 raw_compressions.csv）
        save_universe_state(universe, round_dir / "universe_state")

        # 2. 跑 G3
        g3 = run_pipeline(universe, round_dir / "g3", cfg)

        # 3. 抽象 K
        K_new = from_g3(g3, cfg)
        save_K(K_new, round_dir / "feedback_K.json")

        summary_rows.append({
            "round": r + 1,
            "mode": mode,
            "iter_start": n_before,
            "iter_end": n_after,
            "raw_compressions": len(universe.raw_compressions),
            "raw_migrations": len(universe.raw_migrations),
            "g2_nodes": g3.get("g2_nodes"),
            "g2_edges": g3.get("g2_edges"),
            "n_B": g3.get("n_b_members"),
            "n_C": g3.get("n_c_members"),
            "n_selected": g3.get("n_selected"),
            "gen_nodes": g3.get("n_nodes"),
            "gen_edges": g3.get("n_edges"),
            "n_clusters": len(g3.get("clusters", [])),
            "n_migrations": len(g3.get("migrations", [])),
            "n_edge_boosts": len(K_new.get("edge_boosts", [])),
            "n_preferred_paths": len(K_new.get("preferred_paths", [])),
            "fixpoint_method": g3.get("fixpoint_method"),
        })

        K = K_new
        prev_state_dir = round_dir / "universe_state"

    summary_path = out_root / "summary.csv"
    pd.DataFrame(summary_rows, columns=SUMMARY_FIELDS).to_csv(
        summary_path, index=False, encoding="utf-8-sig"
    )

    print(f"\n{'=' * 70}")
    print(f"Done. {cfg['max_rounds']} rounds completed.")
    print(f"Results in: {out_root}")
    print(f"{'=' * 70}")