# Backend API image — for Docker deployment
FROM python:3.10-slim

WORKDIR /srv

# CPU torch keeps the image small
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir "setuptools<70.0.0" \
    && pip install --no-cache-dir \
       fastapi "uvicorn[standard]" pydantic-settings python-multipart \
       Pillow numpy google-genai openai-clip

COPY app ./app
COPY run.py .

EXPOSE 8000
CMD ["python", "run.py"]
