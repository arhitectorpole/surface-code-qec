"""Level 5: combined decode()/decode_with_diagnostics() vs independent oracles.

d=3 (exhaustive): all 64*64 combined syndromes -> weight == oracle_Z + oracle_X,
  syndrome reproduced, determinism; per sector and per syndrome the witness set
  and logical classes equal the exhaustive oracle's set of ALL minimum-weight
  physical representatives (so also validates shortest-path sufficiency of the
  witness enumeration at d=3 for every syndrome).
d=5 (sampled): weight == BFS-oracle sum on SAMPLES random combined syndromes;
  for syndromes with oracle weight <= 3 per sector, witness set == brute-force
  set of all minimum-weight representatives.
"""
import sys, random
from itertools import combinations
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.s0_geometry import build_unrotated_planar_surface_code
from src.decoder_lib_v2 import (build_decoding_graph, decode, decode_with_diagnostics,
                                verify_correction, build_sector_graph,
                                decode_sector_with_diagnostics)
from tests._level4_common import exhaustive_physical_oracle, popcount
from tests.level5_syndrome_bfs_oracle import qubit_columns, bfs_min_weight

SAMPLES = 400
BRUTE_SYNDROMES = 60
SEED = 20261023


def sector_logical_masks(code):
    data = code["data"]
    return {"Z": sum(1 << q for q, (x, y) in enumerate(data) if y == 0),
            "X": sum(1 << q for q, (x, y) in enumerate(data) if x == 0)}


def main():
    fails = []
    # ---- d=3 exhaustive
    code3 = build_unrotated_planar_surface_code(3)
    g3 = build_decoding_graph(3)
    lm3 = sector_logical_masks(code3)
    assert lm3["Z"] == g3.logZ_mask
    oracle3 = {s: exhaustive_physical_oracle(code3, s) for s in "ZX"}
    n_z = len(code3["z_checks"])
    sg3 = {s: build_sector_graph(3, s) for s in "ZX"}
    set_checks = 0
    for sector in "ZX":
        _, best, reps = oracle3[sector]
        for syn in range(1 << n_z):
            _, diag = decode_sector_with_diagnostics(syn, sg3[sector], lm3[sector])
            set_checks += 1
            classes = frozenset(popcount(m & lm3[sector]) & 1 for m in reps[syn])
            if (diag.witness_masks != frozenset(reps[syn]) or diag.logical_classes != classes
                    or diag.matchings_truncated or diag.witnesses_truncated):
                fails.append(("witness_set", sector, syn))
    combined = 0
    for syn in range(1 << g3.n_checks):
        z, x = syn & ((1 << n_z) - 1), syn >> n_z
        r = decode(syn, g3)
        r2 = decode(syn, g3)
        combined += 1
        if (r != r2 or r.correction.syndrome_reproduced != syn
                or not verify_correction(syn, r.correction, g3)
                or r.correction.weight != oracle3["Z"][1][z] + oracle3["X"][1][x]
                or r.mwpm_weight != r.correction.weight):
            fails.append(("combined", syn))
    # diagnostics at the combined level for a sample of syndromes
    for syn in (0, 1, 405, 4095, 2730, 1365):
        r = decode_with_diagnostics(syn, g3)
        z = syn & ((1 << n_z) - 1)
        exp = frozenset(popcount(m & g3.logZ_mask) & 1 for m in oracle3["Z"][2][z])
        if r.degeneracy.sectors_present != set(exp) or r.degeneracy.is_logical_tie != (len(exp) > 1):
            fails.append(("combined_diag", syn))
    print(f"d=3 sector_witness_set_checks={set_checks} combined_syndromes={combined}")

    # ---- d=5 sampled
    code5 = build_unrotated_planar_surface_code(5)
    g5 = build_decoding_graph(5)
    lm5 = sector_logical_masks(code5)
    sg5 = {s: build_sector_graph(5, s) for s in "ZX"}
    cols, oracle5 = {}, {}
    for s in "ZX":
        m, cols[s] = qubit_columns(code5, s)
        oracle5[s] = bfs_min_weight(m, cols[s])
    n_z5 = len(code5["z_checks"])
    rng = random.Random(SEED)
    n = g5.n_data
    for _ in range(SAMPLES):
        syns = {}
        for s in "ZX":
            sy = 0
            for q in rng.sample(range(n), rng.randint(0, 6)):
                sy ^= cols[s][q]
            syns[s] = sy
        syn = syns["Z"] | (syns["X"] << n_z5)
        r = decode(syn, g5)
        if (r.correction.syndrome_reproduced != syn
                or r.correction.weight != int(oracle5["Z"][syns["Z"]]) + int(oracle5["X"][syns["X"]])
                or r != decode(syn, g5)):
            fails.append(("d5_combined", syn))
    brute = 0
    trunc = 0
    for s in "ZX":
        picked = 0
        attempts = 0
        while picked < BRUTE_SYNDROMES and attempts < 100000:
            attempts += 1
            qs = rng.sample(range(n), rng.randint(1, 3))
            sy = 0
            for q in qs:
                sy ^= cols[s][q]
            w = int(oracle5[s][sy])
            if w > 3:
                continue
            truth = set()
            for combo in combinations(range(n), w):
                v = 0
                for q in combo:
                    v ^= cols[s][q]
                if v == sy:
                    truth.add(sum(1 << q for q in combo))
            _, diag = decode_sector_with_diagnostics(sy, sg5[s], lm5[s])
            trunc += int(diag.matchings_truncated or diag.witnesses_truncated)
            brute += 1
            picked += 1
            if diag.witness_masks != frozenset(truth):
                fails.append(("d5_witness_set", s, sy))
    print(f"d=5 combined_samples={SAMPLES} brute_force_witness_set_checks={brute} truncated={trunc}")
    print(f"TOTAL_FAILURES={len(fails)}")
    for f in fails[:5]:
        print("FAIL", f)
    print("RESULT: " + ("PASS" if not fails else "FAIL"))
    return len(fails)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
