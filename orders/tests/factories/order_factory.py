from decimal import Decimal

import factory

from core.tests.factories import AddressFactory, CustomerFactory, CustomerGroupFactory
from orders.models import Order
from orders.models.choices import (
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    ShippingMethod,
)


class OrderFactory(factory.django.DjangoModelFactory):
    """Factory for creating Order instances."""

    class Meta:
        model = Order

    order_number = factory.Sequence(lambda n: f"ORD-{n:06d}")
    customer = factory.SubFactory(CustomerFactory)
    customer_group = factory.SubFactory(CustomerGroupFactory)
    status = OrderStatus.DRAFT
    currency = "USD"
    subtotal = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        positive=True,
        min_value=Decimal("10.00"),
        max_value=Decimal("999.99"),
    )
    shipping_amount = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=Decimal("1.00"),
        max_value=Decimal("50.00"),
    )
    shipping_method = ShippingMethod.STANDARD
    shipping_tax_amount = factory.Faker(
        "pydecimal",
        left_digits=1,
        right_digits=2,
        positive=True,
        min_value=Decimal("0.01"),
        max_value=Decimal("5.00"),
    )
    discount_amount = Decimal("0.00")
    tax_amount = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=Decimal("1.00"),
        max_value=Decimal("50.00"),
    )
    total = factory.LazyAttribute(
        lambda obj: obj.subtotal
        + obj.shipping_amount
        + obj.tax_amount
        + obj.shipping_tax_amount
        - obj.discount_amount
    )
    payment_status = PaymentStatus.PENDING
    payment_method = PaymentMethod.CREDIT_CARD
    payment_gateway = "stripe"
    payment_gateway_id = factory.Faker("uuid4")
    payment_gateway_response = factory.LazyFunction(dict)
    billing_address = factory.SubFactory(AddressFactory, is_billing=True)
    shipping_address = factory.SubFactory(AddressFactory, is_shipping=True)
    email = factory.Faker("email")
    phone = factory.Faker("phone_number")
    customer_note = factory.Faker("text", max_nb_chars=200)
    staff_notes = factory.Faker("text", max_nb_chars=200)
    ip_address = factory.Faker("ipv4")
    user_agent = factory.Faker("user_agent")
    meta_data = factory.LazyFunction(dict)
    created_by = factory.SelfAttribute("customer.user")
    updated_by = factory.SelfAttribute("customer.user")


class DraftOrderFactory(OrderFactory):
    """Factory for creating draft Order instances."""

    status = OrderStatus.DRAFT
    payment_status = PaymentStatus.PENDING


class ConfirmedOrderFactory(OrderFactory):
    """Factory for creating confirmed Order instances."""

    status = OrderStatus.PROCESSING
    payment_status = PaymentStatus.PAID


class ShippedOrderFactory(OrderFactory):
    """Factory for creating shipped Order instances."""

    status = OrderStatus.SHIPPED
    payment_status = PaymentStatus.PAID


class DeliveredOrderFactory(OrderFactory):
    """Factory for creating delivered Order instances."""

    status = OrderStatus.DELIVERED
    payment_status = PaymentStatus.PAID


class CancelledOrderFactory(OrderFactory):
    """Factory for creating cancelled Order instances."""

    status = OrderStatus.CANCELLED
    payment_status = PaymentStatus.CANCELLED
