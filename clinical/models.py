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
        participant = self.practitioner or self.organization or self.location or self.member_display
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
