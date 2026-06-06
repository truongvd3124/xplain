import threading

import clip
import numpy as np
import torch
from PIL import Image


class ClipEngine:
    def __init__(self, backbone: str = "ViT-B/32") -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model, self._preprocess = clip.load(backbone, device=self.device)
        self._model.eval()
        self.logit_scale = float(self._model.logit_scale.exp().item())
        self.lock = threading.Lock()

    @property
    def embed_dim(self) -> int:
        return self._model.visual.output_dim

    def encode_image(self, image: Image.Image) -> np.ndarray:
        """Embed one PIL image -> normalised vector, shape (embed_dim,)."""
        tensor = self._preprocess(image).unsqueeze(0).to(self.device)
        with self.lock, torch.no_grad():
            feat = self._model.encode_image(tensor)
        return _normalise(feat)[0]

    def encode_texts(self, texts: list[str]) -> np.ndarray:
        """Embed a list of strings -> normalised matrix, shape (N, embed_dim)."""
        if not texts:
            return np.zeros((0, self.embed_dim), dtype=np.float32)
        tokens = clip.tokenize(texts, truncate=True).to(self.device)
        with self.lock, torch.no_grad():
            feat = self._model.encode_text(tokens)
        return _normalise(feat)


def _normalise(feat: torch.Tensor) -> np.ndarray:
    """L2-normalise a (N, D) tensor and return it as float32 numpy."""
    feat = feat / feat.norm(dim=-1, keepdim=True)
    return feat.cpu().float().numpy()
