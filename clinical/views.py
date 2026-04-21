from django.contrib import admin
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.shortcuts import render
from django.urls import reverse

from patients.models import PatientProfile

from .models import Observation


MAX_SERIES = 6


def observation_charts(request):
    patient_id = request.GET.get("patient") or ""
    if patient_id and not patient_id.isdigit():
        patient_id = ""

    selected_names = [name for name in request.GET.getlist("names") if name.strip()]
    start_date = parse_date(request.GET.get("start") or "")
    end_date = parse_date(request.GET.get("end") or "")

    numeric_observations = Observation.objects.filter(value_quantity__isnull=False)

    patients = PatientProfile.objects.filter(
        observations__value_quantity__isnull=False,
    ).distinct().order_by("last_name", "first_name")

    if patient_id:
        numeric_observations = numeric_observations.filter(patient_id=patient_id)

    available_names = list(
        numeric_observations.exclude(name="")
        .order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )

    if not selected_names:
        selected_names = _default_observation_names(available_names)

    selected_names = selected_names[:MAX_SERIES]

    chart_observations = numeric_observations.filter(name__in=selected_names)

    if start_date:
        chart_observations = chart_observations.filter(effective_datetime__date__gte=start_date)

    if end_date:
        chart_observations = chart_observations.filter(effective_datetime__date__lte=end_date)

    chart_observations = chart_observations.select_related("patient").order_by("effective_datetime", "created_at", "id")
    chart_series = _chart_series(chart_observations, selected_names)

    context = {
        **admin.site.each_context(request),
        "title": "Observation Charts",
        "patients": patients,
        "selected_patient_id": str(patient_id),
        "available_names": available_names,
        "selected_names": selected_names,
        "start": request.GET.get("start", ""),
        "end": request.GET.get("end", ""),
        "chart_series": chart_series,
        "max_series": MAX_SERIES,
        "observation_add_url": reverse("admin:clinical_observation_add"),
    }
    return render(request, "admin/observation_charts.html", context)


def _default_observation_names(available_names):
    blood_pressure_names = [
        name
        for name in available_names
        if any(fragment in name.lower() for fragment in ("blood pressure", "systolic", "diastolic", "bp "))
    ]

    if blood_pressure_names:
        return blood_pressure_names[:2]

    return available_names[:1]


def _chart_series(observations, selected_names):
    series_by_name = {
        name: {
            "name": name,
            "unit": "",
            "points": [],
        }
        for name in selected_names
    }

    for observation in observations:
        series = series_by_name.get(observation.name)

        if series is None:
            continue

        observed_at = observation.effective_datetime or observation.created_at
        observed_at = timezone.localtime(observed_at)

        if not series["unit"] and observation.unit:
            series["unit"] = observation.unit

        series["points"].append(
            {
                "x": observed_at.isoformat(),
                "label": observed_at.strftime("%b %d, %Y %I:%M %p").replace(" 0", " "),
                "value": float(observation.value_quantity),
                "patient": str(observation.patient),
                "unit": observation.unit,
                "interpretation": observation.interpretation,
                "reference_range": observation.reference_range,
            }
        )

    return [series for series in series_by_name.values() if series["points"]]
