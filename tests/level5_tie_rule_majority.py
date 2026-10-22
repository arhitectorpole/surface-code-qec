"""Level 5: exact evaluation of count-based logical tie rules vs MLD.

Idea: on a logical tie (both classes have the same minimum weight w) the class
with more weight-w errors is the likelier one at leading order in p
(P(s,c) = N_w(s,c) p^w (1-p)^(n-w) + higher order). Rules compared:

  MAJ        : at the tie weight w choose the class with larger N_w(s,c);
               equal counts -> fair coin (average of both classes)
  MAJ-deep   : compare (N_w, N_{w+1}, ..., N_WMAX) lexicographically;
               still equal -> fair coin
  plus MLD / MW-best / MW-random / MW-worst from level5_logical_failure_exact.py.

N_w(s,c) = number of physical errors of weight w with syndrome s and logical
class c. Exact: coefficient of x^w in prod_q ((1+x) or (1-x)) per Walsh-Hadamard
character, inverse WHT in int64 (no sampling, no floating point for counts).

Library cross-check: decode_sector_majority (src/decoder_lib_v2.py) must pick the
same class as MAJ on every d=3 syndrome and on sampled d=5 tie syndromes, and its
witness counts must equal N_w (tests witness completeness).
"""
import sys, random, math
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.s0_geometry import build_unrotated_planar_surface_code
from src.decoder_lib_v2 import build_sector_graph, decode_sector_majority
from tests._level4_common import popcount
from tests.level5_logical_tie_census import class_distances
from tests.level5_logical_failure_exact import joint, odd_counts, P_GRID, rates

WMAX = 14
SEED = 20261026
SAMPLES_D5 = 400


def ihwt(a):
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


def count_tables(t, n, wmax):
    """N[w] has shape (2^m, 2): number of weight-w errors per (syndrome, class)."""
    size = t.size
    # per-t polynomial coefficients of (1+x)^(n-t) (1-x)^t, degree <= wmax
    coef = np.zeros((n + 1, wmax + 1), dtype=np.int64)
    for tt in range(n + 1):
        poly = np.array([1], dtype=object)
        for _ in range(n - tt):
            poly = np.convolve(poly, [1, 1])
        for _ in range(tt):
            poly = np.convolve(poly, [1, -1])
        for w in range(min(wmax, len(poly) - 1) + 1):
            coef[tt, w] = int(poly[w])
    out = []
    for w in range(wmax + 1):
        f = coef[t.astype(np.int64), w]
        N = ihwt(f)
        assert (N % size == 0).all()
        out.append((N // size).reshape(-1, 2))
    return out


def failure_rate_choice(P, choice_prob_class1, tie_mask, dist):
    """Exact failure for a rule: on ties use P(choose class1)=choice_prob_class1;
    off ties choose the minimum-weight class."""
    mw_class = np.argmin(dist, axis=1)
    idx = np.arange(P.shape[0])
    wrong_mw = P[idx, 1 - mw_class]
    wrong_tie = choice_prob_class1 * P[:, 0] + (1 - choice_prob_class1) * P[:, 1]
    return float(np.where(tie_mask, wrong_tie, wrong_mw).sum())


def maj_prob(N, dist, deep):
    """P(choose class 1) on tie syndromes (0.5 when undecided)."""
    size = dist.shape[0]
    mn = dist.min(axis=1)
    p1 = np.full(size, 0.5)
    decided = np.zeros(size, dtype=bool)
    for k in range(WMAX + 1 if deep else 1):
        w = mn + k
        ok = w <= WMAX
        wc = np.clip(w, 0, WMAX)
        c0 = np.zeros(size, dtype=np.int64)
        c1 = np.zeros(size, dtype=np.int64)
        for ww in range(WMAX + 1):
            sel = ok & (wc == ww)
            c0[sel] = N[ww][sel, 0]
            c1[sel] = N[ww][sel, 1]
        new = (~decided) & ok & (c0 != c1)
        p1[new] = (c1[new] > c0[new]).astype(float)
        decided |= new
    return p1, decided


def main():
    fails = 0
    code3 = build_unrotated_planar_surface_code(3)
    code5 = build_unrotated_planar_surface_code(5)
    rng = random.Random(SEED)
    for d, code in ((3, code3), (5, code5)):
        for sector in "ZX":
            m, cols, lm, dist = class_distances(code, sector)
            t = odd_counts(m, cols, lm)
            n = len(code["data"])
            N = count_tables(t, n, WMAX)
            tie = dist[:, 0] == dist[:, 1]
            p1_maj, dec1 = maj_prob(N, dist, deep=False)
            p1_deep, dec2 = maj_prob(N, dist, deep=True)
            nt = int(tie.sum())
            print(f"d={d} sector={sector} ties={nt} undecided_by_MAJ={int((tie & ~dec1).sum())} "
                  f"undecided_by_MAJ-deep={int((tie & ~dec2).sum())}")
            # sanity: counts at min weight positive, and sum over all w reproduces 2^n
            if d == 3:
                tot = sum(int(x.sum()) for x in N)
                if tot != 1 << n:
                    print("  count total mismatch", tot, 1 << n)
                    fails += 1
            if sector == "Z":
                print("  p        MLD          MW-best      MAJ          MAJ-deep     MW-random    MW-worst")
                for p in P_GRID:
                    P = joint(t, p)
                    r, _ = rates(P, dist)
                    maj = failure_rate_choice(P, p1_maj, tie, dist)
                    deep = failure_rate_choice(P, p1_deep, tie, dist)
                    print(f"  {p:<7} {r['MLD']:.6e} {r['MW-best']:.6e} {maj:.6e} {deep:.6e} "
                          f"{r['MW-random']:.6e} {r['MW-worst']:.6e}   "
                          f"MAJ/MLD={maj / r['MLD']:.4f} deep/MLD={deep / r['MLD']:.4f} "
                          f"random/MLD={r['MW-random'] / r['MLD']:.4f}")
                    if maj < r["MW-best"] - 1e-15 or maj > r["MW-worst"] + 1e-15:
                        fails += 1
            # library cross-check
            g = build_sector_graph(d, sector)
            if d == 3:
                syns = [s for s in range(1 << m) if tie[s]]
            else:
                tie_idx = np.flatnonzero(tie)
                syns = [int(s) for s in rng.sample(list(tie_idx), SAMPLES_D5)]
            bad = trunc = undec = cnt_bad = 0
            for s in syns:
                res = decode_sector_majority(s, g, lm)
                trunc += int(res.truncated)
                if res.truncated:
                    continue
                w = int(dist[s, 0])
                n0, n1 = int(N[w][s, 0]), int(N[w][s, 1])
                if (res.count_class0, res.count_class1) != (n0, n1):
                    cnt_bad += 1
                if n0 == n1:
                    undec += 1
                    continue
                want = 1 if n1 > n0 else 0
                if (popcount(res.bitmask & lm) & 1) != want:
                    bad += 1
            print(f"  LIBRARY-CHECK d={d} sector={sector} tie_syndromes_checked={len(syns)} "
                  f"truncated={trunc} equal_count={undec} class_mismatches={bad} witness_count_mismatches={cnt_bad}")
            fails += bad + cnt_bad
    print(f"TOTAL_FAILURES={fails}")
    print("RESULT: " + ("PASS" if fails == 0 else "FAIL"))
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
