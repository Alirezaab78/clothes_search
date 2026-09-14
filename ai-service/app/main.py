"""میکروسرویس محلی جستجوی پوشاک؛ بدون Docker و بدون دیتابیس خارجی."""
import io
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import numpy as np
import open_clip
import torch
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from PIL import Image

DIMENSION = 512
DATABASE_PATH = Path(os.getenv("FASHION_AI_DB_PATH", Path(__file__).parents[1] / "data" / "fashion.db"))
MODEL_NAME = os.getenv("OPENCLIP_MODEL", "ViT-B-32")
MODEL_WEIGHTS = os.getenv("OPENCLIP_PRETRAINED", "laion2b_s34b_b79k")

# وزن مدل در اجرای نخست در cache محلی Python ذخیره می‌شود.
model, _, preprocess = open_clip.create_model_and_transforms(MODEL_NAME, pretrained=MODEL_WEIGHTS)
tokenizer = open_clip.get_tokenizer(MODEL_NAME)
model.eval()

def connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    return db

def prepare_database() -> None:
    with connection() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS embeddings (
            product_id INTEGER PRIMARY KEY,
            vector BLOB NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")

@asynccontextmanager
async def lifespan(_: FastAPI):
    prepare_database()
    yield

app = FastAPI(title="Fashion AI Search (Local SQLite)", version="1.1.0", lifespan=lifespan)

def normalize(vector: torch.Tensor) -> np.ndarray:
    vector = vector / vector.norm(dim=-1, keepdim=True)
    return vector[0].detach().cpu().numpy().astype(np.float32)

def image_embedding(raw: bytes) -> np.ndarray:
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    with torch.no_grad():
        return normalize(model.encode_image(preprocess(image).unsqueeze(0)))

def text_embedding(text: str) -> np.ndarray:
    with torch.no_grad():
        return normalize(model.encode_text(tokenizer([text])))

def save_embedding(product_id: int, vector: np.ndarray) -> None:
    with connection() as db:
        db.execute(
            "INSERT INTO embeddings(product_id, vector) VALUES(?, ?) "
            "ON CONFLICT(product_id) DO UPDATE SET vector=excluded.vector, updated_at=CURRENT_TIMESTAMP",
            (product_id, vector.tobytes()),
        )

def nearest(vector: np.ndarray, limit: int) -> list[dict]:
    """Cosine similarity برای کاتالوگ کوچک تا متوسط، بدون سرویس خارجی."""
    with connection() as db:
        rows = db.execute("SELECT product_id, vector FROM embeddings").fetchall()
    ranked = []
    for product_id, raw in rows:
        candidate = np.frombuffer(raw, dtype=np.float32)
        if candidate.size == DIMENSION:
            ranked.append((int(product_id), float(np.dot(vector, candidate))))
    ranked.sort(key=lambda item: item[1], reverse=True)
    return [{"product_id": product_id, "score": round(score, 4)} for product_id, score in ranked[:limit]]

@app.get("/health")
def health():
    with connection() as db:
        count = db.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    return {"status": "ok", "storage": "sqlite", "database": str(DATABASE_PATH), "indexed_products": count}

@app.post("/index")
async def index_product(product_id: int = Form(...), image: UploadFile = File(...)):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(422, "فایل تصویر معتبر نیست")
    save_embedding(product_id, image_embedding(await image.read()))
    return {"indexed": True, "product_id": product_id}

@app.post("/search")
async def search(text: Optional[str] = Form(None), image: Optional[UploadFile] = File(None), limit: int = Form(24)):
    if not text and not image:
        raise HTTPException(422, "text یا image لازم است")
    vector = image_embedding(await image.read()) if image else text_embedding(text or "")
    return {"results": nearest(vector, min(max(limit, 1), 50))}
