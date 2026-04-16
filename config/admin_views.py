from django.contrib import admin
from django.shortcuts import render
from django.urls import reverse


def settings_hub(request):
    cards = [
        {
            "title": "Users",
            "description": "Manage the local owner account and password.",
            "url": reverse("admin:auth_user_changelist"),
            "icon": "fas fa-user",
        },
        {
            "title": "Groups",
            "description": "Advanced Django permission groups.",
            "url": reverse("admin:auth_group_changelist"),
            "icon": "fas fa-users",
        },
        {
            "title": "Recovery Keys",
            "description": "View recovery-key status and stored hashes.",
            "url": reverse("admin:patients_recoverycredential_changelist"),
            "icon": "fas fa-key",
        },
    ]

    context = {
        **admin.site.each_context(request),
        "title": "Settings",
        "settings_cards": cards,
    }
    return render(request, "admin/settings_hub.html", context)
