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


def _tree_ids(node):
    ids = [node["id"]]
    for child in node["children"]:
        ids.extend(_tree_ids(child))
    return ids


def test_breeder_pedigrees_two_families(api, breed, breeder, make_cat):
    mother = make_cat(
        breed, breeder, "Maya", Cat.Sex.FEMALE, date(2020, 1, 1))
    make_cat(
        breed, breeder, "Luna", Cat.Sex.FEMALE, date(2024, 1, 1),
        mother=mother)
    father = make_cat(
        breed, breeder, "Tom", Cat.Sex.MALE, date(2020, 1, 1))
    make_cat(
        breed, breeder, "Mars", Cat.Sex.MALE, date(2024, 1, 1),
        father=father)

    response = api.get(f"/api/breeders/{breeder.pk}/pedigrees/")

    assert response.status_code == 200
    families = response.data["families"]
    assert len(families) == 2
    assert [
        [root["name"] for root in family["roots"]] for family in families
    ] == [["Maya"], ["Tom"]]


def test_breeder_pedigrees_shared_parents(api, breed, breeder, make_cat):
    mother = make_cat(
        breed, breeder, "Mimi", Cat.Sex.FEMALE, date(2020, 1, 1))
    father = make_cat(
        breed, breeder, "Leo", Cat.Sex.MALE, date(2020, 1, 1))
    make_cat(
        breed, breeder, "Kit", Cat.Sex.FEMALE, date(2024, 1, 1),
        mother=mother, father=father)
    make_cat(
        breed, breeder, "Pal", Cat.Sex.MALE, date(2024, 1, 1),
        mother=mother, father=father)

    response = api.get(f"/api/breeders/{breeder.pk}/pedigrees/")

    assert response.status_code == 200
    families = response.data["families"]
    assert len(families) == 1
    family = families[0]
    assert [root["id"] for root in family["roots"]] == [mother.pk, father.pk]
    ids = _tree_ids(family["tree"])
    assert len(ids) == len(set(ids))
    assert mother.pk in ids
    assert father.pk not in ids
    assert all(
        child["father"]["id"] == father.pk
        for child in family["tree"]["children"]
    )


def test_breeder_pedigrees_include_sold(api, breed, breeder, make_cat):
    sold = make_cat(
        breed, breeder, "Sold", Cat.Sex.MALE, date(2023, 1, 1),
        status=Cat.Status.SOLD)

    response = api.get(f"/api/breeders/{breeder.pk}/pedigrees/")

    assert response.status_code == 200
    family = response.data["families"][0]
    assert family["cats_count"] == 1
    assert _tree_ids(family["tree"]) == [sold.pk]


def test_breeder_pedigrees_include_external_ancestor(
    api, breed, breeder, other_breeder, make_cat
):
    grandmother = make_cat(
        breed, other_breeder, "Grandma", Cat.Sex.FEMALE, date(2018, 1, 1))
    child = make_cat(
        breed, breeder, "Baby", Cat.Sex.FEMALE, date(2024, 1, 1),
        mother=grandmother)

    response = api.get(f"/api/breeders/{breeder.pk}/pedigrees/")

    assert response.status_code == 200
    family = response.data["families"][0]
    assert [root["id"] for root in family["roots"]] == [grandmother.pk]
    assert family["tree"]["id"] == grandmother.pk
    assert family["tree"]["children"][0]["id"] == child.pk


def test_breeder_pedigrees_unknown_breeder(api):
    response = api.get("/api/breeders/999999/pedigrees/")

    assert response.status_code == 404


def test_breeder_pedigrees_survives_cycle(api, breed, breeder, make_cat):
    first = make_cat(
        breed, breeder, "A", Cat.Sex.FEMALE, date(2020, 1, 1))
    second = make_cat(
        breed, breeder, "B", Cat.Sex.FEMALE, date(2021, 1, 1),
        mother=first)
    Cat.objects.filter(pk=first.pk).update(mother_id=second.pk)

    response = api.get(f"/api/breeders/{breeder.pk}/pedigrees/")

    assert response.status_code == 200
    assert len(response.data["families"]) == 1

