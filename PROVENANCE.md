# Provenance

## Original S1 decoder

The original historical `decoder_lib.py` used for S1/d=3 is currently **unavailable**.

It must not be reconstructed from memory or inferred from downstream artifacts and then treated as the original implementation.

## decoder_lib_v2

`decoder_lib_v2.py` is a **new independent baseline**, created 2026-09-05.

Purpose: establish a clean, auditable implementation against the canonical S0 geometry.

It must **not** be used to retroactively validate historical S1 results.

## Geometry source

The canonical S0 geometry is `src/s0_geometry.py` and is preserved unchanged from the saved S0 artifact.

## Historical results

Historical S1/S2 results remain historical artifacts. Any future v2 benchmark is a new measurement and is not a revalidation of those results.

## Frozen methodological separation

- MWPM output is a decoder witness.
- Exact logical-sector minima are computed independently for benchmark validation.
- Solver tie behavior and physical logical-sector degeneracy are separate diagnostics.
- Boundary costs must represent physical distance/cost.
- No later observation may retroactively modify frozen S0-S11 methodology.
