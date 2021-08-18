from django.urls import path
from neuronsimulator import views

urlpatterns = [
    path("", views.home, name="home"),
    path("list_input_params", views.list_input_params, name="list_input_params"),
]
