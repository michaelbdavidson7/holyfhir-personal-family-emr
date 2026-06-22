from dataclasses import dataclass

from django.urls import reverse


@dataclass(frozen=True)
class ResourceCard:
    title: str
    model: object
    description: str
    icon: str
    admin_name: str | None = None
    count_label: str = "record"

    def to_card(self):
        admin_name = self.admin_name or f"clinical_{self.model._meta.model_name}"

        return {
            "title": self.title,
            "description": self.description,
            "url": reverse(f"admin:{admin_name}_changelist"),
            "icon": self.icon,
            "count": self.model.objects.count(),
            "count_label": self.count_label,
        }
