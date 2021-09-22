from django import forms
from django.core.validators import MinValueValidator
from neuronsimulator.models import Neuron

STIM_TYPE_CHOICES = (
    ("rectangular", "rectangular"),
    ("delta", "delta"),
    ("sine", "sine"),
    ("realistic", "realistic"),
)


class NeuronInputParamForm(forms.Form):
    stim_neu_id = forms.CharField(max_length=10, widget=forms.HiddenInput())
    resp_neu_ids = forms.CharField(
        max_length=3000, required=False, widget=forms.HiddenInput()
    )
    nt = forms.IntegerField(
        initial=1000,
        label="Number of time points(nt)",
        validators=[MinValueValidator(1)],
    )
    # use t_max to replace dt
    t_max = forms.DecimalField(
        initial=100,
        label="Maximum time(t_max)",
        validators=[MinValueValidator(0)],
        help_text="value requirement: t_max>dur",
    )
    stim_type = forms.ChoiceField(
        choices=STIM_TYPE_CHOICES,
        widget=forms.Select,
        label="Type of standard stimulus(stim_type)",
        initial="rectangular",
    )
    dur = forms.DecimalField(
        initial=2.0,
        label="Duration of the stimulus(dur)",
        validators=[MinValueValidator(0.1)],
    )

    def clean(self):
        cleaned_data = super().clean()

        stim_neu_id = cleaned_data.get("stim_neu_id")
        resp_neu_ids = cleaned_data.get("resp_neu_ids")

        # a neuron cannot be selected for both stim_neu_id and resp_neu_ids
        if resp_neu_ids is not None:
            resp_neu_arr = cleaned_data.get("resp_neu_ids").split(",")
            if stim_neu_id in resp_neu_arr:
                raise forms.ValidationError(
                    "Response neuron(s) cannot include stimulated neuron, please make a different selection."
                )

        # t_max should be larger than dur
        t_max = float(cleaned_data.get("t_max"))
        dur = float(cleaned_data.get("dur"))
        if t_max < dur:
            raise forms.ValidationError("t_max must be larger than dur.")

    def clean_stim_neu_id(self):
        neurons = Neuron.objects.values_list("name", flat=True).all()
        stim_neu_id = self.cleaned_data.get("stim_neu_id", None)
        if stim_neu_id not in neurons:
            raise forms.ValidationError("stimulated neuron is not a valid neuron")
        return stim_neu_id

    def clean_resp_neu_ids(self):
        neurons = Neuron.objects.values_list("name", flat=True).all()
        resp_neu_ids = self.cleaned_data.get("resp_neu_ids", None)

        """
        resp_neu_ids could be None based on wormfunconn source code
        but require at least one resp neuron at this stage of test
        will deal with this case later: resp_neu_ids=None and use a threshold value
        """
        if len(resp_neu_ids) == 0:
            raise forms.ValidationError(
                "You must select at least one response neuron (for testing)."
            )
        else:
            resp_neu_arr = resp_neu_ids.split(",")
            invalid_neurons = [i for i in resp_neu_arr if i not in neurons]
            if len(invalid_neurons) > 0:
                raise forms.ValidationError(
                    f"Invalid response neuron(s) encountered: [{', '.join(invalid_neurons)}]"
                )
        return resp_neu_ids


# keep ParamForm for now (as a reference for evaluating NeuronInputParamForm and form render)
class ParamForm(forms.Form):
    stim_neuron = forms.CharField(
        max_length=10, widget=forms.TextInput, label="stim_neu_id"
    )
    resp_neurons = forms.CharField(
        max_length=3000, widget=forms.Textarea(attrs={"rows": 3}), label="resp_neu_ids"
    )
    nt = forms.IntegerField(initial=1000, label="nt", help_text="Number of time points")
    dt = forms.DecimalField(initial=0.1, label="dt", help_text="Time step")
    stim_type = forms.CharField(
        widget=forms.TextInput,
        label="stim_type",
        initial="rectangular",
        help_text="Type of standard stimulus",
    )
    dur = forms.IntegerField(
        initial=2, label="dur", help_text="Duration of the stimulus"
    )
