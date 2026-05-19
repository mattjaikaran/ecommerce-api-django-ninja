import pytest
from django.test import Client

from core.tests.factories import AdminUserFactory, UserFactory
from products.models import Product
from products.tests.factories import (
    FeaturedProductFactory,
    ProductCategoryFactory,
    ProductFactory,
    PublishedProductFactory,
)


@pytest.mark.django_db
class TestProductController:
    """Test operations for ProductController."""

    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.admin_user = AdminUserFactory()
        self.regular_user = UserFactory()
        self.client.force_login(self.admin_user)

    def test_create_product(self):
        """Test creating a new product."""
        category = ProductCategoryFactory()
        product_data = {
            "name": "Test Product",
            "slug": "test-product-123",
            "description": "A test product description",
            "category_id": str(category.id),
            "price": "99.99",
            "quantity": 10,
            "weight": "1.5",
            "status": "DRAFT",
        }

        response = self.client.post(
            "/api/products", data=product_data, content_type="application/json"
        )

        assert response.status_code == 201
        assert Product.objects.filter(name=product_data["name"]).exists()

        product = Product.objects.get(name=product_data["name"])
        assert product.slug == product_data["slug"]
        assert str(product.price) == product_data["price"]
        assert product.quantity == product_data["quantity"]

    def test_create_product_duplicate_slug(self):
        """Test creating product with duplicate slug fails."""
        existing_product = ProductFactory()
        category = ProductCategoryFactory()
        product_data = {
            "name": "Test Product",
            "slug": existing_product.slug,
            "description": "A test product description",
            "category_id": str(category.id),
            "price": "99.99",
            "quantity": 10,
        }

        response = self.client.post(
            "/api/products", data=product_data, content_type="application/json"
        )

        assert response.status_code == 409

    def test_read_product_list(self):
        """Test retrieving list of products."""
        ProductFactory.create_batch(5)

        response = self.client.get("/api/products")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5

    def test_read_product_list_filters(self):
        """Test filtering products by various criteria."""
        category = ProductCategoryFactory()
        ProductFactory.create_batch(3, category=category)
        FeaturedProductFactory.create_batch(2, category=category)

        # Test category filter
        response = self.client.get(f"/api/products?category_id={category.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5  # 3 regular + 2 featured

        # Test featured filter
        response = self.client.get("/api/products?featured=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_read_product_detail(self):
        """Test retrieving a specific product."""
        product = ProductFactory()

        response = self.client.get(f"/api/products/{product.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(product.id)
        assert data["name"] == product.name
        assert data["slug"] == product.slug

    def test_read_product_detail_not_found(self):
        """Test retrieving non-existent product returns 404."""
        import uuid

        fake_id = uuid.uuid4()

        response = self.client.get(f"/api/products/{fake_id}")

        assert response.status_code == 404

    def test_update_product(self):
        """Test updating a product."""
        product = ProductFactory()
        category = ProductCategoryFactory()
        update_data = {
            "name": "Updated Product Name",
            "slug": "updated-product-name-xyz",
            "description": "Updated description",
            "category_id": str(category.id),
            "price": "149.99",
        }

        response = self.client.put(
            f"/api/products/{product.id}",
            data=update_data,
            content_type="application/json",
        )

        assert response.status_code == 200
        product.refresh_from_db()
        assert product.name == update_data["name"]
        assert str(product.price) == update_data["price"]
        assert product.description == update_data["description"]

    def test_update_product_invalid_data(self):
        """Test updating product with invalid data (missing required fields) fails with 422."""
        product = ProductFactory()
        update_data = {
            "name": "Missing required fields",
            # slug, category_id, price intentionally omitted
        }

        response = self.client.put(
            f"/api/products/{product.id}",
            data=update_data,
            content_type="application/json",
        )

        assert response.status_code == 422

    def test_delete_product(self):
        """Test deleting a product (soft delete)."""
        product = ProductFactory()

        response = self.client.delete(f"/api/products/{product.id}")

        assert response.status_code == 204
        product.refresh_from_db()
        assert product.is_deleted is True

    def test_search_products(self):
        """Test searching products by name."""
        ProductFactory(name="Smartphone Case")
        ProductFactory(name="Phone Charger")
        ProductFactory(name="Laptop Stand")

        response = self.client.get("/api/products?search=phone")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2  # Should match "Smartphone" and "Phone"

    def test_product_ordering(self):
        """Test ordering products."""
        old_product = ProductFactory()
        new_product = ProductFactory()

        # Test ordering by creation date (newest first)
        response = self.client.get("/api/products?ordering=-created_at")

        assert response.status_code == 200
        data = response.json()
        # Newer product should come first
        product_ids = [item["id"] for item in data]
        new_index = product_ids.index(str(new_product.id))
        old_index = product_ids.index(str(old_product.id))
        assert new_index < old_index


@pytest.mark.django_db
class TestProductControllerPermissions:
    """Test permission requirements for ProductController."""

    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.regular_user = UserFactory()
        self.admin_user = AdminUserFactory()

    def test_product_list_requires_auth(self):
        """Test that product list requires authentication."""
        PublishedProductFactory.create_batch(3)

        response = self.client.get("/api/products")

        assert response.status_code == 401

    def test_product_list_authenticated(self):
        """Test that authenticated users can list products."""
        PublishedProductFactory.create_batch(3)
        self.client.force_login(self.regular_user)

        response = self.client.get("/api/products")

        assert response.status_code == 200

    def test_product_detail_requires_auth(self):
        """Test that product detail requires authentication."""
        product = PublishedProductFactory()

        response = self.client.get(f"/api/products/{product.id}")

        assert response.status_code == 401

    def test_product_detail_authenticated(self):
        """Test that authenticated users can access product detail."""
        product = PublishedProductFactory()
        self.client.force_login(self.regular_user)

        response = self.client.get(f"/api/products/{product.id}")

        assert response.status_code == 200

    def test_create_product_requires_admin(self):
        """Test that creating product requires admin permissions."""
        category = ProductCategoryFactory()
        product_data = {
            "name": "Test Product",
            "slug": "test-product-123",
            "description": "A test product description",
            "category_id": str(category.id),
            "price": "99.99",
            "quantity": 10,
        }

        # Test without authentication
        response = self.client.post(
            "/api/products", data=product_data, content_type="application/json"
        )
        assert response.status_code == 401

        # Test with regular user
        self.client.force_login(self.regular_user)
        response = self.client.post(
            "/api/products", data=product_data, content_type="application/json"
        )
        assert response.status_code == 403

    def test_update_product_requires_admin(self):
        """Test that updating product requires admin permissions."""
        product = ProductFactory()
        category = ProductCategoryFactory()
        update_data = {
            "name": "Updated Product Name",
            "slug": "updated-product-requires-admin",
            "category_id": str(category.id),
            "price": "99.99",
        }

        # Test without authentication
        response = self.client.put(
            f"/api/products/{product.id}",
            data=update_data,
            content_type="application/json",
        )
        assert response.status_code == 401

        # Test with regular user
        self.client.force_login(self.regular_user)
        response = self.client.put(
            f"/api/products/{product.id}",
            data=update_data,
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_product_requires_admin(self):
        """Test that deleting product requires admin permissions."""
        product = ProductFactory()

        # Test without authentication
        response = self.client.delete(f"/api/products/{product.id}")
        assert response.status_code == 401

        # Test with regular user
        self.client.force_login(self.regular_user)
        response = self.client.delete(f"/api/products/{product.id}")
        assert response.status_code == 403
