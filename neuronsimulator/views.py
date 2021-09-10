import os

import numpy as np
import plotly.graph_objects as go
import wormfunconn as wfc
from django.conf import settings
from django.shortcuts import render
from neuronsimulator.forms import NeuronInputParamForm, ParamForm
from neuronsimulator.models import Neuron
from plotly.offline import plot


def home(request):
    return render(request, "home.html")


def plot_neural_responses(request):
    context = {}
    params = {}

    # all neurons
    neurons = Neuron.objects.all()

    # form
    my_form = NeuronInputParamForm(request.POST or None)

    # context
    context = {"neurons": neurons, "form": my_form}

    if my_form.is_valid():
        params = my_form.cleaned_data
        # get input parameters for calling wormfunconn
        stim_neu_id = params["stim_neu_id"]
        resp_neu_ids = params["resp_neu_ids"]
        resp_neu_ids = resp_neu_ids.split(",")
        nt = int(params["nt"])
        t_max = float(params["t_max"])
        stim_type = params["stim_type"]
        dur = float(params["dur"])

        # print("stim_neu_id", stim_neu_id)
        # print("resp_neu_ids", resp_neu_ids)

        # Get atlas folder and file name
        folder = os.path.join(settings.MEDIA_ROOT, "atlas/")
        # use mock file for now, need get the file from the lab
        fname = "mock.pickle"

        # Create FunctionalAtlas instance from file
        if os.path.isfile(os.path.join(folder, fname)):
            funatlas = wfc.FunctionalAtlas.from_file(folder, fname)
        else:
            raise FileNotFoundError("Input Atlas file was not found")

        # calculate dt from t_max and nt
        dt = t_max / nt

        # Get stimulus
        try:
            stim = funatlas.get_standard_stimulus(
                nt, dt=dt, stim_type=stim_type, duration=dur
            )
        except Exception as e:
            raise ValueError("Got error with get_standard_stimulus:", e)

        # print("The size of stim ndarray is:", stim.size)

        # Get responses
        try:
            resp = funatlas.get_responses(
                stim, dt, stim_neu_id, resp_neu_ids=resp_neu_ids
            )
        except Exception as e:
            raise ValueError("Got error with getting output from get_responses", e)

        # print("The size of resp ndarray is :",resp.size)

        # convert and verify values for plotting neural responses using plotly
        # ref: https://plotly.com/python/line-charts/#line-plot-with-goscatter
        # ref: https://albertrtk.github.io/2021/01/24/Graph-on-a-web-page-with-Plotly-and-Django.html
        total_resp_neurons = len(resp_neu_ids)
        total_resp_data_set = resp.T.shape[1]
        # print("total_resp_neurons:", total_resp_neurons)
        # print("total_resp_data_set:", total_resp_data_set)
        if total_resp_data_set != total_resp_neurons:
            raise ValueError(
                "Total number mismatch: neural response datasets vs. response neurons"
            )

        # transposed array for response datasets
        y_data_set = resp.T
        x_data = np.arange(y_data_set.shape[0])

        graphs = []
        for i in range(total_resp_neurons):
            # print(resp_neu_ids[i])
            y_data = y_data_set[..., i]
            # adding scatter plot of each set of y_data vs. x_data
            graphs.append(
                go.Scatter(x=x_data, y=y_data, mode="lines", name=resp_neu_ids[i])
            )

        # layout of the figure.
        layout = {
            "title": "Plot: Neural Responses to Stimulus",
            "xaxis_title": "Time Point",
            "yaxis_title": "Neural Response",
            "height": 480,
            "width": 640,
        }

        # Getting HTML needed to render the plot.
        plot_div = plot({"data": graphs, "layout": layout}, output_type="div")

        context = {
            "neurons": neurons,
            "form": my_form,
            "params": params,
            "plot_div": plot_div,
        }

    return render(request, "neuronsimulator/plot_neural_responses.html", context)


# keep list_input_params for now for comparing NeuronInputParamForm with ParamForm
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
