# Contributing

1. Create a project-local virtual environment with Python 3.11–3.13.
2. Install `requirements-dev.txt`.
3. Run `pytest -q` before opening a pull request.
4. Keep evidence provenance intact and never add secrets or private uploads.

Small focused pull requests are preferred. New model providers must preserve the mock mode used by the offline test suite.
