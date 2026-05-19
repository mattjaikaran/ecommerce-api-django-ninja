import pytest
from django.test import Client

from core.tests.factories import CustomerFactory, UserFactory


@pytest.mark.django_db
class TestOrderURLs:
    def setup_method(self):
        self.user = UserFactory()
        self.customer = CustomerFactory(user=self.user)

    def test_unauthenticated_returns_401_not_500(self):
        """Unauthenticated request must return 401 (not 500 ConfigError)."""
        c = Client()
        response = c.get("/api/orders")
        # 401 is expected; 500 means the response schema is missing for auth errors
        assert response.status_code in (401, 403), (
            f"Expected 401/403 but got {response.status_code}"
        )

    def test_authenticated_returns_200(self):
        """Authenticated request returns 200 with a list."""
        c = Client()
        c.force_login(self.user)
        response = c.get("/api/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
