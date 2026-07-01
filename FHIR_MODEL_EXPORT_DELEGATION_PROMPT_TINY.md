Create models only for: Patient, Practitioner, Organization, Encounter, Observation.

Use `fhir/schema/r4/fhir.schema.json` as the local FHIR R4 source of truth for resource names, required fields, field types, and allowed enum/code values.
Use existing project style.
Do not invent fields.
Only edit app/fhir_models/core.py.
Run tests after.
Stop after those 5 resources.
