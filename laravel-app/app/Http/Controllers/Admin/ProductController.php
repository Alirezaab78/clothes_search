<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Product;
use App\Models\Shop;
use App\Services\FashionAiService;
use Illuminate\Http\Request;

class ProductController extends Controller
{
    public function create() { return view('admin.products.create', ['shops' => Shop::orderBy('name')->get()]); }

    public function store(Request $request, FashionAiService $ai)
    {
        $data = $request->validate(['shop_id' => ['required', 'exists:shops,id'], 'name' => ['required', 'string', 'max:255'], 'description' => ['nullable', 'string'], 'category' => ['nullable', 'string', 'max:100'], 'price' => ['nullable', 'integer', 'min:0'], 'image' => ['required', 'image', 'max:10240']]);
        $data['image_path'] = $request->file('image')->store('products', 'public'); unset($data['image']);
        $product = Product::create($data);
        $ai->indexProduct($product); // در تولید، این عملیات را به صف منتقل کنید.
        return redirect()->route('admin.products.create')->with('success', 'محصول ثبت و ایندکس شد.');
    }
}
