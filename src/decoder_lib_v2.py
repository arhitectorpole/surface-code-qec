"""decoder_lib_v2.py - new independent surface-code decoding baseline.

Geometry stage: S0-derived decoding graph shell with physical boundary costs.
Original S1 decoder_lib.py is unavailable; this is not a reconstruction.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

IMPLEMENTATION_RECORD = {
    "version": "v2.0",
    "status": "research-mwpm-d3-d5-validated",
    "code_type": "unrotated_planar_surface_code",
    "geometry_source": "s0_geometry.py (canonical)",
    "mwpm_backend": "exact_bitmask_dp",
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
            boundary_nodes["top_Z"].weight_to_boundary[cid] = j // 2 + 1
            boundary_nodes["bottom_Z"].adjacent_defects.add(cid)
            boundary_nodes["bottom_Z"].weight_to_boundary[cid] = (max_coord - j) // 2 + 1
        else:
            boundary_nodes["left_X"].adjacent_defects.add(cid)
            boundary_nodes["left_X"].weight_to_boundary[cid] = i // 2 + 1
            boundary_nodes["right_X"].adjacent_defects.add(cid)
            boundary_nodes["right_X"].weight_to_boundary[cid] = (max_coord - i) // 2 + 1

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

# ---------------------------------------------------------------------------
# Sector-local exact MWPM (Level 5). Follows GRAPH_CONTRACT.md:
#   * one graph per CSS sector, syndrome is sector-local (bit i = i-th check
#     of that sector in S0 order);
#   * check-check edge iff the two checks share exactly one data qubit;
#   * boundary edge from a check to side T/B/L/R for every data qubit that
#     touches exactly one check of the sector and lies on that side
#     (corner qubits give one edge per side, same physical mask);
#   * every edge costs 1 and carries exactly one data qubit;
#   * exact minimum-cost matching (bitmask DP over defects), no pruning;
#   * deterministic ties: first-found in a fixed order (boundary before pairs,
#     partners ascending) and lexicographically smallest edge sequence by
#     data-qubit index among shortest paths.
# Output weight equals the exact physical minimum (see AUDIT.md, Level 5).
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SectorGraph:
    d: int
    sector: str
    n_data: int
    n_checks: int
    check_masks: Tuple[int, ...]
    # adjacency[node] -> sorted list of (qubit, neighbour); nodes are
    # ("c", i) or ("b", side)
    adjacency: Dict[Tuple[str, object], Tuple[Tuple[int, Tuple[str, object]], ...]]

@dataclass(frozen=True)
class SectorCorrection:
    bitmask: int
    weight: int
    syndrome_reproduced: int
    matching_cost: int

def build_sector_graph(d: int, sector: str) -> SectorGraph:
    if d < 3 or d % 2 == 0:
        raise ValueError("distance must be odd and >= 3")
    if sector not in ("Z", "X"):
        raise ValueError("sector must be 'Z' or 'X'")
    from .s0_geometry import build_unrotated_planar_surface_code
    code = build_unrotated_planar_surface_code(d)
    data = code["data"]
    checks = code["z_checks"] if sector == "Z" else code["x_checks"]
    qsets = [set(qs) for _, qs in checks]
    masks = tuple(sum(1 << q for q in qs) for qs in qsets)
    max_coord = 2 * d - 2
    adj: Dict[Tuple[str, object], List[Tuple[int, Tuple[str, object]]]] = {
        **{("c", i): [] for i in range(len(checks))},
        **{("b", side): [] for side in "TBLR"},
    }
    for i in range(len(checks)):
        for j in range(i + 1, len(checks)):
            common = qsets[i] & qsets[j]
            if len(common) == 1:
                q = next(iter(common))
                adj[("c", i)].append((q, ("c", j)))
                adj[("c", j)].append((q, ("c", i)))
    degree = [0] * len(data)
    for qs in qsets:
        for q in qs:
            degree[q] += 1
    for i, qs in enumerate(qsets):
        for q in qs:
            if degree[q] != 1:
                continue
            x, y = data[q]
            sides = []
            if x == 0:
                sides.append("L")
            if x == max_coord:
                sides.append("R")
            if y == 0:
                sides.append("T")
            if y == max_coord:
                sides.append("B")
            for side in sides:
                adj[("c", i)].append((q, ("b", side)))
                adj[("b", side)].append((q, ("c", i)))
    frozen = {k: tuple(sorted(v, key=lambda t: (t[0], str(t[1])))) for k, v in adj.items()}
    return SectorGraph(d, sector, len(data), len(checks), masks, frozen)

def _bfs_dist(graph: SectorGraph, src):
    from collections import deque
    dist = {src: 0}
    queue = deque([src])
    while queue:
        u = queue.popleft()
        for _, v in graph.adjacency[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist

def _canonical_path_mask(graph: SectorGraph, src, dst_dist) -> int:
    """Lexicographically smallest (by qubit index) shortest path from src to
    the target whose BFS distances are dst_dist; returns XOR of its qubits."""
    mask = 0
    u = src
    while dst_dist[u] > 0:
        for q, v in graph.adjacency[u]:
            if dst_dist.get(v) == dst_dist[u] - 1:
                mask ^= 1 << q
                u = v
                break
    return mask

def syndrome_of_sector_mask(graph: SectorGraph, mask: int) -> int:
    syn = 0
    for i, cm in enumerate(graph.check_masks):
        if popcount(mask & cm) & 1:
            syn |= 1 << i
    return syn

def decode_sector(syndrome: int, graph: SectorGraph) -> SectorCorrection:
    """Exact MWPM decode of one CSS sector. Raises on out-of-range syndrome."""
    if syndrome < 0 or syndrome >= (1 << graph.n_checks):
        raise ValueError("syndrome outside sector range")
    defects = [i for i in range(graph.n_checks) if (syndrome >> i) & 1]
    if not defects:
        return SectorCorrection(0, 0, 0, 0)
    from_check = {i: _bfs_dist(graph, ("c", i)) for i in range(graph.n_checks)}
    dpair = {(a, b): from_check[a][("c", b)] for a in defects for b in defects}
    dbound = {}
    for a in defects:
        best_side = min("TBLR", key=lambda s: (from_check[a][("b", s)], s))
        dbound[a] = (from_check[a][("b", best_side)], best_side)
    memo: Dict[int, Tuple[int, tuple]] = {}
    full = (1 << len(defects)) - 1

    def solve(rem: int):
        if rem == 0:
            return 0, ()
        if rem in memo:
            return memo[rem]
        k = (rem & -rem).bit_length() - 1
        rest = rem & ~(1 << k)
        a = defects[k]
        c, plan = solve(rest)
        best = (dbound[a][0] + c, (("b", a, dbound[a][1]),) + plan)
        r = rest
        while r:
            m = (r & -r).bit_length() - 1
            r &= r - 1
            c2, plan2 = solve(rest & ~(1 << m))
            cand = dpair[(a, defects[m])] + c2
            if cand < best[0]:
                best = (cand, (("p", a, defects[m]),) + plan2)
        memo[rem] = best
        return best

    cost, plan = solve(full)
    mask = 0
    for item in plan:
        if item[0] == "b":
            _, a, side = item
            target = _bfs_dist(graph, ("b", side))
            mask ^= _canonical_path_mask(graph, ("c", a), target)
        else:
            _, a, b = item
            target = _bfs_dist(graph, ("c", b))
            mask ^= _canonical_path_mask(graph, ("c", a), target)
    return SectorCorrection(mask, popcount(mask), syndrome_of_sector_mask(graph, mask), cost)

# ---------------------------------------------------------------------------
# Degeneracy diagnostics (sector-local) and combined decode().
# Witness sets are derived from minimum-cost matchings x shortest-path choices.
# They are physical minimum-weight witnesses (cost == oracle minimum, see
# AUDIT.md Level 5) but are NOT proven to be ALL minimum-weight corrections
# beyond the tested cases; truncation flags report when caps were hit.
# ---------------------------------------------------------------------------

MAX_MATCHINGS = 5000
MAX_WITNESS_MASKS = 20000
MAX_PATHS_PER_CONNECTION = 2000

@dataclass(frozen=True)
class SectorDiagnostics:
    num_optimal_matchings: int
    matchings_truncated: bool
    witness_masks: frozenset
    witnesses_truncated: bool
    logical_classes: frozenset
    is_logical_tie: bool

def _all_shortest_path_masks(graph: SectorGraph, src, target_dist, cap: int):
    """Masks (XOR of qubits) of every shortest path src -> target, deduplicated."""
    out = set()
    stack = [(src, 0)]
    while stack and len(out) < cap:
        u, m = stack.pop()
        if target_dist[u] == 0:
            out.add(m)
            continue
        for q, v in graph.adjacency[u]:
            if target_dist.get(v) == target_dist[u] - 1:
                stack.append((v, m ^ (1 << q)))
    return out

def decode_sector_with_diagnostics(syndrome: int, graph: SectorGraph, logical_mask: int):
    """Exact decode plus enumeration of optimal matchings and their witnesses.

    logical_mask: data-qubit mask whose overlap parity defines the logical class.
    """
    correction = decode_sector(syndrome, graph)
    defects = [i for i in range(graph.n_checks) if (syndrome >> i) & 1]
    if not defects:
        return correction, SectorDiagnostics(1, False, frozenset({0}), False, frozenset({0}), False)
    from_check = {i: _bfs_dist(graph, ("c", i)) for i in range(graph.n_checks)}
    side_dist = {s: _bfs_dist(graph, ("b", s)) for s in "TBLR"}
    memo: Dict[int, int] = {}

    def cost(rem: int) -> int:
        if rem == 0:
            return 0
        if rem in memo:
            return memo[rem]
        k = (rem & -rem).bit_length() - 1
        rest = rem & ~(1 << k)
        a = defects[k]
        best = min(from_check[a][("b", s)] for s in "TBLR") + cost(rest)
        r = rest
        while r:
            m = (r & -r).bit_length() - 1
            r &= r - 1
            best = min(best, from_check[a][("c", defects[m])] + cost(rest & ~(1 << m)))
        memo[rem] = best
        return best

    plans = []
    truncated = False

    def enumerate_plans(rem: int, acc: tuple):
        nonlocal truncated
        if len(plans) >= MAX_MATCHINGS:
            truncated = True
            return
        if rem == 0:
            plans.append(acc)
            return
        k = (rem & -rem).bit_length() - 1
        rest = rem & ~(1 << k)
        a = defects[k]
        total = cost(rem)
        for s in "TBLR":
            if from_check[a][("b", s)] + cost(rest) == total:
                enumerate_plans(rest, acc + (("b", a, s),))
        r = rest
        while r:
            m = (r & -r).bit_length() - 1
            r &= r - 1
            if from_check[a][("c", defects[m])] + cost(rest & ~(1 << m)) == total:
                enumerate_plans(rest & ~(1 << m), acc + (("p", a, defects[m]),))

    enumerate_plans((1 << len(defects)) - 1, ())

    conn_cache: Dict[tuple, set] = {}
    def conn_masks(item):
        if item not in conn_cache:
            if item[0] == "b":
                conn_cache[item] = _all_shortest_path_masks(
                    graph, ("c", item[1]), side_dist[item[2]], MAX_PATHS_PER_CONNECTION)
            else:
                conn_cache[item] = _all_shortest_path_masks(
                    graph, ("c", item[1]), from_check[item[2]], MAX_PATHS_PER_CONNECTION)
        return conn_cache[item]

    witnesses = set()
    wtrunc = False
    for plan in plans:
        acc = {0}
        for item in plan:
            acc = {x ^ y for x in acc for y in conn_masks(item)}
            if len(acc) > MAX_WITNESS_MASKS:
                wtrunc = True
                acc = set(list(acc)[:MAX_WITNESS_MASKS])
        witnesses |= acc
        if len(witnesses) >= MAX_WITNESS_MASKS:
            wtrunc = True
            break
    if any(len(v) >= MAX_PATHS_PER_CONNECTION for v in conn_cache.values()):
        wtrunc = True
    # Keep only valid minimum-weight witnesses (cancellation can only lower weight).
    best_w = min(popcount(w) for w in witnesses | {correction.bitmask})
    witnesses = {w for w in witnesses | {correction.bitmask}
                 if syndrome_of_sector_mask(graph, w) == syndrome and popcount(w) == best_w}
    classes = frozenset(popcount(w & logical_mask) & 1 for w in witnesses)
    return correction, SectorDiagnostics(
        len(plans), truncated, frozenset(witnesses), wtrunc, classes, len(classes) > 1)

@dataclass(frozen=True)
class MajorityTieCorrection:
    bitmask: int
    weight: int
    syndrome_reproduced: int
    count_class0: int          # distinct minimum-weight witnesses with logical class 0
    count_class1: int          # ... with logical class 1
    tie_decided_by_count: bool  # True iff a logical tie was resolved by unequal counts
    truncated: bool            # enumeration caps hit: counts are lower bounds, rule fell back
    num_matchings: int = 0     # optimal matchings enumerated (cap: MAX_MATCHINGS)

def decode_sector_majority(syndrome: int, graph: SectorGraph, logical_mask: int) -> MajorityTieCorrection:
    """Exact MWPM with a likelihood-motivated logical tie rule.

    On a logical tie (minimum-weight corrections exist in both logical classes) the
    class with MORE distinct minimum-weight witnesses is chosen: at leading order in p
    that class is the more probable one. Within the chosen class the lexicographically
    smallest (weight, mask) witness is returned. If counts are equal, or enumeration
    was truncated, the default decode_sector() correction is returned unchanged.
    """
    base, diag = decode_sector_with_diagnostics(syndrome, graph, logical_mask)
    n0 = sum(1 for w in diag.witness_masks if (popcount(w & logical_mask) & 1) == 0)
    n1 = len(diag.witness_masks) - n0
    truncated = bool(diag.matchings_truncated or diag.witnesses_truncated)
    if len(diag.logical_classes) < 2 or n0 == n1 or truncated:
        return MajorityTieCorrection(base.bitmask, base.weight, base.syndrome_reproduced,
                                     n0, n1, False, truncated, diag.num_optimal_matchings)
    want = 1 if n1 > n0 else 0
    best = min((w for w in diag.witness_masks if (popcount(w & logical_mask) & 1) == want))
    return MajorityTieCorrection(best, popcount(best), syndrome_of_sector_mask(graph, best),
                                 n0, n1, True, False, diag.num_optimal_matchings)

_SECTOR_GRAPH_CACHE: Dict[Tuple[int, str], SectorGraph] = {}

def _sector_graph(d: int, sector: str) -> SectorGraph:
    key = (d, sector)
    if key not in _SECTOR_GRAPH_CACHE:
        _SECTOR_GRAPH_CACHE[key] = build_sector_graph(d, sector)
    return _SECTOR_GRAPH_CACHE[key]

def _split_syndrome(syndrome: int, graph: DecodingGraph):
    n_z = sum(1 for st in graph.stabilizers if st.check_type is CheckType.Z)
    z_syn = syndrome & ((1 << n_z) - 1)
    x_syn = syndrome >> n_z
    return z_syn, x_syn, n_z

def _x_sector_logical_mask(graph: DecodingGraph) -> int:
    """Logical-X analogue for the X-sector (Z-type) correction: data qubits with i == 0."""
    from .s0_geometry import build_unrotated_planar_surface_code
    code = build_unrotated_planar_surface_code(graph.d)
    return sum(1 << q for q, (i, j) in enumerate(code["data"]) if i == 0)

def _decode_impl(syndrome: int, graph: DecodingGraph, diagnostics: bool) -> DecodeResult:
    if syndrome < 0 or syndrome >= (1 << graph.n_checks):
        raise ValueError("syndrome outside graph range")
    z_syn, x_syn, n_z = _split_syndrome(syndrome, graph)
    gz = _sector_graph(graph.d, "Z")
    gx = _sector_graph(graph.d, "X")
    n = graph.n_data
    x_logical_mask = _x_sector_logical_mask(graph)
    if diagnostics:
        cz, dz = decode_sector_with_diagnostics(z_syn, gz, graph.logZ_mask)
        cx, dx = decode_sector_with_diagnostics(x_syn, gx, x_logical_mask)
    else:
        cz, cx = decode_sector(z_syn, gz), decode_sector(x_syn, gx)
        dz = dx = None
    # Packed correction: bits [0,n) = X-type flips fixing the Z-check syndrome;
    # bits [n,2n) = Z-type flips fixing the X-check syndrome.
    packed = cz.bitmask | (cx.bitmask << n)
    reproduced = cz.syndrome_reproduced | (cx.syndrome_reproduced << n_z)
    logical = popcount(packed & graph.logZ_mask) % 2  # CONTRACT.md: low n bits only
    correction = Correction(packed, cz.weight + cx.weight, logical, reproduced)
    if diagnostics:
        degeneracy = DegeneracyInfo(
            num_optimal_matchings=dz.num_optimal_matchings * dx.num_optimal_matchings,
            sectors_present=set(dz.logical_classes),
            is_degenerate=(len(dz.witness_masks) > 1 or len(dx.witness_masks) > 1),
            is_logical_tie=dz.is_logical_tie,
            matching_details=[dz, dx],
        )
    else:
        degeneracy = DegeneracyInfo()
    solver_info = {
        "solver": "exact_bitmask_dp_mwpm", "tie_policy": IMPLEMENTATION_RECORD["tie_policy"],
        "z_sector_weight": cz.weight, "x_sector_weight": cx.weight,
        "z_sector_matching_cost": cz.matching_cost, "x_sector_matching_cost": cx.matching_cost,
        "x_sector_logical_class": popcount(cx.bitmask & x_logical_mask) & 1,
        "packing": "bits[0,n)=X-type correction for Z-checks, bits[n,2n)=Z-type correction for X-checks",
    }
    if diagnostics:
        solver_info["diagnostics_truncated"] = bool(
            dz.matchings_truncated or dx.matchings_truncated
            or dz.witnesses_truncated or dx.witnesses_truncated)
        solver_info["x_sector_is_logical_tie"] = dx.is_logical_tie
        solver_info["x_sector_logical_classes"] = sorted(dx.logical_classes)
    return DecodeResult(correction, degeneracy, correction.weight, solver_info)

def decode(syndrome: int, graph: DecodingGraph) -> DecodeResult:
    """Deterministic exact-MWPM correction; degeneracy fields left unknown (None)."""
    return _decode_impl(syndrome, graph, diagnostics=False)

def decode_with_diagnostics(syndrome: int, graph: DecodingGraph) -> DecodeResult:
    """As decode(), plus matching/witness enumeration (see truncation flag in solver_info)."""
    return _decode_impl(syndrome, graph, diagnostics=True)

def validate_graph(graph: DecodingGraph) -> Dict[str, object]:
    return audit_geometry(graph)

def verify_correction(syndrome: int, correction: Correction, graph: DecodingGraph) -> bool:
    if syndrome < 0 or syndrome >= (1 << graph.n_checks):
        raise ValueError("syndrome outside graph range")
    return correction.syndrome_reproduced == syndrome
