from django.core.cache import cache


def test_redis_cache_set_and_get():
    cache_key = "test:redis:cache:set-get"
    cache_value = "ok"

    cache.set(cache_key, cache_value, timeout=30)

    assert cache.get(cache_key) == cache_value