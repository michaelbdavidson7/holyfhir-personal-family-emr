from django.contrib import admin
from django import forms
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from urllib.parse import urlencode

from patients.models import PatientProfile

from .models import Observation
from .models import QuickLog


MAX_SERIES = 6
QUICK_LOG_LAST_CATEGORY_SESSION_KEY = "quick_logs_last_category"
QUICK_LOG_LAST_PATIENT_SESSION_KEY = "quick_logs_last_patient"


class QuickLogForm(forms.ModelForm):
    class Meta:
        model = QuickLog
        fields = ("patient", "category", "logged_at", "summary", "details")
        widgets = {
            "patient": forms.Select(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "logged_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "summary": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Bowel movement, breakfast, symptom, etc.",
                }
            ),
            "details": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Optional notes",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["logged_at"].input_formats = ["%Y-%m-%dT%H:%M"]


def quick_logs(request):
    selected_patient_id = (
        request.GET.get("patient") or request.POST.get("patient") or ""
    )
    if selected_patient_id and not selected_patient_id.isdigit():
        selected_patient_id = ""
    selected_category = request.GET.get("category") or ""
    if selected_category not in dict(QuickLog.CATEGORY_CHOICES):
        selected_category = ""

    initial = {
        "logged_at": timezone.localtime(timezone.now()).strftime("%Y-%m-%dT%H:%M")
    }
    last_category = request.session.get(QUICK_LOG_LAST_CATEGORY_SESSION_KEY)
    if last_category in dict(QuickLog.CATEGORY_CHOICES):
        initial["category"] = last_category
    if selected_category:
        initial["category"] = selected_category
    last_patient_id = request.session.get(QUICK_LOG_LAST_PATIENT_SESSION_KEY)
    if last_patient_id and PatientProfile.objects.filter(pk=last_patient_id).exists():
        initial["patient"] = last_patient_id
    if selected_patient_id:
        initial["patient"] = selected_patient_id

    if request.method == "POST":
        form = QuickLogForm(request.POST)
        if form.is_valid():
            quick_log = form.save()
            request.session[QUICK_LOG_LAST_CATEGORY_SESSION_KEY] = quick_log.category
            request.session[QUICK_LOG_LAST_PATIENT_SESSION_KEY] = quick_log.patient_id
            messages.success(request, "Quick log added.")
            return redirect(_quick_logs_url(quick_log.patient_id, quick_log.category))
    else:
        form = QuickLogForm(initial=initial)

    logs = QuickLog.objects.select_related("patient").order_by(
        "-logged_at", "-created_at", "-id"
    )
    if selected_patient_id:
        logs = logs.filter(patient_id=selected_patient_id)
    if selected_category:
        logs = logs.filter(category=selected_category)

    patients = PatientProfile.objects.order_by("last_name", "first_name")
    category_tabs = _quick_log_category_tabs(selected_patient_id, selected_category)

    context = {
        **admin.site.each_context(request),
        "title": "Quick Logs",
        "form": form,
        "logs": logs[:100],
        "patients": patients,
        "selected_patient_id": str(selected_patient_id),
        "selected_category": selected_category,
        "category_tabs": category_tabs,
        "admin_changelist_url": reverse("admin:clinical_quicklog_changelist"),
    }
    return render(request, "admin/quick_logs.html", context)


def _quick_logs_url(patient_id="", category=""):
    params = {}
    if patient_id:
        params["patient"] = patient_id
    if category:
        params["category"] = category
    query = urlencode(params)
    if not query:
        return reverse("quick_logs")
    return f"{reverse('quick_logs')}?{query}"


def _quick_log_category_tabs(selected_patient_id, selected_category):
    tabs = [
        {
            "label": "All",
            "category": "",
            "url": _quick_logs_url(selected_patient_id),
            "active": not selected_category,
        }
    ]
    for category, label in QuickLog.CATEGORY_CHOICES:
        tabs.append(
            {
                "label": label,
                "category": category,
                "url": _quick_logs_url(selected_patient_id, category),
                "active": selected_category == category,
            }
        )
    return tabs


def observation_charts(request):
    patient_id = request.GET.get("patient") or ""
    if patient_id and not patient_id.isdigit():
        patient_id = ""

    selected_names = [name for name in request.GET.getlist("names") if name.strip()]
    start_date = parse_date(request.GET.get("start") or "")
    end_date = parse_date(request.GET.get("end") or "")

    numeric_observations = Observation.objects.filter(value_quantity__isnull=False)

    patients = (
        PatientProfile.objects.filter(
            observations__value_quantity__isnull=False,
        )
        .distinct()
        .order_by("last_name", "first_name")
    )

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
        chart_observations = chart_observations.filter(
            effective_datetime__date__gte=start_date
        )

    if end_date:
        chart_observations = chart_observations.filter(
            effective_datetime__date__lte=end_date
        )

    chart_observations = chart_observations.select_related("patient").order_by(
        "effective_datetime", "created_at", "id"
    )
    chart_series = _chart_series(chart_observations, selected_names)

    context = {
        **admin.site.each_context(request),
        "title": "Health Trends",
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
        if any(
            fragment in name.lower()
            for fragment in ("blood pressure", "systolic", "diastolic", "bp ")
        )
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
