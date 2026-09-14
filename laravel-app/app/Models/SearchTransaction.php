<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class SearchTransaction extends Model
{
    protected $fillable = ['user_id', 'query_text', 'query_image_path', 'results_count', 'status', 'metadata'];
    protected function casts(): array { return ['metadata' => 'array']; }
    public function user() { return $this->belongsTo(User::class); }
}
