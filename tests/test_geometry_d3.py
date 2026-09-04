import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.s0_geometry import build_unrotated_planar_surface_code
from src.decoder_lib_v2 import build_decoding_graph


def gf2_rank(rows, ncols):
    rows = list(rows)
    rank = 0
    for col in range(ncols):
        pivot = next((i for i in range(rank, len(rows)) if (rows[i] >> col) & 1), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for i in range(len(rows)):
            if i != rank and ((rows[i] >> col) & 1):
                rows[i] ^= rows[rank]
        rank += 1
    return rank


def test_d3_geometry_counts():
    code = build_unrotated_planar_surface_code(3)
    assert len(code["data"]) == 13
    assert len(code["z_checks"]) == 6
    assert len(code["x_checks"]) == 6


def test_d3_check_weights():
    code = build_unrotated_planar_surface_code(3)
    weights = [len(qs) for _, qs in code["z_checks"] + code["x_checks"]]
    assert sorted(weights) == [3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4]


def test_d3_full_css_stabilizer_rank_is_12():
    code = build_unrotated_planar_surface_code(3)
    n = len(code["data"])
    rows = []

    # X stabilizers occupy the X half of the CSS Pauli vector;
    # Z stabilizers occupy the Z half. This preserves Pauli type.
    for _, qs in code["x_checks"]:
        rows.append(sum(1 << q for q in qs))
    for _, qs in code["z_checks"]:
        rows.append(sum(1 << (n + q) for q in qs))

    assert gf2_rank(rows, 2 * n) == 12


def test_d3_syndrome_ranks_and_space():
    code = build_unrotated_planar_surface_code(3)
    n = len(code["data"])
    z_incidence = [sum(1 << q for q in qs) for _, qs in code["z_checks"]]
    x_incidence = [sum(1 << q for q in qs) for _, qs in code["x_checks"]]

    # X data errors are detected by Z checks; Z data errors by X checks.
    assert gf2_rank(z_incidence, n) == 6
    assert gf2_rank(x_incidence, n) == 6
    assert 2 ** (6 + 6) == 4096


def test_decoder_graph_matches_s0_counts():
    graph = build_decoding_graph(3)
    assert graph.n_data == 13
    assert graph.n_checks == 12
    assert len(graph.stabilizers) == 12
    assert graph.logZ_mask.bit_count() == 3
    assert graph.defect_graph == {}


def test_logz_path_is_left_edge_of_canonical_frame():
    code = build_unrotated_planar_surface_code(3)
    expected = {q for q, (_, j) in enumerate(code["data"]) if j == 0}
    graph = build_decoding_graph(3)
    assert graph.logZ_set == expected
