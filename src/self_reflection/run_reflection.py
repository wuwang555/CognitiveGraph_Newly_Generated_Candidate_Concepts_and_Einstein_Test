# -*- coding: utf-8 -*-
"""入口脚本。

用法：
    cd src/self_reflection
    CONFIG_METHOD=A python run_reflection.py --rounds 5 --interval 10000 --num_concepts 51
"""

import argparse
import os
import random
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parents[1]
for _p in (str(_HERE), str(_PROJ)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
np.random.seed(42)
random.seed(42)

def _resolve(p):
    p = Path(p)
    return p if p.is_absolute() else (_PROJ / p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=None)
    ap.add_argument("--interval", type=int, default=None)
    ap.add_argument("--num_concepts", type=int, default=None)
    ap.add_argument("--concept_config", type=str, default=None)
    ap.add_argument("--output_root", type=str, default=None)
    ap.add_argument("--random_seed", type=int, default=None)
    ap.add_argument("--individual_id", type=int, default=None)
    args = ap.parse_args()

    if args.concept_config:
        os.environ["CONFIG_METHOD"] = args.concept_config
    else:
        os.environ.setdefault("CONFIG_METHOD", "A")

    # ★ 与主仓库 run_static.py 一致：seed 固定，再用 IndividualVariation 生成个体参数
    random.seed(42)
    np.random.seed(42)

    from config import BASE_PARAMETERS, VARIATION_RANGES
    from src.utils.individual_variation import (
        IndividualVariation, create_enhanced_individual_params,
    )

    from src.self_reflection.config_reflect import REFLECTION_CONFIG
    from src.self_reflection.reflect_loop import run_reflection_loop

    cfg = dict(REFLECTION_CONFIG)
    if args.rounds is not None:
        cfg["max_rounds"] = args.rounds
    if args.interval is not None:
        cfg["interval_iterations"] = args.interval
    if args.num_concepts is not None:
        cfg["num_concepts"] = args.num_concepts
    if args.output_root is not None:
        cfg["output_root"] = str(_resolve(args.output_root))
    if args.random_seed is not None:
        cfg["random_seed"] = args.random_seed
    if args.individual_id is not None:
        cfg["individual_id"] = args.individual_id
    cfg["concept_config"] = os.environ.get("CONFIG_METHOD", "A")

    # ★ 生成个体参数，与 run_static.py 一致
    var_sim = IndividualVariation(BASE_PARAMETERS, VARIATION_RANGES)
    base_params = var_sim.generate_individual(
        f"scale{cfg['num_concepts']}_ind{cfg['individual_id']}"
    )
    ind_params = create_enhanced_individual_params(base_params)
    cfg["individual_params"] = ind_params

    print(f"[run] concept_config = {cfg['concept_config']}")
    print(f"[run] num_concepts   = {cfg['num_concepts']}")
    print(f"[run] individual     = scale{cfg['num_concepts']}_ind{cfg['individual_id']}")
    print(f"[run] learning_rate  = {ind_params.get('base_learning_rate'):.4f}")
    print(f"[run] forgetting_rate = {ind_params.get('forgetting_rate'):.6f}")

    run_reflection_loop(cfg)


if __name__ == "__main__":
    main()