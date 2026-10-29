# -*- coding: utf-8 -*-
"""
主入口：在 B−C 四维距离图上跑演化 + 压缩/迁移检测。

用法：
    cd src/generative_graph
    python run_generative.py
    python run_generative.py --configs A --scales 51
    python run_generative.py --configs A --pools B C B_minus_C --scales 51 71
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ---- 路径 ----
_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parent
_PROJ = _SRC.parent
for _p in (str(_HERE), str(_SRC), str(_PROJ)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd
import networkx as nx

from config_gen import GENERATIVE_GRAPH_CONFIG
from build_graph import build_bc_graph
from evolve import evolve
from detect import detect_compression, detect_migration


# ====================================================================== #
# 路径解析
# ====================================================================== #
def _resolve_paths(cfg):
    def _abs(p):
        p = Path(p)
        return p if p.is_absolute() else (_PROJ / p)

    input_root = _abs(cfg["input_root"])
    output_root = _abs(cfg["output_root"])
    return input_root, output_root


def _save_graph(G, out_dir):
    node_rows = []
    for n, d in G.nodes(data=True):
        row = {"concept": n}
        for k in ("b", "c", "g1_z", "g2_z", "c_norm", "g1_norm", "g2_norm"):
            if k in d:
                row[k] = d[k]
        node_rows.append(row)
    pd.DataFrame(node_rows).to_csv(
        out_dir / "graph_nodes.csv", index=False, encoding="utf-8-sig")

    edge_rows = []
    for u, v, d in G.edges(data=True):
        edge_rows.append({
            "concept_a": u,
            "concept_b": v,
            "weight": float(d.get("weight", 0.0)),
            "original_weight": float(d.get("original_weight", d.get("weight", 0.0))),
            "count": int(d.get("count", 0)),
            "traversal_count": int(d.get("traversal_count", 0)),
        })
    pd.DataFrame(edge_rows).to_csv(
        out_dir / "graph_edges.csv", index=False, encoding="utf-8-sig")


def _save_history(history, traversal_history, out_dir):
    if history:
        pd.DataFrame({
            "iteration": list(range(len(history))),
            "mean_distance": [float(x) for x in history],
        }).to_csv(out_dir / "energy_history.csv", index=False, encoding="utf-8-sig")

    if traversal_history:
        rows = []
        for i, path in enumerate(traversal_history):
            rows.append({"idx": i, "path": " -> ".join(path), "length": len(path)})
        pd.DataFrame(rows).to_csv(
            out_dir / "traversal_history.csv", index=False, encoding="utf-8-sig")


def _save_compressions(comps, out_dir):
    if comps:
        pd.DataFrame(comps).to_csv(
            out_dir / "candidate_compressions.csv",
            index=False, encoding="utf-8-sig")


def _save_migrations(migs, out_dir):
    if migs:
        pd.DataFrame(migs).to_csv(
            out_dir / "candidate_migrations.csv",
            index=False, encoding="utf-8-sig")


# ====================================================================== #
# 单个 (config, scale, pool)
# ====================================================================== #
def run_one(config, scale, pool, cfg, input_root, output_root):
    """跑单个 (config, scale, pool)。"""
    print(f"\n[config={config}, scale={scale}, pool={pool}]")

    G, info = build_bc_graph(
        config, scale, {**cfg, "input_root": str(input_root)}, pool=pool)
    if G is None:
        print(f"  [skip] {info.get('status')}")
        return None

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    print(f"  graph: {n_nodes} nodes, {n_edges} edges  "
          f"(B={info['n_B']}, C={info['n_C']}, B−C={info['n_B_minus_C']})")

    # 演化
    print(f"  evolving ({cfg['iterations']} iterations) ...")
    history, traversals = evolve(G, cfg)

    if history:
        initial = history[0]
        final = history[-1]
        reduction = (initial - final) / initial * 100 if initial > 0 else 0.0
        print(f"  energy: {initial:.4f} → {final:.4f}  "
              f"(distance reduction {reduction:.1f}%)")

    # 压缩 / 迁移
    comps = detect_compression(G, cfg)
    migs = detect_migration(G, cfg)
    print(f"  compressions: {len(comps)}  migrations: {len(migs)}")

    # 保存 —— 路径改为 config_{config}/pool_{pool}/scale{scale}/
    out_dir = output_root / f"config_{config}" / f"pool_{pool}" / f"scale{scale}"
    out_dir.mkdir(parents=True, exist_ok=True)
    _save_graph(G, out_dir)
    _save_history(history, traversals, out_dir)
    _save_compressions(comps, out_dir)
    _save_migrations(migs, out_dir)
    with open(out_dir / "info.json", "w", encoding="utf-8") as f:
        json.dump({**info, "n_compressions": len(comps), "n_migrations": len(migs)},
                  f, ensure_ascii=False, indent=2)

    return {
        "config": config,
        "concept_pool": pool,
        "scale": scale,
        "n_B": info["n_B"],
        "n_C": info["n_C"],
        "n_B_minus_C": info["n_B_minus_C"],
        "n_graph_nodes": n_nodes,
        "n_graph_edges": n_edges,
        "initial_distance": float(history[0]) if history else None,
        "final_distance": float(history[-1]) if history else None,
        "distance_reduction_pct": (
            float((history[0] - history[-1]) / history[0] * 100)
            if history and history[0] > 0 else None
        ),
        "n_compressions": len(comps),
        "n_migrations": len(migs),
        "n_traversals": len(traversals),
    }


# ====================================================================== #
# 输入诊断
# ====================================================================== #
def _diagnose_inputs(configs, scales, input_root):
    """打印每个 (config, scale) 期望的文件是否存在（与 pool 无关）。"""
    print("\n[输入诊断]")
    missing = []
    for config in configs:
        for scale in scales:
            checks = [
                ("4D coords",   input_root / "four_dim_vectors" / f"config_{config}" / f"scale{scale}.csv"),
                ("B fixpoint",  input_root / "endo_result" / f"scale{scale}" / f"config_{config}" / "minsize_1" / "fixpoint_B" / "fixpoints.json"),
                ("C fixpoint",  input_root / "endo_result" / f"scale{scale}" / f"config_{config}" / "minsize_1" / "fixpoint_C" / "fixpoints.json"),
                ("raw events",  input_root / "endo_result" / f"raw_events_{config}" / "raw_compression_events.csv"),
            ]
            for name, p in checks:
                ok = "OK" if p.exists() else "MISSING"
                if not p.exists():
                    missing.append((config, scale, name, str(p)))
                print(f"  [{ok:7s}] {config}/{scale} {name:12s}  {p}")
    if missing:
        print(f"\n  ⚠ {len(missing)} 个文件缺失，具体如上。")
        print(f"  提示：input_root 当前 = {input_root}")
        print(f"  请确认 four_dim_vectors/ 和 endo_result/ 是否在这个目录下。")
    else:
        print("  ✓ 全部输入就绪")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", nargs="+", default=None)
    ap.add_argument("--pools", nargs="+", default=None,
                    help="概念池列表，可选值：B / C / B_minus_C，可自由组合")
    ap.add_argument("--scales", nargs="+", type=int, default=None)
    ap.add_argument("--iterations", type=int, default=None)
    args = ap.parse_args()

    cfg = dict(GENERATIVE_GRAPH_CONFIG)
    if args.configs:
        cfg["configs"] = args.configs
    if args.pools:
        cfg["concept_pools"] = args.pools
    if args.scales:
        cfg["scales"] = args.scales
    if args.iterations:
        cfg["iterations"] = args.iterations

    input_root, output_root = _resolve_paths(cfg)
    output_root.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("generative_graph — 从四维概念空间到生成图")
    print(f"  configs       = {cfg['configs']}")
    print(f"  concept_pools = {cfg['concept_pools']}")
    print(f"  scales        = {cfg['scales']}")
    print(f"  iterations    = {cfg['iterations']}")
    print(f"  results_root  = {output_root}")
    print("=" * 70)

    _diagnose_inputs(cfg["configs"], cfg["scales"], input_root)

    rows = []
    for config in cfg["configs"]:
        for pool in cfg["concept_pools"]:
            for scale in cfg["scales"]:
                row = run_one(config, scale, pool, cfg, input_root, output_root)
                if row is not None:
                    rows.append(row)

    if rows:
        summary = pd.DataFrame(rows)
        # 保证 config / concept_pool / scale 三列在前
        front = ["config", "concept_pool", "scale"]
        cols = front + [c for c in summary.columns if c not in front]
        summary = summary[cols]
        summary.to_csv(output_root / "summary.csv",
                       index=False, encoding="utf-8-sig")
        print("\n" + "=" * 70)
        print(f"[saved] {output_root / 'summary.csv'}")
        print(summary.to_string(index=False))
    else:
        print("\n[warning] no rows generated — 检查上游数据是否存在")


if __name__ == "__main__":
    main()