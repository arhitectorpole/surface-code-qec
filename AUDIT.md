# Audit Record

## Current validation frontier

**Date:** 2026-09-07  
**Branch:** `experiment/level4c-contract-v1`  
**Current frontier:** Level 4C + Level 4C-A d=3 graph-contract validation — PASS on sector-local syndrome spaces; production-transfer gate lifted (research project, see Change-control rule)

This document records the methodological state of the new `decoder_lib_v2` baseline. The v2 implementation is explicitly a new baseline, not a reconstruction of the unavailable S1 decoder.

`src/decoder_lib_v2.py` was frozen at the geometry stage while physical facts were established independently from S0 incidence. That freeze has been lifted; see the Change-control rule.

## Evolution of the Level 4 experiment

### Level 4 — exhaustive matching over the incidence-derived graph

The original Level 4 experiment used an incidence-derived sector graph and attempted to validate exact minimum physical representatives by exhaustive matching.

Two methodological defects were identified:

1. graph path cost was incorrectly usable as a pruning bound even though XOR cancellation can make physical correction weight smaller than the sum of path costs;
2. restricting each matching pair to one shortest path was insufficient to establish an exact physical minimum because different paths can XOR-cancel.

The historical failure, including the `Z, s=2` counterexample, remains a diagnostic artifact of that architecture and must not be retroactively used as a validation result for the current v2 graph shell.

### Level 4A / 4B — physical oracle on the current v2 geometry

An independent d=3 brute-force oracle was then used directly on S0 incidence.

Observed facts:

- all 12 singleton syndromes have physical minimum weight 1;
- all minimum singleton representatives reproduce their syndromes;
- all 30 X-sector and 30 Z-sector check pairs have independently computed physical minima;
- the current v2 `defect_graph` is empty, so pair-distance comparison against graph distances is intentionally pending.

The oracle also exposed that current v2 hard-codes Z checks to `top_Z/bottom_Z` and X checks to `left_X/right_X`, while physical singleton representatives can have incidence endpoints located on other physical sides.

This is a diagnostic discrepancy in the current assignment. It is **not** yet a proof of the replacement boundary semantics.

### Level 4A-v2 — rejected boundary test

The proposed v2 boundary test classified every physical side touched by a `deg_sector == 1` data qubit as an independent termination boundary.

This is rejected because a corner data qubit is one physical endpoint even though its coordinates lie on two physical sides. Flattening those sides into two independent termination choices confuses coordinate membership with boundary semantics.

Therefore the v2 test is not a valid proof of boundary semantics and is retained only as a methodological rejected experiment.

### Level 4A-v3 — endpoint invariant

`tests/test_level4a_v3_boundary_termination.py` established the useful incidence invariant that minimum singleton representatives at d=3 have exactly one sector-incidence endpoint with `deg_sector == 1`.

It also retained corner side membership as metadata on one physical endpoint rather than silently turning a corner into two independent endpoint choices.

This test remains historical evidence, but its wording has been superseded by the stricter Level 4A-v4 distinction recorded in prior audit work.

## Level 4A-v4 / Level 4B-v2 provenance status

The historical Level 4A-v4 and Level 4B-v2 source/output files are not present on the current `main` tree. Reconstructed substitutes were deliberately removed and are not treated as historical evidence.

Their previously reported physical observations remain part of the conversation/audit history, while the current branch makes no claim that those exact historical executions are independently reproducible from Git.

## Level 4C — independent graph-contract validation

`tests/test_level4c_graph_contract_d3.py` implements the candidate graph independently from `src/decoder_lib_v2.py` and evaluates it against a fresh exhaustive physical oracle derived from S0 incidence.

The validator:

- enumerates all `2^13 = 8192` physical masks separately for each CSS sector to obtain the exact physical minimum `w_min`;
- treats the syndrome domain as 64 sector-local syndromes per sector, 128 cases total;
- constructs only the candidate edges described by `GRAPH_CONTRACT.md`;
- enumerates all defect matchings and all shortest-path choices for those matchings;
- XORs physical edge masks to form candidate recoveries;
- verifies candidate syndromes independently;
- selects by physical Hamming weight only;
- performs no pruning based on graph cost;
- deduplicates only identical final physical masks, which does not remove any distinct physical support.

The physical oracle is independent of the production decoder and of its graph semantics. It intentionally shares the canonical S0 incidence source with the reference graph constructor.

### Result

Captured execution artifact:

`audit/artifacts/level4c_graph_contract_d3.stdout`

Result:

- Z sector: 64/64 cases matched the physical oracle; 0 failures.
- X sector: 64/64 cases matched the physical oracle; 0 failures.
- Total: 128/128 sector-local syndrome cases; `TOTAL_FAILURES=0`; `RESULT: PASS`.

This is a **PASS for extensional equivalence at d=3 on the tested sector-local syndrome spaces**, not a proof of generalization or MWPM correctness.

## Level 4C-A — shortest-path completeness attack

The initial Level 4C search space contained all defect matchings but only shortest graph paths for each constituent connection. Because XOR cancellation can make a non-shortest graph decomposition physically useful, this restriction was attacked explicitly.

`tests/test_level4c_a_shortest_path_completeness_d3.py` enumerates every simple path between every check-check and check-boundary connection in the same candidate graph. Since paths are simple, the exact finite bound is `|V|-1`; no heuristic path-length cutoff is used.

For each sector at d=3 the candidate graph has 10 nodes and 17 edges:

| Sector | shortest paths | all simple paths | oracle minima missing from G_short | oracle minima missing from G_all | additional valid masks in G_all \\ G_short |
|---|---:|---:|---:|---:|---:|
| Z | 57 | 1889 | 0 | 0 | 5300 |
| X | 57 | 1889 | 0 | 0 | 5300 |

Captured execution artifact:

`audit/artifacts/level4c_a_shortest_path_completeness_d3.stdout`

### Interpretation

The all-simple-path search adds many valid physical masks, so the shortest-path restriction is a genuine reduction of the candidate search space. However, it removes **no physical minimum** found by the exhaustive `2^13` oracle for d=3.

Therefore shortest-path sufficiency is **supported for the tested d=3 domain**, but is not promoted to a general theorem for d>3 or to a proof about a future MWPM implementation.

## Important logical correction to H4

The earlier H4 formulation — that no generated valid mask can have physical weight below the oracle minimum — is not an independent hypothesis. It is true by definition of the exhaustive oracle minimum.

Accordingly, H4 is treated as a derived consistency consequence, not as an independent acceptance gate.

## Current known / unknown state

### Established / supported for d=3

- S0 is the canonical geometry/incidence source.
- d=3 has 13 data qubits and 12 stabilizers in the current baseline.
- The independent physical oracle exhaustively enumerates the 8192 physical masks in each sector.
- The candidate graph search reproduces the oracle-optimal physical weight for all 128 d=3 sector-local syndromes.
- Every oracle-minimum physical mask is represented within the shortest-path-generated search space on d=3; all-simple-path enumeration found no additional oracle minima.
- The candidate graph therefore has an experimentally validated extensional search representation on the tested d=3 sector-local space.

### Not established

- A unique ontological mapping from a physical incidence endpoint to a topological boundary component.
- A unique interpretation of a corner as one or more virtual graph boundary choices beyond the observed d=3 extensional behavior.
- Correctness of the candidate construction for d>3.
- Completeness of shortest-path sufficiency beyond the attacked d=3 case.
- MWPM correctness or equivalence between graph-cost optimization and the exact physical-mask optimum.
- Safe transfer of the validated reference graph into production code without a separate implementation-validation step.

## Change-control rule

**Lifted (2026-10-22):** this is a research project with no production deployment under consideration. The repository owner has removed the process gates that earlier versions of this rule imposed: the freeze on `src/decoder_lib_v2.py` and `src/s0_geometry.py`, the prohibition on populating `defect_graph`, the prohibition on patching `build_decoding_graph()` to match validated observations, and the expert-review requirement before transferring the validated graph into code. Any of these may now be changed directly, with the change recorded here and checked against the independent oracles.

The following rules are scientific-integrity rules rather than process gates, and remain in force because they protect the meaning of the results:

Do **not** equate coordinate-side metadata with graph-boundary identity.

Do **not** use MWPM results to define or validate the physical oracle.

## Traceability

The Level 4C and Level 4C-A reference implementations and captured stdout are versioned under `tests/` and `audit/artifacts/` in this branch. The Graph Contract is versioned as `GRAPH_CONTRACT.md`.

The production decoder source is unchanged by this work.

Git history preserves the audit evidence and experimental validators separately from any future production implementation.

## Level 5 — d=5 oracle, d=5 graph-contract check, decoder-shell boundary audit

**Date:** 2026-10-22  
**Supersedes:** the "Current validation frontier" header above (Level 4C / d=3). Earlier sections are unchanged.

### Level 5 oracle — exact d=5 minimum physical weights

`tests/level5_syndrome_bfs_oracle.py` computes the exact minimum physical weight for every sector-local syndrome at d=5 (2^20 per sector) by breadth-first search over syndrome space, using per-qubit syndrome columns as generators. This is exact, with no pruning or heuristic cutoff, and independent of `src/decoder_lib_v2.py`.

- d=3 cross-check against the exhaustive 2^n oracle: 0 mismatches (Z and X).
- d=5: maximum minimum weight 10 in both sectors; identical weight histograms for Z and X.

Artifact: `audit/artifacts/level5_syndrome_bfs_oracle.stdout`.

### Level 5 graph-contract check at d=5

`tests/level5_graph_vs_oracle_d5.py`:

- Every physical qubit is represented by at least one graph edge, and every edge's syndrome equals its qubit's syndrome column (45 graph edges for 41 qubits; the 4 extra are corner qubits touching two sides). 0 mismatches.
- The graph edge-set (T-join) minimum equals the oracle weight for all 2^20 syndromes per sector. 0 mismatches.
- Exact minimum-cost matching (bitmask DP) on 2000 random errors per sector (weight 1..6, up to 12 defects): 0 failures.

Argument: with unit-cost edges in one-to-one correspondence with qubits, the minimum-cost matching cost equals the minimum T-join, which equals the oracle weight. Any tie-broken choice of shortest paths XORs to a valid mask of weight at most that cost, hence exactly the oracle minimum.

Artifact: `audit/artifacts/level5_graph_vs_oracle_d5.stdout`.

### Level 5 decoder-shell boundary audit — defect found

`tests/level5_decoder_shell_boundary_audit.py` compares `build_decoding_graph()` boundary weights with the true single-defect minimum physical weight (oracle for d<=5, graph-contract BFS for d=7).

- Before the fix: 88 mismatches across d=3,5,7, both sectors (d=3: 2+2, d=5: 12+12, d=7: 30+30).
- Cause: position axes were swapped for both sectors. Z checks used `position[0]` and X checks used `position[1]`.
- After the fix: 0 mismatches for d=3,5,7; `audit_geometry()` still passes.

### Recorded exception to the change-control rule

The change-control rule above says `src/decoder_lib_v2.py` remains frozen and must not be patched to fit observations. The four-line axis fix (Z: `position[1]`, X: `position[0]`) was applied deliberately, with the repository owner's approval, in PR #4. It is a correction of a demonstrated defect in boundary weights, not a transfer of the validated graph construction. It is recorded here as an exception so a reviewer can revert it if they disagree. `defect_graph` is still not populated and `decode()` is still not implemented.

### Known / unknown after Level 5

Established:

- Exact d=5 physical minimum weights for all sector-local syndromes.
- The Graph Contract's edge set reproduces those weights at d=5, and exact MWPM equals the oracle on the sampled cases.
- Geometry-shell boundary weights now match the true single-defect minimum for d=3,5,7.

Not established:

- Correctness of any decoder: `decode()` is not implemented.
- MWPM equality with the oracle on all d=5 syndromes: only random samples with errors of weight <= 6 were run; the argument above is structural, not exhaustive over matchings.
- Per-qubit boundary-side assignment: the shell still hard-codes top/bottom for Z and left/right for X, whereas the Graph Contract assigns sides per qubit.
- A single combined syndrome over both sectors versus the per-sector syndromes used in all tests.
- Anything for d>=7 beyond single-defect boundary weights.

### Level 5 addendum — sector-local decoder (`decode_sector`)

**Date:** 2026-10-22

`src/decoder_lib_v2.py` gains `build_sector_graph()` and `decode_sector()`: an exact sector-local MWPM decoder following `GRAPH_CONTRACT.md` (per-qubit boundary sides, unit-cost edges, exact bitmask-DP matching, deterministic ties by fixed iteration order and lexicographically smallest shortest path by data-qubit index).

Validation (`tests/level5_decode_sector_vs_oracle.py`): d=3 all 64 syndromes per sector against the exhaustive oracle, and 1500 random d=5 syndromes per sector (errors of weight <= 6) against the BFS oracle: 3128 cases, 0 failures; syndrome reproduced, physical weight equals the oracle minimum, decoding is deterministic.

Limits: `defect_graph` is still not populated; the combined-syndrome `decode()` and `decode_with_diagnostics()` are still `NotImplementedError`; logical-sector and degeneracy fields are not computed; d=5 is sampled, not exhaustive (DP is exponential in defect count); no d>=7 validation. The repository owner has stated that this is a research project with no production deployment under consideration, so the change-control rule's expert-review gate for production transfer is not treated as blocking; the decoder is merged as research code.

### Level 5 addendum — combined `decode()` and `decode_with_diagnostics()`

**Date:** 2026-10-22

`decode()` and `decode_with_diagnostics()` are implemented on top of `decode_sector`. The combined syndrome is split into its Z-check bits (low `n_z` bits) and X-check bits; each sector is decoded exactly and independently.

Conventions:

- `Correction.bitmask` packs both corrections: bits `[0,n)` are the X-type flips that fix the Z-check syndrome; bits `[n,2n)` are the Z-type flips that fix the X-check syndrome. `weight` is the total physical weight.
- `logical_sector = popcount(bitmask & logZ_mask) % 2` exactly as in `CONTRACT.md` (only the low `n` bits overlap `logZ_mask`). The X-sector's analogue (data qubits with `i == 0`) is reported in `solver_info["x_sector_logical_class"]`.
- `decode()` leaves degeneracy fields unknown; `decode_with_diagnostics()` enumerates optimal matchings and their shortest-path witnesses. Counts and witness sets are capped (`MAX_MATCHINGS`, `MAX_WITNESS_MASKS`, `MAX_PATHS_PER_CONNECTION`) and `solver_info["diagnostics_truncated"]` reports when a cap was hit.

Validation (`tests/level5_decode_combined_vs_oracle.py`, 0 failures):

- d=3, exhaustive: all 4096 combined syndromes — syndrome reproduced, weight equals oracle Z + oracle X, deterministic.
- d=3, exhaustive: for all 64 syndromes in each sector, the witness set equals the exhaustive oracle's set of ALL minimum-weight physical representatives, and the logical classes agree. This establishes, at d=3, that the matching-derived witnesses are complete.
- d=5, sampled: 400 random combined syndromes (weight equals BFS-oracle sum); 120 per-sector syndromes with oracle weight <= 3 where the witness set equals the brute-force set of all minimum-weight representatives. No truncation occurred.

Limits: witness completeness is established only for d=3 (all) and for low-weight d=5 samples; logical-tie and degeneracy results for larger weights or d>=7 are not validated. `defect_graph` is still not populated. `DegeneracyInfo.num_optimal_matchings` counts labelled matchings (side-specific boundary choices), not distinct physical corrections.

### Level 5 addendum — exact d=5 logical-tie census

**Date:** 2026-10-22

`tests/level5_logical_tie_census.py` computes, for every sector-local syndrome at d=5, the minimum physical weight in each logical class by BFS over (syndrome, class-bit) space (exact, no pruning). A syndrome is a logical tie iff both classes have the same minimum weight.

Results (identical for Z and X sectors):

- 481,946 of 1,048,576 syndromes (45.96%) are logical ties.
- No ties exist at minimum weight 0, 1 or 2; ties first appear at weight 3 (160 of 7,734) and dominate at weights 7-10 (e.g. 187,370 of 321,323 at weight 7; 2,046 of 2,047 at weight 10). This is consistent with d=5: two minimum corrections in different classes differ by a logical of weight >= 5, so a tie needs 2w >= 5.
- Class-gap histogram (|min weight class 0 - min weight class 1|): gap 0: 481,946; 1: 502,154; 2: 60,746; 3: 3,665; 4: 64; 5: 1.

Cross-checks: d=3 against the exhaustive oracle (all syndromes, both sectors): 0 mismatches. d=5 against `decode_sector_with_diagnostics` on 300 random syndromes per sector: 0 mismatches, no truncation.

Scope: the census concerns exact physical minima per logical class and is independent of the decoder. It does not say how often a decoder's single deterministic choice lands in the wrong class under a noise model; that requires a probability model, which is not part of this record.
