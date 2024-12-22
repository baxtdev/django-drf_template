from rest_framework import serializers

from apps.user.models import User


class ShortDescUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = (
            'last_activity',
            'password',
            'is_superuser',
            'is_staff',
            'groups',
            'user_permissions'
        )