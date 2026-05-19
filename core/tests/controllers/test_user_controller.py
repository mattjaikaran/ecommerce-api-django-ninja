import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from core.tests.factories import AdminUserFactory, SuperUserFactory, UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestUserController:
    """Test operations for UserController."""

    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.admin_user = AdminUserFactory()
        self.regular_user = UserFactory()
        self.client.force_login(self.admin_user)

    def test_create_user_signup(self):
        """Test creating a new user via signup endpoint."""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "username": "johndoe123",
            "password": "testpass123",
            "confirm_password": "testpass123",
        }

        response = self.client.post(
            "/api/users/signup", data=user_data, content_type="application/json"
        )

        assert response.status_code == 201
        assert User.objects.filter(email=user_data["email"]).exists()

        user = User.objects.get(email=user_data["email"])
        assert user.first_name == user_data["first_name"]
        assert user.last_name == user_data["last_name"]
        assert user.username == user_data["username"]

    def test_create_user_duplicate_email(self):
        """Test creating user with duplicate email fails."""
        existing_user = UserFactory()
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": existing_user.email,
            "username": "johndoe123",
            "password": "testpass123",
            "confirm_password": "testpass123",
        }

        response = self.client.post(
            "/api/users/signup", data=user_data, content_type="application/json"
        )

        assert response.status_code == 400

    def test_create_user_duplicate_username(self):
        """Test creating user with duplicate username fails."""
        existing_user = UserFactory()
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "username": existing_user.username,
            "password": "testpass123",
            "confirm_password": "testpass123",
        }

        response = self.client.post(
            "/api/users/signup", data=user_data, content_type="application/json"
        )

        assert response.status_code == 400

    def test_read_user_list(self):
        """Test retrieving list of users."""
        UserFactory.create_batch(5)

        response = self.client.get("/api/users")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5  # At least 5 users plus existing ones

    def test_read_user_detail(self):
        """Test retrieving a specific user."""
        user = UserFactory()

        response = self.client.get(f"/api/users/{user.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(user.id)
        assert data["email"] == user.email
        assert data["username"] == user.username

    def test_read_user_detail_not_found(self):
        """Test retrieving non-existent user returns 404."""
        import uuid

        fake_id = uuid.uuid4()

        response = self.client.get(f"/api/users/{fake_id}")

        assert response.status_code == 404

    def test_update_user_profile(self):
        """Test updating user profile."""
        user = UserFactory()
        update_data = {"first_name": "Updated", "last_name": "Name", "username": user.username, "email": user.email}

        response = self.client.put(
            f"/api/users/{user.id}", data=update_data, content_type="application/json"
        )

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == update_data["first_name"]
        assert user.last_name == update_data["last_name"]

    def test_update_user_invalid_data(self):
        """Test updating user with a duplicate email fails."""
        user = UserFactory()
        existing_user = UserFactory()
        update_data = {
            "email": existing_user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

        response = self.client.put(
            f"/api/users/{user.id}", data=update_data, content_type="application/json"
        )

        assert response.status_code in (400, 409)

    def test_delete_user(self):
        """Test deleting a user."""
        user = UserFactory()
        user_id = user.id

        response = self.client.delete(f"/api/users/{user_id}")

        assert response.status_code == 204
        assert not User.objects.filter(id=user_id).exists()

    def test_user_login(self):
        """Test user login endpoint."""
        user = UserFactory()
        user.set_password("testpass123")
        user.save()

        login_data = {"username": user.username, "password": "testpass123"}

        response = self.client.post(
            "/api/users/login", data=login_data, content_type="application/json"
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "refresh" in data

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials fails."""
        user = UserFactory()
        login_data = {"username": user.username, "password": "wrongpass"}

        response = self.client.post(
            "/api/users/login", data=login_data, content_type="application/json"
        )

        assert response.status_code == 401


@pytest.mark.django_db
class TestUserControllerPermissions:
    """Test permission requirements for UserController."""

    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.regular_user = UserFactory()

    def test_user_list_requires_authentication(self):
        """Test that user list endpoint requires authentication."""
        response = self.client.get("/api/users")

        assert response.status_code == 401

    def test_user_detail_requires_authentication(self):
        """Test that user detail endpoint requires authentication."""
        user = UserFactory()

        response = self.client.get(f"/api/users/{user.id}")

        assert response.status_code == 401

    def test_regular_user_can_access_own_profile(self):
        """Test that regular user can access their own profile."""
        self.client.force_login(self.regular_user)

        response = self.client.get(f"/api/users/{self.regular_user.id}")

        assert response.status_code == 200

    def test_admin_can_access_all_users(self):
        """Test that admin can access all user profiles."""
        admin = AdminUserFactory()
        self.client.force_login(admin)

        response = self.client.get(f"/api/users/{self.regular_user.id}")

        assert response.status_code == 200

    def test_superuser_can_delete_users(self):
        """Test that superuser can delete users."""
        superuser = SuperUserFactory()
        self.client.force_login(superuser)

        response = self.client.delete(f"/api/users/{self.regular_user.id}")

        assert response.status_code == 204
