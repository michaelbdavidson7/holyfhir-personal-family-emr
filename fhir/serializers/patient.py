
def patient_to_fhir(patient):
    return {
        "resourceType": "Patient",
        "id": f"patient-{patient.id}",
        "name": [
            {
                "family": patient.last_name,
                "given": [patient.first_name],
            }
        ],
        "birthDate": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        "telecom": [
            {"system": "phone", "value": patient.phone},
            {"system": "email", "value": patient.email},
        ],
        "address": [
            {
                "line": [patient.address_line_1, patient.address_line_2] if patient.address_line_2 else [patient.address_line_1],
                "city": patient.city,
                "state": patient.state,
                "postalCode": patient.postal_code,
                "country": patient.country,
            }
        ],
    }