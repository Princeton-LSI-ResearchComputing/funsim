from django.urls import path
from neuronsimulator import views

urlpatterns = [
    path("", views.home, name="home"),
    path("list_input_params", views.list_input_params, name="list_input_params"),
    path(
        "plot_neural_responses",
        views.plot_neural_responses,
        name="plot_neural_responses",
    ),
]
