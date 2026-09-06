# Level 4 Audit Artifacts

This directory contains the versioned execution artifact for the independent Level 4C graph-contract validation.

## Reproduction

Run from the repository root:

```bash
python tests/test_level4c_graph_contract_d3.py
```

Expected terminal summary:

```text
LEVEL 4C GRAPH-CONTRACT VALIDATOR ... TOTAL_CASES=128 TOTAL_FAILURES=0 RESULT: PASS
```

The Level 4C validator is intentionally independent of `src/decoder_lib_v2.py`. Its physical oracle enumerates all 8192 data-qubit masks separately for each CSS sector, while the syndrome domain is 64 sector-local syndromes per sector.

The historical Level 4A-v4 and Level 4B-v2 source/output files are not present on the current `main` tree. They are therefore not represented here by reconstructed substitutes.

The versioned 4C stdout is the audit artifact for the graph-contract PASS on this branch.
