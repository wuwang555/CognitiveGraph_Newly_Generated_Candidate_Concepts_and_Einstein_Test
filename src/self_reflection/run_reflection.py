# -*- coding: utf-8 -*-
"""入口脚本。

用法：
    cd src/self_reflection
    CONFIG_METHOD=A python run_reflection.py --rounds 5 --interval 10000 --num_concepts 51
"""

import argparse
import os
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=None)
    ap.add_argument("--interval", type=int, default=None)
    ap.add_argument("--num_concepts", type=int, default=None)
    ap.add_argument("--concept_config", type=str, default=None,
                    help="A / B / C")
    ap.add_argument("--output_root", type=str, default=None)
    ap.add_argument("--random_seed", type=int, default=None)
    args = ap.parse_args()

    # 先设置环境变量，再 import 会触发 config 加载的模块
    if args.concept_config:
        os.environ["CONFIG_METHOD"] = args.concept_config
    else:
        os.environ.setdefault("CONFIG_METHOD", "A")

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
    cfg["concept_config"] = os.environ.get("CONFIG_METHOD", "A")

    run_reflection_loop(cfg)


if __name__ == "__main__":
    main()