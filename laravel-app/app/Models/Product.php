<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Product extends Model
{
    use HasFactory;
    protected $fillable = ['shop_id', 'name', 'description', 'image_path', 'category', 'price', 'is_active', 'indexed_at'];
    protected function casts(): array { return ['price' => 'decimal:0', 'is_active' => 'boolean', 'indexed_at' => 'datetime']; }
    public function shop() { return $this->belongsTo(Shop::class); }
}
