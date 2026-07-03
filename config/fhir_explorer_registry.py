"""FHIR Explorer resource registry.

Generated from FHIR_RESOURCE_SUPPORT.md.
Drop this into something like clinical/fhir_explorer_registry.py.
"""

from django.apps import apps
from django.urls import NoReverseMatch, reverse


FHIR_EXPLORER_GROUPS = [
    {
        "title": "Foundation / Conformance",
        "icon": "fas fa-server",
        "resources": [
            {
                "resource": "CapabilityStatement",
                "model": "clinical.CapabilityStatement",
                "description": "Technical server capability metadata.",
            },
            {
                "resource": "StructureDefinition",
                "model": "clinical.StructureDefinition",
                "description": "Profile/extension definitions.",
            },
            {
                "resource": "ImplementationGuide",
                "model": "clinical.ImplementationGuide",
                "description": "IG package metadata.",
            },
            {
                "resource": "SearchParameter",
                "model": "clinical.SearchParameter",
                "description": "Search metadata.",
            },
            {
                "resource": "MessageDefinition",
                "model": "clinical.MessageDefinition",
                "description": "Messaging definition.",
            },
            {
                "resource": "OperationDefinition",
                "model": "clinical.OperationDefinition",
                "description": "Operation metadata.",
            },
            {
                "resource": "CompartmentDefinition",
                "model": "clinical.CompartmentDefinition",
                "description": "Compartment metadata.",
            },
            {
                "resource": "StructureMap",
                "model": "clinical.StructureMap",
                "description": "Mapping definition.",
            },
            {
                "resource": "GraphDefinition",
                "model": "clinical.GraphDefinition",
                "description": "Resource graph definition.",
            },
            {
                "resource": "ExampleScenario",
                "model": "clinical.ExampleScenario",
                "description": "Documentation/example artifact.",
            },
        ],
    },
    {
        "title": "Foundation / Terminology",
        "icon": "fas fa-language",
        "resources": [
            {
                "resource": "CodeSystem",
                "model": "clinical.CodeSystem",
                "description": "Terminology definition.",
            },
            {
                "resource": "ValueSet",
                "model": "clinical.ValueSet",
                "description": "Terminology value set.",
            },
            {
                "resource": "ConceptMap",
                "model": "clinical.ConceptMap",
                "description": "Terminology mapping.",
            },
            {
                "resource": "NamingSystem",
                "model": "clinical.NamingSystem",
                "description": "Identifier namespace metadata.",
            },
            {
                "resource": "TerminologyCapabilities",
                "model": "clinical.TerminologyCapabilities",
                "description": "Terminology server capability metadata.",
            },
        ],
    },
    {
        "title": "Foundation / Security",
        "icon": "fas fa-shield-alt",
        "resources": [
            {
                "resource": "Provenance",
                "model": "clinical.Provenance",
                "description": "Useful for import/source trust and record history.",
            },
            {
                "resource": "AuditEvent",
                "model": "clinical.AuditEvent",
                "description": "Security/system audit event.",
            },
            {
                "resource": "Consent",
                "model": "clinical.Consent",
                "description": "Privacy, treatment, procedure, vaccine, and other consent directives.",
            },
        ],
    },
    {
        "title": "Foundation / Documents",
        "icon": "fas fa-file-alt",
        "resources": [
            {
                "resource": "Composition",
                "model": "clinical.Composition",
                "description": "Structured document sections; may map to ClinicalDocument/document sections.",
            },
            {
                "resource": "DocumentManifest",
                "model": "clinical.DocumentManifest",
                "description": "Document package/index; link to ClinicalDocument/DocumentReference.",
            },
            {
                "resource": "DocumentReference",
                "model": "documents.ClinicalDocument",
                "description": "Maps to ClinicalDocument; stores attachments and relationships.",
            },
        ],
    },
    {
        "title": "Foundation / Other",
        "icon": "fas fa-cubes",
        "resources": [
            {
                "resource": "CatalogEntry",
                "model": "clinical.CatalogEntry",
                "description": "Catalog metadata.",
            },
            {
                "resource": "Basic",
                "model": "clinical.Basic",
                "description": "Generic extension resource.",
            },
            {
                "resource": "Binary",
                "model": "clinical.BinaryResource",
                "description": "Needed for external/inline document or media content.",
            },
            {
                "resource": "Linkage",
                "model": "clinical.Linkage",
                "description": "Resource identity/linkage metadata.",
            },
            {
                "resource": "MessageHeader",
                "model": "clinical.MessageHeader",
                "description": "Messaging envelope.",
            },
            {
                "resource": "OperationOutcome",
                "model": "clinical.OperationOutcome",
                "description": "Error/result payload.",
            },
            {
                "resource": "Parameters",
                "model": "clinical.Parameters",
                "description": "Operation parameters.",
            },
            {
                "resource": "Subscription",
                "model": "clinical.Subscription",
                "description": "Server subscription metadata.",
            },
        ],
    },
    {
        "title": "Base / Individuals",
        "icon": "fas fa-users",
        "resources": [
            {
                "resource": "Patient",
                "model": "patients.PatientProfile",
                "description": "Maps to PatientProfile.",
            },
            {
                "resource": "Practitioner",
                "model": "clinical.Practitioner",
                "description": "Directory resource.",
            },
            {
                "resource": "PractitionerRole",
                "model": "clinical.PractitionerRole",
                "description": "Links practitioner, organization, specialty, and locations.",
            },
            {
                "resource": "RelatedPerson",
                "model": "clinical.RelatedPerson",
                "description": "Caregivers, family, proxies, and other patient-related people.",
            },
            {
                "resource": "Person",
                "model": "clinical.Person",
                "description": "Identity reconciliation across Patient, Practitioner, RelatedPerson, and Person records.",
            },
            {
                "resource": "Group",
                "model": "clinical.FHIRGroup",
                "description": "Cohorts/groups with managing entity, characteristics, and member links.",
            },
        ],
    },
    {
        "title": "Base / Entities #1",
        "icon": "fas fa-hospital",
        "resources": [
            {
                "resource": "Organization",
                "model": "clinical.Organization",
                "description": "Directory resource.",
            },
            {
                "resource": "OrganizationAffiliation",
                "model": "clinical.OrganizationAffiliation",
                "description": "Organization-to-organization/service relationships.",
            },
            {
                "resource": "HealthcareService",
                "model": "clinical.HealthcareService",
                "description": "Services offered by organizations/locations.",
            },
            {
                "resource": "Endpoint",
                "model": "clinical.Endpoint",
                "description": "Technical endpoint; likely interop/directory support.",
            },
            {
                "resource": "Location",
                "model": "clinical.Location",
                "description": "Directory/site resource.",
            },
        ],
    },
    {
        "title": "Base / Entities #2",
        "icon": "fas fa-boxes",
        "resources": [
            {
                "resource": "Substance",
                "model": "clinical.Substance",
                "description": "Useful for allergies/medications/labs; likely catalog-style.",
            },
            {
                "resource": "BiologicallyDerivedProduct",
                "model": "clinical.BiologicallyDerivedProduct",
                "description": "Blood/tissue/product details.",
            },
            {
                "resource": "Device",
                "model": "clinical.Device",
                "description": "Patient/device inventory and references.",
            },
            {
                "resource": "DeviceMetric",
                "model": "clinical.DeviceMetric",
                "description": "Device measurement channels/configuration.",
            },
        ],
    },
    {
        "title": "Base / Workflow Management",
        "icon": "fas fa-tasks",
        "resources": [
            {
                "resource": "Task",
                "model": "clinical.Task",
                "description": "Workflow/reminders/imported tasks.",
            },
            {
                "resource": "Appointment",
                "model": "clinical.Appointment",
                "description": "Scheduling/calendar support.",
            },
            {
                "resource": "AppointmentResponse",
                "model": "clinical.AppointmentResponse",
                "description": "Appointment participant response.",
            },
            {
                "resource": "Schedule",
                "model": "clinical.Schedule",
                "description": "Availability schedule.",
            },
            {
                "resource": "Slot",
                "model": "clinical.Slot",
                "description": "Bookable time slot.",
            },
            {
                "resource": "VerificationResult",
                "model": "clinical.VerificationResult",
                "description": "Verification metadata.",
            },
            {
                "resource": "Encounter",
                "model": "clinical.Encounter",
                "description": "Visit/action record.",
            },
            {
                "resource": "EpisodeOfCare",
                "model": "clinical.EpisodeOfCare",
                "description": "Larger care episode grouping.",
            },
            {
                "resource": "Flag",
                "model": "clinical.Flag",
                "description": "Patient warnings/alerts.",
            },
            {
                "resource": "List",
                "model": "clinical.FHIRList",
                "description": "FHIR lists/groupings of resources.",
            },
            {
                "resource": "Library",
                "model": "clinical.Library",
                "description": "Knowledge artifact.",
            },
        ],
    },
    {
        "title": "Clinical / Summary",
        "icon": "fas fa-notes-medical",
        "resources": [
            {
                "resource": "AllergyIntolerance",
                "model": "clinical.Allergy",
                "description": "Maps to Allergy; orphan patient strategy still needed.",
            },
            {
                "resource": "AdverseEvent",
                "model": "clinical.AdverseEvent",
                "description": "Harmful events and contributors.",
            },
            {
                "resource": "Condition",
                "model": "clinical.Condition",
                "description": "Problems/diagnoses.",
            },
            {
                "resource": "Procedure",
                "model": "clinical.Procedure",
                "description": "Completed procedures/actions.",
            },
            {
                "resource": "FamilyMemberHistory",
                "model": "clinical.FamilyMemberHistory",
                "description": "Family history with repeating condition details.",
            },
            {
                "resource": "ClinicalImpression",
                "model": "clinical.ClinicalImpression",
                "description": "Clinician assessment/synthesis, findings, and investigations.",
            },
            {
                "resource": "DetectedIssue",
                "model": "clinical.DetectedIssue",
                "description": "Safety/quality issues such as interactions or duplicate therapy.",
            },
        ],
    },
    {
        "title": "Clinical / Diagnostics",
        "icon": "fas fa-vial",
        "resources": [
            {
                "resource": "Observation",
                "model": "clinical.Observation",
                "description": "Vitals/labs/results.",
            },
            {
                "resource": "Media",
                "model": "clinical.Media",
                "description": "Clinical images/photos/media.",
            },
            {
                "resource": "DiagnosticReport",
                "model": "clinical.DiagnosticReport",
                "description": "Diagnostic reports with encounter, requests, specimens, observations, performers, interpreters, and presented forms.",
            },
            {
                "resource": "Specimen",
                "model": "clinical.Specimen",
                "description": "Lab specimen details.",
            },
            {
                "resource": "BodyStructure",
                "model": "clinical.BodyStructure",
                "description": "Anatomical/body-site detail.",
            },
            {
                "resource": "ImagingStudy",
                "model": "clinical.ImagingStudy",
                "description": "Imaging study/series/instance data.",
            },
            {
                "resource": "QuestionnaireResponse",
                "model": "clinical.QuestionnaireResponse",
                "description": "Patient-entered forms and assessments.",
            },
            {
                "resource": "MolecularSequence",
                "model": "clinical.MolecularSequence",
                "description": "Genomics sequence, variant, repository, and quality details.",
            },
        ],
    },
    {
        "title": "Clinical / Medications",
        "icon": "fas fa-pills",
        "resources": [
            {
                "resource": "MedicationRequest",
                "model": "clinical.Medication",
                "description": "Currently maps into local Medication.",
            },
            {
                "resource": "MedicationAdministration",
                "model": "clinical.MedicationAdministration",
                "description": "Administered medication event.",
            },
            {
                "resource": "MedicationDispense",
                "model": "clinical.MedicationDispense",
                "description": "Pharmacy/supply dispense event.",
            },
            {
                "resource": "MedicationStatement",
                "model": "clinical.Medication",
                "description": "Currently maps into local Medication.",
            },
            {
                "resource": "Medication",
                "model": "clinical.MedicationCatalog",
                "description": "Standalone medication catalog/details; maps to MedicationCatalog, separate from requests/statements.",
            },
            {
                "resource": "MedicationKnowledge",
                "model": "clinical.MedicationKnowledge",
                "description": "Drug knowledge/catalog metadata, ingredients, monitoring, and classifications.",
            },
            {
                "resource": "Immunization",
                "model": "clinical.Immunization",
                "description": "Vaccination records.",
            },
            {
                "resource": "ImmunizationEvaluation",
                "model": "clinical.ImmunizationEvaluation",
                "description": "Immunization validity/status evaluation.",
            },
            {
                "resource": "ImmunizationRecommendation",
                "model": "clinical.ImmunizationRecommendation",
                "description": "Vaccine forecast/recommendations.",
            },
        ],
    },
    {
        "title": "Clinical / Care Provision",
        "icon": "fas fa-heartbeat",
        "resources": [
            {
                "resource": "CarePlan",
                "model": "clinical.CarePlan",
                "description": "Care plans with conditions/care teams.",
            },
            {
                "resource": "CareTeam",
                "model": "clinical.CareTeam",
                "description": "Care teams and participants.",
            },
            {
                "resource": "Goal",
                "model": "clinical.Goal",
                "description": "Patient/care goals with addressed concerns, targets, and outcomes.",
            },
            {
                "resource": "ServiceRequest",
                "model": "clinical.ServiceRequest",
                "description": "Orders/referrals/requested services.",
            },
            {
                "resource": "NutritionOrder",
                "model": "clinical.NutritionOrder",
                "description": "Dietary/oral/enteral/supplement orders.",
            },
            {
                "resource": "VisionPrescription",
                "model": "clinical.VisionPrescription",
                "description": "Vision prescription details.",
            },
            {
                "resource": "RiskAssessment",
                "model": "clinical.RiskAssessment",
                "description": "Risk-assessment records with basis records and mitigation notes.",
            },
            {
                "resource": "RequestGroup",
                "model": "clinical.RequestGroup",
                "description": "Grouped/conditional requests and plans.",
            },
        ],
    },
    {
        "title": "Clinical / Request & Response",
        "icon": "fas fa-exchange-alt",
        "resources": [
            {
                "resource": "DeviceRequest",
                "model": "clinical.DeviceRequest",
                "description": "Device orders/requests with reasons, performers, and timing.",
            },
            {
                "resource": "DeviceUseStatement",
                "model": "clinical.DeviceUseStatement",
                "description": "Patient/device usage history.",
            },
            {
                "resource": "GuidanceResponse",
                "model": "clinical.GuidanceResponse",
                "description": "Decision-support response.",
            },
            {
                "resource": "SupplyRequest",
                "model": "clinical.SupplyRequest",
                "description": "Supply request.",
            },
            {
                "resource": "SupplyDelivery",
                "model": "clinical.SupplyDelivery",
                "description": "Supply delivery event.",
            },
        ],
    },
    {
        "title": "Financial / Support",
        "icon": "fas fa-id-card-alt",
        "resources": [
            {
                "resource": "Coverage",
                "model": "clinical.Coverage",
                "description": "Insurance coverage, subscriber IDs, payer details, and benefit classifications.",
            },
            {
                "resource": "CoverageEligibilityRequest",
                "model": "clinical.CoverageEligibilityRequest",
                "description": "Eligibility request.",
            },
            {
                "resource": "CoverageEligibilityResponse",
                "model": "clinical.CoverageEligibilityResponse",
                "description": "Eligibility response.",
            },
            {
                "resource": "EnrollmentRequest",
                "model": "clinical.EnrollmentRequest",
                "description": "Enrollment request.",
            },
            {
                "resource": "EnrollmentResponse",
                "model": "clinical.EnrollmentResponse",
                "description": "Enrollment response.",
            },
        ],
    },
    {
        "title": "Financial / Billing",
        "icon": "fas fa-file-invoice-dollar",
        "resources": [
            {
                "resource": "Claim",
                "model": "clinical.Claim",
                "description": "Claims support if adding insurance/finance.",
            },
            {
                "resource": "ClaimResponse",
                "model": "clinical.ClaimResponse",
                "description": "Claim adjudication response.",
            },
            {
                "resource": "Invoice",
                "model": "clinical.Invoice",
                "description": "Billing invoice.",
            },
        ],
    },
    {
        "title": "Financial / Payment",
        "icon": "fas fa-money-check-alt",
        "resources": [
            {
                "resource": "PaymentNotice",
                "model": "clinical.PaymentNotice",
                "description": "Payment notification.",
            },
            {
                "resource": "PaymentReconciliation",
                "model": "clinical.PaymentReconciliation",
                "description": "Payment reconciliation.",
            },
        ],
    },
    {
        "title": "Financial / General",
        "icon": "fas fa-wallet",
        "resources": [
            {
                "resource": "Account",
                "model": "clinical.Account",
                "description": "Billing/account grouping.",
            },
            {
                "resource": "ChargeItem",
                "model": "clinical.ChargeItem",
                "description": "Charge line item.",
            },
            {
                "resource": "ChargeItemDefinition",
                "model": "clinical.ChargeItemDefinition",
                "description": "Charge item definition.",
            },
            {
                "resource": "Contract",
                "model": "clinical.Contract",
                "description": "Contract/legal agreement.",
            },
            {
                "resource": "ExplanationOfBenefit",
                "model": "clinical.ExplanationOfBenefit",
                "description": "EOB/claims summary; useful for personal records.",
            },
            {
                "resource": "InsurancePlan",
                "model": "clinical.InsurancePlan",
                "description": "Insurance plan details.",
            },
        ],
    },
    {
        "title": "Specialized / Public Health & Research",
        "icon": "fas fa-flask",
        "resources": [
            {
                "resource": "ResearchStudy",
                "model": "clinical.ResearchStudy",
                "description": "Optional research participation area.",
            },
            {
                "resource": "ResearchSubject",
                "model": "clinical.ResearchSubject",
                "description": "Patient participation in a study.",
            },
        ],
    },
    {
        "title": "Specialized / Definitional Artifacts",
        "icon": "fas fa-book-medical",
        "resources": [
            {
                "resource": "ActivityDefinition",
                "model": "clinical.ActivityDefinition",
                "description": "Knowledge artifact.",
            },
            {
                "resource": "DeviceDefinition",
                "model": "clinical.DeviceDefinition",
                "description": "Device catalog/definition.",
            },
            {
                "resource": "EventDefinition",
                "model": "clinical.EventDefinition",
                "description": "Knowledge artifact.",
            },
            {
                "resource": "ObservationDefinition",
                "model": "clinical.ObservationDefinition",
                "description": "Observation catalog/definition.",
            },
            {
                "resource": "PlanDefinition",
                "model": "clinical.PlanDefinition",
                "description": "Care plan definition/knowledge artifact.",
            },
            {
                "resource": "Questionnaire",
                "model": "clinical.Questionnaire",
                "description": "Form definitions.",
            },
            {
                "resource": "SpecimenDefinition",
                "model": "clinical.SpecimenDefinition",
                "description": "Specimen catalog/definition.",
            },
        ],
    },
    {
        "title": "Specialized / Evidence-Based Medicine",
        "icon": "fas fa-microscope",
        "resources": [
            {
                "resource": "ResearchDefinition",
                "model": "clinical.ResearchDefinition",
                "description": "Evidence/research metadata.",
            },
            {
                "resource": "ResearchElementDefinition",
                "model": "clinical.ResearchElementDefinition",
                "description": "Evidence/research metadata.",
            },
            {
                "resource": "Evidence",
                "model": "clinical.Evidence",
                "description": "Evidence artifact.",
            },
            {
                "resource": "EvidenceVariable",
                "model": "clinical.EvidenceVariable",
                "description": "Evidence variable definition.",
            },
            {
                "resource": "EffectEvidenceSynthesis",
                "model": "clinical.EffectEvidenceSynthesis",
                "description": "Evidence synthesis.",
            },
            {
                "resource": "RiskEvidenceSynthesis",
                "model": "clinical.RiskEvidenceSynthesis",
                "description": "Risk evidence synthesis.",
            },
        ],
    },
    {
        "title": "Specialized / Quality Reporting & Testing",
        "icon": "fas fa-clipboard-check",
        "resources": [
            {
                "resource": "Measure",
                "model": "clinical.Measure",
                "description": "Quality measure definition.",
            },
            {
                "resource": "MeasureReport",
                "model": "clinical.MeasureReport",
                "description": "Quality measure report.",
            },
            {
                "resource": "TestScript",
                "model": "clinical.TestScript",
                "description": "FHIR testing artifact.",
            },
            {
                "resource": "TestReport",
                "model": "clinical.TestReport",
                "description": "FHIR testing artifact.",
            },
        ],
    },
    {
        "title": "Specialized / Medication Definition",
        "icon": "fas fa-capsules",
        "resources": [
            {
                "resource": "MedicinalProduct",
                "model": "clinical.MedicinalProduct",
                "description": "Medication/product definition.",
            },
            {
                "resource": "MedicinalProductAuthorization",
                "model": "clinical.MedicinalProductAuthorization",
                "description": "Medication/product definition.",
            },
            {
                "resource": "MedicinalProductContraindication",
                "model": "clinical.MedicinalProductContraindication",
                "description": "Medication/product definition.",
            },
            {
                "resource": "MedicinalProductIndication",
                "model": "clinical.MedicinalProductIndication",
                "description": "Medication/product definition.",
            },
            {
                "resource": "MedicinalProductIngredient",
                "model": "clinical.MedicinalProductIngredient",
                "description": "Medication/product definition.",
            },
            {
                "resource": "MedicinalProductInteraction",
                "model": "clinical.MedicinalProductInteraction",
                "description": "Medication/product definition.",
            },
            {
                "resource": "MedicinalProductManufactured",
                "model": "clinical.MedicinalProductManufactured",
                "description": "Medication/product definition.",
            },
            {
                "resource": "MedicinalProductPackaged",
                "model": "clinical.MedicinalProductPackaged",
                "description": "Medication/product definition.",
            },
            {
                "resource": "MedicinalProductPharmaceutical",
                "model": "clinical.MedicinalProductPharmaceutical",
                "description": "Medication/product definition.",
            },
            {
                "resource": "MedicinalProductUndesirableEffect",
                "model": "clinical.MedicinalProductUndesirableEffect",
                "description": "Medication/product definition.",
            },
            {
                "resource": "SubstanceNucleicAcid",
                "model": "clinical.SubstanceNucleicAcid",
                "description": "Substance definition.",
            },
            {
                "resource": "SubstancePolymer",
                "model": "clinical.SubstancePolymer",
                "description": "Substance definition.",
            },
            {
                "resource": "SubstanceProtein",
                "model": "clinical.SubstanceProtein",
                "description": "Substance definition.",
            },
            {
                "resource": "SubstanceReferenceInformation",
                "model": "clinical.SubstanceReferenceInformation",
                "description": "Substance definition.",
            },
            {
                "resource": "SubstanceSpecification",
                "model": "clinical.SubstanceSpecification",
                "description": "Substance definition.",
            },
            {
                "resource": "SubstanceSourceMaterial",
                "model": "clinical.SubstanceSourceMaterial",
                "description": "Substance definition.",
            },
        ],
    },
]


def _split_model_path(model_path):
    app_label, model_name = model_path.split(".", 1)
    return app_label, model_name


def _get_model(model_path):
    app_label, model_name = _split_model_path(model_path)
    return apps.get_model(app_label, model_name)


def _admin_changelist_url(model):
    route_name = f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
    try:
        return reverse(route_name)
    except NoReverseMatch:
        return None


def build_fhir_explorer_sections():
    """Return directory_sections for templates/admin/fhir_explorer.html.

    Shape matches your existing directory_sections/card template contract.
    Any model that does not exist or is not registered in admin is still shown,
    but with url=None and count=None so the template can handle it gracefully.
    """
    sections = []

    for group in FHIR_EXPLORER_GROUPS:
        cards = []

        for item in group["resources"]:
            model = None
            url = None
            count = None
            admin_model_name = None
            app_label = None
            model_name = None
            has_model = False
            has_admin_url = False

            try:
                model = _get_model(item["model"])
                app_label = model._meta.app_label
                model_name = model._meta.model_name
                admin_model_name = f"{app_label}_{model_name}"
                has_model = True
                count = model.objects.count()
                url = _admin_changelist_url(model)
                has_admin_url = url is not None
            except Exception:
                pass

            cards.append(
                {
                    "title": item["resource"],
                    "resource_type": item["resource"],
                    "model_path": item["model"],
                    "app_label": app_label,
                    "model_name": model_name,
                    "admin_model_name": admin_model_name,
                    "description": item["description"],
                    "url": url,
                    "icon": group["icon"],
                    "count": count,
                    "count_label": "record",
                    "has_model": has_model,
                    "has_admin_url": has_admin_url,
                    "support_status": "First-class",
                }
            )

        sections.append(
            {
                "title": group["title"],
                "icon": group["icon"],
                "cards": cards,
            }
        )

    return sections
