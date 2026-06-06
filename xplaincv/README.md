# XplainCV — Explainable Image Classification Platform

Web application built on **ZCBM (Zero-shot Concept Bottleneck Models)** that classifies images and explains *why* through human-readable concepts with contribution weights.

---

## Architecture

```
Browser (React)
    ↓ HTTP
FastAPI Backend (port 8000)
    ├── /api/classify     → ZCBM Model (GPU singleton)
    ├── /api/datasets     → Scan classnames files
    ├── /api/history      → SQLite database
    └── /uploads/         → Static image files

Frontend (Vite dev server, port 5173)
    └── Proxy /api + /uploads → Backend
```

### Tech Stack

| Layer    | Technology                  |
|----------|-----------------------------|
| Frontend | React 18 + TypeScript + Tailwind CSS + Vite |
| Backend  | FastAPI + SQLAlchemy + Pydantic |
| Database | SQLite (MVP, migrate to PostgreSQL later) |
| AI Model | ZCBM + CLIP ViT-B/32 + FAISS (8M concepts) |

| GPU      | NVIDIA L40S 46GB VRAM       |

---

## Project Structure

```
xplaincv/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, lifespan, CORS, static files
│   │   ├── config.py               # Settings (paths, DB URL, CORS origins)
│   │   ├── database.py             # SQLAlchemy engine + session
│   │   ├── models.py               # ORM: classifications table
│   │   ├── schemas.py              # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── classify.py         # POST /api/classify
│   │   │   ├── history.py          # GET /api/history, /api/history/{id}
│   │   │   └── datasets.py         # GET /api/datasets
│   │   └── services/
│   │       └── zcbm_service.py     # Model singleton, inference, dataset switching
│   ├── uploads/                    # Uploaded images (auto-created)
│   ├── requirements.txt
│   └── run.py                      # uvicorn entry point
├── frontend/
│   ├── src/
│   │   ├── api/client.ts           # Typed API wrapper (fetch)
│   │   ├── components/
│   │   │   ├── Navbar.tsx           # Top navigation bar
│   │   │   ├── ImageUploader.tsx    # Drag & drop image upload
│   │   │   ├── ConceptChart.tsx     # Horizontal bar chart of concept weights
│   │   │   ├── ResultCard.tsx       # Prediction display (class, confidence, metrics)
│   │   │   └── LoadingOverlay.tsx   # Spinner with elapsed timer
│   │   ├── pages/
│   │   │   ├── ClassifyPage.tsx     # Upload + results view
│   │   │   ├── HistoryPage.tsx      # Grid of past classifications
│   │   │   └── DetailPage.tsx       # Single classification detail
│   │   ├── App.tsx                  # Router setup
│   │   └── main.tsx                 # Entry point
│   ├── package.json
│   └── vite.config.ts              # Proxy config for /api + /uploads
└── README.md
```

---

## API Endpoints

### POST /api/classify

Upload an image and classify it.

**Request:** `multipart/form-data`
- `image` (file) — image file (JPEG, PNG, WebP, BMP, TIFF)
- `dataset` (string) — dataset name (e.g., `food101`, `imagenet`, `eurosat`)

**Response:**
```json
{
  "id": 1,
  "predicted_class": "hamburger",
  "confidence": 0.7923,
  "sparsity": 0.8491,
  "clip_score": 0.7362,
  "feat_gap": 0.6873,
  "concepts": [
    {"name": "beste burger", "score": 0.3732},
    {"name": "fergburgers", "score": -0.3511}
  ],
  "inference_time_ms": 1435,
  "image_url": "/uploads/uuid.png",
  "dataset": "food101",
  "created_at": "2026-04-07T16:25:46Z"
}
```

### GET /api/datasets

List available classification datasets.

**Response:**
```json
[
  {"name": "food101", "display_name": "Food-101", "num_classes": 101},
  {"name": "imagenet", "display_name": "ImageNet", "num_classes": 1000}
]
```

### GET /api/history?page=1&page_size=20

Paginated list of past classifications.

### GET /api/history/{id}

Full detail of a single classification (same format as classify response).

---

## Setup & Running

### Prerequisites

- Server with NVIDIA GPU (tested on L40S 46GB)
- Python 3.12 + venv at `/home/ubuntu/zcbm/venv/`
- Node.js 20+
- ZCBM concept bank built:
  - `concept_bank/all.txt` (8M concepts, 117MB)
  - `index/all_ViT-B32_index.bin` (FAISS index, 16GB)

### Install Dependencies

```bash
# Backend (uses existing ZCBM venv)
source /home/ubuntu/zcbm/venv/bin/activate
pip install fastapi uvicorn[standard] sqlalchemy pydantic-settings python-multipart aiofiles

# Frontend
cd /home/ubuntu/zcbm/xplaincv/frontend
npm install
```

### Start Backend

```bash
cd /home/ubuntu/zcbm/xplaincv/backend
source /home/ubuntu/zcbm/venv/bin/activate
python run.py
```

- Runs on `http://0.0.0.0:8000`
- First startup takes ~60s to load ZCBM model into GPU
- Single worker only (GPU model cannot be shared across processes)

### Start Frontend

```bash
cd /home/ubuntu/zcbm/xplaincv/frontend
npm run dev -- --host 0.0.0.0
```

- Runs on `http://localhost:5173`
- Proxies `/api` and `/uploads` to backend automatically

### Access from Local Machine (SSH)

Since the app runs on a remote server, forward ports via SSH:

```bash
ssh -L 5173:localhost:5173 -L 8000:localhost:8000 ubuntu@<your-ec2-host>
```

Then open **http://localhost:5173** in your browser.

---

## Key Design Decisions

### Model Singleton with Dataset Switching

The ZCBM model is loaded **once** at startup (~17GB GPU memory). When a user selects a different dataset (e.g., Food-101 → ImageNet), only three lightweight fields are swapped:

1. `id_classname_dict` — label-to-name mapping
2. `class_names` — list of class names
3. `_classname_features = None` — forces recomputation on next inference

The backbone (CLIP ViT-B/32), FAISS index, and concept bank remain unchanged. A threading lock ensures thread-safety during inference.

### Async Inference

Inference takes ~1-12 seconds. The backend uses `asyncio.to_thread()` to run inference without blocking the FastAPI event loop, so other requests (datasets, history) remain responsive.

### Concept Storage

Concepts are stored as a JSON string in the `concepts_json` column. This avoids join tables for the MVP while keeping data accessible. Will normalize when migrating to PostgreSQL.

### Image Storage

Uploaded images are saved as `uploads/{uuid}.{ext}` and served via FastAPI's `StaticFiles` mount. The frontend accesses them via `/uploads/{filename}`.

---

## Available Datasets

| Name | Display Name | Classes |
|------|-------------|---------|
| `caltech101` | Caltech-101 | 100 |
| `cub` | CUB-200 Birds | 200 |
| `dtd` | DTD Textures | 47 |
| `eurosat` | EuroSAT | 10 |
| `fgvc_aircraft` | FGVC Aircraft | 100 |
| `food101` | Food-101 | 101 |
| `imagenet` | ImageNet | 1000 |
| `oxford_flowers` | Oxford Flowers | 102 |
| `oxford_pets` | Oxford Pets | 37 |
| `stanford_cars` | Stanford Cars | 196 |
| `sun397` | SUN-397 Scenes | 397 |
| `ucf101` | UCF-101 Actions | 101 |

Choose a dataset that matches your image domain for best results. If your image doesn't belong to any class in the dataset, the model will still pick the closest match (with low confidence).

---

## Testing

### Backend API

```bash
# Test datasets endpoint
curl http://localhost:8000/api/datasets | python3 -m json.tool

# Test classification
curl -X POST \
  -F "image=@/path/to/image.jpg" \
  -F "dataset=food101" \
  http://localhost:8000/api/classify | python3 -m json.tool

# Test history
curl http://localhost:8000/api/history | python3 -m json.tool

# Test single classification detail
curl http://localhost:8000/api/history/1 | python3 -m json.tool
```

### Frontend

1. Open http://localhost:5173
2. **Classify Page**: Drag & drop an image, select dataset, click Classify
3. Wait ~12s for inference (loading overlay with timer)
4. View predicted class + concept bar chart
5. **History Page**: Click "History" in navbar to see past classifications
6. **Detail Page**: Click any card in history to see full details

---

## Concept Bank Details

Built from 4 caption datasets (as per ZCBM paper):

| Source | Captions |
|--------|----------|
| Flickr30k | 155K |
| CC3M | 3.3M |
| CC12M | 12M |
| YFCC15M | 14.8M |

**Total concepts after filtering:** 8,040,357
**FAISS index:** 16GB (ViT-B/32 embeddings, 512 dims)
**Filtering:** `--sampling_prob 0.01` (1% sampling for similarity dedup)

---

## Known Limitations

1. **Concept quality** — Concepts are noun phrases from web captions, so they tend to be names/labels (e.g., "beste burger") rather than visual attributes (e.g., "beef patty", "sesame bun").

2. **Dataset mismatch** — If the image doesn't match any class in the selected dataset, the model picks the closest class with low confidence.

3. **Inference time** — ~1-12 seconds per image due to FAISS search + Lasso regression on CPU.

4. **No auth** — MVP has no user accounts or authentication.

5. **SQLite** — Single-writer limitation; will migrate to PostgreSQL for production.

---

## Future Roadmap

- [ ] User accounts + authentication
- [ ] PostgreSQL migration
- [ ] Batch upload (multiple images)
- [ ] Custom dataset support (user-defined class names)
- [ ] S3 image storage
- [ ] Docker deployment
- [ ] Stronger backbone (ViT-L/14) for higher accuracy
