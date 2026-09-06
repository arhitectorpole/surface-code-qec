# Graph Contract

## 0. Status and Scope

- **Status:** *Experimental specification* – not yet validated.
- **Revision note:** v1.1 clarifies the syndrome-domain accounting and tightens the d=3 pair-intersection statement. The candidate graph semantics are otherwise unchanged.
- **Scope:** d=3 surface code (planar, unrotated), CSS stabilizer formalism.
- **Relation to production:** This document defines a candidate graph construction to be tested independently by Level 4C. **It does not modify** `src/decoder_lib_v2.py` or `src/s0_geometry.py`. Production code remains frozen until validation passes.
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

### 2.1 Singleton Endpoint Invariant (Level 4A-v4)

For every single-check syndrome `{c}` (12 checks total):

- The independent physical oracle gives `w_min({c}) = 1` (a single-qubit error).
- Every minimal representative has exactly one data qubit `q` that satisfies:
  - `q ∈ Q(c)`
  - `deg_S(q) = 1` (endpoint)
- If `q` lies at a corner, it touches two physical sides, but it remains **one physical endpoint**, not two independent termination points.

*Status:* **PROVEN** for d=3 (see audit artifacts `test_level4a_v4_endpoint_catalogue.py` and its output).

### 2.2 Shared-Qubit Pair Primitive (Level 4B-v2)

For every pair of checks `(c_i, c_j)` within the same sector:

- The physical oracle gives `w_min({c_i, c_j})` exactly.
- If `Q(c_i) ∩ Q(c_j) = {q}` (single shared data qubit) then `w_min = 1` and the minimal representative is the single-qubit error on `q`.
- If the intersection is empty, no single-qubit error can flip exactly both checks, so `w_min ≥ 2`. Within the d=3 S0 geometry used here, same-sector intersections are at most singleton; no multi-qubit intersection case is part of this validated catalogue.

*Status:* **PROVEN** for d=3 (see audit artifacts `test_level4b_v2_pair_catalogue.py` and its output).

---

## 3. Candidate Graph Construction

This section defines a **candidate** graph `G_S = (V, E)` for each sector `S ∈ {Z, X}`.
It is a **hypothesis** to be tested by Level 4C.

### 3.1 Check–Check Edges

For every pair of check nodes `(c_i, c_j)` in the same sector:

- If `Q(c_i) ∩ Q(c_j) = {q}` (single shared qubit), then add an undirected edge `e = (c_i, c_j)` with:
  - **weight** = 1 (graph cost)
  - **physical mask** = `{q}`
  - **provenance** = the shared qubit `q`

No other check–check edges are added.

*Remark:* This construction is motivated by the proven weight-1 pair primitive. Whether this edge set is sufficient to reproduce all physical minima for larger syndromes is **UNPROVEN**.

### 3.2 Check–Boundary Edges

For each check node `c` and each data qubit `q ∈ Q(c)`:

- **If** `deg_S(q) == 1` (i.e., `q` is an incidence endpoint for `c`), determine the physical sides of `q` from its coordinates:
  - `x == 0` → side `L`
  - `x == 2d-2` → side `R`
  - `y == 0` → side `T`
  - `y == 2d-2` → side `B`
- For **each** side `b` that `q` belongs to, add an undirected edge `e = (c, B_b)` with:
  - **weight** = 1
  - **physical mask** = `{q}`
  - **provenance** = endpoint qubit `q` and side `b`

Thus, a corner qubit (belonging to two sides) generates **two edges** to the corresponding boundary nodes, both with the same physical mask `{q}`.

*Rationale:* This allows the graph to represent paths ending at either side that are physically equivalent. Whether this semantic is correct and does not introduce false solutions is **UNPROVEN**.

### 3.3 Edge Provenance

Every edge must be annotated with:

- Its physical mask (list of data qubits)
- The physical primitive that justifies its existence (e.g., shared qubit or singleton endpoint)
- The source file/version of S0 that defines the incidence.

This provenance is essential for reconstructing physical corrections from graph paths.

---

## 4. Path Semantics

### 4.1 Physical Mask of a Path

Given a path `P = (v0, v1, ..., vk)` in `G_S`, the physical mask `M(P)` is the XOR (symmetric difference) of the physical masks of all edges traversed.

### 4.2 Syndrome of a Path

The syndrome `syn(M(P))` is computed by applying each check `c` in the sector to the mask:
`syn_c = parity( M(P) ∩ Q(c) )`.
A path is **syndrome-correct** if `syn(M(P))` equals the set of defect check nodes that the path is supposed to connect (or terminate).

### 4.3 Graph Weight

The graph weight of a path is the sum of edge weights (currently all 1, so equal to number of edges).

### 4.4 Physical Weight

The physical weight of a path is `|M(P)|` (Hamming weight of the mask).

**Critical rule:** Graph weight is **not** used as a proxy for physical weight when determining optimal physical correction. The physical weight is computed independently from the mask.

---

## 5. Candidate Decoding Semantics

Given a syndrome `S_def` (a set of check nodes in one sector that have flipped), the decoding procedure is defined as follows:

1. **Match defects** – pair up check nodes in `S_def` into pairs, and possibly pair some defects to boundary nodes, such that every defect is used exactly once.
2. **For each matching**:
   - For each pair `(c_i, c_j)`, take a shortest path between them in `G_S`.
   - For each boundary-terminated defect `c`, take a shortest path from `c` to one of the boundary nodes.
3. **Combine** all paths from a matching by XORing their physical masks to obtain a candidate correction mask `M_candidate`.
4. Verify that `syn(M_candidate) == S_def`. If not, discard.
5. Compute physical weight `|M_candidate|`.
6. Among all valid matchings and path choices, select the mask with minimal physical weight.

*Remark:* This selection is based on physical Hamming weight, not graph cost. The graph is merely a tool to generate candidate masks; it does not define the optimality criterion.

---

## 6. Explicit Hypotheses (H1–H4)

The following statements are **hypotheses** that Level 4C will test:

| ID | Hypothesis | Status |
|----|------------|--------|
| H1 | The check–check edges as defined in §3.1 are sufficient to represent all pair-type physical primitives (including those with `w_min ≥ 2`) via concatenation of edges. | **UNPROVEN** |
| H2 | The check–boundary edges as defined in §3.2 correctly represent all singleton endpoint terminations, including corners with two edges, such that every singleton syndrome has at least one minimal physical correction represented. | **UNPROVEN** |
| H3 | For every sector-local syndrome, the above decoding procedure yields at least one candidate mask whose physical weight equals `w_min(S_def)` as given by the independent oracle. | **UNPROVEN** |
| H4 | The graph construction does **not** introduce any candidate mask that reproduces the correct syndrome but has a lower physical weight than the true minimum. | **UNPROVEN** |

---

## 7. Non-Claims

The following statements are **explicitly not claimed** by this contract:

- **Graph cost equals physical Hamming weight** – they are separate quantities; graph weight is not used in the optimality criterion.
- **Boundary side membership alone proves graph boundary semantics** – a physical qubit touching a side does not automatically guarantee that the corresponding boundary node edge is semantically valid; it is a candidate construction.
- **The construction is optimal for d>3** – this contract is only for d=3; generalisation requires further validation.
- **This contract implements a MWPM decoder** – it defines a search procedure; MWPM is a separate optimisation layer that will be added later only after Level 4C passes.

---

## 8. Level 4C Acceptance Criteria

Level 4C validation will be considered **passed** if:

1. For **every sector-local syndrome** `S_def` (including the empty syndrome) in each d=3 CSS sector, i.e. all `2^6 = 64` syndromes for Z and all `2^6 = 64` syndromes for X, the candidate decoding procedure (§5) produces at least one valid physical mask whose syndrome exactly equals `S_def`.
2. The minimal physical weight found by the procedure equals `w_min(S_def)` as computed by the independent exhaustive physical oracle, which enumerates all `2^13 = 8192` data-qubit masks separately for each CSS sector.
3. All generated masks have a clear provenance trace to S0 incidence and the edge primitives defined in §3.
4. The validation script (`test_level4c_graph_contract_d3.py`) is self-contained, does **not** import or rely on `decoder_lib_v2.py`, and its outputs are reproducible and versioned.

If any syndrome fails (i.e., the procedure yields no valid mask or a mask with incorrect minimal weight), the contract is considered **rejected**, and the counterexample must be documented as new physical evidence to refine the hypotheses.

### 8.1 Syndrome-domain accounting

- The exhaustive physical oracle enumerates `2^13 = 8192` physical masks per CSS sector.
- For d=3, each sector has rank 6 and therefore exactly 64 sector-local syndromes.
- Level 4C therefore tests 128 syndrome cases total: 64 in Z and 64 in X. It does **not** treat `8192` as the number of distinct syndromes.

---

## 9. Provenance and Artifacts

This contract is based on:

- **S0 geometry:** `src/s0_geometry.py` (blob SHA `1e52217e7bbb56103977c68a7aaa8cbda92521af`).
- **Singleton endpoint catalogue:** `tests/test_level4a_v4_endpoint_catalogue.py` and its captured stdout.
- **Pair catalogue:** `tests/test_level4b_v2_pair_catalogue.py` and its captured stdout.
- **Level 4C validator:** `tests/test_level4c_graph_contract_d3.py` (reference implementation of §3–§5, independent of `decoder_lib_v2.py`).

The execution logs of these catalogues must be stored in `audit/artifacts/` to provide a verifiable chain of evidence.
All claims of PROVEN facts (§2) refer to those versioned artifacts.

---

## 10. Relation to Production Code

This contract is a **specification for a reference implementation** that will be used solely for validation. The production decoder (`src/decoder_lib_v2.py`) remains frozen and will be updated **only after** Level 4C passes. At that point, the validated graph construction will replace the current `build_decoding_graph()` implementation, and MWPM will be integrated as a thin wrapper on top of the validated graph.

---

**Document version:** 1.1  
**Last updated:** 2026-09-07  
**Next step:** Preserve the 4A/4B artifacts and run `tests/test_level4c_graph_contract_d3.py` reproducibly.
