import hashlib
import logging

from django.core.cache import cache

from feature_flags.models import FeatureFlag

logger = logging.getLogger(__name__)

_CACHE_TTL = 60


def is_flag_enabled(name: str, user=None) -> bool:
    cache_key = f"ff:{name}"
    cached = cache.get(cache_key)

    if cached is None:
        try:
            flag = FeatureFlag.objects.get(name=name)
        except FeatureFlag.DoesNotExist:
            return False

        if not flag.is_enabled:
            cache.set(cache_key, {"enabled": False, "rollout": 0, "allowed_user_ids": []}, _CACHE_TTL)
            return False

        allowed_user_ids = list(flag.allowed_users.values_list("id", flat=True))
        cached = {
            "enabled": flag.is_enabled,
            "rollout": flag.rollout_percentage,
            "allowed_user_ids": [str(u) for u in allowed_user_ids],
        }
        cache.set(cache_key, cached, _CACHE_TTL)

    if not cached.get("enabled"):
        return False

    rollout = cached.get("rollout", 100)
    if rollout == 100:
        return True

    if user is not None:
        if str(user.id) in (cached.get("allowed_user_ids") or []):
            return True
        user_hash = int(hashlib.md5(f"{user.id}{name}".encode()).hexdigest(), 16)
        return (user_hash % 100) < rollout

    return False


def get_all_flags() -> list:
    return list(FeatureFlag.objects.all())


class FeatureFlagService:
    @staticmethod
    def is_flag_enabled(name: str, user=None) -> bool:
        return is_flag_enabled(name, user)

    @staticmethod
    def get_all_flags() -> list:
        return get_all_flags()
