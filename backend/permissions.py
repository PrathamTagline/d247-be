# sports/permissions.py
from rest_framework.permissions import BasePermission
from django.conf import settings


class HasTaglineSecretKey(BasePermission):
    """
    Allows access only if request contains correct x-tagline-secret-key header.
    """

    def has_permission(self, request, view):
        header_key = request.headers.get("x-tagline-secret-key")
        expected_key = getattr(settings, "TAGLINE_SECRET_KEY", None)

        if header_key and expected_key and header_key == expected_key:
            return True
        return False
