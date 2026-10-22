"""Internal consistency probe for the full-corpus provenance scanner.

This diagnostic isolates the CC/CC subcomputation inside the mixed CC+CB corpus
and compares it with the same scanner run on the CC-only subset. It does not use
historical Run A and makes no production or boundary-ontology claim.

The CC-only comparison deliberately supplies an empty exit-info mapping because
motif I is boundary-independent. Any boundary-exit analysis failure must not
contaminate this probe.

If these disagree, the mixed corpus changes a computation that should be
identical on the CC/CC subset. That is a blocking internal bug. If they agree,
then the previously reported 13266 value cannot be attributed to the currently
committed scan_pairs() implementation without recovering the exact earlier
instrument that produced it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "audit"))

from s0_geometry import build_unrotated_planar_surface_code
from _level4_common import graph_construction, connection_catalog
from provenance_reconciliation import flatten_catalog, scan_pairs


def run_sector(d: int, sector: str):
    code = build_unrotated_planar_surface_code(d)
    adjacency, _ = graph_construction(code, sector)
    catalog = connection_catalog(
        adjacency,
        len(code["z_checks"] if sector == "Z" else code["x_checks"]),
    )

    all_paths = flatten_catalog(catalog, sector)
    cc_paths = [p for p in all_paths if p.key[0] == "pair"]

    # For CC/CC pairs classify_motif() is independent of exit_info.
    empty_exit_info = {}
    full_funnel, _ = scan_pairs(all_paths, empty_exit_info)
    cc_funnel_from_full, _ = scan_pairs(cc_paths, empty_exit_info)

    keys = (
        "overlap_pairs",
        "check_endpoint_conflict",
        "endpoint_disjoint_pairs",
        "motif_I",
    )
    full_restricted = {k: full_funnel.get(k, 0) for k in keys}
    cc_direct = {k: cc_funnel_from_full.get(k, 0) for k in keys}

    return {
        "sector": sector,
        "paths_total": len(all_paths),
        "cc_paths_total": len(cc_paths),
        "full_funnel": dict(full_funnel),
        "cc_only_funnel": dict(cc_funnel_from_full),
        "cc_restricted_from_full": full_restricted,
        "cc_only_direct": cc_direct,
        "cc_restricted_matches_direct": full_restricted == cc_direct,
    }


def main():
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    results = [run_sector(d, sector) for sector in ("Z", "X")]
    for result in results:
        print(json.dumps(result, sort_keys=True, indent=2))

    passed = all(r["cc_restricted_matches_direct"] for r in results)
    print("FULL_CORPUS_CC_CONSISTENCY", "PASS" if passed else "FAIL")
    print("SCOPE d=5 current committed S0 + _level4_common.py + provenance_reconciliation.py")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
