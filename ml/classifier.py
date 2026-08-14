import io
from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torchvision import models, transforms

# Checkpoint produced by research/grape_leaf_classifier.ipynb (Section 5).
MODEL_PATH = Path(__file__).resolve().parent.parent / "research" / "models" / "grape_disease_classifier.pt"

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

HEALTHY_LABEL = "Healthy"

# class_names in the checkpoint are the raw dataset folder names (English);
# this maps them to the Uzbek text shown to users.
LABELS_UZ = {
    HEALTHY_LABEL: "Sog'lom barg 🌿",
    "Black_rot": "Qora chirish (Black rot)",
    "Esca": "Eska kasalligi",
    "Leaf_blight": "Barg kuyishi (Leaf blight)",
}

_model: nn.Module | None = None
_class_names: list[str] | None = None
_img_size: int | None = None
_device = torch.device("cpu")


def _load_model() -> None:
    global _model, _class_names, _img_size
    if _model is not None:
        return

    checkpoint = torch.load(MODEL_PATH, map_location=_device)
    _class_names = checkpoint["class_names"]
    _img_size = checkpoint["img_size"]

    model = models.mobilenet_v3_small(weights=None)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, len(_class_names))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    _model = model.to(_device)


@dataclass
class PredictionResult:
    label: str
    label_uz: str
    confidence: float


def predict(image_bytes: bytes) -> PredictionResult:
    """Runs the classifier on raw image bytes. Blocking/CPU-bound —
    call via asyncio.to_thread from async handlers."""
    _load_model()

    transform = transforms.Compose([
        transforms.Resize((_img_size, _img_size)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = transform(image).unsqueeze(0).to(_device)

    with torch.no_grad():
        outputs = _model(tensor)
        probs = torch.softmax(outputs, dim=1)[0]
        idx = int(probs.argmax())

    label = _class_names[idx]
    return PredictionResult(
        label=label,
        label_uz=LABELS_UZ.get(label, label),
        confidence=float(probs[idx]),
    )
