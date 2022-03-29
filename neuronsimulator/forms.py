from django import forms
from django.core.validators import MinValueValidator
from neuronsimulator.models import Neuron
from neuronsimulator.utils import WormfunconnToPlot as wfc2plot


class ParamForm(forms.Form):
    """
    This is a form class used for collecting parameters from POST or GET request to plot neural responses
    """

    stim_type_list = wfc2plot().get_stim_type_list()
    stim_type_choices = wfc2plot().get_stim_type_choice()

    form_opt_field_dict = wfc2plot().get_form_opt_field_dict()

    neuron_choices = [
        (neu_id, neu_id)
        for neu_id in Neuron.objects.all().values_list("name", flat=True)
    ]

    STRAIN_CHOICES = [
        ("wild type", "wild type"),
        ("mutant1", "mutant1"),
    ]

    stim_type = forms.ChoiceField(
        choices=stim_type_choices,
        label="Type of standard stimulus",
        initial="rectangular",
        widget=forms.Select,
    )
    stim_neu_id = forms.ChoiceField(
        choices=neuron_choices,
        initial="ADAL",
        label="Stimulated neuron",
        widget=forms.Select(
            attrs={
                "class": "selectpicker",
                "data-live-search": "true",
                "data-width": "fit",
            }
        ),
    )
    resp_neu_ids = forms.MultipleChoiceField(
        choices=neuron_choices,
        label="Responding neurons",
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-live-search": "true",
                "data-width": "fit",
                "data-actions-box": "true",
            }
        ),
    )
    top_n = forms.IntegerField(
        initial=0,
        label="Top N Responses",
        required=False,
        help_text="If not None, return top N responses with the largest absolute peak amplitude",
        widget=forms.NumberInput(attrs={"max": len(neuron_choices), "min": 0}),
    )
    nt = forms.IntegerField(
        initial=1000,
        label="Number of time points",
        validators=[MinValueValidator(1)],
        widget=forms.HiddenInput(attrs={"min": 1}),
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
    # optional fields based on stim_types
    duration = forms.FloatField()
    frequency = forms.FloatField()
    phi0 = forms.FloatField()
    tau1 = forms.FloatField()
    tau2 = forms.FloatField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set attrs. for optional fields:
        for field_name, field_attrs in self.form_opt_field_dict.items():
            self.fields[field_name].label = field_attrs["label"]
            self.fields[field_name].initial = field_attrs["default"]
            self.fields[field_name].help_text = field_attrs["help_text"]
            self.fields[field_name].widget.attrs["min"] = field_attrs["min_val"]
            self.fields[field_name].widget.attrs["max"] = field_attrs["max_val"]
            self.fields[field_name].widget.attrs["step"] = field_attrs["step"]
            # found a bug in FunctionalAtlas.get_standard_stim_kwargs(stim_type)
            # a workaround for current version
            self.fields["frequency"].initial = 0.1
