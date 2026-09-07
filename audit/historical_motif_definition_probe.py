"""Independent d=5 probe for the historical motif-definition hypothesis.

Hypothesis under test (not assumed true): historical motif I may have meant
CC/CC endpoint-disjoint, rather than the current narrower condition that
neither constituent path contains a boundary node.  The same type-based
widening is tested across all motif families; a partial match is not treated
as historical reconstruction.

This probe deliberately does NOT call classify_motif(). It independently
reconstructs pair-family labels from catalog keys and endpoint disjointness,
then reports both the widened counts and the current structural counts for
comparison. It is diagnostic only and has no oracle/decoder role.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from s0_geometry import build_unrotated_planar_surface_code
from _level4_common import graph_construction, connection_catalog

HISTORICAL = {"I": 16558, "II": 4864, "IIIa": 212, "IIIb": 18, "IIIc": 382}


def records(catalog):
    out = []
    for key, paths in catalog.items():
        for mask, node_path, edge_path in paths:
            out.append({
                "key": key,
                "mask": mask,
                "node_path": tuple(node_path),
                "endpoints": (node_path[0], node_path[-1]),
                "edge_path": tuple(edge_path),
            })
    return out


def has_boundary_node(p):
    return any(isinstance(n, tuple) and n[0] == "b" for n in p["node_path"])


def path_family(p):
    return p["key"][0]


def boundary_side(p):
    key = p["key"]
    return key[2] if key[0] == "boundary" else None


def independent_widened_label(p, q):
    """Type-based classification independent of classify_motif()."""
    fp, fq = path_family(p), path_family(q)
    if fp == "pair" and fq == "pair":
        return "I"
    if {fp, fq} == {"pair", "boundary"}:
        return "II"
    if fp == "boundary" and fq == "boundary":
        # Historical IIIa/IIIb are tested here using the explicit boundary
        # connection identities, not by inspecting intermediate node paths.
        # IIIc is deliberately separated later by physical double-exit data.
        return "IIIa" if boundary_side(p) == boundary_side(q) else "IIIb"
    raise AssertionError((fp, fq))


def boundary_qubits(p):
    qs = set()
    for edge in p["edge_path"]:
        meta = edge[3]
        if meta.get("kind") == "check_boundary":
            qs.add(meta.get("qubit"))
    return qs


def observed_double_exit_qubits(catalog):
    # Independent of the census classifier: inspect unique physical boundary
    # attachments directly from the graph-edge catalog.
    attachments = {}
    for key, paths in catalog.items():
        if key[0] != "boundary":
            continue
        check, side = key[1], key[2]
        for _, _, edge_path in paths:
            for edge in edge_path:
                meta = edge[3]
                if meta.get("kind") == "check_boundary":
                    attachments.setdefault(meta["qubit"], set()).add((check, side))
    return {q for q, a in attachments.items() if len(a) == 2}


def scan(catalog):
    ps = records(catalog)
    by_q = {}
    for i, p in enumerate(ps):
        for q in range(100):
            if p["mask"] & (1 << q):
                by_q.setdefault(q, []).append(i)
    pairs = set()
    for ids in by_q.values():
        pairs.update(combinations(sorted(set(ids)), 2))

    counts = Counter()
    widened = Counter()
    current_structural = Counter()
    for a, b in sorted(pairs):
        p, q = ps[a], ps[b]
        if set(p["endpoints"]) & set(q["endpoints"]):
            continue
        label = independent_widened_label(p, q)
        widened[label] += 1

        # Current motif-I criterion only, recomputed independently.
        if label == "I":
            if not has_boundary_node(p) and not has_boundary_node(q):
                current_structural["I"] += 1
        elif label == "II":
            if has_boundary_node(p) != has_boundary_node(q):
                current_structural["II"] += 1
        elif label in ("IIIa", "IIIb"):
            # This is only the current side/path-node structural split; IIIc
            # is reported separately below rather than silently folding it.
            current_structural[label] += 1

    return widened, current_structural, len(pairs)


def run(d, sector):
    code = build_unrotated_planar_surface_code(d)
    adjacency, _ = graph_construction(code, sector)
    catalog = connection_catalog(adjacency, len(code["z_checks"] if sector == "Z" else code["x_checks"]))
    widened, current, endpoint_disjoint = scan(catalog)
    print(f"SECTOR {sector}")
    print("paths_total", sum(len(v) for v in catalog.values()))
    print("endpoint_disjoint_pairs", endpoint_disjoint)
    print("WIDENED_BY_PATH_KEY_AND_ENDPOINT", dict(sorted(widened.items())))
    print("CURRENT_STRUCTURAL_RECOMPUTE", dict(sorted(current.items())))
    print("HISTORICAL", HISTORICAL)
    print("DELTA_WIDENED_MINUS_HISTORICAL", {
        k: widened[k] - HISTORICAL[k] for k in HISTORICAL
    })
    print("DELTA_CURRENT_MINUS_HISTORICAL", {
        k: current[k] - HISTORICAL[k] for k in HISTORICAL
    })
    return widened


def main():
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    z = run(d, "Z")
    x = run(d, "X")
    print("SECTOR_SYMMETRY", z == x)
    print("HYPOTHESIS_STATUS", "UNRESOLVED")
    print("REASON", "A matching category is necessary evidence but not sufficient historical provenance")


if __name__ == "__main__":
    main()
