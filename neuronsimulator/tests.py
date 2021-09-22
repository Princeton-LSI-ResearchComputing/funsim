from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from neuronsimulator.forms import NeuronInputParamForm
from neuronsimulator.models import Neuron


class NeuronTests(TestCase):
    def setUp(self):
        Neuron.objects.create(name="ADAL")

    def test_neuron_name(self):
        """Neuron lookup by name"""
        ADAL = Neuron.objects.get(name="ADAL")
        self.assertEqual(ADAL.name, "ADAL")


class ViewTests(TestCase):
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

    def test_plot_neural_responses_view(self):
        """
        Test the plot_neural_responses page returns 200
        """
        response = self.client.get(reverse("plot_neural_responses"))
        self.assertEqual(response.status_code, 200)

    def valid_data_set(self):
        # a set of values for valid NeuronInputParamForm
        valid_data_set = {
            "stim_neu_id": "ADAL",
            "resp_neu_ids": "AVAR,ASEL,AWAL",
            "nt": 1000,
            "t_max": 100,
            "stim_type": "rectangular",
            "dur": 2.0,
        }
        return valid_data_set

    def test_input_form_valid(self):
        valid_data_set = self.valid_data_set()
        form = NeuronInputParamForm(data=valid_data_set)
        self.assertTrue(form.is_valid())
        params = form.cleaned_data
        self.assertEqual(len(params), 6)

    def test_input_form_invalid(self):
        """
        check if error(s) raised for invalid form input
        """
        # copy set of valid input values, and then update a value to make form invalid
        valid_data_set = self.valid_data_set()

        # case 1: invalid stim_neu_id would raise an error for this form field
        invalid_data_set1 = valid_data_set.copy()
        invalid_data_set1["stim_neu_id"] = "dummy"
        form = NeuronInputParamForm(data=invalid_data_set1)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors["stim_neu_id"] is not None)

        # case 2: invalid resp_neu_ids would raise an error for this form field
        invalid_data_set2 = valid_data_set.copy()
        invalid_data_set2["resp_neu_ids"] = "dummy, ASEL,AWAL"
        form = NeuronInputParamForm(data=invalid_data_set2)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors["resp_neu_ids"] is not None)

        # case 3: assigning ADAL to both stim_neu_id and resp_neu_ids would raise a form non-field error
        # the key for non-field errors in error dictionary is  "__all__"
        invalid_data_set3 = valid_data_set.copy()
        invalid_data_set3["resp_neu_ids"] = "ADAL,ASEL,AWAL"
        form = NeuronInputParamForm(data=invalid_data_set3)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors["__all__"] is not None)

        # case 4: t_max< dur would raise a form non-field error
        invalid_data_set4 = valid_data_set.copy()
        invalid_data_set4["t_max"] = 1.0
        form = NeuronInputParamForm(data=invalid_data_set4)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors["__all__"] is not None)

    def test_plot_neural_responses_post_success(self):

        # if form is valid after post, 6 items are returned for params
        self.ALL_PARAMS_COUNT = 6

        valid_data_set = self.valid_data_set()
        form = NeuronInputParamForm(data=valid_data_set)
        self.assertTrue(form.is_valid())

        response = self.client.post(
            reverse("plot_neural_responses"), data=valid_data_set
        )
        # response context if form post is valid
        self.assertIsNotNone(response.context["form"])
        self.assertIsNotNone(response.context["plot_div"])
        self.assertEqual(len(response.context["neurons"]), self.ALL_NEURONS_COUNT)
        self.assertEqual(len(response.context["params"]), self.ALL_PARAMS_COUNT)
