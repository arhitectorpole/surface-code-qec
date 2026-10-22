"""Level 5: decoder_lib_v2.decode_sector vs the exact oracles.

d=3: every sector-local syndrome (64 per sector) vs the exhaustive 2^n oracle.
d=5: all syndromes reachable from errors of weight <= 6 sampled at random
     (SAMPLES per sector) vs the BFS oracle.
Checks: syndrome reproduced, physical weight == oracle minimum, matching cost ==
physical weight lower bound (cost >= weight), determinism (decode twice).
"""
import sys, random
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.s0_geometry import build_unrotated_planar_surface_code
from src.decoder_lib_v2 import build_sector_graph, decode_sector
from tests._level4_common import exhaustive_physical_oracle
from tests.level5_syndrome_bfs_oracle import qubit_columns, bfs_min_weight

SAMPLES = 1500
SEED = 20261022


def check(graph, syndrome, truth, failures):
    a = decode_sector(syndrome, graph)
    b = decode_sector(syndrome, graph)
    ok = (a == b and a.syndrome_reproduced == syndrome
          and a.weight == truth and a.matching_cost >= a.weight)
    if not ok:
        failures.append((graph.sector, syndrome, truth, a))


def main():
    total = 0
    fails = []
    for sector in ("Z", "X"):
        code = build_unrotated_planar_surface_code(3)
        g = build_sector_graph(3, sector)
        _, best, _ = exhaustive_physical_oracle(code, sector)
        for s in range(1 << g.n_checks):
            check(g, s, best[s], fails)
            total += 1
        print(f"d=3 sector={sector} exhaustive_syndromes={1 << g.n_checks}")
    rng = random.Random(SEED)
    for sector in ("Z", "X"):
        code = build_unrotated_planar_surface_code(5)
        g = build_sector_graph(5, sector)
        m, cols = qubit_columns(code, sector)
        oracle = bfs_min_weight(m, cols)
        for _ in range(SAMPLES):
            qs = rng.sample(range(g.n_data), rng.randint(1, 6))
            s = 0
            for q in qs:
                s ^= cols[q]
            check(g, s, int(oracle[s]), fails)
            total += 1
        print(f"d=5 sector={sector} sampled_syndromes={SAMPLES}")
    print(f"TOTAL_CASES={total} TOTAL_FAILURES={len(fails)}")
    for f in fails[:5]:
        print("FAIL", f)
    print("RESULT: " + ("PASS" if not fails else "FAIL"))
    return len(fails)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
