from django.shortcuts import render
from neuronsimulator.forms import ParamForm
from neuronsimulator.models import Neuron


def home(request):
    return render(request, "home.html")


def list_input_params(request):

    context = {}
    params = {}

    # all neurons
    neurons = Neuron.objects.all()

    # form
    my_form = ParamForm()
    if request.method == "POST":
        my_form = ParamForm(request.POST)
        # print(request.POST)
        if my_form.is_valid():
            stim_neuron = my_form.cleaned_data["stim_neuron"]
            resp_neurons = my_form.cleaned_data["resp_neurons"]
            nt = my_form.cleaned_data["nt"]
            dt = my_form.cleaned_data["dt"]
            stim_type = my_form.cleaned_data["stim_type"]
            dur = my_form.cleaned_data["dur"]

            # TODO: will add code for validations
            params["stim_neuron"] = stim_neuron
            params["resp_neurons"] = resp_neurons
            params["nt"] = nt
            params["dt"] = dt
            params["stim_type"] = stim_type
            params["dur"] = dur
        else:
            my_form = ParamForm()

    context = {"neurons": neurons, "form": my_form, "params": params}
    return render(request, "neuronsimulator/list_input_params.html", context)
