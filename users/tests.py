import pytest

pytestmark = pytest.mark.django_db

ME_URL = "/auth/users/me/"


def test_me_requires_auth(api_client):
    response = api_client.get(ME_URL)

    assert response.status_code == 401


def test_me_plain_user(api_client, plain_user):
    api_client.force_authenticate(user=plain_user)

    response = api_client.get(ME_URL)

    assert response.status_code == 200
    assert response.data["id"] == plain_user.id
    assert response.data["username"] == "plainuser"
    assert response.data["role"] == "user"
    assert response.data["is_staff"] is False
    assert response.data["breeder_id"] is None


def test_me_breeder(api_client, breeder_user, breeder):
    api_client.force_authenticate(user=breeder_user)

    response = api_client.get(ME_URL)

    assert response.status_code == 200
    assert response.data["role"] == "breeder"
    assert response.data["breeder_id"] == breeder.pk


def test_me_staff(api_client, staff_user):
    api_client.force_authenticate(user=staff_user)

    response = api_client.get(ME_URL)

    assert response.status_code == 200
    assert response.data["is_staff"] is True
    assert response.data["breeder_id"] is None
