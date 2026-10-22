# Graph Contract

## 0. Status and Scope

- **Status:** *Experimental specification* — validated extensionally for the tested d=3 sector-local spaces by Level 4C and attacked for shortest-path completeness by Level 4C-A; not promoted to production.
- **Revision:** v1.3. Corrects the former tautological H4 formulation, records the 4C-A completeness attack, and makes the oracle-independence wording explicit.
- **Scope:** d=3 unrotated planar surface code, CSS stabilizer formalism.
- **Production relation:** This document defines a candidate reference graph. It does not modify `src/decoder_lib_v2.py` or `src/s0_geometry.py`.
- **Epistemic rule:** Physical facts, graph hypotheses, and validation results are kept distinct.

---

## 1. Definitions

### 1.1 Data Qubits

For d=3, the canonical S0 geometry contains 13 data qubits with coordinates on the `{0,2,4}` lattice.

### 1.2 Check Nodes

There are 6 Z checks and 6 X checks. Graph checks are indexed locally as `c_0 ... c_5` within each sector.

### 1.3 Sector Incidence

For a sector `S`, `Q_S(c)` is the set of data qubits incident on check `c`.

```text
deg_S(q) = |{ c in S : q in Q_S(c) }|
```

### 1.4 Boundary Nodes

The candidate graph contains four abstract boundary nodes:

- `B_T` — top
- `B_B` — bottom
- `B_L` — left
- `B_R` — right

They are graph objects, not physical qubits. No separate corner nodes are used.

---

## 2. Prior Physical Evidence

### 2.1 Singleton Endpoint Evidence

Prior Level 4A evidence established for d=3 that minimum singleton representatives are single-qubit physical errors with an incidence endpoint satisfying `deg_S(q) == 1`. A corner remains one physical endpoint even when its coordinate touches two geometric sides.

The original Level 4A-v4 source/output are not present on the current `main` tree. They are therefore treated as prior conversation/audit evidence rather than as a currently reproducible Git artifact.

### 2.2 Shared-Qubit Pair Evidence

Prior Level 4B evidence established for d=3 that weight-1 pair representatives coincide with a shared qubit in `Q(c_i) ∩ Q(c_j)`.

The original Level 4B-v2 source/output are not present on the current `main` tree. Reconstructed substitutes are not treated as historical evidence.

---

## 3. Candidate Graph Construction

### 3.1 Check–Check Edges

For each same-sector pair `(c_i,c_j)`, if `Q(c_i) ∩ Q(c_j) = {q}`, add an undirected edge:

```text
(c_i, c_j), graph_weight=1, physical_mask={q}
```

with provenance identifying the shared physical qubit `q`.

No other direct check–check edges are added by this candidate construction.

### 3.2 Check–Boundary Edges

For each check `c` and each `q in Q(c)` with `deg_S(q) == 1`, inspect the coordinate sides of `q`.

For every touched side `b`, add:

```text
(c, B_b), graph_weight=1, physical_mask={q}
```

with provenance identifying `c`, `q`, and `b`.

A corner can therefore produce two graph boundary edges carrying the same physical mask. This is an extensional graph construction hypothesis, not a claim that a corner is ontologically two independent physical terminations.

### 3.3 Provenance

Every graph edge used by the reference validator must retain enough information to reconstruct its physical mask and its originating S0 incidence primitive.

---

## 4. Path and Recovery Semantics

### 4.1 Physical Mask

For a graph path `P`, the recovered physical mask `M(P)` is the XOR of all edge physical masks traversed by the path.

### 4.2 Syndrome

For each sector check `c`:

```text
syn_c(M) = parity(M intersect Q(c))
```

A recovered candidate is valid only when its physical mask reproduces the target sector syndrome.

### 4.3 Graph Weight

All primitive edges in the candidate d=3 graph have graph weight 1.

### 4.4 Physical Weight

The physical objective is the Hamming weight `|M|` of the recovered physical mask.

**Critical rule:** graph weight is not an admissible proxy for physical weight and is never used as an optimality proof or pruning bound in the reference validation.

### 4.5 Candidate Search

For a sector-local defect syndrome:

1. Pair defects with one another or terminate them at boundary nodes, using every defect exactly once.
2. For each connection, enumerate the permitted constituent graph paths.
3. XOR constituent physical masks.
4. Verify the syndrome.
5. Minimize physical Hamming weight over valid masks.

Level 4C uses all shortest constituent paths. Level 4C-A additionally compares this space against all simple constituent paths in the same candidate graph.

---

## 5. Explicit Hypotheses

| ID | Hypothesis | Current status |
|---|---|---|
| H1 | Candidate check–check edges are sufficient to represent all d=3 physical minima through concatenation. | **SUPPORTED FOR TESTED d=3 DOMAIN** |
| H2 | Candidate check–boundary edges, including corner duplication, are sufficient to represent all d=3 physical minima. | **SUPPORTED FOR TESTED d=3 DOMAIN** |
| H3 | Exhaustive matching plus all shortest constituent paths reproduces the exact physical minimum for every d=3 sector-local syndrome. | **PASS** |
| H4 | Restricting each constituent connection to shortest graph paths loses no d=3 oracle-minimum physical mask. | **PASS / 4C-A** |

These statuses are empirical statements about the tested d=3 reference construction. They are not general theorems for larger distance.

**Note on the former H4:** The earlier statement “no generated candidate can be lighter than the oracle minimum” was tautological because `w_min` is defined by exhaustive physical minimization. It is therefore not treated as an independent hypothesis or acceptance gate.

---

## 6. Level 4C Acceptance

The Level 4C acceptance test covers all sector-local syndromes:

- 64 Z-sector syndromes;
- 64 X-sector syndromes;
- 128 cases total.

The physical oracle independently enumerates all `2^13 = 8192` physical masks per sector and returns the exact `w_min` for each syndrome.

The Level 4C graph search passes when every tested syndrome has at least one syndrome-correct generated mask and the minimum physical weight among generated valid masks equals the oracle minimum.

The oracle is independent of the production decoder and of its graph semantics. It intentionally shares the canonical S0 incidence source with the reference graph constructor.

### Level 4C result

The versioned execution artifact reports:

```text
Z: 64/64, failures=0
X: 64/64, failures=0
TOTAL_CASES=128
TOTAL_FAILURES=0
RESULT: PASS
```

This establishes **extensional equivalence for the tested d=3 sector-local syndrome spaces under the shortest-path search semantics**.

It does not establish d>3 correctness, production-transfer correctness, or MWPM correctness.

---

## 7. Level 4C-A Shortest-Path Completeness Attack

The shortest-path restriction is attacked by exhaustive enumeration of **all simple paths** between every check-check and check-boundary connection in the same candidate graph.

Because a simple path cannot repeat a node, the maximum simple-path length is exactly `|V|-1`; no heuristic path-length cutoff is used.

For d=3, each sector candidate graph has 10 nodes and 17 edges.

| Sector | shortest constituent paths | all simple constituent paths | oracle minima missing from G_short | oracle minima missing from G_all | additional valid masks in G_all \\ G_short |
|---|---:|---:|---:|---:|---:|
| Z | 57 | 1889 | 0 | 0 | 5300 |
| X | 57 | 1889 | 0 | 0 | 5300 |

The attack finds **no oracle-minimum mask outside the shortest-path-generated search space** for d=3.

At the same time, all-simple-path enumeration adds many other syndrome-correct physical masks. Thus the shortest-path restriction is a genuine reduction of the search space, not a vacuous reformulation.

**Disposition:** H4 is supported for d=3 only.

---

## 8. Non-Claims

- Graph cost equals physical Hamming weight.
- Physical side membership uniquely determines the decoding boundary ontology.
- Corner duplication in the candidate graph is the unique physical interpretation of a corner.
- The candidate graph is proven for `d > 3`.
- Shortest-path sufficiency is a theorem for arbitrary graph sizes or code distances.
- A MWPM implementation is validated by these experiments.
- The historical Level 4A-v4 / Level 4B-v2 source and stdout are currently present in Git.

---

## 9. Provenance and Artifacts

### Canonical geometry

- `src/s0_geometry.py`
- blob SHA: `1e52217e7bbb56103977c68a7aaa8cbda92521af`

### Historical physical evidence

Level 4A-v4 and Level 4B-v2 are relied upon as prior audit/conversation evidence. Their exact historical source/output are not currently present on `main`; reconstructed replacements are intentionally excluded from the historical evidence chain.

### Versioned experimental evidence

- `tests/test_level4c_graph_contract_d3.py`
- `tests/test_level4c_a_shortest_path_completeness_d3.py`
- `tests/_level4_common.py`
- `audit/artifacts/level4c_graph_contract_d3.stdout`
- `audit/artifacts/level4c_a_shortest_path_completeness_d3.stdout`
- `audit/artifacts/README.md`
- `audit/LEVEL4C_ADVERSARIAL_REVIEW.md`

---

## 10. Relation to Production

`src/decoder_lib_v2.py` and `src/s0_geometry.py` remain frozen on this experimental branch.

A future production transfer must be a separate reviewed change, followed by validation of the transferred implementation against the same independent physical oracle and provenance requirements.

---

**Document version:** 1.3  
**Last updated:** 2026-09-07  
**Current status:** Level 4C PASS + Level 4C-A PASS for d=3 sector-local spaces; production remains frozen.
