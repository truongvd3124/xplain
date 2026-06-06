# XplainScreen — Explainable Automated Image Screening

Production-grade system for **screening image batches against user-defined
classes**, built on Zero-shot Concept Bottleneck Models (ZCBM) + CLIP. Every
ACCEPT/REJECT decision is explained at the visual-concept level.

```
describe class in plain text ──► LLM (Gemini) extracts visual concepts
        + reference images   ──► CLIP embeds both ──► calibrated profile
upload image batch ──► Celery worker scores each image ──► dashboard
                       ACCEPTED / REJECTED + "missing: floppy ears, …"
```

## Architecture

| Layer | Tech |
|---|---|
| API | FastAPI, layered (router → service → repository), DI via `Depends` |
| ML | PyTorch + OpenAI CLIP ViT-B/32 (GPU), Gemini for concept extraction |
| DB | PostgreSQL 16 + pgvector (embeddings stored as `vector(512)`) |
| Queue | Celery + Redis (broker db1, results db2, cache db0) |
| Frontend | React 19 + TypeScript + Vite + Tailwind v4 + TanStack Query + Recharts |

### Scoring (ported from the validated xplaincv-mvp prototype)

- Concept presence: `P = sigmoid(logit_scale · (sim(image, concept) − sim(image, "a photo")))`
- `concept_score` = importance-weighted mean of presence probabilities
- `prototype_score` = cosine to the mean reference embedding, mapped through a
  window `[proto_lo, proto_hi]` calibrated **leave-one-out** (needs ≥3 refs)
- `final = 0.5·concept_score + 0.5·prototype_score` (concept-only without refs)
- **ACCEPTED** iff `final ≥ profile.threshold_score` **and** ≥60% of concepts present
- Reject reason = lowest-probability missing concepts

## Local development

Prereqs: Docker (postgres+redis only), the shared GPU venv at
`/home/ubuntu/zcbm/venv` (torch + openai-clip), Node 20.

```bash
# one-time
python -m venv --system-site-packages .venv
echo "/home/ubuntu/zcbm/venv/lib/python3.12/site-packages" \
  > .venv/lib/python3.12/site-packages/_zcbm_shared.pth
.venv/bin/pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # add GEMINI_API_KEY
(cd frontend && npm install)

# every time
./run.sh          # infra + migrations + API:8000 + worker + UI:5173
```

Or by hand:

```bash
sudo docker compose up -d                       # postgres + redis
(cd backend && ../.venv/bin/alembic upgrade head)
backend/run_api.sh                              # FastAPI :8000
backend/run_worker.sh                           # Celery (solo pool — see below)
(cd frontend && npm run dev)                    # Vite :5173 (proxies /api)
```

> **⚠ CUDA + Celery:** the worker MUST run with `--pool=solo` (or `threads`).
> The default prefork pool forks after CUDA init and crashes. CLIP is loaded
> in the `worker_process_init` signal, never at import time.

## API

```
POST   /api/profiles/extract-concepts        text -> concepts (Gemini, sync)
POST   /api/profiles                         create profile + concepts
POST   /api/profiles/{id}/reference-images   multipart upload, embedded on arrival
POST   /api/profiles/{id}/build              embed concepts + calibrate threshold
GET    /api/profiles[/{id}] · DELETE /api/profiles/{id}
POST   /api/batches                          multipart files + profile_id -> 202 {batch_id}
GET    /api/batches · /api/batches/{id}?page=   status + paginated results
GET    /api/results/{id}                     full per-concept explanation
GET    /api/health
```

## Project layout

```
backend/app/
  config.py          settings (.env)
  db/                SQLAlchemy models + session (5 tables, pgvector)
  repositories/      data access (profiles, batches, results)
  services/          clip_engine, scoring (pure math), llm/ (provider iface),
                     concept/profile/batch/screening services
  routers/           thin HTTP layer
  tasks/             celery_app + screen_batch task
  storage/local.py   image storage (swap for S3 in prod)
frontend/src/
  api/ hooks/        typed client + TanStack Query (1.5s polling while processing)
  pages/             ProfileBuilder (3-step wizard), Dashboard, BatchDetail,
                     Explainability (concept bar chart vs threshold)
```

## Deployment notes (AWS)

- `backend/Dockerfile.api` and `backend/Dockerfile.worker` are provided for
  ECS/EC2. They install CPU torch by default; use an `nvidia/cuda` base + the
  cu124 wheel index for GPU workers. **Do not build them on the dev box** (disk).
- Point `DATABASE_URL` at RDS Postgres (with the `vector` extension) and
  `REDIS_URL`/`CELERY_*` at ElastiCache.
- Replace `app/storage/local.py` with an S3 implementation and serve images
  from CloudFront; the rest of the code only touches `save_*`/`open_rgb`.

## Operational notes

- Batch progress is flushed every `BATCH_CHUNK_PROGRESS` (5) images; the
  dashboard polls and shows a live progress bar.
- A corrupt image inside a batch is recorded as REJECTED with
  `processing error: …` — it never fails the batch.
- `screen_batch` is idempotent (deletes partial results on retry) and uses
  `task_acks_late` so a killed worker re-delivers the job.
- Profiles need **≥3 reference images** for leave-one-out calibration —
  that is what separates visually similar classes (cat vs dog).
