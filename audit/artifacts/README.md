# Level 4 Audit Artifacts

This directory contains versioned execution artifacts for the independent Level 4C graph-contract validation and the Level 4C-A shortest-path completeness attack.

## Reproduction

Run from the repository root:

```bash
python tests/test_level4c_graph_contract_d3.py
python tests/test_level4c_a_shortest_path_completeness_d3.py
```

Expected terminal summaries:

```text
LEVEL 4C GRAPH-CONTRACT VALIDATOR ... TOTAL_CASES=128 TOTAL_FAILURES=0 RESULT: PASS
LEVEL 4C-A: SHORTEST-PATH COMPLETENESS ATTACK ... RESULT: PASS
```

The Level 4C validator is intentionally independent of `src/decoder_lib_v2.py`. Its physical oracle enumerates all 8192 data-qubit masks separately for each CSS sector, while the syndrome domain is 64 sector-local syndromes per sector.

The Level 4C-A attack is also independent of `src/decoder_lib_v2.py`. It compares the shortest-path search space against an exhaustive simple-path search on the same candidate graph. Because paths are simple, the exact finite path-length bound is `|V|-1`; no heuristic cutoff is used.

Observed d=3 result:

```text
Z: shortest_paths=57, all_simple_paths=1889, oracle_minima_missing_from_G_short=0
X: shortest_paths=57, all_simple_paths=1889, oracle_minima_missing_from_G_short=0
Z: additional_valid_masks_in_G_all_not_G_short=5300
X: additional_valid_masks_in_G_all_not_G_short=5300
```

Thus all-simple-path enumeration adds valid physical masks but no oracle-minimum mask missing from the shortest-path-generated search space for d=3.

The historical Level 4A-v4 and Level 4B-v2 source/output files are not present on the current `main` tree. They are therefore not represented here by reconstructed substitutes.

The versioned 4C and 4C-A stdout files are the audit artifacts for these experimental results on this branch.
