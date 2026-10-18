# Evaluation plan

The synthetic `examples/demo_bundle/` is a small golden corpus for the judge demo. Evaluate:

1. **Ingestion coverage:** all four demo modalities produce records with source provenance.
2. **Retrieval recall:** the North row and report paragraph are returned for the cross-modal question.
3. **Grounding:** each final citation points to an existing evidence ID.
4. **Selective routing:** text-only questions do not request table or visual modes; chart-comparison questions do.
5. **Reliability:** empty bundles produce an explicit no-evidence status.
6. **Conflict behavior:** different numeric claims lower confidence and surface a warning.

Run `pytest -q` and then `python scripts/run_demo.py`. Model-backed evaluation can be added later through a provider adapter without changing the evidence schema.
