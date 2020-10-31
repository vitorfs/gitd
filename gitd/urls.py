from django.urls import path

from gitd.core import views

urlpatterns = [
    path("github/", views.github, name="github"),
]
