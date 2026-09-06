# Audit Record

## Current validation frontier

**Date:** 2026-09-07  
**Branch:** `experiment/level4c-contract-v1`  
**Current frontier:** Level 4C d=3 graph-contract validation — PASS on sector-local syndrome spaces

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

This test remains historical evidence for the endpoint invariant, but its wording has been superseded by the stricter Level 4A-v4 catalogue distinction below.

## Level 4A-v4 — Endpoint Incidence Catalogue

The active singleton interpretation is deliberately limited to physical facts.

For every sector and every singleton syndrome, the catalogue records:

- the minimum physical weight;
- every minimum physical representative;
- the concrete data-qubit endpoint(s) identified by sector incidence degree `== 1`;
- endpoint coordinates;
- physical boundary sides touched by each endpoint, as geometry metadata only;
- the current v2 boundary weights as a diagnostic comparison only.

### Established by the catalogue

- singleton minimum physical representatives are obtained independently from S0 incidence;
- each minimum singleton representative at d=3 has exactly one incidence endpoint;
- a corner endpoint remains one physical data qubit even when its coordinate belongs to two physical sides;
- for some checks the currently assigned v2 boundary components do not contain a weight equal to the singleton physical minimum.

The last item is classified as a **DIAGNOSTIC DISCREPANCY**, not as a proof that the scalar cost formula itself is wrong.

### Explicitly unproven

The following mapping remains unproven:

`physical endpoint -> topological boundary component -> graph boundary node`

In particular, `physical_sides(q)` is metadata. It must not be treated as a graph-boundary identity without an independent semantic argument.

## Level 4B-v2 — Pair Incidence Catalogue

The pair catalogue independently enumerates minimum physical representatives for every pair syndrome within each CSS sector.

For each pair `(c1, c2)` it records:

- physical minimum weight;
- all minimum physical representative masks;
- support qubits of each representative;
- the pure-incidence intersection `Q(c1) ∩ Q(c2)`;
- which shared incidence qubits occur in the representative support;
- coordinates / physical sides as geometry metadata only.

### Established pair facts

For d=3 weight-1 pair cases, the single-qubit minimum representative coincides with a shared data qubit in the incidence intersection `Q(c1) ∩ Q(c2)`.

This establishes a physical primitive transition candidate:

`check c1 <-> shared data qubit q <-> check c2`

with physical representative weight 1.

However, this does **not** by itself prove that the future decoding graph must encode that physical primitive as one direct check-to-check graph edge. The direct-edge representation is a graph hypothesis tested below.

For pair syndromes with larger physical minima, the oracle provides the target physical cost and representative provenance, but graph distance and graph path structure were initially unproven.

## Pre-implementation Graph Contract hypothesis

`GRAPH_CONTRACT.md` v1.1 defines the candidate graph construction and an explicit d=3 validation scope. The contract remains a reference specification; production code is not changed by the validation.

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

### Result

Captured execution artifact:

`audit/artifacts/level4c_graph_contract_d3.stdout`

Result:

- Z sector: 64/64 cases matched the physical oracle; 0 failures.
- X sector: 64/64 cases matched the physical oracle; 0 failures.
- Total: 128/128 sector-local syndrome cases; `TOTAL_FAILURES=0`; `RESULT: PASS`.

This is a **PASS for extensional equivalence at d=3 on the tested sector-local syndrome spaces**.

### What the PASS establishes

For this d=3 reference implementation, the candidate graph construction generates at least one syndrome-correct physical mask for every sector-local syndrome, and the minimum physical weight among generated valid masks equals the independently enumerated physical oracle minimum.

This validates the candidate graph construction as a search representation of the physical decoding problem on the tested d=3 spaces.

### What the PASS does not establish

The PASS does not by itself prove a unique physical interpretation of every boundary component. In particular, the semantic statement

`physical endpoint -> topological boundary component -> graph boundary node`

remains an interpretation hypothesis even though the tested graph construction is extensionally correct for d=3.

It also does not establish correctness for d>3, nor does it establish MWPM correctness.

## Current known / unknown state

### Established

- S0 is the canonical geometry/incidence source.
- d=3 has 13 data qubits and 12 stabilizers in the current baseline.
- Singleton physical minima can be obtained independently by exhaustive enumeration.
- A minimum singleton representative can be inspected through its actual incidence endpoint.
- Pair physical minima can be obtained independently by exhaustive enumeration.
- Weight-1 pair representatives can be checked directly against shared-qubit incidence provenance.
- The candidate Graph Contract construction passes independent Level 4C validation on all 128 d=3 sector-local syndrome cases.
- Syndrome reproduction can be checked independently of the production decoder backend.

### Not established

- A unique ontological mapping from a physical incidence endpoint to a topological boundary component.
- A unique interpretation of a corner as one or more virtual graph boundary choices beyond the extensional graph behavior observed at d=3.
- Whether the same candidate construction remains correct for d>3 without further validation.
- MWPM correctness and whether an MWPM implementation can recover the exact physical optimum without additional path-state handling.

## Change-control rule

Do **not** patch `build_decoding_graph()` merely to fit Level 4A-v4, Level 4B-v2, or Level 4C observations.

Do **not** populate `defect_graph` in production until the validated graph construction is deliberately transferred after review of the 4C evidence.

Do **not** equate coordinate-side metadata with graph-boundary identity.

Do **not** use MWPM results to define or validate the physical oracle.

`src/decoder_lib_v2.py` and `src/s0_geometry.py` remain frozen during this experimental validation branch.

## Traceability

The physical catalogue scripts and captured stdout are versioned under `tests/` and `audit/artifacts/` in this branch. The Graph Contract is versioned as `GRAPH_CONTRACT.md`.

The production decoder source is unchanged by this work.

Git history preserves the audit evidence and experimental validator separately from any future production implementation.
