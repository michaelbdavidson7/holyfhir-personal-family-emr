# Local LLM Task: Extend Django Model -> FHIR Export Serializers

We are working in a Django personal EMR/FHIR app.

## Goal
Continue implementing real Django model to FHIR JSON export serializers.

The first-pass serializer framework exists in:

- `fhir/serializers.py`
- `fhir/exporter.py`
- `fhir/forms.py`
- `fhir/views.py`
- `templates/admin/fhir_export.html`

The exporter now has a checkbox: **Include current app records as FHIR**. When enabled, `build_fhir_export_zip(..., include_model_serialized=True)` serializes supported Django models first, then also includes snapshot fallback resources.

## Current Supported Model Serializers
Implemented in `fhir/serializers.py`:

- `PatientProfile` -> `Patient`
- `Condition` -> `Condition`
- `Allergy` -> `AllergyIntolerance`
- `Medication` -> `MedicationStatement`
- `Immunization` -> `Immunization`
- `Observation` -> `Observation`
- `Encounter` -> `Encounter`

## Pattern To Follow
Add a serializer function:

```python
def serialize_goal(goal):
    return compact(
        {
            "resourceType": "Goal",
            "id": str(goal.pk),
            "subject": patient_reference(goal.patient),
            "description": codeable_text(goal.description),
        }
    )
```

Then register it:

```python
SERIALIZER_MODELS = (
    ...,
    Goal,
)

SERIALIZERS = {
    ...,
    Goal: serialize_goal,
}
```

Use helpers already present:

- `compact(resource)` removes empty values.
- `patient_reference(patient)` creates `Patient/<pk>` references.
- `codeable_text(text)` creates simple CodeableConcept text fields.

## Important Rules
- Keep serializers conservative. Prefer valid basic FHIR over clever/incomplete over-mapping.
- Do not delete snapshot fallback behavior.
- Do not serialize unsupported fields as random extensions yet unless asked.
- Avoid migrations. This should be serializer/export code only.
- Add or update tests in `fhir/tests.py`.

## Good Next Resources
Prioritize patient-linked clinical resources:

1. `Procedure` -> `Procedure`
2. `CareTeam` -> `CareTeam`
3. `CarePlan` -> `CarePlan`
4. `DiagnosticReport` -> `DiagnosticReport`
5. `DocumentReference`/`ClinicalDocument` -> `DocumentReference`
6. `ServiceRequest` -> `ServiceRequest`
7. `Goal` -> `Goal`
8. `RiskAssessment` -> `RiskAssessment`
9. `FamilyMemberHistory` -> `FamilyMemberHistory`
10. `RelatedPerson` -> `RelatedPerson`

## Verification
Run:

```bash
venv\Scripts\python.exe manage.py check
venv\Scripts\python.exe manage.py test fhir
venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```
