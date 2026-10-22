# Level 4D — MWPM Admissibility Attack (d=3)

## Purpose

Level 4D tests the specific gap between:

- exact physical optimization: `min |M|` after XOR of primitive physical masks;
- graph-cost optimization: minimum sum of constituent connection costs before XOR.

This is an adversarial validation layer. It does not modify production code.

## Reference graph

The candidate graph is the construction defined by `GRAPH_CONTRACT.md` and implemented independently from `src/decoder_lib_v2.py`.

For d=3 each sector contains 17 primitive graph edges.

## Exact matching procedure

No external MWPM solver is used. Because d=3 has only six check defects per sector, the test exhaustively enumerates:

1. every allowed pairing of remaining defects and boundary terminations;
2. every minimum-cost constituent path for each connection;
3. every tie among those minimum-cost paths.

This is an exact enumeration of the MWPM objective induced by the selected constituent path-cost model. It is therefore stronger for the d=3 audit than relying on one solver implementation or one arbitrary tie-break rule.

Boundary nodes have unlimited termination capacity, matching the candidate contract semantics.

## Cost models

Two constituent cost models are tested independently:

### Model A — graph cost

`cost(path) = number of graph edges in the path`.

### Model B — physical constituent cost

`cost(path) = Hamming weight of the XOR physical mask of that constituent path`.

The final recovered physical mask is always computed by XOR, and its physical weight is always evaluated separately.

## Acceptance / failure condition

For every sector-local syndrome, every minimum-cost matching witness is checked.

The attack reports a failure if:

- a minimum-cost matching witness is not syndrome-correct;
- the physical weight of a minimum-cost witness differs from the independent exhaustive physical oracle minimum; or
- multiple minimum-cost witnesses produce different physical weights, exposing tie-sensitive correctness.

## Result

The exhaustive d=3 run produced:

```text
Z graph-cost model:     64/64, failures=0
Z physical-cost model:  64/64, failures=0
X graph-cost model:     64/64, failures=0
X physical-cost model:  64/64, failures=0

TOTAL_MODE_CASES=256
TOTAL_FAILURES=0
RESULT: PASS
```

There were no minimum-cost witnesses with invalid syndromes and no cost-tie cases with differing physical weights.

The graph-cost and physical-cost models both had objective ranges `0..3` on the d=3 syndrome space.

## Interpretation

For d=3, the previously identified cancellation mechanism does **not** cause a disagreement between the exact graph-cost MWPM objective and the physical optimum for this candidate graph. Every minimum-cost matching witness tested is compatible with the physical oracle optimum.

This is stronger than the preceding Level 4C result because it directly attacks the possibility that graph-cost optimization could select a physically suboptimal recovery.

However, the result remains a **d=3 admissibility result only**. It does not prove:

- correctness for d>3;
- that a production MWPM implementation preserves all minimum-cost witness choices;
- that solver tie-breaking remains harmless;
- that the candidate graph is the right generalized graph construction;
- that non-shortest paths can never become relevant at larger d.

## Important distinction from Level 4C-A

Level 4C-A established that, at d=3, shortest constituent paths contain all oracle-minimum physical masks found by the all-simple-path search.

Level 4D establishes a different statement: **after restricting to the shortest-path connection space, minimizing the constituent graph cost itself does not select a physically suboptimal recovery at d=3.**

Thus:

```text
4C-A: shortest-path search does not lose the d=3 physical optimum.
4D:   graph-cost MWPM does not lose the d=3 physical optimum.
```

## Current gate status

```text
4C               PASS  (d=3 extensional graph/physical equivalence)
4C-A             PASS  (d=3 shortest-path completeness)
4D               PASS  (d=3 MWPM-cost admissibility)
d > 3            UNTESTED
production MWPM  BLOCKED pending review and higher-distance validation
```
