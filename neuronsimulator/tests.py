from urllib.parse import parse_qs, urlparse

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from neuronsimulator.forms import ParamForm
from neuronsimulator.models import Neuron
from neuronsimulator.utils import WormfunconnToPlot as wfc2plot


class NeuronTests(TestCase):
    def setUp(self):
        Neuron.objects.create(name="ADAL")

    def test_neuron_name(self):
        """Neuron lookup by name"""
        ADAL = Neuron.objects.get(name="ADAL")
        self.assertEqual(ADAL.name, "ADAL")


class ViewTests(TestCase):
    """
    test views as well as related form, and methods in utils
    """

    @classmethod
    def setUpTestData(cls):
        call_command(
            "load_neurons", "neuronsimulator/example_data/worm_neuron_list.tsv"
        )
        cls.ALL_NEURONS_COUNT = 300

    def test_neurons_loaded(self):
        self.assertEqual(Neuron.objects.all().count(), self.ALL_NEURONS_COUNT)

    def test_home_view(self):
        """
        Test the home page returns 200
        """
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def valid_data_set(self):
        # a set of values for form "ParamForm", which can generate response plots for both wild-type and unc-31
        valid_data_set = {
            "stim_type": "rectangular",
            "stim_neu_id": "FLPL",
            "resp_neu_ids": ["FLPL", "I4", "I6"],
            "nt": 1000,
            "t_max": 100,
            "duration": 1.0,
            "frequency": 0.1,
            "phi0": "0.0",
            "tau1": "1.0",
            "tau2": "0.8",
            "top_n": None,
            "strain_type": "wild-type",
        }
        return valid_data_set

    def test_input_form_valid(self):
        valid_data_set = self.valid_data_set()
        form = ParamForm(data=valid_data_set)
        self.assertTrue(form.is_valid())
        params = form.cleaned_data
        self.assertEqual(len(params), 12)

    def test_input_form_invalid(self):
        """
        check if error(s) raised for invalid form input
        """
        # copy set of valid input values, and then update a value to make form invalid
        valid_data_set = self.valid_data_set()

        # case 1: set duration to None
        invalid_data_set1 = valid_data_set.copy()
        invalid_data_set1["duration"] = None
        form1 = ParamForm(data=invalid_data_set1)
        self.assertFalse(form1.is_valid())
        self.assertTrue(form1.errors["duration"] is not None)

        # case 2: invalid strain_type
        invalid_data_set2 = valid_data_set.copy()
        invalid_data_set2["strain_type"] = "dummy"
        form2 = ParamForm(data=invalid_data_set2)
        self.assertFalse(form2.is_valid())
        self.assertTrue(form2.errors["strain_type"] is not None)

        # case 3: invalid stim_type
        invalid_data_set3 = valid_data_set.copy()
        invalid_data_set3["stim_type"] = "dummy"
        form3 = ParamForm(data=invalid_data_set3)
        self.assertFalse(form3.is_valid())
        self.assertTrue(form3.errors["stim_type"] is not None)

    def test_reqd_params_keys(self):
        valid_data_set = self.valid_data_set()
        reqd_params_dict, app_error_dict = wfc2plot().get_reqd_params_dict(
            valid_data_set
        )
        reqd_params_keys = reqd_params_dict.keys()
        expt_keys_for_rectangular_type = wfc2plot().get_reqd_params_keys("rectangular")
        self.assertEqual(len(reqd_params_keys), len(expt_keys_for_rectangular_type))
        self.assertEqual(any(reqd_params_keys), any(expt_keys_for_rectangular_type))

    def test_resp_labels(self):
        valid_data_set = self.valid_data_set()

        # case 1: test wild-type
        valid_data_set1 = valid_data_set.copy()
        reqd_params_dict1, app_error_dict1 = wfc2plot().get_reqd_params_dict(
            valid_data_set1
        )
        (
            resp1,
            labels_1,
            confidences,
            msg,
            app_error_dict,
        ) = wfc2plot().get_resp_in_ndarray(valid_data_set1)
        self.assertEqual(resp1.shape[0], 3)
        self.assertEqual(resp1.shape[1], 1000)
        self.assertEqual(len(labels_1), 3)
        self.assertEqual(app_error_dict1, {})

        # case 2: test unc-31
        valid_data_set2 = valid_data_set.copy()
        valid_data_set2["strain_type"] = "unc-31"
        reqd_params_dict2, app_error_dict2 = wfc2plot().get_reqd_params_dict(
            valid_data_set2
        )
        (
            resp2,
            labels_2,
            confidences,
            msg,
            app_error_dict,
        ) = wfc2plot().get_resp_in_ndarray(valid_data_set2)
        self.assertEqual(resp2.shape[0], 3)
        self.assertEqual(resp2.shape[1], 1000)
        self.assertEqual(len(labels_2), 3)
        self.assertEqual(app_error_dict2, {})

    def test_get_url_to_params(self):
        valid_data_set = self.valid_data_set()
        reqd_params_dict, app_error_dict = wfc2plot().get_reqd_params_dict(
            valid_data_set
        )
        url_query_string, app_error_dict = wfc2plot().get_url_query_string_for_plot(
            valid_data_set
        )
        url_param_dict = parse_qs(urlparse(url_query_string).path)
        # each value is list type in url_param_dict
        self.assertEqual(
            str(url_param_dict["stim_type"][0]), valid_data_set["stim_type"]
        )
        self.assertEqual(
            str(url_param_dict["stim_neu_id"][0]), valid_data_set["stim_neu_id"]
        )
        self.assertEqual(
            any(url_param_dict["resp_neu_ids"][0]), any(valid_data_set["resp_neu_ids"])
        )
        self.assertEqual(int(url_param_dict["nt"][0]), valid_data_set["nt"])
        self.assertEqual(float(url_param_dict["t_max"][0]), valid_data_set["t_max"])
        self.assertEqual(
            float(url_param_dict["duration"][0]), valid_data_set["duration"]
        )

    def test_get_stim_type_choice(self):
        stim_type_choice = wfc2plot().get_stim_type_choice()
        sel_choice = ("delta", "delta")
        stim_type_choice = wfc2plot().get_stim_type_choice()
        self.assertTrue(sel_choice in stim_type_choice)

    def test_get_form_opt_field_dict(self):
        form_opt_field_dict = wfc2plot().get_form_opt_field_dict()
        self.assertEqual(form_opt_field_dict["duration"]["stim_type"], "rectangular")
        self.assertEqual(form_opt_field_dict["duration"]["default"], 1.0)
