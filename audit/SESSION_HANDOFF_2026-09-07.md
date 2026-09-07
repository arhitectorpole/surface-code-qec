# Session Handoff — 2026-09-07

## Purpose

This file preserves the current decoder/QEC investigation state so that a later chat can resume from the repository rather than relying on transient conversation context.

## Repository state

- Repository: `arhitectorpole/surface-code-qec`
- Working branch: `experiment/level4c-contract-v1`
- Production branch remains frozen.
- Draft PR #1 remains open/unmerged.
- Last known PR head: `dec1565a761d827a55b2817a0f9a493f5065a191`
- Base `main`: `1bba4c16942ecf6e35ae1ea715cf2423e0d5a913`

## Canonical source versions

### S0 geometry

`src/s0_geometry.py`

- Blob SHA: `1e52217e7bbb56103977c68a7aaa8cbda92521af`
- d=3: 13 data qubits, 6 checks per CSS sector.
- d=5: 41 data qubits, 20 checks per CSS sector.

### Level-4 common helper

`tests/_level4_common.py`

- Blob SHA: `3d826f1e716b19b109a95f42235a0a58f4a025bc`
- This is the committed reference used for provenance reconciliation.
- Verified catalog keys:
  - `('pair', i, j)`
  - `('boundary', i, side)`
- Check-check edge metadata contains `kind`, `checks`, `qubit`.
- Check-boundary edge metadata contains `kind`, `check`, `qubit`, `side`.
- `all_shortest_paths()` enumerates all shortest paths.

### Frozen production baseline

`src/decoder_lib_v2.py`

- Blob SHA on working branch: `89ba8fd0cdf93fddb392ff4303015a7776750eab`
- Remains frozen; do not update as part of reconciliation.

## Validated d=3 artifacts

- `tests/test_level4c_graph_contract_d3.py`
  - Blob SHA: `18d587f5013e6e8f8ba401d2a3eaca3a09430633`
  - 64/64 syndromes per sector matched the independent physical oracle.
  - 128 total cases, 0 failures.
- `tests/test_level4c_a_shortest_path_completeness_d3.py`
  - Blob SHA: `7c52ee28abdc4751f2597d3525f8c8dd0ad710eb`
  - d=3 all-simple-path attack found no oracle-minimum mask missing from shortest-path candidate space.
  - 57 shortest constituent paths/sector; 1889 simple constituent paths/sector.
- `tests/test_level4d_mwpm_admissibility_d3.py`
  - Blob SHA: `ea42d1e43cdac2ba0555b312acc90c97c7f9b954`
  - 256 mode-cases total, 0 failures.
  - Graph-cost and physical-constituent-cost modes both matched the oracle at d=3.

## Current epistemic status

```text
S0 geometry                         PROVEN
4A/4B historical physical facts    PRIOR EVIDENCE / provenance gap
Graph Contract d=3                 EXTENSIONALLY VALIDATED
4C                                  PASS
4C-A shortest-path completeness     PASS (d=3)
4D MWPM admissibility               PASS (d=3)
Boundary ontology                   UNPROVEN
d > 3                               UNTESTED until current census/reconciliation
Concrete external MWPM solver      UNVALIDATED
Production graph transfer           BLOCKED
```

## Current reconciliation problem

A prior diagnostic d=5 path-cancellation run reported, per sector:

```text
shortest paths:       546
graph edges:           45
overlap_pairs:         22034
partial_cancellation:  22034
full_cancellation:     0
motif_I:               16558
motif_II:               4864
motif_IIIa:              212
motif_IIIb:               18
motif_IIIc:              382
```

These numbers are **NOT currently accepted evidence**. An independent reconstruction from the committed `_level4_common.py` produced different totals. Therefore the prior run is explicitly `UNRECONCILED` and must not be used to infer graph semantics or to create an audit claim.

Do not tune the new implementation to reproduce `212` or `22034`.

## Current architectural rules

### Exit multiplicity

Boundary-node identity is the `side` in verified catalog edge metadata. Corner-ness is not an input assumption.

For each physical qubit `q`, derive:

```text
q -> {(check, side), ...}
```

from verified check-boundary edges.

Classify only the observed incidence cardinality:

```text
1 attachment -> SINGLE
2 attachments -> DOUBLE
>2 attachments -> ANOMALOUS
```

`DOUBLE` is a census label only. It does not assert geometric corner semantics.

For every attachment preserve provenance:

```text
(qubit, check, side)
```

`ANOMALOUS` must stop motif classification for that sector after its diagnostic report is emitted; there is no silent continuation.

### Motif funnel

The pairwise funnel is:

```text
L0 geometry
  -> L1 graph
  -> L2 shortest-path corpus
  -> L3 canonicalization
  -> L4 physical-overlap index
  -> L5 pairwise structural filters
       |-- check endpoint conflict -> reject
       `-- endpoint-disjoint -> classify_motif
  -> L6 motif classification
```

Do not put a blanket endpoint-disjoint gate before motif classification if IIIa is defined by shared boundary-node identity.

The accounting invariant is:

```text
overlap_pairs = check_endpoint_conflict + endpoint_disjoint_pairs
endpoint_disjoint_pairs = motif_I + motif_II + motif_IIIa + motif_IIIb + motif_IIIc
```

### Cancellation

For path physical masks `p`, `q`:

```text
Delta = |p| + |q| - |p xor q| = 2*|p & q|
```

The overlap index is lossless for cancellation detection because `Delta > 0` iff physical supports intersect.

`overlap_no_cancellation == 0` under an overlap-index definition is tautological, not a substantive finding.

## Next required step

Run provenance reconciliation for `run_B`, separately for Z and X, comparing against the historical/diagnostic `run_A` only as a provenance target:

1. L0 geometry signature
2. L1 graph signature
3. L2 shortest-path catalog
4. L3 canonicalized path corpus
5. L4 overlap index / overlap-pair count
6. L5 structural-filter funnel
7. L6 motif classification

Stop and report the **first divergent layer**. Do not interpret downstream differences until the divergence is localized.

## Historical/provenance caveat

The exact historical 4A-v4 and 4B-v2 source/output artifacts are not present on `main`; reconstructed substitutes must not be presented as historical artifacts.

The original `decoder_lib.py` is unavailable. `decoder_lib_v2.py` is a new baseline, not a reconstruction.
