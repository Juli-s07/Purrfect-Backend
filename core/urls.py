from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view()),
    path("cats/", views.CatListView.as_view()),
    path("cats/<int:pk>/pedigree/", views.CatPedigreeView.as_view()),
    path("cats/<int:pk>/", views.CatDetailView.as_view()),
    path("breeders/", views.BreederListView.as_view()),
    path("breeders/<int:pk>/alumni/", views.BreederAlumniView.as_view()),
    path("breeders/<int:pk>/", views.BreederDetailView.as_view()),
    path("breeds/", views.BreedListView.as_view()),
    path("breeds/<int:pk>/", views.BreedDetailView.as_view()),
    path("for-buyers/", views.Buyers.as_view()),
    path("for-breeders/", views.Breeders.as_view()),
    path("contacts/", views.Contacts.as_view()),
]
