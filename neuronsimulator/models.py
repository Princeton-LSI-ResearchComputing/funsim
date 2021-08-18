from django.db import models


class Neuron(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=10,
        unique=True,
        help_text="The unique name of the worm neuron",
    )

    class Meta:
        verbose_name = "neuron"
        verbose_name_plural = "neurons"
        ordering = ["name"]

    def __str__(self):
        return str(self.name)
