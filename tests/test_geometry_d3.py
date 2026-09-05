from src.s0_geometry import build_unrotated_planar_surface_code
from src.decoder_lib_v2 import build_decoding_graph, audit_geometry


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
    assert sorted(weights) == [3] * 8 + [4] * 4


def test_d3_full_css_stabilizer_rank_is_12():
    code = build_unrotated_planar_surface_code(3)
    n = len(code["data"])
    rows = [sum(1 << q for q in qs) for _, qs in code["x_checks"]]
    rows += [sum(1 << (n + q) for q in qs) for _, qs in code["z_checks"]]
    assert gf2_rank(rows, 2 * n) == 12


def test_d3_syndrome_ranks_and_space():
    code = build_unrotated_planar_surface_code(3)
    n = len(code["data"])
    z_rows = [sum(1 << q for q in qs) for _, qs in code["z_checks"]]
    x_rows = [sum(1 << q for q in qs) for _, qs in code["x_checks"]]
    assert gf2_rank(z_rows, n) == 6
    assert gf2_rank(x_rows, n) == 6
    assert 2 ** (6 + 6) == 4096


def test_d3_boundary_types_and_physical_weights():
    graph = build_decoding_graph(3)
    assert set(graph.boundary_nodes) == {"top_Z", "bottom_Z", "left_X", "right_X"}
    assert graph.boundary_nodes["top_Z"].boundary_type == "Z"
    assert graph.boundary_nodes["bottom_Z"].boundary_type == "Z"
    assert graph.boundary_nodes["left_X"].boundary_type == "X"
    assert graph.boundary_nodes["right_X"].boundary_type == "X"

    max_coord = 4
    for stab in graph.stabilizers:
        cid = stab.check_id
        i, j = stab.position
        if stab.check_type.value == "Z":
            assert graph.boundary_nodes["top_Z"].weight_to_boundary[cid] == i // 2 + 1
            assert graph.boundary_nodes["bottom_Z"].weight_to_boundary[cid] == (max_coord - i) // 2 + 1
        else:
            assert graph.boundary_nodes["left_X"].weight_to_boundary[cid] == j // 2 + 1
            assert graph.boundary_nodes["right_X"].weight_to_boundary[cid] == (max_coord - j) // 2 + 1


def test_d3_boundary_weights_are_positive():
    graph = build_decoding_graph(3)
    for node in graph.boundary_nodes.values():
        assert node.weight_to_boundary
        assert min(node.weight_to_boundary.values()) == 1


def test_d3_audit_passes():
    report = audit_geometry(build_decoding_graph(3))
    assert report["pass"] is True
    assert report["css_stabilizer_rank"] == 12
    assert report["achievable_syndromes"] == 4096
    assert report["boundary_physical_weights_populated"] is True


def test_logz_path_is_left_edge_of_canonical_frame():
    code = build_unrotated_planar_surface_code(3)
    expected = {q for q, (_, j) in enumerate(code["data"]) if j == 0}
    graph = build_decoding_graph(3)
    assert graph.logZ_set == expected
