from django.db import models
from django.contrib.auth.models import User
import pyotp

class SecurityQuestionSet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    question_1 = models.CharField(max_length=255, blank=True, null=True)
    question_2 = models.CharField(max_length=255, blank=True, null=True)
    question_3 = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Pytania bezpieczeństwa: {self.user.username}"

class Photo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Zdjęcie użytkownika: {self.user.username}"

class AuthenticatorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_secret = models.CharField(max_length=32, blank=True, null=True)
    authenticator_enabled = models.BooleanField(default=False)

    def generate_otp_secret(self):
        self.otp_secret = pyotp.random_base32()
        self.save()

    def get_totp_uri(self):
        if not self.otp_secret:
            return None
        return pyotp.totp.TOTP(self.otp_secret).provisioning_uri(
            name=self.user.username,
            issuer_name="TwojaAplikacja"
        )

    def __str__(self):
        return f"Authenticator: {self.user.username}"