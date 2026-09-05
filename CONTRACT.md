# decoder_lib_v2 Contract

**Status:** frozen baseline contract + experimental validation gate

- Original S1 `decoder_lib.py`: unavailable.
- `decoder_lib_v2.py`: new baseline, not a reconstruction.
- Created: 2026-09-05.

## Architecture

```text
canonical S0 geometry
        ↓
decoding-graph construction
        ↓
MWPM backend
        ↓
deterministic correction
        ↓
syndrome + logical-sector checks
        ↓
independent exact benchmark
```

## Geometry

- Code: unrotated planar surface code.
- Distance: odd `d >= 3`.
- Data qubits: `d² + (d-1)²`.
- Stabilizers: X/Z checks defined by canonical S0 geometry.
- d=3: 13 data qubits and 12 checks (6 X, 6 Z).
- Stabilizer rank and syndrome-space size are validated rather than assumed.

## Decoder

- Algorithm: MWPM.
- Weights: unit physical-error weights for the declared phenomenological model.
- Boundary handling: virtual boundary nodes with **physical distance/cost**.
- Tie policy: deterministic; undirected matching edges are canonicalized before lexicographic comparison.
- Output: deterministic correction bitmask on data qubits.

## Logical sector

For the fixed physical logical-Z path `logZ_set` inherited from S0:

`sector = popcount(correction & logZ_mask) % 2`

The MWPM result is a witness only. It is not treated as the exact minimum logical sector.

## Diagnostics

`decode()` returns one deterministic correction. Degeneracy diagnostics are separate and may enumerate optimal matchings. Until explicit enumeration is implemented, degeneracy counts must not be claimed as known.

## Required invariants

- Correct data/check counts.
- Correct stabilizer/check incidence.
- Correct rank.
- Correction reproduces the input syndrome.
- Claimed MWPM weight matches the returned witness.
- Boundary matching is physically weighted.
- Deterministic tie handling is reproducible.

## Benchmark separation

Independent exact benchmarking compares MWPM logical sector with exact `w0/w1` minima. Weight-bounded d=5 scans must explicitly track unresolved cases when the MWPM witness lies outside the explored range.

Historical S1/S2 results are not retroactively validated by v2.

## Experimental Validation Status

### Current gate: Level 4A-v3

`tests/test_level4a_v3_boundary_termination.py` is the current validation frontier for the geometry-stage baseline.

It independently enumerates physical d=3 error masks for every singleton syndrome and records:

- physical minimum weight;
- all minimum physical representatives;
- incidence endpoints (`deg_sector == 1` data qubits);
- physical sides touched by each endpoint.

A corner's two coordinate sides are retained as properties of the **same physical endpoint**. They are not interpreted as two independent virtual-boundary choices.

The test reports the current coordinate boundary formula as a diagnostic but does not use that formula to define the physical oracle or to prove boundary semantics.

### Validation gate

The following changes are blocked until Level 4A-v3 and its stdout have been reviewed:

- no boundary-semantic patch to `build_decoding_graph()`;
- no population of `defect_graph`;
- no MWPM implementation based on unvalidated boundary edges.

### Next gates

```text
Level 4A-v3
    ↓
boundary termination contract
    ↓
Level 4B: independent physical pair oracle
    ↓
defect_graph edge contract
    ↓
Level 4C: graph path → physical correction
    ↓
MWPM
```

Level 4B must compare every same-sector check pair against an independent physical minimum before graph distances are accepted. Level 4C must verify that graph paths recover syndrome-correct physical masks and that their physical weights agree with the relevant oracle minima.

The audit history and rejected experiments are recorded in `AUDIT.md`.
