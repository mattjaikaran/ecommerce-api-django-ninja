from unittest.mock import patch

import pytest

from feature_flags.models import FeatureFlag
from feature_flags.services import is_flag_enabled
from feature_flags.tests.factories import FeatureFlagFactory


@pytest.mark.django_db
class TestFeatureFlagModel:
    def test_create_flag(self):
        flag = FeatureFlagFactory()
        assert flag.id is not None
        assert flag.is_enabled is True
        assert flag.rollout_percentage == 100

    def test_disabled_flag(self):
        flag = FeatureFlagFactory(is_enabled=False)
        assert flag.is_enabled is False


@pytest.mark.django_db
class TestFeatureFlagService:
    def test_nonexistent_flag_returns_false(self):
        with patch("feature_flags.services.feature_flag_service.cache") as mock_cache:
            mock_cache.get.return_value = None
            result = is_flag_enabled("nonexistent_flag")
        assert result is False

    def test_enabled_flag_100_percent_returns_true(self):
        FeatureFlagFactory(name="full_rollout", is_enabled=True, rollout_percentage=100)

        with patch("feature_flags.services.feature_flag_service.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set = lambda *a, **k: None
            result = is_flag_enabled("full_rollout")
        assert result is True

    def test_disabled_flag_returns_false(self):
        FeatureFlagFactory(name="disabled_flag", is_enabled=False, rollout_percentage=100)

        with patch("feature_flags.services.feature_flag_service.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set = lambda *a, **k: None
            result = is_flag_enabled("disabled_flag")
        assert result is False

    def test_cache_hit_enabled(self):
        with patch("feature_flags.services.feature_flag_service.cache") as mock_cache:
            mock_cache.get.return_value = {"enabled": True, "rollout": 100, "allowed_user_ids": []}
            result = is_flag_enabled("cached_flag")
        assert result is True

    def test_cache_hit_disabled(self):
        with patch("feature_flags.services.feature_flag_service.cache") as mock_cache:
            mock_cache.get.return_value = {"enabled": False, "rollout": 0, "allowed_user_ids": []}
            result = is_flag_enabled("cached_disabled")
        assert result is False

    def test_rollout_zero_percent_returns_false(self):
        FeatureFlagFactory(name="zero_rollout", is_enabled=True, rollout_percentage=0)

        with patch("feature_flags.services.feature_flag_service.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set = lambda *a, **k: None
            result = is_flag_enabled("zero_rollout", user=None)
        assert result is False
