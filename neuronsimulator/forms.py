import wormfunconn as wfc
from django import forms
from django.core.validators import MinValueValidator
from neuronsimulator.utils import WormfunconnToPlot as wfc2plot


class ParamForm(forms.Form):
    """
    This is a form class used for collecting parameters from POST or GET request to plot neural responses
    """

    stim_type_list = wfc2plot().get_stim_type_list()
    stim_type_choices = wfc2plot().get_stim_type_choice()

    form_opt_field_dict = wfc2plot().get_form_opt_field_dict()

    strains = wfc.strains

    STRAIN_CHOICES = [(strain, strain) for strain in strains]

    strain_type = forms.ChoiceField(
        choices=STRAIN_CHOICES,
        widget=forms.Select,
        label="Type of strain",
        initial="wild-type",
    )
    stim_type = forms.ChoiceField(
        choices=stim_type_choices,
        label="Activity waveform of stimulated neuron",
        initial="realistic",
        widget=forms.Select,
    )
    stim_neu_id = forms.ChoiceField()
    resp_neu_ids = forms.MultipleChoiceField()
    top_n = forms.IntegerField(
        initial=10,
        label="Top N most responsive",
        required=False,
        help_text="If not None, return top N responses with the largest absolute peak amplitude.",
        widget=forms.NumberInput(attrs={"min": 0}),
    )
    nt = forms.IntegerField(
        initial=1000,
        label="Number of time points",
        validators=[MinValueValidator(1)],
        widget=forms.HiddenInput(attrs={"min": 1}),
    )
    t_max = forms.FloatField(
        initial=100,
        label="Time window to plot (s)",
        validators=[MinValueValidator(0.1)],
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

        # default choices for neurons
        neuron_ids, app_error_dict = wfc2plot().get_neuron_ids("wild-type")
        # set neuron choices based on strain type
        if "strain_type" in self.data:
            try:
                strain_type = self.data.get("strain_type")
                neuron_ids, app_error_dict = wfc2plot().get_neuron_ids(strain_type)
            except (ValueError, TypeError):
                neuron_ids, app_error_dict = wfc2plot().get_neuron_ids("wild-type")

        neuron_choices = [(neu_id, neu_id) for neu_id in neuron_ids]

        self.fields["stim_neu_id"] = forms.ChoiceField(
            choices=neuron_choices,
            required=False,
            label="Stimulated neuron",
            widget=forms.Select(
                attrs={
                    "class": "selectpicker",
                    "data-live-search": "true",
                    "data-width": "fit",
                    "title": "Choose one neuron",
                }
            ),
        )

        self.fields["resp_neu_ids"] = forms.MultipleChoiceField(
            choices=neuron_choices,
            label="Hand selected neurons",
            required=False,
            widget=forms.SelectMultiple(
                attrs={
                    "class": "selectpicker",
                    "data-live-search": "true",
                    "data-width": "fit",
                    "data-actions-box": "true",
                    "data-selected-text-format": "count > 12",
                    "title": "Choose neurons a priori",
                }
            ),
        )

        self.fields["top_n"].widget.attrs["max"] = len(neuron_ids) - 1
