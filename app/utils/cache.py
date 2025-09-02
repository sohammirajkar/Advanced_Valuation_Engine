"""
Redis caching utilities for valuation computations
Implements intelligent caching strategies for expensive calculations
"""

import redis
import json
import hashlib
import pickle
from typing import Any, Optional, Dict, Union, cast
from functools import wraps
import time
from datetime import datetime, timedelta


class RedisCache:
    """Redis-based caching system for valuation computations"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 1):
        """Initialize Redis connection for caching"""
        self.redis_client: redis.Redis = redis.Redis(host=host, port=port, db=db, decode_responses=False)
        self.default_ttl = 3600  # 1 hour default TTL
        
    def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate a unique cache key from parameters"""
        # Sort parameters for consistent hashing
        sorted_params = sorted(params.items())
        params_str = json.dumps(sorted_params, sort_keys=True, default=str)
        
        # Create hash of parameters
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        
        return f"{prefix}:{params_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return pickle.loads(cast(bytes, cached_data))
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        try:
            ttl = ttl or self.default_ttl
            serialized_value = pickle.dumps(value)
            return bool(self.redis_client.setex(key, ttl, serialized_value))
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            keys = cast(list, self.redis_client.keys(pattern))
            if keys:
                return cast(int, self.redis_client.delete(*keys))
            return 0
        except Exception as e:
            print(f"Cache clear pattern error: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = cast(Dict[str, Any], self.redis_client.info())
            return {
                "used_memory": info.get("used_memory_human", "N/A"),
                "keys": cast(int, self.redis_client.dbsize()),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
            }
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {}


# Global cache instance
cache = RedisCache()


def cached_computation(prefix: str, ttl: Optional[int] = None, use_params: Optional[list] = None):
    """
    Decorator for caching expensive computations
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        use_params: List of parameter names to include in cache key (if None, uses all)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract function parameters for cache key
            if use_params:
                cache_params = {k: v for k, v in kwargs.items() if k in use_params}
            else:
                cache_params = kwargs.copy()
            
            # Add positional args to cache params
            if args:
                cache_params["_args"] = args
            
            # Generate cache key
            cache_key = cache._generate_cache_key(prefix, cache_params)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Compute result
            start_time = time.time()
            result = func(*args, **kwargs)
            computation_time = time.time() - start_time
            
            # Add metadata to result if it's a dict
            if isinstance(result, dict):
                result["_cache_metadata"] = {
                    "computation_time": computation_time,
                    "cached_at": datetime.now().isoformat(),
                    "cache_key": cache_key
                }
            
            # Cache the result
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str) -> int:
    """Utility function to invalidate cache patterns"""
    return cache.clear_pattern(pattern)


def warm_cache_for_common_parameters():
    """Pre-compute and cache results for common parameter combinations"""
    from app.models.valuation_models import BlackScholesModel, BinomialTreeModel
    
    # Common stock prices
    stock_prices = [50, 100, 150, 200]
    # Common strikes
    strikes = [90, 100, 110]
    # Common times to expiration
    times = [0.25, 0.5, 1.0]  # 3 months, 6 months, 1 year
    # Common volatilities
    volatilities = [0.15, 0.25, 0.35]
    # Risk-free rate
    r = 0.05
    
    print("Warming cache with common parameter combinations...")
    
    for S in stock_prices:
        for K in strikes:
            for T in times:
                for sigma in volatilities:
                    try:
                        # Cache Black-Scholes calculations
                        BlackScholesModel.european_call(S, K, T, r, sigma)
                        BlackScholesModel.european_put(S, K, T, r, sigma)
                        BlackScholesModel.greeks(S, K, T, r, sigma, "call")
                        BlackScholesModel.greeks(S, K, T, r, sigma, "put")
                        
                        # Cache some binomial tree calculations
                        if S <= 100 and K <= 100:  # Limit to avoid too many computations
                            BinomialTreeModel.american_option(S, K, T, r, sigma, 50, "call")
                            BinomialTreeModel.american_option(S, K, T, r, sigma, 50, "put")
                    except Exception as e:
                        print(f"Error warming cache for S={S}, K={K}, T={T}, sigma={sigma}: {e}")
    
    print("Cache warming completed!")


class CacheManager:
    """Advanced cache management utilities"""
    
    def __init__(self, cache_instance: Optional[RedisCache] = None):
        self.cache = cache_instance or cache
    
    def get_cached_computations_summary(self) -> Dict[str, Any]:
        """Get summary of cached computations"""
        try:
            all_keys = cast(list, self.cache.redis_client.keys("*"))
            
            summary = {
                "total_keys": len(all_keys),
                "by_prefix": {},
                "total_memory": 0
            }
            
            for key in all_keys:
                if isinstance(key, bytes):
                    key = key.decode()
                
                prefix = key.split(":")[0] if ":" in key else "unknown"
                
                if prefix not in summary["by_prefix"]:
                    summary["by_prefix"][prefix] = 0
                summary["by_prefix"][prefix] += 1
            
            return summary
        except Exception as e:
            return {"error": str(e)}
    
    def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries"""
        # Redis automatically handles TTL, but this can force cleanup of old patterns
        patterns_to_clean = [
            "monte_carlo:*",  # Clean old Monte Carlo results older than 1 day
            "option_pricing:*"  # Clean old option pricing older than 1 day
        ]
        
        total_cleaned = 0
        for pattern in patterns_to_clean:
            total_cleaned += self.cache.clear_pattern(pattern)
        
        return total_cleaned
    
    def schedule_cache_warmup(self):
        """Schedule regular cache warmup for production"""
        # This would typically be called by a scheduler like Celery beat
        warm_cache_for_common_parameters()


# Initialize cache manager
cache_manager = CacheManager()