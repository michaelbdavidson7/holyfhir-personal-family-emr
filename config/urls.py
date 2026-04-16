"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path
from config.auth_forms import RateLimitedAdminAuthenticationForm
from config.admin_views import fhir_interop_hub, recovery_key_generate, settings_hub
from fhir.views import import_fhir_data
from patients.views import first_run_setup, recovery_key_reset_confirm, recovery_key_reset_start

admin.site.login_form = RateLimitedAdminAuthenticationForm

def admin_root_redirect(request):
    return redirect("/admin/patients/patientprofile/")
    
urlpatterns = [
    path('', first_run_setup, name='first_run_setup'),
    path('setup/', first_run_setup, name='setup'),
    path('recovery/reset/', recovery_key_reset_start, name='recovery_key_reset_start'),
    path('recovery/reset/confirm/', recovery_key_reset_confirm, name='recovery_key_reset_confirm'),
    path('admin/settings/', admin.site.admin_view(settings_hub), name='admin_settings'),
    path('admin/settings/recovery-key/', admin.site.admin_view(recovery_key_generate), name='admin_recovery_key_generate'),
    path('admin/fhir/interop/', admin.site.admin_view(fhir_interop_hub), name='fhir_interop_hub'),
    path('admin/fhir/import/', import_fhir_data, name='fhir_import'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
