# ویترین‌یاب

پلتفرم فارسی جستجوی پوشاک مشابه با Laravel و FastAPI/OpenCLIP. این نسخه برای اجرای محلی به Docker یا Qdrant نیاز ندارد.

## ساختار

- `laravel-app/`: رابط کاربری، کاربران، محصولات، فروشگاه‌ها و اعتبار جستجو.
- `ai-service/`: میکروسرویس Python. بردارها در SQLite محلی در `ai-service/data/fashion.db` نگهداری می‌شوند.

## اجرای سرویس هوش مصنوعی در ویندوز

در PowerShell:

```powershell
cd E:\Alireza\projects\gapcode_projects\clothes_search\ai-service
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

برای اطمینان، `http://127.0.0.1:8001/health` را باز کنید. در اجرای اول، وزن مدل OpenCLIP دانلود و در cache محلی Python ذخیره می‌شود؛ دفعات بعد از همان cache استفاده می‌کند.

## اجرای Laravel

در `laravel-app/.env` مطمئن شوید این مقادیر تنظیم شده‌اند:

```env
DB_CONNECTION=sqlite
FASHION_AI_URL=http://127.0.0.1:8001
```

سپس:

```powershell
cd E:\Alireza\projects\gapcode_projects\clothes_search\laravel-app
php artisan key:generate
php artisan migrate
php artisan storage:link
php artisan serve
```

## روش جستجوی محلی

هنگام ثبت محصول، Laravel عکس را به `POST /index` می‌فرستد و embedding تصویر در SQLite ذخیره می‌شود. `POST /search` embedding متن یا تصویر را با cosine similarity با همهٔ بردارهای محلی مقایسه می‌کند و شناسهٔ محصولات و نمرهٔ تطابق را برمی‌گرداند. این حالت برای شروع و کاتالوگ کوچک تا متوسط مناسب است. اگر کاتالوگ بسیار بزرگ شد، می‌توان لایهٔ SQLite را بعداً با FAISS جایگزین کرد؛ قرارداد ارتباطی Laravel تغییر نمی‌کند.

## نکات انتشار

- OTP را با یک سرویس پیامکی ایرانی و rate limit پیاده‌سازی کنید.
- اتصال درگاه پرداخت به کلید و callback واقعی زرین‌پال یا نکست‌پی نیاز دارد.
- مسیر ثبت محصول با `auth` محافظت شده است؛ پیش از انتشار، نقش/مجوز ادمین نیز اضافه کنید.
