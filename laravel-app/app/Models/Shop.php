<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Shop extends Model
{
    use HasFactory;

    protected $fillable = ['name', 'mall_name', 'address', 'floor', 'unit', 'latitude', 'longitude', 'phone', 'is_active'];

    protected function casts(): array
    {
        return ['latitude' => 'float', 'longitude' => 'float', 'is_active' => 'boolean'];
    }

    public function products() { return $this->hasMany(Product::class); }
}
