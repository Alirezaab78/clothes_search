<?php

namespace App\Http\Controllers;

use App\Models\Product;
use App\Models\SearchTransaction;
use App\Services\FashionAiService;
use Illuminate\Http\Request;

class SearchController extends Controller
{
    public function search(Request $request, FashionAiService $ai)
    {
        $data = $request->validate(['text' => ['nullable', 'string', 'max:500'], 'image' => ['nullable', 'image', 'max:10240']]);
        if (blank($data['text'] ?? null) && ! $request->hasFile('image')) return back()->withErrors(['text' => 'متن جستجو یا تصویر را وارد کنید.']);

        // برای نسخه تولید: اعتبار فعال اشتراک/اعتبار کاربر پیش از فراخوانی سرویس کنترل شود.
        $matches = $ai->search($data['text'] ?? null, $request->file('image'));
        $scores = collect($matches)->pluck('score', 'product_id');
        $products = Product::with('shop')->whereIn('id', $scores->keys())->where('is_active', true)->get()
            ->sortByDesc(fn ($product) => $scores[$product->id] ?? 0)->values();
        if ($request->user()) SearchTransaction::create(['user_id' => $request->user()->id, 'query_text' => $data['text'] ?? null, 'results_count' => $products->count(), 'status' => 'completed']);

        return view('search', compact('products', 'scores'));
    }
}
