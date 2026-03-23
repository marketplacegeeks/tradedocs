import phonenumbers
from rest_framework import serializers
from .models import User, UserRole


class UserProfileSerializer(serializers.ModelSerializer):
    """Returns the current user's public profile — used by the /me endpoint."""
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "role", "is_active", "phone_country_code", "phone_number",
        ]
        read_only_fields = fields


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing users in User Management."""
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "role", "is_active", "date_joined",
            "phone_country_code", "phone_number",
        ]
        read_only_fields = fields


class UserCreateSerializer(serializers.ModelSerializer):
    """Used by Company Admin to invite (create) a new user."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "role", "password", "phone_country_code", "phone_number"]
        extra_kwargs = {
            "phone_country_code": {"required": False, "default": ""},
            "phone_number": {"required": False, "default": ""},
        }

    def validate(self, attrs):
        # Guard: only SUPER_ADMIN may create another COMPANY_ADMIN user.
        request = self.context.get("request")
        if attrs.get("role") == UserRole.COMPANY_ADMIN:
            if not request or request.user.role != UserRole.SUPER_ADMIN:
                raise serializers.ValidationError(
                    {"role": "Only a Super Admin can create Company Admin users."}
                )

        # Phone validation: both fields must be provided together, or neither.
        code = attrs.get("phone_country_code", "").strip()
        number = attrs.get("phone_number", "").strip()
        if code or number:
            if not code or not number:
                raise serializers.ValidationError(
                    {"phone": "Both phone country code and phone number must be provided together."}
                )
            try:
                parsed = phonenumbers.parse(code + number)
                if not phonenumbers.is_valid_number(parsed):
                    raise serializers.ValidationError(
                        {"phone": "The phone number is not valid for the given country code."}
                    )
            except phonenumbers.NumberParseException:
                raise serializers.ValidationError(
                    {"phone": "Invalid phone number format. Use a dial code like +91 and a local number."}
                )
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    """Used by Company Admin to change a user's role, active status, or phone number."""

    class Meta:
        model = User
        fields = ["role", "is_active", "phone_country_code", "phone_number"]

    def validate(self, attrs):
        request = self.context.get("request")
        instance = self.instance

        # Guard 1: A Company Admin cannot modify their own account via this serializer.
        if request and instance and request.user.pk == instance.pk:
            if "is_active" in attrs:
                raise serializers.ValidationError(
                    {"is_active": "You cannot deactivate your own account."}
                )
            if "role" in attrs:
                raise serializers.ValidationError(
                    {"role": "You cannot change your own role."}
                )

        # Guard 2: Cannot deactivate or demote the last active Company Admin.
        if instance and instance.role == UserRole.COMPANY_ADMIN:
            active_admin_count = User.objects.filter(
                role=UserRole.COMPANY_ADMIN, is_active=True
            ).count()
            if attrs.get("is_active") is False and active_admin_count <= 1:
                raise serializers.ValidationError(
                    {"is_active": "Cannot deactivate the last active Company Admin."}
                )
            if "role" in attrs and attrs["role"] != UserRole.COMPANY_ADMIN and active_admin_count <= 1:
                raise serializers.ValidationError(
                    {"role": "Cannot change the role of the last active Company Admin."}
                )

        # Phone validation: both fields must be provided together, or neither.
        code = attrs.get("phone_country_code", "").strip()
        number = attrs.get("phone_number", "").strip()
        if code or number:
            if not code or not number:
                raise serializers.ValidationError(
                    {"phone": "Both phone country code and phone number must be provided together."}
                )
            try:
                parsed = phonenumbers.parse(code + number)
                if not phonenumbers.is_valid_number(parsed):
                    raise serializers.ValidationError(
                        {"phone": "The phone number is not valid for the given country code."}
                    )
            except phonenumbers.NumberParseException:
                raise serializers.ValidationError(
                    {"phone": "Invalid phone number format. Use a dial code like +91 and a local number."}
                )

        return attrs
