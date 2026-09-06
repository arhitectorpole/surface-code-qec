from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.s0_geometry import build_unrotated_planar_surface_code
from tests._level4_common import exhaustive_physical_oracle, sector_checks


def main():
    code = build_unrotated_planar_surface_code(3)
    print("LEVEL 4A-v4 ENDPOINT CATALOGUE")
    print("d=3 n_data=%d" % len(code["data"]))
    for sector in ("Z", "X"):
        checks = sector_checks(code, sector)
        _check_masks, best, representatives = exhaustive_physical_oracle(code, sector)
        degree = [0] * len(code["data"])
        for _, qubits in checks:
            for q in qubits:
                degree[q] += 1
        print(f"\nSECTOR {sector}: n_checks={len(checks)} unique_syndromes={len(best)}")
        for ci, ((x, y), qubits) in enumerate(checks):
            syndrome = 1 << ci
            min_weight = best[syndrome]
            min_masks = sorted(representatives[syndrome])
            endpoint_qubits = [
                q for q in qubits
                if degree[q] == 1 and any(mask & (1 << q) for mask in min_masks)
            ]
            sides_by_q = {}
            for mask in min_masks:
                q = (mask & -mask).bit_length() - 1
                xx, yy = code["data"][q]
                sides = []
                if xx == 0:
                    sides.append("L")
                if xx == 4:
                    sides.append("R")
                if yy == 0:
                    sides.append("T")
                if yy == 4:
                    sides.append("B")
                sides_by_q[q] = tuple(sides)
            print(
                f"{sector}{ci} pos={(x,y)} qs={tuple(qubits)} "
                f"min_weight={min_weight} min_reps={min_masks} "
                f"incidence_endpoints={endpoint_qubits} sides={sides_by_q}"
            )
            assert min_weight == 1
            assert endpoint_qubits
    print("\nRESULT: PASS")


if __name__ == "__main__":
    main()
