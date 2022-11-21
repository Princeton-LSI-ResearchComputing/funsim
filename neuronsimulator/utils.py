import os
import re
from collections import namedtuple
from urllib.parse import urlencode

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from django.conf import settings
from plotly.offline import plot
from wormfunconn import FunctionalAtlas


class WormfunconnToPlot:
    """
    contains a set of methods for calling wormfuconn package to parse parameters and generate
    url and plot(s) for displaying neural responses on the webpage
    capture error in each step and then log it to a dictionary (app_error_dict) in output
    """

    @classmethod
    def get_stim_type_list(cls):
        """
        get the list of stim_types defined by wormfunconn package
        """
        stim_type_list = ["realistic", "rectangular", "delta", "sinusoidal"]
        return stim_type_list

    @classmethod
    def get_stim_type_choice(cls):
        """
        get stim type choices in the format required by Django form ChoiceField
        """
        stim_type_list = cls.get_stim_type_list()
        stim_type_choices = []
        for stim_type in stim_type_list:
            stim_type_choices.append((stim_type, stim_type))
        return stim_type_choices

    @classmethod
    def get_form_opt_field_dict(cls):
        """
        The method is used to get all attrs. of optional fields for the web form.
        The field names are defined as kwargs in FunctionalAtlas.get_standard_stim_kwargs(stim_type)
        method.
        example:
        stim_type=="sinusoidal":
        kwargs = [{"name": "frequency", "type": "float", "default": 0.25,
                        "label": "Frequency (Hz)", "range": [0.,0.25]},
                       {"name": "phi0", "type": "float", "default": 0.0,
                        "label": "Phase", "range": [0.,6.28]}]
        """
        stim_type_list = cls.get_stim_type_list()
        stim_kwarg_dict = {}
        form_opt_field_dict = {}
        for stim_type in stim_type_list:
            stim_kwarg_dict[stim_type] = FunctionalAtlas.get_standard_stim_kwargs(
                stim_type
            )

        for stim_type, field_kwargs in stim_kwarg_dict.items():
            for field_kwarg in field_kwargs:
                # form_opt_field_dict: key is field_name; value is a list of field attrs
                field_name = field_kwarg["name"]
                field_attrs = field_kwarg
                form_opt_field_dict[field_name] = field_attrs
                # add more items to field_attrs which are used for rendering web form fields
                field_attrs["stim_type"] = stim_type
                label = field_kwarg["label"]
                default_val = str(field_kwarg["default"])
                range_val = str(field_kwarg["range"])
                min_val = field_kwarg["range"][0]
                max_val = field_kwarg["range"][1]
                field_attrs[
                    "help_text"
                ] = f"Values for {label}: default={default_val}; range: {range_val}"
                field_attrs["min_val"] = min_val
                field_attrs["max_val"] = max_val
                field_attrs["step"] = 1
                if max_val is not None:
                    if round(max_val) <= 10:
                        field_attrs["step"] = 0.01
                    elif round(max_val) > 10 and round(max_val) <= 100:
                        field_attrs["step"] = 0.1

        return form_opt_field_dict

    def get_funatlas(self, strain_type):
        self.strain_type = strain_type
        # Get atlas folder and file name
        folder = os.path.join(settings.MEDIA_ROOT, "atlas/")
        # TODO: need to change the file names when the dtaasets are ready
        # use mock file based on strain type
        # the file names may change later
        if strain_type == "wild-type":
            fname = "wild-type.pickle"
        elif strain_type == "unc-31":
            fname = "unc-31.pickle"
        else:
            fname = "wild-type.pickle"

        app_error_dict = {}

        # Create FunctionalAtlas instance from file
        if os.path.isfile(os.path.join(folder, fname)):
            funatlas = FunctionalAtlas.from_file(folder, fname)
        else:
            funatlas = None
            app_error_dict["atlas_file_error"] = "Input Atlas file was not found"
        return funatlas, app_error_dict

    @staticmethod
    def t_max_to_dt(t_max, nt):
        dt = t_max / nt
        return dt

    @staticmethod
    def dt_to_t_max(dt, nt):
        t_max = dt * nt
        return t_max

    def get_neuron_ids(self, strain_type):
        self.strain_type = strain_type
        funatlas, app_error_dict = self.get_funatlas(strain_type)
        if funatlas:
            try:
                neuron_id_list = funatlas.get_neuron_ids(stim=True)
            except Exception as e:
                neuron_id_list = []
                app_error_dict["get_neuron_ids_error"] = e
        return neuron_id_list, app_error_dict

    @staticmethod
    def resp_labels_to_dict(labels):
        """
        The labels returned from get_responses is np.array
        the label format: resp_neu_ids (rank)
        e.g.
        array(['AIZR (0)', 'DD6 (1)', 'AINL (2)', 'DVB (3)']
        output:
            convert label to a key/value pair in dictionary: {"resp_neu_id"; rank}
        """
        resp_neu_id_rank_dict = {}
        label_list = labels.tolist()
        for item in label_list:
            m = re.match(r"(\w+) (\()(\d+)(\))", item)
            resp_neu_id_rank_dict[m[1]] = int(m[3])
        return resp_neu_id_rank_dict

    @staticmethod
    def get_reqd_params_keys(input_stim_type):
        """
        For a stim_type, get kwargs required by FunctionalAtlas.get_standard_stimulus method
        """
        # shared kwargs for all stim_types
        reqd_params_keys = [
            "strain_type",
            "stim_type",
            "stim_neu_id",
            "resp_neu_ids",
            "nt",
            "t_max",
            "top_n",
        ]
        # add other keys based on stim_type
        stim_kwargs = FunctionalAtlas.get_standard_stim_kwargs(input_stim_type)
        for i in range(len(stim_kwargs)):
            reqd_params_keys.append(stim_kwargs[i]["name"])
        return reqd_params_keys

    def get_reqd_params_dict(self, params_dict):
        """
        params_dict:
            expect to get from request with POST or GET method
            The form contains parameters for all stim_type, though only display required fields based on stim_type
        output:
            reqd_params_dict: filtered keys/values based on stim_type
            app_error_dict: logged errors
        """
        self.params_dict = params_dict
        # set default values
        reqd_params_dict = {}
        app_error_dict = {}

        # input need to be a dictionary
        if type(params_dict) is dict:
            # verify stim_type
            stim_type = params_dict["stim_type"]
            exp_stim_type_list = ["rectangular", "delta", "sinusoidal", "realistic"]
            if stim_type in exp_stim_type_list:
                reqd_params_keys = self.get_reqd_params_keys(stim_type)
                reqd_params_dict = {key: params_dict[key] for key in reqd_params_keys}
            else:
                app_error_dict[
                    "input_parameter_error"
                ] = f"undefined stim_type:{stim_type}."
        else:
            app_error_dict["input_parameter_error"] = "input is not a dictionary."
        return reqd_params_dict, app_error_dict

    def get_resp_in_ndarray(self, params_dict):
        self.params_dict = params_dict
        app_error_dict = {}
        reqd_params_dict, app_error_dict = self.get_reqd_params_dict(params_dict)
        stim = np.empty(0)

        if reqd_params_dict:
            # get required values for every stim_type first
            strain_type = reqd_params_dict["strain_type"]
            stim_type = reqd_params_dict["stim_type"]
            nt = int(reqd_params_dict["nt"])
            t_max = float(reqd_params_dict["t_max"])
            dt = self.t_max_to_dt(t_max, nt)
            stim_neu_id = reqd_params_dict["stim_neu_id"]
            # resp_neu_ids
            resp_neu_ids = reqd_params_dict["resp_neu_ids"]
            if len(resp_neu_ids) == 0:
                resp_neu_ids = None
            # top_n
            top_n = reqd_params_dict["top_n"]
            if top_n is None or top_n == "None":
                top_n = None
            else:
                top_n = int(top_n)

            if app_error_dict == {}:
                # Create FunctionalAtlas instance from file
                funatlas, app_error_dict = self.get_funatlas(strain_type)

            # call get_standard_stimulus based on stim_type
            if funatlas:
                try:
                    if stim_type == "rectangular":
                        duration = float(reqd_params_dict["duration"])
                        stim = funatlas.get_standard_stimulus(
                            nt, dt=dt, stim_type=stim_type, duration=duration
                        )
                    elif stim_type == "delta":
                        stim = funatlas.get_standard_stimulus(
                            nt, dt=dt, stim_type=stim_type, duration=dt
                        )
                    elif stim_type == "sinusoidal":
                        frequency = float(reqd_params_dict["frequency"])
                        phi0 = float(reqd_params_dict["phi0"])
                        stim = funatlas.get_standard_stimulus(
                            nt,
                            dt=dt,
                            stim_type=stim_type,
                            frequency=frequency,
                            phi0=phi0,
                        )
                    elif stim_type == "realistic":
                        tau1 = float(reqd_params_dict["tau1"])
                        tau2 = float(reqd_params_dict["tau2"])
                        stim = funatlas.get_standard_stimulus(
                            nt, dt=dt, stim_type=stim_type, tau1=tau1, tau2=tau2
                        )
                except Exception as e:
                    stim = np.empty(0)
                    app_error_dict["get_standard_stimulus_error"] = e

        # Get response
        if stim_neu_id is not None and stim_neu_id != "" and stim.size > 0:
            try:
                resp, labels, confidences, msg = funatlas.get_responses(
                    stim,
                    dt,
                    stim_neu_id,
                    resp_neu_ids=resp_neu_ids,
                    threshold=0.0,
                    top_n=top_n,
                )
            except Exception as e:
                app_error_dict["get_responses_error"] = e
                resp = np.empty(0)
                labels = []
                confidences = None
                msg = None
        else:
            resp = np.empty(0)
            labels = []
            confidences = None
            msg = None

        return resp, labels, confidences, msg, app_error_dict

    def get_plot_html_div(self, params_dict):
        """
        convert and verify values for plotting neural responses using plotly
        references:
        https://plotly.com/python/line-charts/#line-plot-with-goscatter
        https://albertrtk.github.io/2021/01/24/Graph-on-a-web-page-with-Plotly-and-Django.html
        https://plotly.com/python-api-reference/generated/plotly.graph_objects.Scatter.html
        https://plotly.com/python/reference/scatter/
        https://plotly.com/python-api-reference/generated/plotly.colors.html
        https://plotly.com/python/hover-text-and-formatting/#selecting-a-hovermode-in-a-figure-created-with-plotlygraphobjects
        https://plotly.com/python/figure-labels/
        """
        self.params_dict = params_dict
        nt = int(params_dict["nt"])
        t_max = float(params_dict["t_max"])
        dt = self.t_max_to_dt(t_max, nt)

        # get response related output
        resp, labels, confidences, msg, app_error_dict = self.get_resp_in_ndarray(
            params_dict
        )
        # default value
        plot_div = None
        resp_msg = None
        if msg is not None and msg != "":
            resp_msg = "Notes:\n" + msg

        # create colormap for n colors
        n_colors = len(labels)
        if n_colors >= 2:
            colors = px.colors.sample_colorscale(
                "rainbow", [n / (n_colors - 1) for n in range(n_colors)]
            )
        else:
            colors = ["rgb(255, 0, 0)"]

        if resp.size > 0:
            stim_neu_id = params_dict["stim_neu_id"]
            # transposed array for response datasets
            y_data_set = resp.T
            x_data = np.arange(nt) * dt
            graphs = []
            for i in range(len(labels)):
                y_data = y_data_set[..., i]
                # adding scatter plot of each set of y_data vs. x_data
                graphs.append(
                    go.Scatter(
                        x=x_data,
                        y=y_data,
                        mode="lines",
                        line=dict(color=colors[i], width=4),
                        opacity=confidences[i],
                        name=labels[i],
                        hovertemplate="(%{x},%{y})",
                    )
                )

            # layout of the figure.
            layout = {
                "title": f"Plot: Neural Responses to Stimulated Neuron ({stim_neu_id})",
                "xaxis_title": "Time (s)",
                "yaxis_title": "Neural Response",
                "legend_title_text": "Responding Neuron (rank)",
                "showlegend": True,
                "height": 800,
                "width": 1200,
            }

            """
            Getting HTML needed to render the plot
            ref: https://github.com/plotly/plotly.py/blob/master/packages/python/plotly/plotly/offline/offline.py
            Notes:
                plotly.offline.plot function has following arguments set to True as default:
                validate (default=True): validate that all of the keys in the figure are valid
                include_plotlyjs (default=True):
                a script tag containing the plotly.js source code (~3MB) is included in the output.
                plot_div should have passed validations if no error raised
            """
            try:
                plot_div = plot({"data": graphs, "layout": layout}, output_type="div")
            except Exception as e:
                app_error_dict["plot_html_data_error"] = e

        return plot_div, resp_msg, app_error_dict

    def get_url_query_string_for_plot(self, params_dict):
        """
        create url from a dictionary for required parameters
        """
        self.reqd_params_dict = params_dict
        reqd_params_dict, app_error_dict = self.get_reqd_params_dict(params_dict)
        if reqd_params_dict:
            """
            filtered_params_dict = {
                k: v for (k, v) in reqd_params_dict.items() if v is not None
            }
            try:
                url_query_string = urlencode(filtered_params_dict, doseq=True)
            """
            try:
                url_query_string = urlencode(reqd_params_dict, doseq=True)
            except Exception as e:
                app_error_dict["plot_url_error"] = e
        else:
            url_query_string = None
        return url_query_string, app_error_dict

    def get_code_snippet_for_plot(self, params_dict):
        """
        call "get_code_snippet" method to get code snippet based on kwargs for a stim_type
        """
        self.params_dict = params_dict
        reqd_params_dict, app_error_dict = self.get_reqd_params_dict(params_dict)
        # get required values for every stim_type first
        # TODO: need to add strain_type later
        # strain_type = reqd_params_dict["strain_type"]
        stim_type = reqd_params_dict["stim_type"]
        stim_neu_id = reqd_params_dict["stim_neu_id"]
        resp_neu_ids = reqd_params_dict["resp_neu_ids"]
        nt = int(reqd_params_dict["nt"])
        t_max = float(reqd_params_dict["t_max"])
        top_n = reqd_params_dict["top_n"]

        dt = self.t_max_to_dt(t_max, nt)

        stim_kwargs = {}
        stim_kwargs_list = FunctionalAtlas.get_standard_stim_kwargs(stim_type)
        for i in range(len(stim_kwargs_list)):
            k = stim_kwargs_list[i]["name"]
            stim_kwargs[k] = float(reqd_params_dict[k])

        # get code snippet
        try:
            code_snippet = FunctionalAtlas.get_code_snippet(
                nt,
                dt,
                stim_type,
                stim_kwargs,
                stim_neu_id,
                resp_neu_ids,
                threshold=0.0,
                top_n=top_n,
                sort_by_amplitude=True,
            )
        except Exception as e:
            app_error_dict["plot_code_snippet_error"] = e
        return code_snippet, app_error_dict

    def get_all_output_for_plot(self, params_dict):
        """
        a wrapper to call several methods to get all output for a neural response plot,
        including plot_div, code_snippet, url_query_string for generating plot with GET method.
        Possible error messages are merged into app_error_dict

        """
        self.params_dict = params_dict
        app_error_dict = {}
        # get required parameters and values first
        reqd_params_dict, app_error_dict1 = self.get_reqd_params_dict(params_dict)
        # get plot_div
        plot_div, resp_msg, app_error_dict2 = self.get_plot_html_div(reqd_params_dict)
        # get url_query_string for the plot
        url_query_string, app_error_dict3 = self.get_url_query_string_for_plot(
            reqd_params_dict
        )
        # get code snippet for the plot
        code_snippet, app_error_dict4 = self.get_code_snippet_for_plot(reqd_params_dict)
        app_error_dict = {
            **app_error_dict1,
            **app_error_dict2,
            **app_error_dict3,
            **app_error_dict4,
        }
        # all output in namedtuple
        AllOutput = namedtuple(
            "AllOutput",
            "plot_div, resp_msg, url_query_string, code_snippet, app_error_dict",
        )
        all_out = AllOutput(
            plot_div, resp_msg, url_query_string, code_snippet, app_error_dict
        )
        return all_out
