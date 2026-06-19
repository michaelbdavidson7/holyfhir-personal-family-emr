from django.db import models
from patients.models import PatientProfile


class Condition(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="conditions")
    name = models.CharField(max_length=255)
    icd10_code = models.CharField(max_length=20, blank=True)
    snomed_code = models.CharField(max_length=30, blank=True)
    clinical_status = models.CharField(max_length=30, blank=True)  # active, resolved, inactive
    onset_date = models.DateField(null=True, blank=True)
    abatement_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Allergy(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="allergies")
    substance = models.CharField(max_length=255)
    rxnorm_code = models.CharField(max_length=30, blank=True)
    snomed_code = models.CharField(max_length=30, blank=True)
    category = models.CharField(max_length=50, blank=True)  # food, medication, environment
    criticality = models.CharField(max_length=20, blank=True)  # low, high, unable-to-assess
    reaction = models.CharField(max_length=255, blank=True)
    severity = models.CharField(max_length=20, blank=True)  # mild, moderate, severe
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Allergies"

    def __str__(self):
        return self.substance


class Medication(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="medications")
    name = models.CharField(max_length=255)
    rxnorm_code = models.CharField(max_length=30, blank=True)
    dosage_text = models.CharField(max_length=255, blank=True)
    route = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, blank=True)  # active, stopped, completed
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    prescriber = models.CharField(max_length=255, blank=True)
    indication = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Immunization(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="immunizations")
    vaccine_name = models.CharField(max_length=255)
    cvx_code = models.CharField(max_length=20, blank=True)
    occurrence_date = models.DateField(null=True, blank=True)
    lot_number = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    performer = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.vaccine_name


class Observation(models.Model):
    OBSERVATION_TYPES = [
        ("vital", "Vital"),
        ("lab", "Lab"),
        ("other", "Other"),
    ]

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="observations")
    specimen = models.ForeignKey(
        "Specimen",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations",
    )
    device = models.ForeignKey(
        "Device",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations",
    )
    category = models.CharField(max_length=20, choices=OBSERVATION_TYPES, default="other")
    name = models.CharField(max_length=255)
    loinc_code = models.CharField(max_length=30, blank=True)

    value_string = models.CharField(max_length=255, blank=True)
    value_quantity = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True)

    effective_datetime = models.DateTimeField(null=True, blank=True)
    interpretation = models.CharField(max_length=50, blank=True)  # high, low, normal
    reference_range = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vitals & Lab Result"
        verbose_name_plural = "Vitals & Labs"

    def __str__(self):
        return self.name


class Specimen(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="specimens")
    parent_specimens = models.ManyToManyField("self", blank=True, symmetrical=False, related_name="child_specimens")
    accession_identifier = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, blank=True)
    specimen_type = models.CharField(max_length=255, blank=True)
    received_time = models.DateTimeField(null=True, blank=True)
    collected_datetime = models.DateTimeField(null=True, blank=True)
    collection_method = models.CharField(max_length=255, blank=True)
    body_site = models.CharField(max_length=255, blank=True)
    collector_display = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.specimen_type or self.accession_identifier or f"Specimen #{self.pk}"


class Encounter(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="encounters")
    episodes_of_care = models.ManyToManyField("EpisodeOfCare", blank=True, related_name="encounters")
    encounter_type = models.CharField(max_length=100, blank=True)  # office visit, ED, inpatient
    status = models.CharField(max_length=30, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    provider_name = models.CharField(max_length=255, blank=True)
    facility_name = models.CharField(max_length=255, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Visit"
        verbose_name_plural = "Visits"

    def __str__(self):
        return self.encounter_type or self.reason or f"Visit #{self.pk}"


class Device(models.Model):
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="devices",
        null=True,
        blank=True,
    )
    owner = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="devices",
    )
    location = models.ForeignKey(
        "Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="devices",
    )
    display_name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=30, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    model_number = models.CharField(max_length=255, blank=True)
    serial_number = models.CharField(max_length=255, blank=True)
    lot_number = models.CharField(max_length=255, blank=True)
    distinct_identifier = models.CharField(max_length=255, blank=True)
    udi_carrier = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name


class CareTeam(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="care_teams")
    managing_organizations = models.ManyToManyField(
        "Organization",
        blank=True,
        related_name="managed_care_teams",
    )
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=30, blank=True)
    category = models.CharField(max_length=255, blank=True)
    participants = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Care Team"
        verbose_name_plural = "Care Team"

    def __str__(self):
        return self.name


class CarePlan(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="care_plans")
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=30, blank=True)
    intent = models.CharField(max_length=30, blank=True)
    category = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    author_display = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    conditions = models.ManyToManyField(Condition, blank=True, related_name="care_plans")
    care_teams = models.ManyToManyField(CareTeam, blank=True, related_name="care_plans")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Care Plan"
        verbose_name_plural = "Care Plans"

    def __str__(self):
        return self.title


class FamilyMemberHistory(models.Model):
    """FHIR FamilyMemberHistory: significant health conditions in a person related to the patient."""

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="family_member_histories",
        help_text="FHIR patient: the patient whose family history this record describes.",
    )
    conditions = models.ManyToManyField(
        Condition,
        blank=True,
        related_name="family_member_histories",
        help_text="FHIR condition: patient Condition records that help represent or match the family history.",
    )
    status = models.CharField(
        max_length=30,
        blank=True,
        help_text="FHIR status: partial, completed, entered-in-error, or health-unknown.",
    )
    relationship = models.CharField(max_length=255, help_text="FHIR relationship: how this relative is related to the patient.")
    sex = models.CharField(max_length=30, blank=True, help_text="FHIR sex: recorded sex of the family member.")
    born_date = models.DateField(null=True, blank=True, help_text="FHIR bornDate: actual or approximate birth date.")
    born_text = models.CharField(max_length=255, blank=True, help_text="FHIR bornString/Period: textual birth details.")
    age_text = models.CharField(max_length=255, blank=True, help_text="FHIR age[x]: age or age range at the time recorded.")
    estimated_age = models.BooleanField(default=False, help_text="FHIR estimatedAge: whether the age is approximate.")
    deceased = models.BooleanField(null=True, blank=True, help_text="FHIR deceasedBoolean: whether the relative is deceased.")
    deceased_date = models.DateField(null=True, blank=True, help_text="FHIR deceasedDate: date of death when known.")
    deceased_text = models.CharField(max_length=255, blank=True, help_text="FHIR deceased[x]: age, range, or text about death.")
    reason = models.CharField(max_length=255, blank=True, help_text="FHIR reasonCode/reasonReference: why this history was recorded.")
    notes = models.TextField(blank=True, help_text="FHIR note: general notes about the related person.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Family Member History"
        verbose_name_plural = "Family Member Histories"

    def __str__(self):
        return self.relationship


class FamilyMemberHistoryCondition(models.Model):
    """FHIR FamilyMemberHistory.condition: a condition the related person had."""

    family_member_history = models.ForeignKey(
        FamilyMemberHistory,
        on_delete=models.CASCADE,
        related_name="condition_links",
        help_text="The family member history record this condition belongs to.",
    )
    condition = models.ForeignKey(
        Condition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="family_history_condition_links",
        help_text="Optional matching local Condition record.",
    )
    condition_text = models.CharField(max_length=255, help_text="FHIR code: condition suffered by the family member.")
    outcome = models.CharField(max_length=255, blank=True, help_text="FHIR outcome: result such as death or disability.")
    contributed_to_death = models.BooleanField(
        null=True,
        blank=True,
        help_text="FHIR contributedToDeath: whether this condition contributed to death.",
    )
    onset_text = models.CharField(max_length=255, blank=True, help_text="FHIR onset[x]: when the condition first appeared.")
    notes = models.TextField(blank=True, help_text="FHIR note: extra notes about this specific family condition.")

    def __str__(self):
        return self.condition_text


class ClinicalImpression(models.Model):
    """FHIR ClinicalImpression: a clinician's assessment and synthesis of patient findings."""

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="clinical_impressions",
        help_text="FHIR subject: patient who was assessed.",
    )
    encounter = models.ForeignKey(
        Encounter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clinical_impressions",
        help_text="FHIR encounter: visit or encounter where the assessment occurred.",
    )
    assessor_practitioner = models.ForeignKey(
        "Practitioner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clinical_impressions",
        help_text="FHIR assessor: clinician responsible for the assessment.",
    )
    assessor_role = models.ForeignKey(
        "PractitionerRole",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clinical_impressions",
        help_text="FHIR assessor: practitioner role used when the assessor is represented by role.",
    )
    conditions = models.ManyToManyField(
        Condition,
        blank=True,
        related_name="clinical_impressions",
        help_text="FHIR finding/problem references resolved to local Condition records.",
    )
    observations = models.ManyToManyField(
        Observation,
        blank=True,
        related_name="clinical_impressions",
        help_text="FHIR finding/investigation references resolved to local Observation records.",
    )
    problems = models.ManyToManyField(
        Condition,
        blank=True,
        related_name="clinical_impression_problem_refs",
        help_text="FHIR problem: conditions or problems considered during the assessment.",
    )
    investigations_observations = models.ManyToManyField(
        Observation,
        blank=True,
        related_name="clinical_impression_investigations",
        help_text="FHIR investigation.item: observations reviewed as part of the assessment.",
    )
    status = models.CharField(max_length=30, blank=True, help_text="FHIR status: state of the assessment.")
    description = models.TextField(blank=True, help_text="FHIR description: why the assessment was performed.")
    effective_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="FHIR effective[x]: time or period covered by the assessment.",
    )
    date = models.DateTimeField(null=True, blank=True, help_text="FHIR date: when the assessment was made.")
    protocol = models.TextField(blank=True, help_text="FHIR protocol: clinical protocol or guideline followed.")
    summary = models.TextField(blank=True, help_text="FHIR summary: narrative summary of the assessment.")
    prognosis = models.TextField(blank=True, help_text="FHIR prognosisCodeableConcept/prognosisReference: expected outcome.")
    notes = models.TextField(blank=True, help_text="FHIR note: clinical notes about the impression.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Clinical Impression"
        verbose_name_plural = "Clinical Impressions"

    def __str__(self):
        return self.description or self.summary or f"Clinical Impression #{self.pk}"


class ClinicalImpressionFinding(models.Model):
    """FHIR ClinicalImpression.finding: a relevant condition, observation, or coded finding."""

    clinical_impression = models.ForeignKey(
        ClinicalImpression,
        on_delete=models.CASCADE,
        related_name="finding_links",
        help_text="The clinical impression this finding belongs to.",
    )
    condition = models.ForeignKey(
        Condition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clinical_impression_findings",
        help_text="FHIR finding.itemReference resolved to a local Condition.",
    )
    observation = models.ForeignKey(
        Observation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clinical_impression_findings",
        help_text="FHIR finding.itemReference resolved to a local Observation.",
    )
    finding_text = models.CharField(max_length=255, blank=True, help_text="FHIR finding.itemCodeableConcept or display text.")
    basis = models.TextField(blank=True, help_text="FHIR basis: reason this finding is relevant.")

    def __str__(self):
        return self.finding_text or str(self.condition or self.observation or f"Finding #{self.pk}")


class DiagnosticReport(models.Model):
    """FHIR DiagnosticReport: diagnostic report context, results, conclusions, and issued forms."""

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="diagnostic_reports",
        help_text="FHIR subject: patient who the report is about.",
    )
    encounter = models.ForeignKey(
        "Encounter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="diagnostic_reports",
        help_text="FHIR encounter: care event associated with the report.",
    )
    care_plans = models.ManyToManyField(
        "CarePlan",
        blank=True,
        related_name="diagnostic_reports",
        help_text="FHIR basedOn: care plans that requested or relate to this report.",
    )
    service_requests = models.ManyToManyField(
        "ServiceRequest",
        blank=True,
        related_name="diagnostic_reports",
        help_text="FHIR basedOn: service requests or orders this report fulfills.",
    )
    specimens = models.ManyToManyField(
        "Specimen",
        blank=True,
        related_name="diagnostic_reports",
        help_text="FHIR specimen: specimens the report is based on.",
    )
    observations = models.ManyToManyField(
        Observation,
        blank=True,
        related_name="diagnostic_reports",
        help_text="FHIR result: observations included as atomic report results.",
    )
    performers_practitioners = models.ManyToManyField(
        "Practitioner",
        blank=True,
        related_name="performed_diagnostic_reports",
        help_text="FHIR performer: practitioners responsible for issuing the report.",
    )
    performers_roles = models.ManyToManyField(
        "PractitionerRole",
        blank=True,
        related_name="performed_diagnostic_reports",
        help_text="FHIR performer: practitioner roles responsible for issuing the report.",
    )
    performers_organizations = models.ManyToManyField(
        "Organization",
        blank=True,
        related_name="performed_diagnostic_reports",
        help_text="FHIR performer: organizations responsible for issuing the report.",
    )
    performers_care_teams = models.ManyToManyField(
        "CareTeam",
        blank=True,
        related_name="performed_diagnostic_reports",
        help_text="FHIR performer: care teams responsible for issuing the report.",
    )
    interpreter_practitioners = models.ManyToManyField(
        "Practitioner",
        blank=True,
        related_name="interpreted_diagnostic_reports",
        help_text="FHIR resultsInterpreter: practitioners responsible for interpreting results.",
    )
    interpreter_roles = models.ManyToManyField(
        "PractitionerRole",
        blank=True,
        related_name="interpreted_diagnostic_reports",
        help_text="FHIR resultsInterpreter: practitioner roles responsible for interpreting results.",
    )
    interpreter_organizations = models.ManyToManyField(
        "Organization",
        blank=True,
        related_name="interpreted_diagnostic_reports",
        help_text="FHIR resultsInterpreter: organizations responsible for interpreting results.",
    )
    interpreter_care_teams = models.ManyToManyField(
        "CareTeam",
        blank=True,
        related_name="interpreted_diagnostic_reports",
        help_text="FHIR resultsInterpreter: care teams responsible for interpreting results.",
    )
    presented_documents = models.ManyToManyField(
        "documents.ClinicalDocument",
        blank=True,
        related_name="diagnostic_reports",
        help_text="FHIR presentedForm: documents created from attached issued report content.",
    )
    status = models.CharField(max_length=30, blank=True, help_text="FHIR status: registered, partial, preliminary, final, etc.")
    category = models.CharField(max_length=255, blank=True, help_text="FHIR category: diagnostic service section.")
    code = models.CharField(max_length=255, help_text="FHIR code: name or code for this diagnostic report.")
    effective_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="FHIR effective[x]: clinically relevant date/time for the report.",
    )
    issued = models.DateTimeField(null=True, blank=True, help_text="FHIR issued: when this report version was released.")
    conclusion = models.TextField(blank=True, help_text="FHIR conclusion: clinical interpretation of test results.")
    conclusion_code = models.CharField(max_length=255, blank=True, help_text="FHIR conclusionCode: coded interpretation.")
    presented_form_summary = models.TextField(blank=True, help_text="FHIR presentedForm: summary of attachments that were not stored.")
    imaging_study_summary = models.TextField(blank=True, help_text="FHIR imagingStudy: unresolved imaging study references.")
    media_summary = models.TextField(blank=True, help_text="FHIR media: unresolved key image/media references.")
    notes = models.TextField(blank=True, help_text="FHIR note/text: additional imported report notes.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Diagnostic Report"
        verbose_name_plural = "Diagnostic Reports"

    def __str__(self):
        return self.code or f"Diagnostic Report #{self.pk}"


class DetectedIssue(models.Model):
    """FHIR DetectedIssue: an actual or potential clinical issue involving patient-specific actions."""

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="detected_issues",
        help_text="FHIR patient: patient whose care record contains the issue.",
    )
    author_practitioner = models.ForeignKey(
        "Practitioner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authored_detected_issues",
        help_text="FHIR author: practitioner who identified the issue.",
    )
    author_role = models.ForeignKey(
        "PractitionerRole",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authored_detected_issues",
        help_text="FHIR author: practitioner role that identified the issue.",
    )
    author_device = models.ForeignKey(
        "Device",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authored_detected_issues",
        help_text="FHIR author: device or decision-support system that identified the issue.",
    )
    implicated_conditions = models.ManyToManyField(
        Condition,
        blank=True,
        related_name="detected_issue_implications",
        help_text="FHIR implicated: condition resources involved in the issue.",
    )
    implicated_medications = models.ManyToManyField(
        Medication,
        blank=True,
        related_name="detected_issue_implications",
        help_text="FHIR implicated: medication request/statement resources involved in the issue.",
    )
    implicated_immunizations = models.ManyToManyField(
        Immunization,
        blank=True,
        related_name="detected_issue_implications",
        help_text="FHIR implicated: immunizations involved in the issue.",
    )
    implicated_observations = models.ManyToManyField(
        Observation,
        blank=True,
        related_name="detected_issue_implications",
        help_text="FHIR implicated: observations involved in the issue.",
    )
    implicated_service_requests = models.ManyToManyField(
        "ServiceRequest",
        blank=True,
        related_name="detected_issue_implications",
        help_text="FHIR implicated: service requests or orders involved in the issue.",
    )
    implicated_procedures = models.ManyToManyField(
        "Procedure",
        blank=True,
        related_name="detected_issue_implications",
        help_text="FHIR implicated: procedures involved in the issue.",
    )
    implicated_devices = models.ManyToManyField(
        "Device",
        blank=True,
        related_name="detected_issue_implications",
        help_text="FHIR implicated: devices involved in the issue.",
    )
    implicated_diagnostic_reports = models.ManyToManyField(
        DiagnosticReport,
        blank=True,
        related_name="detected_issue_implications",
        help_text="FHIR implicated: diagnostic reports involved in the issue.",
    )
    evidence_observations = models.ManyToManyField(
        Observation,
        blank=True,
        related_name="detected_issue_evidence",
        help_text="FHIR evidence.detail: observations that support the detected issue.",
    )
    evidence_conditions = models.ManyToManyField(
        Condition,
        blank=True,
        related_name="detected_issue_evidence",
        help_text="FHIR evidence.detail: conditions that support the detected issue.",
    )
    evidence_diagnostic_reports = models.ManyToManyField(
        DiagnosticReport,
        blank=True,
        related_name="detected_issue_evidence",
        help_text="FHIR evidence.detail: diagnostic reports that support the detected issue.",
    )
    status = models.CharField(max_length=30, blank=True, help_text="FHIR status: registered, preliminary, final, etc.")
    code = models.CharField(max_length=255, blank=True, help_text="FHIR code: issue category such as duplicate therapy.")
    severity = models.CharField(max_length=30, blank=True, help_text="FHIR severity: high, moderate, or low.")
    identified_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="FHIR identified[x]: when the issue was first identified.",
    )
    detail = models.TextField(blank=True, help_text="FHIR detail: description and context for the issue.")
    reference = models.URLField(blank=True, help_text="FHIR reference: authority or knowledge source for the issue.")
    evidence_summary = models.TextField(blank=True, help_text="FHIR evidence.code/detail: imported evidence summary.")
    mitigation_summary = models.TextField(blank=True, help_text="FHIR mitigation: steps taken to reduce or address the risk.")
    implicated_summary = models.TextField(blank=True, help_text="FHIR implicated: unresolved implicated resource references.")
    notes = models.TextField(blank=True, help_text="Additional imported issue notes.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Detected Issue"
        verbose_name_plural = "Detected Issues"

    def __str__(self):
        return self.code or self.detail or f"Detected Issue #{self.pk}"


class Person(models.Model):
    """FHIR Person: shared demographics and identity links across patient/practitioner/related-person roles."""

    managing_organization = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_people",
        help_text="FHIR managingOrganization: custodian of the person record.",
    )
    active = models.BooleanField(default=True, help_text="FHIR active: whether this person record is in active use.")
    name = models.CharField(max_length=255, blank=True, help_text="FHIR name: name associated with the person.")
    gender = models.CharField(max_length=30, blank=True, help_text="FHIR gender: administrative gender.")
    birth_date = models.DateField(null=True, blank=True, help_text="FHIR birthDate: date the person was born.")
    phone = models.CharField(max_length=30, blank=True, help_text="FHIR telecom: phone contact.")
    email = models.EmailField(blank=True, help_text="FHIR telecom: email contact.")
    address = models.TextField(blank=True, help_text="FHIR address: one or more addresses for the person.")
    notes = models.TextField(blank=True, help_text="Imported notes or source text for this person.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "People"

    def __str__(self):
        return self.name or f"Person #{self.pk}"


class PersonLink(models.Model):
    """FHIR Person.link: a role-specific resource believed to represent the same actual person."""

    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="link_records")
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="person_identity_links",
    )
    practitioner = models.ForeignKey(
        "Practitioner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="person_identity_links",
    )
    related_person = models.ForeignKey(
        "RelatedPerson",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="person_identity_links",
    )
    linked_person = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_from_person_records",
    )
    target_display = models.CharField(max_length=255, blank=True)
    target_reference = models.CharField(max_length=255, blank=True)
    assurance = models.CharField(max_length=30, blank=True, help_text="FHIR assurance: level1, level2, level3, or level4.")

    class Meta:
        verbose_name = "Person Link"
        verbose_name_plural = "Person Links"

    def __str__(self):
        target = self.patient or self.practitioner or self.related_person or self.linked_person or self.target_display
        return f"{self.person} -> {target or self.target_reference or 'linked resource'}"


class RelatedPerson(models.Model):
    """FHIR RelatedPerson: a person involved with a patient but not the direct target of care."""

    person = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_person_roles",
        help_text="Optional shared Person identity for this patient-specific related person role.",
    )
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="related_people",
        help_text="FHIR patient: the patient this person is related to.",
    )
    active = models.BooleanField(default=True, help_text="FHIR active: whether this related person record is in active use.")
    name = models.CharField(max_length=255, blank=True, help_text="FHIR name: name associated with the related person.")
    relationship = models.CharField(
        max_length=255,
        blank=True,
        help_text="FHIR relationship: spouse, parent, guardian, caregiver, friend, etc.",
    )
    gender = models.CharField(max_length=30, blank=True, help_text="FHIR gender: administrative gender.")
    birth_date = models.DateField(null=True, blank=True, help_text="FHIR birthDate: date the related person was born.")
    phone = models.CharField(max_length=30, blank=True, help_text="FHIR telecom: phone contact.")
    email = models.EmailField(blank=True, help_text="FHIR telecom: email contact.")
    address = models.TextField(blank=True, help_text="FHIR address: contact or visit address.")
    language = models.CharField(max_length=255, blank=True, help_text="FHIR communication.language: language used for health communication.")
    language_preferred = models.BooleanField(
        null=True,
        blank=True,
        help_text="FHIR communication.preferred: whether this language is preferred.",
    )
    period_start = models.DateField(null=True, blank=True, help_text="FHIR period.start: when this relationship became valid.")
    period_end = models.DateField(null=True, blank=True, help_text="FHIR period.end: when this relationship stopped being valid.")
    notes = models.TextField(blank=True, help_text="Imported notes or source text for this related person.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Related Person"
        verbose_name_plural = "Related People"

    def __str__(self):
        parts = [self.name, self.relationship]
        return " - ".join(part for part in parts if part) or f"Related Person #{self.pk}"


class FHIRGroup(models.Model):
    """FHIR Group: a defined collection of people, practitioners, devices, medications, substances, or groups."""

    managing_organization = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_groups",
        help_text="FHIR managingEntity: organization responsible for the group.",
    )
    managing_practitioner = models.ForeignKey(
        "Practitioner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_groups",
        help_text="FHIR managingEntity: practitioner responsible for the group.",
    )
    managing_role = models.ForeignKey(
        "PractitionerRole",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_groups",
        help_text="FHIR managingEntity: practitioner role responsible for the group.",
    )
    managing_related_person = models.ForeignKey(
        RelatedPerson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_groups",
        help_text="FHIR managingEntity: related person responsible for the group.",
    )
    active = models.BooleanField(default=True, help_text="FHIR active: whether this group record is in active use.")
    group_type = models.CharField(max_length=30, blank=True, help_text="FHIR type: person, practitioner, device, etc.")
    actual = models.BooleanField(default=True, help_text="FHIR actual: actual members vs intended/definitional group.")
    code = models.CharField(max_length=255, blank=True, help_text="FHIR code: kind of group members.")
    name = models.CharField(max_length=255, blank=True, help_text="FHIR name: human label for the group.")
    quantity = models.PositiveIntegerField(null=True, blank=True, help_text="FHIR quantity: number of members.")
    characteristic_summary = models.TextField(blank=True, help_text="FHIR characteristic: included/excluded member traits.")
    notes = models.TextField(blank=True, help_text="Imported notes or source text for this group.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Group"
        verbose_name_plural = "Groups"

    def __str__(self):
        return self.name or self.code or f"Group #{self.pk}"


class FHIRGroupMember(models.Model):
    """FHIR Group.member: a resource that belongs or belonged to a group."""

    group = models.ForeignKey(FHIRGroup, on_delete=models.CASCADE, related_name="member_links")
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="group_memberships",
    )
    practitioner = models.ForeignKey(
        "Practitioner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="group_memberships",
    )
    practitioner_role = models.ForeignKey(
        "PractitionerRole",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="group_memberships",
    )
    device = models.ForeignKey(
        "Device",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="group_memberships",
    )
    medication = models.ForeignKey(
        Medication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="group_memberships",
    )
    member_group = models.ForeignKey(
        FHIRGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parent_group_memberships",
    )
    entity_display = models.CharField(max_length=255, blank=True)
    entity_reference = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    inactive = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name = "Group Member"
        verbose_name_plural = "Group Members"

    def __str__(self):
        member = (
            self.patient
            or self.practitioner
            or self.practitioner_role
            or self.device
            or self.medication
            or self.member_group
            or self.entity_display
        )
        return str(member or self.entity_reference or f"Group Member #{self.pk}")


class PractitionerRole(models.Model):
    practitioner = models.ForeignKey(
        "Practitioner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="roles",
    )
    organization = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="practitioner_roles",
    )
    locations = models.ManyToManyField("Location", blank=True, related_name="practitioner_roles")
    active = models.BooleanField(default=True)
    role = models.CharField(max_length=255, blank=True)
    specialty = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Practitioner Role"
        verbose_name_plural = "Practitioner Roles"

    def __str__(self):
        parts = [str(part) for part in [self.practitioner, self.role, self.organization] if part]
        return " - ".join(parts) or f"Practitioner Role #{self.pk}"


class ServiceRequest(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="service_requests")
    encounter = models.ForeignKey(
        Encounter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="service_requests",
    )
    requester_practitioner = models.ForeignKey(
        "Practitioner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_services",
    )
    requester_role = models.ForeignKey(
        PractitionerRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_services",
    )
    requester_organization = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_services",
    )
    requester_device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_services",
    )
    care_plans = models.ManyToManyField(CarePlan, blank=True, related_name="service_requests")
    replaces = models.ManyToManyField("self", blank=True, symmetrical=False, related_name="replacement_requests")
    performers_practitioners = models.ManyToManyField(
        "Practitioner",
        blank=True,
        related_name="service_request_performances",
    )
    performers_roles = models.ManyToManyField(
        PractitionerRole,
        blank=True,
        related_name="service_request_performances",
    )
    performers_organizations = models.ManyToManyField(
        "Organization",
        blank=True,
        related_name="service_request_performances",
    )
    performers_care_teams = models.ManyToManyField(CareTeam, blank=True, related_name="service_requests")
    performers_devices = models.ManyToManyField(Device, blank=True, related_name="service_request_performances")
    locations = models.ManyToManyField("Location", blank=True, related_name="service_requests")
    conditions = models.ManyToManyField(Condition, blank=True, related_name="service_requests")
    specimens = models.ManyToManyField(Specimen, blank=True, related_name="service_requests")
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=30, blank=True)
    intent = models.CharField(max_length=30, blank=True)
    category = models.CharField(max_length=255, blank=True)
    priority = models.CharField(max_length=30, blank=True)
    do_not_perform = models.BooleanField(default=False)
    authored_on = models.DateTimeField(null=True, blank=True)
    occurrence_start = models.DateTimeField(null=True, blank=True)
    occurrence_end = models.DateTimeField(null=True, blank=True)
    performer_type = models.CharField(max_length=255, blank=True)
    location_code = models.CharField(max_length=255, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    patient_instruction = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"

    def __str__(self):
        return self.name


class EpisodeOfCare(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="episodes_of_care")
    managing_organization = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="episodes_of_care",
    )
    care_manager_practitioner = models.ForeignKey(
        "Practitioner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_episodes",
    )
    care_manager_role = models.ForeignKey(
        PractitionerRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_episodes",
    )
    referral_requests = models.ManyToManyField(ServiceRequest, blank=True, related_name="episodes_of_care")
    care_teams = models.ManyToManyField(CareTeam, blank=True, related_name="episodes_of_care")
    status = models.CharField(max_length=30, blank=True)
    episode_type = models.CharField(max_length=255, blank=True)
    diagnosis_summary = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Episode of Care"
        verbose_name_plural = "Episodes of Care"

    def __str__(self):
        return self.episode_type or f"Episode of Care #{self.pk}"


class AdverseEvent(models.Model):
    """FHIR AdverseEvent: an actual or potential harmful event involving a patient."""

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="adverse_events",
        help_text="FHIR subject: patient affected by the adverse event.",
    )
    encounter = models.ForeignKey(
        Encounter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="adverse_events",
        help_text="FHIR encounter: visit or encounter associated with the event.",
    )
    location = models.ForeignKey(
        "Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="adverse_events",
        help_text="FHIR location: where the event occurred.",
    )
    recorder_practitioner = models.ForeignKey(
        "Practitioner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_adverse_events",
        help_text="FHIR recorder: person who recorded the event.",
    )
    recorder_role = models.ForeignKey(
        PractitionerRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_adverse_events",
        help_text="FHIR recorder: practitioner role used when the recorder is represented by role.",
    )
    resulting_conditions = models.ManyToManyField(
        Condition,
        blank=True,
        related_name="adverse_events",
        help_text="FHIR resultingCondition: conditions that resulted from the event.",
    )
    contributor_practitioners = models.ManyToManyField(
        "Practitioner",
        blank=True,
        related_name="adverse_event_contributions",
        help_text="FHIR contributor: practitioners involved in the event.",
    )
    contributor_roles = models.ManyToManyField(
        PractitionerRole,
        blank=True,
        related_name="adverse_event_contributions",
        help_text="FHIR contributor: practitioner roles involved in the event.",
    )
    contributor_devices = models.ManyToManyField(
        Device,
        blank=True,
        related_name="adverse_event_contributions",
        help_text="FHIR contributor: devices involved in the event.",
    )
    suspect_immunizations = models.ManyToManyField(
        Immunization,
        blank=True,
        related_name="suspected_adverse_events",
        help_text="FHIR suspectEntity.instance: immunizations suspected to have contributed.",
    )
    suspect_procedures = models.ManyToManyField(
        "Procedure",
        blank=True,
        related_name="suspected_adverse_events",
        help_text="FHIR suspectEntity.instance: procedures suspected to have contributed.",
    )
    suspect_medications = models.ManyToManyField(
        Medication,
        blank=True,
        related_name="suspected_adverse_events",
        help_text="FHIR suspectEntity.instance: medications suspected to have contributed.",
    )
    suspect_devices = models.ManyToManyField(
        Device,
        blank=True,
        related_name="suspected_adverse_events",
        help_text="FHIR suspectEntity.instance: devices suspected to have contributed.",
    )
    reference_documents = models.ManyToManyField(
        "documents.ClinicalDocument",
        blank=True,
        related_name="adverse_events",
        help_text="FHIR referenceDocument: documents relevant to the event.",
    )
    subject_medical_history_conditions = models.ManyToManyField(
        Condition,
        blank=True,
        related_name="adverse_event_medical_history_refs",
        help_text="FHIR subjectMedicalHistory: prior conditions relevant to the event.",
    )
    subject_medical_history_observations = models.ManyToManyField(
        Observation,
        blank=True,
        related_name="adverse_event_medical_history_refs",
        help_text="FHIR subjectMedicalHistory: prior observations relevant to the event.",
    )
    subject_medical_history_immunizations = models.ManyToManyField(
        Immunization,
        blank=True,
        related_name="adverse_event_medical_history_refs",
        help_text="FHIR subjectMedicalHistory: prior immunizations relevant to the event.",
    )
    subject_medical_history_procedures = models.ManyToManyField(
        "Procedure",
        blank=True,
        related_name="adverse_event_medical_history_refs",
        help_text="FHIR subjectMedicalHistory: prior procedures relevant to the event.",
    )
    actuality = models.CharField(max_length=30, blank=True, help_text="FHIR actuality: actual or potential adverse event.")
    category = models.CharField(max_length=255, blank=True, help_text="FHIR category: product-problem, product-quality, etc.")
    event = models.CharField(max_length=255, blank=True, help_text="FHIR event: type of adverse event.")
    event_date = models.DateTimeField(null=True, blank=True, help_text="FHIR date: when the adverse event occurred.")
    detected_date = models.DateTimeField(null=True, blank=True, help_text="FHIR detected: when the event was detected.")
    recorded_date = models.DateTimeField(null=True, blank=True, help_text="FHIR recordedDate: when the event was recorded.")
    seriousness = models.CharField(max_length=255, blank=True, help_text="FHIR seriousness: serious, non-serious, etc.")
    severity = models.CharField(max_length=255, blank=True, help_text="FHIR severity: mild, moderate, severe, etc.")
    outcome = models.CharField(max_length=255, blank=True, help_text="FHIR outcome: result or final state of the event.")
    suspect_entity_summary = models.TextField(blank=True, help_text="FHIR suspectEntity: imported summary for unsupported suspects.")
    causality_summary = models.TextField(blank=True, help_text="FHIR causality: assessment of causality for suspect entities.")
    notes = models.TextField(blank=True, help_text="FHIR note: additional event notes.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Adverse Event"
        verbose_name_plural = "Adverse Events"

    def __str__(self):
        return self.event or self.category or f"Adverse Event #{self.pk}"


class CareTeamParticipant(models.Model):
    care_team = models.ForeignKey(CareTeam, on_delete=models.CASCADE, related_name="participant_links")
    practitioner = models.ForeignKey(
        "Practitioner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="care_team_participations",
    )
    organization = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="care_team_participations",
    )
    location = models.ForeignKey(
        "Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="care_team_participations",
    )
    related_person = models.ForeignKey(
        RelatedPerson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="care_team_participations",
    )
    role = models.CharField(max_length=255, blank=True)
    member_display = models.CharField(max_length=255, blank=True)
    member_reference = models.CharField(max_length=255, blank=True)
    on_behalf_of_display = models.CharField(max_length=255, blank=True)
    on_behalf_of_reference = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Care Team Participant"
        verbose_name_plural = "Care Team Participants"

    def __str__(self):
        participant = self.practitioner or self.organization or self.location or self.related_person or self.member_display
        if self.role and participant:
            return f"{self.role}: {participant}"
        return str(participant or self.role or f"Participant #{self.pk}")


class Practitioner(models.Model):
    name = models.CharField(max_length=255)
    npi = models.CharField(max_length=30, blank=True)
    active = models.BooleanField(default=True)
    qualification = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Procedure(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="procedures")
    encounter = models.ForeignKey(
        Encounter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="procedures",
    )
    care_plans = models.ManyToManyField(CarePlan, blank=True, related_name="procedures")
    service_requests = models.ManyToManyField(ServiceRequest, blank=True, related_name="procedures")
    conditions = models.ManyToManyField(Condition, blank=True, related_name="procedures")
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=30, blank=True)
    category = models.CharField(max_length=255, blank=True)
    performed_start = models.DateTimeField(null=True, blank=True)
    performed_end = models.DateTimeField(null=True, blank=True)
    body_site = models.CharField(max_length=255, blank=True)
    outcome = models.CharField(max_length=255, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    location_display = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProcedurePerformer(models.Model):
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE, related_name="performer_links")
    practitioner = models.ForeignKey(
        Practitioner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="procedure_performances",
    )
    organization = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="procedure_performances",
    )
    role = models.CharField(max_length=255, blank=True)
    actor_display = models.CharField(max_length=255, blank=True)
    actor_reference = models.CharField(max_length=255, blank=True)
    on_behalf_of_display = models.CharField(max_length=255, blank=True)
    on_behalf_of_reference = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Procedure Performer"
        verbose_name_plural = "Procedure Performers"

    def __str__(self):
        performer = self.practitioner or self.organization or self.actor_display
        if self.role and performer:
            return f"{self.role}: {performer}"
        return str(performer or self.role or f"Performer #{self.pk}")


class Organization(models.Model):
    name = models.CharField(max_length=255)
    organization_type = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=30, blank=True)
    mode = models.CharField(max_length=30, blank=True)
    location_type = models.CharField(max_length=255, blank=True)
    managing_organization = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
