from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    # Make email the unique identifier
    email = models.EmailField(_('email address'), unique=True)
    # Add a username field for display purposes
    username = models.CharField(_('username'), max_length=150, unique=False, null=True)  # Not unique

    # Set email as the USERNAME_FIELD
    USERNAME_FIELD = 'email'
    # Add username to REQUIRED_FIELDS
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email