from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import Breed, Breeder, Cat


@pytest.fixture
def breeder(db):
    user = get_user_model().objects.create_user(
        username="testbreeder",
        email="breeder@example.com",
        password="pass12345",
    )
    return Breeder.objects.create(
        user=user,
        name="Test cattery",
        country_code="UA",
        city="Kyiv",
        phone="000",
    )


@pytest.fixture
def breed(db):
    return Breed.objects.create(name="Test breed")


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def make_cat(db):
    def _make_cat(breed, breeder, name, sex, birth_date, mother=None, father=None,
                  status=Cat.Status.AVAILABLE):
        return Cat.objects.create(
            name=name,
            sex=sex,
            breed=breed,
            breeder=breeder,
            birth_date=birth_date,
            price=100,
            photo_url="https://example.com/cat.jpg",
            mother=mother,
            father=father,
            status=status,
        )

    return _make_cat


@pytest.fixture
def cat_payload():
    def _cat_payload(breed, breeder, **extra):
        payload = {
            "name": "Kitten",
            "sex": Cat.Sex.FEMALE,
            "breed_id": breed.pk,
            "breeder_id": breeder.pk,
            "birth_date": date(2024, 1, 1),
            "price": 100,
            "photo_url": "https://example.com/cat.jpg",
        }
        payload.update(extra)
        return payload

    return _cat_payload
