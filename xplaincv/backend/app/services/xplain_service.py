import sys
import threading
import time
import warnings

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from sklearn.linear_model import Lasso

from app.config import Settings
from app.services.concept_filter import is_noise, normalize_class_names

warnings.filterwarnings("ignore")


class XplainService:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._model = None
        self._current_dataset: str | None = None
        self._lock = threading.Lock()
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._datasets: dict[str, dict] = {}
        self._scan_datasets()

    def _scan_datasets(self):
        classnames_dir = self._settings.ZCBM_ROOT / self._settings.CLASSNAMES_DIR
        for f in sorted(classnames_dir.glob("*.txt")):
            num_classes = sum(1 for _ in f.open())
            name = f.stem
            self._datasets[name] = {
                "name": name,
                "display_name": self._format_display_name(name),
                "num_classes": num_classes,
                "path": str(f),
            }

    @staticmethod
    def _format_display_name(name: str) -> str:
        mapping = {
            "imagenet": "ImageNet",
            "eurosat": "EuroSAT",
            "food101": "Food-101",
            "caltech101": "Caltech-101",
            "cub": "CUB-200 Birds",
            "dtd": "DTD Textures",
            "fgvc_aircraft": "FGVC Aircraft",
            "oxford_flowers": "Oxford Flowers",
            "oxford_pets": "Oxford Pets",
            "stanford_cars": "Stanford Cars",
            "sun397": "SUN-397 Scenes",
            "ucf101": "UCF-101 Actions",
        }
        return mapping.get(name, name.replace("_", " ").title())

    def load_model(self, initial_dataset: str = "food101"):
        root = self._settings.ZCBM_ROOT
        sys.path.insert(0, str(root))
        from model.zeroshot_cbm import ZCBM

        classname_file = self._datasets[initial_dataset]["path"]
        self._model = ZCBM(
            backbone_name=self._settings.BACKBONE,
            classname_file=classname_file,
            concept_index=str(root / self._settings.CONCEPT_INDEX),
            metadata_path=str(root / self._settings.METADATA_PATH),
            num_concept_candidates=self._settings.NUM_CONCEPT_CANDIDATES,
            num_present_concepts=self._settings.NUM_PRESENT_CONCEPTS,
            selection_strategy="lasso",
            alpha=self._settings.LASSO_ALPHA,
        )
        self._model = self._model.to(self._device)
        self._model.eval()
        self._current_dataset = initial_dataset

    def _switch_dataset(self, dataset: str):
        if dataset == self._current_dataset:
            return
        if dataset not in self._datasets:
            raise ValueError(f"Unknown dataset: {dataset}")
        classname_file = self._datasets[dataset]["path"]
        self._model.id_classname_dict = self._model._make_classname_dict(classname_file)
        self._model.class_names = list(self._model.id_classname_dict.values())
        self._model._classname_features = None
        self._current_dataset = dataset

    def _encode_texts(self, texts: list[str]) -> torch.Tensor:
        tokens = torch.cat([self._model.tokenizer(t) for t in texts]).to(self._device)
        with torch.no_grad():
            feat = self._model.backbone.encode_text(tokens)
        return feat / feat.norm(dim=-1, keepdim=True)

    def get_datasets(self) -> list[dict]:
        return [
            {
                "name": d["name"],
                "display_name": d["display_name"],
                "num_classes": d["num_classes"],
            }
            for d in self._datasets.values()
        ]

    # Mode 1: Auto (original ZCBM, bank search only)
    def classify_auto(self, image: Image.Image, dataset: str) -> dict:
        with self._lock:
            self._switch_dataset(dataset)
            img_tensor = self._model.img_preprocess(image).unsqueeze(0).to(self._device)
            start = time.time()
            with torch.no_grad():
                output = self._model(img_tensor)
            elapsed_ms = int((time.time() - start) * 1000)

        # Cosmetic display filter (see app.services.concept_filter).
        # ZCBM has already done Lasso internally on the unfiltered bank, so
        # the prediction is fixed; we only sanitize what the user sees.
        class_names = normalize_class_names(self._model.class_names)
        concepts = [
            {"name": str(n), "score": round(float(s), 6), "source": "bank"}
            for n, s in zip(output["topk_concepts"][0], output["topk_scores"][0])
            if not is_noise(str(n), class_names)
        ]
        return {
            "mode": "auto",
            "predicted_class": output["pred_classnames"][0],
            "confidence": round(float(output["probs"][0].item()), 6),
            "feat_gap": round(float(output["feat_gap"]), 6),
            "concepts": concepts,
            "user_contributions": None,
            "dataset": dataset,
            "labels": None,
            "user_concepts": None,
            "intervention": None,
            "inference_time_ms": elapsed_ms,
        }

    # Mode 2: Manual (user concepts + user labels, no bank)
    def classify_manual(
        self, image: Image.Image, concepts: list[str], labels: list[str]
    ) -> dict:
        with self._lock:
            img_tensor = self._model.img_preprocess(image).unsqueeze(0).to(self._device)
            start = time.time()
            with torch.no_grad():
                img_feat = self._model.backbone.encode_image(img_tensor)
                img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)

            concept_feat = self._encode_texts(concepts)
            label_feat = self._encode_texts([f"a photo of {l}" for l in labels])

            c_cpu = concept_feat.cpu().float()
            l_cpu = label_feat.cpu().float()
            img_cpu = img_feat.cpu().float()

            lasso = Lasso(alpha=self._settings.LASSO_ALPHA, fit_intercept=False)
            lasso.fit(c_cpu.numpy().T, img_cpu.squeeze(0).numpy())
            coefs = torch.from_numpy(lasso.coef_).float()

            predicted = (coefs.unsqueeze(-1) * c_cpu).sum(dim=0, keepdim=True)
            pred_norm = predicted / predicted.norm(dim=-1, keepdim=True)
            label_sims = (pred_norm @ l_cpu.T).squeeze(0).clamp(0, 1)
            prob, pred_idx = label_sims.topk(1)

            feat_gap = F.pairwise_distance(img_cpu, predicted, p=2).item()
            elapsed_ms = int((time.time() - start) * 1000)

        concept_scores = sorted(
            [
                {"name": n, "score": round(float(c), 6), "source": "user"}
                for n, c in zip(concepts, coefs)
            ],
            key=lambda x: abs(x["score"]),
            reverse=True,
        )
        label_scores = sorted(
            [
                {"name": n, "score": round(float(s), 6)}
                for n, s in zip(labels, label_sims)
            ],
            key=lambda x: x["score"],
            reverse=True,
        )
        return {
            "mode": "manual",
            "predicted_class": labels[pred_idx.item()],
            "confidence": round(float(prob.item()), 6),
            "feat_gap": round(feat_gap, 6),
            "concepts": concept_scores,
            "user_contributions": None,
            "dataset": None,
            "labels": label_scores,
            "user_concepts": concepts,
            "intervention": None,
            "inference_time_ms": elapsed_ms,
        }

    # Mode 3: Hybrid (dual-Lasso bank/user with alpha blending)
    def classify_hybrid(
        self,
        image: Image.Image,
        user_concepts: list[str],
        dataset: str,
        alpha: float = 0.5,
    ) -> dict:
        alpha = max(0.0, min(1.0, float(alpha)))
        with self._lock:
            self._switch_dataset(dataset)
            img_tensor = self._model.img_preprocess(image).unsqueeze(0).to(self._device)
            start = time.time()
            with torch.no_grad():
                img_feat = self._model.backbone.encode_image(img_tensor)
                img_norm = img_feat / img_feat.norm(dim=-1, keepdim=True)

                retrieved = self._model.conceptbase(images_z=img_feat)
                bank_vecs_all = torch.tensor(
                    np.array(retrieved[0]["embeddings"])
                ).cpu().float()
                bank_names_all = [str(n) for n in retrieved[0]["concepts"][0]]

                # Drop junk + class-name circular reasoning BEFORE Lasso fit,
                # so noisy concepts cannot influence the bank reconstruction.
                # See app.services.concept_filter.is_noise.
                class_names = normalize_class_names(self._model.class_names)
                keep = [
                    i for i, n in enumerate(bank_names_all)
                    if not is_noise(n, class_names)
                ]
                if len(keep) < 4:
                    # Filter ate too much — fall back to original 32 candidates.
                    keep = list(range(len(bank_names_all)))
                bank_vecs = bank_vecs_all[keep]
                bank_names = [bank_names_all[i] for i in keep]

                img_cpu = img_norm.cpu().float().squeeze(0)
                img_np = img_cpu.numpy()

                # Bank-only Lasso
                lasso_b = Lasso(alpha=self._settings.LASSO_ALPHA, fit_intercept=False)
                lasso_b.fit(bank_vecs.numpy().T, img_np)
                bank_coefs = torch.from_numpy(lasso_b.coef_).float()
                bank_raw = (bank_coefs.unsqueeze(-1) * bank_vecs).sum(dim=0, keepdim=True)

                # User-only Lasso
                user_vecs = self._encode_texts(user_concepts).cpu().float()
                lasso_u = Lasso(alpha=self._settings.LASSO_ALPHA, fit_intercept=False)
                lasso_u.fit(user_vecs.numpy().T, img_np)
                user_coefs = torch.from_numpy(lasso_u.coef_).float()
                user_raw = (user_coefs.unsqueeze(-1) * user_vecs).sum(dim=0, keepdim=True)

                bank_norm = float(bank_raw.norm().item())
                user_norm = float(user_raw.norm().item())

                bank_dir = (
                    bank_raw / bank_norm if bank_norm > 1e-6 else bank_raw
                )
                if user_norm > 1e-6:
                    user_dir = user_raw / user_norm
                    effective_alpha = alpha
                else:
                    # User concepts reconstructed to zero → can't blend, collapse to bank
                    user_dir = bank_dir
                    effective_alpha = 0.0

                final_vec = (
                    (1.0 - effective_alpha) * bank_dir + effective_alpha * user_dir
                )

                class_feat = (
                    self._model.get_text_features(img_tensor.device).cpu().float()
                )
                final_scores = (100.0 * final_vec @ class_feat.T).softmax(
                    dim=-1
                ).squeeze(0)
                bank_scores = (100.0 * bank_dir @ class_feat.T).softmax(
                    dim=-1
                ).squeeze(0)

                final_prob, final_idx = final_scores.topk(1)
                bank_prob, bank_idx = bank_scores.topk(1)

                feat_gap = float(
                    F.pairwise_distance(img_cpu.unsqueeze(0), final_vec, p=2).item()
                )
            elapsed_ms = int((time.time() - start) * 1000)

        # Scaled contributions: each concept's share of the FINAL direction
        bank_scale = (1.0 - effective_alpha) / max(bank_norm, 1e-8)
        user_scale = effective_alpha / max(user_norm, 1e-8)
        bank_items = [
            {
                "name": n,
                "score": round(float(bank_coefs[i]) * bank_scale, 6),
                "source": "bank",
            }
            for i, n in enumerate(bank_names)
        ]
        bank_items.sort(key=lambda x: abs(x["score"]), reverse=True)
        top_bank = bank_items[: self._settings.NUM_PRESENT_CONCEPTS]

        user_items = [
            {
                "name": n,
                "score": round(float(user_coefs[i]) * user_scale, 6),
                "source": "user",
            }
            for i, n in enumerate(user_concepts)
        ]
        user_items.sort(key=lambda x: abs(x["score"]), reverse=True)

        bank_pred_class = self._model.id_classname_dict[str(bank_idx.item())]
        final_pred_class = self._model.id_classname_dict[str(final_idx.item())]
        bank_confidence = float(bank_prob.item())
        final_confidence = float(final_prob.item())

        num_user = len(user_concepts)
        user_active = int((user_coefs.abs() > 1e-6).sum().item())
        intervention = {
            "user_concept_count": num_user,
            "user_concept_active": user_active,
            "success_rate": round(user_active / num_user, 4) if num_user > 0 else 0.0,
            "contribution_ratio": round(effective_alpha, 4),
            "alpha": round(alpha, 4),
            "bank_reconstr_norm": round(bank_norm, 4),
            "user_reconstr_norm": round(user_norm, 4),
            "changed_prediction": bank_pred_class != final_pred_class,
            "confidence_delta": round(final_confidence - bank_confidence, 6),
            "agreement": bank_pred_class == final_pred_class,
        }

        return {
            "mode": "hybrid",
            "predicted_class": final_pred_class,
            "confidence": round(final_confidence, 6),
            "feat_gap": round(feat_gap, 6),
            "concepts": top_bank,
            "user_contributions": user_items,
            "dataset": dataset,
            "labels": None,
            "user_concepts": user_concepts,
            "intervention": intervention,
            "bank_only": {
                "predicted_class": bank_pred_class,
                "confidence": round(bank_confidence, 6),
            },
            "inference_time_ms": elapsed_ms,
        }
