from django import forms

from .importer import loads_fhir_json


class FHIRImportForm(forms.Form):
    fhir_file = forms.FileField(
        label="FHIR JSON file",
        required=False,
        help_text="Upload a FHIR Bundle or a single FHIR resource as JSON.",
    )
    fhir_json = forms.CharField(
        label="FHIR JSON",
        widget=forms.Textarea(attrs={"rows": 14}),
        required=False,
        help_text="Paste a FHIR Bundle or single resource when you do not have a file.",
    )

    def clean(self):
        cleaned_data = super().clean()
        uploaded_file = cleaned_data.get("fhir_file")
        pasted_json = cleaned_data.get("fhir_json", "").strip()

        if not uploaded_file and not pasted_json:
            raise forms.ValidationError("Upload a FHIR JSON file or paste FHIR JSON.")

        if uploaded_file and pasted_json:
            raise forms.ValidationError("Use either a file upload or pasted JSON, not both.")

        if uploaded_file:
            try:
                raw = uploaded_file.read().decode("utf-8")
            except UnicodeDecodeError as exc:
                raise forms.ValidationError("FHIR file must be UTF-8 encoded JSON.") from exc
        else:
            raw = pasted_json

        try:
            cleaned_data["payload"] = loads_fhir_json(raw)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

        return cleaned_data
