# Audit Record

## Current validation frontier

**Date:** 2026-09-07  
**Branch:** `main`  
**Current frontier:** Pre-implementation Graph Contract hypothesis informed by Level 4A-v4 and Level 4B-v2

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

For reported d=3 weight-1 pair cases, the single-qubit minimum representative coincides with a shared data qubit in the incidence intersection `Q(c1) ∩ Q(c2)`.

This establishes a physical primitive transition candidate:

`check c1 <-> shared data qubit q <-> check c2`

with physical representative weight 1.

However, this does **not** yet prove that the future decoding graph must encode that physical primitive as one direct check-to-check graph edge.

For pair syndromes with larger physical minima, the oracle provides the target physical cost and representative provenance, but graph distance and graph path structure remain unproven.

## Pre-implementation Graph Contract hypothesis

The following is a **hypothesis to be tested**, not an implementation specification yet.

### H1 — Physical primitive for shared-qubit pairs

If two checks in the same CSS sector share a data qubit `q`, and a single-qubit error on `q` produces exactly the two-check syndrome `{c1, c2}`, then `(c1, q, c2)` is a validated physical primitive of weight 1.

Candidate graph consequence:

- the eventual decoding graph should be capable of representing this primitive with total graph cost 1;
- provenance back to the physical qubit `q` must be retained.

Unproven:

- whether the representation must be one direct edge or a different graph construction with the same physical semantics.

### H2 — Physical endpoint primitive for singleton syndromes

If a minimum singleton representative terminates at a concrete data qubit `q` with `deg_sector(q) == 1`, then `(c, q)` is a validated physical endpoint primitive.

Known metadata include the coordinate and physical sides containing `q`.

Candidate graph consequence:

- the eventual decoding graph must be capable of representing a termination whose recovered physical correction includes the validated endpoint provenance;
- the graph cost assigned to that termination must be validated against the independent physical oracle.

Still unproven:

- which topological boundary component `q` belongs to for decoding purposes;
- how a topological boundary component maps to a virtual graph boundary node;
- whether a corner endpoint corresponds to one or more virtual graph choices;
- whether `coordinate_distance/2 + 1` is exact once the correct boundary semantic has been identified.

### H3 — Physical metric preservation

For every validated graph connection or graph path eventually introduced, the implementation must preserve both:

1. **syndrome semantics** — recovered physical correction reproduces the intended sector syndrome;
2. **physical metric** — recovered correction has the physical weight predicted by the independent oracle for the tested d=3 case.

Graph cost alone is not accepted as a substitute for physical correction weight.

### H4 — Provenance is part of the contract

Every primitive graph connection that participates in physical recovery must retain enough provenance to reconstruct the contributing data-qubit correction.

A graph edge or path without physical recovery provenance is insufficient for Level 4C validation.

## Current known / unknown state

### Established

- S0 is the canonical geometry/incidence source.
- d=3 has 13 data qubits and 12 stabilizers in the current baseline.
- Singleton physical minima can be obtained independently by exhaustive enumeration.
- A minimum singleton representative can be inspected through its actual incidence endpoint.
- Pair physical minima can be obtained independently by exhaustive enumeration.
- Weight-1 pair representatives can be checked directly against shared-qubit incidence provenance.
- Syndrome reproduction can be checked independently of the decoder backend.

### Not established

- The correct semantic mapping from a physical incidence endpoint to a topological boundary component.
- The mapping from a topological boundary component to a virtual graph boundary node.
- Whether the current `coordinate_distance/2 + 1` formula is exact for every physically valid boundary termination.
- Whether each shared-qubit physical primitive should be encoded as one direct check-to-check graph edge.
- Exact graph distances for pair syndromes with physical minimum weight >= 2.
- Path recovery from the eventual graph back to a physical correction.
- MWPM correctness.

## Change-control rule

Do **not** patch `build_decoding_graph()` merely to fit Level 4A-v4 or Level 4B-v2 observations.

Do **not** populate `defect_graph` until the physical boundary semantic and pair representation contracts have been explicitly tested.

Do **not** equate coordinate-side metadata with graph-boundary identity.

Do **not** use MWPM results to define or validate the physical oracle.

`src/decoder_lib_v2.py` and `src/s0_geometry.py` remain frozen during this pre-contract validation stage.

## Next experiments

1. Preserve the Level 4A-v4 endpoint catalogue as an audit artifact.
2. Preserve the Level 4B-v2 pair catalogue and its shared-qubit provenance as an audit artifact.
3. Formulate and test a boundary-semantic hypothesis mapping physical endpoints to topological boundary components without using the production decoder as the oracle.
4. Formulate the pair graph-representation hypothesis and verify that it can reproduce all d=3 pair physical minima with physical provenance.
5. Only then construct a candidate `defect_graph`.
6. Run Level 4C: graph path -> physical correction, checking syndrome reproduction, physical weight, and provenance.
7. Only after these layers pass, implement the MWPM backend.

## Traceability

The Level 4A-v3 test was added as a standalone historical validation artifact. Level 4A-v4 and Level 4B-v2 refine the evidence boundary: they catalogue physical facts while deliberately leaving graph semantics unproven.

Production decoder code remains unchanged by these audit steps.

Git history should preserve the physical catalogues, this Graph Contract hypothesis, and any later production implementation changes as separate evidence layers.
