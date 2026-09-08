from __future__ import annotations
from itertools import combinations
from collections import deque
from functools import lru_cache


def popcount(x: int) -> int:
    return x.bit_count()


def parity(x: int) -> int:
    return x.bit_count() & 1


def sector_checks(code, sector):
    return code["z_checks"] if sector == "Z" else code["x_checks"]


def make_check_masks(code, sector):
    masks = []
    for _, qs in sector_checks(code, sector):
        mask = 0
        for q in qs:
            mask |= 1 << q
        masks.append(mask)
    return masks


def syndrome_of_mask(mask: int, check_masks):
    syndrome = 0
    for c, check_mask in enumerate(check_masks):
        if parity(mask & check_mask):
            syndrome |= 1 << c
    return syndrome


def exhaustive_physical_oracle(code, sector):
    """Independent oracle: enumerate all 2^n physical masks."""
    check_masks = make_check_masks(code, sector)
    n = len(code["data"])
    best = [n + 1] * (1 << len(check_masks))
    representatives = [set() for _ in best]
    for mask in range(1 << n):
        syndrome = syndrome_of_mask(mask, check_masks)
        weight = popcount(mask)
        if weight < best[syndrome]:
            best[syndrome] = weight
            representatives[syndrome] = {mask}
        elif weight == best[syndrome]:
            representatives[syndrome].add(mask)
    return check_masks, best, representatives


def graph_construction(code, sector):
    """Candidate graph exactly as stated in GRAPH_CONTRACT.md."""
    checks = sector_checks(code, sector)
    data = code["data"]
    d = code["d"]
    max_coord = 2 * d - 2
    nodes = ([('c', i) for i in range(len(checks))] +
             [('b', side) for side in ('T', 'B', 'L', 'R')])
    adjacency = {node: [] for node in nodes}
    edges = []

    for i, j in combinations(range(len(checks)), 2):
        intersection = set(checks[i][1]) & set(checks[j][1])
        if len(intersection) == 1:
            q = next(iter(intersection))
            edge = (('c', i), ('c', j), 1 << q,
                    {"kind": "check_check", "checks": (i, j), "qubit": q})
            edges.append(edge)
            adjacency[edge[0]].append(edge)
            adjacency[edge[1]].append(edge)

    degree = [0] * len(data)
    for _, qubits in checks:
        for q in qubits:
            degree[q] += 1

    for i, (_, qubits) in enumerate(checks):
        for q in qubits:
            if degree[q] != 1:
                continue
            x, y = data[q]
            sides = []
            if x == 0:
                sides.append('L')
            if x == max_coord:
                sides.append('R')
            if y == 0:
                sides.append('T')
            if y == max_coord:
                sides.append('B')
            for side in sides:
                edge = (('c', i), ('b', side), 1 << q,
                        {"kind": "check_boundary", "check": i,
                         "qubit": q, "side": side})
                edges.append(edge)
                adjacency[edge[0]].append(edge)
                adjacency[edge[1]].append(edge)
    return adjacency, edges


def other_endpoint(edge, node):
    return edge[1] if edge[0] == node else edge[0]


def all_shortest_paths(adjacency, src, dst):
    """Return every shortest path as (nodes, edges). Positive unit weights."""
    distances = {src: 0}
    queue = deque([src])
    while queue:
        u = queue.popleft()
        for edge in adjacency[u]:
            v = other_endpoint(edge, u)
            if v not in distances:
                distances[v] = distances[u] + 1
                queue.append(v)
    if dst not in distances:
        return []

    paths = []
    def visit(u, node_path, edge_path):
        if u == dst:
            paths.append((tuple(node_path), tuple(edge_path)))
            return
        for edge in adjacency[u]:
            v = other_endpoint(edge, u)
            if distances.get(v) == distances[u] + 1:
                visit(v, node_path + [v], edge_path + [edge])
    visit(src, [src], [])
    return paths


def xor_edge_masks(edges):
    mask = 0
    for edge in edges:
        mask ^= edge[2]
    return mask


def connection_catalog(adjacency, nchecks):
    catalog = {}
    for i, j in combinations(range(nchecks), 2):
        paths = all_shortest_paths(adjacency, ('c', i), ('c', j))
        catalog[('pair', i, j)] = [
            (xor_edge_masks(edge_path), node_path, edge_path)
            for node_path, edge_path in paths
        ]
    for i in range(nchecks):
        for side in ('T', 'B', 'L', 'R'):
            paths = all_shortest_paths(adjacency, ('c', i), ('b', side))
            catalog[('boundary', i, side)] = [
                (xor_edge_masks(edge_path), node_path, edge_path)
                for node_path, edge_path in paths
            ]
    return catalog


def exhaustive_shortest_path_search(syndrome: int, nchecks: int, catalog):
    """Exhaust all matchings and all shortest-path choices.

    Deduplication by final physical mask is an equivalence reduction only;
    it never prunes a distinct physical support. No graph-cost pruning occurs.
    """
    if syndrome == 0:
        return {0: ()}

    boundaries = ('T', 'B', 'L', 'R')

    @lru_cache(maxsize=None)
    def solve(remaining):
        if remaining == 0:
            return {0: ()}

        i = (remaining & -remaining).bit_length() - 1
        rest = remaining & ~(1 << i)
        masks = {}

        for j in range(i + 1, nchecks):
            if rest & (1 << j):
                for mask, node_path, edge_path in catalog[('pair', i, j)]:
                    for tail_mask, tail_provenance in solve(rest & ~(1 << j)).items():
                        masks.setdefault(
                            mask ^ tail_mask,
                            tail_provenance + (("pair", i, j, node_path, edge_path),),
                        )

        for side in boundaries:
            for mask, node_path, edge_path in catalog[('boundary', i, side)]:
                for tail_mask, tail_provenance in solve(rest).items():
                    masks.setdefault(
                        mask ^ tail_mask,
                        tail_provenance + (("boundary", i, side, node_path, edge_path),),
                    )
        return masks

    return solve(syndrome)
