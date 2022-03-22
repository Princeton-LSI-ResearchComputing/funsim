from django.urls import path
from neuronsimulator import views

urlpatterns = [
    path("", views.home, name="home"),
]
