from django import forms

# from django.core.exceptions import ValidationError
from neuronsimulator.models import Neuron


class ParamForm(forms.Form):
    stim_neuron = forms.CharField(
        max_length=10, widget=forms.TextInput, label="stim_neu_id"
    )
    resp_neurons = forms.CharField(
        max_length=3000, widget=forms.Textarea(attrs={'rows':3}), 
        label="resp_neu_ids"
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
