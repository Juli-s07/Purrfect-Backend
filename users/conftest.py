import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import Breeder


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def plain_user(db):
    return get_user_model().objects.create_user(
        username="plainuser",
        email="plain@example.com",
        password="pass12345",
    )


@pytest.fixture
def breeder_user(db):
    return get_user_model().objects.create_user(
        username="breederuser",
        email="breeder@example.com",
        password="pass12345",
        role="breeder",
    )


@pytest.fixture
def breeder(db, breeder_user):
    return Breeder.objects.create(
        user=breeder_user,
        name="Fixture cattery",
        country_code="UA",
        city="Kyiv",
        phone="000",
    )


@pytest.fixture
def staff_user(db):
    return get_user_model().objects.create_user(
        username="staffuser",
        email="staff@example.com",
        password="pass12345",
        is_staff=True,
    )
