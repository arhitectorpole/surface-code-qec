"""Level 5: exhaustive check of decode_sector_majority over EVERY d=5 logical tie.

Usage: python tests/level5_tie_rule_exhaustive_d5.py Z|X

Reference (independent of the decoder's matching/path enumeration): exact counts
N_w(s, c) of weight-w errors per (syndrome, class) from an integer Walsh-Hadamard
transform (see level5_tie_rule_majority.py). For every tie syndrome s (dist[s,0] ==
dist[s,1] == w) the library result must satisfy:
  * no enumeration truncation (truncated == False) and num_matchings < MAX_MATCHINGS;
  * (count_class0, count_class1) == (N_w(s,0), N_w(s,1));
  * N_w(s,0) != N_w(s,1): chosen class == argmax, tie_decided_by_count is True;
    N_w(s,0) == N_w(s,1): correction equals the default decode_sector() correction;
  * returned correction reproduces the syndrome and has weight w.
Any violation is a FAIL; the number of ties checked must equal the census (481946).
This checks agreement with the count-based reference. It does not prove optimality
relative to MLD (that is the separate exact-rate comparison).
"""
import sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.s0_geometry import build_unrotated_planar_surface_code
from src.decoder_lib_v2 import (build_sector_graph, decode_sector, decode_sector_majority,
                                syndrome_of_sector_mask, MAX_MATCHINGS)
from tests._level4_common import popcount
from tests.level5_logical_tie_census import class_distances
from tests.level5_logical_failure_exact import odd_counts
from tests.level5_tie_rule_majority import count_tables, WMAX

EXPECTED_TIES_D5 = 481946


def main(sector):
    code = build_unrotated_planar_surface_code(5)
    m, cols, lm, dist = class_distances(code, sector)
    t = odd_counts(m, cols, lm)
    N = count_tables(t, len(code["data"]), WMAX)
    ties = np.flatnonzero(dist[:, 0] == dist[:, 1])
    g = build_sector_graph(5, sector)
    viol = {"truncated": 0, "matchings_at_cap": 0, "counts": 0, "class": 0,
            "decided_flag": 0, "fallback": 0, "syndrome": 0, "weight": 0}
    decided = equal = 0
    max_match = max_total = 0
    t0 = time.time()
    for i, s in enumerate(ties):
        s = int(s)
        w = int(dist[s, 0])
        n0, n1 = int(N[w][s, 0]), int(N[w][s, 1])
        r = decode_sector_majority(s, g, lm)
        max_match = max(max_match, r.num_matchings)
        max_total = max(max_total, n0 + n1)
        if r.truncated:
            viol["truncated"] += 1
            continue
        if r.num_matchings >= MAX_MATCHINGS:
            viol["matchings_at_cap"] += 1
        if (r.count_class0, r.count_class1) != (n0, n1):
            viol["counts"] += 1
        if syndrome_of_sector_mask(g, r.bitmask) != s or r.syndrome_reproduced != s:
            viol["syndrome"] += 1
        if popcount(r.bitmask) != w or r.weight != w:
            viol["weight"] += 1
        if n0 != n1:
            decided += 1
            if (popcount(r.bitmask & lm) & 1) != (1 if n1 > n0 else 0):
                viol["class"] += 1
            if not r.tie_decided_by_count:
                viol["decided_flag"] += 1
        else:
            equal += 1
            if r.bitmask != decode_sector(s, g).bitmask or r.tie_decided_by_count:
                viol["fallback"] += 1
        if (i + 1) % 50000 == 0:
            print(f"  progress {i+1}/{len(ties)} ({time.time()-t0:.0f}s) violations={sum(viol.values())}", flush=True)
    total_viol = sum(viol.values()) + int(len(ties) != EXPECTED_TIES_D5)
    print(f"EXHAUSTIVE d=5 sector={sector} ties_checked={len(ties)} (census {EXPECTED_TIES_D5}) "
          f"decided_by_count={decided} equal_count_fallback={equal}")
    print(f"  max_optimal_matchings_enumerated={max_match} (cap {MAX_MATCHINGS}); "
          f"max_min_weight_errors_at_tie={max_total}")
    print("  violations: " + ", ".join(f"{k}={v}" for k, v in viol.items()))
    print(f"TOTAL_FAILURES={total_viol}")
    print("RESULT: " + ("PASS" if total_viol == 0 else "FAIL"))
    return total_viol


if __name__ == "__main__":
    sec = sys.argv[1] if len(sys.argv) > 1 else "Z"
    assert sec in ("Z", "X")
    sys.exit(1 if main(sec) else 0)
