import factory

from feature_flags.models import FeatureFlag


class FeatureFlagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FeatureFlag

    name = factory.Sequence(lambda n: f"test_flag_{n}")
    description = factory.Faker("sentence")
    is_enabled = True
    rollout_percentage = 100
