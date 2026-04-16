from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from django.utils import timezone

from patients.forms import RecoveryKeyPasswordResetForm, RecoveryKeySetPasswordForm
from patients.recovery import generate_recovery_key, hash_recovery_key


class FirstRunOwnerForm(UserCreationForm):
    confirm_no_password_recovery = forms.BooleanField(
        label="I understand HolyFHIR cannot recover this password for me.",
        required=True,
        error_messages={
            "required": "Please confirm that you understand there is no password recovery yet.",
        },
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username",)


def first_run_setup(request):
    User = get_user_model()

    if User.objects.exists():
        return redirect("/admin/")

    if request.method == "POST":
        form = FirstRunOwnerForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            login(request, user)
            return redirect("/admin/")
    else:
        form = FirstRunOwnerForm()

    return render(request, "first_run_setup.html", {"form": form})


def recovery_key_reset_start(request):
    if request.method == "POST":
        form = RecoveryKeyPasswordResetForm(request.POST)

        if form.is_valid():
            request.session["recovery_reset_user_id"] = form.cleaned_data["user"].pk
            request.session["recovery_reset_credential_id"] = form.cleaned_data["credential"].pk
            return redirect("recovery_key_reset_confirm")
    else:
        form = RecoveryKeyPasswordResetForm()

    return render(request, "recovery_key_reset_start.html", {"form": form})


def recovery_key_reset_confirm(request):
    user_id = request.session.get("recovery_reset_user_id")
    credential_id = request.session.get("recovery_reset_credential_id")

    if not user_id or not credential_id:
        return redirect("recovery_key_reset_start")

    User = get_user_model()
    user = User.objects.get(pk=user_id)

    if request.method == "POST":
        form = RecoveryKeySetPasswordForm(user, request.POST)

        if form.is_valid():
            form.save()
            credential = user.recovery_credential
            new_recovery_key = generate_recovery_key()
            credential.recovery_key_hash = hash_recovery_key(new_recovery_key)
            credential.last_used_at = timezone.now()
            credential.save(update_fields=["recovery_key_hash", "last_used_at"])
            request.session.pop("recovery_reset_user_id", None)
            request.session.pop("recovery_reset_credential_id", None)
            messages.warning(
                request,
                "Your password was reset. Save the new recovery key before closing this page.",
            )
            return render(
                request,
                "recovery_key_reset_done.html",
                {"new_recovery_key": new_recovery_key},
            )
    else:
        form = RecoveryKeySetPasswordForm(user)

    return render(request, "recovery_key_reset_confirm.html", {"form": form})
