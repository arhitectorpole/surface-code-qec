"""Level 5: exact logical failure rates under i.i.d. single-type errors.

Model: each data qubit flips independently with probability p (X-type errors seen
by the Z-sector checks; Z-type errors for the X sector are the mirror problem).
Failure = decoder's chosen logical class != true class of the error.

Exact method: the joint distribution P(syndrome, class) is the convolution over
qubits of ((1-p)*delta_0 + p*delta_g_q) in GF(2)^(m+1); via Walsh-Hadamard
transform, Fhat(k) = (1-2p)^t(k), t(k) = #{q : <k,g_q> odd}. No sampling.

Decoder rules compared (all exact, using the independent oracle class distances):
  MLD            : per syndrome choose the class with larger P  (optimal decoder)
  MW-best-tie    : minimum weight class; on ties choose the likelier class
  MW-random-tie  : minimum weight class; ties broken by a fair coin
  MW-worst-tie   : minimum weight class; on ties choose the less likely class
The library decoder (deterministic tie rule) is checked exactly at d=3 and by
Monte Carlo at d=5; it must lie within [MW-best-tie, MW-worst-tie].
d=3 WHT results are cross-checked against brute-force enumeration of all 2^13 masks.
"""
import sys, random, math
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.s0_geometry import build_unrotated_planar_surface_code
from src.decoder_lib_v2 import build_sector_graph, decode_sector
from tests._level4_common import popcount
from tests.level5_logical_tie_census import class_distances, logical_mask

P_GRID = [0.001, 0.003, 0.01, 0.02, 0.03, 0.05, 0.08, 0.10, 0.15]
MC_P = [0.03, 0.05, 0.10]
MC_SAMPLES = 3000
SEED = 20261025


def parity_of(x):
    x = x ^ (x >> 16)
    x ^= x >> 8
    x ^= x >> 4
    x ^= x >> 2
    x ^= x >> 1
    return x & 1


def wht(a):
    a = a.copy()
    n = a.size
    h = 1
    while h < n:
        a = a.reshape(-1, 2, h)
        x = a[:, 0, :] + a[:, 1, :]
        y = a[:, 0, :] - a[:, 1, :]
        a = np.stack([x, y], axis=1).reshape(-1)
        h *= 2
    return a


def odd_counts(m, cols, lm):
    ext = [(c << 1) | ((lm >> q) & 1) for q, c in enumerate(cols)]
    k = np.arange(1 << (m + 1), dtype=np.int64)
    t = np.zeros(k.size, dtype=np.int16)
    for g in ext:
        t += parity_of(k & g).astype(np.int16)
    return t


def joint(t, p):
    f = (1.0 - 2.0 * p) ** t.astype(np.float64)
    P = wht(f) / f.size
    P = np.clip(P, 0.0, None)
    return P.reshape(-1, 2)  # [syndrome, class]


def rates(P, dist):
    tie = dist[:, 0] == dist[:, 1]
    mw_class = np.argmin(dist, axis=1)
    idx = np.arange(P.shape[0])
    wrong_mw = P[idx, 1 - mw_class]
    out = {}
    out["MLD"] = float(P.min(axis=1).sum())
    pmin = P.min(axis=1)
    pmax = P.max(axis=1)
    out["MW-best"] = float(np.where(tie, pmin, wrong_mw).sum())
    out["MW-random"] = float(np.where(tie, 0.5 * (pmin + pmax), wrong_mw).sum())
    out["MW-worst"] = float(np.where(tie, pmax, wrong_mw).sum())
    return out, float(P.sum())


def brute_joint_d3(code, sector, p):
    from tests.level5_syndrome_bfs_oracle import qubit_columns
    m, cols = qubit_columns(code, sector)
    lm = logical_mask(code, sector)
    n = len(code["data"])
    P = np.zeros((1 << m, 2))
    for mask in range(1 << n):
        s = 0
        for q in range(n):
            if (mask >> q) & 1:
                s ^= cols[q]
        w = popcount(mask)
        P[s, popcount(mask & lm) & 1] += p ** w * (1 - p) ** (n - w)
    return P


def main():
    fails = 0
    code3 = build_unrotated_planar_surface_code(3)
    code5 = build_unrotated_planar_surface_code(5)
    results = {}
    for d, code in ((3, code3), (5, code5)):
        for sector in "ZX":
            m, cols, lm, dist = class_distances(code, sector)
            t = odd_counts(m, cols, lm)
            results[(d, sector)] = (m, cols, lm, dist, t)

    # brute-force cross-check of the WHT method at d=3
    for sector in "ZX":
        m, cols, lm, dist, t = results[(3, sector)]
        for p in (0.01, 0.1):
            err = float(np.abs(joint(t, p) - brute_joint_d3(code3, sector, p)).max())
            print(f"CROSSCHECK d=3 sector={sector} p={p} max_abs_diff_vs_bruteforce={err:.2e}")
            if err > 1e-12:
                fails += 1

    table = {}
    for d in (3, 5):
        for sector in "ZX":
            m, cols, lm, dist, t = results[(d, sector)]
            for p in P_GRID:
                r, tot = rates(joint(t, p), dist)
                if abs(tot - 1.0) > 1e-9:
                    fails += 1
                table[(d, sector, p)] = r
        zx = max(abs(table[(d, "Z", p)][k] - table[(d, "X", p)][k])
                 for p in P_GRID for k in table[(d, "Z", p)])
        print(f"d={d} Z-vs-X max_abs_difference_in_failure_rates={zx:.2e}")
        print(f"d={d} exact logical failure rate (sector Z; X identical)")
        print("  p       MLD         MW-best     MW-random   MW-worst")
        for p in P_GRID:
            r = table[(d, "Z", p)]
            print(f"  {p:<6} {r['MLD']:.6e} {r['MW-best']:.6e} {r['MW-random']:.6e} {r['MW-worst']:.6e}")
        for key in ("MLD", "MW-random", "MW-worst"):
            a, b = table[(d, "Z", 0.001)][key], table[(d, "Z", 0.003)][key]
            slope = math.log(b / a) / math.log(0.003 / 0.001)
            print(f"  low-p log-log slope ({key}, p=0.001..0.003): {slope:.2f}")
        for p in P_GRID:
            r = table[(d, "Z", p)]
            if not (r["MLD"] <= r["MW-best"] + 1e-15 <= r["MW-random"] + 1e-15 <= r["MW-worst"] + 1e-15):
                fails += 1

    # Library decoder: exact at d=3, Monte Carlo at d=5 (sector Z)
    m, cols, lm, dist, t = results[(3, "Z")]
    g3 = build_sector_graph(3, "Z")
    dec_class = np.array([popcount(decode_sector(s, g3).bitmask & lm) & 1 for s in range(1 << m)])
    for p in (0.01, 0.05, 0.1):
        P = joint(t, p)
        exact = float(P[np.arange(P.shape[0]), 1 - dec_class].sum())
        r = table[(3, "Z", p)] if p in P_GRID else rates(P, dist)[0]
        ok = r["MW-best"] - 1e-15 <= exact <= r["MW-worst"] + 1e-15
        print(f"d=3 library decoder exact failure p={p}: {exact:.6e} within[best,worst]=[{r['MW-best']:.6e},{r['MW-worst']:.6e}] {ok}")
        fails += int(not ok)

    m, cols, lm, dist, t = results[(5, "Z")]
    g5 = build_sector_graph(5, "Z")
    rng = random.Random(SEED)
    n = g5.n_data
    for p in MC_P:
        bad = 0
        for _ in range(MC_SAMPLES):
            e = 0
            s = 0
            for q in range(n):
                if rng.random() < p:
                    e |= 1 << q
                    s ^= cols[q]
            c = decode_sector(s, g5)
            if (popcount(e & lm) & 1) != (popcount(c.bitmask & lm) & 1):
                bad += 1
        est = bad / MC_SAMPLES
        se = math.sqrt(max(est * (1 - est), 1e-12) / MC_SAMPLES)
        r = table[(5, "Z", p)]
        ok = (r["MW-best"] - 4 * se) <= est <= (r["MW-worst"] + 4 * se)
        print(f"d=5 library decoder Monte Carlo p={p}: {est:.4f} +- {se:.4f} (n={MC_SAMPLES}); "
              f"exact bounds [{r['MW-best']:.4f}, {r['MW-worst']:.4f}], MLD={r['MLD']:.4f} within={ok}")
        fails += int(not ok)

    print(f"TOTAL_FAILURES={fails}")
    print("RESULT: " + ("PASS" if fails == 0 else "FAIL"))
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
