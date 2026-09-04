# decoder_lib_v2 Contract

**Status:** frozen baseline contract

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
