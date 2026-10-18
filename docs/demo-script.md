# Two-minute demo script

**0:00–0:20 — Problem.** Ordinary RAG often sees paragraphs but loses spreadsheet rows, chart context, and visual uncertainty.

**0:20–0:40 — Solution.** Introduce EvidenceLens: a multimodal evidence index with citations, selective agents, a contradiction check, and a verification step.

**0:40–1:00 — Architecture.** Show the upload flow, specialized parsers, orchestrator, hybrid index, synthesis, consistency check, and critic. Emphasize that the UI exposes only safe workflow events, not hidden chain-of-thought.

**1:00–2:00 — Live demo.** Open `/`, upload the files from `examples/demo_bundle/`, and ask: “Which region had the largest decline, what evidence supports this conclusion, and are there inconsistencies between the chart, table, and report?” Show the answer, confidence, citations, table row, chart evidence, and warning when visual evidence is uncertain. Ask “What information is missing?” to demonstrate the no-overclaim limitation.

**2:00–2:20 — Innovation and OmniRush.** Highlight selective orchestration, provenance-preserving normalization, cross-modal contradiction warnings, deterministic tests, and reproducible Docker packaging. State that OmniRush.ai was the sole generative AI development agent.
