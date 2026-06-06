# XplainCV MVP

An interpretable, **custom-dataset** image verification app built on CLIP.

Unlike the original ZCBM app (kept as a backup in `../xplaincv/`), this MVP
lets the user define their own classes and then performs **one-class
verification** — "is this image a dog, and how confident are we?" — with an
explicit *reject* option when the evidence is too weak.

## How it works

**Tab 1 — Builder**
1. Describe a class in plain language ("a dog has floppy ears, a furry coat…").
2. An LLM (Gemini) extracts the *visual* concepts CLIP can actually detect.
3. Optionally attach a few reference images.
4. Save — concepts and images are CLIP-embedded and an accept/reject
   threshold is calibrated.

**Tab 2 — Verify**
1. Pick a saved profile and upload an image.
2. The app scores the image from two evidence sources — per-concept presence
   probabilities and similarity to the reference images — and either
   **accepts** with a confidence % or **rejects** with a reason.

See `backend/app/services/verify_service.py` for the scoring maths.

## Run it

### Backend
```bash
cd backend
cp .env.example .env          # optional: add GEMINI_API_KEY for AI extraction
# CLIP + torch come from the parent zcbm venv:
/home/ubuntu/zcbm/venv/bin/pip install -r requirements.txt
PYTHONPATH=. /home/ubuntu/zcbm/venv/bin/python run.py
```
Backend serves on `http://localhost:8000` (`/docs` for the API).

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend serves on `http://localhost:5173` and proxies `/api` to the backend.

## Notes
- Without `GEMINI_API_KEY` the Builder still works — you just type concepts
  by hand instead of using AI extraction.
- Profiles are stored as plain folders under `backend/data/profiles/`.
- The original 3-mode ZCBM app is untouched in `../xplaincv/`.
