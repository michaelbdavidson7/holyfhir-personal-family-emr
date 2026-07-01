import json
from collections import defaultdict
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from django.utils import timezone

from .models import FHIRResourceSnapshot
from .serializers import SERIALIZER_MODELS, serialize_model_resource


def exportable_snapshot_queryset():
    return (
        FHIRResourceSnapshot.objects.filter(is_valid=True)
        .exclude(import_status=FHIRResourceSnapshot.IMPORT_STATUS_INVALID)
        .order_by("resource_type", "resource_id", "-created_at", "-pk")
    )


def latest_snapshots(queryset):
    seen = set()
    snapshots = []
    for snapshot in queryset:
        key = (
            snapshot.resource_type,
            snapshot.resource_id or f"snapshot-{snapshot.pk}",
        )
        if key in seen:
            continue
        seen.add(key)
        snapshots.append(snapshot)
    return snapshots


def build_fhir_export_zip(
    queryset, latest_only=True, patient=None, include_model_serialized=False
):
    grouped_resources = defaultdict(list)
    skipped = 0

    if include_model_serialized:
        for resource in serialized_model_resources(patient=patient):
            grouped_resources[resource["resourceType"]].append(resource)

    snapshots = latest_snapshots(queryset) if latest_only else list(queryset)
    for snapshot in snapshots:
        resource = snapshot.raw_json
        if not isinstance(resource, dict) or not resource.get("resourceType"):
            skipped += 1
            continue
        grouped_resources[resource["resourceType"]].append(resource)

    archive_bytes = BytesIO()
    with ZipFile(archive_bytes, "w", compression=ZIP_DEFLATED) as archive:
        manifest = {
            "resourceType": "Bundle",
            "type": "collection",
            "timestamp": timezone.now().isoformat(),
            "total": sum(len(resources) for resources in grouped_resources.values()),
            "export": {
                "format": "ndjson-by-resource-type",
                "latestOnly": latest_only,
                "modelSerialized": include_model_serialized,
                "skipped": skipped,
            },
            "entry": [
                {
                    "resource": {
                        "resourceType": "Basic",
                        "code": {"text": resource_type},
                        "extension": [
                            {
                                "url": "https://holyfhir.local/fhir-export-count",
                                "valueInteger": len(resources),
                            }
                        ],
                    }
                }
                for resource_type, resources in sorted(grouped_resources.items())
            ],
        }
        archive.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        )

        for resource_type, resources in sorted(grouped_resources.items()):
            lines = [
                json.dumps(resource, ensure_ascii=False, separators=(",", ":"))
                for resource in resources
            ]
            archive.writestr(f"FHIR/{resource_type}.ndjson", "\n".join(lines) + "\n")

    archive_bytes.seek(0)
    return archive_bytes.getvalue()


def serialized_model_resources(patient=None):
    for model in SERIALIZER_MODELS:
        queryset = model.objects.all()
        if patient:
            if model._meta.label_lower == "patients.patientprofile":
                queryset = queryset.filter(pk=patient.pk)
            elif any(field.name == "patient" for field in model._meta.fields):
                queryset = queryset.filter(patient=patient)
            else:
                queryset = queryset.none()
        for obj in queryset.order_by("pk"):
            resource = serialize_model_resource(obj)
            if resource:
                yield resource
