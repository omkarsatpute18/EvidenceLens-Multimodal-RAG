# Vercel deployment guide

EvidenceLens is a FastAPI application and is configured for Vercel's Python runtime. Vercel loads the ASGI app from `app.main:app` using the `[tool.vercel]` entrypoint in `pyproject.toml` and the `app/main.py` function configuration in `vercel.json`.

## Prerequisites

- A GitHub repository containing the committed EvidenceLens source.
- A Vercel account connected to that GitHub account.
- No API key is required for the default mock-mode deployment.

## Dashboard deployment

1. Open <https://vercel.com/new>.
2. Import `omkarsatpute18/EvidenceLens-Multimodal-RAG` after the repository has been pushed.
3. Keep the detected Python configuration and the repository root as the project root.
4. Deploy once with the safe defaults.
5. In **Project Settings → Environment Variables**, set:

   ```text
   MODEL_PROVIDER=mock
   MOCK_MODE=true
   OCR_ENABLED=false
   MAX_UPLOAD_MB=4
   TOP_K=8
   ```

6. Redeploy after saving environment variables.
7. Open the generated deployment URL and verify `/health`.

Expected health response includes:

```json
{
  "status": "ok",
  "version": "0.3.0",
  "mock_mode": true
}
```

## Optional provider-backed analysis

Add these environment variables in Vercel's dashboard only:

```text
MODEL_PROVIDER=openai_compatible
MODEL_NAME=your-model-name
MODEL_BASE_URL=https://your-provider.example/v1
MODEL_API_KEY=your-secret
MOCK_MODE=false
OCR_ENABLED=false
MAX_UPLOAD_MB=4
```

Do not place `MODEL_API_KEY` in GitHub, `vercel.json`, or `.env.example`.

## CLI deployment

Vercel's current CLI can deploy the connected repository. After installing and authenticating the CLI locally, run from the repository root:

```bash
vercel login
vercel link
vercel deploy
vercel deploy --prod
```

The dashboard method is preferred for this project because it keeps environment secrets out of shell history and makes the deployment URL easy to verify.

## Vercel limitations for this MVP

- Vercel runs the FastAPI app as a serverless function rather than a continuously running process.
- Evidence is stored in process memory and may disappear when the function is recycled.
- The demo should use a small bundle and `MAX_UPLOAD_MB=4`.
- Tesseract is not installed by Vercel; leave `OCR_ENABLED=false` there.
- Add authentication, durable storage, per-user isolation, malware scanning, and rate limiting before using sensitive evidence.
- A successful deployment URL must be verified manually; this repository does not claim one yet.
