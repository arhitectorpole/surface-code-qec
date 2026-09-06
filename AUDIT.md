# Audit Record

## Current validation frontier

**Date:** 2026-09-07  
**Branch:** `experiment/level4c-contract-v1`  
**Current frontier:** Level 4C + Level 4C-A d=3 graph-contract validation — PASS on sector-local syndrome spaces; production transfer remains blocked pending expert review

This document records the methodological state of the new `decoder_lib_v2` baseline. The v2 implementation is explicitly a new baseline, not a reconstruction of the unavailable S1 decoder.

The production implementation remains frozen at the geometry stage while physical facts are established independently from S0 incidence.

## Evolution of the Level 4 experiment

### Level 4 — exhaustive matching over the incidence-derived graph

The original Level 4 experiment used an incidence-derived sector graph and attempted to validate exact minimum physical representatives by exhaustive matching.

Two methodological defects were identified:

1. graph path cost was incorrectly usable as a pruning bound even though XOR cancellation can make physical correction weight smaller than the sum of path costs;
2. restricting each matching pair to one shortest path was insufficient to establish an exact physical minimum because different paths can XOR-cancel.

The historical failure, including the `Z, s=2` counterexample, remains a diagnostic artifact of that architecture and must not be retroactively used as a validation result for the current v2 graph shell.

### Level 4A / 4B — physical oracle on the current v2 geometry

An independent d=3 brute-force oracle was then used directly on S0 incidence.

Observed facts:

- all 12 singleton syndromes have physical minimum weight 1;
- all minimum singleton representatives reproduce their syndromes;
- all 30 X-sector and 30 Z-sector check pairs have independently computed physical minima;
- the current v2 `defect_graph` is empty, so pair-distance comparison against graph distances is intentionally pending.

The oracle also exposed that current v2 hard-codes Z checks to `top_Z/bottom_Z` and X checks to `left_X/right_X`, while physical singleton representatives can have incidence endpoints located on other physical sides.

This is a diagnostic discrepancy in the current assignment. It is **not** yet a proof of the replacement boundary semantics.

### Level 4A-v2 — rejected boundary test

The proposed v2 boundary test classified every physical side touched by a `deg_sector == 1` data qubit as an independent termination boundary.

This is rejected because a corner data qubit is one physical endpoint even though its coordinates lie on two physical sides. Flattening those sides into two independent termination choices confuses coordinate membership with boundary semantics.

Therefore the v2 test is not a valid proof of boundary semantics and is retained only as a methodological rejected experiment.

### Level 4A-v3 — endpoint invariant

`tests/test_level4a_v3_boundary_termination.py` established the useful incidence invariant that minimum singleton representatives at d=3 have exactly one sector-incidence endpoint with `deg_sector == 1`.

It also retained corner side membership as metadata on one physical endpoint rather than silently turning a corner into two independent endpoint choices.

This test remains historical evidence, but its wording has been superseded by the stricter Level 4A-v4 distinction recorded in prior audit work.

## Level 4A-v4 / Level 4B-v2 provenance status

The historical Level 4A-v4 and Level 4B-v2 source/output files are not present on the current `main` tree. Reconstructed substitutes were deliberately removed and are not treated as historical evidence.

Their previously reported physical observations remain part of the conversation/audit history, while the current branch makes no claim that those exact historical executions are independently reproducible from Git.

## Level 4C — independent graph-contract validation

`tests/test_level4c_graph_contract_d3.py` implements the candidate graph independently from `src/decoder_lib_v2.py` and evaluates it against a fresh exhaustive physical oracle derived from S0 incidence.

The validator:

- enumerates all `2^13 = 8192` physical masks separately for each CSS sector to obtain the exact physical minimum `w_min`;
- treats the syndrome domain as 64 sector-local syndromes per sector, 128 cases total;
- constructs only the candidate edges described by `GRAPH_CONTRACT.md`;
- enumerates all defect matchings and all shortest-path choices for those matchings;
- XORs physical edge masks to form candidate recoveries;
- verifies candidate syndromes independently;
- selects by physical Hamming weight only;
- performs no pruning based on graph cost;
- deduplicates only identical final physical masks, which does not remove any distinct physical support.

The physical oracle is independent of the production decoder and of its graph semantics. It intentionally shares the canonical S0 incidence source with the reference graph constructor.

### Result

Captured execution artifact:

`audit/artifacts/level4c_graph_contract_d3.stdout`

Result:

- Z sector: 64/64 cases matched the physical oracle; 0 failures.
- X sector: 64/64 cases matched the physical oracle; 0 failures.
- Total: 128/128 sector-local syndrome cases; `TOTAL_FAILURES=0`; `RESULT: PASS`.

This is a **PASS for extensional equivalence at d=3 on the tested sector-local syndrome spaces**, not a proof of generalization or MWPM correctness.

## Level 4C-A — shortest-path completeness attack

The initial Level 4C search space contained all defect matchings but only shortest graph paths for each constituent connection. Because XOR cancellation can make a non-shortest graph decomposition physically useful, this restriction was attacked explicitly.

`tests/test_level4c_a_shortest_path_completeness_d3.py` enumerates every simple path between every check-check and check-boundary connection in the same candidate graph. Since paths are simple, the exact finite bound is `|V|-1`; no heuristic path-length cutoff is used.

For each sector at d=3 the candidate graph has 10 nodes and 17 edges:

| Sector | shortest paths | all simple paths | oracle minima missing from G_short | oracle minima missing from G_all | additional valid masks in G_all \\ G_short |
|---|---:|---:|---:|---:|---:|
| Z | 57 | 1889 | 0 | 0 | 5300 |
| X | 57 | 1889 | 0 | 0 | 5300 |

Captured execution artifact:

`audit/artifacts/level4c_a_shortest_path_completeness_d3.stdout`

### Interpretation

The all-simple-path search adds many valid physical masks, so the shortest-path restriction is a genuine reduction of the candidate search space. However, it removes **no physical minimum** found by the exhaustive `2^13` oracle for d=3.

Therefore shortest-path sufficiency is **supported for the tested d=3 domain**, but is not promoted to a general theorem for d>3 or to a proof about a future MWPM implementation.

## Important logical correction to H4

The earlier H4 formulation — that no generated valid mask can have physical weight below the oracle minimum — is not an independent hypothesis. It is true by definition of the exhaustive oracle minimum.

Accordingly, H4 is treated as a derived consistency consequence, not as an independent acceptance gate.

## Current known / unknown state

### Established / supported for d=3

- S0 is the canonical geometry/incidence source.
- d=3 has 13 data qubits and 12 stabilizers in the current baseline.
- The independent physical oracle exhaustively enumerates the 8192 physical masks in each sector.
- The candidate graph search reproduces the oracle-optimal physical weight for all 128 d=3 sector-local syndromes.
- Every oracle-minimum physical mask is represented within the shortest-path-generated search space on d=3; all-simple-path enumeration found no additional oracle minima.
- The candidate graph therefore has an experimentally validated extensional search representation on the tested d=3 sector-local space.

### Not established

- A unique ontological mapping from a physical incidence endpoint to a topological boundary component.
- A unique interpretation of a corner as one or more virtual graph boundary choices beyond the observed d=3 extensional behavior.
- Correctness of the candidate construction for d>3.
- Completeness of shortest-path sufficiency beyond the attacked d=3 case.
- MWPM correctness or equivalence between graph-cost optimization and the exact physical-mask optimum.
- Safe transfer of the validated reference graph into production code without a separate implementation-validation step.

## Change-control rule

Do **not** patch `build_decoding_graph()` merely to fit Level 4A-v4, Level 4B-v2, Level 4C, or Level 4C-A observations.

Do **not** populate `defect_graph` in production until the validated graph construction is deliberately transferred after expert review.

Do **not** equate coordinate-side metadata with graph-boundary identity.

Do **not** use MWPM results to define or validate the physical oracle.

`src/decoder_lib_v2.py` and `src/s0_geometry.py` remain frozen during this experimental validation branch.

## Traceability

The Level 4C and Level 4C-A reference implementations and captured stdout are versioned under `tests/` and `audit/artifacts/` in this branch. The Graph Contract is versioned as `GRAPH_CONTRACT.md`.

The production decoder source is unchanged by this work.

Git history preserves the audit evidence and experimental validators separately from any future production implementation.
