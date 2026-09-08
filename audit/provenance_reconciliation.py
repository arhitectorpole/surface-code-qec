"""Layered reconciliation instrument for the d=5 cancellation-census provenance gap.

This is a reconstructed instrument, not a claim to reproduce the lost Run A
implementation. It is intentionally derived from the committed S0 geometry
and Level-4 common graph/path helpers.

The instrument stops conceptually at the first divergent layer:
L0 geometry -> L1 graph -> graph/catalog boundary cross-check
-> L2 shortest-path corpus -> L3 canonicalization -> L4 overlap index
-> L5 structural filters -> L6 motif classification.

No physical oracle is used here. No decoder result is inferred from this
instrument. The historical 22034/212 result is an external UNRECONCILED
reference only.

Execution note: this file is intentionally runnable from GitHub Actions.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from enum import Enum
from hashlib import sha256
from itertools import combinations
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from s0_geometry import build_unrotated_planar_surface_code
from _level4_common import graph_construction, connection_catalog

SIDES = ("T", "B", "L", "R")
HISTORICAL_RUN_A = {"overlap_pairs": 22034, "motif_IIIa": 212}


class ExitMultiplicity(str, Enum):
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    ANOMALOUS = "ANOMALOUS"


class GraphCatalogInconsistency(RuntimeError):
    """Hard-stop status for disagreement between graph edges and catalog refs."""

    status = "GRAPH_CATALOG_INCONSISTENCY"


@dataclass(frozen=True)
class PathRecord:
    sector: str
    key: tuple
    mask: int
    node_path: tuple
    edge_signature: tuple
    endpoints: tuple
    graph_cost: int


@dataclass
class MotifRecord:
    id: int
    sector: str
    motif: str
    cancellation_type: str
    path_ids: tuple
    endpoints: tuple
    graph_costs: tuple
    physical_masks: tuple
    xor_mask: int
    delta: int
    boundary_nodes: tuple
    composability: str = "PROVEN"
    eligible_for_oracle_pipeline: bool = True
    epistemic_status: str = "CENSUS"


def stable_hash(obj) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=list)
    return sha256(payload.encode()).hexdigest()


def geometry_signature(code, sector):
    checks = code["z_checks"] if sector == "Z" else code["x_checks"]
    return {
        "d": code["d"],
        "data_count": len(code["data"]),
        "check_count": len(checks),
        "data_coords": tuple(code["data"]),
        "check_coords": tuple(sorted(pos for pos, _ in checks)),
        "check_supports": tuple(sorted(tuple(sorted(qs)) for _, qs in checks)),
    }


def canonical_edge_signature(edge):
    u, v, mask, meta = edge
    endpoints = tuple(sorted((u, v), key=repr))
    return (
        endpoints,
        meta.get("kind"),
        tuple(sorted(meta.get("checks", ()))),
        meta.get("check"),
        meta.get("qubit"),
        meta.get("side"),
        mask,
    )


def graph_signature(edges):
    return tuple(sorted((canonical_edge_signature(e) for e in edges), key=repr))


def graph_boundary_attachment_triples(edges):
    """Return static graph boundary attachments as (check, side, qubit)."""
    triples = set()
    for _u, _v, _mask, meta in edges:
        if meta.get("kind") != "check_boundary":
            continue
        triples.add((meta["check"], meta["side"], meta["qubit"]))
    return triples


def boundary_edge_attachments_from_graph(edges):
    """Aggregate physical boundary attachments from the static graph edge list.

    This deliberately does NOT inspect shortest-path occurrences. Each
    check_boundary graph edge contributes exactly one (check, side)
    attachment for its physical qubit, regardless of how many shortest
    paths later traverse that edge.
    """
    attachments = defaultdict(set)
    for check, side, qubit in graph_boundary_attachment_triples(edges):
        attachments[qubit].add((check, side))
    return attachments


def catalog_boundary_attachment_triples(catalog):
    """Derive boundary attachment refs from boundary connections in catalog.

    A catalog boundary connection ('boundary', check, side) is accepted only
    when each shortest-path representative contains a concrete check_boundary
    edge whose metadata carries the same check and side. The physical qubit of
    that edge is the catalog-derived exit qubit.

    Pair connections are intentionally ignored here: they may traverse a
    boundary node, but they are not boundary-termination references.
    """
    triples = set()
    malformed = []
    for key in sorted(catalog, key=repr):
        if not key or key[0] != "boundary":
            continue
        check, side = key[1], key[2]
        for path_index, (_mask, _node_path, edge_path) in enumerate(catalog[key]):
            matching = []
            for edge in edge_path:
                meta = edge[3]
                if (meta.get("kind") == "check_boundary"
                        and meta.get("check") == check
                        and meta.get("side") == side):
                    matching.append(meta.get("qubit"))
            matching = [q for q in matching if q is not None]
            if not matching:
                malformed.append({
                    "key": key,
                    "path_index": path_index,
                    "reason": "boundary path lacks matching check_boundary edge",
                })
                continue
            for qubit in matching:
                triples.add((check, side, qubit))
    return triples, malformed


def catalog_derived_exit_attachments(catalog):
    """Diagnostic catalog-derived attachment map; graph remains source of truth."""
    triples, malformed = catalog_boundary_attachment_triples(catalog)
    attachments = defaultdict(set)
    for check, side, qubit in triples:
        attachments[qubit].add((check, side))
    return {
        q: tuple(sorted(items))
        for q, items in sorted(attachments.items())
    }, malformed


def cross_check_graph_catalog_boundary_attachments(edges, catalog):
    """Enforce Catalog ⊆ Graph and Graph ⊆ Catalog before path interpretation."""
    graph_triples = graph_boundary_attachment_triples(edges)
    catalog_triples, malformed = catalog_boundary_attachment_triples(catalog)

    catalog_not_in_graph = sorted(catalog_triples - graph_triples)
    graph_not_in_catalog = sorted(graph_triples - catalog_triples)
    if malformed or catalog_not_in_graph or graph_not_in_catalog:
        details = {
            "status": GraphCatalogInconsistency.status,
            "malformed_catalog_boundary_paths": malformed,
            "catalog_not_in_graph": catalog_not_in_graph,
            "graph_not_in_catalog": graph_not_in_catalog,
            "graph_attachment_count": len(graph_triples),
            "catalog_attachment_count": len(catalog_triples),
        }
        raise GraphCatalogInconsistency(json.dumps(details, sort_keys=True, default=list))

    return {
        "status": "PASS",
        "attachment_count": len(graph_triples),
        "graph_sha256": stable_hash(sorted(graph_triples)),
        "catalog_sha256": stable_hash(sorted(catalog_triples)),
    }


def analyze_boundary_exit_multiplicity(edges):
    """Classify physical boundary exits from the graph, not the path corpus."""
    raw = boundary_edge_attachments_from_graph(edges)
    result = {}
    anomalies = {}
    for q, items in raw.items():
        attachments = tuple(sorted(items))
        n = len(attachments)
        if n == 1:
            mult = ExitMultiplicity.SINGLE
        elif n == 2:
            mult = ExitMultiplicity.DOUBLE
        else:
            mult = ExitMultiplicity.ANOMALOUS
            anomalies[q] = attachments
        result[q] = {"qubit": q, "multiplicity": mult.value,
                     "attachments": attachments}
    return result, anomalies


def canonical_path_key(record):
    return (record.key, record.endpoints, record.graph_cost,
            record.mask, record.edge_signature, record.node_path)


def flatten_catalog(catalog, sector):
    records = []
    for key in sorted(catalog, key=repr):
        for mask, node_path, edge_path in catalog[key]:
            endpoints = (node_path[0], node_path[-1])
            edges = tuple(canonical_edge_signature(e) for e in edge_path)
            records.append(PathRecord(sector, key, mask, tuple(node_path),
                                      edges, endpoints, len(edge_path)))
    records.sort(key=canonical_path_key)
    return records


def path_signature(paths):
    return tuple((p.key, p.mask, p.node_path, p.edge_signature, p.graph_cost)
                 for p in paths)


def connection_histogram(paths):
    return Counter(p.key for p in paths)


def overlap_index(paths):
    index = defaultdict(list)
    for pid, p in enumerate(paths):
        mask = p.mask
        while mask:
            bit = mask & -mask
            q = bit.bit_length() - 1
            index[q].append(pid)
            mask ^= bit
    return index


def classify_motif(p, q, exit_info):
    pbs = [n for n in p.node_path if isinstance(n, tuple) and n[0] == "b"]
    qbs = [n for n in q.node_path if isinstance(n, tuple) and n[0] == "b"]
    if not pbs and not qbs:
        return "I"
    if bool(pbs) != bool(qbs):
        return "II"
    pnode = pbs[-1][1]
    qnode = qbs[-1][1]
    if pnode == qnode:
        return "IIIa"
    qnums = set()
    for path in (p, q):
        for edge in path.edge_signature:
            if edge[1] == "check_boundary" and edge[4] is not None:
                qnums.add(edge[4])
    if any(exit_info.get(x, {}).get("multiplicity") == ExitMultiplicity.DOUBLE.value
           for x in qnums):
        return "IIIc"
    return "IIIb"


def cancellation_type(delta, xor_mask):
    if delta == 0:
        return "NONE"
    if xor_mask == 0:
        return "FULL_PHYSICAL_CANCELLATION"
    return "PARTIAL"


def scan_pairs(paths, exit_info):
    index = overlap_index(paths)
    candidate_pairs = set()
    for ids in index.values():
        for a, b in combinations(sorted(set(ids)), 2):
            candidate_pairs.add((a, b))

    funnel = Counter()
    records = []
    for a, b in sorted(candidate_pairs):
        p, q = paths[a], paths[b]
        funnel["overlap_pairs"] += 1
        if set(p.endpoints) & set(q.endpoints):
            funnel["check_endpoint_conflict"] += 1
            continue
        funnel["endpoint_disjoint_pairs"] += 1
        motif = classify_motif(p, q, exit_info)
        funnel[f"motif_{motif}"] += 1
        xor_mask = p.mask ^ q.mask
        delta = p.mask.bit_count() + q.mask.bit_count() - xor_mask.bit_count()
        ctype = cancellation_type(delta, xor_mask)
        status = ("GRAPH_REPRESENTATION_ANOMALY"
                  if ctype == "FULL_PHYSICAL_CANCELLATION" else "CENSUS")
        composability = "UNPROVEN" if motif == "IIIa" else "PROVEN"
        eligible = motif != "IIIa"
        records.append(MotifRecord(
            id=len(records), sector=p.sector, motif=motif,
            cancellation_type=ctype, path_ids=(a, b),
            endpoints=(p.endpoints, q.endpoints),
            graph_costs=(p.graph_cost, q.graph_cost),
            physical_masks=(p.mask, q.mask), xor_mask=xor_mask, delta=delta,
            boundary_nodes=tuple(sorted(set(
                [n[1] for n in p.node_path + q.node_path
                 if isinstance(n, tuple) and n[0] == "b"]))),
            composability=composability,
            eligible_for_oracle_pipeline=eligible,
            epistemic_status=status,
        ))
    funnel["overlap_no_cancellation"] = sum(r.delta == 0 for r in records)
    funnel["partial_cancellation"] = sum(r.cancellation_type == "PARTIAL" for r in records)
    funnel["full_cancellation"] = sum(
        r.cancellation_type == "FULL_PHYSICAL_CANCELLATION" for r in records)
    return funnel, records


def run_sector(d, sector):
    code = build_unrotated_planar_surface_code(d)
    geo = geometry_signature(code, sector)

    # L1: construct static graph and establish graph-level exit multiplicity.
    adjacency, edges = graph_construction(code, sector)
    graph = graph_signature(edges)
    exit_info, anomalies = analyze_boundary_exit_multiplicity(edges)
    if anomalies:
        raise RuntimeError(f"ANOMALOUS exit multiplicity: {anomalies}")

    # Boundary contract: the shortest-path catalog must be extensionally
    # consistent with the graph before any catalog path is flattened or used.
    catalog = connection_catalog(adjacency, geo["check_count"])
    graph_catalog_check = cross_check_graph_catalog_boundary_attachments(edges, catalog)

    # Only after the hard-stop consistency layer may path interpretation begin.
    paths = flatten_catalog(catalog, sector)
    funnel, records = scan_pairs(paths, exit_info)
    return {
        "sector": sector,
        "geometry": geo,
        "geometry_sha256": stable_hash(geo),
        "graph_edges": len(edges),
        "graph_sha256": stable_hash(graph),
        "graph_catalog_cross_check": graph_catalog_check,
        "paths_total": len(paths),
        "catalog_sha256": stable_hash(path_signature(paths)),
        "connection_path_histogram": sorted(
            ((repr(k), v) for k, v in connection_histogram(paths).items())),
        "overlap_sha256": stable_hash(
            sorted((q, tuple(ids)) for q, ids in overlap_index(paths).items())),
        "motif_sha256": stable_hash([asdict(r) for r in records]),
        "exit_multiplicity_summary": Counter(
            v["multiplicity"] for v in exit_info.values()),
        "funnel": dict(funnel),
        "historical_run_A": HISTORICAL_RUN_A,
        "records": records,
    }


def compact(result):
    return {
        "sector": result["sector"],
        "geometry": (result["geometry"]["data_count"],
                     result["geometry"]["check_count"]),
        "graph_edges": result["graph_edges"],
        "graph_catalog_cross_check": result["graph_catalog_cross_check"],
        "paths_total": result["paths_total"],
        "funnel": result["funnel"],
        "exit_multiplicity_summary": dict(result["exit_multiplicity_summary"]),
        "hashes": {k: result[k] for k in (
            "geometry_sha256", "graph_sha256", "catalog_sha256",
            "overlap_sha256", "motif_sha256")},
        "historical_run_A": result["historical_run_A"],
    }


def main():
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    all_results = []
    for sector in ("Z", "X"):
        result = run_sector(d, sector)
        all_results.append(result)
        print(json.dumps(compact(result), sort_keys=True, indent=2, default=list))
    if len(all_results) == 2:
        z, x = all_results
        print("SECTOR_SYMMETRY", compact(z) == compact(x))
    print("PROVENANCE_STATUS UNRECONCILED")
    print("HISTORICAL_RUN_A_NOT_REPRODUCED_BY_CLAIM")


if __name__ == "__main__":
    main()
