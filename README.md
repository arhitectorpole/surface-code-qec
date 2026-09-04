# surface-code-qec

Independent, auditable baseline implementation for decoding an unrotated planar surface code.

## Status

This repository contains a **new baseline** (`decoder_lib_v2.py`). It is **not a reconstruction** of the historical S1 `decoder_lib.py`, which is unavailable.

The canonical S0 geometry is preserved separately and must not be silently modified.

## Methodological rules

- No retroactive validation of historical S1/S2 results with v2.
- Geometry is derived from the canonical S0 source.
- MWPM is a decoder witness, not exact ground truth.
- Exact logical-sector minima are computed externally for benchmark stages.
- Boundary matching uses physical distance/cost, not zero-cost virtual edges.
- Deterministic tie handling is explicit and auditable.
- Decoder output and degeneracy diagnostics remain separate.
- Later observations do not modify earlier frozen stages.

## Planned structure

```text
surface-code-qec/
├── src/
│   ├── s0_geometry.py
│   └── decoder_lib_v2.py
├── tests/
├── benchmarks/
├── audit/
├── docs/
├── PROVENANCE.md
├── CONTRACT.md
└── README.md
```

## Execution sequence

1. Freeze provenance and decoder contract.
2. Preserve canonical S0 geometry.
3. Implement and audit `build_decoding_graph(d)` without MWPM.
4. Validate d=3 geometry invariants.
5. Add MWPM and deterministic witness selection.
6. Validate every reachable d=3 syndrome against an independent exact benchmark.
7. Proceed to d=5 with explicit weight-bounded/unresolved tracking.

See `PROVENANCE.md` and `CONTRACT.md` for the frozen methodological record.
