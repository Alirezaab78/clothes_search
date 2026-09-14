<?php

use App\Http\Controllers\SearchController;
use App\Http\Controllers\Admin\ProductController;
use Illuminate\Support\Facades\Route;

Route::view('/', 'search')->name('home');
Route::post('/search', [SearchController::class, 'search'])->name('search');
Route::middleware('auth')->group(function () {
    Route::get('/admin/products/create', [ProductController::class, 'create'])->name('admin.products.create');
    Route::post('/admin/products', [ProductController::class, 'store'])->name('admin.products.store');
});
