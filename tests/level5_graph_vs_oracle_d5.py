"""Level 5: d=5 graph-contract check against the exact syndrome-BFS oracle.

Part A (structural, all 2^20 syndromes per sector):
  - every physical qubit appears as >=1 graph edge, and every graph edge for
    qubit q flips exactly the checks in q's syndrome column (check-check edge:
    the two checks; check-boundary edge: the single check);
  - therefore the T-join (edge-set) minimum over the GRAPH equals the physical
    oracle weight for every syndrome (BFS with graph-edge generators == BFS with
    qubit-column generators).
Part B (empirical, random samples): exact minimum-cost matching (check-check
  shortest-path distances, nearest-boundary distances, exact bitmask DP) equals
  the oracle weight. Since min-cost matching == min T-join, any tie-broken
  shortest-path choice XORs to a mask of weight <= cost == oracle minimum, and
  validity forces equality.
"""
import sys, random
from functools import lru_cache
from collections import deque
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.s0_geometry import build_unrotated_planar_surface_code
from tests._level4_common import graph_construction
from tests.level5_syndrome_bfs_oracle import qubit_columns, bfs_min_weight

SAMPLES = 2000
SEED = 20260922


def graph_generators(code, sector, edges, m):
    """Per-edge syndrome column (bitmask over checks) and the qubit it carries."""
    gens = []
    for u, v, mask, info in edges:
        col = 0
        for node in (u, v):
            if node[0] == 'c':
                col ^= 1 << node[1]
        gens.append((mask.bit_length() - 1, col))
    return gens


def pair_and_boundary_dist(adjacency, m):
    nodes = list(adjacency)
    def bfs(src):
        d = {src: 0}
        q = deque([src])
        while q:
            u = q.popleft()
            for e in adjacency[u]:
                v = e[1] if e[0] == u else e[0]
                if v not in d:
                    d[v] = d[u] + 1
                    q.append(v)
        return d
    D = [[0] * m for _ in range(m)]
    B = [0] * m
    for i in range(m):
        d = bfs(('c', i))
        for j in range(m):
            D[i][j] = d[('c', j)]
        B[i] = min(d[('b', s)] for s in ('T', 'B', 'L', 'R'))
    return D, B


def mwpm_cost(defects, D, B):
    @lru_cache(maxsize=None)
    def solve(rem):
        if rem == 0:
            return 0
        i = (rem & -rem).bit_length() - 1
        rest = rem & ~(1 << i)
        best = B[defects[i]] + solve(rest)
        r = rest
        while r:
            j = (r & -r).bit_length() - 1
            r &= r - 1
            c = D[defects[i]][defects[j]] + solve(rest & ~(1 << j))
            if c < best:
                best = c
        return best
    return solve((1 << len(defects)) - 1)


def main():
    d = 5
    code = build_unrotated_planar_surface_code(d)
    n = len(code["data"])
    rng = random.Random(SEED)
    total_fail = 0
    for sector in ("Z", "X"):
        m, cols = qubit_columns(code, sector)
        adjacency, edges = graph_construction(code, sector)
        gens = graph_generators(code, sector, edges, m)

        # A1: edge <-> qubit column consistency and coverage.
        covered = set()
        bad = 0
        for q, col in gens:
            covered.add(q)
            if col != cols[q]:
                bad += 1
        uncovered = n - len(covered)

        # A2: graph-generator BFS == physical oracle for all 2^m syndromes.
        oracle = bfs_min_weight(m, cols)
        graph_cols = sorted({col for _, col in gens})
        gdist = bfs_min_weight(m, graph_cols)
        mism = int((gdist != oracle).sum())

        # B: exact MWPM cost on random errors.
        D, B = pair_and_boundary_dist(adjacency, m)
        bfail = 0
        maxdef = 0
        for _ in range(SAMPLES):
            w = rng.randint(1, 6)
            qs = rng.sample(range(n), w)
            s = 0
            for q in qs:
                s ^= cols[q]
            defects = tuple(i for i in range(m) if (s >> i) & 1)
            maxdef = max(maxdef, len(defects))
            if mwpm_cost(defects, D, B) != int(oracle[s]):
                bfail += 1
        print(f"d={d} sector={sector} graph_edges={len(edges)} "
              f"column_mismatch_edges={bad} uncovered_qubits={uncovered} "
              f"graph_vs_oracle_syndrome_mismatches={mism}/{1<<m} "
              f"mwpm_samples={SAMPLES} max_defects={maxdef} mwpm_failures={bfail}")
        total_fail += bad + uncovered + mism + bfail
    print(f"TOTAL_FAILURES={total_fail}")
    print("RESULT: " + ("PASS" if total_fail == 0 else "FAIL"))
    return total_fail


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
