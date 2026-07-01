from clinical.models import (
    Allergy,
    Condition,
    Encounter,
    Immunization,
    Medication,
    Observation,
)
from patients.models import PatientProfile


SERIALIZER_MODELS = (
    PatientProfile,
    Condition,
    Allergy,
    Medication,
    Immunization,
    Observation,
    Encounter,
)
ALLERGY_CATEGORIES = {"food", "medication", "environment", "biologic"}
ALLERGY_CRITICALITIES = {"low", "high", "unable-to-assess"}
ALLERGY_REACTION_SEVERITIES = {"mild", "moderate", "severe"}
ENCOUNTER_STATUSES = {
    "planned",
    "arrived",
    "triaged",
    "in-progress",
    "onleave",
    "finished",
    "cancelled",
    "entered-in-error",
    "unknown",
}
MEDICATION_STATEMENT_STATUSES = {
    "active",
    "completed",
    "entered-in-error",
    "intended",
    "stopped",
    "on-hold",
    "unknown",
    "not-taken",
}
PATIENT_GENDERS = {"male", "female", "other", "unknown"}


def serialize_model_resource(obj):
    serializer = SERIALIZERS.get(obj.__class__)
    if not serializer:
        return None
    return serializer(obj)


def patient_reference(patient):
    return {"reference": f"Patient/{patient.pk}", "display": str(patient)}


def codeable_text(text):
    return {"text": text} if text else None


def compact(resource):
    if isinstance(resource, dict):
        cleaned = {key: compact(value) for key, value in resource.items()}
        return {
            key: value
            for key, value in cleaned.items()
            if value not in (None, "", [], {})
        }
    if isinstance(resource, list):
        cleaned = [compact(item) for item in resource]
        return [item for item in cleaned if item not in (None, "", [], {})]
    return resource


def allowed_code(value, allowed, default=None):
    normalized = (value or "").strip().lower()
    if normalized in allowed:
        return normalized
    return default


def serialize_patient(patient):
    gender = allowed_code(patient.sex_at_birth, PATIENT_GENDERS)
    return compact(
        {
            "resourceType": "Patient",
            "id": str(patient.pk),
            "name": [{"family": patient.last_name, "given": [patient.first_name]}],
            "birthDate": patient.date_of_birth.isoformat()
            if patient.date_of_birth
            else None,
            "gender": gender,
            "telecom": [
                {"system": "phone", "value": patient.phone},
                {"system": "email", "value": patient.email},
            ],
            "address": [
                {
                    "line": [
                        line
                        for line in [patient.address_line_1, patient.address_line_2]
                        if line
                    ],
                    "city": patient.city,
                    "state": patient.state,
                    "postalCode": patient.postal_code,
                    "country": patient.country,
                }
            ],
        }
    )


def serialize_condition(condition):
    return compact(
        {
            "resourceType": "Condition",
            "id": str(condition.pk),
            "subject": patient_reference(condition.patient),
            "code": codeable_text(condition.name),
            "clinicalStatus": codeable_text(condition.clinical_status),
            "onsetDateTime": condition.onset_date.isoformat()
            if condition.onset_date
            else None,
            "abatementDateTime": condition.abatement_date.isoformat()
            if condition.abatement_date
            else None,
            "note": [{"text": condition.notes}],
        }
    )


def serialize_allergy(allergy):
    category = allowed_code(allergy.category, ALLERGY_CATEGORIES)
    criticality = allowed_code(allergy.criticality, ALLERGY_CRITICALITIES)
    severity = allowed_code(allergy.severity, ALLERGY_REACTION_SEVERITIES)
    return compact(
        {
            "resourceType": "AllergyIntolerance",
            "id": str(allergy.pk),
            "patient": patient_reference(allergy.patient),
            "code": codeable_text(allergy.substance),
            "category": [category] if category else [],
            "criticality": criticality,
            "reaction": [
                {
                    "manifestation": [codeable_text(allergy.reaction)],
                    "severity": severity,
                }
            ],
            "note": [{"text": allergy.notes}],
        }
    )


def serialize_medication(medication):
    status = allowed_code(
        medication.status, MEDICATION_STATEMENT_STATUSES, default="unknown"
    )
    return compact(
        {
            "resourceType": "MedicationStatement",
            "id": str(medication.pk),
            "status": status,
            "subject": patient_reference(medication.patient),
            "medicationCodeableConcept": codeable_text(medication.name),
            "dosage": [
                {
                    "text": medication.dosage_text,
                    "route": codeable_text(medication.route),
                    "timing": {"code": codeable_text(medication.frequency)},
                }
            ],
            "effectivePeriod": {
                "start": medication.start_date.isoformat()
                if medication.start_date
                else None,
                "end": medication.end_date.isoformat() if medication.end_date else None,
            },
            "reasonCode": [codeable_text(medication.indication)],
            "note": [{"text": medication.notes}],
        }
    )


def serialize_immunization(immunization):
    return compact(
        {
            "resourceType": "Immunization",
            "id": str(immunization.pk),
            "status": "completed",
            "patient": patient_reference(immunization.patient),
            "vaccineCode": codeable_text(immunization.vaccine_name),
            "occurrenceDateTime": immunization.occurrence_date.isoformat()
            if immunization.occurrence_date
            else None,
            "lotNumber": immunization.lot_number,
            "manufacturer": {"display": immunization.manufacturer},
            "performer": [{"actor": {"display": immunization.performer}}],
            "note": [{"text": immunization.notes}],
        }
    )


def serialize_observation(observation):
    return compact(
        {
            "resourceType": "Observation",
            "id": str(observation.pk),
            "status": "final",
            "category": [codeable_text(observation.get_category_display())],
            "code": codeable_text(observation.name),
            "subject": patient_reference(observation.patient),
            "effectiveDateTime": observation.effective_datetime.isoformat()
            if observation.effective_datetime
            else None,
            "valueQuantity": {
                "value": float(observation.value_quantity)
                if observation.value_quantity is not None
                else None,
                "unit": observation.unit,
            },
            "valueString": observation.value_string
            if observation.value_quantity is None
            else "",
            "interpretation": [codeable_text(observation.interpretation)],
            "referenceRange": [{"text": observation.reference_range}],
            "note": [{"text": observation.notes}],
        }
    )


def serialize_encounter(encounter):
    status = allowed_code(encounter.status, ENCOUNTER_STATUSES, default="unknown")
    return compact(
        {
            "resourceType": "Encounter",
            "id": str(encounter.pk),
            "status": status,
            "class": encounter_class(encounter),
            "type": [codeable_text(encounter.encounter_type)],
            "subject": patient_reference(encounter.patient),
            "period": {
                "start": encounter.start_time.isoformat()
                if encounter.start_time
                else None,
                "end": encounter.end_time.isoformat() if encounter.end_time else None,
            },
            "reasonCode": [codeable_text(encounter.reason)],
            "location": [{"location": {"display": encounter.facility_name}}],
            "participant": [{"individual": {"display": encounter.provider_name}}],
        }
    )


def encounter_class(encounter):
    text = (encounter.encounter_type or "").lower()
    if "emergency" in text or "ed" in text:
        code = "EMER"
        display = "emergency"
    elif "inpatient" in text:
        code = "IMP"
        display = "inpatient encounter"
    elif "virtual" in text or "tele" in text:
        code = "VR"
        display = "virtual"
    else:
        code = "AMB"
        display = "ambulatory"
    return {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": code,
        "display": display,
    }


SERIALIZERS = {
    PatientProfile: serialize_patient,
    Condition: serialize_condition,
    Allergy: serialize_allergy,
    Medication: serialize_medication,
    Immunization: serialize_immunization,
    Observation: serialize_observation,
    Encounter: serialize_encounter,
}
