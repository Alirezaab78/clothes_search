<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Subscription extends Model
{
    protected $fillable = ['user_id', 'plan', 'searches_remaining', 'starts_at', 'expires_at', 'payment_reference', 'status'];
    protected function casts(): array { return ['starts_at' => 'datetime', 'expires_at' => 'datetime']; }
    public function user() { return $this->belongsTo(User::class); }
}
