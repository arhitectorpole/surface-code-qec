# Level 4 Audit Artifacts

These files are versioned execution artifacts for the d=3 physical catalogues and the independent Level 4C graph-contract validator.

## Reproduction

Run from the repository root:

```bash
python tests/test_level4a_v4_endpoint_catalogue.py
python tests/test_level4b_v2_pair_catalogue.py
python tests/test_level4c_graph_contract_d3.py
```

Expected terminal summaries:

```text
LEVEL 4A-v4 ENDPOINT CATALOGUE ... RESULT: PASS
LEVEL 4B-v2 PAIR CATALOGUE ... RESULT: PASS
LEVEL 4C GRAPH-CONTRACT VALIDATOR ... TOTAL_CASES=128 TOTAL_FAILURES=0 RESULT: PASS
```

The Level 4C validator is intentionally independent of `src/decoder_lib_v2.py`. Its physical oracle enumerates all 8192 data-qubit masks separately for each CSS sector, while the syndrome domain is 64 sector-local syndromes per sector.

`SHA256SUMS.txt` records SHA-256 digests of the contract, test sources, and captured stdout artifacts as committed here.
