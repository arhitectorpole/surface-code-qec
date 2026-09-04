# Geometry audit notes

## d=3 result

The canonical S0 geometry gives:

- 13 data qubits;
- 6 X checks;
- 6 Z checks;
- 12 total checks;
- X-check incidence rank 6;
- Z-check incidence rank 6;
- full CSS stabilizer rank 12;
- 4096 combined syndrome labels.

## Important rank subtlety

The check-support masks alone are `n_data`-bit objects. If X- and Z-check support masks are stacked into the same 13-bit vector space, their binary rank is only 10. That number is **not** the stabilizer rank, because it erases Pauli type.

For the stabilizer-rank audit, X checks occupy the X half of a `2*n_data` CSS Pauli vector and Z checks occupy the Z half. In that representation the d=3 rank is 12.

Likewise, syndrome coverage is audited through the two CSS incidence maps: X errors are detected by Z checks and Z errors by X checks. Each has rank 6, giving `2^(6+6) = 4096` combined syndrome labels.

This correction is intentional: we do not certify a false rank-12 result from a type-erasing incidence matrix.

## Current implementation boundary

`build_decoding_graph()` currently constructs the S0-derived stabilizer shell and logical-Z path. The defect graph remains empty until the physical-distance boundary construction and MWPM stage are implemented and separately audited.
