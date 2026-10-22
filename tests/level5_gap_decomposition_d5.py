"""Level 5: where does the remaining gap between the count-based tie rule (MAJ) and MLD come from? (d=5)

Probabilities: for p <= 0.02 from exact integer counts, P(s,c) = sum_w N_w(s,c) p^w (1-p)^(n-w)
(w <= WMAX; missing mass < 1e-14), which has no cancellation; the Walsh-Hadamard joint() in
float64 has ~1e-17 absolute noise and misclassifies syndromes whose probabilities are ~1e-21
at p=0.001. For p >= 0.05 joint() is used (probabilities large, noise irrelevant).

Excess(s) = P[chosen class wrong] - min_c P(s,c); MLD = sum_s min_c P(s,c). Categories:
non-tie (minimum-weight class != MLD class), decided tie (count rule picks wrong class),
undecided tie (equal counts at the tie weight, scored as a fair coin).

Asserted: (1) at p <= 0.003 the count rule never disagrees with the MLD class on a decided tie;
(2) at p <= 0.02 the deep rule is within 1e-4 of MLD; (3) Z and X sectors give identical counts of
disagreements; (4) WHT-based and count-based MLD agree to 1e-6 (relative) for p <= 0.02;
(5) categories sum to the total excess.
"""
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.s0_geometry import build_unrotated_planar_surface_code
from tests.level5_logical_tie_census import class_distances
from tests.level5_logical_failure_exact import joint, odd_counts
from tests.level5_tie_rule_majority import count_tables, maj_prob, failure_rate_choice, WMAX

P_LIST = [0.001, 0.003, 0.01, 0.02, 0.05, 0.1]


def main():
    fails = 0
    code = build_unrotated_planar_surface_code(5)
    n = len(code["data"])
    dis_by_sector = {}
    for sec in "ZX":
        m, cols, lm, dist = class_distances(code, sec)
        t = odd_counts(m, cols, lm)
        N = count_tables(t, n, WMAX)
        tie = dist[:, 0] == dist[:, 1]
        p1, dec = maj_prob(N, dist, False)
        p1d, _ = maj_prob(N, dist, True)
        mw = np.argmin(dist, axis=1)
        idx = np.arange(dist.shape[0])
        dt, ut = tie & dec, tie & ~dec
        pick = (p1 > 0.5).astype(int)
        dis_by_sector[sec] = []
        if sec == "Z":
            print("d=5 sector Z: p, MLD, total excess/MLD, [non-tie, decided-tie, undecided-tie] excess/MLD, "
                  "decided ties with rule class != MLD class, deep/MLD")
        for p in P_LIST:
            if p <= 0.02:
                P = sum(N[w].astype(np.float64) * p**w * (1 - p)**(n - w) for w in range(WMAX + 1))
                mld_wht = joint(t, p).min(axis=1).sum()
                if abs(mld_wht - P.min(axis=1).sum()) / P.min(axis=1).sum() > 1e-6:
                    print(f"  PRECISION-FAIL p={p}")
                    fails += 1
            else:
                P = joint(t, p)
            pmin = P.min(axis=1)
            mld = pmin.sum()
            wrong = np.where(tie, p1 * P[:, 0] + (1 - p1) * P[:, 1], P[idx, 1 - mw])
            ex = wrong - pmin
            parts = [ex[~tie].sum(), ex[dt].sum(), ex[ut].sum()]
            if abs(sum(parts) - ex.sum()) > 1e-12 * mld + 1e-300:
                fails += 1
            dis = int((dt & (pick != (P[:, 1] > P[:, 0]).astype(int))).sum())
            dis_by_sector[sec].append(dis)
            deep = failure_rate_choice(P, p1d, tie, dist) / mld
            if sec == "Z":
                print(f"  p={p:<6} MLD={mld:.4e} excess={ex.sum()/mld:.4%} "
                      f"[{parts[0]/mld:.4%}, {parts[1]/mld:.4%}, {parts[2]/mld:.4%}] disagreements={dis} deep/MLD={deep:.5f}")
            if p <= 0.003 and dis != 0:
                fails += 1
            if p <= 0.02 and deep - 1 > 1e-4:
                fails += 1
        if sec == "Z":
            u = ut
            w0 = dist.min(axis=1)
            P = sum(N[w].astype(np.float64) * 0.001**w * (1 - 0.001)**(n - w) for w in range(WMAX + 1))
            ex = np.where(tie, p1 * P[:, 0] + (1 - p1) * P[:, 1], P[idx, 1 - mw]) - P.min(axis=1)
            print("  p=0.001 undecided-tie excess by tie weight (share of MLD): " + ", ".join(
                f"{i}:{ex[u & (w0 == i)].sum() / P.min(axis=1).sum():.4%}" for i in range(11) if (u & (w0 == i)).any()))
            print(f"  undecided ties by tie weight: " + ", ".join(
                f"{i}:{int((u & (w0 == i)).sum())}" for i in range(11) if (u & (w0 == i)).any()))
    if dis_by_sector["Z"] != dis_by_sector["X"]:
        print("  Z/X disagreement counts differ:", dis_by_sector)
        fails += 1
    print(f"TOTAL_FAILURES={fails}")
    print("RESULT: " + ("PASS" if fails == 0 else "FAIL"))
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
