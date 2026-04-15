from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import FHIRImportForm
from .importer import import_fhir_payloads


@staff_member_required
def import_fhir_data(request):
    if request.method == "POST":
        form = FHIRImportForm(request.POST, request.FILES)
        if form.is_valid():
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
                    f"{result.unsupported} unsupported resources skipped."
                ),
            )
            return redirect(reverse("admin:fhir_fhirresourcesnapshot_changelist"))
    else:
        form = FHIRImportForm()

    return render(request, "admin/fhir_import.html", {"form": form})
