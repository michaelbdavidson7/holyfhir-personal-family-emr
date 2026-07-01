from io import BytesIO
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

from django import forms

from patients.models import PatientProfile

from .importer import loads_fhir_documents


FHIR_ZIP_SIDECAR_FILENAMES = {
    "log.ndjson",
}


class FHIRImportForm(forms.Form):
    patient = forms.ModelChoiceField(
        label="Attach to patient",
        queryset=PatientProfile.objects.order_by("last_name", "first_name", "id"),
        required=False,
        empty_label="Select a Patient",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Choose an existing profile to attach this import to. Leave blank to create or update from the FHIR Patient resource.",
    )
    fhir_file = forms.FileField(
        label="FHIR JSON file",
        required=False,
        help_text="Upload a MyChart ZIP export, NDJSON file, FHIR Bundle, or single FHIR resource JSON.",
    )
    fhir_json = forms.CharField(
        label="FHIR JSON",
        widget=forms.Textarea(attrs={"rows": 14}),
        required=False,
        help_text="Paste a FHIR Bundle, NDJSON, or single resource when you do not have a file.",
    )

    def clean(self):
        cleaned_data = super().clean()
        uploaded_file = cleaned_data.get("fhir_file")
        pasted_json = cleaned_data.get("fhir_json", "").strip()

        if not uploaded_file and not pasted_json:
            raise forms.ValidationError(
                "Upload a FHIR ZIP/JSON/NDJSON file or paste FHIR JSON."
            )

        if uploaded_file and pasted_json:
            raise forms.ValidationError(
                "Use either a file upload or pasted JSON, not both."
            )

        if uploaded_file:
            cleaned_data["payloads"] = self._payloads_from_upload(uploaded_file)
        else:
            try:
                cleaned_data["payloads"] = loads_fhir_documents(
                    pasted_json, "pasted FHIR JSON"
                )
            except ValueError as exc:
                raise forms.ValidationError(str(exc)) from exc

        return cleaned_data

    def _payloads_from_upload(self, uploaded_file):
        filename = uploaded_file.name or ""
        content = uploaded_file.read()
        if filename.lower().endswith(".zip"):
            return self._payloads_from_zip(content)

        try:
            raw = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise forms.ValidationError(
                "FHIR file must be UTF-8 encoded JSON/NDJSON or a ZIP export."
            ) from exc

        try:
            return loads_fhir_documents(raw, filename)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

    def _payloads_from_zip(self, content):
        payloads = []
        try:
            with ZipFile(BytesIO(content)) as archive:
                for name in archive.namelist():
                    path = PurePosixPath(name)
                    if path.name.startswith(".") or not path.name:
                        continue
                    if path.name.lower() in FHIR_ZIP_SIDECAR_FILENAMES:
                        continue
                    if path.suffix.lower() not in {".json", ".ndjson"}:
                        continue
                    try:
                        raw = archive.read(name).decode("utf-8-sig")
                    except UnicodeDecodeError as exc:
                        raise forms.ValidationError(
                            f"{name} must be UTF-8 encoded."
                        ) from exc
                    try:
                        payloads.extend(loads_fhir_documents(raw, path.name))
                    except ValueError as exc:
                        raise forms.ValidationError(f"{name}: {exc}") from exc
        except BadZipFile as exc:
            raise forms.ValidationError(
                "Uploaded ZIP file could not be opened."
            ) from exc

        if not payloads:
            raise forms.ValidationError(
                "ZIP file did not contain any FHIR JSON or NDJSON files."
            )
        return payloads


class FHIRExportForm(forms.Form):
    patient = forms.ModelChoiceField(
        label="Patient",
        queryset=PatientProfile.objects.order_by("last_name", "first_name", "id"),
        required=False,
        empty_label="All patients and shared records",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Choose one patient, or leave this blank to export every valid FHIR snapshot.",
    )
    latest_only = forms.BooleanField(
        label="Only export the latest copy of each resource",
        required=False,
        initial=True,
        help_text="Recommended. This avoids duplicate copies from repeated imports.",
    )

    include_model_serialized = forms.BooleanField(
        label="Include current app records as FHIR",
        required=False,
        initial=True,
        help_text="Exports supported Django records as fresh FHIR JSON before falling back to saved snapshots.",
    )


class MedicalSummaryPDFForm(forms.Form):
    patient = forms.ModelChoiceField(
        label="Patient",
        queryset=PatientProfile.objects.order_by("last_name", "first_name", "id"),
        required=True,
        empty_label="Select a Patient",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Choose the patient whose human-readable medical summary should be downloaded.",
    )
    include_allergies = forms.BooleanField(
        label="Allergies",
        required=False,
        initial=True,
    )
    include_medications = forms.BooleanField(
        label="Medications",
        required=False,
        initial=True,
    )
    include_conditions = forms.BooleanField(
        label="Conditions",
        required=False,
        initial=True,
    )
    include_everything_else = forms.BooleanField(
        label="Everything else",
        required=False,
        initial=False,
        help_text="Adds the rest of the patient-linked resources. This can make a long PDF.",
    )

    def summary_options(self):
        return {
            "include_allergies": self.cleaned_data.get("include_allergies", False),
            "include_medications": self.cleaned_data.get("include_medications", False),
            "include_conditions": self.cleaned_data.get("include_conditions", False),
            "include_everything_else": self.cleaned_data.get(
                "include_everything_else", False
            ),
        }


class QuickPatientCreateForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ("first_name", "last_name", "date_of_birth")
        labels = {
            "first_name": "First name",
            "last_name": "Last name",
            "date_of_birth": "Date of birth",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }
