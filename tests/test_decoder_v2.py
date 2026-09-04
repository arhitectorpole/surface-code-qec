import pytest

from src.decoder_lib_v2 import build_decoding_graph, decode, decode_with_diagnostics


def test_invalid_distance_rejected():
    with pytest.raises(ValueError):
        build_decoding_graph(2)
    with pytest.raises(ValueError):
        build_decoding_graph(4)


def test_syndrome_range_is_checked_before_decoder_stage():
    graph = build_decoding_graph(3)
    with pytest.raises(ValueError):
        decode(-1, graph)
    with pytest.raises(ValueError):
        decode(1 << graph.n_checks, graph)


def test_mwpm_is_explicitly_not_claimed_implemented():
    graph = build_decoding_graph(3)
    with pytest.raises(NotImplementedError):
        decode(0, graph)
    with pytest.raises(NotImplementedError):
        decode_with_diagnostics(0, graph)
