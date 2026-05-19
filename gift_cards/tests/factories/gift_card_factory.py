import factory

from gift_cards.models import GiftCard
from gift_cards.services import GiftCardService


class GiftCardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GiftCard

    code = factory.LazyFunction(GiftCardService.generate_code)
    initial_balance = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    current_balance = factory.SelfAttribute("initial_balance")
    is_active = True
