from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .backups import create_pre_import_database_backup
from .exporter import build_fhir_export_zip, exportable_snapshot_queryset
from .forms import (
    FHIRExportForm,
    FHIRImportForm,
    MedicalSummaryPDFForm,
    QuickPatientCreateForm,
)
from .importer import import_fhir_payloads
from .medical_summary import build_patient_medical_summary_pdf


@staff_member_required
def import_fhir_data(request):
    can_add_patient = request.user.has_perm("patients.add_patientprofile")
    base_context = admin.site.each_context(request)

    if request.method == "POST":
        if request.POST.get("action") == "create_patient":
            patient_form = QuickPatientCreateForm(request.POST)
            if not can_add_patient:
                messages.error(request, "You do not have permission to add patients.")
            elif patient_form.is_valid():
                patient = patient_form.save()
                messages.success(request, f"Patient added: {patient}.")
                return redirect(f"{reverse('fhir_import')}?patient={patient.pk}")
            form = FHIRImportForm()
            return render(
                request,
                "admin/fhir_import.html",
                {
                    **base_context,
                    "title": "Import FHIR Data",
                    "form": form,
                    "patient_form": patient_form,
                    "can_add_patient": can_add_patient,
                    "patient_add_url": reverse("admin:patients_patientprofile_add"),
                    "show_patient_modal": True,
                },
            )

        form = FHIRImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                backup_path = create_pre_import_database_backup()
            except OSError as error:
                messages.error(
                    request,
                    f"FHIR import was not started because the pre-import database copy failed: {error}",
                )
                patient_form = QuickPatientCreateForm()
                return render(
                    request,
                    "admin/fhir_import.html",
                    {
                        **base_context,
                        "title": "Import FHIR Data",
                        "form": form,
                        "patient_form": patient_form,
                        "can_add_patient": can_add_patient,
                        "patient_add_url": reverse("admin:patients_patientprofile_add"),
                        "show_patient_modal": False,
                    },
                )

            result = import_fhir_payloads(
                form.cleaned_data["payloads"],
                target_patient=form.cleaned_data.get("patient"),
            )
            if result.errors:
                for error in result.errors:
                    messages.warning(request, error)
            messages.success(
                request,
                (
                    f"FHIR import complete: {result.created} created, "
                    f"{result.updated} updated, {result.snapshots} snapshots saved, "
                    f"{result.unsupported} unsupported resources preserved as snapshots."
                ),
            )
            if backup_path:
                messages.info(
                    request, f"Pre-import database copy created: {backup_path}"
                )
            return redirect(reverse("admin:fhir_fhirresourcesnapshot_changelist"))
        patient_form = QuickPatientCreateForm()
    else:
        form = FHIRImportForm(initial={"patient": request.GET.get("patient") or None})
        patient_form = QuickPatientCreateForm()

    return render(
        request,
        "admin/fhir_import.html",
        {
            **base_context,
            "title": "Import FHIR Data",
            "form": form,
            "patient_form": patient_form,
            "can_add_patient": can_add_patient,
            "patient_add_url": reverse("admin:patients_patientprofile_add"),
            "show_patient_modal": False,
        },
    )


@staff_member_required
def export_fhir_data(request):
    base_context = admin.site.each_context(request)
    export_form = FHIRExportForm(initial={"latest_only": True})
    summary_form = MedicalSummaryPDFForm()

    if (
        request.method == "POST"
        and request.POST.get("action") == "download_medical_summary_pdf"
    ):
        summary_form = MedicalSummaryPDFForm(request.POST)
        if summary_form.is_valid():
            patient = summary_form.cleaned_data["patient"]
            pdf = build_patient_medical_summary_pdf(
                patient, summary_form.summary_options()
            )
            filename = f"medical-summary-patient-{patient.pk}.pdf"
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
    elif request.method == "POST":
        export_form = FHIRExportForm(request.POST)
        if export_form.is_valid():
            queryset = exportable_snapshot_queryset()
            patient = export_form.cleaned_data.get("patient")
            if patient:
                queryset = queryset.filter(patient=patient)

            archive = build_fhir_export_zip(
                queryset,
                latest_only=export_form.cleaned_data.get("latest_only", False),
                patient=patient,
                include_model_serialized=export_form.cleaned_data.get(
                    "include_model_serialized", False
                ),
            )
            filename = "fhir-export.zip"
            if patient:
                filename = f"fhir-export-patient-{patient.pk}.zip"
            response = HttpResponse(archive, content_type="application/zip")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

    return render(
        request,
        "admin/fhir_export.html",
        {
            **base_context,
            "title": "Export FHIR Data",
            "form": export_form,
            "summary_form": summary_form,
        },
    )
