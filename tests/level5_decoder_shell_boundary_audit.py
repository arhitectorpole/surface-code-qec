"""Level 5: audit decoder_lib_v2 geometry-shell boundary costs against the graph contract.

For every check, compares:
  decoder  : weight_to_boundary on the node(s) it assigns to that check's sector
  contract : BFS distance in the GRAPH_CONTRACT graph to each side T/B/L/R
  oracle   : exact min physical weight of the single-defect syndrome (d<=5, BFS oracle)
Reports mismatches; does not modify the decoder.
"""
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.s0_geometry import build_unrotated_planar_surface_code
from src.decoder_lib_v2 import build_decoding_graph, CheckType
from tests._level4_common import graph_construction
from tests.level5_syndrome_bfs_oracle import qubit_columns, bfs_min_weight


def side_dists(adjacency, i):
    d = {('c', i): 0}
    q = deque([('c', i)])
    while q:
        u = q.popleft()
        for e in adjacency[u]:
            v = e[1] if e[0] == u else e[0]
            if v not in d:
                d[v] = d[u] + 1
                q.append(v)
    return {s: d[('b', s)] for s in "TBLR"}


def main():
    total_bad = 0
    for dist in (3, 5, 7):
        code = build_unrotated_planar_surface_code(dist)
        graph = build_decoding_graph(dist)
        nz = len(code["z_checks"])
        for sector, ctype, nodes in (("Z", CheckType.Z, ("top_Z", "bottom_Z")),
                                     ("X", CheckType.X, ("left_X", "right_X"))):
            adjacency, _ = graph_construction(code, sector)
            m = len(code["z_checks"] if sector == "Z" else code["x_checks"])
            oracle = None
            if dist <= 5:
                _, cols = qubit_columns(code, sector)
                oracle = bfs_min_weight(m, cols)
            offset = 0 if sector == "Z" else nz
            bad_oracle = bad_set = 0
            example = None
            for i in range(m):
                cid = i + offset
                assert graph.stabilizers[cid].check_type is ctype
                dec = sorted(graph.boundary_nodes[n].weight_to_boundary[cid] for n in nodes)
                sd = side_dists(adjacency, i)
                con = sorted(sd.values())
                truth = min(sd.values()) if oracle is None else int(oracle[1 << i])
                if min(dec) != truth:
                    bad_oracle += 1
                    example = example or (i, graph.stabilizers[cid].position, dec, sd, truth)
                # decoder's two values should be the two sides the contract says this sector terminates on
                if sorted(sd.values())[:2] != dec and sorted(set(sd.values()))[:1] != dec[:1]:
                    bad_set += 1
            print(f"d={dist} sector={sector} checks={m} decoder_min_vs_true_single_defect_mismatches={bad_oracle}"
                  + (f" example(check={example[0]} pos={example[1]} decoder={example[2]} contract_sides={example[3]} true={example[4]})" if example else ""))
            total_bad += bad_oracle
    print(f"TOTAL_MISMATCHES={total_bad}")
    print("RESULT: " + ("PASS" if total_bad == 0 else "FAIL"))


if __name__ == "__main__":
    main()
