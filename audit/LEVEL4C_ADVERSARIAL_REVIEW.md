# Level 4C Adversarial Review

## Scope

This review attacks the Level 4C PASS without modifying the frozen production decoder.

## Finding 1 — H4 in the original contract was tautological

A candidate physical mask cannot have weight below the exhaustive oracle minimum for the same syndrome by definition of that minimum. Therefore the former H4 was not an independent acceptance gate.

**Disposition:** H4 is not treated as an independent proof obligation. The meaningful Level 4C criterion is equality of the minimum generated valid physical weight with the independently enumerated oracle minimum.

## Finding 2 — Level 4C enumerated shortest paths, not all graph paths

The Level 4C reference implementation enumerates all defect matchings and all shortest paths for each constituent connection. This is a deliberate search restriction and must not be silently promoted to a theorem about all paths in the graph.

## Level 4C-A completeness attack

The Level 4C-A validator enumerates every simple path between every check-check and check-boundary connection in the same candidate graph. Since a simple path cannot visit a node twice, its length is exactly bounded by `|V|-1`; no heuristic depth cutoff is used.

For d=3, each sector candidate graph has 10 nodes and 17 edges.

| Sector | shortest paths | all simple paths | oracle minima missing from G_short | oracle minima missing from G_all | extra valid masks in G_all \ G_short |
|---|---:|---:|---:|---:|---:|
| Z | 57 | 1889 | 0 | 0 | 5300 |
| X | 57 | 1889 | 0 | 0 | 5300 |

## Interpretation

All-simple-path enumeration adds many valid physical masks, demonstrating that the shortest-path restriction is a real reduction of search space. However, for d=3 it does not remove any physical minimum found by the exhaustive `2^13` oracle.

Therefore:

- `G_short` is empirically sufficient to represent every d=3 oracle minimum tested;
- the shortest-path restriction is **supported for d=3**, not proven as a general theorem;
- the candidate graph remains unvalidated for `d>3`;
- this result does not validate MWPM, because a future MWPM solver optimizes graph cost rather than the post hoc physical-mask objective used by the reference search.

## Independence wording

The physical oracle is independent of the production decoder and of its graph semantics. It shares the canonical S0 incidence source with the reference graph constructor; this shared source is intentional and is not counted as semantic circularity.

## Production decision

**NO production transfer from this review alone.**

The 4C/4C-A results justify a reviewed experimental candidate graph for d=3. Any production transfer must separately preserve physical provenance and be followed by a new validation of the transferred implementation.

## Provenance note

The historical Level 4A-v4 and Level 4B-v2 source/output artifacts are not present on the current `main` tree and are not reconstructed here. The currently versioned Level 4C and Level 4C-A artifacts are independent experimental evidence.
