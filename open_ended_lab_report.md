# Open Ended Lab: Deployment & Quality Gates Report

## 1. Reproducible Container Image
- **Dockerfile**: Used `python:3.11-slim` as the base image for a minimal footprint.
- **Layer Optimization**: dependencies (`requirements.txt`) are copied and installed first to utilize Docker's cache, speeding up subsequent builds.
- **Multi-stage Deployment**: The image is configured to run the FastAPI server by default, ensuring a consistent environment from dev to prod.

## 2. Secret-Free Image
- **Runtime Injection**: No API keys are baked into the image.
- **Environment Variables**: Use `${GEMINI_API_KEY}` in the `docker-compose.yaml` to inject secrets at runtime.
- **.dockerignore**: Excluded local `.env`, `.db`, and `venv` files to prevent leakage.

## 3. Multi-Service Orchestration
- **Docker Compose**: Orchestrates the Agent API service.
- **Persistence**: Volumes are defined for the FAISS index and SQLite checkpoint database, ensuring data survives container restarts.

## 4. Automated Quality Gates (CI/CD)
- **Headless Eval Script**: `run_eval.py` was made CI-ready with exit codes (0 for pass, 1 for fail).
- **GitHub Actions**: Configured `main.yml` to trigger the evaluation suite on every push.
- **Thresholds**: Versioned in `eval_threshold_config.json` to enforce strict quality standards (85%+ for Faithfulness and Relevancy).

## How to Run Demo
1. Build & Start: `docker-compose up --build`
2. Access API: `http://localhost:3000`
3. Running Evaluations: `python run_eval.py`
