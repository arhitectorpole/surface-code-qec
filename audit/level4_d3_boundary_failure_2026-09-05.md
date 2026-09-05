# Level 4 d=3 Boundary Termination Failure — 2026-09-05

## Status

**Experiment:** Level 4 fixed exhaustive validation, `d=3`

**Baseline:** `src/decoder_lib_v2.py`

**Test:** `tests/test_level4_exhaustive_d3_fixed.py`

This is an audit record. It does **not** modify the v2 implementation.

## Result

- Total syndromes tested: **128**
- Passed: **78**
- Failed: **50**
- Z-sector: 64 syndromes
- X-sector: 64 syndromes

The test enumerates all matchings and all combinations of shortest paths for each matching. Graph-cost pruning is disabled.

## First counterexample

**Sector:** Z

**Syndrome:** `s = 2` (`000010₂`)

**Exact oracle weight:** `1`

**Graph physical weight:** `1`

**Graph cost:** `1`

**Syndrome verification:** FAIL

Thus the first failure is not caused by shortest-path restriction: it is a singleton termination using a single graph edge of length 1.

## Physical diagnosis

For the Z-sector at `d=3`:

- Z-check 0: position `(0,1)`, support `[0,1,3]`
- Z-check 1: position `(0,3)`, support `[1,2,4]`

The target syndrome `s=2` requires only Z-check 1 to be odd.

The exact brute-force oracle has a one-qubit representative:

- `q2`
- position `(0,4)`
- weight `1`
- syndrome `2`

The graph instead selected the boundary edge:

- Z-check 1 → TOP
- physical provenance `q1`
- `q1` position `(0,2)`

But `q1` belongs to both Z-check 0 and Z-check 1, so its actual Z-sector syndrome is `3`, not `2`.

Therefore physical boundary membership alone is insufficient to establish valid sector termination.

## Additional construction issue

The current boundary construction uses `seen_cb` keyed by `(check_id, side)`. If multiple boundary data qubits connect the same check to the same physical side, only the first provenance is retained.

For the example above, the valid terminating qubit `q2` can therefore be lost behind the earlier `q1` edge.

## Current conclusion

The present rule

`physical boundary membership → check-to-boundary edge`

is too weak.

A valid boundary termination must be derived from the **CSS-sector incidence action** of the physical data qubit, not merely from its membership in the geometric boundary. The physical side should remain a geometric label, but it must not by itself determine whether a qubit can terminate a sector defect.

This counterexample should be resolved before proceeding to production MWPM.

## Methodological note

Do not attribute this first failure to the known shortest-path restriction. The failing case is a singleton with a one-edge path, so no non-shortest path or XOR cancellation is required to expose the defect.

## Provenance

This record corresponds to the clean Level 4 experiment performed after removing graph-cost pruning and enumerating all shortest-path combinations. It is intentionally preserved as a separate audit artifact rather than rewriting the v2 baseline.