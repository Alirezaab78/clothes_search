"""Seed محصول‌های Apparel از Hugging Face در Laravel و موتور جستجوی محلی.

نمونه:
    python seed_or_index_data.py --limit 50
"""
import argparse
import io
import sqlite3
import sys
from pathlib import Path

import requests
from datasets import load_dataset

DATASET_NAME = "ashraq/fashion-product-images-small"
DEFAULT_LIMIT = 50
ROOT = Path(__file__).resolve().parents[1]


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="دانلود و ایندکس پوشاک نمونه")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="تعداد محصول Apparel (پیش‌فرض: 50)")
    parser.add_argument("--ai-url", default="http://127.0.0.1:8001", help="آدرس FastAPI")
    parser.add_argument("--laravel-db", type=Path, default=ROOT / "laravel-app/database/database.sqlite")
    parser.add_argument("--laravel-storage", type=Path, default=ROOT / "laravel-app/storage/app/public/products")
    return parser.parse_args()


def ensure_shop(db: sqlite3.Connection) -> int:
    shop_name = "ویترین نمونه پوشاک"
    row = db.execute("SELECT id FROM shops WHERE name = ? LIMIT 1", (shop_name,)).fetchone()
    if row:
        return int(row[0])
    cursor = db.execute(
        """INSERT INTO shops (name, mall_name, address, floor, unit, latitude, longitude, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
        (shop_name, "کاتالوگ آنلاین", "نمونهٔ داده برای آزمایش جستجوی تصویری", "آنلاین", "A-01", 35.7219, 51.3347),
    )
    return int(cursor.lastrowid)


def upsert_product(db: sqlite3.Connection, shop_id: int, item: dict, image_path: str) -> int:
    row = db.execute("SELECT id FROM products WHERE image_path = ? LIMIT 1", (image_path,)).fetchone()
    name = item.get("productDisplayName") or f"محصول پوشاک {item['id']}"
    description = " | ".join(str(item.get(key, "")) for key in ("gender", "subCategory", "articleType", "baseColour", "season") if item.get(key))
    if row:
        product_id = int(row[0])
        db.execute(
            "UPDATE products SET name=?, description=?, category=?, is_active=1, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (name, description, item.get("articleType") or item.get("subCategory"), product_id),
        )
        return product_id
    cursor = db.execute(
        """INSERT INTO products (shop_id, name, description, image_path, category, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
        (shop_id, name, description, image_path, item.get("articleType") or item.get("subCategory")),
    )
    return int(cursor.lastrowid)


def save_image(image, target: Path) -> bytes:
    target.parent.mkdir(parents=True, exist_ok=True)
    image = image.convert("RGB")
    image.save(target, format="JPEG", quality=90, optimize=True)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def index(ai_url: str, product_id: int, image_bytes: bytes, filename: str) -> None:
    response = requests.post(
        f"{ai_url.rstrip('/')}/index",
        data={"product_id": str(product_id)},
        files={"image": (filename, image_bytes, "image/jpeg")},
        timeout=180,
    )
    response.raise_for_status()


def main() -> int:
    args = arguments()
    if args.limit < 1:
        raise SystemExit("--limit باید حداقل 1 باشد.")
    if not args.laravel_db.exists():
        raise SystemExit(f"دیتابیس Laravel یافت نشد: {args.laravel_db}")
    try:
        requests.get(f"{args.ai_url.rstrip('/')}/health", timeout=10).raise_for_status()
    except requests.RequestException as error:
        raise SystemExit(f"سرویس AI آماده نیست: {error}") from error

    # streaming از دانلود کامل دیتاست جلوگیری می‌کند؛ فقط آیتم‌های لازم خوانده می‌شوند.
    stream = load_dataset(DATASET_NAME, split="train", streaming=True)
    indexed = skipped = 0
    with sqlite3.connect(args.laravel_db) as db:
        shop_id = ensure_shop(db)
        for item in stream:
            if item.get("masterCategory") != "Apparel":
                continue
            source_id = int(item["id"])
            relative_path = f"products/hf_{source_id}.jpg"
            try:
                image_bytes = save_image(item["image"], args.laravel_storage / f"hf_{source_id}.jpg")
                product_id = upsert_product(db, shop_id, item, relative_path)
                index(args.ai_url, product_id, image_bytes, f"hf_{source_id}.jpg")
                indexed += 1
                print(f"[{indexed}/{args.limit}] محصول {product_id} ایندکس شد: {item.get('productDisplayName', source_id)}")
            except Exception as error:  # خطای یک عکس، کل seed را متوقف نکند.
                skipped += 1
                print(f"⚠️  آیتم {source_id} رد شد: {error}", file=sys.stderr)
            if indexed >= args.limit:
                break
        db.commit()

    if indexed == 0:
        raise SystemExit("هیچ محصول Apparel ایندکس نشد.")
    print(f"✅ Seed کامل شد: {indexed} محصول ایندکس و {skipped} مورد رد شد.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
