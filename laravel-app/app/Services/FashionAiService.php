<?php

namespace App\Services;

use App\Models\Product;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Http;

class FashionAiService
{
    /** ارسال متن یا تصویر به FastAPI و دریافت شناسه‌ها با نمره شباهت. */
    public function search(?string $text, ?UploadedFile $image, int $limit = 24): array
    {
        $request = Http::acceptJson()->timeout(20);
        if ($token = config('services.fashion_ai.token')) $request = $request->withToken($token);
        $data = ['text' => $text, 'limit' => $limit];
        if ($image) {
            $request = $request->attach('image', file_get_contents($image->getRealPath()), $image->getClientOriginalName());
        }
        return $request->post(rtrim(config('services.fashion_ai.url'), '/').'/search', $data)->throw()->json('results', []);
    }

    public function indexProduct(Product $product): void
    {
        $path = storage_path('app/public/'.$product->image_path);
        Http::timeout(60)->attach('image', file_get_contents($path), basename($path))
            ->post(rtrim(config('services.fashion_ai.url'), '/').'/index', ['product_id' => $product->id])->throw();
        $product->update(['indexed_at' => now()]);
    }
}
