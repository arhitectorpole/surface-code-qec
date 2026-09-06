from __future__ import annotations
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
    connection_catalog,
    exhaustive_shortest_path_search,
    other_endpoint,
    syndrome_of_mask,
    xor_edge_masks,
)


def all_simple_paths(adjacency, src, dst):
    """Enumerate every simple path from src to dst.

    Because paths are simple, their edge length is bounded by |V|-1; this is
    an exact finite bound, not a heuristic cutoff.
    """
    paths = []

    def visit(node, visited, node_path, edge_path):
        if node == dst:
            paths.append((tuple(node_path), tuple(edge_path)))
            return
        for edge in adjacency[node]:
            nxt = other_endpoint(edge, node)
            if nxt in visited:
                continue
            visit(nxt, visited | {nxt}, node_path + [nxt], edge_path + [edge])

    visit(src, {src}, [src], [])
    return paths


def all_simple_connection_catalog(adjacency, nchecks):
    catalog = {}
    for i, j in combinations(range(nchecks), 2):
        paths = all_simple_paths(adjacency, ('c', i), ('c', j))
        catalog[('pair', i, j)] = [
            (xor_edge_masks(edge_path), node_path, edge_path)
            for node_path, edge_path in paths
        ]
    for i in range(nchecks):
        for side in ('T', 'B', 'L', 'R'):
            paths = all_simple_paths(adjacency, ('c', i), ('b', side))
            catalog[('boundary', i, side)] = [
                (xor_edge_masks(edge_path), node_path, edge_path)
                for node_path, edge_path in paths
            ]
    return catalog


def exhaustive_all_path_search(syndrome, nchecks, catalog):
    """Enumerate matchings with every simple constituent path."""
    if syndrome == 0:
        return {0: ()}

    @lru_cache(maxsize=None)
    def solve(remaining):
        if remaining == 0:
            return {0: ()}

        i = (remaining & -remaining).bit_length() - 1
        rest = remaining & ~(1 << i)
        masks = {}

        for j in range(i + 1, nchecks):
            if not (rest & (1 << j)):
                continue
            for mask, node_path, edge_path in catalog[('pair', i, j)]:
                for tail_mask, tail_provenance in solve(rest & ~(1 << j)).items():
                    masks.setdefault(
                        mask ^ tail_mask,
                        tail_provenance + (("pair", i, j, node_path, edge_path),),
                    )

        for side in ('T', 'B', 'L', 'R'):
            for mask, node_path, edge_path in catalog[('boundary', i, side)]:
                for tail_mask, tail_provenance in solve(rest).items():
                    masks.setdefault(
                        mask ^ tail_mask,
                        tail_provenance + (("boundary", i, side, node_path, edge_path),),
                    )
        return masks

    return solve(syndrome)


def main():
    code = build_unrotated_planar_surface_code(3)
    print("LEVEL 4C-A: SHORTEST-PATH COMPLETENESS ATTACK")
    print("graph=independent_candidate_construction_from_GRAPH_CONTRACT")
    print("comparison=G_short_vs_G_all_simple_paths")
    print("simple_path_bound=|V|-1 (exact for simple paths; no heuristic cutoff)")

    total_short_misses = 0
    total_all_misses = 0

    for sector in ('Z', 'X'):
        check_masks, _oracle_best, oracle_reps = exhaustive_physical_oracle(code, sector)
        adjacency, edges = graph_construction(code, sector)
        short_catalog = connection_catalog(adjacency, len(check_masks))
        all_catalog = all_simple_connection_catalog(adjacency, len(check_masks))

        short_path_count = sum(len(v) for v in short_catalog.values())
        all_path_count = sum(len(v) for v in all_catalog.values())
        oracle_missing_short = []
        oracle_missing_all = []
        extra_valid_masks = 0

        for syndrome in range(1 << len(check_masks)):
            short_candidates = exhaustive_shortest_path_search(
                syndrome, len(check_masks), short_catalog
            )
            all_candidates = exhaustive_all_path_search(
                syndrome, len(check_masks), all_catalog
            )

            short_valid = {
                mask for mask in short_candidates
                if syndrome_of_mask(mask, check_masks) == syndrome
            }
            all_valid = {
                mask for mask in all_candidates
                if syndrome_of_mask(mask, check_masks) == syndrome
            }

            missing_short = set(oracle_reps[syndrome]) - short_valid
            missing_all = set(oracle_reps[syndrome]) - all_valid
            if missing_short:
                oracle_missing_short.append((syndrome, sorted(missing_short)))
            if missing_all:
                oracle_missing_all.append((syndrome, sorted(missing_all)))
            extra_valid_masks += len(all_valid - short_valid)

        total_short_misses += len(oracle_missing_short)
        total_all_misses += len(oracle_missing_all)
        print(
            f"SECTOR {sector}: nodes={len(adjacency)} edges={len(edges)} "
            f"shortest_paths={short_path_count} all_simple_paths={all_path_count}"
        )
        print(
            f"  oracle_minima_missing_from_G_short={len(oracle_missing_short)}"
        )
        print(
            f"  oracle_minima_missing_from_G_all={len(oracle_missing_all)}"
        )
        print(
            f"  additional_valid_masks_in_G_all_not_G_short={extra_valid_masks}"
        )
        for syndrome, masks in oracle_missing_short:
            print(f"  SHORT_COUNTEREXAMPLE syndrome=0x{syndrome:02x} masks={masks}")
        for syndrome, masks in oracle_missing_all:
            print(f"  ALL_PATH_COUNTEREXAMPLE syndrome=0x{syndrome:02x} masks={masks}")

    print("TOTAL_SECTORS=2")
    print(f"TOTAL_ORACLE_MINIMA_MISSING_FROM_G_SHORT={total_short_misses}")
    print(f"TOTAL_ORACLE_MINIMA_MISSING_FROM_G_ALL={total_all_misses}")
    if total_short_misses or total_all_misses:
        print("RESULT: FAIL")
        raise SystemExit(1)

    print("RESULT: PASS")
    print(
        "INTERPRETATION: for d=3, every oracle-minimum physical mask is "
        "represented within the shortest-path-generated search space; all-simple-path "
        "enumeration adds valid masks but no missing oracle minimum."
    )


if __name__ == '__main__':
    main()
