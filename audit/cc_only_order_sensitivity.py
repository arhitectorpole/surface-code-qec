"""CC-only shortest-path order-sensitivity probe.

Purpose: test whether traversal order in the current graph/path implementation
changes the *content* of the d=5 CC-only shortest-path corpus, rather than merely
changing its enumeration order.

This is a diagnostic instrument only. It does not access historical Run A and
does not claim historical provenance. It deliberately excludes boundary-edge
paths, but CC shortest paths may still traverse a boundary node as an
intermediate graph node; therefore endpoint-disjoint is NOT synonymous with
motif I. Both quantities are reported explicitly.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from hashlib import sha256
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from s0_geometry import build_unrotated_planar_surface_code
from _level4_common import graph_construction, connection_catalog


def stable_hash(obj) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=list)
    return sha256(payload.encode()).hexdigest()


def reverse_adjacency(adjacency):
    return {node: list(reversed(edges)) for node, edges in adjacency.items()}


def repr_sorted_adjacency(adjacency):
    return {node: sorted(edges, key=repr) for node, edges in adjacency.items()}


def canonical_edge(edge):
    u, v, mask, meta = edge
    endpoints = tuple(sorted((u, v), key=repr))
    return (
        endpoints,
        meta.get("kind"),
        tuple(sorted(meta.get("checks", ()))),
        meta.get("check"),
        meta.get("qubit"),
        meta.get("side"),
        mask,
    )


def cc_records(catalog):
    records = []
    for key, paths in catalog.items():
        if key[0] != "pair":
            continue
        for mask, node_path, edge_path in paths:
            records.append((
                key,
                mask,
                tuple(node_path),
                tuple(canonical_edge(e) for e in edge_path),
                len(edge_path),
            ))
    return records


def cc_funnel(catalog):
    paths = cc_records(catalog)
    overlap_pairs = set()
    overlap_by_qubit = defaultdict(list)
    for pid, record in enumerate(paths):
        mask = record[1]
        while mask:
            bit = mask & -mask
            q = bit.bit_length() - 1
            overlap_by_qubit[q].append(pid)
            mask ^= bit
    for ids in overlap_by_qubit.values():
        for a, b in combinations(sorted(set(ids)), 2):
            overlap_pairs.add((a, b))

    conflicts = 0
    endpoint_disjoint = 0
    motif_I = 0
    for a, b in overlap_pairs:
        pa, pb = paths[a], paths[b]
        if set((pa[2][0], pa[2][-1])) & set((pb[2][0], pb[2][-1])):
            conflicts += 1
            continue
        endpoint_disjoint += 1
        pa_has_boundary = any(isinstance(n, tuple) and n[0] == "b" for n in pa[2])
        pb_has_boundary = any(isinstance(n, tuple) and n[0] == "b" for n in pb[2])
        if not pa_has_boundary and not pb_has_boundary:
            motif_I += 1

    return {
        "cc_paths_total": len(paths),
        "cc_connection_histogram": sorted(
            ((repr(k), sum(1 for p in paths if p[0] == k))
             for k in sorted({p[0] for p in paths}, key=repr)),
        ),
        "cc_overlap_pairs": len(overlap_pairs),
        "cc_endpoint_conflicts": conflicts,
        "cc_endpoint_disjoint_pairs": endpoint_disjoint,
        "motif_I": motif_I,
        "cc_path_hash": stable_hash(sorted(paths, key=repr)),
    }


def run_variant(code, sector, variant):
    adjacency, _ = graph_construction(code, sector)
    if variant == "native":
        adj = adjacency
    elif variant == "reversed":
        adj = reverse_adjacency(adjacency)
    elif variant == "repr_sorted":
        adj = repr_sorted_adjacency(adjacency)
    else:
        raise ValueError(variant)
    nchecks = len(code["z_checks"] if sector == "Z" else code["x_checks"])
    catalog = connection_catalog(adj, nchecks)
    return cc_funnel(catalog)


def main():
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    variants = ("native", "reversed", "repr_sorted")
    overall = []
    for sector in ("Z", "X"):
        code = build_unrotated_planar_surface_code(d)
        results = {v: run_variant(code, sector, v) for v in variants}
        native = results["native"]
        print(f"SECTOR {sector}")
        for variant in variants:
            print(variant, json.dumps(results[variant], sort_keys=True))
        for variant in variants[1:]:
            same = results[variant]["cc_path_hash"] == native["cc_path_hash"]
            same_funnel = results[variant] == native
            print(f"COMPARE native_vs_{variant} corpus_same={same} funnel_same={same_funnel}")
            overall.append(same and same_funnel)
    print("ORDER_SENSITIVITY_RESULT", "PASS" if all(overall) else "FAIL")
    print("SCOPE d=5 current committed S0 + _level4_common.py; CC-only; no historical claim")


if __name__ == "__main__":
    main()
