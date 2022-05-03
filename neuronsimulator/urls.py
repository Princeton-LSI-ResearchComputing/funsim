from django.urls import path
from neuronsimulator import views

urlpatterns = [
    path("", views.home, name="home"),
    path("load_neurons/", views.load_neurons, name="load_neurons"),
]
