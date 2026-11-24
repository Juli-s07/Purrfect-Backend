from django.contrib import admin

from django.contrib import admin
from .models import Cat, Breeder, Breed

@admin.register(Cat)
class CatAdmin(admin.ModelAdmin):
    list_display = ("name", "breed", "breeder", "mother", "father", "price", "status")
    list_filter = ("status", "breed")
    search_fields = ("name",)
    list_editable = ("status",)
    autocomplete_fields = ("mother", "father")
    fieldsets = (
        (None, {"fields": ("name", "sex", "breed", "breeder", "birth_date")}),
        ("Pedigree", {"fields": ("mother", "father")}),
        ("Sale", {"fields": ("price", "status", "photo_url", "description")}),
    )

admin.site.register(Breeder)
admin.site.register(Breed)
