import logging

from django.contrib.auth import get_user_model
from django.utils import timezone
from django_countries.serializer_fields import CountryField
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Breed, Breeder, Cat

logger = logging.getLogger(__name__)
User = get_user_model()

class BreedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Breed
        fields = ["id", "name"]


class BreederShortSerializer(serializers.ModelSerializer):
    country_code = CountryField(country_dict=True)
    class Meta:
        model = Breeder
        fields = ["id", "name", "country_code", "city"]

class CatQuerySerializer(serializers.Serializer):
    search = serializers.CharField(required=False)
    breed_id = serializers.IntegerField(required=False)
    breeder_id = serializers.IntegerField(required=False)
    country_code = serializers.CharField(required=False, max_length=2)
    min_price = serializers.IntegerField(required=False, min_value=0)
    max_price = serializers.IntegerField(required=False, min_value=0)
    status = serializers.ChoiceField(choices=["available", "reserved", "sold"], required=False)
    sort_by = serializers.ChoiceField(choices=["price", "created_at"], default="created_at")
    order = serializers.ChoiceField(choices=["asc", "desc"], default="desc")
    page = serializers.IntegerField(min_value=1, default=1)
    limit = serializers.IntegerField(min_value=1, max_value=100, default=10)

    def validate(self, attrs):
        if "min_price" in attrs and "max_price" in attrs and attrs["min_price"] > attrs["max_price"]:
            logger.warning("Invalid range of price: min_price=%s, max_price=%s", attrs["min_price"], attrs["max_price"])
            raise serializers.ValidationError("min_price cannot be greater than max_price")
        return attrs

class CatParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cat
        fields = ["id", "name", "sex", "photo_url", "status"]


class CatSerializer(serializers.ModelSerializer):
    breed = BreedSerializer(read_only=True)
    breeder = BreederShortSerializer(read_only=True)
    mother = CatParentSerializer(read_only=True)
    father = CatParentSerializer(read_only=True)
    breed_id = serializers.PrimaryKeyRelatedField(
        queryset=Breed.objects.all(), source="breed", write_only=True)
    breeder_id = serializers.PrimaryKeyRelatedField(
        queryset=Breeder.objects.all(), source="breeder", write_only=True)
    mother_id = serializers.PrimaryKeyRelatedField(
        queryset=Cat.objects.all(), source="mother", allow_null=True, required=False)
    father_id = serializers.PrimaryKeyRelatedField(
        queryset=Cat.objects.all(), source="father", allow_null=True, required=False)
    class Meta:
        model = Cat
        fields = ["id", "name", "sex", "breed", "breeder", "breed_id", "breeder_id",
              "mother", "father", "mother_id", "father_id",
              "birth_date", "price", "description", "status", "photo_url", "created_at"]
        read_only_fields = ["created_at"]

    def validate_birth_date(self, value):
        if value > timezone.localdate():
            logger.warning("Birth date can't be in the future: birth_date=%s", value)
            raise serializers.ValidationError("Birth date cannot be in the future")
        return value

    def validate(self, attrs):
        cat = self.instance
        mother = attrs.get("mother", cat.mother if cat else None)
        father = attrs.get("father", cat.father if cat else None)
        birth_date = attrs.get("birth_date", cat.birth_date if cat else None)

        if cat and cat.pk in (getattr(mother, "pk", None), getattr(father, "pk", None)):
            raise serializers.ValidationError({"detail": "Cat can't be its own parent."})

        if mother and mother.sex != Cat.Sex.FEMALE:
            raise serializers.ValidationError({"mother": "Mother must be female."})
        if father and father.sex != Cat.Sex.MALE:
            raise serializers.ValidationError({"father": "Father must be male."})

        if birth_date:
            if mother and mother.birth_date >= birth_date:
                raise serializers.ValidationError({"mother": "Mother must be born before the cat."})
            if father and father.birth_date >= birth_date:
                raise serializers.ValidationError({"father": "Father must be born before the cat."})

        return attrs


class CatShortSerializer(serializers.ModelSerializer):
    breed = BreedSerializer(read_only=True)

    class Meta:
        model = Cat
        fields = ["id", "name", "sex", "breed", "price", "status", "photo_url"]

class CatListResponseSerializer(serializers.Serializer):
    items = CatShortSerializer(many=True)
    page = serializers.IntegerField()
    limit = serializers.IntegerField()
    total = serializers.IntegerField()

class BreederSerializer(serializers.ModelSerializer):
    cats = CatShortSerializer(many=True, read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", write_only=True,
        validators=[UniqueValidator(
            queryset=Breeder.objects.all(),
            message="This user already has a breeder profile",
        )],
    )
    country_code = CountryField(country_dict=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    class Meta:
        model = Breeder
        fields = ["id", "user_id", "name", "country_code", "city", "phone", "email", "description", "cats"]
