from django.urls import path

from gitd.core import views

urlpatterns = [
    path("__gitd__/github/", views.github, name="github"),
]
