import json
import plotly.graph_objects as go
import wormfunconn as wfc

from django.shortcuts import render
from django.urls import reverse

from neuronsimulator.forms import ParamForm
from neuronsimulator.models import Neuron
from neuronsimulator.utils import WormfunconnToPlot as wfc2plot
from plotly.offline import plot


def home(request):

    context = {}
    form_init_dict = {}
    form_params = {}
    reqd_params_dict = {}
    plot_div = {}
    resp_msg = ""
    url_for_plot = ""
    code_snippet = ""
    app_errors = {}

    # website introduction
    web_intro = wfc.website_text["intro"]

    # all neurons
    neurons = Neuron.objects.all()

    # get form initial values
    my_form = ParamForm()  
    for k in my_form.fields.keys():
        form_init_dict[k] = my_form[k].initial

    # get form input from request
    if request.method == "POST":
        my_form = ParamForm(request.POST)
    elif request.method == "GET":
        input_params_dict = dict(request.GET)
        # value in list type, convert to string except for resp_neu_ids
        for key, value in input_params_dict.items():
            if key != "resp_neu_ids":
                input_params_dict.update({key: str(value[0])})
        # merge to get all form fields, input_params_dict have priority in terms of values
        form_data_dict = {**form_init_dict, **input_params_dict}
        my_form = ParamForm(form_data_dict)

    # get form error dict
    form_errors = my_form.errors.as_data

    # get form valid input values
    form_params = my_form.cleaned_data

    if my_form.is_valid():
        # call methods to get plot related output, and write error(s) to app_error_dict
        # get required parameters and values first
        reqd_params_dict, app_error_dict = wfc2plot().get_reqd_params_dict(form_params)
        # get plot_div
        plot_div, resp_msg, app_error_dict = wfc2plot().get_plot_html_div(
            reqd_params_dict
        )
        # get url for plot
        url_query_string, app_error_dict = wfc2plot().get_url_query_string_for_plot(
            reqd_params_dict
        )
        url_for_plot = (
            request.build_absolute_uri("/")[:-1]
            + reverse("home")
            + "?"
            + url_query_string
        )
        # get code snippet for plot
        code_snippet, app_error_dict = wfc2plot().get_code_snippet_for_plot(
            reqd_params_dict
        )
        # add all output to context
        context = {
            "web_intro": web_intro,
            "form": my_form,
            "form_init_dict": form_init_dict,
            "form_errors": form_errors,
            "app_errors": app_error_dict,
            "resp_msg": resp_msg,
            "plot_div": plot_div,
            "url_for_plot": url_for_plot,
            "code_snippet": code_snippet,
        }
    else:
        # for invalid form, render valid form values in addition to form error(s)
        my_form = ParamForm(form_params)
        context = {
            "web_intro": web_intro,
            "neurons": neurons,
            "form": my_form,
            "form_init_dict": form_init_dict,
            "form_errors": form_errors,
        }
    
    return render(request, "home.html", context)
