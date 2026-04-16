from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm

from patients.models import RecoveryCredential
from patients.recovery import check_recovery_key


class RecoveryKeyPasswordResetForm(forms.Form):
    username = forms.CharField(max_length=150)
    recovery_key = forms.CharField(
        label="Recovery key",
        max_length=64,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )

    error_messages = {
        "invalid_recovery": "The username and recovery key did not match.",
    }

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username", "")
        recovery_key = cleaned_data.get("recovery_key", "")

        if not username or not recovery_key:
            return cleaned_data

        User = get_user_model()

        try:
            user = User.objects.get(username=username)
            credential = RecoveryCredential.objects.get(user=user)
        except (User.DoesNotExist, RecoveryCredential.DoesNotExist):
            raise forms.ValidationError(self.error_messages["invalid_recovery"])

        if not check_recovery_key(recovery_key, credential.recovery_key_hash):
            raise forms.ValidationError(self.error_messages["invalid_recovery"])

        cleaned_data["user"] = user
        cleaned_data["credential"] = credential
        return cleaned_data


class RecoveryKeySetPasswordForm(SetPasswordForm):
    pass
