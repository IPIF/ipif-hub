from django import forms
from datetime import time


class IpifRepoForm(forms.Form):
    primary_email = forms.EmailField(
        label="Email address", help_text="Primary email address"
    )
    secondary_email = forms.EmailField(
        label="Email address", help_text="Additional email address", required=False
    )
    tertiary_email = forms.EmailField(
        label="Email address", help_text="Additional email address", required=False
    )
    password = forms.CharField(label="Password", widget=forms.PasswordInput())
    confirm_password = forms.CharField(
        label="Confirm Password", widget=forms.PasswordInput()
    )

    endpoint_slug = forms.CharField(
        label="Endpoint URI prefix",
        help_text="Short URI prefix to namespace data (no spaces or special chars)",
        max_length=12,
    )
    endpoint_name = forms.CharField(label="Endpoint Name", max_length=100)
    endpoint_uri = forms.URLField(label="Endpoint URL")

    provider = forms.CharField(
        label="Provider of the data",
        help_text="e.g. the institution responsible for its creation",
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={"name": "body", "rows": "8", "cols": "70"})
    )

    refresh_frequency = forms.ChoiceField(
        choices=(("daily", "daily"), ("weekly", "weekly"), ("never", "never"))
    )
    refresh_time = forms.TimeField(
        initial=time(0, 0), help_text="Time of day to automatically re-ingest data"
    )
    endpoint_is_ipif = forms.BooleanField(
        initial=False,
        label="IPIF-compliant",
        label_suffix="?",
        help_text="URIs in this dataset point to an IPIF-compliant endpoint",
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("password and confirm_password does not match")


"""

 endpoint_name = models.CharField(max_length=30, default="")
    endpoint_slug = models.CharField(max_length=20, primary_key=True, db_index=True)
    endpoint_uri = models.URLField(db_index=True)
    refresh_frequency = models.CharField(
        max_length=10,
        choices=(("daily", "daily"), ("weekly", "weekly"), ("never", "never")),
    )
    refresh_time = models.TimeField()
    endpoint_is_ipif = models.BooleanField()

    description = models.TextField()
    provider = models.CharField(max_length=100, default="", blank=True)
"""
