# Audit Record

## Current validation frontier

**Date:** 2026-09-05  
**Branch:** `main`  
**Current frontier:** Level 4A-v3 — Physical Singleton Boundary Termination Oracle

This document records the methodological state of the new `decoder_lib_v2` baseline. The v2 implementation is explicitly a new baseline, not a reconstruction of the unavailable S1 decoder.

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

The oracle also exposed that current v2 hard-codes Z checks to `top_Z/bottom_Z` and X checks to `left_X/right_X`, while physical singleton representatives occur on other physical sides as well.

### Level 4A-v2 — rejected boundary test

The proposed v2 boundary test classified every physical side touched by a `deg_sector == 1` data qubit as an independent termination boundary.

This is rejected because a corner data qubit is one physical endpoint even though its coordinates lie on two physical sides. Flattening those sides into two independent termination choices confuses coordinate membership with boundary semantics.

Therefore the v2 test is not a valid proof of boundary semantics and is retained only as a methodological rejected experiment.

## Level 4A-v3 contract

The current test is `tests/test_level4a_v3_boundary_termination.py`.

For every sector and every singleton syndrome it independently enumerates all physical error masks and records the minimum representatives. For each minimum representative it distinguishes:

- **physical_sides_touched:** coordinate-level sides touched by a data qubit;
- **termination_points:** concrete data-qubit endpoints identified by sector incidence degree `== 1`;
- **termination_boundaries:** sides attached to each endpoint as metadata, without treating a corner's two sides as two independent endpoint choices.

The test deliberately does **not** assert a final semantic mapping from endpoint to a virtual graph boundary. That mapping is the next graph-contract question.

The current v2 coordinate formula is reported only as a scalar diagnostic. A matching scalar weight does not by itself prove boundary semantics.

## Current known / unknown state

### Established

- S0 is the canonical geometry/incidence source.
- d=3 has 13 data qubits and 12 stabilizers in the current baseline.
- Singleton physical minima can be obtained independently by exhaustive enumeration.
- A minimum singleton representative can be inspected through its actual incidence endpoint(s).
- Syndrome reproduction can be checked independently of the decoder backend.

### Not established

- The correct semantic mapping from an incidence endpoint to a virtual boundary node.
- Whether the current `coordinate_distance/2 + 1` formula is exact for every physically valid boundary termination.
- Exact graph edge weights for the future `defect_graph`.
- Path recovery from the eventual graph back to a physical correction.
- MWPM correctness.

## Change-control rule

Do **not** patch `build_decoding_graph()` merely to make Level 4A-v3 pass.

Do **not** populate `defect_graph` until the physical boundary and pair edge contracts have been independently established.

Do **not** use MWPM results to define or validate the physical oracle.

## Next experiments

1. Run Level 4A-v3 and preserve its complete stdout.
2. Use the concrete endpoint records to formulate an explicit boundary-termination contract.
3. Build Level 4B against that contract and compare every check pair with independent physical minima.
4. Only then construct `defect_graph`.
5. Run Level 4C: graph path -> physical correction, checking both syndrome reproduction and physical weight.
6. Only after these layers pass, implement the MWPM backend.

## Traceability

The Level 4A-v3 test was added as a standalone validation artifact. The production decoder remains unchanged by this audit step.

The Git history should preserve the test and this audit record as separate evidence from any later production implementation changes.
