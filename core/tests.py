from datetime import date, timedelta

import pytest
from django.utils import timezone

from core.models import Cat
from core.serializers import CatSerializer

pytestmark = pytest.mark.django_db


def test_serializer_rejects_male_mother(breed, breeder, make_cat, cat_payload):
    mother = make_cat(breed, breeder, "Tom", Cat.Sex.MALE, date(2020, 1, 1))
    serializer = CatSerializer(
        data=cat_payload(breed, breeder, mother_id=mother.pk))

    assert not serializer.is_valid()
    assert "mother" in serializer.errors


def test_serializer_accepts_valid_parents(breed, breeder, make_cat, cat_payload):
    mother = make_cat(breed, breeder, "Mimi", Cat.Sex.FEMALE, date(2020, 1, 1))
    father = make_cat(breed, breeder, "Leo", Cat.Sex.MALE, date(2020, 2, 1))
    serializer = CatSerializer(data=cat_payload(
        breed, breeder, mother_id=mother.pk, father_id=father.pk))

    assert serializer.is_valid(), serializer.errors
    cat = serializer.save()
    assert cat.mother == mother
    assert cat.father == father


def test_serializer_rejects_self_as_parent(breed, breeder, make_cat):
    cat = make_cat(breed, breeder, "Self", Cat.Sex.FEMALE, date(2020, 1, 1))
    serializer = CatSerializer(cat, data={"mother_id": cat.pk}, partial=True)

    assert not serializer.is_valid()
    assert "detail" in serializer.errors


def test_serializer_rejects_future_birth_date(breed, breeder, cat_payload):
    future = timezone.localdate() + timedelta(days=1)
    serializer = CatSerializer(
        data=cat_payload(breed, breeder, birth_date=future))

    assert not serializer.is_valid()
    assert "birth_date" in serializer.errors


def test_pedigree_endpoint(api, breed, breeder, make_cat):
    grandmother = make_cat(
        breed, breeder, "Grandma", Cat.Sex.FEMALE, date(2018, 1, 1))
    mother = make_cat(
        breed, breeder, "Mama", Cat.Sex.FEMALE, date(2020, 1, 1),
        mother=grandmother)
    child = make_cat(
        breed, breeder, "Baby", Cat.Sex.FEMALE, date(2024, 1, 1), mother=mother)

    response = api.get(f"/api/cats/{child.pk}/pedigree/")

    assert response.status_code == 200
    assert response.data["name"] == "Baby"
    assert response.data["mother"]["name"] == "Mama"
    assert response.data["mother"]["mother"]["name"] == "Grandma"


def test_alumni_endpoint(api, breed, breeder, make_cat):
    make_cat(breed, breeder, "Available", Cat.Sex.FEMALE, date(2024, 1, 1))
    sold = make_cat(
        breed, breeder, "Sold", Cat.Sex.MALE, date(2023, 1, 1),
        status=Cat.Status.SOLD)

    response = api.get(f"/api/breeders/{breeder.pk}/alumni/")

    assert response.status_code == 200
    assert [cat["id"] for cat in response.data] == [sold.pk]
