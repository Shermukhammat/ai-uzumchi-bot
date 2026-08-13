"""
One-off local dataset prep: takes the raw extracted Kaggle dataset
(research/dataset_raw/.../Final Training Data/<Class Name>/*.jpg) and
writes an 80/20 train/val split into research/datasets/grape_disease/
using torchvision.datasets.ImageFolder-compatible folder names
(spaces -> underscores, matching CLASS_NAMES in the notebook).

This dataset includes a horizontally-flipped augmented copy of every
source photo (same UUID prefix, "_flipLR" suffix). Splitting file-by-file
lets a photo end up in train while its near-identical flipped twin ends
up in val, leaking information and inflating val accuracy. We split by
base UUID instead so a photo and its flip always land on the same side.

Run once after unzipping a new dataset download:
    python3 research/prepare_dataset.py
"""

import random
import shutil
from collections import defaultdict
from pathlib import Path

RAW_ROOT = Path(__file__).parent / "dataset_raw" / "Final Training Data"
OUT_ROOT = Path(__file__).parent / "datasets" / "grape_disease"

VAL_FRACTION = 0.2
SEED = 42

# Kaggle folder name -> notebook's CLASS_NAMES convention
CLASS_NAME_MAP = {
    "Black Rot": "Black_rot",
    "ESCA": "Esca",
    "Healthy": "Healthy",
    "Leaf Blight": "Leaf_blight",
}


def base_image_id(filename: str) -> str:
    """Groups a photo with its augmented variants (e.g. '..._flipLR.JPG')."""
    return filename.split("___")[0]


def main() -> None:
    random.seed(SEED)

    if not RAW_ROOT.exists():
        raise SystemExit(f"Raw dataset not found at {RAW_ROOT} — unzip it first.")

    class_dirs = [d for d in RAW_ROOT.iterdir() if d.is_dir()]
    if not class_dirs:
        raise SystemExit(f"No class folders found under {RAW_ROOT}")

    for class_dir in sorted(class_dirs):
        out_name = CLASS_NAME_MAP.get(class_dir.name, class_dir.name.replace(" ", "_"))
        images = [p for p in class_dir.iterdir() if p.is_file()]

        groups: dict[str, list[Path]] = defaultdict(list)
        for img_path in images:
            groups[base_image_id(img_path.name)].append(img_path)

        group_ids = list(groups.keys())
        random.shuffle(group_ids)

        split_idx = int(len(group_ids) * (1 - VAL_FRACTION))
        train_ids, val_ids = group_ids[:split_idx], group_ids[split_idx:]

        train_images = [p for gid in train_ids for p in groups[gid]]
        val_images = [p for gid in val_ids for p in groups[gid]]

        for split_name, split_images in (("train", train_images), ("val", val_images)):
            split_dir = OUT_ROOT / split_name / out_name
            split_dir.mkdir(parents=True, exist_ok=True)
            for img_path in split_images:
                shutil.copy2(img_path, split_dir / img_path.name)

        print(f"{class_dir.name:15s} -> {out_name:12s}  "
              f"train={len(train_images):5d} ({len(train_ids)} source photos)  "
              f"val={len(val_images):5d} ({len(val_ids)} source photos)")

    print(f"\nDone. Dataset written to: {OUT_ROOT}")
    print("Classes found:", sorted(CLASS_NAME_MAP.get(d.name, d.name.replace(' ', '_')) for d in class_dirs))
    print("NOTE: update CLASS_NAMES in the notebook to match the classes actually found above.")


if __name__ == "__main__":
    main()
