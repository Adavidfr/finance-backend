from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle

from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    # Sin autenticación: si el navegador manda un token viejo o vencido en la
    # cabecera, DRF respondería 401 aunque el endpoint sea público.
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"