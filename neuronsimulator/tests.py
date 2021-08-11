from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from neuronsimulator.models import Neuron


class HomeViewTests(TestCase):
    """
    Tests for home page view
    """

    def test_home_view(self):
        """
        Test that home page returns 200
        """
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)


class NeuronTests(TestCase):
    def setUp(self):
        Neuron.objects.create(name="ADAL")

    def test_neuron_name(self):
        """Neuron lookup by name"""
        ADAL = Neuron.objects.get(name="ADAL")
        self.assertEqual(ADAL.name, "ADAL")


class DataLoadingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command(
            "load_neurons", "neuronsimulator/example_data/worm_neuron_list.tsv"
        )
        cls.ALL_NEURONS_COUNT = 300

    def test_neurons_loaded(self):
        self.assertEqual(Neuron.objects.all().count(), self.ALL_NEURONS_COUNT)
