"""Forensic d=5 probe for the historical motif-definition hypothesis.

Diagnostic only: no oracle/decoder role and no claim of historical source recovery.

Fixed hypothesis: historical motif classes used connection-family identity plus
endpoint-disjointness, while boundary-boundary pairs retained the observed
DOUBLE-exit subdivision for IIIc. The hypothesis is all-or-nothing: every
historical class total must match simultaneously. Any mismatch means
NOT_CONFIRMED. Even a five-row match does not prove corpus/source identity.

The static graph is the source of truth for boundary-exit multiplicity. Before
any path-level probe runs, graph boundary attachments and boundary references
in the connection catalog are checked bidirectionally. Catalog-derived exit
attachments are retained only as a diagnostic representation after that hard
consistency check; they are not described as an independent source of truth.

Level 1 is a full-corpus cheap assertion. It derives boundary presence directly
from canonical path edge metadata and checks classify_motif() against that
separate boolean predicate. Level 2 is a deterministic boundary-focused corpus
covering A/B/C class boundaries, including A2a/A2b CC/CC paths that traverse a
boundary node.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "audit"))

from s0_geometry import build_unrotated_planar_surface_code
from _level4_common import graph_construction, connection_catalog
from provenance_reconciliation import (
    analyze_boundary_exit_multiplicity,
    catalog_derived_exit_attachments,
    classify_motif,
    cross_check_graph_catalog_boundary_attachments,
    flatten_catalog,
)

HISTORICAL = {"I": 16558, "II": 4864, "IIIa": 212, "IIIb": 18, "IIIc": 382}


def boundary_edge_qubits(path):
    """Separate path predicate: inspect canonical edge metadata directly."""
    return {edge[4] for edge in path.edge_signature if edge[1] == "check_boundary"}


def has_boundary_edge(path):
    return bool(boundary_edge_qubits(path))


def family(path):
    return path.key[0]


def side(path):
    return path.key[2] if path.key[0] == "boundary" else None


def catalog_derived_exit_diagnostic(catalog):
    """Build a catalog-derived multiplicity view after graph↔catalog validation.

    This is deliberately named diagnostic rather than recomputation: its source
    is the catalog, so it is not independent of catalog path construction.
    """
    attachments, malformed = catalog_derived_exit_attachments(catalog)
    assert not malformed, malformed
    result = {}
    for q, items in sorted(attachments.items()):
        n = len(items)
        result[q] = {
            "multiplicity": "SINGLE" if n == 1 else "DOUBLE" if n == 2 else "ANOMALOUS",
            "attachments": items,
        }
    return result


def independent_widened_label(p, q, exit_info):
    """Historical class hypothesis, structurally separate from classify_motif()."""
    fp, fq = family(p), family(q)
    if fp == fq == "pair":
        return "I"
    if {fp, fq} == {"pair", "boundary"}:
        return "II"
    if fp == fq == "boundary":
        if side(p) == side(q):
            return "IIIa"
        doubles = {qnum for qnum, info in exit_info.items()
                   if info["multiplicity"] == "DOUBLE"}
        return "IIIc" if (boundary_edge_qubits(p) & boundary_edge_qubits(q) & doubles) else "IIIb"
    raise AssertionError((fp, fq))


def collect_pairs(paths):
    by_qubit = defaultdict(list)
    for pid, path in enumerate(paths):
        mask = path.mask
        while mask:
            bit = mask & -mask
            by_qubit[bit.bit_length() - 1].append(pid)
            mask ^= bit
    pairs = set()
    for ids in by_qubit.values():
        pairs.update(combinations(sorted(set(ids)), 2))
    return [(a, b) for a, b in sorted(pairs)
            if not (set(paths[a].endpoints) & set(paths[b].endpoints))]


def level1_full_assert(paths, pairs):
    checks = Counter()
    for a, b in pairs:
        p, q = paths[a], paths[b]
        actual = classify_motif(p, q, {})
        bp, bq = has_boundary_edge(p), has_boundary_edge(q)
        if not bp and not bq:
            assert actual == "I", (a, b, actual, "I")
        elif bp != bq:
            assert actual == "II", (a, b, actual, "II")
        else:
            assert actual in {"IIIa", "IIIb", "IIIc"}, (a, b, actual)
        checks[f"actual_{actual}"] += 1
    return checks


def deterministic_boundary_corpus(paths, pairs, exit_info, limit_per_bucket=8):
    doubles = {q for q, info in exit_info.items() if info["multiplicity"] == "DOUBLE"}
    buckets = defaultdict(list)
    for a, b in pairs:
        p, q = paths[a], paths[b]
        fp, fq = family(p), family(q)
        bp, bq = has_boundary_edge(p), has_boundary_edge(q)
        if fp == fq == "pair":
            if not bp and not bq:
                bucket = "A1_CC_CC_no_boundary"
            else:
                qset = boundary_edge_qubits(p) | boundary_edge_qubits(q)
                bucket = "A2b_CC_CC_boundary_double_exit" if qset & doubles else "A2a_CC_CC_boundary_single_exit"
        elif {fp, fq} == {"pair", "boundary"}:
            bucket = "B_CC_CB"
        elif fp == fq == "boundary":
            if side(p) == side(q):
                bucket = "C1_CB_CB_same_boundary"
            elif (boundary_edge_qubits(p) & boundary_edge_qubits(q) & doubles):
                bucket = "C3_CB_CB_different_boundary_double_exit"
            else:
                bucket = "C2_CB_CB_different_boundary_single_exit"
        else:
            continue
        if len(buckets[bucket]) < limit_per_bucket:
            buckets[bucket].append((a, b))
    return buckets


def level2_assert(paths, buckets, exit_info):
    checked = 0
    production_exit_for_classifier = {
        q: {"multiplicity": info["multiplicity"]}
        for q, info in exit_info.items()
    }
    for bucket, pairs in sorted(buckets.items()):
        assert pairs, bucket
        for a, b in pairs:
            p, q = paths[a], paths[b]
            actual = classify_motif(p, q, production_exit_for_classifier)
            widened = independent_widened_label(p, q, exit_info)
            bp, bq = has_boundary_edge(p), has_boundary_edge(q)
            if bucket.startswith("A1"):
                assert not bp and not bq and actual == "I" and widened == "I"
            elif bucket.startswith("A2"):
                assert family(p) == family(q) == "pair" and (bp or bq)
                assert widened == "I"
                # This is the explicit A2-vs-II boundary: a CC/CC path that
                # traverses a boundary remains family I under the hypothesis.
                assert actual in {"I", "II", "IIIa", "IIIb", "IIIc"}
            elif bucket.startswith("B"):
                assert bp != bq and actual == "II" and widened == "II"
            elif bucket.startswith("C1"):
                assert bp and bq and side(p) == side(q)
                assert actual == "IIIa" and widened == "IIIa"
            elif bucket.startswith("C2"):
                assert bp and bq and side(p) != side(q)
                assert actual == "IIIb" and widened == "IIIb"
            elif bucket.startswith("C3"):
                assert bp and bq and side(p) != side(q)
                assert actual == "IIIc" and widened == "IIIc"
            else:
                raise AssertionError(bucket)
            checked += 1
    return checked


def run(d, sector):
    code = build_unrotated_planar_surface_code(d)
    adjacency, edges = graph_construction(code, sector)
    check_count = len(code["z_checks"] if sector == "Z" else code["x_checks"])

    # Source of truth: static graph boundary-edge attachments.
    production_exit, anomalies = analyze_boundary_exit_multiplicity(edges)
    assert not anomalies, anomalies

    catalog = connection_catalog(adjacency, check_count)

    # Hard stop before flattening or motif interpretation.
    cross_check = cross_check_graph_catalog_boundary_attachments(edges, catalog)
    assert cross_check["status"] == "PASS", cross_check

    # Catalog view is now only a diagnostic representation. Equality here is
    # expected because the bidirectional edge-level contract has already passed.
    catalog_exit = catalog_derived_exit_diagnostic(catalog)
    graph_attachment_view = {
        q: {
            "multiplicity": info["multiplicity"],
            "attachments": info["attachments"],
        }
        for q, info in sorted(production_exit.items())
    }
    assert graph_attachment_view == catalog_exit, (
        "graph/catalog exit diagnostic mismatch",
        graph_attachment_view,
        catalog_exit,
    )

    paths = flatten_catalog(catalog, sector)
    pairs = collect_pairs(paths)
    level1 = level1_full_assert(paths, pairs)
    buckets = deterministic_boundary_corpus(paths, pairs, production_exit)
    level2_cases = level2_assert(paths, buckets, production_exit)

    widened = Counter()
    current = Counter()
    for a, b in pairs:
        p, q = paths[a], paths[b]
        widened[independent_widened_label(p, q, production_exit)] += 1
        current[classify_motif(p, q, production_exit)] += 1

    all_five_match = all(widened[k] == HISTORICAL[k] for k in HISTORICAL)
    doubles = {q for q, info in production_exit.items() if info["multiplicity"] == "DOUBLE"}
    a2a = a2b = 0
    for a, b in pairs:
        p, q = paths[a], paths[b]
        if family(p) == family(q) == "pair" and (has_boundary_edge(p) or has_boundary_edge(q)):
            if (boundary_edge_qubits(p) | boundary_edge_qubits(q)) & doubles:
                a2b += 1
            else:
                a2a += 1

    print(f"SECTOR {sector}")
    print("graph_catalog_cross_check", cross_check)
    print("paths_total", len(paths))
    print("endpoint_disjoint_pairs", len(pairs))
    print("level1_full_assert", dict(sorted(level1.items())))
    print("deterministic_buckets", {k: len(v) for k, v in sorted(buckets.items())})
    print("level2_cases_checked", level2_cases)
    print("exit_multiplicity", dict(sorted(Counter(info["multiplicity"] for info in production_exit.values()).items())))
    print("A2a_count", a2a)
    print("A2b_count", a2b)
    print("WIDENED_BY_PATH_KEY_AND_ENDPOINT", dict(sorted(widened.items())))
    print("CURRENT_STRUCTURAL", dict(sorted(current.items())))
    print("HISTORICAL", HISTORICAL)
    print("DELTA_WIDENED_MINUS_HISTORICAL", {k: widened[k] - HISTORICAL[k] for k in HISTORICAL})
    print("ALL_FIVE_MATCH", all_five_match)
    return widened, all_five_match


def main():
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    z, zmatch = run(d, "Z")
    x, xmatch = run(d, "X")
    assert z == x, "sector asymmetry in widened historical reconstruction"
    assert zmatch == xmatch
    print("HYPOTHESIS_STATUS", "STRONGLY_SUPPORTED_BUT_NOT_PROVEN" if zmatch else "NOT_CONFIRMED")
    print("CORPUS_IDENTITY", "UNPROVEN")
    print("HISTORICAL_CODE_IDENTITY", "UNPROVEN")


if __name__ == "__main__":
    main()
