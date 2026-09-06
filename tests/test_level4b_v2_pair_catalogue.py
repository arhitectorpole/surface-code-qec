from pathlib import Path
import sys
from itertools import combinations
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.s0_geometry import build_unrotated_planar_surface_code
from tests._level4_common import exhaustive_physical_oracle, sector_checks


def main():
    code = build_unrotated_planar_surface_code(3)
    print("LEVEL 4B-v2 PAIR CATALOGUE")
    for sector in ("Z", "X"):
        checks = sector_checks(code, sector)
        _check_masks, best, representatives = exhaustive_physical_oracle(code, sector)
        print(f"\nSECTOR {sector}:")
        for i, j in combinations(range(len(checks)), 2):
            intersection = tuple(sorted(set(checks[i][1]) & set(checks[j][1])))
            syndrome = (1 << i) | (1 << j)
            min_masks = sorted(representatives[syndrome])
            print(
                f"{sector}-({i},{j}) intersection={intersection} "
                f"phys_min={best[syndrome]} min_reps={min_masks}"
            )
            if len(intersection) == 1:
                q = intersection[0]
                assert best[syndrome] == 1 and min_masks == [1 << q]
            else:
                assert best[syndrome] >= 2
    print("\nRESULT: PASS")


if __name__ == "__main__":
    main()
