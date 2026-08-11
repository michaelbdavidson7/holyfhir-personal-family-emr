from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model, login, password_validation
from django.shortcuts import redirect, render
from django.utils import timezone
from config.branding import APP_SHORT_NAME

from patients.forms import RecoveryKeyPasswordResetForm, RecoveryKeySetPasswordForm
from patients.models import RecoveryCredential
from patients.recovery import generate_recovery_key, hash_recovery_key
from system_settings.models import SystemSettings


class SecurityChoiceForm(forms.Form):
    AUTH_OFF = "off"
    AUTH_ON = "on"
    AUTH_CHOICES = (
        (
            AUTH_OFF,
            "Open without a password (recommended).",
        ),
        (
            AUTH_ON,
            "Ask for a password.",
        ),
    )

    auth_enabled = forms.ChoiceField(
        label="Choose one",
        choices=AUTH_CHOICES,
        initial=AUTH_OFF,
        widget=forms.RadioSelect,
    )
    password1 = forms.CharField(
        label="Choose a password",
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Only needed if you choose to use a password.",
    )
    password2 = forms.CharField(
        label="Type the password again",
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    confirm_no_password_recovery = forms.BooleanField(
        label=f"I understand I must write down the {APP_SHORT_NAME} recovery key on the next screen.",
        required=False,
    )

    def __init__(
        self,
        *args,
        auth_initial=AUTH_OFF,
        password_required=True,
        recovery_ack_required=True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.fields["auth_enabled"].initial = auth_initial
        self.password_required = password_required
        self.recovery_ack_required = recovery_ack_required

        if not password_required:
            self.fields[
                "password1"
            ].help_text = "Leave blank to keep the current password."

    def clean(self):
        cleaned_data = super().clean()
        auth_enabled = cleaned_data.get("auth_enabled") == self.AUTH_ON
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        password_supplied = bool(password1 or password2)
        needs_password = auth_enabled and (self.password_required or password_supplied)
        needs_recovery_ack = auth_enabled and (
            self.recovery_ack_required or password_supplied
        )

        if not auth_enabled:
            return cleaned_data

        if needs_password:
            if not password1:
                self.add_error("password1", "Please type a password.")
            if not password2:
                self.add_error("password2", "Please type the password again.")
            if password1 and password2 and password1 != password2:
                self.add_error("password2", "Those passwords do not match.")
            if password1:
                try:
                    password_validation.validate_password(password1)
                except forms.ValidationError as error:
                    self.add_error("password1", error)

        if needs_recovery_ack and not cleaned_data.get("confirm_no_password_recovery"):
            self.add_error(
                "confirm_no_password_recovery",
                "Please check the box so you remember to write down the recovery key.",
            )

        return cleaned_data

    @property
    def auth_is_enabled(self):
        return self.cleaned_data.get("auth_enabled") == self.AUTH_ON

    @property
    def has_new_password(self):
        return bool(self.cleaned_data.get("password1"))


class FirstRunOwnerForm(SecurityChoiceForm):
    username = forms.CharField(
        label="Your name",
        max_length=150,
        initial="Owner",
        help_text="If you decide to use a password, this is the name you type first.",
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        help_text="Optional. Saved only on this computer.",
    )

    field_order = [
        "username",
        "email",
        "auth_enabled",
        "password1",
        "password2",
        "confirm_no_password_recovery",
    ]

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        User = get_user_model()

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That owner name is already in use.")

        return username


class SetupWizardForm(SecurityChoiceForm):
    pass


def _save_sign_in_setting(auth_enabled):
    system_settings = SystemSettings.get_solo()
    system_settings.app_lock_enabled = auth_enabled

    if not auth_enabled:
        system_settings.lock_shortcut_enabled = False
        system_settings.login_lockout_enabled = False

    system_settings.save(
        update_fields=[
            "app_lock_enabled",
            "lock_shortcut_enabled",
            "login_lockout_enabled",
            "updated_at",
        ]
    )


def _generate_recovery_key_for_user(user):
    recovery_key = generate_recovery_key()
    RecoveryCredential.objects.update_or_create(
        user=user,
        defaults={"recovery_key_hash": hash_recovery_key(recovery_key)},
    )
    return recovery_key


def _security_form_options_for_user(user):
    auth_enabled = SystemSettings.get_solo().app_lock_enabled
    has_recovery_key = RecoveryCredential.objects.filter(user=user).exists()
    return {
        "auth_initial": (
            SecurityChoiceForm.AUTH_ON if auth_enabled else SecurityChoiceForm.AUTH_OFF
        ),
        "password_required": not user.has_usable_password(),
        "recovery_ack_required": not has_recovery_key,
    }


def _render_setup(request, **context):
    defaults = {
        "recovery_step": False,
        "setup_wizard_mode": False,
    }
    defaults.update(context)
    return render(request, "first_run_setup.html", defaults)


def first_run_setup(request):
    User = get_user_model()
    recovery_key = request.session.get("first_run_recovery_key")

    if recovery_key and request.user.is_authenticated:
        if request.method == "POST" and request.POST.get("continue_to_app"):
            request.session.pop("first_run_recovery_key", None)
            return redirect("/admin/")

        return _render_setup(
            request,
            recovery_key=recovery_key,
            recovery_step=True,
        )

    if User.objects.exists():
        return redirect("/admin/")

    if request.method == "POST":
        form = FirstRunOwnerForm(request.POST)

        if form.is_valid():
            auth_enabled = form.auth_is_enabled
            user = User(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                is_staff=True,
                is_superuser=True,
            )

            if auth_enabled:
                user.set_password(form.cleaned_data["password1"])
            else:
                user.set_unusable_password()

            user.save()
            _save_sign_in_setting(auth_enabled)
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            if auth_enabled:
                request.session["first_run_recovery_key"] = (
                    _generate_recovery_key_for_user(user)
                )
                return redirect("setup")

            request.session.pop("first_run_recovery_key", None)
            return redirect("/admin/")
    else:
        form = FirstRunOwnerForm()

    return _render_setup(request, form=form)


def setup_wizard(request):
    owner = request.user
    recovery_key = request.session.get("setup_wizard_recovery_key")

    if recovery_key:
        if request.method == "POST" and request.POST.get("continue_to_app"):
            request.session.pop("setup_wizard_recovery_key", None)
            return redirect("/admin/")

        return _render_setup(
            request,
            recovery_key=recovery_key,
            recovery_step=True,
            setup_wizard_mode=True,
            owner=owner,
        )

    form_options = _security_form_options_for_user(owner)

    if request.method == "POST":
        form = SetupWizardForm(request.POST, **form_options)

        if form.is_valid():
            auth_enabled = form.auth_is_enabled

            if auth_enabled:
                if form.has_new_password:
                    owner.set_password(form.cleaned_data["password1"])
                    owner.save(update_fields=["password"])
                    login(
                        request,
                        owner,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )

                _save_sign_in_setting(True)

                if form.has_new_password or form_options["recovery_ack_required"]:
                    request.session["setup_wizard_recovery_key"] = (
                        _generate_recovery_key_for_user(owner)
                    )
                    return redirect("setup_wizard")

                messages.success(request, "Setup updated. Sign-in is turned on.")
                return redirect("/admin/")

            owner.set_unusable_password()
            owner.save(update_fields=["password"])
            RecoveryCredential.objects.filter(user=owner).delete()
            _save_sign_in_setting(False)
            messages.success(request, "Setup updated. Sign-in is turned off.")
            return redirect("/admin/")
    else:
        form = SetupWizardForm(**form_options)

    return _render_setup(
        request,
        form=form,
        setup_wizard_mode=True,
        owner=owner,
    )


def recovery_key_reset_start(request):
    if request.method == "POST":
        form = RecoveryKeyPasswordResetForm(request.POST)

        if form.is_valid():
            request.session["recovery_reset_user_id"] = form.cleaned_data["user"].pk
            request.session["recovery_reset_credential_id"] = form.cleaned_data[
                "credential"
            ].pk
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
