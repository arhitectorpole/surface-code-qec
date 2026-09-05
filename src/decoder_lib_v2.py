"""decoder_lib_v2.py - new independent surface-code decoding baseline.

Geometry stage: S0-derived decoding graph shell with physical boundary costs.
Original S1 decoder_lib.py is unavailable; this is not a reconstruction.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

IMPLEMENTATION_RECORD = {
    "version": "v2.0",
    "status": "geometry-stage",
    "code_type": "unrotated_planar_surface_code",
    "geometry_source": "s0_geometry.py (canonical)",
    "mwpm_backend": "TBD - detected at runtime",
    "tie_policy": "lexicographic_edge_sort",
    "boundary_handling": "virtual_boundary_nodes_physical_weight",
    "created": "2026-09-05",
    "purpose": "new_baseline_not_reconstruction_of_S1",
}

class CheckType(Enum):
    X = "X"
    Z = "Z"

@dataclass(frozen=True)
class StabilizerInfo:
    check_id: int
    check_type: CheckType
    data_qubits: Tuple[int, ...]
    position: Tuple[int, int]

@dataclass
class BoundaryNode:
    boundary_id: str
    boundary_type: str
    adjacent_defects: Set[int] = field(default_factory=set)
    weight_to_boundary: Dict[int, int] = field(default_factory=dict)

@dataclass
class DecodingGraph:
    d: int
    n_data: int
    n_checks: int
    data_qubits: List[int]
    stabilizers: List[StabilizerInfo]
    check_masks: List[int]
    logZ_set: Set[int]
    logZ_mask: int
    boundary_nodes: Dict[str, BoundaryNode]
    defect_graph: Dict[int, Dict[int, int]]

@dataclass(frozen=True)
class Correction:
    bitmask: int
    weight: int
    logical_sector: int
    syndrome_reproduced: int

@dataclass
class DegeneracyInfo:
    num_optimal_matchings: Optional[int] = None
    sectors_present: Set[int] = field(default_factory=set)
    is_degenerate: Optional[bool] = None
    is_logical_tie: Optional[bool] = None
    matching_details: List[object] = field(default_factory=list)

@dataclass(frozen=True)
class DecodeResult:
    correction: Correction
    degeneracy: DegeneracyInfo
    mwpm_weight: int
    solver_info: Dict[str, object]

def popcount(x: int) -> int:
    return x.bit_count()

def compute_rank_gf2(rows: List[int], ncols: int) -> int:
    work = list(rows)
    rank = 0
    for col in range(ncols):
        pivot = next((i for i in range(rank, len(work)) if (work[i] >> col) & 1), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        for i in range(len(work)):
            if i != rank and ((work[i] >> col) & 1):
                work[i] ^= work[rank]
        rank += 1
    return rank

def build_decoding_graph(d: int) -> DecodingGraph:
    """Build the S0-derived graph shell with physical boundary costs.

    Important: lattice coordinates are spaced by two between neighboring
    stabilizers. Therefore coordinate distance is not itself the physical
    error weight. A boundary-truncated check requires one data error to
    terminate a string, so the boundary cost is coordinate_distance/2 + 1.
    """
    if d < 3 or d % 2 == 0:
        raise ValueError("distance must be odd and >= 3")

    from .s0_geometry import build_unrotated_planar_surface_code
    code = build_unrotated_planar_surface_code(d)
    data = code["data"]
    stabilizers: List[StabilizerInfo] = []
    check_masks: List[int] = []
    check_id = 0
    for check_type, checks in ((CheckType.Z, code["z_checks"]), (CheckType.X, code["x_checks"])):
        for position, qubits in checks:
            qs = tuple(sorted(qubits))
            stabilizers.append(StabilizerInfo(check_id, check_type, qs, position))
            mask = 0
            for q in qs:
                mask |= 1 << q
            check_masks.append(mask)
            check_id += 1

    logZ_set = {q for q, (i, j) in enumerate(data) if j == 0}
    logZ_mask = sum(1 << q for q in logZ_set)

    boundary_nodes = {
        "top_Z": BoundaryNode("top_Z", "Z"),
        "bottom_Z": BoundaryNode("bottom_Z", "Z"),
        "left_X": BoundaryNode("left_X", "X"),
        "right_X": BoundaryNode("right_X", "X"),
    }
    max_coord = 2 * d - 2

    for stab in stabilizers:
        cid = stab.check_id
        i, j = stab.position
        if stab.check_type is CheckType.Z:
            boundary_nodes["top_Z"].adjacent_defects.add(cid)
            boundary_nodes["top_Z"].weight_to_boundary[cid] = i // 2 + 1
            boundary_nodes["bottom_Z"].adjacent_defects.add(cid)
            boundary_nodes["bottom_Z"].weight_to_boundary[cid] = (max_coord - i) // 2 + 1
        else:
            boundary_nodes["left_X"].adjacent_defects.add(cid)
            boundary_nodes["left_X"].weight_to_boundary[cid] = j // 2 + 1
            boundary_nodes["right_X"].adjacent_defects.add(cid)
            boundary_nodes["right_X"].weight_to_boundary[cid] = (max_coord - j) // 2 + 1

    return DecodingGraph(d, len(data), len(stabilizers), list(range(len(data))),
                         stabilizers, check_masks, logZ_set, logZ_mask,
                         boundary_nodes, {})

def audit_geometry(graph: DecodingGraph) -> Dict[str, object]:
    expected_n_data = graph.d ** 2 + (graph.d - 1) ** 2
    expected_n_checks = 2 * graph.d * (graph.d - 1)
    n = graph.n_data
    x_rows = [sum(1 << q for q in s.data_qubits) for s in graph.stabilizers if s.check_type is CheckType.X]
    z_rows = [sum(1 << q for q in s.data_qubits) for s in graph.stabilizers if s.check_type is CheckType.Z]
    css_rank = compute_rank_gf2(x_rows + [m << n for m in z_rows], 2 * n)
    x_rank = compute_rank_gf2(x_rows, n)
    z_rank = compute_rank_gf2(z_rows, n)
    return {
        "d": graph.d, "n_data": graph.n_data, "expected_n_data": expected_n_data,
        "n_checks": graph.n_checks, "expected_n_checks": expected_n_checks,
        "n_x_checks": len(x_rows), "n_z_checks": len(z_rows),
        "x_incidence_rank": x_rank, "z_incidence_rank": z_rank,
        "css_stabilizer_rank": css_rank, "expected_css_rank": expected_n_checks,
        "achievable_syndromes": 2 ** (x_rank + z_rank),
        "logZ_weight": popcount(graph.logZ_mask),
        "defect_graph_populated": bool(graph.defect_graph),
        "boundary_physical_weights_populated": all(
            bool(node.weight_to_boundary) for node in graph.boundary_nodes.values()
        ),
        "pass": graph.n_data == expected_n_data and graph.n_checks == expected_n_checks
        and x_rank == len(x_rows) and z_rank == len(z_rows) and css_rank == expected_n_checks
        and len(graph.logZ_set) == popcount(graph.logZ_mask)
        and all(bool(node.weight_to_boundary) for node in graph.boundary_nodes.values()),
    }

def decode(syndrome: int, graph: DecodingGraph) -> DecodeResult:
    if syndrome < 0 or syndrome >= (1 << graph.n_checks):
        raise ValueError("syndrome outside graph range")
    raise NotImplementedError("MWPM decoder stage is not implemented yet")

def decode_with_diagnostics(syndrome: int, graph: DecodingGraph) -> DecodeResult:
    if syndrome < 0 or syndrome >= (1 << graph.n_checks):
        raise ValueError("syndrome outside graph range")
    raise NotImplementedError("diagnostic enumeration stage is not implemented yet")

def validate_graph(graph: DecodingGraph) -> Dict[str, object]:
    return audit_geometry(graph)

def verify_correction(syndrome: int, correction: Correction, graph: DecodingGraph) -> bool:
    if syndrome < 0 or syndrome >= (1 << graph.n_checks):
        raise ValueError("syndrome outside graph range")
    return correction.syndrome_reproduced == syndrome
