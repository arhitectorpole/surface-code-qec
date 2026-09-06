from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.s0_geometry import build_unrotated_planar_surface_code
from tests._level4_common import (
    exhaustive_physical_oracle,
    graph_construction,
    connection_catalog,
    exhaustive_shortest_path_search,
    syndrome_of_mask,
    popcount,
)


def validate_sector(code, sector):
    check_masks, oracle_best, _oracle_representatives = exhaustive_physical_oracle(code, sector)
    adjacency, edges = graph_construction(code, sector)
    catalog = connection_catalog(adjacency, len(check_masks))
    failures = []
    records = []
    for syndrome in range(1 << len(check_masks)):
        candidates = exhaustive_shortest_path_search(
            syndrome, len(check_masks), catalog
        )
        valid = {}
        provenance_complete = True
        for mask, provenance in candidates.items():
            if syndrome_of_mask(mask, check_masks) == syndrome:
                valid[mask] = provenance
                if syndrome != 0 and not provenance:
                    provenance_complete = False
        found_weight = min((popcount(mask) for mask in valid), default=None)
        record = {
            "sector": sector,
            "syndrome": f"0x{syndrome:02x}",
            "oracle_weight": oracle_best[syndrome],
            "found_weight": found_weight,
            "valid_masks": len(valid),
            "provenance_complete": provenance_complete,
        }
        records.append(record)
        if found_weight != oracle_best[syndrome] or not provenance_complete:
            failures.append(record)
    return edges, catalog, records, failures


def main():
    code = build_unrotated_planar_surface_code(3)
    print("LEVEL 4C GRAPH-CONTRACT VALIDATOR")
    print("production_decoder_imported=False")
    print("oracle=exhaustive_2^13_physical_masks_per_CSS_sector")
    print("syndrome_domain=64_Z_plus_64_X_sector_local_cases")
    all_failures = []
    total_cases = 0
    for sector in ("Z", "X"):
        edges, catalog, records, failures = validate_sector(code, sector)
        total_cases += len(records)
        all_failures.extend(failures)
        print(
            f"SECTOR {sector}: checks=6 graph_edges={len(edges)} "
            f"shortest_path_catalog_entries={len(catalog)} "
            f"cases={len(records)} failures={len(failures)}"
        )
        for record in records:
            print(
                "{sector} syn={syndrome} oracle={oracle_weight} "
                "found={found_weight} valid_masks={valid_masks} "
                "provenance_complete={provenance_complete}".format(**record)
            )
    print(f"TOTAL_CASES={total_cases}")
    print(f"TOTAL_FAILURES={len(all_failures)}")
    if all_failures:
        print("RESULT: FAIL")
        for failure in all_failures:
            print("COUNTEREXAMPLE", failure)
        raise SystemExit(1)
    print("RESULT: PASS")
    print(
        "INTERPRETATION: graph construction is extensionally equivalent to the "
        "independent physical oracle on the tested d=3 sector-local syndrome spaces."
    )


if __name__ == "__main__":
    main()
