"""Level 5: exact syndrome->minimum-physical-weight oracle by syndrome-space BFS.

Independent of src/decoder_lib_v2.py. Uses only canonical S0 incidence.

Method: the minimum weight of any error with syndrome s equals the shortest-path
distance from 0 to s in the Cayley graph on GF(2)^m whose generators are the
per-qubit syndrome columns h_q. This is exact (no heuristic cutoff, no pruning)
and costs O(2^m * n) instead of O(2^n).

d=3 is cross-checked against the exhaustive 2^n oracle from _level4_common.
"""
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.s0_geometry import build_unrotated_planar_surface_code
from tests._level4_common import make_check_masks, exhaustive_physical_oracle


def qubit_columns(code, sector):
    check_masks = make_check_masks(code, sector)
    cols = []
    for q in range(len(code["data"])):
        col = 0
        for c, m in enumerate(check_masks):
            if (m >> q) & 1:
                col |= 1 << c
        cols.append(col)
    return len(check_masks), cols


def bfs_min_weight(m, cols):
    size = 1 << m
    dist = np.full(size, -1, dtype=np.int16)
    dist[0] = 0
    frontier = np.array([0], dtype=np.int64)
    w = 0
    while frontier.size:
        w += 1
        nxt = []
        for col in cols:
            cand = frontier ^ col
            cand = cand[dist[cand] < 0]
            if cand.size:
                cand = np.unique(cand)
                dist[cand] = w
                nxt.append(cand)
        frontier = np.unique(np.concatenate(nxt)) if nxt else np.array([], dtype=np.int64)
    return dist


def main():
    # Cross-check at d=3 against the exhaustive physical oracle.
    code3 = build_unrotated_planar_surface_code(3)
    for sector in ("Z", "X"):
        m, cols = qubit_columns(code3, sector)
        dist = bfs_min_weight(m, cols)
        _, best, _ = exhaustive_physical_oracle(code3, sector)
        mism = sum(int(dist[s]) != best[s] for s in range(1 << m))
        print(f"CROSSCHECK d=3 sector={sector} syndromes={1<<m} mismatches={mism}")
        assert mism == 0

    for d in (5,):
        code = build_unrotated_planar_surface_code(d)
        n = len(code["data"])
        for sector in ("Z", "X"):
            m, cols = qubit_columns(code, sector)
            dist = bfs_min_weight(m, cols)
            assert (dist >= 0).all(), "unreachable syndrome (H not full row rank)"
            hist = np.bincount(dist)
            print(f"d={d} sector={sector} data_qubits={n} checks={m} "
                  f"syndromes={1<<m} max_min_weight={int(dist.max())}")
            print("  weight_histogram=" + ",".join(f"{w}:{int(c)}" for w, c in enumerate(hist)))
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
