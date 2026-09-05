"""
test_level4a_v3_boundary_termination.py

Level 4A-v3: physical singleton representatives and incidence endpoints.

This test deliberately separates three notions:
  1. physical_sides_touched: coordinate-level geometry of a data qubit;
  2. termination_points: concrete data-qubit endpoints identified by
     sector incidence degree == 1;
  3. termination_boundaries: sides touched by each endpoint, retained as
     metadata of ONE endpoint rather than flattened into independent options.

The test does NOT assert that a corner's two physical sides are two
independent termination choices. Boundary semantic interpretation remains an
explicit graph-contract question.

The current v2 boundary formula is reported for comparison only. It is not
used to construct the physical oracle and is not treated as proven.

Run from repository root:
    python tests/test_level4a_v3_boundary_termination.py
"""

import sys
from pathlib import Path

# Import src as a namespace package so decoder_lib_v2's relative S0 import
# remains valid without changing production code merely to run this test.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.decoder_lib_v2 import build_decoding_graph, CheckType, popcount


SIDE_NAMES = ("top", "bottom", "left", "right")


def sector_check_data(graph, sector):
    """Return sector checks and masks in their graph-local order."""
    rows = []
    masks = []
    for idx, stab in enumerate(graph.stabilizers):
        if stab.check_type is sector:
            rows.append(stab)
            masks.append(graph.check_masks[idx])
    return rows, masks


def sector_degree(graph, sector):
    """Count sector-incidence degree of every data qubit."""
    degree = {q: 0 for q in graph.data_qubits}
    for stab in graph.stabilizers:
        if stab.check_type is sector:
            for q in stab.data_qubits:
                degree[q] += 1
    return degree


def physical_sides(graph, q):
    """Return coordinate sides touched by one physical data qubit."""
    i, j = graph.data_positions[q]
    m = 2 * graph.d - 2
    sides = []
    if i == 0:
        sides.append("top")
    if i == m:
        sides.append("bottom")
    if j == 0:
        sides.append("left")
    if j == m:
        sides.append("right")
    return tuple(sides)


def syndrome(error_mask, check_masks):
    """Compute a local sector syndrome directly from physical incidence."""
    result = 0
    for k, mask in enumerate(check_masks):
        if popcount(error_mask & mask) & 1:
            result |= 1 << k
    return result


def singleton_oracle(graph, sector):
    """Find all minimum-weight physical representatives for every singleton."""
    checks, check_masks = sector_check_data(graph, sector)
    oracle = {}

    for error in range(1 << graph.n_data):
        synd = syndrome(error, check_masks)
        if synd == 0 or (synd & (synd - 1)):
            continue

        local_idx = synd.bit_length() - 1
        cid = checks[local_idx].check_id
        weight = popcount(error)

        entry = oracle.setdefault(cid, {"min_weight": None, "masks": []})
        if entry["min_weight"] is None or weight < entry["min_weight"]:
            entry["min_weight"] = weight
            entry["masks"] = [error]
        elif weight == entry["min_weight"]:
            entry["masks"].append(error)

    return checks, check_masks, oracle


def endpoint_records(graph, sector, masks, degree):
    """Describe incidence endpoints without turning corner sides into options."""
    records = []
    for mask in masks:
        endpoints = []
        for q in graph.data_qubits:
            if ((mask >> q) & 1) and degree[q] == 1:
                endpoints.append({
                    "q": q,
                    "position": graph.data_positions[q],
                    "physical_sides_touched": physical_sides(graph, q),
                })
        records.append(endpoints)
    return records


def current_v2_formula(graph, stab):
    """Report the boundary costs encoded by current decoder_lib_v2."""
    max_coord = 2 * graph.d - 2
    i, j = stab.position
    if stab.check_type is CheckType.Z:
        return {
            "top_Z": i // 2 + 1,
            "bottom_Z": (max_coord - i) // 2 + 1,
        }
    return {
        "left_X": j // 2 + 1,
        "right_X": (max_coord - j) // 2 + 1,
    }


def main():
    print("=" * 70)
    print("LEVEL 4A-v3: Boundary Termination Oracle (d=3)")
    print("=" * 70)
    print("Physical oracle: exhaustive over all 2^13 physical error masks.")
    print("Endpoint semantics: incidence degree == 1; corner sides remain metadata.")

    graph = build_decoding_graph(3)
    print(f"\nGraph: n_data={graph.n_data}, n_checks={graph.n_checks}")

    any_fail = False
    total_singletons = 0

    for sector in (CheckType.Z, CheckType.X):
        checks, check_masks, oracle = singleton_oracle(graph, sector)
        degree = sector_degree(graph, sector)
        print("\n" + "=" * 70)
        print(f"{sector.value}-SECTOR")
        print("=" * 70)

        for stab in checks:
            cid = stab.check_id
            data = oracle[cid]
            masks = data["masks"]
            records = endpoint_records(graph, sector, masks, degree)
            formula = current_v2_formula(graph, stab)
            total_singletons += 1

            endpoint_count_set = {len(r) for r in records}
            singleton_endpoint_ok = endpoint_count_set == {1}
            if not singleton_endpoint_ok:
                any_fail = True

            print(f"  {sector.value}-check {cid}: position={stab.position}")
            print(f"    min_weight={data['min_weight']}, minimum_representatives={len(masks)}")
            print(f"    current_v2_boundary_formula={formula}")
            print(f"    incidence_endpoint_count(s)={[len(r) for r in records]}")
            print(f"    termination_points={records}")

            # Compare only the scalar minimum weight with formula values.
            # Do not infer boundary semantics from coordinate-side membership.
            formula_matches_weight = data["min_weight"] in formula.values()
            print(f"    formula_contains_min_weight={formula_matches_weight}")

            if not formula_matches_weight:
                print("    NOTE: current v2 formula has no boundary edge with the physical singleton minimum.")

    print("\n" + "=" * 70)
    print("LEVEL 4A-v3 SUMMARY")
    print("=" * 70)
    print(f"  Singleton checks tested: {total_singletons}")
    print("  Physical oracle: PASS (minimum representatives computed directly from incidence)")

    if any_fail:
        print("  ❌ INCIDENCE ENDPOINT INVARIANT FAILED")
        print("     A singleton minimum representative did not have exactly one deg=1 endpoint.")
        raise SystemExit(1)

    print("  ✅ Every minimum singleton representative has exactly one incidence endpoint")
    print("  ✅ Corner side membership is retained as endpoint metadata, not independent options")
    print("  ⚠ Boundary semantic mapping remains UNPROVEN")
    print("  ⚠ Current v2 coordinate formula is diagnostic only")
    print("=" * 70)


if __name__ == "__main__":
    main()
