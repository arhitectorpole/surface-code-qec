# Graph Contract

## 0. Status and Scope

- **Status:** *Experimental specification* – validated extensionally for the tested d=3 sector-local spaces by Level 4C; not yet promoted to production semantics.
- **Revision note:** v1.2 records the provenance boundary discovered during implementation: the historical Level 4A-v4 and Level 4B-v2 source files are not present on the current `main` tree, so reconstructed scripts are not treated as historical evidence. The candidate graph semantics and 4C result are independently versioned below.
- **Scope:** d=3 surface code (planar, unrotated), CSS stabilizer formalism.
- **Relation to production:** This document defines a candidate graph construction validated independently by Level 4C. **It does not modify** `src/decoder_lib_v2.py` or `src/s0_geometry.py`. Production code remains frozen pending review and deliberate transfer.
- **Epistemic layers:** Each section clearly distinguishes PROVEN facts, HYPOTHESES, and UNPROVEN claims.

---

## 1. Definitions

### 1.1 Data Qubits

Let `D` be the set of data qubits in the unrotated planar surface code of distance `d=3`.
From S0 geometry:

```text
|D| = 13
```

Each data qubit has coordinates `(x, y)` with `x, y ∈ {0, 2, 4}` (step 2).

### 1.2 Check Nodes

There are two CSS sectors: **Z-stabilizers** and **X-stabilizers**.
For d=3, the S0 geometry contains 6 checks per sector and 12 stabilizers total.

We denote local check nodes as `c_i`, `i=0..5`, within each sector.

### 1.3 Sector Incidence

For each check `c` and sector `S ∈ {Z, X}`, the support `Q_S(c)` is the set of data qubits incident to that stabilizer (from S0 geometry).
Incidence degree of a data qubit `q` with respect to sector `S`:

```text
deg_S(q) = |{ c ∈ S : q ∈ Q_S(c) }|
```

### 1.4 Boundary Nodes

We define four topological boundary components for the square lattice:

- `B_T` (top)
- `B_B` (bottom)
- `B_L` (left)
- `B_R` (right)

These are abstract graph nodes, not physical qubits. There are **no separate corner nodes**; corners are represented by adjacency to two boundary nodes.

---

## 2. Proven Physical Primitives

### 2.1 Singleton Endpoint Invariant

The prior Level 4A evidence established, for d=3 single-check syndromes, that minimum physical representatives are single-qubit errors with an incidence endpoint satisfying `deg_S(q) == 1`, and that a corner remains one physical endpoint even when its coordinate touches two sides.

**Provenance status:** The original historical Level 4A-v4 source/output are referenced by prior audit notes but are not present in the current `main` tree. This document therefore does not claim that those historical artifacts are independently reproducible from `main` in their original form.

### 2.2 Shared-Qubit Pair Primitive

The prior Level 4B evidence established, for d=3 weight-1 pair cases, that the single-qubit minimum representative coincides with a shared data qubit in `Q(c_i) ∩ Q(c_j)`.

For the S0 d=3 geometry used here, same-sector pair intersections are at most singleton. If the intersection is empty, no single-qubit error can flip exactly both checks, so `w_min ≥ 2`.

**Provenance status:** The original historical Level 4B-v2 source/output are referenced by prior audit notes but are not present in the current `main` tree. This document does not treat any reconstructed replacement as historical evidence.

---

## 3. Candidate Graph Construction

This section defines a **candidate** graph `G_S = (V, E)` for each sector `S ∈ {Z, X}`.

### 3.1 Check–Check Edges

For every pair of check nodes `(c_i, c_j)` in the same sector:

- If `Q(c_i) ∩ Q(c_j) = {q}` (single shared qubit), then add an undirected edge `e = (c_i, c_j)` with:
  - **weight** = 1 (graph cost)
  - **physical mask** = `{q}`
  - **provenance** = the shared qubit `q`

No other check–check edges are added.

### 3.2 Check–Boundary Edges

For each check node `c` and each data qubit `q ∈ Q(c)`:

- **If** `deg_S(q) == 1`, determine the physical sides of `q` from its coordinates:
  - `x == 0` → side `L`
  - `x == 2d-2` → side `R`
  - `y == 0` → side `T`
  - `y == 2d-2` → side `B`
- For **each** touched side `b`, add an undirected edge `e = (c, B_b)` with:
  - **weight** = 1
  - **physical mask** = `{q}`
  - **provenance** = endpoint qubit `q` and side `b`

Thus, a corner qubit generates two boundary edges with the same physical mask `{q}`.

The mapping from physical side metadata to topological boundary semantics remains an interpretation question even though the candidate construction has passed the d=3 extensional test below.

### 3.3 Edge Provenance

Every edge must be annotated with:

- its physical mask;
- the physical primitive that justifies its existence;
- the S0 incidence source/version.

---

## 4. Path Semantics

### 4.1 Physical Mask of a Path

For a path `P`, `M(P)` is the XOR (symmetric difference) of the physical masks of all traversed edges.

### 4.2 Syndrome of a Path

For sector check `c`, `syn_c = parity(M(P) ∩ Q(c))`.
A candidate is retained only if its recovered physical mask reproduces the target syndrome.

### 4.3 Graph Weight

The graph weight is the sum of edge weights. In this candidate graph all primitive edges have weight 1.

### 4.4 Physical Weight

The physical weight is `|M(P)|` (Hamming weight of the recovered physical mask).

**Critical rule:** Graph weight is not an admissible proxy for physical weight in the optimality decision.

---

## 5. Candidate Decoding Semantics

Given a sector-local defect syndrome `S_def`:

1. Pair defects with one another or terminate them at boundary nodes, using each defect exactly once.
2. For each pair/boundary connection, enumerate all shortest graph paths.
3. XOR all path physical masks.
4. Verify syndrome reproduction.
5. Minimize physical Hamming weight over valid recovered masks.

The search may deduplicate identical final physical masks, because identical masks are physically equivalent; this is not graph-cost pruning.

---

## 6. Explicit Hypotheses (H1–H4)

| ID | Hypothesis | Status after Level 4C |
|----|------------|-----------------------|
| H1 | Check–check edges are sufficient to represent all tested d=3 pair-type minima through concatenation. | **SUPPORTED FOR d=3 EXTENSIONAL TEST** |
| H2 | Check–boundary edges are sufficient to represent all tested d=3 singleton and multi-defect minima, including corner cases. | **SUPPORTED FOR d=3 EXTENSIONAL TEST** |
| H3 | The search procedure produces the oracle-optimal physical weight for every tested d=3 sector-local syndrome. | **PASS** |
| H4 | No generated syndrome-correct candidate has physical weight below the independent oracle minimum. | **PASS** |

These statuses are restricted to the Level 4C d=3 test domain. They are not general proofs for larger distance or for a future MWPM implementation.

---

## 7. Non-Claims

- Graph cost equals physical Hamming weight.
- Physical side membership alone uniquely determines decoding-boundary semantics.
- The construction is proven for `d>3`.
- A MWPM solver has been validated by this contract.
- The exact historical Level 4A-v4 / Level 4B-v2 scripts are present in the current repository tree.

---

## 8. Level 4C Acceptance Criteria

Level 4C is **passed for d=3 sector-local decoding** when:

1. Every one of the 64 Z-sector syndromes and every one of the 64 X-sector syndromes yields at least one valid recovered physical mask.
2. The minimum physical weight among generated valid masks equals the independent physical oracle minimum obtained by enumerating all `2^13 = 8192` physical masks separately for each sector.
3. Candidate recoveries retain primitive-to-qubit provenance internally.
4. The validation implementation does not import or rely on `decoder_lib_v2.py` and does not use graph cost for physical optimality pruning.

Failure of any case rejects the candidate graph contract for the tested domain.

### 8.1 Syndrome-domain accounting

- The physical oracle enumerates 8192 physical masks per CSS sector.
- Each d=3 sector has 6 independent checks and therefore 64 sector-local syndromes.
- Level 4C covers 128 syndrome cases total: 64 Z + 64 X.

---

## 9. Provenance and Artifacts

### Canonical source

- **S0 geometry:** `src/s0_geometry.py`, blob SHA `1e52217e7bbb56103977c68a7aaa8cbda92521af`.

### Historical physical-oracle evidence

- Level 4A-v4 and Level 4B-v2 were reported in the audit/conversation history and are relied upon as prior physical evidence.
- Their exact historical source files and stdout are **not currently present on the `main` tree**. This is a provenance gap, not silently repaired here.
- `tests/test_level4a_v3_boundary_termination.py` remains versioned historical evidence for the underlying singleton endpoint invariant.

### New versioned Level 4C evidence

- `tests/test_level4c_graph_contract_d3.py`
- `tests/_level4_common.py`
- `audit/artifacts/level4c_graph_contract_d3.stdout`
- `audit/artifacts/README.md`
- `audit/artifacts/SHA256SUMS.txt`

The Level 4C stdout is the reproducible, versioned record for the graph-contract PASS.

---

## 10. Relation to Production Code

This contract is a reference specification for validation. The production decoder (`src/decoder_lib_v2.py`) remains frozen and is not modified by the Level 4C work.

A future production transfer must be a separate reviewed change, with a new validation record showing that the transferred graph construction preserves the same physical semantics and provenance.

---

**Document version:** 1.2  
**Last updated:** 2026-09-07  
**Current status:** Level 4C PASS for d=3 sector-local syndrome spaces; production implementation remains frozen.
