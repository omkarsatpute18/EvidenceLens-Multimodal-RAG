# Submission checklist

This checklist separates work completed locally from actions that require external accounts or a Docker-enabled machine.

## Completed locally

- [x] Multimodal MVP with citations and provenance
- [x] Optional OpenAI-compatible visual analyzer with deterministic fallback
- [x] Deterministic hybrid retrieval and contextual contradiction checks
- [x] Optional Tesseract OCR path with bounded timeout
- [x] Offline test suite (`pytest -q`)
- [x] Synthetic public-safe demo bundle
- [x] README, architecture, evaluation, and demo script
- [x] `.env.example`, pinned requirements, Dockerfile, and Compose file
- [x] Platform `PORT` support and Render deployment blueprint
- [x] Vercel FastAPI entrypoint, function config, and deployment guide
- [x] Local health endpoint and browser UI
- [x] Demo script and recording guide

## Still requires manual execution

- [ ] Install Docker and run `docker compose up --build`
- [ ] Configure a provider key if demonstrating model-backed visual analysis
- [ ] Capture screenshots from the browser UI
- [ ] Record the 2–3 minute demo described in `docs/demo-script.md`
- [ ] Create a public GitHub repository and push only after authorization
- [ ] Deploy to Vercel or another hosting provider and verify `/health`
- [ ] Add the final repository, deployment, and video links to the submission form

Do not claim a live deployment or provider-backed analysis unless it has been run and verified with the relevant credentials.
