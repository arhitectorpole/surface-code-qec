# Provenance Reconciliation Plan

**Status:** diagnostic instrument; not a validation claim.

## Objective

Reconcile the previously reported d=5 cancellation-census run (`run_A`) with an independent reconstruction from the committed reference implementation (`run_B`). The goal is to locate the first divergent layer, not to reproduce a predetermined number.

## Source pins

- S0: `src/s0_geometry.py` @ `1e52217e7bbb56103977c68a7aaa8cbda92521af`
- Reference Level-4 helper: `tests/_level4_common.py` @ `3d826f1e716b19b109a95f42235a0a58f4a025bc`

## Layered comparison

### L0 — Geometry

Compare a canonical geometry signature containing at least:

- data-qubit count
- check count per sector
- sorted check coordinates
- sorted check supports
- coordinate-to-data-index mapping where relevant

A mismatch here means geometry/path generation cannot yet be compared downstream.

### L1 — Graph

Compare a canonical sorted graph signature containing edge endpoints and semantic metadata:

- node endpoints
- edge kind
- check identifiers
- physical qubit
- boundary side

Boundary-side identity is an observed catalog field, not an imported geometric interpretation.

### L2 — Shortest-path corpus

Enumerate all shortest paths using the verified catalog key schema:

```text
('pair', i, j)
('boundary', i, side)
```

Record:

- number of connection entries
- total shortest-path records
- per-connection path-count histogram
- canonical path signatures

If total paths differ, the divergence is in path enumeration or graph structure.

### L3 — Canonicalization

Canonicalize paths independently of dictionary/set iteration order. Canonicalization must use semantic path endpoints, graph cost, edge metadata, and physical mask—not raw traversal order.

### L4 — Physical-overlap index

Build the inverted index:

```text
physical qubit -> path IDs
```

Generate unordered path pairs from shared physical support. Use a `seen` set so each pair is examined once.

The overlap-pair count is a diagnostic result, not an externally imposed target.

### L5 — Structural pairwise funnel

Apply filters in this order:

```text
overlap_pairs
  -> check_endpoint_conflict + endpoint_disjoint_pairs
  -> classify_motif(endpoint_disjoint_pairs)
```

Do not reject pairs merely because two paths share a boundary node. IIIa is specifically the candidate class in which endpoint-disjoint paths may share a boundary node.

Required accounting:

```text
overlap_pairs = check_endpoint_conflict + endpoint_disjoint_pairs
endpoint_disjoint_pairs = motif_I + motif_II + motif_IIIa + motif_IIIb + motif_IIIc
```

### L6 — Motif classification

Classify endpoint-disjoint pairs into:

- I: CC/CC
- II: CB/CC
- IIIa: CB/CB, same boundary node
- IIIb: CB/CB, different boundary nodes
- IIIc: IIIb plus observed multi-boundary-exit-qubit involvement

The IIIc label is a census classification based on observed exit multiplicity. It does not prove that the involved qubit is geometrically a lattice corner.

## Exit multiplicity provenance

Derive boundary attachments directly from verified check-boundary edge metadata:

```text
qubit -> {(check, side), ...}
```

Observed cardinalities:

```text
1 -> SINGLE
2 -> DOUBLE
>2 -> ANOMALOUS
```

Preserve the exact attachment tuples in each record. `ANOMALOUS` is a reconciliation finding and must stop sector processing after diagnostics are emitted.

## Cancellation classification

For physical masks `p` and `q`:

```text
Delta = |p| + |q| - |p xor q|
      = 2 * |p & q|
```

Classify:

- `Delta == 0`: no physical cancellation
- `0 < Delta < |p| + |q|`: partial cancellation
- `Delta == |p| + |q|`: full cancellation

If full cancellation is observed, record `GRAPH_REPRESENTATION_ANOMALY`. Do not infer that boundary ontology is wrong from that observation alone.

## Provenance hashes

Compute SHA-256 signatures for:

1. geometry signature
2. graph signature
3. canonical path catalog
4. overlap-pair corpus
5. motif corpus

This makes equality independent of process ordering.

## Stop rule

The reconciliation report must identify the first layer at which `run_A` and `run_B` diverge. Downstream differences are not interpreted until that layer is understood.

In particular:

- do not tune code to reproduce the previously reported `212` IIIa count;
- do not treat `22034` overlap pairs as a target;
- do not create a validation/audit artifact from the unreconciled run;
- do not infer boundary ontology from motif counts alone.

## Current provenance status

```text
run_A: UNRECONCILED
run_B: committed-source reconstruction
212 IIIa: UNRECONCILED, not a target
22034 overlap pairs: UNRECONCILED, not a target
```
