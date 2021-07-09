from django.test import TestCase
from django.urls import reverse


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
