from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from neuronsimulator.models import Neuron

STIM_TYPE_CHOICES = (
    ("rectangular", "rectangular"),
    ("delta", "delta"),
    ("sinusoidal", "sinusoidal"),
    ("realistic", "realistic"),
)

STRAIN_CHOICES = (
    ("wild type", "wild type"),
    ("mutant1", "mutant1"),
)


class ParamForm(forms.Form):
    def _neuron_choices():
        queryset = Neuron.objects.all()
        return [(c, c) for c in queryset.values_list("name", flat=True)]

    stim_type = forms.ChoiceField(
        choices=STIM_TYPE_CHOICES,
        label="Type of standard stimulus",
        initial="rectangular",
        widget=forms.Select,
    )
    stim_neu_id = forms.ChoiceField(
        choices=_neuron_choices,
        initial="ADAL",
        label="Stimulated neuron",
        widget =forms.Select(
            attrs={
                "class": "selectpicker",
                "data-live-search": "true",
                "data-width": "fit",
            }
        ),      
    )
    resp_neu_ids = forms.MultipleChoiceField(
        choices=_neuron_choices,
        label="Responding neurons",
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-live-search": "true",
                "data-width": "fit",
                "data-actions-box": "true"
            }
        ),
    )
    top_n = forms.IntegerField(
        initial=0,
        label="Top N Responses",
        required=False,
        help_text="If not None, return top_n responses with the the largest absolute peak amplitude",
        widget=forms.NumberInput(attrs={"min": 0}),
    )
    nt = forms.IntegerField(
        initial=1000,
        label="Number of time points",
        validators=[MinValueValidator(1)],
        widget=forms.HiddenInput(attrs={'min': 1}),
    )
    duration = forms.FloatField(
        initial=1.0,
        label="Duration (s)",
        validators=[MinValueValidator(0)],
        help_text="required parameter when stim_type is rectangular; minimum value is 0",
        widget=forms.NumberInput(attrs={"step": 1, "min": 0.0}),
    )
    frequency = forms.FloatField(
        initial=0.1,
        label="Frequency (Hz)",
        validators=[MinValueValidator(0), MaxValueValidator(0.25)],
        help_text="required parameter when stim_type is sinusoidal; values ranging from 0 to 0.25",
        widget=forms.NumberInput(attrs={"step": 0.01, "max": 0.25, "min": 0.0}),
    )
    phi0 = forms.FloatField(
        initial=0.0,
        label="Phase",
        validators=[MinValueValidator(0), MaxValueValidator(6.28)],
        help_text="required parameter when stim_type is sinusoidal; values ranging from 0 to 6.28",
        widget=forms.NumberInput(attrs={"step": 0.01, "max": 6.28, "min": 0.0}),
    )
    tau1 = forms.FloatField(
        initial=1.0,
        label="Timescale 1 (s)",
        validators=[MinValueValidator(0.5), MaxValueValidator(100)],
        help_text="required parameter when stim_type is realistic; values ranging from 0.5 to 100",
        widget=forms.NumberInput(attrs={"step": 0.1, "max": 100, "min": 0.5}),
    )
    tau2 = forms.FloatField(
        initial=0.8,
        label="Timescale 2 (s)",
        validators=[MinValueValidator(0.5), MaxValueValidator(100)],
        help_text="required parameter when stim_type is realistic; values ranging from 0.5 to 100",
        widget=forms.NumberInput(attrs={"step": 0.1, "max": 100, "min": 0.5}),
    )
    t_max = forms.FloatField(
        initial=100,
        label="Maximum time (t_max)",
        validators=[MinValueValidator(0.1)],
    )
    strain_type = forms.ChoiceField(
        choices=STRAIN_CHOICES,
        widget=forms.Select,
        label="Type of strain",
        initial="wild type",
    )

    def clean(self):
        cleaned_data = super().clean()
        top_n = cleaned_data["top_n"]
        # check top_n value
        if top_n is not None and top_n < 0:
            raise forms.ValidationError(f"Negative value is not allowed for Top_n.")
