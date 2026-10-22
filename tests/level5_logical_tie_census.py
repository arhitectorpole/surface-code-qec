"""Level 5: exact logical-tie census at d=5 (and d=3 cross-check).

Method: BFS over the extended space (syndrome, logical-class bit). Each qubit
generator flips its syndrome column and, if the qubit lies in the logical mask,
the class bit. dist[s, c] = minimum physical weight of any error with syndrome s
and logical class c (exact, no pruning). A syndrome is a logical tie iff
dist[s,0] == dist[s,1]; otherwise the minimum class is unique.

Cross-checks:
  * d=3 against the exhaustive 2^n oracle (all syndromes, both sectors);
  * d=5 against decoder_lib_v2.decode_with_diagnostics on random syndromes
    (is_logical_tie / logical classes of the decoder's witnesses).
"""
import sys, random
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.s0_geometry import build_unrotated_planar_surface_code
from src.decoder_lib_v2 import build_sector_graph, decode_sector_with_diagnostics
from tests._level4_common import exhaustive_physical_oracle, popcount
from tests.level5_syndrome_bfs_oracle import qubit_columns, bfs_min_weight

SEED = 20261024
SAMPLES = 300


def logical_mask(code, sector):
    d = code["data"]
    return sum(1 << q for q, (x, y) in enumerate(d) if (y == 0 if sector == "Z" else x == 0))


def class_distances(code, sector):
    m, cols = qubit_columns(code, sector)
    lm = logical_mask(code, sector)
    ext = [(c << 1) | ((lm >> q) & 1) for q, c in enumerate(cols)]
    dist = bfs_min_weight(m + 1, ext)
    return m, cols, lm, dist.reshape(-1, 2)  # [syndrome, class]


def main():
    fails = 0
    # d=3 exhaustive cross-check
    code3 = build_unrotated_planar_surface_code(3)
    for sector in "ZX":
        m, cols, lm, dist = class_distances(code3, sector)
        _, best, reps = exhaustive_physical_oracle(code3, sector)
        bad = 0
        for s in range(1 << m):
            classes = {popcount(r & lm) & 1 for r in reps[s]}
            tie = int(dist[s, 0]) == int(dist[s, 1])
            if tie != (len(classes) == 2) or min(int(dist[s, 0]), int(dist[s, 1])) != best[s]:
                bad += 1
        print(f"CROSSCHECK d=3 sector={sector} syndromes={1<<m} mismatches={bad}")
        fails += bad

    code5 = build_unrotated_planar_surface_code(5)
    rng = random.Random(SEED)
    for sector in "ZX":
        m, cols, lm, dist = class_distances(code5, sector)
        mn = dist.min(axis=1)
        tie = dist[:, 0] == dist[:, 1]
        gap = np.abs(dist[:, 0].astype(int) - dist[:, 1].astype(int))
        total = 1 << m
        print(f"d=5 sector={sector} syndromes={total} logical_ties={int(tie.sum())} "
              f"tie_fraction={tie.sum()/total:.6f}")
        print("  by_min_weight(w: ties/total) " + ", ".join(
            f"{w}:{int(tie[mn==w].sum())}/{int((mn==w).sum())}" for w in range(int(mn.max()) + 1)))
        print("  class_gap_histogram(gap:count) " + ", ".join(
            f"{g}:{int((gap==g).sum())}" for g in range(int(gap.max()) + 1)))
        # decoder cross-check on samples
        g = build_sector_graph(5, sector)
        bad = 0
        trunc = 0
        n = g.n_data
        for _ in range(SAMPLES):
            sy = 0
            for q in rng.sample(range(n), rng.randint(0, 6)):
                sy ^= cols[q]
            _, diag = decode_sector_with_diagnostics(sy, g, lm)
            trunc += int(diag.matchings_truncated or diag.witnesses_truncated)
            exp_tie = bool(dist[sy, 0] == dist[sy, 1])
            exp_classes = frozenset({0, 1}) if exp_tie else frozenset({int(np.argmin(dist[sy]))})
            if diag.logical_classes != exp_classes or diag.is_logical_tie != exp_tie:
                bad += 1
        print(f"  decoder_crosscheck samples={SAMPLES} mismatches={bad} truncated={trunc}")
        fails += bad
    print(f"TOTAL_FAILURES={fails}")
    print("RESULT: " + ("PASS" if fails == 0 else "FAIL"))
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
