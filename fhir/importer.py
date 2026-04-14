import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils.dateparse import parse_date, parse_datetime

from clinical.models import Allergy, Condition, Encounter, Immunization, Medication, Observation
from patients.models import PatientProfile

from .models import FHIRLink, FHIRResourceSnapshot


SUPPORTED_RESOURCE_TYPES = {
    "Patient",
    "Condition",
    "AllergyIntolerance",
    "MedicationStatement",
    "MedicationRequest",
    "Immunization",
    "Observation",
    "Encounter",
}


@dataclass
class FHIRImportResult:
    created: int = 0
    updated: int = 0
    snapshots: int = 0
    unsupported: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def imported(self):
        return self.created + self.updated


def import_fhir_json(payload, source="imported"):
    resources = _extract_resources(payload)
    result = FHIRImportResult()
    patient_by_reference = {}

    with transaction.atomic():
        for resource in resources:
            if resource.get("resourceType") == "Patient":
                patient, created = _import_patient(resource)
                _record_import(result, created)
                _snapshot(resource, patient, source, result)
                _link(resource, patient, "patients.PatientProfile", patient.id, "fhir_to_internal")
                patient_by_reference.update(_patient_references(resource, patient))

        for resource in resources:
            resource_type = resource.get("resourceType")
            if resource_type == "Patient":
                continue

            patient = _resolve_patient(resource, patient_by_reference)
            if resource_type not in SUPPORTED_RESOURCE_TYPES:
                result.unsupported += 1
                _snapshot(resource, patient, source, result, is_valid=False, errors=["Unsupported resource type."])
                continue

            if not patient:
                result.errors.append(f"{_resource_label(resource)} could not be linked to a patient.")
                _snapshot(resource, None, source, result, is_valid=False, errors=["Missing or unknown patient reference."])
                continue

            importer = {
                "Condition": _import_condition,
                "AllergyIntolerance": _import_allergy,
                "MedicationStatement": _import_medication_statement,
                "MedicationRequest": _import_medication_request,
                "Immunization": _import_immunization,
                "Observation": _import_observation,
                "Encounter": _import_encounter,
            }[resource_type]
            obj, created = importer(resource, patient)
            _record_import(result, created)
            _snapshot(resource, patient, source, result)
            _link(resource, patient, _model_label(obj), obj.id, "fhir_to_internal")

    return result


def loads_fhir_json(raw):
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("FHIR import must be a JSON object.")
    return payload


def _extract_resources(payload):
    resource_type = payload.get("resourceType")
    if resource_type == "Bundle":
        resources = []
        for entry in payload.get("entry", []):
            resource = entry.get("resource") if isinstance(entry, dict) else None
            if isinstance(resource, dict):
                resources.append(resource)
        if not resources:
            raise ValueError("FHIR Bundle does not contain any resources.")
        return resources
    if resource_type:
        return [payload]
    raise ValueError("FHIR JSON must include a resourceType.")


def _import_patient(resource):
    defaults = _patient_defaults(resource)
    patient = _object_for_resource(resource, "patients.PatientProfile")
    if patient:
        for field, value in defaults.items():
            setattr(patient, field, value)
        patient.save()
        return patient, False

    patient = PatientProfile.objects.create(**defaults)
    return patient, True


def _patient_defaults(resource):
    name = _first(resource.get("name")) or {}
    given = name.get("given") or []
    address = _first(resource.get("address")) or {}
    lines = address.get("line") or []

    return {
        "first_name": _first(given) or "",
        "last_name": name.get("family") or "",
        "date_of_birth": _date(resource.get("birthDate")),
        "sex_at_birth": resource.get("gender") or "",
        "phone": _telecom(resource, "phone"),
        "email": _telecom(resource, "email"),
        "address_line_1": _first(lines) or "",
        "address_line_2": lines[1] if len(lines) > 1 else "",
        "city": address.get("city") or "",
        "state": address.get("state") or "",
        "postal_code": address.get("postalCode") or "",
        "country": address.get("country") or "USA",
    }


def _import_condition(resource, patient):
    obj = _object_for_resource(resource, "clinical.Condition") or Condition(patient=patient)
    obj.patient = patient
    obj.name = _codeable_text(resource.get("code")) or "Unknown condition"
    obj.icd10_code = _coding_code(resource.get("code"), "icd-10") or obj.icd10_code
    obj.snomed_code = _coding_code(resource.get("code"), "snomed") or obj.snomed_code
    obj.clinical_status = _codeable_text(resource.get("clinicalStatus")) or ""
    obj.onset_date = _date(resource.get("onsetDateTime") or resource.get("onsetDate") or resource.get("recordedDate"))
    obj.abatement_date = _date(resource.get("abatementDateTime") or resource.get("abatementDate"))
    obj.notes = _notes(resource)
    created = obj.pk is None
    obj.save()
    return obj, created


def _import_allergy(resource, patient):
    obj = _object_for_resource(resource, "clinical.Allergy") or Allergy(patient=patient)
    reaction = _first(resource.get("reaction")) or {}
    obj.patient = patient
    obj.substance = _codeable_text(resource.get("code")) or "Unknown allergy"
    obj.rxnorm_code = _coding_code(resource.get("code"), "rxnorm") or obj.rxnorm_code
    obj.snomed_code = _coding_code(resource.get("code"), "snomed") or obj.snomed_code
    obj.category = _first(resource.get("category")) or ""
    obj.criticality = resource.get("criticality") or ""
    obj.reaction = _codeable_text(_first(reaction.get("manifestation"))) or ""
    obj.severity = reaction.get("severity") or ""
    obj.notes = _notes(resource)
    created = obj.pk is None
    obj.save()
    return obj, created


def _import_medication_statement(resource, patient):
    obj = _object_for_resource(resource, "clinical.Medication") or Medication(patient=patient)
    period = resource.get("effectivePeriod") or {}
    obj.patient = patient
    obj.name = _medication_name(resource) or "Unknown medication"
    obj.rxnorm_code = _coding_code(resource.get("medicationCodeableConcept"), "rxnorm") or obj.rxnorm_code
    obj.dosage_text = _dosage_text(resource)
    obj.status = resource.get("status") or ""
    obj.start_date = _date(period.get("start") or resource.get("effectiveDateTime"))
    obj.end_date = _date(period.get("end"))
    obj.indication = _codeable_text(_first(resource.get("reasonCode"))) or ""
    obj.notes = _notes(resource)
    created = obj.pk is None
    obj.save()
    return obj, created


def _import_medication_request(resource, patient):
    obj = _object_for_resource(resource, "clinical.Medication") or Medication(patient=patient)
    obj.patient = patient
    obj.name = _medication_name(resource) or "Unknown medication"
    obj.rxnorm_code = _coding_code(resource.get("medicationCodeableConcept"), "rxnorm") or obj.rxnorm_code
    obj.dosage_text = _dosage_text(resource)
    obj.status = resource.get("status") or ""
    obj.start_date = _date(resource.get("authoredOn"))
    obj.prescriber = _display(resource.get("requester"))
    obj.indication = _codeable_text(_first(resource.get("reasonCode"))) or ""
    obj.notes = _notes(resource)
    created = obj.pk is None
    obj.save()
    return obj, created


def _import_immunization(resource, patient):
    obj = _object_for_resource(resource, "clinical.Immunization") or Immunization(patient=patient)
    obj.patient = patient
    obj.vaccine_name = _codeable_text(resource.get("vaccineCode")) or "Unknown vaccine"
    obj.cvx_code = _coding_code(resource.get("vaccineCode"), "cvx") or obj.cvx_code
    obj.occurrence_date = _date(resource.get("occurrenceDateTime") or resource.get("occurrenceString"))
    obj.lot_number = resource.get("lotNumber") or ""
    obj.manufacturer = _display(resource.get("manufacturer"))
    obj.performer = _display((_first(resource.get("performer")) or {}).get("actor"))
    obj.notes = _notes(resource)
    created = obj.pk is None
    obj.save()
    return obj, created


def _import_observation(resource, patient):
    obj = _object_for_resource(resource, "clinical.Observation") or Observation(patient=patient)
    value_quantity = resource.get("valueQuantity") or {}
    obj.patient = patient
    obj.category = _observation_category(resource)
    obj.name = _codeable_text(resource.get("code")) or "Unknown observation"
    obj.loinc_code = _coding_code(resource.get("code"), "loinc") or obj.loinc_code
    obj.value_string = resource.get("valueString") or _codeable_text(resource.get("valueCodeableConcept")) or ""
    obj.value_quantity = _decimal(value_quantity.get("value"))
    obj.unit = value_quantity.get("unit") or value_quantity.get("code") or ""
    obj.effective_datetime = _datetime(resource.get("effectiveDateTime"))
    obj.interpretation = _codeable_text(_first(resource.get("interpretation"))) or ""
    obj.reference_range = _reference_range(resource)
    obj.notes = _notes(resource)
    created = obj.pk is None
    obj.save()
    return obj, created


def _import_encounter(resource, patient):
    obj = _object_for_resource(resource, "clinical.Encounter") or Encounter(patient=patient)
    period = resource.get("period") or {}
    obj.patient = patient
    obj.encounter_type = _codeable_text(_first(resource.get("type"))) or _codeable_text(resource.get("class")) or ""
    obj.status = resource.get("status") or ""
    obj.start_time = _datetime(period.get("start"))
    obj.end_time = _datetime(period.get("end"))
    obj.provider_name = _display((_first(resource.get("participant")) or {}).get("individual"))
    obj.facility_name = _display(resource.get("serviceProvider"))
    obj.reason = _codeable_text(_first(resource.get("reasonCode"))) or ""
    obj.summary = _notes(resource)
    created = obj.pk is None
    obj.save()
    return obj, created


def _object_for_resource(resource, django_model):
    resource_id = resource.get("id")
    if not resource_id:
        return None
    link = FHIRLink.objects.filter(
        resource_type=resource.get("resourceType"),
        resource_id=resource_id,
        django_model=django_model,
    ).first()
    if not link:
        return None
    app_label, model_name = django_model.split(".")
    for model in (PatientProfile, Condition, Allergy, Medication, Immunization, Observation, Encounter):
        if model._meta.app_label == app_label and model.__name__ == model_name:
            return model.objects.filter(pk=link.django_object_id).first()
    return None


def _resolve_patient(resource, patient_by_reference):
    subject = resource.get("subject") or resource.get("patient")
    reference = subject.get("reference") if isinstance(subject, dict) else None
    if reference in patient_by_reference:
        return patient_by_reference[reference]
    if reference:
        resource_id = reference.split("/")[-1]
        link = FHIRLink.objects.filter(
            resource_type="Patient",
            resource_id=resource_id,
            django_model="patients.PatientProfile",
        ).first()
        if link:
            return PatientProfile.objects.filter(pk=link.django_object_id).first()
    return None


def _patient_references(resource, patient):
    resource_id = resource.get("id")
    if not resource_id:
        return {}
    return {
        resource_id: patient,
        f"Patient/{resource_id}": patient,
        f"urn:uuid:{resource_id}": patient,
    }


def _link(resource, patient, django_model, object_id, direction):
    resource_id = resource.get("id") or ""
    link = FHIRLink.objects.filter(
        resource_type=resource.get("resourceType"),
        resource_id=resource_id,
        django_model=django_model,
        django_object_id=object_id,
    ).first()
    if not link:
        link = FHIRLink(
            resource_type=resource.get("resourceType"),
            resource_id=resource_id,
            django_model=django_model,
            django_object_id=object_id,
        )
    link.patient = patient
    link.direction = direction
    link.save()


def _snapshot(resource, patient, source, result, is_valid=True, errors=None):
    FHIRResourceSnapshot.objects.create(
        patient=patient,
        resource_type=resource.get("resourceType", ""),
        resource_id=resource.get("id", ""),
        version_id=((resource.get("meta") or {}).get("versionId") or ""),
        source=source,
        raw_json=resource,
        checksum=_checksum(resource),
        is_valid=is_valid,
        validation_errors=errors or [],
    )
    result.snapshots += 1


def _checksum(resource):
    encoded = json.dumps(resource, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _record_import(result, created):
    if created:
        result.created += 1
    else:
        result.updated += 1


def _model_label(obj):
    return f"{obj._meta.app_label}.{obj.__class__.__name__}"


def _resource_label(resource):
    return f"{resource.get('resourceType', 'Resource')}/{resource.get('id', '')}".rstrip("/")


def _first(value):
    return value[0] if isinstance(value, list) and value else None


def _telecom(resource, system):
    for telecom in resource.get("telecom") or []:
        if telecom.get("system") == system:
            return telecom.get("value") or ""
    return ""


def _codeable_text(value):
    if not isinstance(value, dict):
        return ""
    if value.get("text"):
        return value["text"]
    coding = _first(value.get("coding"))
    if not coding:
        return ""
    return coding.get("display") or coding.get("code") or ""


def _coding_code(value, system_fragment):
    if not isinstance(value, dict):
        return ""
    for coding in value.get("coding") or []:
        system = (coding.get("system") or "").lower()
        if system_fragment.lower() in system:
            return coding.get("code") or ""
    return ""


def _display(value):
    if not isinstance(value, dict):
        return ""
    return value.get("display") or value.get("reference") or ""


def _notes(resource):
    notes = []
    for note in resource.get("note") or []:
        text = note.get("text")
        if text:
            notes.append(text)
    return "\n".join(notes)


def _medication_name(resource):
    return (
        _codeable_text(resource.get("medicationCodeableConcept"))
        or _display(resource.get("medicationReference"))
    )


def _dosage_text(resource):
    dosage = _first(resource.get("dosage")) or {}
    return dosage.get("text") or ""


def _observation_category(resource):
    category = _codeable_text(_first(resource.get("category"))).lower()
    if "vital" in category:
        return "vital"
    if "lab" in category or "laboratory" in category:
        return "lab"
    return "other"


def _reference_range(resource):
    first_range = _first(resource.get("referenceRange")) or {}
    text = first_range.get("text")
    if text:
        return text
    low = (first_range.get("low") or {}).get("value")
    high = (first_range.get("high") or {}).get("value")
    if low is not None and high is not None:
        return f"{low} - {high}"
    return ""


def _date(value):
    if not value:
        return None
    parsed = parse_date(str(value)[:10])
    if parsed:
        return parsed
    parsed_datetime = parse_datetime(str(value))
    return parsed_datetime.date() if parsed_datetime else None


def _datetime(value):
    if not value:
        return None
    return parse_datetime(str(value))


def _decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
