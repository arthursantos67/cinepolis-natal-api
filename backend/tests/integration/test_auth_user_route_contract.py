import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_auth_routes_exist_only_under_auth_prefix():
    client = APIClient()

    intended_routes = [
        "/api/v1/auth/register/",
        "/api/v1/auth/login/",
        "/api/v1/auth/token/refresh/",
    ]
    wrong_prefix_routes = [
        "/api/v1/users/register/",
        "/api/v1/users/login/",
        "/api/v1/users/token/refresh/",
    ]

    for route in intended_routes:
        response = client.post(route, {}, format="json")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    for route in wrong_prefix_routes:
        response = client.post(route, {}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_user_routes_exist_only_under_users_prefix():
    client = APIClient()

    intended_routes = [
        "/api/v1/users/me/",
        "/api/v1/users/me/tickets/",
    ]
    wrong_prefix_routes = [
        "/api/v1/auth/me/",
        "/api/v1/auth/me/tickets/",
    ]

    for route in intended_routes:
        response = client.get(route)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    for route in wrong_prefix_routes:
        response = client.get(route)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_openapi_schema_documents_only_canonical_auth_and_user_routes():
    client = APIClient()

    response = client.get("/api/schema/")

    assert response.status_code == status.HTTP_200_OK
    schema = response.content.decode()

    assert "/api/v1/auth/register/" in schema
    assert "/api/v1/auth/login/" in schema
    assert "/api/v1/auth/token/refresh/" in schema
    assert "/api/v1/users/me/" in schema
    assert "/api/v1/users/me/tickets/" in schema

    assert "/api/v1/users/register/" not in schema
    assert "/api/v1/users/login/" not in schema
    assert "/api/v1/users/token/refresh/" not in schema
    assert "/api/v1/auth/me/" not in schema
    assert "/api/v1/auth/me/tickets/" not in schema
