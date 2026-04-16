from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AppLockTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="owner", password="correct-password")

    def test_lock_redirects_to_unlock_and_blocks_admin(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("app_lock"))

        self.assertRedirects(response, reverse("app_unlock"))
        self.assertTrue(self.client.session["app_locked"])

        response = self.client.get(reverse("admin:index"))

        self.assertRedirects(response, reverse("app_unlock"))

    def test_unlock_with_password_clears_lock(self):
        self.client.force_login(self.user)
        session = self.client.session
        session["app_locked"] = True
        session.save()

        response = self.client.post(
            reverse("app_unlock"),
            {"password": "correct-password"},
        )

        self.assertRedirects(response, "/admin/", fetch_redirect_response=False)
        self.assertNotIn("app_locked", self.client.session)
