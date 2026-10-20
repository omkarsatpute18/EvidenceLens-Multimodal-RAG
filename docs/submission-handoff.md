# EvidenceLens submission handoff

## Available now

- **Source repository:** <https://github.com/omkarsatpute18/EvidenceLens-Multimodal-RAG>
- **Live demo:** <https://evidence-lens-multimodal-rag-drab.vercel.app/>
- **Health check:** <https://evidence-lens-multimodal-rag-drab.vercel.app/health>
- **Demo bundle:** `examples/demo_bundle/`
- **Demo script:** `docs/demo-script.md`
- **Video recording guide:** `docs/video-production.md`

## Final assets still needed

### Screenshots

Capture these from the live demo:

1. Initial upload interface.
2. Processed evidence bundle with file and modality badges.
3. Successful answer with confidence, workflow trace, citations, retrieval trace, and evidence previews.

Recommended location:

```text
docs/screenshots/
```

### Video

Record a 2–3 minute MP4 using `docs/demo-script.md`. The repository intentionally does not contain a fake placeholder video or an invented URL. Add the real hosted video URL to the hackathon submission form after upload.

## Important disclosure

The live deployment uses mock mode by default and stores evidence in memory. It is suitable for a public demonstration, not sensitive or durable multi-user data. The OpenAI-compatible provider adapter can be configured through Vercel environment variables without committing secrets.
