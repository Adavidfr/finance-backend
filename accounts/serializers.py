from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from finances.models import Account

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return value

    def validate(self, attrs):
        # Se pasa un usuario temporal para que Django también rechace
        # contraseñas demasiado parecidas al usuario o al correo.
        candidate = User(username=attrs.get("username"), email=attrs.get("email"))
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    def create(self, validated_data):
        # Usuario y cuenta inicial se crean juntos: o se guardan los dos o ninguno.
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            Account.objects.create(
                user=user,
                name="Cuenta principal",
                account_type=Account.AccountType.CHECKING,
            )
        return user