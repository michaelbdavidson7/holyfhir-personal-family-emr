from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render


class FirstRunOwnerForm(UserCreationForm):
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
