from csv import DictReader

from django.core.management import BaseCommand
from neuronsimulator.models import Neuron


class Command(BaseCommand):
    # Show this when the user types help
    help = "Loads data from a neuron list into the database"

    def add_arguments(self, parser):
        parser.add_argument("neuron_list_filename", type=str)

    def handle(self, *args, **options):
        print("Loading neuron data")
        for row in DictReader(
            open(options["neuron_list_filename"]),
            dialect="excel-tab",
        ):
            # print(row['NAME'])
            neuron, created = Neuron.objects.get_or_create(name=row["NAME"])
            if created:
                print(f"Created new record: Neuron:{neuron}")
            neuron.save()
