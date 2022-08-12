from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from neuronsimulator.forms import ParamForm
from neuronsimulator.utils import WormfunconnToPlot as wfc2plot


def home(request):

    context = {}
    form_init_dict = {}
    form_params = {}
    plot_div = {}
    resp_msg = ""
    url_for_plot = ""
    code_snippet = ""
    app_error_dict = {}
    # form_opt_field_dict = {}
    form_opt_field_init_dict = {}

    # get initial values for all form fields
    my_form = ParamForm()
    for k in my_form.fields.keys():
        form_init_dict[k] = my_form[k].initial

    # get initial values and associated stim_type for optional form fields
    form_opt_field_dict = my_form.form_opt_field_dict
    for k, v in form_opt_field_dict.items():
        v2 = {k1: v1 for k1, v1 in v.items() if k1 in ["stim_type", "default"]}
        form_opt_field_init_dict[k] = v2

    # get the list of names for optional fields
    opt_field_names = list(form_opt_field_dict.keys())

    # get form input from request
    if request.method == "POST":
        my_form = ParamForm(request.POST)
    elif request.method == "GET":
        input_params_dict = dict(request.GET)
        # value in list type, convert to string except for resp_neu_ids
        for key, value in input_params_dict.items():
            if key != "resp_neu_ids" and value != ["None"]:
                input_params_dict.update({key: str(value[0])})
            elif value == ["None"]:
                input_params_dict[key] = None
        # merge to get all form fields, input_params_dict have priority in terms of values
        form_data_dict = {**form_init_dict, **input_params_dict}
        my_form = ParamForm(form_data_dict)

    # get form error dict
    form_errors = my_form.errors.as_data

    # get form valid input values
    form_params = my_form.cleaned_data

    if my_form.is_valid():
        # get all output for neural response plot, and write error(s) to app_error_dict
        out = wfc2plot().get_all_output_for_plot(form_params)
        plot_div = out.plot_div
        resp_msg = out.resp_msg
        code_snippet = out.code_snippet
        app_error_dict = out.app_error_dict

        # get url for plot
        url_for_plot = (
            request.build_absolute_uri("/")[:-1]
            + reverse("home")
            + "?"
            + out.url_query_string
        )

        # add all output to context
        context = {
            "form": my_form,
            "form_opt_field_init_dict": form_opt_field_init_dict,
            "opt_field_names": opt_field_names,
            "form_errors": form_errors,
            "app_error_dict": app_error_dict,
            "resp_msg": resp_msg,
            "plot_div": plot_div,
            "url_for_plot": url_for_plot,
            "code_snippet": code_snippet,
        }
    else:
        # for invalid form, render valid form values in addition to form error(s)
        my_form = ParamForm(form_params)
        context = {
            "form": my_form,
            "form_opt_field_init_dict": form_opt_field_init_dict,
            "opt_field_names": opt_field_names,
            "form_errors": form_errors,
        }

    return render(request, "home.html", context)


def load_neurons(request):
    strain_type = request.GET.get("strain_type")
    neuron_ids, app_error_dict = wfc2plot().get_neuron_ids(strain_type)
    response_data = {"neurons": neuron_ids}
    return JsonResponse(response_data)
