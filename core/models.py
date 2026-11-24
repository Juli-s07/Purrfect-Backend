from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

class Breeder(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="breeder")
    name = models.CharField(max_length=150)
    country = models.CharField(max_length=150)
    city = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

class Breed(models.Model):
    name = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

class Cat(models.Model):
    class Sex(models.TextChoices):
        MALE = "male"
        FEMALE = "female"

    class Status(models.TextChoices):
        AVAILABLE = "available"
        RESERVED = "reserved"
        SOLD = "sold"

    name = models.CharField(max_length=100)
    sex = models.CharField(max_length=10, choices=Sex.choices)
    breed = models.ForeignKey(Breed, on_delete=models.PROTECT, related_name="cats")
    breeder = models.ForeignKey(Breeder, on_delete=models.PROTECT, related_name="cats")
    birth_date = models.DateField()
    price = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    photo_url = models.URLField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.AVAILABLE)
    mother = models.ForeignKey( "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children_as_mother",
        limit_choices_to={"sex": "female"},
    )
    father = models.ForeignKey( "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children_as_father",
        limit_choices_to={"sex": "male"},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.pk and self.pk in (self.mother_id, self.father_id):
            raise ValidationError("Cat can't be its own parent.")

        if self.mother:
            if self.mother.sex != self.Sex.FEMALE:
                raise ValidationError({"mother": "Mother must be female."})
            if self.birth_date and self.mother.birth_date >= self.birth_date:
                raise ValidationError({"mother": "Mother must be born before the cat."})

        if self.father:
            if self.father.sex != self.Sex.MALE:
                raise ValidationError({"father": "Father must be male."})
            if self.birth_date and self.father.birth_date >= self.birth_date:
                raise ValidationError({"father": "Father must be born before the cat."})

    def __str__(self):
        return self.name
