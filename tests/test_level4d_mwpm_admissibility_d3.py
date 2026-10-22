"""Level 4D: adversarial MWPM admissibility test for d=3.

This test does not modify production code and does not call an external MWPM
solver. It computes the exact MWPM objective on the candidate graph by
exhaustive enumeration of defect matchings and all constituent shortest paths.

Two path-cost models are tested:
  1. graph: shortest-path edge count;
  2. physical: Hamming weight of the constituent path's physical mask.

For every sector-local syndrome, the minimum-cost matching witnesses are
XORed into physical masks and checked against the independent exhaustive
physical oracle. Ties are retained, so a cost model fails if any minimum-cost
witness can produce a syndrome-correct physical mask heavier than the oracle
minimum.
"""

from collections import deque
from functools import lru_cache
from itertools import combinations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.s0_geometry import build_unrotated_planar_surface_code
from tests._level4_common import (
    exhaustive_physical_oracle,
    graph_construction,
    popcount,
    syndrome_of_mask,
)


def other_endpoint(edge, node):
    return edge[1] if edge[0] == node else edge[0]


def all_simple_paths(adjacency, src, dst):
    """Enumerate every simple path between two graph nodes."""
    paths = []

    def visit(node, seen, node_path, edge_path):
        if node == dst:
            paths.append((tuple(node_path), tuple(edge_path)))
            return
        for edge in adjacency[node]:
            nxt = other_endpoint(edge, node)
            if nxt in seen:
                continue
            seen.add(nxt)
            visit(nxt, seen, node_path + [nxt], edge_path + [edge])
            seen.remove(nxt)

    visit(src, {src}, [src], [])
    return paths


def path_mask(path):
    _nodes, edges = path
    mask = 0
    for edge in edges:
        mask ^= edge[2]
    return mask


def path_cost(path, mode):
    if mode == "graph":
        return len(path[1])
    if mode == "physical":
        return popcount(path_mask(path))
    raise ValueError(f"unknown path-cost mode: {mode}")


def shortest_catalog(adjacency, nchecks, mode):
    """For each connection, keep every path minimizing the selected cost."""
    catalog = {}
    for i, j in combinations(range(nchecks), 2):
        paths = all_simple_paths(adjacency, ("c", i), ("c", j))
        best = min(path_cost(path, mode) for path in paths)
        catalog[("pair", i, j)] = [
            (path_mask(path), path, path_cost(path, mode))
            for path in paths
            if path_cost(path, mode) == best
        ]
    for i in range(nchecks):
        for side in ("T", "B", "L", "R"):
            paths = all_simple_paths(adjacency, ("c", i), ("b", side))
            best = min(path_cost(path, mode) for path in paths)
            catalog[("boundary", i, side)] = [
                (path_mask(path), path, path_cost(path, mode))
                for path in paths
                if path_cost(path, mode) == best
            ]
    return catalog


def exhaustive_mwpm_witnesses(syndrome, nchecks, catalog):
    """Enumerate all minimum-cost matching witnesses for a syndrome.

    Boundary nodes have unlimited termination capacity, matching the candidate
    contract. Returned tuples are (total_cost, physical_mask, provenance).
    """
    if syndrome == 0:
        return [(0, 0, ())]

    @lru_cache(maxsize=None)
    def solve(remaining):
        if remaining == 0:
            return [(0, 0, ())]

        i = (remaining & -remaining).bit_length() - 1
        rest = remaining & ~(1 << i)
        out = []

        for j in range(i + 1, nchecks):
            if not (rest & (1 << j)):
                continue
            for mask, path, cost in catalog[("pair", i, j)]:
                for tail_cost, tail_mask, tail_prov in solve(rest & ~(1 << j)):
                    out.append(
                        (
                            cost + tail_cost,
                            mask ^ tail_mask,
                            tail_prov + ((("pair", i, j), path),),
                        )
                    )

        for side in ("T", "B", "L", "R"):
            for mask, path, cost in catalog[("boundary", i, side)]:
                for tail_cost, tail_mask, tail_prov in solve(rest):
                    out.append(
                        (
                            cost + tail_cost,
                            mask ^ tail_mask,
                            tail_prov + ((("boundary", i, side), path),),
                        )
                    )

        minimum = min(item[0] for item in out)
        return [item for item in out if item[0] == minimum]

    return solve(syndrome)


def validate_sector(code, sector, mode):
    check_masks, oracle_best, _oracle_reps = exhaustive_physical_oracle(code, sector)
    adjacency, edges = graph_construction(code, sector)
    catalog = shortest_catalog(adjacency, len(check_masks), mode)
    failures = []
    records = []

    for syndrome in range(1 << len(check_masks)):
        witnesses = exhaustive_mwpm_witnesses(syndrome, len(check_masks), catalog)
        valid = [
            item
            for item in witnesses
            if syndrome_of_mask(item[1], check_masks) == syndrome
        ]
        physical_weights = sorted({popcount(item[1]) for item in valid})
        graph_cost = witnesses[0][0]
        best_physical = min(physical_weights, default=None)
        record = {
            "syndrome": f"0x{syndrome:02x}",
            "oracle_weight": oracle_best[syndrome],
            "mwpm_cost": graph_cost,
            "valid_min_witnesses": len(valid),
            "physical_weights": physical_weights,
        }
        records.append(record)
        if best_physical != oracle_best[syndrome] or len(valid) != len(witnesses):
            failures.append(record)

    path_count = sum(len(paths) for paths in catalog.values())
    return edges, path_count, records, failures


def main():
    code = build_unrotated_planar_surface_code(3)
    print("LEVEL 4D MWPM-ADMISSIBILITY ATTACK")
    print("production_decoder_imported=False")
    print("oracle=exhaustive_2^13_physical_masks_per_CSS_sector")
    print("matching=exhaustive_exact_minimum_cost_with_all_ties")

    all_failures = []
    total_cases = 0

    for sector in ("Z", "X"):
        for mode in ("graph", "physical"):
            edges, path_count, records, failures = validate_sector(code, sector, mode)
            total_cases += len(records)
            all_failures.extend((sector, mode, f) for f in failures)
            varying = sum(1 for r in records if len(r["physical_weights"]) > 1)
            print(
                f"SECTOR {sector} mode={mode}: graph_edges={len(edges)} "
                f"cost-minimal-constituent-paths={path_count} cases={len(records)} "
                f"failures={len(failures)} tie_physical_weight_variation_cases={varying}"
            )
            for record in records:
                print(
                    f"{sector} mode={mode} syn={record['syndrome']} "
                    f"oracle={record['oracle_weight']} mwpm_cost={record['mwpm_cost']} "
                    f"valid_min_witnesses={record['valid_min_witnesses']} "
                    f"physical_weights={record['physical_weights']}"
                )

    print(f"TOTAL_CASES={total_cases}")
    print(f"TOTAL_FAILURES={len(all_failures)}")
    if all_failures:
        print("RESULT: FAIL")
        for failure in all_failures:
            print("COUNTEREXAMPLE", failure)
        raise SystemExit(1)

    print("RESULT: PASS")
    print(
        "INTERPRETATION: every exact minimum-cost matching witness tested "
        "produced a syndrome-correct physical mask at the independent oracle "
        "minimum for both cost models on d=3."
    )


if __name__ == "__main__":
    main()
